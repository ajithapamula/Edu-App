# core/tts_processor.py
import io
import glob
import random
import logging
from pathlib import Path
from typing import AsyncGenerator, Dict, Optional

import torch
from chatterbox.tts import ChatterboxTTS

# Optional WAV writer (recommended)
try:
    import soundfile as sf  # pip install soundfile
    HAVE_SF = True
except Exception:
    HAVE_SF = False

logger = logging.getLogger(__name__)


class UnifiedTTSProcessor:
    """
    One TTS for Daily Standup + Weekly Interview using Chatterbox.

    - Picks one reference audio from ref_audios/ per session and keeps it fixed.
    - Async streaming API: generate_ultra_fast_stream(text, session_id=...)
      yields bytes chunks (WAV if soundfile is available, else raw PCM16).
    - health_check() for readiness probes.
    """
    def __init__(
        self,
        ref_audio_dir: Path,
        device: Optional[str] = None,
        encode: str = "wav",           # "wav" or "pcm16"
        chunk_tokens: int = 25,
        temperature: float = 0.8,
        cfg_weight: float = 0.1,
        exaggeration: float = 0.6,
    ):
        self.ref_audio_dir = Path(ref_audio_dir)
        self.encode = encode
        self.chunk_tokens = chunk_tokens
        self.temperature = temperature
        self.cfg_weight = cfg_weight
        self.exaggeration = exaggeration

        # Device autodetect
        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            elif torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
        self.device = device

        logger.info("[TTS] Loading ChatterboxTTS on device=%s ...", self.device)
        self.model = ChatterboxTTS.from_pretrained(device=self.device)  # exposes .sr

        # session_id -> chosen audio_prompt_path
        self._session_voice_map: Dict[str, Optional[str]] = {}

        # Pre-scan reference audio pool
        self._ref_pool = self._scan_ref_audios(self.ref_audio_dir)
        if not self._ref_pool:
            logger.warning("[TTS] No reference audios found in %s", self.ref_audio_dir)

    # ---------------- Session voice handling ----------------
    def start_session(self, session_id: str):
        """Choose & pin one reference file for this session (sticky voice)."""
        if session_id in self._session_voice_map:
            return
        self._session_voice_map[session_id] = self._choose_ref_audio()

    def end_session(self, session_id: str):
        """Forget the pinned voice for a session."""
        self._session_voice_map.pop(session_id, None)

    def _scan_ref_audios(self, ref_dir: Path):
        patterns = ["*.wav", "*.mp3", "*.flac", "*.ogg", "*.m4a"]
        pool = []
        for p in patterns:
            pool.extend(glob.glob(str(ref_dir / p)))
        return pool

    def _choose_ref_audio(self) -> Optional[str]:
        if not self._ref_pool:
            return None
        return random.choice(self._ref_pool)

    # ---------------- Public API: streaming ----------------
    async def generate_ultra_fast_stream(
        self,
        text: str,
        session_id: Optional[str] = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream audio bytes for the given text.
        - If Chatterbox has `generate_stream` (sync generator), iterate it directly.
        - Otherwise, fall back to one-shot `generate` and yield a single chunk.
        """
        if not text or not text.strip():
            return

        # pin / fetch session voice
        audio_prompt_path = None
        if session_id:
            if session_id not in self._session_voice_map:
                self.start_session(session_id)
            audio_prompt_path = self._session_voice_map.get(session_id)

        try:
            # --- Preferred path: streaming available (sync generator) ---
            if hasattr(self.model, "generate_stream") and callable(getattr(self.model, "generate_stream")):
                # NOTE: generate_stream in example_vc_stream.py is a *sync* generator
                # so we iterate it directly (this may block briefly while yielding).
                for audio_chunk, _metrics in self.model.generate_stream(
                    text=text,
                    audio_prompt_path=audio_prompt_path,
                    chunk_size=self.chunk_tokens,
                    temperature=self.temperature,
                    cfg_weight=self.cfg_weight,
                    exaggeration=self.exaggeration,
                    print_metrics=False,
                ):
                    yield self._encode_chunk(audio_chunk, self.model.sr)
                return

            # --- Fallback path: no streaming in this build; use one-shot generate ---
            if hasattr(self.model, "generate") and callable(getattr(self.model, "generate")):
                wav = self.model.generate(text=text, audio_prompt_path=audio_prompt_path)
                # yield once so the frontend still gets "some" audio
                yield self._encode_chunk(wav, self.model.sr)
                return

            # Neither method is present
            raise AttributeError("ChatterboxTTS has neither generate_stream nor generate")

        except Exception as e:
            logger.error("[TTS] Streaming/generation error: %s", e)
            return


    # ---------------- Health check ----------------
    async def health_check(self) -> dict:
        try:
            text = "test"
            chunks = 0
            gen = self.model.generate_stream(
                text=text, audio_prompt_path=None, chunk_size=10,
                exaggeration=0.7,
                temperature=0.8, cfg_weight=0.1, print_metrics=False
            )
            async for audio_chunk, _m in gen:
                _ = audio_chunk
                chunks += 1
                if chunks >= 1:
                    break
            return {"status": "healthy", "chunks": chunks, "device": self.device}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ---------------- Encoding helpers ----------------
    def _encode_chunk(self, tensor_chunk: "torch.Tensor", sr: int) -> bytes:
        pcm = tensor_chunk.squeeze().detach().cpu().numpy()

        if self.encode == "wav" and HAVE_SF:
            buf = io.BytesIO()
            # write 16-bit PCM WAV
            sf.write(buf, pcm, sr, subtype="PCM_16", format="WAV")
            return buf.getvalue()

        # Fallback: raw PCM16 frames (little-endian)
        import numpy as np
        pcm = pcm.clip(-1.0, 1.0)
        i16 = (pcm * 32767.0).astype(np.int16)
        return i16.tobytes()
