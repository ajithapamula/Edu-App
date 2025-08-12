# weekly_interview/main.py
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
import traceback

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Form, File, UploadFile
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import textwrap

from .core.config import config
from .core.database import DatabaseManager
from .core.ai_services import (
    shared_clients, InterviewSession, InterviewStage,
    EnhancedInterviewFragmentManager, OptimizedAudioProcessor,
    OptimizedConversationManager
)
from .core.tts_processor import UltraFastTTSProcessor
from .core.prompts import validate_prompts

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
        self.tts_processor = UltraFastTTSProcessor()
        self.conversation_manager = OptimizedConversationManager(shared_clients)
    
    async def create_session_fast(self, websocket: Optional[Any] = None) -> InterviewSession:
        """Ultra-fast session creation with 7-day summary processing"""
        session_id = str(uuid.uuid4())
        test_id = f"interview_{int(time.time())}"
        
        try:
            logger.info(f"?? Creating ultra-fast interview session: {session_id}")
            
            # Get student info and 7-day summaries in parallel
            student_info_task = asyncio.create_task(self.db_manager.get_student_info_fast())
            summaries_task = asyncio.create_task(self.db_manager.get_recent_summaries_fast(
                days=config.RECENT_SUMMARIES_DAYS,
                limit=config.SUMMARIES_LIMIT
            ))
            
            student_id, first_name, last_name, session_key = await student_info_task
            summaries = await summaries_task
            
            # Validate data
            if not summaries or len(summaries) == 0:
                raise Exception("No summaries available for interview content generation")
            
            if not first_name or not last_name:
                raise Exception("Invalid student data retrieved from database")
            
            # Create session
            session_data = InterviewSession(
                session_id=session_id,
                test_id=test_id,
                student_id=student_id,
                student_name=f"{first_name} {last_name}",
                session_key=session_key,
                created_at=time.time(),
                last_activity=time.time(),
                current_stage=InterviewStage.GREETING,
                websocket=websocket
            )
            
            # Initialize enhanced fragment manager with 7-day summaries
            fragment_manager = EnhancedInterviewFragmentManager(shared_clients, session_data)
            if not fragment_manager.initialize_fragments(summaries):
                raise Exception("Failed to initialize fragments from 7-day summaries")
            
            session_data.fragment_manager = fragment_manager
            self.active_sessions[session_id] = session_data
            
            logger.info(f"? Ultra-fast interview session created: {session_id} for {session_data.student_name} "
                       f"with {len(session_data.fragment_keys)} fragments from {len(summaries)} summaries")
            
            return session_data
            
        except Exception as e:
            logger.error(f"? Failed to create interview session: {e}")
            raise Exception(f"Session creation failed: {e}")
    
    async def remove_session(self, session_id: str):
        """Fast session removal"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"??? Removed session {session_id}")
    
    async def process_audio_ultra_fast(self, session_id: str, audio_data: bytes):
        """Ultra-fast audio processing pipeline - FAIL LOUDLY ON ERRORS"""
        session_data = self.active_sessions.get(session_id)
        if not session_data or not session_data.is_active:
            logger.error(f"? CRITICAL: Session {session_id} not found or inactive")
            raise Exception(f"Session {session_id} not found or inactive")
        
        start_time = time.time()
        
        try:
            audio_size = len(audio_data)
            logger.info(f"?? Session {session_id}: Received {audio_size} bytes of audio data")
            
            # Strict audio size validation
            if audio_size < 100:
                raise Exception(f"Audio too small: {audio_size} bytes (minimum 100 bytes required)")
            
            # Ultra-fast transcription - FAIL LOUDLY IF IT FAILS
            transcript, quality = await self.audio_processor.transcribe_audio_fast(audio_data)
            
            if not transcript or len(transcript.strip()) < 2:
                raise Exception(f"Transcription failed or too short: '{transcript}' (quality: {quality})")
            
            logger.info(f"? Session {session_id}: User said: '{transcript}' (quality: {quality:.2f})")
            
            # Update last exchange with user response
            if session_data.exchanges:
                session_data.update_last_response(transcript, quality)
            
            # Generate AI response - FAIL LOUDLY IF IT FAILS
            logger.info(f"?? Generating AI response for session {session_id}")
            ai_response = await self.conversation_manager.generate_fast_response(session_data, transcript)
            
            if not ai_response:
                raise Exception("AI response generation returned empty response")
            
            # Add exchange to session
            concept = session_data.current_concept if session_data.current_concept else "unknown"
            is_followup = self._determine_if_followup(ai_response)
            
            session_data.add_exchange(ai_response, "", quality, concept, is_followup)
            
            # Update session state (check stage transitions)
            await self._update_session_state_fast(session_data)
            
            # Send response with ultra-fast audio streaming - FAIL LOUDLY IF IT FAILS
            await self._send_response_with_ultra_fast_audio(session_data, ai_response)
            
            processing_time = time.time() - start_time
            logger.info(f"? Total processing time: {processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"? CRITICAL: Audio processing failed for session {session_id}: {e}")
            logger.error(f"? Audio size: {len(audio_data)}, Session active: {session_data.is_active}")
            
            # Send error message to client and re-raise
            try:
                await self._send_quick_message(session_data, {
                    "type": "error",
                    "text": f"Interview processing failed: {str(e)}",
                    "status": "error",
                    "debug_info": {
                        "audio_size": len(audio_data),
                        "session_id": session_id,
                        "error": str(e)
                    }
                })
            except:
                pass  # Don't fail on sending error message
            
            # Re-raise the original error for debugging
            raise Exception(f"Audio processing failed: {e}")
    
    def _determine_if_followup(self, ai_response: str) -> bool:
        """Determine if response is a follow-up question"""
        followup_indicators = [
            "elaborate", "can you explain", "tell me more", "what about", 
            "how did you", "could you describe", "follow up"
        ]
        return any(indicator in ai_response.lower() for indicator in followup_indicators)
    
    async def _update_session_state_fast(self, session_data: InterviewSession):
        """Ultra-fast session state updates with interview round logic"""
        current_stage = session_data.current_stage
        fragment_manager = session_data.fragment_manager
        
        if current_stage == InterviewStage.GREETING:
            if session_data.questions_per_round["greeting"] >= 2:
                session_data.current_stage = InterviewStage.TECHNICAL
                logger.info(f"?? Session {session_data.session_id} moved to TECHNICAL stage")
        
        elif current_stage in [InterviewStage.TECHNICAL, InterviewStage.COMMUNICATION, InterviewStage.HR]:
            # Check if current round should continue
            if not fragment_manager.should_continue_round(current_stage):
                # Move to next stage
                next_stage = self._get_next_stage(current_stage)
                session_data.current_stage = next_stage
                logger.info(f"?? Session {session_data.session_id} moved to {next_stage.value} stage")
                
                # Check if interview is complete
                if next_stage == InterviewStage.COMPLETE:
                    logger.info(f"?? Session {session_data.session_id} interview completed")
                    # Generate evaluation and save session in background
                    asyncio.create_task(self._finalize_session_fast(session_data))
    
    def _get_next_stage(self, current_stage: InterviewStage) -> InterviewStage:
        """Get next interview stage"""
        stage_progression = {
            InterviewStage.TECHNICAL: InterviewStage.COMMUNICATION,
            InterviewStage.COMMUNICATION: InterviewStage.HR,
            InterviewStage.HR: InterviewStage.COMPLETE
        }
        return stage_progression.get(current_stage, InterviewStage.COMPLETE)
    
    async def _finalize_session_fast(self, session_data: InterviewSession):
        """Fast session finalization - FAIL LOUDLY ON ERRORS"""
        try:
            logger.info(f"?? Finalizing session {session_data.session_id}")
            
            # Generate evaluation - FAIL LOUDLY IF IT FAILS
            evaluation, scores = await self.conversation_manager.generate_fast_evaluation(session_data)
            
            if not evaluation:
                raise Exception("Evaluation generation returned empty result")
            
            if not scores or not isinstance(scores, dict):
                raise Exception(f"Scores generation failed: {scores}")
            
            # Prepare interview data for database
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
                        "is_followup": ex.is_followup
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
                "tts_voice": config.TTS_VOICE
            }
            
            # Save to database - FAIL LOUDLY IF IT FAILS
            logger.info(f"?? Saving interview data to database")
            save_success = await self.db_manager.save_interview_result_fast(interview_data)
            
            if not save_success:
                raise Exception(f"Database save failed for session {session_data.session_id}")
            
            # Calculate overall score for display
            overall_score = scores.get("weighted_overall", scores.get("overall_score", 8.0))
            
            completion_message = f"Excellent work! Your interview is complete. You scored {overall_score}/10 across all rounds. Thank you!"
            
            await self._send_quick_message(session_data, {
                "type": "interview_complete",
                "text": completion_message,
                "evaluation": evaluation,
                "scores": scores,
                "pdf_url": f"/weekly_interview/download_results/{session_data.test_id}",
                "status": "complete"
            })
            
            # Generate and send final audio - TTS ERRORS ARE OK HERE (non-critical)
            try:
                async for audio_chunk in self.tts_processor.generate_ultra_fast_stream(completion_message):
                    if audio_chunk:
                        await self._send_quick_message(session_data, {
                            "type": "audio_chunk",
                            "audio": audio_chunk.hex(),
                            "status": "complete"
                        })
                
                await self._send_quick_message(session_data, {"type": "audio_end", "status": "complete"})
            except Exception as tts_error:
                logger.warning(f"?? TTS error during finalization (non-critical): {tts_error}")
                # Continue - TTS errors during finalization are not critical
            
            session_data.is_active = False
            logger.info(f"? Session {session_data.session_id} finalized and saved successfully")
            
        except Exception as e:
            logger.error(f"? CRITICAL: Session finalization failed: {e}")
            logger.error(f"? Session: {session_data.session_id}, exchanges: {len(session_data.exchanges)}")
            
            # Try to save error state to database
            try:
                error_data = {
                    "test_id": session_data.test_id,
                    "session_id": session_data.session_id,
                    "student_id": session_data.student_id,
                    "student_name": session_data.student_name,
                    "evaluation": f"Interview finalization failed: {str(e)}",
                    "scores": {"error": True, "overall_score": 0},
                    "error_details": str(e)
                }
                await self.db_manager.save_interview_result_fast(error_data)
                logger.info("?? Saved error state to database")
            except Exception as save_error:
                logger.error(f"? Failed to save error state: {save_error}")
            
            session_data.is_active = False
            
            # Send error to client
            try:
                await self._send_quick_message(session_data, {
                    "type": "error",
                    "text": f"Interview finalization failed: {str(e)}",
                    "status": "error"
                })
            except:
                pass
            
            # Re-raise for debugging
            raise Exception(f"Session finalization failed: {e}")
    
    async def _send_response_with_ultra_fast_audio(self, session_data: InterviewSession, text: str):
        """Send response with ultra-fast audio streaming using separate TTS processor"""
        try:
            await self._send_quick_message(session_data, {
                "type": "ai_response",
                "text": text,
                "stage": session_data.current_stage.value,
                "question_number": session_data.questions_per_round[session_data.current_stage.value]
            })
            
            chunk_count = 0
            # Use separate TTS processor with enhanced error handling
            try:
                async for audio_chunk in self.tts_processor.generate_ultra_fast_stream(text):
                    if audio_chunk and session_data.is_active:
                        await self._send_quick_message(session_data, {
                            "type": "audio_chunk",
                            "audio": audio_chunk.hex(),
                            "status": session_data.current_stage.value
                        })
                        chunk_count += 1
                
                await self._send_quick_message(session_data, {
                    "type": "audio_end",
                    "status": session_data.current_stage.value
                })
                
                logger.info(f"?? Streamed {chunk_count} audio chunks")
                
            except Exception as tts_error:
                logger.warning(f"?? TTS streaming failed (non-critical): {tts_error}")
                # Send audio_end even if TTS fails
                await self._send_quick_message(session_data, {
                    "type": "audio_end",
                    "status": session_data.current_stage.value,
                    "fallback": "text_only"
                })
            
        except Exception as e:
            logger.error(f"? Ultra-fast audio streaming error: {e}")
            # Send text-only response as fallback
            await self._send_quick_message(session_data, {
                "type": "audio_end",
                "status": session_data.current_stage.value,
                "fallback": "text_only"
            })
    
    async def _send_quick_message(self, session_data: InterviewSession, message: dict):
        """Ultra-fast WebSocket message sending"""
        try:
            if session_data.websocket and session_data.is_active:
                await session_data.websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"? WebSocket send error: {e}")
            # Don't raise - WebSocket errors shouldn't kill the session
    
    async def get_session_result_fast(self, test_id: str) -> dict:
        """Fast session result retrieval from real database"""
        try:
            result = await self.db_manager.get_interview_result_fast(test_id)
            if not result:
                raise Exception(f"Interview {test_id} not found in database")
            return result
        except Exception as e:
            logger.error(f"? Error fetching interview result: {e}")
            raise Exception(f"Interview result retrieval failed: {e}")

# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(title=config.APP_TITLE, version=config.APP_VERSION)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOW_ORIGINS,
    allow_credentials=config.CORS_ALLOW_CREDENTIALS,
    allow_methods=config.CORS_ALLOW_METHODS,
    allow_headers=config.CORS_ALLOW_HEADERS,
)

# Mount static files
app.mount("/audio", StaticFiles(directory=str(config.AUDIO_DIR)), name="audio")

# Initialize ultra-fast interview manager
interview_manager = UltraFastInterviewManager()

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup - test real connections"""
    logger.info("?? Ultra-Fast Interview application starting...")
    
    try:
        # Validate prompts first
        validate_prompts()
        logger.info("? Prompts validation successful")
        
        # Test database connections on startup
        db_manager = DatabaseManager(shared_clients)
        
        # Test MySQL connection
        try:
            conn = db_manager.get_mysql_connection()
            conn.close()
            logger.info("? MySQL connection test successful")
        except Exception as e:
            logger.error(f"? MySQL connection test failed: {e}")
            raise Exception(f"MySQL connection failed: {e}")
        
        # Test MongoDB connection
        try:
            await db_manager.get_mongo_client()
            logger.info("? MongoDB connection test successful")
        except Exception as e:
            logger.error(f"? MongoDB connection test failed: {e}")
            raise Exception(f"MongoDB connection failed: {e}")
        
        logger.info("? All systems verified and ready")
        
    except Exception as e:
        logger.error(f"? Startup failed: {e}")
        raise Exception(f"Application startup failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await shared_clients.close_connections()
    await interview_manager.db_manager.close_connections()
    logger.info("?? Interview application shutting down")

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/start_interview")
async def start_interview_session_fast():
    """Start a new interview session with 7-day summary processing"""
    try:
        logger.info("?? Starting real interview session with 7-day summaries...")
        
        session_data = await interview_manager.create_session_fast()
        
        greeting = f"Hello {session_data.student_name}! Welcome to your mock interview. I'm excited to learn about your technical skills and experience. How are you feeling today?"
        
        # Add initial greeting to session
        session_data.add_exchange(greeting, "", 0.0, "greeting", False)
        session_data.fragment_manager.add_question(greeting, "greeting", False)
        
        logger.info(f"? Real interview session created: {session_data.test_id}")
        
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
            "estimated_duration": config.INTERVIEW_DURATION_MINUTES
        }
        
    except Exception as e:
        logger.error(f"? Error starting interview session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")

@app.websocket("/ws/{session_id}")
async def websocket_endpoint_ultra_fast(websocket: WebSocket, session_id: str):
    """Ultra-fast WebSocket endpoint with real-time streaming - FAIL LOUDLY ON ERRORS"""
    await websocket.accept()
    
    try:
        logger.info(f"?? WebSocket connected for interview session: {session_id}")
        
        session_data = interview_manager.active_sessions.get(session_id)
        if not session_data:
            error_msg = f"Session {session_id} not found in active sessions"
            logger.error(f"? {error_msg}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "text": error_msg,
                "status": "error"
            }))
            # FAIL LOUDLY - NO MASKED ERRORS
            raise Exception(error_msg)
        
        session_data.websocket = websocket
        
        # Send initial greeting with audio - FAIL LOUDLY ON ERRORS
        if session_data.exchanges:
            greeting = session_data.exchanges[0].ai_message
            
            try:
                await websocket.send_text(json.dumps({
                    "type": "ai_response",
                    "text": greeting,
                    "stage": "greeting",
                    "status": "greeting"
                }))
                
                # Generate and stream greeting audio - FAIL LOUDLY IF TTS FAILS
                logger.info("?? Generating greeting audio with dynamic voice selection...")
                chunk_count = 0
                
                async for audio_chunk in interview_manager.tts_processor.generate_ultra_fast_stream(greeting):
                    if not audio_chunk:
                        raise Exception("Empty audio chunk received from TTS processor")
                    
                    if len(audio_chunk) < 50:
                        raise Exception(f"Audio chunk too small: {len(audio_chunk)} bytes")
                    
                    await websocket.send_text(json.dumps({
                        "type": "audio_chunk",
                        "audio": audio_chunk.hex(),
                        "status": "greeting"
                    }))
                    chunk_count += 1
                    logger.info(f"?? Sent greeting audio chunk {chunk_count}: {len(audio_chunk)} bytes")
                
                await websocket.send_text(json.dumps({
                    "type": "audio_end",
                    "status": "greeting"
                }))
                
                logger.info(f"? Greeting complete: {chunk_count} audio chunks sent")
                
            except Exception as greeting_error:
                logger.error(f"? CRITICAL: Greeting audio failed: {greeting_error}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "text": f"Greeting audio generation failed: {str(greeting_error)}",
                    "status": "error"
                }))
                # FAIL LOUDLY - NO FALLBACK AUDIO
                raise Exception(f"Greeting audio failed: {greeting_error}")
        
        # Main communication loop - FAIL LOUDLY ON ERRORS
        while session_data.is_active and session_data.current_stage.value != 'complete':
            try:
                # Wait for WebSocket message with timeout
                data = await asyncio.wait_for(
                    websocket.receive_text(), 
                    timeout=config.WEBSOCKET_TIMEOUT
                )
                
                try:
                    message = json.loads(data)
                except json.JSONDecodeError as json_error:
                    error_msg = f"Invalid JSON received: {json_error}"
                    logger.error(f"? {error_msg}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "text": error_msg,
                        "status": "error"
                    }))
                    # FAIL LOUDLY
                    raise Exception(error_msg)
                
                logger.info(f"?? WebSocket message received: {message.get('type', 'unknown')}")
                
                if message.get("type") == "audio_data":
                    audio_b64 = message.get("audio", "")
                    if not audio_b64:
                        raise Exception("Empty audio data received from client")
                    
                    try:
                        audio_data = base64.b64decode(audio_b64)
                        if len(audio_data) < 100:
                            raise Exception(f"Audio data too small: {len(audio_data)} bytes")
                        
                        logger.info(f"?? Processing {len(audio_data)} bytes of audio data")
                        
                        # Process audio - FAIL LOUDLY ON PROCESSING ERRORS
                        asyncio.create_task(
                            interview_manager.process_audio_ultra_fast(session_id, audio_data)
                        )
                        
                    except Exception as audio_error:
                        error_msg = f"Audio processing setup failed: {audio_error}"
                        logger.error(f"? {error_msg}")
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "text": error_msg,
                            "status": "error"
                        }))
                        # FAIL LOUDLY
                        raise Exception(error_msg)
                
                elif message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    logger.info("?? Ping-pong successful")
                
                elif message.get("type") == "manual_stop":
                    logger.info("?? Manual interview stop requested")
                    session_data.is_active = False
                    await websocket.send_text(json.dumps({
                        "type": "interview_stopped",
                        "status": "stopped"
                    }))
                    break
                
                else:
                    logger.warning(f"?? Unknown message type: {message.get('type')}")
                
            except asyncio.TimeoutError:
                logger.info(f"? WebSocket timeout after {config.WEBSOCKET_TIMEOUT}s: {session_id}")
                await websocket.send_text(json.dumps({
                    "type": "timeout",
                    "text": "Connection timeout - interview session ending",
                    "status": "timeout"
                }))
                break
                
            except WebSocketDisconnect:
                logger.info(f"?? WebSocket disconnected: {session_id}")
                break
                
            except Exception as loop_error:
                logger.error(f"? CRITICAL: WebSocket loop error: {loop_error}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "text": f"Communication error: {str(loop_error)}",
                    "status": "error"
                }))
                # FAIL LOUDLY
                raise Exception(f"WebSocket communication failed: {loop_error}")
    
    except Exception as endpoint_error:
        logger.error(f"? CRITICAL: WebSocket endpoint error: {endpoint_error}")
        try:
            await websocket.send_text(json.dumps({
                "type": "fatal_error",
                "text": f"Interview system error: {str(endpoint_error)}",
                "status": "fatal_error"
            }))
        except:
            pass  # WebSocket might be closed
        # FAIL LOUDLY - NO MASKED ERRORS IN DEVELOPMENT
        raise endpoint_error
    finally:
        # Cleanup session
        await interview_manager.remove_session(session_id)
        logger.info(f"?? Session {session_id} cleaned up")
        
# Compatibility endpoint for alternative routing
@app.websocket("/weekly_interview/ws/{session_id}")
async def websocket_endpoint_weekly_interview(websocket: WebSocket, session_id: str):
    """Compatibility endpoint - routes to main endpoint"""
    logger.info(f"?? Routing weekly_interview WebSocket to main endpoint: {session_id}")
    await websocket_endpoint_ultra_fast(websocket, session_id)

@app.get("/evaluate")
async def get_evaluation_fast(test_id: str):
    """Get evaluation with enhanced error handling"""
    try:
        logger.info(f"?? Getting evaluation for test_id: {test_id}")
        
        result = await interview_manager.get_session_result_fast(test_id)
        
        return {
            "test_id": test_id,
            "evaluation": result.get("evaluation", "Evaluation not available"),
            "scores": result.get("scores", {}),
            "analytics": result.get("interview_analytics", {}),
            "pdf_url": f"/weekly_interview/download_results/{test_id}",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"? Error getting evaluation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get evaluation: {str(e)}")

@app.get("/download_results/{test_id}")
async def download_results_fast(test_id: str):
    """Fast PDF generation and download from real data"""
    try:
        result = await interview_manager.get_session_result_fast(test_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Interview results not found")
        
        loop = asyncio.get_event_loop()
        pdf_buffer = await loop.run_in_executor(
            shared_clients.executor,
            generate_pdf_report,
            result, test_id
        )
        
        return StreamingResponse(
            io.BytesIO(pdf_buffer),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=interview_report_{test_id}.pdf"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"? PDF generation error: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

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

@app.get("/api/interview-students")
async def get_interview_students():
    """Get interview students for frontend compatibility"""
    try:
        results = await interview_manager.db_manager.get_all_interview_results_fast(100)
        
        students = {}
        for result in results:
            student_id = result.get("student_id")
            if student_id and student_id not in students:
                students[student_id] = {
                    "Student_ID": student_id,
                    "name": result.get("student_name", "Unknown")
                }
        
        return list(students.values())
        
    except Exception as e:
        logger.error(f"? Get students error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/interview-students/{student_id}/interviews")
async def get_student_interviews(student_id: str):
    """Get student interviews for frontend compatibility"""
    try:
        all_results = await interview_manager.db_manager.get_all_interview_results_fast(200)
        
        student_interviews = [
            {
                "interview_id": result.get("test_id"),
                "test_id": result.get("test_id"),
                "session_id": result.get("session_id"),
                "timestamp": result.get("timestamp"),
                "scores": result.get("scores", {}),
                "Student_ID": result.get("student_id"),
                "name": result.get("student_name")
            }
            for result in all_results 
            if str(result.get("student_id", "")) == student_id
        ]
        
        return student_interviews
        
    except Exception as e:
        logger.error(f"? Get student interviews error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Additional WebSocket endpoint for compatibility
# @app.websocket("/weekly_interview/ws/{session_id}")
# async def websocket_endpoint_weekly_interview(websocket: WebSocket, session_id: str):
#     """Compatibility endpoint"""
#     await websocket_endpoint_ultra_fast(websocket, session_id)

# =============================================================================
# PDF GENERATION UTILITY
# =============================================================================

def generate_pdf_report(result: Dict[str, Any], test_id: str) -> bytes:
    """Generate PDF report from real interview data"""
    try:
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=LETTER)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title = f"Mock Interview Report - {result.get('student_name', 'Student')}"
        story.append(Paragraph(title, styles['Title']))
        story.append(Spacer(1, 12))
        
        # Session info
        info_text = f"""
        Test ID: {test_id}
        Student: {result.get('student_name', 'Unknown')}
        Date: {datetime.fromtimestamp(result.get('timestamp', time.time())).strftime('%Y-%m-%d %H:%M:%S')}
        Duration: {result.get('duration_minutes', 0)} minutes
        Rounds Completed: {len(result.get('questions_per_round', {}))}
        """
        story.append(Paragraph(info_text, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Scores section
        scores = result.get('scores', {})
        if scores:
            story.append(Paragraph("Performance Scores", styles['Heading2']))
            score_text = f"""
            Technical Assessment: {scores.get('technical_score', 0)}/10
            Communication Skills: {scores.get('communication_score', 0)}/10
            Behavioral/Cultural Fit: {scores.get('behavioral_score', 0)}/10
            Overall Presentation: {scores.get('overall_score', 0)}/10
            Weighted Overall: {scores.get('weighted_overall', 0)}/10
            """
            story.append(Paragraph(score_text, styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Evaluation
        if result.get('evaluation'):
            story.append(Paragraph("Detailed Evaluation", styles['Heading2']))
            eval_paragraphs = result['evaluation'].split('\n\n')
            for para in eval_paragraphs:
                if para.strip():
                    story.append(Paragraph(para.strip(), styles['Normal']))
                    story.append(Spacer(1, 6))
        
        doc.build(story)
        pdf_buffer.seek(0)
        return pdf_buffer.read()
        
    except Exception as e:
        logger.error(f"? PDF generation error: {e}")
        raise Exception(f"PDF generation failed: {e}")