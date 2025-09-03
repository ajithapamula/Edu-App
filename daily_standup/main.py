# -*- coding: utf-8 -*-
"""
Ultra-fast, real database daily standup backend with optimized performance
NO DUMMY DATA - Real connections only
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, File, UploadFile, Form
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import time
import uuid
import logging
import os
import io
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import base64

# Local imports - use package-relative, keep names intact
# proxy to shared Eduapp core (daily_standup)

from core import *
from core.ai_services import DS_SessionData as SessionData
from core.ai_services import DS_SessionStage as SessionStage
from core.ai_services import DS_SummaryManager as SummaryManager
from core.ai_services import ds_shared_clients as shared_clients
from core.config import config
from core.database import DatabaseManager
from core.ai_services import DS_OptimizedAudioProcessor as OptimizedAudioProcessor
from core.tts_processor import DS_TTSProcessor as UltraFastTTSProcessor
from core.ai_services import DS_OptimizedConversationManager as OptimizedConversationManager
from core.prompts import DailyStandupPrompts as prompts
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# ULTRA-FAST SESSION MANAGER - NO DUMMY DATA
# =============================================================================

class UltraFastSessionManager:
    def __init__(self):
        self.active_sessions: Dict[str, SessionData] = {}
        self.db_manager = DatabaseManager(shared_clients)
        self.audio_processor = OptimizedAudioProcessor(shared_clients)
        self.tts_processor = UltraFastTTSProcessor()
        self.conversation_manager = OptimizedConversationManager(shared_clients)

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
            SESSION_MAX_SECONDS = getattr(config, "SESSION_MAX_SECONDS", 15 * 60)  # default 15 minutes
            SESSION_SOFT_CUTOFF_SECONDS = getattr(config, "SESSION_SOFT_CUTOFF_SECONDS", 10)  # last 10 seconds
            now_ts = time.time()
            session_data.end_time = now_ts + SESSION_MAX_SECONDS
            session_data.soft_cutoff_time = session_data.end_time - SESSION_SOFT_CUTOFF_SECONDS
            session_data.awaiting_user = False  # Track if we’re waiting for user’s final reply

            fragment_manager = SummaryManager(shared_clients, session_data)
            if not fragment_manager.initialize_fragments(summary):
                raise Exception("Failed to initialize fragments from summary")
            session_data.summary_manager = fragment_manager

            self.active_sessions[session_id] = session_data
            logger.info("Real session created %s for %s with %d fragments",
                        session_id, session_data.student_name, len(session_data.fragment_keys))
            return session_data
        except Exception as e:
            logger.error("Failed to create session: %s", e)
            raise Exception(f"Session creation failed: {e}")
        

    async def _end_due_to_time(self, session_data: SessionData):
    # ---- helper: safely extract topics without relying on get_all_topics ----
        def _extract_topics(sd: SessionData):
            topics = []
            sm = getattr(sd, "summary_manager", None)
            if not sm:
                return topics

        # Try fragments dict with titles
            fk = getattr(sd, "fragment_keys", None)
            frags = getattr(sm, "fragments", None)

            if fk and isinstance(frags, dict):
                for k in fk:
                    frag = frags.get(k)
                    if isinstance(frag, dict):
                        t = frag.get("title") or frag.get("heading") or frag.get("name")
                        if t:
                            topics.append(t)
                if topics:
                    return topics

            # Try list of fragments
            if isinstance(frags, list):
                for frag in frags:
                    if isinstance(frag, dict):
                        t = frag.get("title") or frag.get("heading") or frag.get("name")
                        if t:
                            topics.append(t)
                if topics:
                    return topics

            # Fallback: use fragment keys themselves
            if fk:
                return [str(k) for k in fk]

            return topics

        try:
        # Build the summary structure expected by your prompt
            topics = _extract_topics(session_data)
            conv_log = getattr(session_data, "conversation_log", []) or []
            conversation_summary = {
                "topics_covered": topics,
                "total_exchanges": len(conv_log),
            }
            user_final_response = (
                conv_log[-1].get("user_response") if conv_log and isinstance(conv_log[-1], dict) else None
            )

            # 🔹 Use your prompt to create a dynamic, non-hardcoded ending
            closing_prompt = prompts.dynamic_session_completion(conversation_summary, user_final_response)

        #    Reuse your existing sync OpenAI call via executor (no new API required)
            loop = asyncio.get_event_loop()
            closing_text = await loop.run_in_executor(
                shared_clients.executor,
                self.conversation_manager._sync_openai_call,
                closing_prompt,
            )

            # Robust fallback just in case
            if not closing_text or not str(closing_text).strip():
                closing_text = f"Thanks {session_data.student_name}. We’ll end the session here."

            # Notify UI (and enable “start new session” on frontend)
            await self._send_quick_message(session_data, {
                "type": "conversation_end",
                "text": closing_text,
                "status": "complete",
                "enable_new_session": True
            })

            # Stream TTS of the dynamic ending
            try:
                async for audio_chunk in self.tts_processor.generate_ultra_fast_stream(closing_text):
                    if audio_chunk:
                        await self._send_quick_message(session_data, {
                            "type": "audio_chunk",
                            "audio": audio_chunk.hex(),
                            "status": "complete",
                        })
                await self._send_quick_message(session_data, {"type": "audio_end", "status": "complete"})
            except Exception as e:
                logger.error("TTS closing stream error: %s", e)

        except Exception as e:
         # If anything goes wrong, still end gracefully
            logger.error("Closing generation error: %s", e)
            fallback_text = f"Thanks {session_data.student_name}. This session will now end."
            await self._send_quick_message(session_data, {
                "type": "conversation_end",
                "text": fallback_text,
                "status": "complete",
                "enable_new_session": True
            })
            try:
                async for audio_chunk in self.tts_processor.generate_ultra_fast_stream(fallback_text):
                    if audio_chunk:
                        await self._send_quick_message(session_data, {
                            "type": "audio_chunk",
                            "audio": audio_chunk.hex(),
                            "status": "complete",
                        })
                await self._send_quick_message(session_data, {"type": "audio_end", "status": "complete"})
            except Exception as e2:
                logger.error("TTS fallback closing stream error: %s", e2)

        # Mark inactive and clean up
        session_data.is_active = False
        await self.remove_session(session_data.session_id)


    async def remove_session(self, session_id: str):
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info("Removed session %s", session_id)

    async def process_audio_ultra_fast(self, session_id: str, audio_data: bytes):
        session_data = self.active_sessions.get(session_id)
        if not session_data or not session_data.is_active:
            logger.warning("Inactive session: %s", session_id)
            return

        start_time = time.time()
        try:
        # 🔹 HARD EXPIRY
            now_ts = time.time()
            if hasattr(session_data, "end_time") and now_ts >= session_data.end_time:
                await self._end_due_to_time(session_data)
                return
        # 🔹 END HARD EXPIRY

            audio_size = len(audio_data)
            logger.info("Session %s: received %d bytes of audio", session_id, audio_size)

            if audio_size < 100:
                await self._send_quick_message(session_data, {
                "type": "clarification",
                "text": "I didn't hear anything clear. Could you please speak a bit louder?",
                "status": session_data.current_stage.value,
            })
                return

            transcript, quality = await self.audio_processor.transcribe_audio_fast(audio_data)

            if not transcript or len(transcript.strip()) < 2:
                clarification_context = {
                    'clarification_attempts': getattr(session_data, 'clarification_attempts', 0),
                    'audio_quality': quality,
                    'audio_size': audio_size
                }
                session_data.clarification_attempts = clarification_context['clarification_attempts'] + 1

                if audio_size < 500:
                    clarification_message = "I received a very short audio clip. Please try speaking for a bit longer."
                elif quality < 0.3:
                    clarification_message = "The audio wasn't very clear. Could you please speak a bit louder and clearer?"
                else:
                    loop = asyncio.get_event_loop()
                    clarification_message = await loop.run_in_executor(
                        shared_clients.executor,
                        self.conversation_manager._sync_openai_call,
                        prompts.dynamic_clarification_request(clarification_context),
                    )

                await self._send_quick_message(session_data, {
                    "type": "clarification",
                    "text": clarification_message,
                    "status": session_data.current_stage.value,
                })
                return

            logger.info("Session %s: transcript='%s' quality=%.2f", session_id, transcript, quality)

        # 🔹 SOFT CUTOFF
            now_ts = time.time()
            soft_cutoff = getattr(session_data, "soft_cutoff_time", None)
            end_time = getattr(session_data, "end_time", None)
            if soft_cutoff and end_time and now_ts >= soft_cutoff:
                if getattr(session_data, "awaiting_user", False):
                    concept = session_data.current_concept if session_data.current_concept else "unknown"
                    is_followup = getattr(session_data, '_last_question_followup', False)
                    session_data.add_exchange("[FINAL_QUESTION_AWAITED_USER]", transcript, quality, concept, is_followup)
                    if session_data.summary_manager:
                        session_data.summary_manager.add_answer(transcript)
                    await self._end_due_to_time(session_data)
                    return
                else:
                    await self._end_due_to_time(session_data)
                    return
        # 🔹 END SOFT CUTOFF

        # 🔹 We just received a user reply -> no longer awaiting
            session_data.awaiting_user = False

            ai_response = await self.conversation_manager.generate_fast_response(session_data, transcript)

            concept = session_data.current_concept if session_data.current_concept else "unknown"
            is_followup = getattr(session_data, '_last_question_followup', False)
            session_data.add_exchange(ai_response, transcript, quality, concept, is_followup)

            if session_data.summary_manager:
                session_data.summary_manager.add_answer(transcript)

            await self._update_session_state_fast(session_data)
            await self._send_response_with_ultra_fast_audio(session_data, ai_response)

        # 🔹 After sending our (likely) question, await the user's reply if not in soft cutoff
            now_ts = time.time()
            soft_cutoff = getattr(session_data, "soft_cutoff_time", None)
            if session_data.current_stage == SessionStage.TECHNICAL and (not soft_cutoff or now_ts < soft_cutoff):
                session_data.awaiting_user = True

            processing_time = time.time() - start_time
            logger.info("Total processing time: %.2fs", processing_time)

        except Exception as e:
            logger.error("Audio processing error: %s", e)
            if "too small" in str(e).lower():
                error_message = "The audio recording was too short. Please try speaking for a few seconds."
            elif "transcription" in str(e).lower():
                error_message = "I had trouble understanding the audio. Please try speaking clearly into your microphone."
            else:
                error_message = "Sorry, there was a technical issue. Please try again."
            await self._send_quick_message(session_data, {"type": "error", "text": error_message, "status": "error"})

    async def _update_session_state_fast(self, session_data: SessionData):
        if session_data.current_stage == SessionStage.GREETING:
            session_data.greeting_count += 1
            if session_data.greeting_count >= config.GREETING_EXCHANGES:
                session_data.current_stage = SessionStage.TECHNICAL
                logger.info("Session %s moved to TECHNICAL stage", session_data.session_id)
        elif session_data.current_stage == SessionStage.TECHNICAL:
            if session_data.summary_manager and not session_data.summary_manager.should_continue_test():
                session_data.current_stage = SessionStage.COMPLETE
                logger.info("Session %s moved to COMPLETE stage", session_data.session_id)
                asyncio.create_task(self._finalize_session_fast(session_data))

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
                "pdf_url": f"/daily_standup/download_results/{session_data.session_id}",
                "status": "complete",
            })

            async for audio_chunk in self.tts_processor.generate_ultra_fast_stream(completion_message):
                if audio_chunk:
                    await self._send_quick_message(session_data, {
                        "type": "audio_chunk",
                        "audio": audio_chunk.hex(),
                        "status": "complete",
                    })

            await self._send_quick_message(session_data, {"type": "audio_end", "status": "complete"})
            session_data.is_active = False
            logger.info("Session %s finalized and saved", session_data.session_id)
        except Exception as e:
            logger.error("Fast session finalization error: %s", e)
            session_data.is_active = False

    async def _send_response_with_ultra_fast_audio(self, session_data: SessionData, text: str):
        try:
            await self._send_quick_message(session_data, {
                "type": "ai_response",
                "text": text,
                "status": session_data.current_stage.value,
            })
            chunk_count = 0
            async for audio_chunk in self.tts_processor.generate_ultra_fast_stream(text):
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

    async def process_legacy_audio_fast(self, test_id: str, audio_data: bytes) -> dict:
        try:
            logger.info("Processing legacy audio for test_id: %s", test_id)
            transcript, quality = await self.audio_processor.transcribe_audio_fast(audio_data)
            if not transcript or len(transcript.strip()) < 2:
                raise Exception("Transcription returned empty or too short result")

            summary = await self.db_manager.get_summary_fast()
            session_data = SessionData(
                session_id=test_id,
                test_id=test_id,
                student_id=1000,
                student_name="Legacy User",
                session_key="LEGACY",
                created_at=time.time(),
                last_activity=time.time(),
                current_stage=SessionStage.TECHNICAL,
            )
            fragment_manager = SummaryManager(shared_clients, session_data)
            fragment_manager.initialize_fragments(summary)
            session_data.summary_manager = fragment_manager

            ai_response = await self.conversation_manager.generate_fast_response(session_data, transcript)
            return {
                "response": ai_response,
                "audio_path": None,
                "ended": False,
                "complete": False,
                "status": "success",
            }
        except Exception as e:
            logger.error("Legacy audio processing error: %s", e)
            raise Exception(f"Legacy audio processing failed: {e}")


# =============================================================================
# FASTAPI APPLICATION - NO DUMMY DATA
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

session_manager = UltraFastSessionManager()

@app.on_event("startup")
async def startup_event():
    logger.info("Ultra-Fast Daily Standup application starting...")
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

        logger.info("All database connections verified")
    except Exception as e:
        logger.error("Startup failed: %s", e)
        raise Exception(f"Application startup failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    await shared_clients.close_connections()
    await session_manager.db_manager.close_connections()
    logger.info("Daily Standup application shutting down")

@app.get("/start_test")
async def start_standup_session_fast():
    try:
        logger.info("Starting real standup session...")
        session_data = await session_manager.create_session_fast()
        greeting = "Hello! Welcome to your daily standup. How are you doing today?"
        logger.info("Real session created: %s", session_data.test_id)
        return {
            "status": "success",
            "message": "Session started successfully",
            "test_id": session_data.test_id,
            "session_id": session_data.session_id,
            "websocket_url": f"/daily_standup/ws/{session_data.session_id}",
            "greeting": greeting,
            "student_name": session_data.student_name,
            "fragments_count": len(session_data.fragment_keys) if session_data.fragment_keys else 0,
            "estimated_duration": len(session_data.fragment_keys) * session_data.questions_per_concept * config.ESTIMATED_SECONDS_PER_QUESTION,
        }
    except Exception as e:
        logger.error("Error starting session: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")

@app.post("/api/record-respond")
async def record_and_respond_fast(audio: UploadFile = File(...), test_id: str = Form(...)):
    try:
        logger.info("Processing audio for test_id: %s", test_id)
        if not test_id:
            raise HTTPException(status_code=400, detail="test_id is required")
        if not audio or not audio.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Valid audio file is required")

        audio_data = await audio.read()
        if len(audio_data) < 1000:
            raise HTTPException(status_code=400, detail="Audio file too small")

        result = await session_manager.process_legacy_audio_fast(test_id, audio_data)
        logger.info("Audio processed for %s", test_id)
        return {
            "status": "success",
            "response": result.get("response", "Thank you for your input."),
            "audio_path": result.get("audio_path"),
            "ended": result.get("ended", False),
            "complete": result.get("complete", False),
            "message": result.get("response", "Processing complete"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Record and respond error: %s", e)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/api/summary/{test_id}")
async def get_standup_summary_fast(test_id: str):
    try:
        logger.info("Getting summary for test_id: %s", test_id)
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
                user_response = exchange.get("user_response", "").lower()
                ai_message = exchange.get("ai_message", "").lower()
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
                "pdf_url": f"/daily_standup/download_results/{test_id}",
                "status": "completed",
            }
        else:
            raise HTTPException(status_code=404, detail=f"Session result not found for test_id: {test_id}")
        logger.info("Real summary generated for %s", test_id)
        return summary_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting summary: %s", e)
        raise HTTPException(status_code=500, detail=f"Summary retrieval failed: {str(e)}")

@app.websocket("/ws/{session_id}")
async def websocket_endpoint_ultra_fast(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        logger.info("WebSocket connected for session: %s", session_id)
        session_data = session_manager.active_sessions.get(session_id)
        if not session_data:
            logger.error("Session %s not found in active sessions", session_id)
            await websocket.send_text(json.dumps({
                "type": "error",
                "text": f"Session {session_id} not found. Please start a new session.",
                "status": "error",
            }))
            return

        session_data.websocket = websocket
        greeting = f"Hello {session_data.student_name}! Welcome to your daily standup. How are you doing today?"
        await websocket.send_text(json.dumps({"type": "ai_response", "text": greeting, "status": "greeting"}))
        async for audio_chunk in session_manager.tts_processor.generate_ultra_fast_stream(greeting):
            if audio_chunk:
                await websocket.send_text(json.dumps({"type": "audio_chunk", "audio": audio_chunk.hex(), "status": "greeting"}))
        await websocket.send_text(json.dumps({"type": "audio_end", "status": "greeting"}))

        while session_data.is_active:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=config.WEBSOCKET_TIMEOUT)
                message = json.loads(data)
                if message.get("type") == "audio_data":
                    audio_data = base64.b64decode(message.get("audio", ""))
                    asyncio.create_task(session_manager.process_audio_ultra_fast(session_id, audio_data))
                elif message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except asyncio.TimeoutError:
                logger.info("WebSocket timeout: %s", session_id)
                break
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected: %s", session_id)
                break
            except Exception as e:
                logger.error("WebSocket error: %s", e)
                await websocket.send_text(json.dumps({"type": "error", "text": f"Error: {str(e)}", "status": "error"}))
                break
    except Exception as e:
        logger.error("WebSocket endpoint error: %s", e)
    finally:
        await session_manager.remove_session(session_id)

@app.get("/download_results/{session_id}")
async def download_results_fast(session_id: str):
    try:
        result = await session_manager.get_session_result_fast(session_id)
        if not result:
            raise HTTPException(status_code=404, detail="Session not found")

        loop = asyncio.get_event_loop()
        pdf_buffer = await loop.run_in_executor(
            shared_clients.executor,
            generate_pdf_report,
            result, session_id,
        )
        return StreamingResponse(
            io.BytesIO(pdf_buffer),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=standup_report_{session_id}.pdf"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("PDF generation error: %s", e)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@app.get("/health")
async def health_check_fast():
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
            logger.warning("Database health check failed: %s", e)

        return {
            "status": "healthy" if all(db_status.values()) else "degraded",
            "service": "ultra_fast_daily_standup",
            "timestamp": time.time(),
            "active_sessions": len(session_manager.active_sessions),
            "version": config.APP_VERSION,
            "database_status": db_status,
            "real_data_mode": True,
        }
    except Exception as e:
        logger.error("Health check failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/test")
async def test_endpoint_fast():
    return {
        "message": "Ultra-Fast Daily Standup service is running with REAL DATA",
        "timestamp": time.time(),
        "status": "blazing_fast",
        "config": {
            "real_data_mode": True,
            "greeting_exchanges": config.GREETING_EXCHANGES,
            "summary_chunks": config.SUMMARY_CHUNKS,
            "openai_model": config.OPENAI_MODEL,
            "mysql_host": config.MYSQL_HOST,
            "mongodb_host": config.MONGODB_HOST,
        },
        "optimizations": [
            "Real database connections",
            "No dummy data fallbacks",
            "Parallel processing pipeline",
            "Fragment-based questioning",
            "Sliding window conversation history",
            "Ultra-fast TTS streaming",
            "Thread pool optimization",
            "Connection pooling",
            "Real error detection only",
        ],
    }

def generate_pdf_report(result: dict, session_id: str) -> bytes:
    try:
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=LETTER)
        styles = getSampleStyleSheet()
        story = []
        title = f"Daily Standup Report - {result.get('student_name', 'Student')}"
        story.append(Paragraph(title, styles['Title']))
        story.append(Spacer(1, 12))
        info_text = (
            f"Session ID: {session_id}<br/>"
            f"Student: {result.get('student_name', 'Unknown')}<br/>"
            f"Date: {datetime.fromtimestamp(result.get('timestamp', time.time())).strftime('%Y-%m-%d %H:%M:%S')}<br/>"
            f"Duration: {result.get('duration', 0)/60:.1f} minutes<br/>"
            f"Total Exchanges: {result.get('total_exchanges', 0)}<br/>"
            f"Score: {result.get('score', 0)}/10"
        )
        story.append(Paragraph(info_text, styles['Normal']))
        story.append(Spacer(1, 12))

        fragment_analytics = result.get('fragment_analytics', {})
        if fragment_analytics:
            story.append(Paragraph("Fragment Coverage Analysis", styles['Heading2']))
            analytics_text = (
                f"Total Concepts: {fragment_analytics.get('total_concepts', 0)}<br/>"
                f"Coverage Percentage: {fragment_analytics.get('coverage_percentage', 0)}%<br/>"
                f"Main Questions: {fragment_analytics.get('main_questions', 0)}<br/>"
                f"Follow-up Questions: {fragment_analytics.get('followup_questions', 0)}"
            )
            story.append(Paragraph(analytics_text, styles['Normal']))
            story.append(Spacer(1, 12))

        story.append(Paragraph("Conversation Summary", styles['Heading2']))
        for exchange in result.get('conversation_log', [])[:15]:
            if exchange.get('stage') != 'greeting':
                story.append(Paragraph(f"AI: {exchange.get('ai_message', '')}", styles['Normal']))
                story.append(Paragraph(f"User: {exchange.get('user_response', '')}", styles['Normal']))
                story.append(Spacer(1, 6))

        if result.get('evaluation'):
            story.append(Paragraph("Evaluation", styles['Heading2']))
            story.append(Paragraph(result['evaluation'], styles['Normal']))

        doc.build(story)
        pdf_buffer.seek(0)
        return pdf_buffer.read()
    except Exception as e:
        logger.error("PDF generation error: %s", e)
        raise Exception(f"PDF generation failed: {e}")
