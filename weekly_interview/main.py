# -*- coding: utf-8 -*-
"""
Enhanced Mock Interview System - Time-Based Rounds
Communication (10 min) -> Technical (20 min) -> HR (15 min)
Real-time WebSocket interview with adaptive difficulty and silence handling

FIXED: Now properly triggers evaluation when HR round completes
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
                    {"summary": "Fallback summary: The student has been learning programming, working on projects involving data analysis and web development."},
                    {"summary": "Additional context: Recent work includes database integration, API development, and exploring real-time features."}
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
                current_stage=InterviewStage.INTRODUCTION,
                websocket=websocket,
            )

            fragment_manager = EnhancedInterviewFragmentManager(shared_clients, session_data)
            if not fragment_manager.initialize_fragments(summaries):
                raise Exception("Failed to initialize fragments from summaries")

            session_data.fragment_manager = fragment_manager
            self.tts_processor.start_session(session_data.session_id)
            self.active_sessions[session_id] = session_data

            logger.info("Interview session created: %s for %s", session_id, session_data.student_name)
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
                await self._handle_silence(session_data)
                return

            if session_data.exchanges:
                answer_quality = self.conversation_manager._assess_answer_quality(transcript)
                session_data.update_last_response(transcript, quality, answer_quality)

            logger.info("Generating AI response for session %s", session_id)
            ai_response = await self.conversation_manager.generate_fast_response(
                session_data, transcript, self.db_manager
            )
            if not ai_response:
                raise Exception("AI response generation returned empty response")

            # CHECK IF INTERVIEW IS COMPLETE AND TRIGGER EVALUATION
            if session_data.current_stage == InterviewStage.COMPLETE:
                logger.info("Session %s: Interview COMPLETE - triggering evaluation", session_id)
                
                await self._send_quick_message(session_data, {
                    "type": "ai_response",
                    "text": ai_response,
                    "stage": "complete",
                    "status": "completing"
                })
                
                try:
                    async for audio_chunk in self.tts_processor.generate_ultra_fast_stream(
                        ai_response, session_id=session_data.session_id
                    ):
                        if audio_chunk:
                            await self._send_quick_message(session_data, {
                                "type": "audio_chunk",
                                "audio": audio_chunk.hex(),
                                "status": "completing",
                            })
                    await self._send_quick_message(session_data, {"type": "audio_end", "status": "completing"})
                except Exception as tts_error:
                    logger.warning("TTS error during completion: %s", tts_error)
                
                await self._finalize_session_fast(session_data)
                logger.info("Total processing time (with evaluation): %.2fs", time.time() - start_time)
                return

            concept = session_data.current_concept if session_data.current_concept else "general"
            is_followup = self._determine_if_followup(ai_response)
            answer_quality = session_data.last_answer_quality
            session_data.add_exchange(ai_response, "", quality, concept, is_followup, answer_quality)
            
            await self._send_response_with_ultra_fast_audio(session_data, ai_response)
            logger.info("Total processing time: %.2fs", time.time() - start_time)
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
        silence_response = await self.conversation_manager.generate_silence_response(session_data)
        
        await self._send_quick_message(session_data, {
            "type": "silence_prompt",
            "text": silence_response,
            "stage": session_data.current_stage.value,
        })
        
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

    async def _finalize_session_fast(self, session_data: InterviewSession):
        try:
            logger.info("Finalizing session %s - generating evaluation", session_data.session_id)
            
            await self._send_quick_message(session_data, {
                "type": "evaluation_generating",
                "text": "Generating your comprehensive evaluation...",
                "status": "evaluating"
            })
            
            evaluation, scores = await self.conversation_manager.generate_fast_evaluation(session_data)
            if not evaluation:
                raise Exception("Evaluation generation returned empty result")

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
                "followup_questions": session_data.followup_questions,
            }

            await self.db_manager.save_interview_result_fast(interview_data)

            overall_score = scores.get("weighted_overall", 5.0)
            completion_message = (
                f"Thank you {session_data.student_name}! Your interview is complete. "
                f"You scored {overall_score}/10 overall. Great job today!"
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
            logger.info("Session %s finalized with score %.1f/10", session_data.session_id, overall_score)
        except Exception as e:
            logger.error("Session finalization failed: %s", e)
            session_data.is_active = False
            raise Exception(f"Session finalization failed: {e}")

    async def _send_response_with_ultra_fast_audio(self, session_data: InterviewSession, text: str):
        try:
            fragment_manager = session_data.fragment_manager
            time_remaining = fragment_manager.get_round_time_remaining() if fragment_manager else 0
            
            await self._send_quick_message(session_data, {
                "type": "ai_response",
                "text": text,
                "stage": session_data.current_stage.value,
                "question_number": session_data.questions_per_round.get(session_data.current_stage.value, 0),
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
        except Exception as e:
            logger.error("Audio streaming error: %s", e)

    async def _send_quick_message(self, session_data: InterviewSession, message: dict):
        try:
            if session_data.websocket and session_data.is_active:
                await session_data.websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error("WebSocket send error: %s", e)

    async def get_session_result_fast(self, test_id: str) -> dict:
        result = await self.db_manager.get_interview_result_fast(test_id)
        if not result:
            raise Exception(f"Interview {test_id} not found")
        return result


app = FastAPI(
    title=config.APP_TITLE,
    version=config.APP_VERSION,
    description="Weekly Interview System"
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
    try:
        validate_prompts()
        db_manager = DatabaseManager(shared_clients)
        conn = db_manager.get_mysql_connection()
        conn.close()
        await db_manager.get_mongo_client()
        logger.info("All systems ready")
    except Exception as e:
        logger.error("Startup failed: %s", e)
        raise

@app.on_event("shutdown")
async def shutdown_event():
    await shared_clients.close_connections()
    await interview_manager.db_manager.close_connections()

@app.get("/start_interview")
async def start_interview_session():
    try:
        session_data = await interview_manager.create_session_fast()
        first_question = await interview_manager.conversation_manager.generate_first_question(session_data)
        session_data.add_exchange(first_question, "", 0.0, "introduction", False)
        if session_data.fragment_manager:
            session_data.fragment_manager.add_question(first_question, "introduction", False)
        
        return {
            "status": "success",
            "test_id": session_data.test_id,
            "session_id": session_data.session_id,
            "websocket_url": f"/weekly_interview/ws/{session_data.session_id}",
            "first_question": first_question,
            "student_name": session_data.student_name,
            "current_round": "introduction",
        }
    except Exception as e:
        logger.error("Error starting interview: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        session_data = interview_manager.active_sessions.get(session_id)
        if not session_data:
            await websocket.send_text(json.dumps({"type": "error", "text": "Session not found"}))
            return

        session_data.websocket = websocket
        
        if session_data.exchanges:
            first_question = session_data.exchanges[0].ai_message
            await websocket.send_text(json.dumps({
                "type": "ai_response",
                "text": first_question,
                "stage": "introduction",
            }))
            
            async for audio_chunk in interview_manager.tts_processor.generate_ultra_fast_stream(
                first_question, session_id=session_id
            ):
                if audio_chunk:
                    await websocket.send_text(json.dumps({
                        "type": "audio_chunk",
                        "audio": audio_chunk.hex(),
                    }))
            await websocket.send_text(json.dumps({"type": "audio_end"}))

        while session_data.is_active and session_data.current_stage != InterviewStage.COMPLETE:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=config.WEBSOCKET_TIMEOUT)
                message = json.loads(data)
                
                if message.get("type") == "audio_data":
                    audio_b64 = message.get("audio", "")
                    if not audio_b64:
                        await interview_manager._handle_silence(session_data)
                        continue
                    audio_data = base64.b64decode(audio_b64)
                    if len(audio_data) < 100:
                        await interview_manager._handle_silence(session_data)
                        continue
                    await interview_manager.process_audio_ultra_fast(session_id, audio_data)
                    
                    if session_data.current_stage == InterviewStage.COMPLETE:
                        break
                        
                elif message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    
                elif message.get("type") == "manual_stop":
                    session_data.is_active = False
                    break
                    
            except asyncio.TimeoutError:
                break
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error("WebSocket error: %s", e)
                break
                
    except Exception as e:
        logger.error("WebSocket endpoint error: %s", e)
    finally:
        await interview_manager.remove_session(session_id)

@app.websocket("/weekly_interview/ws/{session_id}")
async def websocket_endpoint_alias(websocket: WebSocket, session_id: str):
    await websocket_endpoint(websocket, session_id)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "active_sessions": len(interview_manager.active_sessions)}

@app.get("/download_results/{test_id}")
async def download_results(test_id: str):
    try:
        result = await interview_manager.get_session_result_fast(test_id)
        pdf_buffer = await asyncio.get_event_loop().run_in_executor(
            shared_clients.executor, generate_pdf_report, result, test_id
        )
        return StreamingResponse(
            io.BytesIO(pdf_buffer),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=interview_report_{test_id}.pdf"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def generate_pdf_report(result: Dict[str, Any], test_id: str) -> bytes:
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=LETTER)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph(f"Interview Report - {result.get('student_name', 'Student')}", styles['Title']))
    story.append(Spacer(1, 12))
    
    scores = result.get('scores', {})
    if scores:
        story.append(Paragraph("<b>Scores</b>", styles['Heading2']))
        for key, value in scores.items():
            story.append(Paragraph(f"{key}: {value}/10", styles['Normal']))
        story.append(Spacer(1, 12))
    
    if result.get('evaluation'):
        story.append(Paragraph("<b>Evaluation</b>", styles['Heading2']))
        story.append(Paragraph(result['evaluation'][:2000], styles['Normal']))
    
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer.read()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)