# -*- coding: utf-8 -*-
"""
Enhanced Mock Interview System - Time-Based Rounds
Communication (10 min) -> Technical (20 min) -> HR (15 min)
Real-time WebSocket interview with adaptive difficulty and silence handling
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

from core.config import config
from core.database import DatabaseManager
from core.ai_services import (
    wi_shared_clients as shared_clients,
    WI_InterviewSession as InterviewSession,
    WI_InterviewStage as InterviewStage,
    WI_EnhancedInterviewFragmentManager as EnhancedInterviewFragmentManager,
    WI_OptimizedAudioProcessor as OptimizedAudioProcessor,
    WI_OptimizedConversationManager as OptimizedConversationManager,
)
from core.tts_processor import UnifiedTTSProcessor as UltraFastTTSProcessor
from core.prompts import validate_prompts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# INTERVIEW MANAGER - Time-Based Rounds
# =============================================================================

class UltraFastInterviewManager:
    def __init__(self):
        self.active_sessions: Dict[str, InterviewSession] = {}
        self.db_manager = DatabaseManager(shared_clients)
        self.audio_processor = OptimizedAudioProcessor(shared_clients)
        self.tts_processor = UltraFastTTSProcessor(
            ref_audio_dir=getattr(config, "REF_AUDIO_DIR", Path("ref_audios")),
            encode=getattr(config, "TTS_STREAM_ENCODING", "wav"),
        )
        self.conversation_manager = OptimizedConversationManager(shared_clients)

    async def create_session_fast(self, websocket: Optional[Any] = None) -> InterviewSession:
        session_id = str(uuid.uuid4())
        test_id = f"interview_{int(time.time())}"
        try:
            logger.info("Creating interview session: %s", session_id)

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
                        "summary": "Fallback summary: The student has been learning programming, working on projects involving data analysis and web development."
                    },
                    {
                        "summary": "Additional context: Recent work includes database integration, API development, and exploring real-time features."
                    }
                ]

            if not first_name or not last_name:
                raise Exception("Invalid student data retrieved from database")

            # Create session starting with COMMUNICATION stage (not GREETING)
            session_data = InterviewSession(
                session_id=session_id,
                test_id=test_id,
                student_id=student_id,
                student_name=f"{first_name} {last_name}",
                session_key=session_key,
                created_at=time.time(),
                last_activity=time.time(),
                current_stage=InterviewStage.COMMUNICATION,  # Start with Communication
                websocket=websocket,
            )

            fragment_manager = EnhancedInterviewFragmentManager(shared_clients, session_data)
            if not fragment_manager.initialize_fragments(summaries):
                raise Exception("Failed to initialize fragments from summaries")

            session_data.fragment_manager = fragment_manager

            # Pin one reference voice for this session
            self.tts_processor.start_session(session_data.session_id)

            self.active_sessions[session_id] = session_data

            logger.info(
                "Interview session created: %s for %s | Starting with Communication Round (10 min)",
                session_id, session_data.student_name,
            )
            return session_data
        except Exception as e:
            logger.error("Failed to create interview session: %s", e)
            raise Exception(f"Session creation failed: {e}")

    async def remove_session(self, session_id: str):
        if session_id in self.active_sessions:
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
                raise Exception(f"Audio too small: {audio_size} bytes")
    
            transcript, quality = await self.audio_processor.transcribe_audio_fast(audio_data)
            logger.info("Session %s: transcript='%s' quality=%.2f", session_id, (transcript or "").strip()[:50], quality)
            
            if not transcript or len(transcript.strip()) < 2:
                # Handle silence
                await self._handle_silence(session_data)
                return

            if session_data.exchanges:
                # Assess answer quality for adaptive difficulty
                answer_quality = self.conversation_manager._assess_answer_quality(transcript)
                session_data.update_last_response(transcript, quality, answer_quality)

            logger.info("Generating AI response for session %s", session_id)
            ai_response = await self.conversation_manager.generate_fast_response(session_data, transcript)
            if not ai_response:
                raise Exception("AI response generation returned empty response")

            concept = session_data.current_concept if session_data.current_concept else "general"
            is_followup = self._determine_if_followup(ai_response)
            answer_quality = session_data.last_answer_quality
            session_data.add_exchange(ai_response, "", quality, concept, is_followup, answer_quality)

            # Check for round transition
            await self._check_round_transition(session_data)
            
            await self._send_response_with_ultra_fast_audio(session_data, ai_response)

            processing_time = time.time() - start_time
            logger.info("Total processing time: %.2fs", processing_time)
        except Exception as e:
            logger.error("Audio processing failed for session %s: %s", session_id, e)
            try:
                await self._send_quick_message(session_data, {
                    "type": "error",
                    "text": f"Processing error: {str(e)}",
                    "status": "error",
                })
            except Exception:
                pass
            raise Exception(f"Audio processing failed: {e}")

    async def _handle_silence(self, session_data: InterviewSession):
        """Handle candidate silence with gentle prompts"""
        silence_response = await self.conversation_manager.generate_silence_response(session_data)
        
        await self._send_quick_message(session_data, {
            "type": "silence_prompt",
            "text": silence_response,
            "stage": session_data.current_stage.value,
        })
        
        # Send TTS for silence prompt
        try:
            async for audio_chunk in self.tts_processor.generate_ultra_fast_stream(
                silence_response, session_id=session_data.session_id
            ):
                if audio_chunk:
                    await self._send_quick_message(session_data, {
                        "type": "audio_chunk",
                        "audio": audio_chunk.hex(),
                        "status": "silence_prompt",
                    })
            await self._send_quick_message(session_data, {"type": "audio_end", "status": "silence_prompt"})
        except Exception as e:
            logger.warning("TTS error for silence prompt: %s", e)

    def _determine_if_followup(self, ai_response: str) -> bool:
        indicators = ["elaborate", "can you explain", "tell me more", "what about",
                      "how did you", "could you describe", "follow up", "specifically"]
        return any(indicator in ai_response.lower() for indicator in indicators)

    async def _check_round_transition(self, session_data: InterviewSession):
        """Check if current round should end and transition to next"""
        fragment_manager = session_data.fragment_manager
        current_stage = session_data.current_stage
        
        if current_stage == InterviewStage.COMPLETE:
            return
        
        # Check if round should continue
        if fragment_manager.should_continue_round(current_stage):
            return
        
        # Transition to next round
        next_stage = self._get_next_stage(current_stage)
        
        # Generate transition message
        transition_message = await self.conversation_manager.generate_round_transition(
            session_data, next_stage
        )
        
        # Send transition notification
        await self._send_quick_message(session_data, {
            "type": "round_transition",
            "from_stage": current_stage.value,
            "to_stage": next_stage.value,
            "text": transition_message,
            "time_remaining": fragment_manager.get_round_time_remaining(),
        })
        
        # Send TTS for transition
        try:
            async for audio_chunk in self.tts_processor.generate_ultra_fast_stream(
                transition_message, session_id=session_data.session_id
            ):
                if audio_chunk:
                    await self._send_quick_message(session_data, {
                        "type": "audio_chunk",
                        "audio": audio_chunk.hex(),
                        "status": "transition",
                    })
            await self._send_quick_message(session_data, {"type": "audio_end", "status": "transition"})
        except Exception as e:
            logger.warning("TTS error during transition: %s", e)
        
        # Update session stage
        if next_stage == InterviewStage.COMPLETE:
            logger.info("Session %s interview completed", session_data.session_id)
            asyncio.create_task(self._finalize_session_fast(session_data))
        else:
            session_data.start_round(next_stage)
            logger.info("Session %s transitioned to %s round", session_data.session_id, next_stage.value)

    def _get_next_stage(self, current_stage: InterviewStage) -> InterviewStage:
        """Get next stage in the sequence: Communication -> Technical -> HR -> Complete"""
        order = {
            InterviewStage.COMMUNICATION: InterviewStage.TECHNICAL,
            InterviewStage.TECHNICAL: InterviewStage.HR,
            InterviewStage.HR: InterviewStage.COMPLETE,
        }
        return order.get(current_stage, InterviewStage.COMPLETE)

    async def _finalize_session_fast(self, session_data: InterviewSession):
        """Finalize interview with comprehensive evaluation"""
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
                "timestamp": time.time(),
                "conversation_log": [
                    {
                        "timestamp": ex.timestamp,
                        "stage": ex.stage.value,
                        "ai_message": ex.ai_message,
                        "user_response": ex.user_response,
                        "transcript_quality": ex.transcript_quality,
                        "concept": ex.concept,
                        "is_followup": ex.is_followup,
                        "answer_quality": ex.answer_quality,
                    }
                    for ex in session_data.exchanges
                ],
                "evaluation": evaluation,
                "scores": scores,
                "duration_minutes": round((time.time() - session_data.created_at) / 60, 1),
                "questions_per_round": dict(session_data.questions_per_round),
                "round_durations": {
                    stage: session_data.round_start_times.get(stage, 0)
                    for stage in ["communication", "technical", "hr"]
                },
                "followup_questions": session_data.followup_questions,
                "fragments_covered": len([c for c, count in session_data.concept_question_counts.items() if count > 0]),
                "total_fragments": len(session_data.fragment_keys),
            }

            logger.info("Saving interview data to database")
            save_success = await self.db_manager.save_interview_result_fast(interview_data)
            if not save_success:
                logger.warning(f"Database save returned False for session {session_data.session_id}")

            overall_score = scores.get("weighted_overall", 5.0)
            completion_message = (
                f"Thank you {session_data.student_name}! Your interview is complete. "
                f"You scored {overall_score}/10 overall. "
                f"I'll send you a detailed evaluation report. Great job today!"
            )

            await self._send_quick_message(session_data, {
                "type": "interview_complete",
                "text": completion_message,
                "evaluation": evaluation,
                "scores": scores,
                "pdf_url": f"/weekly_interview/download_results/{session_data.test_id}",
                "status": "complete",
            })

            try:
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
            logger.info("Session %s finalized successfully", session_data.session_id)
        except Exception as e:
            logger.error("Session finalization failed: %s", e)
            session_data.is_active = False
            try:
                await self._send_quick_message(session_data, {
                    "type": "error",
                    "text": f"Interview finalization error: {str(e)}",
                    "status": "error",
                })
            except Exception:
                pass
            raise Exception(f"Session finalization failed: {e}")

    async def _send_response_with_ultra_fast_audio(self, session_data: InterviewSession, text: str):
        """Send AI response with streaming audio"""
        try:
            # Include round timing info
            fragment_manager = session_data.fragment_manager
            time_remaining = fragment_manager.get_round_time_remaining() if fragment_manager else 0
            
            await self._send_quick_message(session_data, {
                "type": "ai_response",
                "text": text,
                "stage": session_data.current_stage.value,
                "question_number": session_data.questions_per_round[session_data.current_stage.value],
                "time_remaining_seconds": time_remaining,
                "difficulty": session_data.current_difficulty,
            })
            
            chunk_count = 0
            try:
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
            logger.error("Audio streaming error: %s", e)

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

app = FastAPI(
    title=config.APP_TITLE,
    version=config.APP_VERSION,
    description="Weekly Interview System - Communication -> Technical -> HR (Time-Based Rounds)"
)

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
    logger.info("Weekly Interview System starting...")
    logger.info("Interview Structure: Communication (10min) -> Technical (20min) -> HR (15min)")
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
        logger.info("All systems ready - Interview system online")
    except Exception as e:
        logger.error("Startup failed: %s", e)
        raise Exception(f"Application startup failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    await shared_clients.close_connections()
    await interview_manager.db_manager.close_connections()
    logger.info("Interview application shutting down")

@app.get("/start_interview")
async def start_interview_session():
    """Start a new interview session with Communication -> Technical -> HR flow"""
    try:
        logger.info("Starting new interview session...")
        session_data = await interview_manager.create_session_fast()
        
        # Generate first confidence-building question
        first_question = await interview_manager.conversation_manager.generate_first_question(session_data)
        session_data.add_exchange(first_question, "", 0.0, "introduction", False)
        session_data.fragment_manager.add_question(first_question, "introduction", False)
        
        logger.info("Interview session created: %s", session_data.test_id)
        return {
            "status": "success",
            "message": "Interview session started - Communication Round",
            "test_id": session_data.test_id,
            "session_id": session_data.session_id,
            "websocket_url": f"/weekly_interview/ws/{session_data.session_id}",
            "first_question": first_question,
            "student_name": session_data.student_name,
            "interview_structure": {
                "rounds": [
                    {"name": "Communication", "duration_minutes": 10},
                    {"name": "Technical", "duration_minutes": 20},
                    {"name": "HR", "duration_minutes": 15},
                ],
                "total_duration_minutes": config.INTERVIEW_DURATION_MINUTES,
            },
            "current_round": "communication",
            "estimated_duration": config.INTERVIEW_DURATION_MINUTES,
        }
    except Exception as e:
        logger.error("Error starting interview session: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        logger.info("WebSocket connected for session: %s", session_id)
        session_data = interview_manager.active_sessions.get(session_id)
        if not session_data:
            error_msg = f"Session {session_id} not found"
            logger.error(error_msg)
            await websocket.send_text(json.dumps({"type": "error", "text": error_msg}))
            raise Exception(error_msg)

        session_data.websocket = websocket
        
        # Send first question with audio
        if session_data.exchanges:
            first_question = session_data.exchanges[0].ai_message
            try:
                await websocket.send_text(json.dumps({
                    "type": "ai_response",
                    "text": first_question,
                    "stage": "communication",
                    "status": "communication",
                    "round_info": {
                        "current": "Communication",
                        "duration_minutes": 10,
                        "question_number": 1,
                    }
                }))
                
                chunk_count = 0
                async for audio_chunk in interview_manager.tts_processor.generate_ultra_fast_stream(
                    first_question, session_id=session_id
                ):
                    if audio_chunk:
                        await websocket.send_text(json.dumps({
                            "type": "audio_chunk",
                            "audio": audio_chunk.hex(),
                            "status": "communication"
                        }))
                        chunk_count += 1
                await websocket.send_text(json.dumps({"type": "audio_end", "status": "communication"}))
                logger.info("First question sent: %d audio chunks", chunk_count)
            except Exception as greeting_error:
                logger.error("First question audio failed: %s", greeting_error)
                raise Exception(f"First question failed: {greeting_error}")

        # Main message loop
        while session_data.is_active and session_data.current_stage != InterviewStage.COMPLETE:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=config.WEBSOCKET_TIMEOUT)
                try:
                    message = json.loads(data)
                except json.JSONDecodeError as json_error:
                    logger.error("Invalid JSON: %s", json_error)
                    await websocket.send_text(json.dumps({"type": "error", "text": "Invalid JSON"}))
                    continue

                logger.info("WebSocket message type: %s", message.get('type', 'unknown'))
                
                if message.get("type") == "audio_data":
                    audio_b64 = message.get("audio", "")
                    if not audio_b64:
                        # Handle empty audio as silence
                        await interview_manager._handle_silence(session_data)
                        continue
                    try:
                        audio_data = base64.b64decode(audio_b64)
                        if len(audio_data) < 100:
                            await interview_manager._handle_silence(session_data)
                            continue
                        asyncio.create_task(interview_manager.process_audio_ultra_fast(session_id, audio_data))
                    except Exception as audio_error:
                        logger.error("Audio processing error: %s", audio_error)
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "text": f"Audio error: {audio_error}"
                        }))
                        
                elif message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    
                elif message.get("type") == "get_status":
                    fragment_manager = session_data.fragment_manager
                    await websocket.send_text(json.dumps({
                        "type": "status",
                        "stage": session_data.current_stage.value,
                        "time_elapsed_seconds": session_data.get_round_elapsed_time(),
                        "time_remaining_seconds": fragment_manager.get_round_time_remaining() if fragment_manager else 0,
                        "questions_asked": session_data.questions_per_round.get(session_data.current_stage.value, 0),
                        "difficulty": session_data.current_difficulty,
                    }))
                    
                elif message.get("type") == "manual_stop":
                    logger.info("Manual stop requested")
                    session_data.is_active = False
                    await websocket.send_text(json.dumps({"type": "interview_stopped"}))
                    break
                    
            except asyncio.TimeoutError:
                logger.info("WebSocket timeout: %s", session_id)
                await websocket.send_text(json.dumps({
                    "type": "timeout",
                    "text": "Connection timeout - interview ending"
                }))
                break
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected: %s", session_id)
                break
            except Exception as loop_error:
                logger.error("WebSocket error: %s", loop_error)
                break
                
    except Exception as endpoint_error:
        logger.error("WebSocket endpoint error: %s", endpoint_error)
        try:
            await websocket.send_text(json.dumps({
                "type": "fatal_error",
                "text": f"System error: {str(endpoint_error)}"
            }))
        except Exception:
            pass
    finally:
        await interview_manager.remove_session(session_id)
        logger.info("Session %s cleaned up", session_id)
    
@app.get("/health")
async def health_check():
    """Health check endpoint with interview configuration info"""
    try:
        db_status = {"mysql": False, "mongodb": False}
        tts_status = {"status": "unknown"}
        
        try:
            db_manager = DatabaseManager(shared_clients)
            conn = db_manager.get_mysql_connection()
            conn.close()
            db_status["mysql"] = True
            await db_manager.get_mongo_client()
            db_status["mongodb"] = True
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
        
        try:
            tts_status = await interview_manager.tts_processor.health_check()
        except Exception as e:
            logger.warning(f"TTS health check failed: {e}")
            tts_status = {"status": "error", "error": str(e)}
        
        overall_status = "healthy" if all(db_status.values()) else "degraded"
        
        return {
            "status": overall_status,
            "service": "weekly_interview_system",
            "timestamp": time.time(),
            "active_sessions": len(interview_manager.active_sessions),
            "version": config.APP_VERSION,
            "database_status": db_status,
            "tts_status": tts_status,
            "interview_config": {
                "total_duration_minutes": config.INTERVIEW_DURATION_MINUTES,
                "rounds": {
                    "communication": f"{config.COMMUNICATION_ROUND_DURATION // 60} minutes",
                    "technical": f"{config.TECHNICAL_ROUND_DURATION // 60} minutes",
                    "hr": f"{config.HR_ROUND_DURATION // 60} minutes",
                },
                "round_order": ["Communication", "Technical", "HR"],
                "evaluation_criteria": [
                    "Communication", "Technical", "Leadership", "Behaviour", "Confidence"
                ],
            },
            "features": {
                "time_based_rounds": True,
                "adaptive_difficulty": True,
                "silence_handling": True,
                "real_time_streaming": True,
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.websocket("/weekly_interview/ws/{session_id}")
async def websocket_endpoint_alias(websocket: WebSocket, session_id: str):
    """Alias endpoint for weekly_interview prefix"""
    await websocket_endpoint(websocket, session_id)

@app.get("/download_results/{test_id}")
async def download_results(test_id: str):
    """Download interview results as PDF"""
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
    """Generate comprehensive PDF report with 5 evaluation criteria"""
    try:
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=LETTER)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title = f"Weekly Interview Report - {result.get('student_name', 'Student')}"
        story.append(Paragraph(title, styles['Title']))
        story.append(Spacer(1, 12))

        # Basic Info
        info_text = (
            f"<b>Test ID:</b> {test_id}<br/>"
            f"<b>Student:</b> {result.get('student_name', 'Unknown')}<br/>"
            f"<b>Date:</b> {datetime.fromtimestamp(result.get('timestamp', time.time())).strftime('%Y-%m-%d %H:%M:%S')}<br/>"
            f"<b>Duration:</b> {result.get('duration_minutes', 0)} minutes<br/>"
            f"<b>Rounds Completed:</b> Communication, Technical, HR"
        )
        story.append(Paragraph(info_text, styles['Normal']))
        story.append(Spacer(1, 12))

        # Performance Scores (5 criteria)
        scores = result.get('scores', {})
        if scores:
            story.append(Paragraph("<b>Performance Scores</b>", styles['Heading2']))
            score_text = (
                f"<b>Communication:</b> {scores.get('communication_score', 0)}/10<br/>"
                f"<b>Technical:</b> {scores.get('technical_score', 0)}/10<br/>"
                f"<b>Leadership:</b> {scores.get('leadership_score', 0)}/10<br/>"
                f"<b>Behaviour:</b> {scores.get('behaviour_score', 0)}/10<br/>"
                f"<b>Confidence:</b> {scores.get('confidence_score', 0)}/10<br/>"
                f"<br/><b>Weighted Overall:</b> {scores.get('weighted_overall', 0)}/10"
            )
            story.append(Paragraph(score_text, styles['Normal']))
            story.append(Spacer(1, 12))

        # Questions Per Round
        questions_per_round = result.get('questions_per_round', {})
        if questions_per_round:
            story.append(Paragraph("<b>Questions Per Round</b>", styles['Heading2']))
            rounds_text = (
                f"Communication Round: {questions_per_round.get('communication', 0)} questions<br/>"
                f"Technical Round: {questions_per_round.get('technical', 0)} questions<br/>"
                f"HR Round: {questions_per_round.get('hr', 0)} questions"
            )
            story.append(Paragraph(rounds_text, styles['Normal']))
            story.append(Spacer(1, 12))

        # Detailed Evaluation
        if result.get('evaluation'):
            story.append(Paragraph("<b>Detailed Evaluation</b>", styles['Heading2']))
            for para in result['evaluation'].split('\n\n'):
                p = para.strip()
                if p:
                    # Handle markdown-style headers
                    if p.startswith('**') and p.endswith('**'):
                        story.append(Paragraph(f"<b>{p.strip('*')}</b>", styles['Heading3']))
                    else:
                        story.append(Paragraph(p, styles['Normal']))
                    story.append(Spacer(1, 6))

        doc.build(story)
        pdf_buffer.seek(0)
        return pdf_buffer.read()
    except Exception as e:
        logger.error("PDF generation error: %s", e)
        raise Exception(f"PDF generation failed: {e}")


# Run with: uvicorn weekly_interview:app --reload --port 8001
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)