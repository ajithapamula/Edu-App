#Daily Stand Up Main
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import time
import uuid
import logging
import io
from typing import Dict, Optional, Any
from pathlib import Path
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import base64

# Local imports - use package-relative, keep names intact
from core import *
from core.ai_services import DS_SessionData as SessionData
from core.ai_services import DS_SessionStage as SessionStage
from core.ai_services import DS_SummaryManager as SummaryManager
from core.ai_services import ds_shared_clients as shared_clients
from core.config import config
from core.database import DatabaseManager
from core.ai_services import DS_OptimizedAudioProcessor as OptimizedAudioProcessor
# ⬇ Unified Chatterbox TTS
from core.tts_processor import UnifiedTTSProcessor as UltraFastTTSProcessor
from core.ai_services import DS_OptimizedConversationManager as OptimizedConversationManager
from core.prompts import DailyStandupPrompts as prompts

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# ENHANCED SESSION MANAGER WITH SILENCE DETECTION - COMPLETE VERSION
# =============================================================================

class UltraFastSessionManagerWithSilenceHandling:
    def __init__(self):
        self.active_sessions: Dict[str, SessionData] = {}
        self.db_manager = DatabaseManager(shared_clients)
        self.audio_processor = OptimizedAudioProcessor(shared_clients)
        self.tts_processor = UltraFastTTSProcessor(
            ref_audio_dir=getattr(config, "REF_AUDIO_DIR", Path("ref_audios")),
            encode=getattr(config, "TTS_STREAM_ENCODING", "wav"),
        )
        self.conversation_manager = OptimizedConversationManager(shared_clients)

    # --- small helper: domain inference to steer prompts ---
    def _infer_domain(self, text: str) -> str:
        try:
            t = (text or "").lower()
            if any(k in t for k in ("mysql", "database", "sql")): return "databases"
            if any(k in t for k in ("react", "frontend", "jsx")): return "frontend"
            if any(k in t for k in ("api", "fastapi", "backend")): return "backend"
            return "general"
        except Exception:
            return "general"

    # Enhanced silence response generation
    async def generate_dynamic_silence_response(self, session_data: SessionData, silence_context: dict = None):
        """Generate dynamic response to user silence using LLM"""
        try:
            # Get silence count for this session
            silence_count = getattr(session_data, 'silence_response_count', 0)
            session_data.silence_response_count = silence_count + 1
            
            # Build context for silence response
            context = {
                "name": session_data.student_name,
                "silence_count": session_data.silence_response_count,
                "current_stage": session_data.current_stage.value,
                "conversation_length": len(getattr(session_data,"conversation_log", [])),
                "time_elapsed": time.time() - session_data.created_at,
                "domain": getattr(session_data, "current_domain", "your work"),
                "last_topic": getattr(session_data, "current_concept", None),
                "silence_context": silence_context or {}
            }
            
            # Generate contextual silence response prompt
            silence_prompt = self._build_silence_response_prompt(context)
            
            # Generate response using LLM (not STT!)
            loop = asyncio.get_event_loop()
            response_text = await loop.run_in_executor(
                shared_clients.executor,
                self.conversation_manager._sync_openai_call,
                silence_prompt,
            )
            
            response_text = (response_text or "").strip()
            
            # Fallback responses if LLM fails
            if not response_text or len(response_text.split()) < 3:
                fallback_responses = [
                    f"Take your time, {session_data.student_name}. I'm here when you're ready to continue.",
                    f"No worries, {session_data.student_name}. Feel free to share your thoughts when you're comfortable.",
                    f"I understand you might need a moment to think. Let's continue whenever you're ready.",
                    f"That's okay, {session_data.student_name}. Would you like me to ask about something different?"
                ]
                response_text = fallback_responses[min(silence_count, len(fallback_responses) - 1)]
            
            logger.info("Generated silence response #%d: %s", session_data.silence_response_count, response_text[:50])
            return response_text
            
        except Exception as e:
            logger.error("Silence response generation error: %s", e)
            return f"I understand, {session_data.student_name}. Take your time, and let's continue when you're ready."

    def _build_silence_response_prompt(self, context: dict) -> str:
        """Build contextual prompt for silence response"""
        
        if context["silence_count"] == 1:
            # First silence - gentle encouragement
            return f"""
            The student {context["name"]} has been silent for a moment during their daily standup interview.
            This is their first silence. Generate a gentle, encouraging response that:
            
            1. Acknowledges their silence without making them feel pressured
            2. Offers reassurance and patience
            3. Keeps the conversation tone supportive and professional
            4. Uses their name naturally
            5. Is concise (1-2 sentences maximum)
            
            Context:
            - Current stage: {context["current_stage"]}
            - Time elapsed: {context["time_elapsed"]:.1f} seconds
            - Last topic discussed: {context.get("last_topic", "general standup questions")}
            
            Generate a supportive response that encourages them to continue when ready:
            """
            
        elif context["silence_count"] == 2:
            # Second silence - offer alternatives
            return f"""
            The student {context["name"]} has been silent again during their standup.
            This is their second silence. Generate a helpful response that:
            
            1. Offers to move to a different topic
            2. Suggests they might need more time to think
            3. Remains encouraging and patient
            4. Provides a gentle alternative or option
            5. Is still concise but slightly more directive
            
            Context:
            - Current domain: {context["domain"]}
            - Conversation length: {context["conversation_length"]} exchanges
            - Previous silences: {context["silence_count"] - 1}
            
            Generate a response that offers options while staying supportive:
            """
            
        else:
            # Multiple silences - gentle transition
            return f"""
            The student {context["name"]} has been silent multiple times ({context["silence_count"]} times).
            Generate a response that:
            
            1. Acknowledges this might be a challenging topic
            2. Offers to move forward or wrap up gracefully
            3. Maintains respect for their situation
            4. Provides a clear path forward
            5. Stays professional and understanding
            
            Context:
            - Multiple silences encountered
            - Session time: {context["time_elapsed"]:.1f} seconds
            - Current stage: {context["current_stage"]}
            
            Generate a respectful response that helps move the conversation forward:
            """

    async def create_session_fast(self, websocket: Optional[Any] = None) -> SessionData:
        session_id = str(uuid.uuid4())
        test_id = f"standup_{int(time.time())}"
        try:
            student_info_task = asyncio.create_task(self.db_manager.get_student_info_fast())
            summary_task = asyncio.create_task(self.db_manager.get_summary_fast())
            student_id, first_name, last_name, session_key = await student_info_task
            summary = await summary_task

            if not summary or len(summary.strip()) < 50:
                raise Exception("Invalid summary retrieved from database")
            if not first_name or not last_name:
                raise Exception("Invalid student data retrieved from database")

            session_data = SessionData(
                session_id=session_id,
                test_id=test_id,
                student_id=student_id,
                student_name=f"{first_name} {last_name}",
                session_key=session_key,
                created_at=time.time(),
                last_activity=time.time(),
                current_stage=SessionStage.GREETING,
                websocket=websocket,
            )

            # ---- existing silence counters ----
            session_data.silence_response_count = 0
            session_data.max_silence_responses = 3

            # ---- NEW refined silence state & guards ----
            session_data.consecutive_silence_chunks = 0
            session_data.silence_chunks_threshold = getattr(config, "SILENCE_CHUNKS_THRESHOLD", 3)
            session_data.silence_ready = False               # ignore silence until greeting TTS ends
            session_data.silence_prompt_active = False       # True while streaming a silence TTS
            session_data.has_user_spoken = False             # "in-between" only after first speech
            session_data.silence_grace_after_greeting_s = getattr(
                config, "SILENCE_GRACE_AFTER_GREETING_SECONDS", 4
            )
            session_data.greeting_end_ts = None              # set after greeting audio_end

            # 15 minutes hard limit; 2 min soft wrap-up window
            SESSION_MAX_SECONDS = getattr(config, "SESSION_MAX_SECONDS", 15 * 60)
            SESSION_SOFT_CUTOFF_SECONDS = getattr(config, "SESSION_SOFT_CUTOFF_SECONDS", 2 * 60)
            now_ts = time.time()
            session_data.end_time = now_ts + SESSION_MAX_SECONDS
            session_data.soft_cutoff_time = session_data.end_time - SESSION_SOFT_CUTOFF_SECONDS
            session_data.awaiting_user = False
            session_data.clarification_attempts = 0
            session_data.current_domain = "general"

            session_data._hard_stop_task = asyncio.create_task(self._hard_stop_watchdog(session_data))

            fragment_manager = SummaryManager(shared_clients, session_data)
            if not fragment_manager.initialize_fragments(summary):
                raise Exception("Failed to initialize fragments from summary")
            session_data.summary_manager = fragment_manager

            self.tts_processor.start_session(session_data.session_id)

            self.active_sessions[session_id] = session_data
            logger.info(
                "Enhanced session created %s for %s with %d fragments and silence handling",
                session_id, session_data.student_name, len(session_data.fragment_keys)
            )
            return session_data
        except Exception as e:
            logger.error("Failed to create enhanced session: %s", e)
            raise Exception(f"Session creation failed: {e}")

    # --- gentle nudge when no/poor audio ---
    async def generate_silence_response(self, session_data: SessionData):
        try:
            context = {
                "name": session_data.student_name,
                "domain": getattr(session_data, "current_domain", "your work") or "your work",
                "simple_english": True,
            }
            prompt = prompts.dynamic_silence_response(context)
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                shared_clients.executor,
                self.conversation_manager._sync_openai_call,
                prompt,
            )
            text = (text or "").strip()
            if not text or len(text.split()) < 3:
                text = f"Are you comfortable to continue {session_data.student_name}? Let's start whenever you're ready."
            await self._send_quick_message(session_data, {
                "type": "ai_response",
                "text": text,
                "status": session_data.current_stage.value
            })
            async for audio_chunk in self.tts_processor.generate_ultra_fast_stream(
                text, session_id=session_data.session_id
            ):
                if audio_chunk:
                    await self._send_quick_message(session_data, {
                        "type": "audio_chunk",
                        "audio": audio_chunk.hex(),
                        "status": session_data.current_stage.value
                    })
            await self._send_quick_message(session_data, {"type": "audio_end", "status": session_data.current_stage.value})
            logger.info("Sent silence-based prompt.")
        except Exception as e:
            logger.error("Failed to send silence-based response: %s", e)

    # --- default answer support from frontend ---
    async def process_default_answer(self, session_id: str, default_text: str):
        session_data = self.active_sessions.get(session_id)
        if not session_data or not session_data.is_active:
            logger.warning("Inactive session: %s", session_id)
            return

        start_time = time.time()
        try:
            logger.info("Session %s: processing default answer: %s", session_id, default_text)

            now_ts = time.time()
            if hasattr(session_data, "end_time") and now_ts >= session_data.end_time:
                await self._end_due_to_time(session_data)
                return

            quality = 0.5
            ai_response = await self.conversation_manager.generate_fast_response(session_data, default_text)

            concept = session_data.current_concept if session_data.current_concept else "default_answer"
            is_followup = getattr(session_data, '_last_question_followup', False)
            session_data.add_exchange(ai_response, default_text, quality, concept, is_followup)

            if session_data.summary_manager:
                session_data.summary_manager.add_answer(default_text)

            await self._update_session_state_fast(session_data)
            await self._send_response_with_ultra_fast_audio(session_data, ai_response)

            now_ts = time.time()
            soft_cutoff = getattr(session_data, "soft_cutoff_time", None)
            if session_data.current_stage == SessionStage.TECHNICAL and (not soft_cutoff or now_ts < soft_cutoff):
                session_data.awaiting_user = True

            logger.info("Default answer processing time: %.2fs", time.time() - start_time)

        except Exception as e:
            logger.error("Default answer processing error: %s", e)
            await self._send_quick_message(session_data, {
                "type": "error",
                "text": "Sorry, there was an issue processing your response. Please try again.",
                "status": "error"
            })

    # --- auto-advance when we can't hear the user ---
    async def _auto_advance_question(self, session_data: SessionData):
        try:
            logger.info("Session %s: auto-advancing to next question", session_data.session_id)

            advance_responses = [
                "I understand. Let's move on to the next topic.",
                "No worries, let's continue with something else.",
                "That's okay, let me ask about something different.",
                "Let's try a different question."
            ]
            attempt = getattr(session_data, 'clarification_attempts', 0)
            auto_advance_response = advance_responses[attempt] if attempt < len(advance_responses) else advance_responses[0]

            session_data.add_exchange(auto_advance_response, "[AUTO_ADVANCE]", 0.3, "auto_advance", False)
            session_data.clarification_attempts = 0

            await self._update_session_state_fast(session_data)
            await self._send_response_with_ultra_fast_audio(session_data, auto_advance_response)

            now_ts = time.time()
            end_time = getattr(session_data, "end_time", None)
            soft_cutoff = getattr(session_data, "soft_cutoff_time", None)
            time_remaining = (end_time - now_ts) if end_time else float('inf')

            if (session_data.current_stage == SessionStage.TECHNICAL and
                time_remaining > 60 and
                (not soft_cutoff or now_ts < soft_cutoff)):
                session_data.awaiting_user = True
            else:
                await self._finalize_session_fast(session_data)

        except Exception as e:
            logger.error("Auto-advance error: %s", e)
            await self._finalize_session_fast(session_data)

    async def _hard_stop_watchdog(self, session_data: SessionData):
        try:
            delay = max(0.0, getattr(session_data, "end_time", time.time()) - time.time())
            await asyncio.sleep(delay)
            if not session_data.is_active:
                return

            if getattr(session_data, "awaiting_user", False):
                setattr(session_data, "hard_cutoff_reached", True)
                grace = getattr(config, "FINAL_ANSWER_GRACE_SECONDS", 0)
                if grace > 0:
                    await asyncio.sleep(grace)
                    if session_data.is_active:
                        await self._end_due_to_time(session_data)
            else:
                await self._end_due_to_time(session_data)
        except asyncio.CancelledError:
            return

    async def _end_due_to_time(self, session_data: SessionData):
        def _extract_topics(sd: SessionData):
            topics = []
            sm = getattr(sd, "summary_manager", None)
            if not sm:
                return topics
            fk = getattr(sd, "fragment_keys", None)
            frags = getattr(sm, "fragments", None)
            if fk and isinstance(frags, dict):
                for k in fk:
                    frag = frags.get(k)
                    if isinstance(frag, dict):
                        t = frag.get("title") or frag.get("heading") or frag.get("name")
                        if t:
                            topics.append(t)
                if topics: return topics
            if isinstance(frags, list):
                for frag in frags:
                    if isinstance(frag, dict):
                        t = frag.get("title") or frag.get("heading") or frag.get("name")
                        if t:
                            topics.append(t)
                if topics: return topics
            if fk:
                return [str(k) for k in fk]
            return topics

        try:
            session_data.awaiting_user = False
        except Exception:
            pass

        try:
            topics = _extract_topics(session_data)
            conv_log = getattr(session_data, "conversation_log", []) or []
            user_final_response = (
                conv_log[-1].get("user_response") if conv_log and isinstance(conv_log[-1], dict) else None
            )
            conversation_summary = {
                "topics_covered": topics,
                "total_exchanges": len(conv_log),
            }

            closing_prompt = prompts.dynamic_session_completion(conversation_summary, user_final_response)
            loop = asyncio.get_event_loop()
            closing_text = await loop.run_in_executor(
                shared_clients.executor,
                self.conversation_manager._sync_openai_call,
                closing_prompt,
            )
            closing_text = (closing_text or "").strip()
            if len(closing_text.split()) < 6:
                closing_text = f"Thanks {session_data.student_name}; we'll stop here now—session complete."

            evaluation, score = None, None
            try:
                evaluation, score = await self.conversation_manager.generate_fast_evaluation(session_data)
            except Exception as e_eval:
                logger.error("Evaluation generation error (time-cutoff): %s", e_eval)

            try:
                if evaluation is not None and score is not None:
                    saved = await self.db_manager.save_session_result_fast(session_data, evaluation, score)
                    if not saved:
                        logger.error("Save (time-cutoff) failed for %s", session_data.session_id)
            except Exception as e_save:
                logger.exception("Save error (time-cutoff): %s", e_save)

            await self._send_quick_message(session_data, {
                "type": "conversation_end",
                "text": closing_text,
                "status": "complete",
                "enable_new_session": True,
                "evaluation": evaluation,
                "score": score,
                "pdf_url": f"/download_results/{session_data.session_id}",
                "redirect_to": "/dashboard",
            })

            try:
                async for audio_chunk in self.tts_processor.generate_ultra_fast_stream(
                    closing_text, session_id=session_data.session_id
                ):
                    if audio_chunk:
                        await self._send_quick_message(session_data, {
                            "type": "audio_chunk",
                            "audio": audio_chunk.hex(),
                            "status": "complete",
                        })
                await self._send_quick_message(session_data, {"type": "audio_end", "status": "complete"})
            except Exception as e_tts:
                logger.error("TTS closing stream error: %s", e_tts)

        except Exception as e:
            logger.error("Closing generation error: %s", e)
            fallback_text = f"Thanks {session_data.student_name}; we'll stop here now—session complete."

            evaluation, score = None, None
            try:
                evaluation, score = await self.conversation_manager.generate_fast_evaluation(session_data)
            except Exception as e_eval2:
                logger.error("Evaluation generation error (fallback): %s", e_eval2)

            try:
                if evaluation is not None and score is not None:
                    saved = await self.db_manager.save_session_result_fast(session_data, evaluation, score)
                    if not saved:
                        logger.error("Save (fallback) failed for %s", session_data.session_id)
            except Exception as e_save2:
                logger.exception("Save error (fallback): %s", e_save2)

            await self._send_quick_message(session_data, {
                "type": "conversation_end",
                "text": fallback_text,
                "status": "complete",
                "enable_new_session": True,
                "evaluation": evaluation,
                "score": score,
                "pdf_url": f"/download_results/{session_data.session_id}",
            })

            try:
                async for audio_chunk in self.tts_processor.generate_ultra_fast_stream(
                    fallback_text, session_id=session_data.session_id
                ):
                    if audio_chunk:
                        await self._send_quick_message(session_data, {
                            "type": "audio_chunk",
                            "audio": audio_chunk.hex(),
                            "status": "complete",
                        })
                await self._send_quick_message(session_data, {"type": "audio_end", "status": "complete"})
            except Exception as e_tts2:
                logger.error("TTS fallback closing stream error: %s", e_tts2)

        finally:
            session_data.is_active = False
            try:
                task = getattr(session_data, "_hard_stop_task", None)
                if task and not task.done():
                    task.cancel()
            except Exception:
                pass
            try:
                if session_data.websocket:
                    await session_data.websocket.close(code=1000)
            except Exception:
                pass
            await self.remove_session(session_data.session_id)

    async def remove_session(self, session_id: str):
        if session_id in self.active_sessions:
            try:
                self.tts_processor.end_session(session_id)
            except Exception:
                pass
            del self.active_sessions[session_id]
            logger.info("Removed session %s", session_id)

    # Enhanced audio processing with silence detection
    async def process_audio_with_silence_status(self, session_id: str, message_data: dict):
        """Process audio data with refined silence gating & consecutive counter."""
        session_data = self.active_sessions.get(session_id)
        if not session_data or not session_data.is_active:
            logger.warning("Inactive session: %s", session_id)
            return

        start_time = time.time()

        try:
            # Extract status info
            user_status = message_data.get('userStatus', 'unknown')
            silence_detected_flag = bool(message_data.get('silenceDetected', False))
            recording_duration = int(message_data.get('recordingDuration', 0))
            audio_b64 = message_data.get('audio', '') or ''

            # Time limits
            now_ts = time.time()
            end_time = getattr(session_data, "end_time", None)
            if end_time and now_ts >= end_time:
                if getattr(session_data, "awaiting_user", False):
                    try:
                        if audio_b64:
                            audio_bytes = base64.b64decode(audio_b64)
                            transcript, quality = await self.audio_processor.transcribe_audio_fast(audio_bytes)
                            logger.info("🗣️ User transcript: %s  (quality=%.2f, bytes=%d)",
                            (transcript or "").strip(), quality, len(audio_bytes))
                            if transcript.strip():
                                concept = session_data.current_concept or "unknown"
                                is_followup = getattr(session_data, "_last_question_followup", False)
                                session_data.add_exchange("[FINAL_ANSWER]", transcript, quality, concept, is_followup)
                                if session_data.summary_manager:
                                    session_data.summary_manager.add_answer(transcript)
                    except Exception as final_err:
                        logger.error("Final audio processing error: %s", final_err)
                await self._end_due_to_time(session_data)
                return

            # ---- refined silence gating ----
            past_greeting_grace = (
                session_data.greeting_end_ts is not None and
                (now_ts - session_data.greeting_end_ts) >= session_data.silence_grace_after_greeting_s
            )
            has_audio_payload = bool(audio_b64)
            # We only treat a chunk as "silence" if:
            # - greeting finished (silence_ready), and
            # - user has spoken already OR grace window after greeting passed, and
            # - frontend marks this as silence
            is_silence_chunk = (
                not has_audio_payload
                and session_data.silence_ready
                and (session_data.has_user_spoken or past_greeting_grace)
                and (silence_detected_flag or user_status in ('user_silent', 'user_stopped_speaking'))
            )

            # If the user explicitly says speaking → reset silence and mark spoken
            if user_status == 'user_speaking':
                session_data.consecutive_silence_chunks = 0
                session_data.silence_prompt_active = False
                session_data.has_user_spoken = True
                session_data.last_user_speech_ts = time.time()
            # ---- PATH A: silence chunk → skip STT, count, fire only at threshold ----
            if is_silence_chunk:
                session_data.consecutive_silence_chunks += 1
                logger.info(
                    "Session %s: silent chunk counted (%d/%d)",
                    session_id, session_data.consecutive_silence_chunks, session_data.silence_chunks_threshold
                )

                if session_data.consecutive_silence_chunks >= session_data.silence_chunks_threshold:
                    session_data.consecutive_silence_chunks = 0
                    # Build short, supportive silence response using prompts (no STT)
                    try:
                        ctx = {
                            "name": session_data.student_name,
                            "silence_count": getattr(session_data, 'silence_response_count', 0) + 1,
                            "current_stage": session_data.current_stage.value,
                            "conversation_length": len(getattr(session_data, "conversation_log", [])),
                            "time_elapsed": time.time() - session_data.created_at,
                            "domain": getattr(session_data, "current_domain", "your work"),
                            "last_topic": getattr(session_data, "current_concept", None),
                            "silence_context": {
                                "recording_duration": recording_duration,
                                "user_status": user_status,
                                "audio_size": len(audio_b64)
                            }
                        }
                        prompt = prompts.dynamic_silence_response(ctx)
                        loop = asyncio.get_event_loop()
                        text = await loop.run_in_executor(
                            shared_clients.executor,
                            self.conversation_manager._sync_openai_call,
                            prompt,
                        )
                        text = (text or "").strip()
                        if len(text.split()) < 3:
                            text = f"Take your time, {session_data.student_name}. We can continue whenever you’re ready."

                        # Log and stream
                        session_data.silence_response_count = getattr(session_data, 'silence_response_count', 0) + 1
                        concept = session_data.current_concept or "silence_handling"
                        session_data.add_exchange(text, "[USER_SILENT]", 0.0, concept, False)

                        session_data.silence_prompt_active = True
                        await self._send_silence_response_with_audio(session_data, text)
                        session_data.silence_prompt_active = False

                        soft_cutoff = getattr(session_data, "soft_cutoff_time", None)
                        if session_data.current_stage == SessionStage.TECHNICAL and (not soft_cutoff or now_ts < soft_cutoff):
                            session_data.awaiting_user = True

                    except Exception as e_sil:
                        logger.error("Silence prompt generation/streaming error: %s", e_sil)

                logger.info("Silence handling time: %.2fs", time.time() - start_time)
                return

            # ---- PATH B: normal audio → run STT ----
            if not audio_b64:
                logger.debug("Session %s: no audio data received", session_id)
                return

            audio_bytes = base64.b64decode(audio_b64)
            logger.info("Session %s: processing normal audio (%d bytes)", session_id, len(audio_bytes))
            transcript, quality = await self.audio_processor.transcribe_audio_fast(audio_bytes)
            logger.info("🗣️ User transcript: %s  (quality=%.2f, bytes=%d)",(transcript or "").strip(), quality, len(audio_bytes))
            # Reset silence counter and mark spoken on any real transcript
            if transcript and transcript.strip():
                session_data.consecutive_silence_chunks = 0
                session_data.has_user_spoken = True
                session_data.last_user_speech_ts = time.time()
            # Poor transcript handling (clarify → auto-advance)
            if not transcript or len(transcript.strip()) < 2:
                attempt = getattr(session_data, 'clarification_attempts', 0) + 1
                session_data.clarification_attempts = attempt
                if attempt >= 2:
                    await self._auto_advance_question(session_data)
                    return

                loop = asyncio.get_event_loop()
                clarification_message = await loop.run_in_executor(
                    shared_clients.executor,
                    self.conversation_manager._sync_openai_call,
                    prompts.dynamic_clarification_request({
                        'clarification_attempts': attempt,
                        'audio_quality': quality,
                        'audio_size': len(audio_bytes)
                    }),
                )
                await self._send_quick_message(session_data, {
                    "type": "clarification",
                    "text": (clarification_message or "Could you please repeat that?"),
                    "status": session_data.current_stage.value,
                })
                return

            # Normal conversation flow
            session_data.clarification_attempts = 0

            try:
                session_data.current_domain = self._infer_domain(transcript)
            except Exception as e:
                logger.debug("Domain inference error: %s", e)

            # Re-check time windows post-STT
            now_ts = time.time()
            soft_cutoff = getattr(session_data, "soft_cutoff_time", None)
            if end_time and now_ts >= end_time:
                concept = session_data.current_concept or "unknown"
                is_followup = getattr(session_data, "_last_question_followup", False)
                session_data.add_exchange("[TIME_EXPIRED]", transcript, quality, concept, is_followup)
                if session_data.summary_manager:
                    session_data.summary_manager.add_answer(transcript)
                await self._end_due_to_time(session_data)
                return
            elif soft_cutoff and now_ts >= soft_cutoff:
                concept = session_data.current_concept or "unknown"
                is_followup = getattr(session_data, "_last_question_followup", False)
                session_data.add_exchange("", transcript, quality, concept, is_followup)
                if session_data.summary_manager:
                    session_data.summary_manager.add_answer(transcript)
                ai_response = await self.conversation_manager.generate_fast_response(session_data, transcript)
                session_data.conversation_log[-1]["ai_response"] = ai_response
                await self._send_response_with_ultra_fast_audio(session_data, ai_response)
                await self._end_due_to_time(session_data)
                return

            # Generate AI response
            session_data.awaiting_user = False
            ai_response = await self.conversation_manager.generate_fast_response(session_data, transcript)

            concept = session_data.current_concept or "unknown"
            is_followup = getattr(session_data, "_last_question_followup", False)
            session_data.add_exchange(ai_response, transcript, quality, concept, is_followup)

            if session_data.summary_manager:
                session_data.summary_manager.add_answer(transcript)

            await self._update_session_state_fast(session_data)
            await self._send_response_with_ultra_fast_audio(session_data, ai_response)

            now_ts = time.time()
            if session_data.current_stage == SessionStage.TECHNICAL and (not soft_cutoff or now_ts < soft_cutoff):
                session_data.awaiting_user = True

            logger.info("Total audio processing time: %.2fs", time.time() - start_time)

        except Exception as e:
            logger.error("Enhanced audio processing error: %s", e)
            await self._send_quick_message(session_data, {
                "type": "error",
                "text": "There was a problem processing your response. Please try again.",
                "status": "error",
            })

    # Handle standalone silence notifications
    async def process_silence_notification(self, session_id: str, silence_data: dict):
        """
        Process standalone silence notification using refined gating:
        - Ignore until greeting audio finished (silence_ready)
        - Ignore while client is still recording
        - Ignore during small cooldown right after speech
        - Only count if user has spoken already OR we're past the post-greeting grace
        - Trigger a single supportive silence response only after N consecutive events
        """
        session_data = self.active_sessions.get(session_id)
        if not session_data or not session_data.is_active:
            logger.warning("Inactive session for silence notification: %s", session_id)
            return

        try:
            # 0) Do not consider silence until greeting playback finished
            if not getattr(session_data, "silence_ready", False):
                return

            now_ts = time.time()

            # 1) If the client reports it's *still recording*, don't treat this as silence
            if silence_data.get('recordingActive'):
                logger.debug("Session %s: silence ping ignored (recordingActive=True)", session_id)
                return

            # 2) Cooldown immediately after a speech turn (prevents instant silence after stop)
            cooldown_s = getattr(config, "SILENCE_COOLDOWN_AFTER_SPEECH_SECONDS", 2.0)
            last_speech_ts = getattr(session_data, "last_user_speech_ts", None)
            if last_speech_ts is not None and (now_ts - last_speech_ts) < cooldown_s:
                logger.debug(
                    "Session %s: silence ping ignored (within %.2fs speech cooldown)",
                    session_id, cooldown_s
                )
                return

            # 3) Respect a small grace window after greeting before counting initial quiet
            past_greeting_grace = (
                getattr(session_data, "greeting_end_ts", None) is not None and
                (now_ts - session_data.greeting_end_ts) >= getattr(
                    session_data, "silence_grace_after_greeting_s", 4
                )
            )

            # Only count if user has already spoken (true in-between) OR we're past grace
            if not (getattr(session_data, "has_user_spoken", False) or past_greeting_grace):
                logger.debug(
                    "Session %s: silence ping ignored (no prior speech and still in grace window)",
                    session_id
                )
                return

            # 4) Count consecutive silence events and trigger only at threshold
            session_data.consecutive_silence_chunks = getattr(session_data, "consecutive_silence_chunks", 0) + 1
            threshold = getattr(session_data, "silence_chunks_threshold", getattr(config, "SILENCE_CHUNKS_THRESHOLD", 1))
            logger.info(
                "Session %s: silence notification counted (%d/%d)",
                session_id, session_data.consecutive_silence_chunks, threshold
            )

            if session_data.consecutive_silence_chunks < threshold:
                return

            # Reached threshold ⇒ reset counter and produce a supportive silence response
            session_data.consecutive_silence_chunks = 0

            try:
                # Build minimal context for a short supportive response
                ctx = {
                    "name": session_data.student_name,
                    "silence_count": getattr(session_data, 'silence_response_count', 0) + 1,
                    "current_stage": session_data.current_stage.value,
                    "conversation_length": len(getattr(session_data, "conversation_log", [])),
                    "time_elapsed": time.time() - session_data.created_at,
                    "domain": getattr(session_data, "current_domain", "your work"),
                    "last_topic": getattr(session_data, "current_concept", None),
                    "silence_context": {
                        "notification_type": "standalone",
                        "status": silence_data.get('status', 'user_silent'),
                        "timestamp": silence_data.get('timestamp', now_ts),
                        "recording_active": bool(silence_data.get('recordingActive', False)),
                    }
                }

                # Generate a concise, supportive message (your existing helper)
                # NOTE: If you prefer to avoid LLM here, replace this call with a local template.
                text = await self.generate_dynamic_silence_response(session_data, ctx)
                if not text or len(text.split()) < 3:
                    text = f"Take your time, {session_data.student_name}. We can continue whenever you’re ready."

                # Log the exchange and stream TTS
                session_data.silence_response_count = getattr(session_data, 'silence_response_count', 0) + 1
                concept = getattr(session_data, "current_concept", None) or "silence_handling"
                session_data.add_exchange(text, "[USER_SILENT]", 0.0, concept, False)

                session_data.silence_prompt_active = True
                await self._send_silence_response_with_audio(session_data, text)
                session_data.silence_prompt_active = False

                # After a silence response, keep listening if we're still in TECHNICAL stage
                soft_cutoff = getattr(session_data, "soft_cutoff_time", None)
                if (session_data.current_stage == SessionStage.TECHNICAL and
                    (soft_cutoff is None or now_ts < soft_cutoff)):
                    session_data.awaiting_user = True

                logger.info("Session %s: standalone silence prompt delivered", session_id)

            except Exception as e_sil:
                logger.error("Session %s: silence prompt generation/streaming error: %s", session_id, e_sil)

        except Exception as e:
            logger.error("Silence notification processing error: %s", e)

    # Send silence response with specific message type
    async def _send_silence_response_with_audio(self, session_data: SessionData, text: str):
        """Send silence response with TTS audio; cancel mid-stream if speech resumes."""
        try:
            await self._send_quick_message(session_data, {
                "type": "silence_response",
                "text": text,
                "status": session_data.current_stage.value,
            })

            chunk_count = 0
            async for audio_chunk in self.tts_processor.generate_ultra_fast_stream(
                text, session_id=session_data.session_id
            ):
                if not session_data.is_active or not session_data.silence_prompt_active:
                    break
                await self._send_quick_message(session_data, {
                    "type": "audio_chunk",
                    "audio": audio_chunk.hex(),
                    "status": session_data.current_stage.value,
                })
                chunk_count += 1

            await self._send_quick_message(session_data, {
                "type": "audio_end",
                "status": session_data.current_stage.value
            })

            logger.info("Streamed %d silence response audio chunks", chunk_count)

        except Exception as e:
            logger.error("Silence response audio streaming error: %s", e)

    # Legacy method - redirect to new audio processing
    async def process_audio_ultra_fast(self, session_id: str, audio_data: bytes):
        """Legacy method - convert to new format and use enhanced processing"""
        # Convert old format to new message format
        import base64
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        message_data = {
            'audio': audio_b64,
            'userStatus': 'user_speaking',  # Default status
            'silenceDetected': False,
            'recordingDuration': 0
        }
        await self.process_audio_with_silence_status(session_id, message_data)

    async def _update_session_state_fast(self, session_data: SessionData):
        try:
            if session_data.current_stage == SessionStage.GREETING:
                session_data.greeting_count += 1
                if session_data.greeting_count >= config.GREETING_EXCHANGES:
                    session_data.current_stage = SessionStage.TECHNICAL
                    logger.info("Session %s moved to TECHNICAL stage", session_data.session_id)
            elif session_data.current_stage == SessionStage.TECHNICAL:
                now_ts = time.time()
                soft_cutoff = getattr(session_data, "soft_cutoff_time", None)
                if session_data.summary_manager:
                    has_covered_enough = not session_data.summary_manager.should_continue_test()
                    approaching_time_limit = soft_cutoff and now_ts >= (soft_cutoff - 60)
                    if has_covered_enough or approaching_time_limit:
                        session_data.current_stage = SessionStage.COMPLETE
                        logger.info("Session %s moved to COMPLETE stage (covered: %s, time: %s)",
                                    session_data.session_id, has_covered_enough, approaching_time_limit)
                        asyncio.create_task(self._finalize_session_fast(session_data))
        except Exception as e:
            logger.error("Session state update error: %s", e)

    async def _finalize_session_fast(self, session_data: SessionData):
        try:
            evaluation, score = await self.conversation_manager.generate_fast_evaluation(session_data)
            save_success = await self.db_manager.save_session_result_fast(session_data, evaluation, score)
            if not save_success:
                logger.error("Failed to save session %s", session_data.session_id)

            completion_message = f"Great job! Your standup session is complete. You scored {score}/10. Thank you!"
            await self._send_quick_message(session_data, {
                "type": "conversation_end",
                "text": completion_message,
                "evaluation": evaluation,
                "score": score,
                "pdf_url": f"/download_results/{session_data.session_id}",
                "status": "complete",
                "enable_new_session": True,
                "redirect_to": "/dashboard",
                "end_reason": "completed",
            })

            async for audio_chunk in self.tts_processor.generate_ultra_fast_stream(
                completion_message, session_id=session_data.session_id
            ):
                if audio_chunk:
                    await self._send_quick_message(session_data, {
                        "type": "audio_chunk",
                        "audio": audio_chunk.hex(),
                        "status": "complete",
                    })
            await self._send_quick_message(session_data, {"type": "audio_end", "status": "complete"})

        except Exception as e:
            logger.error("Fast session finalization error: %s", e)
        finally:
            session_data.is_active = False
            try:
                task = getattr(session_data, "_hard_stop_task", None)
                if task and not task.done():
                    task.cancel()
            except Exception:
                pass
            try:
                if session_data.websocket:
                    await session_data.websocket.close(code=1000)
            except Exception:
                pass
            await self.remove_session(session_data.session_id)

    async def _send_response_with_ultra_fast_audio(self, session_data: SessionData, text: str):
        try:
            await self._send_quick_message(session_data, {
                "type": "ai_response",
                "text": text,
                "status": session_data.current_stage.value,
            })
            chunk_count = 0
            async for audio_chunk in self.tts_processor.generate_ultra_fast_stream(
                text, session_id=session_data.session_id
            ):
                if audio_chunk and session_data.is_active:
                    await self._send_quick_message(session_data, {
                        "type": "audio_chunk",
                        "audio": audio_chunk.hex(),
                        "status": session_data.current_stage.value,
                    })
                    chunk_count += 1
            await self._send_quick_message(session_data, {"type": "audio_end", "status": session_data.current_stage.value})
            logger.info("Streamed %d audio chunks", chunk_count)
        except Exception as e:
            logger.error("Ultra-fast audio streaming error: %s", e)

    async def _send_quick_message(self, session_data: SessionData, message: dict):
        try:
            if session_data.websocket:
                await session_data.websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error("WebSocket send error: %s", e)

    async def get_session_result_fast(self, session_id: str) -> dict:
        try:
            result = await self.db_manager.get_session_result_fast(session_id)
            if not result:
                raise Exception(f"Session {session_id} not found in database")
            return result
        except Exception as e:
            logger.error("Error fetching session result: %s", e)
            raise Exception(f"Session result retrieval failed: {e}")


# =============================================================================
# FASTAPI APPLICATION - COMPLETE VERSION WITH SILENCE HANDLING
# =============================================================================

app = FastAPI(title=config.APP_TITLE, version=config.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOW_ORIGINS,
    allow_credentials=config.CORS_ALLOW_CREDENTIALS,
    allow_methods=config.CORS_ALLOW_METHODS,
    allow_headers=config.CORS_ALLOW_HEADERS,
)

app.mount("/audio", StaticFiles(directory=str(config.AUDIO_DIR)), name="audio")

# Create the enhanced session manager instance
session_manager = UltraFastSessionManagerWithSilenceHandling()

@app.on_event("startup")
async def startup_event():
    logger.info("Ultra-Fast Daily Standup with Enhanced Silence Detection starting...")
    try:
        db_manager = DatabaseManager(shared_clients)
        try:
            conn = db_manager.get_mysql_connection()
            conn.close()
            logger.info("MySQL connection test successful")
        except Exception as e:
            logger.error("MySQL connection test failed: %s", e)
            raise Exception(f"MySQL connection failed: {e}")

        try:
            await db_manager.get_mongo_client()
            logger.info("MongoDB connection test successful")
        except Exception as e:
            logger.error("MongoDB connection test failed: %s", e)
            raise Exception(f"MongoDB connection failed: {e}")

        logger.info("All database connections verified - silence detection ready")
    except Exception as e:
        logger.error("Startup failed: %s", e)

@app.on_event("shutdown")
async def shutdown_event():
    await shared_clients.close_connections()
    await session_manager.db_manager.close_connections()
    logger.info("Enhanced Daily Standup application shutting down")

@app.get("/start_test")
async def start_standup_session_fast():
    try:
        logger.info("Starting enhanced standup session with silence detection...")
        session_data = await session_manager.create_session_fast()
        greeting = "Hello! Welcome to your daily standup with enhanced silence detection. How are you doing today?"
        logger.info("Enhanced session created: %s", session_data.test_id)
        return {
            "status": "success",
            "message": "Session started successfully with silence detection",
            "test_id": session_data.test_id,
            "session_id": session_data.session_id,
            "websocket_url": f"/ws/{session_data.session_id}",
            "greeting": greeting,
            "student_name": session_data.student_name,
            "fragments_count": len(session_data.fragment_keys) if session_data.fragment_keys else 0,
            "estimated_duration": len(session_data.fragment_keys) * session_data.questions_per_concept * config.ESTIMATED_SECONDS_PER_QUESTION,
            "features": ["silence_detection", "dynamic_responses", "enhanced_vad"],
            "silence_handling": {
                "max_responses": session_data.max_silence_responses,
                "uses_llm": True,
                "bypasses_stt": True
            }
        }
    except Exception as e:
        logger.error("Error starting enhanced session: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")

@app.get("/api/summary/{test_id}")
async def get_standup_summary_fast(test_id: str):
    """Get standup session summary from real database"""
    try:
        logger.info(f"Getting summary for test_id: {test_id}")
        if not test_id:
            raise HTTPException(status_code=400, detail="test_id is required")

        result = await session_manager.get_session_result_fast(test_id)

        if result:
            exchanges = result.get("conversation_log", [])

            yesterday_work = ""
            today_plans = ""
            blockers = ""
            additional_notes = ""

            for exchange in exchanges:
                user_response = (exchange.get("user_response") or "").lower()
                ai_message = (exchange.get("ai_message") or "").lower()

                if any(word in ai_message for word in ["yesterday", "accomplished", "completed"]):
                    yesterday_work = exchange.get("user_response", "")
                elif any(word in ai_message for word in ["today", "plan", "working on"]):
                    today_plans = exchange.get("user_response", "")
                elif any(word in ai_message for word in ["blocker", "challenge", "obstacle", "stuck"]):
                    blockers = exchange.get("user_response", "")
                elif exchange.get("user_response") and not yesterday_work and not today_plans:
                    additional_notes = exchange.get("user_response", "")

            summary_data = {
                "test_id": test_id,
                "session_id": result.get("session_id", test_id),
                "student_name": result.get("student_name", "Student"),
                "timestamp": result.get("timestamp", time.time()),
                "duration": result.get("duration", 0),
                "yesterday": yesterday_work or "Progress discussed during session",
                "today": today_plans or "Plans outlined during session",
                "blockers": blockers or "No specific blockers mentioned",
                "notes": additional_notes or "Additional discussion points covered",
                "accomplishments": yesterday_work,
                "plans": today_plans,
                "challenges": blockers,
                "additional_info": additional_notes,
                "evaluation": result.get("evaluation", "Session completed successfully"),
                "score": result.get("score", 8.0),
                "total_exchanges": result.get("total_exchanges", 0),
                "fragment_analytics": result.get("fragment_analytics", {}),
                "pdf_url": f"/download_results/{test_id}",
                "status": "completed",
                "silence_responses": result.get("silence_responses", 0)
            }
            logger.info(f"Enhanced summary generated for {test_id}")
            return summary_data

        raise HTTPException(status_code=404, detail=f"Session result not found for test_id: {test_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=f"Summary retrieval failed: {str(e)}")

# =============================================================================
# PDF GENERATION UTILITY
# =============================================================================

def generate_pdf_report(result: dict, session_id: str) -> bytes:
    """Generate PDF report from real session data with silence handling info"""
    try:
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=LETTER)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title = f"Enhanced Daily Standup Report - {result.get('student_name', 'Student')}"
        story.append(Paragraph(title, styles['Title']))
        story.append(Spacer(1, 12))

        # Session info
        silence_count = result.get('silence_responses', 0)
        info_text = f"""
        Session ID: {session_id}
        Student: {result.get('student_name', 'Unknown')}
        Date: {datetime.fromtimestamp(result.get('timestamp', time.time())).strftime('%Y-%m-%d %H:%M:%S')}
        Duration: {result.get('duration', 0)/60:.1f} minutes
        Total Exchanges: {result.get('total_exchanges', 0)}
        Silence Responses: {silence_count}
        Score: {result.get('score', 0)}/10
        Enhanced Features: Silence Detection, Dynamic Responses
        """
        story.append(Paragraph(info_text, styles['Normal']))
        story.append(Spacer(1, 12))

        # Silence handling summary
        if silence_count > 0:
            story.append(Paragraph("Silence Handling Summary", styles['Heading2']))
            silence_text = f"""
            The system detected {silence_count} instances where the student was silent.
            Dynamic LLM-generated responses were provided to encourage participation.
            No speech-to-text processing was performed for silent periods.
            """
            story.append(Paragraph(silence_text, styles['Normal']))
            story.append(Spacer(1, 12))

        # Fragment analytics if available
        fragment_analytics = result.get('fragment_analytics', {})
        if fragment_analytics:
            story.append(Paragraph("Fragment Coverage Analysis", styles['Heading2']))
            analytics_text = f"""
            Total Concepts: {fragment_analytics.get('total_concepts', 0)}
            Coverage Percentage: {fragment_analytics.get('coverage_percentage', 0)}%
            Main Questions: {fragment_analytics.get('main_questions', 0)}
            Follow-up Questions: {fragment_analytics.get('followup_questions', 0)}
            """
            story.append(Paragraph(analytics_text, styles['Normal']))
            story.append(Spacer(1, 12))

        # Conversation log
        story.append(Paragraph("Conversation Summary", styles['Heading2']))
        for exchange in result.get('conversation_log', [])[:15]:
            if exchange.get('stage') != 'greeting':
                ai_msg = exchange.get('ai_message', '')
                user_resp = exchange.get('user_response', '')
                
                story.append(Paragraph(f"AI: {ai_msg}", styles['Normal']))
                
                # Handle silence indicators
                if user_resp == '[USER_SILENT]':
                    story.append(Paragraph("User: [Silent - dynamic response provided]", styles['Normal']))
                else:
                    story.append(Paragraph(f"User: {user_resp}", styles['Normal']))
                story.append(Spacer(1, 6))

        # Evaluation
        if result.get('evaluation'):
            story.append(Paragraph("Evaluation", styles['Heading2']))
            story.append(Paragraph(result['evaluation'], styles['Normal']))

        doc.build(story)
        pdf_buffer.seek(0)
        return pdf_buffer.read()

    except Exception as e:
        logger.error(f"Enhanced PDF generation error: {e}")
        raise Exception(f"PDF generation failed: {e}")

@app.get("/download_results/{session_id}")
async def download_results_fast(session_id: str):
    """Fast PDF generation and download from real data with silence handling"""
    try:
        result = await session_manager.get_session_result_fast(session_id)
        if not result:
            raise HTTPException(status_code=404, detail="Session not found")

        loop = asyncio.get_event_loop()
        pdf_buffer = await loop.run_in_executor(
            shared_clients.executor,
            generate_pdf_report,
            result, session_id
        )

        return StreamingResponse(
            io.BytesIO(pdf_buffer),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=enhanced_standup_report_{session_id}.pdf"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced PDF generation error: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@app.get("/test")
async def enhanced_test_endpoint():
    """Enhanced test endpoint with silence detection features"""
    return {
        "message": "Ultra-Fast Daily Standup with Enhanced Silence Detection",
        "timestamp": time.time(),
        "status": "blazing_fast_with_silence_handling",
        "config": {
            "real_data_mode": True,
            "silence_detection": True,
            "greeting_exchanges": config.GREETING_EXCHANGES,
            "summary_chunks": config.SUMMARY_CHUNKS,
            "openai_model": config.OPENAI_MODEL,
            "mysql_host": config.MYSQL_HOST,
            "mongodb_host": config.MONGODB_HOST
        },
        "enhanced_features": [
            "Real database connections",
            "Dynamic silence response generation",
            "Status-aware audio processing", 
            "LLM-powered silence handling",
            "No STT for silence cases",
            "Contextual silence responses",
            "Enhanced VAD with status tracking",
            "Intelligent conversation flow",
            "Multi-tier silence escalation",
            "Ultra-fast TTS streaming"
        ],
        "silence_handling": {
            "detection_threshold": "1-2 seconds",
            "response_types": ["encouragement", "alternatives", "gentle_transition"],
            "max_responses_per_session": 3,
            "uses_llm_for_responses": True,
            "bypasses_stt": True
        }
    }

@app.get("/health")
async def health_check_fast():
    """Ultra-fast health check with real database status and silence detection"""
    try:
        db_status = {"mysql": False, "mongodb": False}
        try:
            db_manager = DatabaseManager(shared_clients)
            conn = db_manager.get_mysql_connection()
            conn.close()
            db_status["mysql"] = True
            await db_manager.get_mongo_client()
            db_status["mongodb"] = True
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")

        return {
            "status": "healthy" if all(db_status.values()) else "degraded",
            "service": "ultra_fast_daily_standup_with_silence_detection",
            "timestamp": time.time(),
            "active_sessions": len(session_manager.active_sessions),
            "version": config.APP_VERSION,
            "database_status": db_status,
            "real_data_mode": True,
            "silence_detection_enabled": True,
            "features": ["enhanced_vad", "dynamic_silence_responses", "llm_powered_handling"]
        }
    except Exception as e:
        logger.error(f"Enhanced health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# =============================================================================
# ENHANCED WEBSOCKET WITH SILENCE HANDLING
# =============================================================================
@app.websocket("/ws/{session_id}")
async def enhanced_websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    hb_task = None
    session_data = None

    try:
        logger.info("Enhanced WebSocket connected for session: %s", session_id)

        session_data = session_manager.active_sessions.get(session_id)
        if not session_data or not getattr(session_data, "is_active", True):
            logger.error("Session %s not found or inactive", session_id)
            await websocket.send_text(json.dumps({
                "type": "error",
                "text": f"Session {session_id} not found. Please start a new session.",
                "status": "error",
            }))
            return

        session_data.websocket = websocket

        greeting = f"Hello {session_data.student_name}! Welcome to your daily standup with enhanced silence detection. How are you doing today?"
        await websocket.send_text(json.dumps({
            "type": "ai_response",
            "text": greeting,
            "status": "greeting"
        }))

        try:
            async for audio_chunk in session_manager.tts_processor.generate_ultra_fast_stream(
                greeting, session_id=session_id
            ):
                if audio_chunk and getattr(session_data, "is_active", False) and session_data.websocket is websocket:
                    await websocket.send_text(json.dumps({
                        "type": "audio_chunk",
                        "audio": audio_chunk.hex(),
                        "status": "greeting",
                    }))
            await websocket.send_text(json.dumps({"type": "audio_end", "status": "greeting"}))

            # ---- NEW: enable silence handling only AFTER greeting audio finishes ----
            session_data.silence_ready = True
            session_data.greeting_end_ts = time.time()

        except Exception as tts_error:
            logger.error("TTS error during greeting: %s", tts_error)
            # Even if TTS failed, allow the session to proceed
            session_data.silence_ready = True
            session_data.greeting_end_ts = time.time()

        async def _heartbeat(ws: WebSocket, sd, interval: int = 30):
            try:
                while sd and getattr(sd, "is_active", False):
                    await asyncio.sleep(interval)
                    if getattr(sd, "websocket", None) is ws:
                        await ws.send_text(json.dumps({"type": "ping"}))
            except Exception:
                pass

        hb_task = asyncio.create_task(_heartbeat(websocket, session_data, interval=30))

        while getattr(session_data, "is_active", False):
            try:
                timeout_s = max(120, getattr(config, "WEBSOCKET_TIMEOUT", 60))
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=timeout_s)
                message = json.loads(raw)
                mtype = message.get("type")

                if mtype == "audio_data":
                    asyncio.create_task(session_manager.process_audio_with_silence_status(session_id, message))

                elif mtype == "silence_detected":
                    logger.info("Session %s: received silence notification", session_id)
                    asyncio.create_task(session_manager.process_silence_notification(session_id, message))

                elif mtype == "user_status_update":
                    status = message.get("status", "unknown")
                    logger.debug("Session %s: user status update: %s", session_id, status)

                elif mtype == "default_answer":
                    default_text = message.get("text", "I need more time to think about this.")
                    logger.info("Session %s: default answer: %s", session_id, default_text)
                    asyncio.create_task(session_manager.process_default_answer(session_id, default_text))

                elif mtype == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))

                elif mtype == "heartbeat":
                    await websocket.send_text(json.dumps({"type": "heartbeat_ack"}))

                else:
                    logger.debug("Unknown WS message type: %s", mtype)
                    continue

            except asyncio.TimeoutError:
                logger.debug("WebSocket timeout for session %s - sending keepalive", session_id)
                if getattr(session_data, "is_active", False) and session_data.websocket is websocket:
                    try:
                        await websocket.send_text(json.dumps({"type": "ping"}))
                    except Exception as ping_error:
                        logger.error("Keepalive ping failed: %s", ping_error)
                        break
                continue

            except WebSocketDisconnect:
                logger.info("WebSocket disconnected: %s", session_id)
                if session_data and getattr(session_data, "websocket", None) is websocket:
                    session_data.websocket = None
                break

            except json.JSONDecodeError as json_error:
                logger.error("JSON decode error: %s", json_error)
                try:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "text": "Invalid message format",
                        "status": "error",
                    }))
                except Exception:
                    pass
                continue

            except Exception as e:
                logger.error("Enhanced WebSocket error: %s", e)
                error_message = "Connection error occurred"

                if "silence" in str(e).lower():
                    error_message = "Silence processing error. Please continue speaking."
                    continue
                elif "audio" in str(e).lower():
                    error_message = "Audio processing error. Please try again."
                elif "timeout" in str(e).lower():
                    error_message = "Request timeout. Please try again."

                try:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "text": error_message,
                        "status": "error",
                    }))
                except Exception:
                    pass

                if "critical" in str(e).lower() or "fatal" in str(e).lower():
                    break
                else:
                    continue

    except Exception as e:
        logger.error("Enhanced WebSocket endpoint error: %s", e)

    finally:
        if hb_task and not hb_task.done():
            hb_task.cancel()
        if session_data and getattr(session_data, "websocket", None) is websocket:
            session_data.websocket = None
        logger.info("Enhanced WebSocket cleanup completed for session: %s", session_id)
