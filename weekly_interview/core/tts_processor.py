# weekly_interview/core/tts_processor.py
"""
Dynamic TTS Processor - NO HARDCODED VALUES, FAIL LOUDLY FOR DEBUGGING
Uses dynamic voice selection with preference order, no static fallbacks
"""

import asyncio
import edge_tts
import logging
import re
from typing import AsyncGenerator, List
from .config import config

logger = logging.getLogger(__name__)

class UltraFastTTSProcessor:
    """Dynamic TTS processor with intelligent voice selection - NO HARDCODED VALUES"""
    
    def __init__(self):
        # Start with config voice but will be dynamically determined
        self.voice = config.TTS_VOICE
        self.rate = config.TTS_SPEED
        self.available_voices = None
        self._voices_checked = False
        self.voice_selection_strategy = "dynamic"
    
    async def _check_voice_availability(self):
        """Dynamically check and select best available voice - FAIL LOUDLY ON ERRORS"""
        if self._voices_checked:
            return
            
        try:
            logger.info("?? Dynamically checking available TTS voices...")
            voices = await edge_tts.list_voices()
            self.available_voices = [voice["Name"] for voice in voices]
            
            logger.info(f"?? Found {len(self.available_voices)} total voices")
            
            # Dynamic voice selection with preference order (NO HARDCODED FALLBACKS)
            voice_preferences = [
                config.TTS_VOICE,  # User configured voice first
                # Dynamic English preferences in order of quality
                *[v for v in self.available_voices if "en-US" in v and "JennyNeural" in v],
                *[v for v in self.available_voices if "en-US" in v and "Neural" in v],
                *[v for v in self.available_voices if "en-GB" in v and "Neural" in v],
                *[v for v in self.available_voices if "en-AU" in v and "Neural" in v],
                *[v for v in self.available_voices if "en-IN" in v and "Neural" in v],
                *[v for v in self.available_voices if "en-" in v and "Neural" in v],
                *[v for v in self.available_voices if "en-" in v],
            ]
            
            # Remove duplicates while preserving order
            seen = set()
            unique_preferences = []
            for voice in voice_preferences:
                if voice and voice not in seen and voice in self.available_voices:
                    unique_preferences.append(voice)
                    seen.add(voice)
            
            if not unique_preferences:
                # FAIL LOUDLY - NO HARDCODED FALLBACKS
                available_english = [v for v in self.available_voices if "en-" in v.lower()]
                error_msg = f"NO SUITABLE ENGLISH VOICES FOUND! Available English voices: {available_english[:5]}"
                logger.error(f"? {error_msg}")
                raise Exception(error_msg)
            
            # Select the first available voice from preferences
            selected_voice = unique_preferences[0]
            
            if selected_voice != self.voice:
                old_voice = self.voice
                self.voice = selected_voice
                logger.info(f"?? Voice changed: {old_voice} ? {self.voice}")
            else:
                logger.info(f"? Using configured voice: {self.voice}")
            
            # Log voice details for debugging
            voice_details = next((v for v in voices if v["Name"] == self.voice), None)
            if voice_details:
                logger.info(f"?? Voice details: {voice_details.get('Locale', 'Unknown')} - {voice_details.get('Gender', 'Unknown')}")
            
            self._voices_checked = True
            
        except Exception as e:
            logger.error(f"? CRITICAL: Voice availability check failed: {e}")
            # FAIL LOUDLY - NO MASKED ERRORS
            raise Exception(f"TTS voice selection failed: {e}")
    
    def split_text_optimized(self, text: str) -> List[str]:
        """Dynamic text splitting based on content length"""
        if not text or not text.strip():
            raise Exception("Empty text provided for TTS processing")
        
        # Dynamic chunk size based on text length
        base_chunk_size = config.TTS_CHUNK_SIZE * 5
        text_length = len(text)
        
        if text_length < 100:
            # Short text - single chunk
            return [text.strip()]
        elif text_length < 300:
            # Medium text - split by sentences
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences if s.strip()]
        else:
            # Long text - intelligent chunking
            sentences = re.split(r'[.!?]+', text)
            chunks = []
            current_chunk = ""
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                if len(current_chunk) + len(sentence) > base_chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    current_chunk += " " + sentence if current_chunk else sentence
            
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            return chunks if chunks else [text.strip()]
    
    async def generate_ultra_fast_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        """Generate dynamic TTS stream - FAIL LOUDLY ON CRITICAL ERRORS"""
        if not text or not text.strip():
            raise Exception("Empty text provided for TTS generation")
        
        try:
            # Dynamic voice selection
            await self._check_voice_availability()
            
            chunks = self.split_text_optimized(text)
            logger.info(f"?? Generating TTS for {len(chunks)} chunks with voice: {self.voice}")
            
            if not chunks:
                raise Exception("Text splitting produced no valid chunks")
            
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    logger.warning(f"?? Skipping empty chunk {i+1}")
                    continue
                
                logger.info(f"?? Processing chunk {i+1}/{len(chunks)}: '{chunk[:50]}...'")
                
                # Generate audio for this chunk - FAIL LOUDLY
                try:
                    audio_data = await self._generate_chunk_audio_with_dynamic_retry(chunk, chunk_index=i+1)
                    
                    if not audio_data:
                        raise Exception(f"Chunk {i+1} generated no audio data")
                    
                    if len(audio_data) < 100:
                        raise Exception(f"Chunk {i+1} generated insufficient audio: {len(audio_data)} bytes")
                    
                    yield audio_data
                    logger.info(f"? Chunk {i+1} generated: {len(audio_data)} bytes")
                    
                except Exception as chunk_error:
                    logger.error(f"? CRITICAL: Chunk {i+1} failed: {chunk_error}")
                    # FAIL LOUDLY - NO SILENT FALLBACKS
                    raise Exception(f"TTS chunk {i+1} generation failed: {chunk_error}")
                        
        except Exception as e:
            logger.error(f"? CRITICAL: TTS stream generation failed: {e}")
            logger.error(f"? Text length: {len(text)}, Voice: {self.voice}")
            # FAIL LOUDLY - NO FALLBACKS IN DEVELOPMENT
            raise Exception(f"TTS generation failed: {e}")
    
    async def _generate_chunk_audio_with_dynamic_retry(self, chunk: str, chunk_index: int, max_retries: int = 2) -> bytes:
        """Generate audio with dynamic retry strategy - FAIL LOUDLY"""
        
        for attempt in range(max_retries):
            try:
                logger.info(f"?? TTS attempt {attempt + 1}/{max_retries} for chunk {chunk_index}")
                
                # Create TTS communicator
                tts = edge_tts.Communicate(
                    text=chunk,
                    voice=self.voice,
                    rate=self.rate
                )
                
                audio_data = b""
                chunk_count = 0
                
                # Collect audio data with timeout
                async def collect_audio():
                    nonlocal audio_data, chunk_count
                    async for tts_chunk in tts.stream():
                        if tts_chunk["type"] == "audio" and tts_chunk["data"]:
                            audio_data += tts_chunk["data"]
                            chunk_count += 1
                
                # Dynamic timeout based on chunk length
                timeout_seconds = max(10.0, len(chunk) * 0.1)
                logger.info(f"?? Using {timeout_seconds}s timeout for {len(chunk)} char chunk")
                
                await asyncio.wait_for(collect_audio(), timeout=timeout_seconds)
                
                if not audio_data:
                    raise Exception(f"No audio data received from EdgeTTS (0 bytes, {chunk_count} chunks)")
                
                if len(audio_data) < 50:
                    raise Exception(f"Insufficient audio data: {len(audio_data)} bytes from {chunk_count} chunks")
                
                logger.info(f"? Generated {len(audio_data)} bytes from {chunk_count} TTS chunks")
                return audio_data
                    
            except asyncio.TimeoutError:
                error_msg = f"TTS timeout after {timeout_seconds}s on attempt {attempt + 1}"
                logger.error(f"?? {error_msg}")
                
                if attempt == max_retries - 1:
                    raise Exception(f"TTS timeout after {max_retries} attempts: {error_msg}")
                
                # Brief delay before retry
                await asyncio.sleep(1.0)
                
            except Exception as e:
                error_msg = f"TTS generation error on attempt {attempt + 1}: {e}"
                logger.error(f"? {error_msg}")
                
                if attempt == max_retries - 1:
                    # On final attempt, try voice switching if available
                    if self.available_voices and len(self.available_voices) > 1:
                        logger.info("?? Attempting voice switch on final retry...")
                        await self._try_alternative_voice()
                        
                        # One final attempt with new voice
                        try:
                            tts = edge_tts.Communicate(text=chunk, voice=self.voice, rate=self.rate)
                            audio_data = b""
                            async for tts_chunk in tts.stream():
                                if tts_chunk["type"] == "audio" and tts_chunk["data"]:
                                    audio_data += tts_chunk["data"]
                            
                            if audio_data and len(audio_data) > 50:
                                logger.info(f"? Voice switch successful: {len(audio_data)} bytes")
                                return audio_data
                        
                        except Exception as voice_switch_error:
                            logger.error(f"? Voice switch also failed: {voice_switch_error}")
                    
                    # FAIL LOUDLY - NO FALLBACKS
                    raise Exception(f"TTS failed after {max_retries} attempts: {error_msg}")
                
                await asyncio.sleep(0.5 * (attempt + 1))
        
        # Should never reach here
        raise Exception("TTS generation failed unexpectedly")
    
    async def _try_alternative_voice(self):
        """Try switching to alternative voice dynamically"""
        if not self.available_voices or len(self.available_voices) < 2:
            return
        
        current_voice = self.voice
        
        # Find next best English voice
        english_voices = [v for v in self.available_voices if "en-" in v and v != current_voice]
        
        if english_voices:
            # Prefer Neural voices
            neural_voices = [v for v in english_voices if "Neural" in v]
            if neural_voices:
                self.voice = neural_voices[0]
            else:
                self.voice = english_voices[0]
            
            logger.info(f"?? Voice switched: {current_voice} ? {self.voice}")
        else:
            logger.warning("?? No alternative English voices available")
    
    async def health_check(self) -> dict:
        """Dynamic health check with detailed voice information"""
        try:
            await self._check_voice_availability()
            
            # Quick test with minimal text
            test_text = "Test"
            test_success = False
            
            try:
                test_audio = await self._generate_chunk_audio_with_dynamic_retry(test_text, chunk_index=0, max_retries=1)
                test_success = bool(test_audio and len(test_audio) > 0)
            except Exception as test_error:
                logger.warning(f"?? Health check test failed: {test_error}")
            
            english_voice_count = len([v for v in self.available_voices if "en-" in v]) if self.available_voices else 0
            
            return {
                "status": "healthy" if test_success else "degraded",
                "provider": "EdgeTTS",
                "current_voice": self.voice,
                "voice_selection_strategy": self.voice_selection_strategy,
                "total_voices": len(self.available_voices) if self.available_voices else 0,
                "english_voices_available": english_voice_count,
                "test_generation": "success" if test_success else "failed",
                "configured_voice": config.TTS_VOICE,
                "voice_changed": self.voice != config.TTS_VOICE
            }
            
        except Exception as e:
            logger.error(f"? TTS health check failed: {e}")
            return {
                "status": "unhealthy",
                "provider": "EdgeTTS",
                "error": str(e),
                "voice_selection_strategy": self.voice_selection_strategy
            }