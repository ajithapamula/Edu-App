"""
TTS Processing module for Daily Standup application
Handles all Text-to-Speech operations with modular design for easy TTS model switching
"""

import re
import logging
import edge_tts
from typing import List, AsyncGenerator

from .config import config

logger = logging.getLogger(__name__)

# =============================================================================
# TTS PROCESSOR CLASS
# =============================================================================

class UltraFastTTSProcessor:
    """
    Ultra-fast TTS processor using Edge TTS
    Modular design allows easy switching to other TTS services (OpenAI, ElevenLabs, etc.)
    """
    
    def __init__(self):
        self.voice = config.TTS_VOICE
        self.rate = config.TTS_RATE
    
    def split_text_optimized(self, text: str) -> List[str]:
        """Optimized text splitting for minimal latency"""
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        
        current_chunk = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if len(current_chunk) + len(sentence) > config.TTS_CHUNK_SIZE * 5:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text]
    
    async def generate_ultra_fast_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        """Ultra-fast audio generation with parallel processing"""
        try:
            chunks = self.split_text_optimized(text)
            
            tasks = []
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                
                if i == 0:
                    async for audio_chunk in self._generate_chunk_audio(chunk):
                        if audio_chunk:
                            yield audio_chunk
                else:
                    tasks.append(self._generate_chunk_audio(chunk))
            
            for task in tasks:
                async for audio_chunk in task:
                    if audio_chunk:
                        yield audio_chunk
                        
        except Exception as e:
            logger.error(f"?? Ultra-fast TTS error: {e}")
            raise Exception(f"TTS generation failed: {e}")
    
    async def _generate_chunk_audio(self, chunk: str) -> AsyncGenerator[bytes, None]:
        """Generate audio for a single chunk"""
        try:
            tts = edge_tts.Communicate(chunk, self.voice, rate=self.rate)
            audio_data = b""
            
            async for tts_chunk in tts.stream():
                if tts_chunk["type"] == "audio":
                    audio_data += tts_chunk["data"]
            
            if audio_data:
                yield audio_data
            else:
                raise Exception("EdgeTTS returned empty audio data")
                
        except Exception as e:
            logger.error(f"?? Chunk TTS error: {e}")
            raise Exception(f"TTS chunk generation failed: {e}")

