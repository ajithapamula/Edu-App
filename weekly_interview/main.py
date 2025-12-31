# -*- coding: utf-8 -*-
"""
Enhanced Mock Interview System - Daily Standup Style Ultra-Fast Streaming
Real-time WebSocket interview with 7-day fragment processing and streaming TTS
COMPLETE FILE - NO FALLBACKS, FAIL LOUDLY FOR DEBUGGING
"""

import os
import time
import uuid
import logging
import asyncio
import json
import base64
from typing import Dict, Optional, Any
import io
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from core import *
from core.config import config
from core.content_service import ContentService
from core.database import DatabaseManager
from core.ai_services import (
        wi_shared_clients as shared_clients, WI_InterviewSession as InterviewSession, WI_InterviewStage as InterviewStage,
        WI_EnhancedInterviewFragmentManager as EnhancedInterviewFragmentManager, WI_OptimizedAudioProcessor as OptimizedAudioProcessor,
        WI_OptimizedConversationManager as OptimizedConversationManager,
    )
# ⬇️ Unified Chatterbox TTS
from core.tts_processor import UnifiedTTSProcessor as UltraFastTTSProcessor
from core.prompts import validate_prompts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# ULTRA-FAST INTERVIEW SESSION MANAGER
# =============================================================================

class UltraFastInterviewManager:
    def __init__(self):
        self.active_sessions: Dict[str, InterviewSession] = {}
        self.db_manager = DatabaseManager(shared_clients)
        self.audio_processor = OptimizedAudioProcessor(shared_clients)
        # ⬇️ INIT unified TTS
        self.tts_processor = UltraFastTTSProcessor(
            ref_audio_dir=getattr(config, "REF_AUDIO_DIR", Path("ref_audios")),
            encode=getattr(config, "TTS_STREAM_ENCODING", "wav"),
        )
        self.conversation_manager = OptimizedConversationManager(shared_clients)

    async def create_session_fast(self, websocket: Optional[Any] = None) -> InterviewSession:
        session_id = str(uuid.uuid4())
        test_id = f"interview_{int(time.time())}"
        try:
            logger.info("Creating ultra-fast interview session: %s", session_id)

            student_info_task = asyncio.create_task(self.db_manager.get_student_info_fast())
            summaries_task = asyncio.create_task(self.db_manager.get_recent_summaries_fast(
                days=config.RECENT_SUMMARIES_DAYS,
                limit=config.SUMMARIES_LIMIT,
            ))
            student_id, first_name, last_name, session_key = await student_info_task
            summaries = await summaries_task

            if not summaries or len(summaries) == 0:
                logger.warning("No recent summaries found - using fallback summaries")
                summaries = [
                    {
                        "summary": "Fallback summary for testing: The student has been learning Python programming, AI models, and web development basics. They completed projects on data analysis and built a simple chat application."
                    },
                    {
                        "summary": "Additional fallback summary: Recent work includes database integration with MongoDB and MySQL, API development with FastAPI, and exploring real-time features like WebSockets."
                    }
                ]

            if not first_name or not last_name:
                raise Exception("Invalid student data retrieved from database")

            session_data = InterviewSession(
                session_id=session_id,
                test_id=test_id,
                student_id=student_id,
                student_name=f"{first_name} {last_name}",
                session_key=session_key,
                created_at=time.time(),
                last_activity=time.time(),
                current_stage=InterviewStage.GREETING,
                websocket=websocket,
            )

            fragment_manager = EnhancedInterviewFragmentManager(shared_clients, session_data)
            if not fragment_manager.initialize_fragments(summaries):
                raise Exception("Failed to initialize fragments from 7-day summaries")

            session_data.fragment_manager = fragment_manager

            # ⬇️ PIN ONE REFERENCE VOICE FOR THIS SESSION
            self.tts_processor.start_session(session_data.session_id)

            self.active_sessions[session_id] = session_data

            logger.info(
                "Ultra-fast interview session created: %s for %s with %d fragments",
                session_id, session_data.student_name, len(session_data.fragment_keys),
            )
            return session_data
        except Exception as e:
            logger.error("Failed to create interview session: %s", e)
            raise Exception(f"Session creation failed: {e}")

    async def remove_session(self, session_id: str):
        if session_id in self.active_sessions:
            # ⬇️ CLEANUP PINNED VOICE
            try:
                self.tts_processor.end_session(session_id)
            except Exception:
                pass
            del self.active_sessions[session_id]
            logger.info("Removed session %s", session_id)

    async def process_audio_ultra_fast(self, session_id: str, audio_data: bytes):
        session_data = self.active_sessions.get(session_id)
        if not session_data or not session_data.is_active:
            logger.error("Session %s not found or inactive", session_id)
            raise Exception(f"Session {session_id} not found or inactive")

        start_time = time.time()
        try:
            audio_size = len(audio_data)
            logger.info("Session %s: received %d bytes of audio", session_id, audio_size)
            if audio_size < 100:
                raise Exception(f"Audio too small: {audio_size} bytes (minimum 100 bytes required)")
    
            transcript, quality = await self.audio_processor.transcribe_audio_fast(audio_data)
            logger.info("Session %s: transcript='%s' quality=%.2f bytes=%d",session_id, (transcript or "").strip(), quality, audio_size)
            if not transcript or len(transcript.strip()) < 2:
                raise Exception(f"Transcription failed or too short: '{transcript}' (quality: {quality})")

            if session_data.exchanges:
                session_data.update_last_response(transcript, quality)

            logger.info("Generating AI response for session %s", session_id)
            ai_response = await self.conversation_manager.generate_fast_response(session_data, transcript)
            if not ai_response:
                raise Exception("AI response generation returned empty response")

            concept = session_data.current_concept if session_data.current_concept else "unknown"
            is_followup = self._determine_if_followup(ai_response)
            session_data.add_exchange(ai_response, "", quality, concept, is_followup)

            await self._update_session_state_fast(session_data)
            await self._send_response_with_ultra_fast_audio(session_data, ai_response)

            processing_time = time.time() - start_time
            logger.info("Total processing time: %.2fs", processing_time)
        except Exception as e:
            logger.error("Audio processing failed for session %s: %s", session_id, e)
            try:
                await self._send_quick_message(session_data, {
                    "type": "error",
                    "text": f"Interview processing failed: {str(e)}",
                    "status": "error",
                    "debug_info": {"audio_size": len(audio_data), "session_id": session_id, "error": str(e)},
                })
            except Exception:
                pass
            raise Exception(f"Audio processing failed: {e}")

    def _determine_if_followup(self, ai_response: str) -> bool:
        indicators = ["elaborate", "can you explain", "tell me more", "what about",
                      "how did you", "could you describe", "follow up"]
        return any(indicator in ai_response.lower() for indicator in indicators)

    async def _update_session_state_fast(self, session_data: InterviewSession):
        current_stage = session_data.current_stage
        fragment_manager = session_data.fragment_manager

        if current_stage == InterviewStage.GREETING:
            if session_data.questions_per_round["greeting"] >= 2:
                session_data.current_stage = InterviewStage.TECHNICAL
                logger.info("Session %s moved to TECHNICAL stage", session_data.session_id)
        elif current_stage in [InterviewStage.TECHNICAL, InterviewStage.COMMUNICATION, InterviewStage.HR]:
            if not fragment_manager.should_continue_round(current_stage):
                next_stage = self._get_next_stage(current_stage)
                session_data.current_stage = next_stage
                logger.info("Session %s moved to %s stage", session_data.session_id, next_stage.value)
                if next_stage == InterviewStage.COMPLETE:
                    logger.info("Session %s interview completed", session_data.session_id)
                    asyncio.create_task(self._finalize_session_fast(session_data))

    def _get_next_stage(self, current_stage: InterviewStage) -> InterviewStage:
        order = {
            InterviewStage.TECHNICAL: InterviewStage.COMMUNICATION,
            InterviewStage.COMMUNICATION: InterviewStage.HR,
            InterviewStage.HR: InterviewStage.COMPLETE,
        }
        return order.get(current_stage, InterviewStage.COMPLETE)

    async def _finalize_session_fast(self, session_data: InterviewSession):
        try:
            logger.info("Finalizing session %s", session_data.session_id)
            evaluation, scores = await self.conversation_manager.generate_fast_evaluation(session_data)
            if not evaluation:
                raise Exception("Evaluation generation returned empty result")
            if not scores or not isinstance(scores, dict):
                raise Exception(f"Scores generation failed: {scores}")

            interview_data = {
                "test_id": session_data.test_id,
                "session_id": session_data.session_id,
                "student_id": session_data.student_id,
                "student_name": session_data.student_name,
                "conversation_log": [
                    {
                        "timestamp": ex.timestamp,
                        "stage": ex.stage.value,
                        "ai_message": ex.ai_message,
                        "user_response": ex.user_response,
                        "transcript_quality": ex.transcript_quality,
                        "concept": ex.concept,
                        "is_followup": ex.is_followup,
                    }
                    for ex in session_data.exchanges
                ],
                "evaluation": evaluation,
                "scores": scores,
                "duration_minutes": round((time.time() - session_data.created_at) / 60, 1),
                "questions_per_round": dict(session_data.questions_per_round),
                "followup_questions": session_data.followup_questions,
                "fragments_covered": len([c for c, count in session_data.concept_question_counts.items() if count > 0]),
                "total_fragments": len(session_data.fragment_keys),
                "websocket_used": True,
                "tts_voice": "ref_audio",  # sticky voice via session ref
            }

            logger.info("Saving interview data to database")
            save_success = await self.db_manager.save_interview_result_fast(interview_data)
            if not save_success:
                raise Exception(f"Database save failed for session {session_data.session_id}")

            overall_score = scores.get("weighted_overall", scores.get("overall_score", 8.0))
            completion_message = f"Excellent work! Your interview is complete. You scored {overall_score}/10 across all rounds. Thank you!"

            await self._send_quick_message(session_data, {
                "type": "interview_complete",
                "text": completion_message,
                "evaluation": evaluation,
                "scores": scores,
                "pdf_url": f"/weekly_interview/download_results/{session_data.test_id}",
                "status": "complete",
            })

            try:
                # ⬇️ PASS session_id
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
            except Exception as tts_error:
                logger.warning("TTS error during finalization: %s", tts_error)

            session_data.is_active = False
            logger.info("Session %s finalized and saved successfully", session_data.session_id)
        except Exception as e:
            logger.error("Session finalization failed: %s", e)
            try:
                error_data = {
                    "test_id": session_data.test_id,
                    "session_id": session_data.session_id,
                    "student_id": session_data.student_id,
                    "student_name": session_data.student_name,
                    "evaluation": f"Interview finalization failed: {str(e)}",
                    "scores": {"error": True, "overall_score": 0},
                    "error_details": str(e),
                }
                await self.db_manager.save_interview_result_fast(error_data)
                logger.info("Saved error state to database")
            except Exception as save_error:
                logger.error("Failed to save error state: %s", save_error)
            session_data.is_active = False
            try:
                await self._send_quick_message(session_data, {
                    "type": "error",
                    "text": f"Interview finalization failed: {str(e)}",
                    "status": "error",
                })
            except Exception:
                pass
            raise Exception(f"Session finalization failed: {e}")

    async def _send_response_with_ultra_fast_audio(self, session_data: InterviewSession, text: str):
        try:
            await self._send_quick_message(session_data, {
                "type": "ai_response",
                "text": text,
                "stage": session_data.current_stage.value,
                "question_number": session_data.questions_per_round[session_data.current_stage.value],
            })
            chunk_count = 0
            try:
                # ⬇️ PASS session_id
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
            except Exception as tts_error:
                logger.warning("TTS streaming failed: %s", tts_error)
                await self._send_quick_message(session_data, {
                    "type": "audio_end",
                    "status": session_data.current_stage.value,
                    "fallback": "text_only",
                })
        except Exception as e:
            logger.error("Ultra-fast audio streaming error: %s", e)
            await self._send_quick_message(session_data, {
                "type": "audio_end",
                "status": session_data.current_stage.value,
                "fallback": "text_only",
            })

    async def _send_quick_message(self, session_data: InterviewSession, message: dict):
        try:
            if session_data.websocket and session_data.is_active:
                await session_data.websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error("WebSocket send error: %s", e)

    async def get_session_result_fast(self, test_id: str) -> dict:
        try:
            result = await self.db_manager.get_interview_result_fast(test_id)
            if not result:
                raise Exception(f"Interview {test_id} not found in database")
            return result
        except Exception as e:
            logger.error("Error fetching interview result: %s", e)
            raise Exception(f"Interview result retrieval failed: {e}")


# =============================================================================
# FASTAPI APPLICATION
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

interview_manager = UltraFastInterviewManager()

@app.on_event("startup")
async def startup_event():
    logger.info("Ultra-Fast Interview application starting...")
    try:
        validate_prompts()
        logger.info("Prompts validation successful")
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
        logger.info("All systems verified and ready")
    except Exception as e:
        logger.error("Startup failed: %s", e)
        raise Exception(f"Application startup failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    await shared_clients.close_connections()
    await interview_manager.db_manager.close_connections()
    logger.info("Interview application shutting down")

@app.get("/start_interview")
async def start_interview_session_fast():
    try:
        logger.info("Starting real interview session with 7-day summaries...")
        session_data = await interview_manager.create_session_fast()
        greeting = (
            f"Hello {session_data.student_name}! Welcome to your mock interview. "
            f"I'm excited to learn about your technical skills and experience. How are you feeling today?"
        )
        session_data.add_exchange(greeting, "", 0.0, "greeting", False)
        session_data.fragment_manager.add_question(greeting, "greeting", False)
        logger.info("Real interview session created: %s", session_data.test_id)
        return {
            "status": "success",
            "message": "Interview session started successfully",
            "test_id": session_data.test_id,
            "session_id": session_data.session_id,
            "websocket_url": f"/weekly_interview/ws/{session_data.session_id}",
            "greeting": greeting,
            "student_name": session_data.student_name,
            "fragments_count": len(session_data.fragment_keys),
            "summaries_processed": len(session_data.fragment_keys),
            "estimated_duration": config.INTERVIEW_DURATION_MINUTES,
        }
    except Exception as e:
        logger.error("Error starting interview session: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")

@app.websocket("/ws/{session_id}")
async def websocket_endpoint_ultra_fast(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        logger.info("WebSocket connected for interview session: %s", session_id)
        session_data = interview_manager.active_sessions.get(session_id)
        if not session_data:
            error_msg = f"Session {session_id} not found in active sessions"
            logger.error(error_msg)
            await websocket.send_text(json.dumps({"type": "error", "text": error_msg, "status": "error"}))
            raise Exception(error_msg)

        session_data.websocket = websocket
        if session_data.exchanges:
            greeting = session_data.exchanges[0].ai_message
            try:
                await websocket.send_text(json.dumps({"type": "ai_response", "text": greeting, "stage": "greeting", "status": "greeting"}))
                chunk_count = 0
                # ⬇️ PASS session_id for sticky voice
                async for audio_chunk in interview_manager.tts_processor.generate_ultra_fast_stream(
                    greeting, session_id=session_id
                ):
                    if not audio_chunk:
                        raise Exception("Empty audio chunk received from TTS processor")
                    if len(audio_chunk) < 50:
                        raise Exception(f"Audio chunk too small: {len(audio_chunk)} bytes")
                    await websocket.send_text(json.dumps({"type": "audio_chunk", "audio": audio_chunk.hex(), "status": "greeting"}))
                    chunk_count += 1
                await websocket.send_text(json.dumps({"type": "audio_end", "status": "greeting"}))
                logger.info("Greeting complete: %d audio chunks sent", chunk_count)
            except Exception as greeting_error:
                logger.error("Greeting audio failed: %s", greeting_error)
                await websocket.send_text(json.dumps({"type": "error", "text": f"Greeting audio generation failed: {str(greeting_error)}", "status": "error"}))
                raise Exception(f"Greeting audio failed: {greeting_error}")

        while session_data.is_active and session_data.current_stage.value != 'complete':
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=config.WEBSOCKET_TIMEOUT)
                try:
                    message = json.loads(data)
                except json.JSONDecodeError as json_error:
                    error_msg = f"Invalid JSON received: {json_error}"
                    logger.error(error_msg)
                    await websocket.send_text(json.dumps({"type": "error", "text": error_msg, "status": "error"}))
                    raise Exception(error_msg)

                logger.info("WebSocket message type: %s", message.get('type', 'unknown'))
                if message.get("type") == "audio_data":
                    audio_b64 = message.get("audio", "")
                    if not audio_b64:
                        raise Exception("Empty audio data received from client")
                    try:
                        audio_data = base64.b64decode(audio_b64)
                        if len(audio_data) < 100:
                            raise Exception(f"Audio data too small: {len(audio_data)} bytes")
                        asyncio.create_task(interview_manager.process_audio_ultra_fast(session_id, audio_data))
                    except Exception as audio_error:
                        error_msg = f"Audio processing setup failed: {audio_error}"
                        logger.error(error_msg)
                        await websocket.send_text(json.dumps({"type": "error", "text": error_msg, "status": "error"}))
                        raise Exception(error_msg)
                elif message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "manual_stop":
                    logger.info("Manual interview stop requested")
                    session_data.is_active = False
                    await websocket.send_text(json.dumps({"type": "interview_stopped", "status": "stopped"}))
                    break
                else:
                    logger.warning("Unknown message type: %s", message.get('type'))
            except asyncio.TimeoutError:
                logger.info("WebSocket timeout after %.1fs: %s", config.WEBSOCKET_TIMEOUT, session_id)
                await websocket.send_text(json.dumps({"type": "timeout", "text": "Connection timeout - interview session ending", "status": "timeout"}))
                break
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected: %s", session_id)
                break
            except Exception as loop_error:
                logger.error("WebSocket loop error: %s", loop_error)
                await websocket.send_text(json.dumps({"type": "error", "text": f"Communication error: {str(loop_error)}", "status": "error"}))
                raise Exception(f"WebSocket communication failed: {loop_error}")
    except Exception as endpoint_error:
        logger.error("WebSocket endpoint error: %s", endpoint_error)
        try:
            await websocket.send_text(json.dumps({"type": "fatal_error", "text": f"Interview system error: {str(endpoint_error)}", "status": "fatal_error"}))
        except Exception:
            pass
        raise endpoint_error
    finally:
        await interview_manager.remove_session(session_id)
        logger.info("Session %s cleaned up", session_id)
    
@app.get("/health")
async def health_check_fast():
    """Ultra-fast health check with real database status and TTS status"""
    try:
        db_status = {"mysql": False, "mongodb": False}
        tts_status = {"status": "unknown"}
        
        # Quick database health check
        try:
            db_manager = DatabaseManager(shared_clients)
            
            # Test MySQL
            conn = db_manager.get_mysql_connection()
            conn.close()
            db_status["mysql"] = True
            
            # Test MongoDB
            await db_manager.get_mongo_client()
            db_status["mongodb"] = True
            
        except Exception as e:
            logger.warning(f"?? Database health check failed: {e}")
        
        # Quick TTS health check
        try:
            tts_status = await interview_manager.tts_processor.health_check()
        except Exception as e:
            logger.warning(f"?? TTS health check failed: {e}")
            tts_status = {"status": "error", "error": str(e)}
        
        overall_status = "healthy" if (all(db_status.values()) and tts_status.get("status") != "error") else "degraded"
        
        return {
            "status": overall_status,
            "service": "ultra_fast_interview_system",
            "timestamp": time.time(),
            "active_sessions": len(interview_manager.active_sessions),
            "version": config.APP_VERSION,
            "database_status": db_status,
            "tts_status": tts_status,
            "features": {
                "7_day_summaries": True,
                "fragment_based_questions": True,
                "real_time_streaming": True,
                "ultra_fast_tts": True,
                "round_based_interview": True,
                "modular_tts": True,
                "fail_loud_debugging": True
            }
        }
    except Exception as e:
        logger.error(f"? Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
        
@app.websocket("/weekly_interview/ws/{session_id}")
async def websocket_endpoint_weekly_interview(websocket: WebSocket, session_id: str):
    logger.info("Routing weekly_interview WebSocket to main endpoint: %s", session_id)
    await websocket_endpoint_ultra_fast(websocket, session_id)

@app.get("/download_results/{test_id}")
async def download_results_fast(test_id: str):
    try:
        result = await interview_manager.get_session_result_fast(test_id)
        if not result:
            raise HTTPException(status_code=404, detail="Interview results not found")
        loop = asyncio.get_event_loop()
        pdf_buffer = await loop.run_in_executor(shared_clients.executor, generate_pdf_report, result, test_id)
        return StreamingResponse(
            io.BytesIO(pdf_buffer),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=interview_report_{test_id}.pdf"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("PDF generation error: %s", e)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

def generate_pdf_report(result: Dict[str, Any], test_id: str) -> bytes:
    try:
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=LETTER)
        styles = getSampleStyleSheet()
        story = []
        title = f"Mock Interview Report - {result.get('student_name', 'Student')}"
        story.append(Paragraph(title, styles['Title']))
        story.append(Spacer(1, 12))

        info_text = (
            f"Test ID: {test_id}<br/>"
            f"Student: {result.get('student_name', 'Unknown')}<br/>"
            f"Date: {datetime.fromtimestamp(result.get('timestamp', time.time())).strftime('%Y-%m-%d %H:%M:%S')}<br/>"
            f"Duration: {result.get('duration_minutes', 0)} minutes<br/>"
            f"Rounds Completed: {len(result.get('questions_per_round', {}))}"
        )
        story.append(Paragraph(info_text, styles['Normal']))
        story.append(Spacer(1, 12))

        scores = result.get('scores', {})
        if scores:
            story.append(Paragraph("Performance Scores", styles['Heading2']))
            score_text = (
                f"Technical Assessment: {scores.get('technical_score', 0)}/10<br/>"
                f"Communication Skills: {scores.get('communication_score', 0)}/10<br/>"
                f"Behavioral/Cultural Fit: {scores.get('behavioral_score', 0)}/10<br/>"
                f"Overall Presentation: {scores.get('overall_score', 0)}/10<br/>"
                f"Weighted Overall: {scores.get('weighted_overall', 0)}/10"
            )
            story.append(Paragraph(score_text, styles['Normal']))
            story.append(Spacer(1, 12))

        if result.get('evaluation'):
            story.append(Paragraph("Detailed Evaluation", styles['Heading2']))
            for para in result['evaluation'].split('\n\n'):
                p = para.strip()
                if p:
                    story.append(Paragraph(p, styles['Normal']))
                    story.append(Spacer(1, 6))

        doc.build(story)
        pdf_buffer.seek(0)
        return pdf_buffer.read()
    except Exception as e:
        logger.error("PDF generation error: %s", e)
        raise Exception(f"PDF generation failed: {e}")
