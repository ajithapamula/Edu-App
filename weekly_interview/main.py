# -*- coding: utf-8 -*-
"""
Enhanced Mock Interview System - Time-Based Rounds
Communication (10 min) -> Technical (20 min) -> HR (15 min)
Real-time WebSocket interview with adaptive difficulty and silence handling

FIXED: Now properly triggers evaluation when HR round completes
FIXED: Removed double add_exchange that caused question number skipping
FIXED: Sends is_repeat flag to frontend for proper question tracking
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

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from reportlab.graphics.shapes import Drawing, Rect, String

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

            # =========================================================================
            # FIXED: Track question count BEFORE generating response to detect if
            # generate_fast_response internally added an exchange
            # =========================================================================
            exchange_count_before = len(session_data.exchanges)
            stage_before = session_data.current_stage

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

            # =========================================================================
            # FIXED Issue 1 & 2: Only add exchange in main.py if generate_fast_response
            # did NOT already add one internally.
            # 
            # generate_fast_response adds exchanges internally for:
            #   - Technical round (all question types)
            #   - HR round (all question types)
            #   - Round transitions (comm->tech, tech->hr)
            #
            # generate_fast_response does NOT add exchanges for:
            #   - Communication round (just returns string)
            #   - Introduction round
            #   - Silence responses (just returns encouragement string)
            #   - Repeat responses
            # =========================================================================
            exchange_count_after = len(session_data.exchanges)
            already_added = exchange_count_after > exchange_count_before
            
            if already_added:
                # generate_fast_response already called add_exchange internally
                # Do NOT add another exchange here
                logger.info("Session %s: Exchange already added by generate_fast_response (before=%d, after=%d), skipping duplicate add_exchange",
                           session_id, exchange_count_before, exchange_count_after)
            else:
                # generate_fast_response did NOT add an exchange (communication, introduction, silence, repeat)
                # We need to add it here
                concept = session_data.current_concept if session_data.current_concept else "general"
                is_followup = self._determine_if_followup(ai_response)
                answer_quality = session_data.last_answer_quality
                session_data.add_exchange(ai_response, "", quality, concept, is_followup, answer_quality)
                logger.info("Session %s: Added exchange from main.py (comm/intro/silence/repeat)", session_id)
            
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
                "evaluation_details": scores.get("evaluation_details", {}),
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
            
            # =========================================================================
            # FIXED Issue 1 & 3: Send is_repeat flag and proper question_number
            # so frontend can track questions correctly and not echo user response
            # =========================================================================
            await self._send_quick_message(session_data, {
                "type": "ai_response",
                "text": text,
                "stage": session_data.current_stage.value,
                "question_number": session_data.questions_per_round.get(session_data.current_stage.value, 0),
                "time_remaining_seconds": time_remaining,
                "difficulty": session_data.current_difficulty,
                "is_repeat": session_data.last_was_repeat,
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
    
def generate_pdf_report(result: dict, test_id: str) -> bytes:
    """
    Professional Interview Evaluation Report PDF Generator.
    
    Replaces the old ~15 line plain-text version.
    Same signature, same return type (bytes), drop-in replacement.
    """
    import io
    from datetime import datetime
    
    pdf_buffer = io.BytesIO()
    
    # ── Page Setup ──────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        leftMargin=20*mm,
        rightMargin=20*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
    )
    
    # ── Color Palette ───────────────────────────────────────────────────────
    PRIMARY      = HexColor("#1a237e")   # Deep indigo
    PRIMARY_LIGHT = HexColor("#e8eaf6")  # Light indigo bg
    ACCENT       = HexColor("#0d47a1")   # Blue
    SUCCESS      = HexColor("#2e7d32")   # Green
    WARNING      = HexColor("#f57f17")   # Amber
    DANGER       = HexColor("#c62828")   # Red
    NEUTRAL      = HexColor("#546e7a")   # Blue-grey
    LIGHT_BG     = HexColor("#f5f5f5")   # Light grey
    DARK_TEXT     = HexColor("#212121")   # Near black
    MED_TEXT      = HexColor("#616161")   # Medium grey
    
    # ── Custom Styles ───────────────────────────────────────────────────────
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        'ReportTitle', parent=styles['Title'],
        fontName='Helvetica-Bold', fontSize=22, textColor=white,
        spaceAfter=6, alignment=TA_LEFT
    ))
    styles.add(ParagraphStyle(
        'ReportSubtitle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=11, textColor=HexColor("#b0bec5"),
        spaceAfter=2, alignment=TA_LEFT
    ))
    styles.add(ParagraphStyle(
        'SectionHeading', parent=styles['Heading2'],
        fontName='Helvetica-Bold', fontSize=14, textColor=PRIMARY,
        spaceBefore=16, spaceAfter=8,
        borderPadding=(0, 0, 4, 0),
    ))
    styles.add(ParagraphStyle(
        'RoundHeading', parent=styles['Heading3'],
        fontName='Helvetica-Bold', fontSize=12, textColor=white,
        spaceBefore=12, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        'QText', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=9.5, textColor=DARK_TEXT,
        spaceBefore=2, spaceAfter=1, leading=13,
    ))
    styles.add(ParagraphStyle(
        'AText', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9.5, textColor=MED_TEXT,
        spaceBefore=1, spaceAfter=1, leading=13,
    ))
    styles.add(ParagraphStyle(
        'FeedbackText', parent=styles['Normal'],
        fontName='Helvetica-Oblique', fontSize=9, textColor=NEUTRAL,
        spaceBefore=1, spaceAfter=4, leading=12,
    ))
    styles.add(ParagraphStyle(
        'BodyText2', parent=styles['Normal'],
        fontName='Helvetica', fontSize=10, textColor=DARK_TEXT,
        spaceBefore=2, spaceAfter=2, leading=14, alignment=TA_JUSTIFY,
    ))
    styles.add(ParagraphStyle(
        'SmallLabel', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, textColor=MED_TEXT,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        'ScoreValue', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=16, textColor=PRIMARY,
        alignment=TA_CENTER,
    ))
    
    story = []
    
    # ── Extract Data ────────────────────────────────────────────────────────
    student_name = result.get("student_name", "Student")
    scores = result.get("scores", {})
    evaluation = result.get("evaluation", "")
    eval_details = result.get("evaluation_details", {})
    duration = result.get("duration_minutes", 0)
    questions_per_round = result.get("questions_per_round", {})
    timestamp = result.get("timestamp", time.time())
    
    try:
        interview_date = datetime.fromtimestamp(timestamp).strftime("%B %d, %Y at %I:%M %p")
    except:
        interview_date = datetime.now().strftime("%B %d, %Y")
    
    overall_score = scores.get("weighted_overall", 5.0)
    
    # Determine grade
    if overall_score >= 8.5:
        grade, grade_color = "Excellent", SUCCESS
    elif overall_score >= 7.0:
        grade, grade_color = "Good", HexColor("#1b5e20")
    elif overall_score >= 5.5:
        grade, grade_color = "Average", WARNING
    elif overall_score >= 4.0:
        grade, grade_color = "Needs Improvement", HexColor("#e65100")
    else:
        grade, grade_color = "Poor", DANGER

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 1: HEADER BANNER
    # ════════════════════════════════════════════════════════════════════════
    header_data = [[
        Paragraph(f"<b>{student_name}</b>", styles['ReportTitle']),
        Paragraph(f"<b>{overall_score}/10</b>", ParagraphStyle(
            'HeaderScore', parent=styles['Normal'],
            fontName='Helvetica-Bold', fontSize=28, textColor=white,
            alignment=TA_RIGHT,
        ))
    ]]
    header_table = Table(header_data, colWidths=[120*mm, 50*mm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, -1), white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 15),
        ('RIGHTPADDING', (-1, -1), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('ROUNDEDCORNERS', [6, 6, 0, 0]),
    ]))
    story.append(header_table)
    
    # Sub-header with meta info
    meta_data = [[
        Paragraph(f"<b>Date:</b> {interview_date}", ParagraphStyle('Meta', fontName='Helvetica', fontSize=8.5, textColor=MED_TEXT)),
        Paragraph(f"<b>Duration:</b> {duration} min", ParagraphStyle('Meta2', fontName='Helvetica', fontSize=8.5, textColor=MED_TEXT)),
        Paragraph(f"<b>Grade:</b> <font color='{grade_color.hexval()}'>{grade}</font>", ParagraphStyle('Meta3', fontName='Helvetica', fontSize=8.5, textColor=MED_TEXT)),
        Paragraph(f"<b>Test ID:</b> {test_id}", ParagraphStyle('Meta4', fontName='Helvetica', fontSize=8.5, textColor=MED_TEXT)),
    ]]
    meta_table = Table(meta_data, colWidths=[48*mm, 35*mm, 42*mm, 45*mm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PRIMARY_LIGHT),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (0, 0), 15),
        ('ROUNDEDCORNERS', [0, 0, 6, 6]),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))
    
    # ════════════════════════════════════════════════════════════════════════
    # SECTION 2: SCORE DASHBOARD
    # ════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("Score Dashboard", styles['SectionHeading']))
    
    score_keys = [
        ("Communication", "communication_score", 0.20),
        ("Technical", "technical_score", 0.30),
        ("Leadership", "leadership_score", 0.15),
        ("Behaviour", "behaviour_score", 0.20),
        ("Confidence", "confidence_score", 0.15),
    ]
    
    def _score_color(val):
        if val >= 8: return SUCCESS
        if val >= 6: return HexColor("#43a047")
        if val >= 4: return WARNING
        return DANGER
    
    def _make_gauge_cell(label, score_val, weight_pct):
        """Create a mini gauge bar for a score dimension"""
        sc = min(max(score_val, 0), 10)
        color = _score_color(sc)
        bar_width = 100  # px
        filled = int(sc / 10 * bar_width)
        
        d = Drawing(bar_width + 10, 14)
        # Background bar
        d.add(Rect(0, 2, bar_width, 10, fillColor=HexColor("#e0e0e0"), strokeColor=None))
        # Filled bar
        if filled > 0:
            d.add(Rect(0, 2, filled, 10, fillColor=color, strokeColor=None))
        # Score text
        d.add(String(bar_width + 3, 3, f"{sc:.1f}", fontName='Helvetica-Bold', fontSize=9, fillColor=color))
        
        return [
            Paragraph(f"<b>{label}</b> <font size='7' color='#9e9e9e'>({int(weight_pct*100)}%)</font>", 
                      ParagraphStyle('GL', fontName='Helvetica-Bold', fontSize=9, textColor=DARK_TEXT)),
            d
        ]
    
    gauge_rows = []
    for label, key, weight in score_keys:
        val = scores.get(key, 5.0)
        gauge_rows.append(_make_gauge_cell(label, val, weight))
    
    # Layout: 2-column grid of gauges + overall score box
    left_col = []
    for row in gauge_rows:
        left_col.append(row)
    
    gauge_table = Table(left_col, colWidths=[55*mm, 50*mm])
    gauge_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (0, -1), 8),
    ]))
    
    # Overall score box
    overall_box_content = [
        [Paragraph(f"<b>{overall_score}</b>", ParagraphStyle('BigScore', fontName='Helvetica-Bold', fontSize=36, textColor=grade_color, alignment=TA_CENTER))],
        [Paragraph("<font size='7'>out of 10</font>", ParagraphStyle('OutOf', fontName='Helvetica', fontSize=7, textColor=MED_TEXT, alignment=TA_CENTER))],
        [Spacer(1, 4)],
        [Paragraph(f"<b>{grade}</b>", ParagraphStyle('GradeLabel', fontName='Helvetica-Bold', fontSize=12, textColor=grade_color, alignment=TA_CENTER))],
    ]
    overall_box = Table(overall_box_content, colWidths=[55*mm])
    overall_box.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 12),
    ]))
    
    dashboard = Table([[gauge_table, overall_box]], colWidths=[110*mm, 60*mm])
    dashboard.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(dashboard)
    story.append(Spacer(1, 8))
    
    # ════════════════════════════════════════════════════════════════════════
    # SECTION 3: KEY METRICS ROW
    # ════════════════════════════════════════════════════════════════════════
    tech_acc = scores.get("technical_accuracy", 0)
    hr_acc = scores.get("hr_accuracy", 0)
    correct = scores.get("questions_correct", 0)
    partial = scores.get("questions_partial", 0)
    wrong = scores.get("questions_wrong", 0)
    silent = scores.get("questions_silent", 0)
    total_qs = scores.get("total_questions", 0)
    
    def _metric_cell(label, value, color=PRIMARY):
        return [
            Paragraph(f"<b>{value}</b>", ParagraphStyle('MV', fontName='Helvetica-Bold', fontSize=16, textColor=color, alignment=TA_CENTER)),
            Paragraph(label, ParagraphStyle('ML', fontName='Helvetica', fontSize=7.5, textColor=MED_TEXT, alignment=TA_CENTER)),
        ]
    
    metrics_row = [
        _metric_cell("Tech Accuracy", f"{tech_acc:.0f}%", SUCCESS if tech_acc >= 70 else (WARNING if tech_acc >= 50 else DANGER)),
        _metric_cell("HR Accuracy", f"{hr_acc:.0f}%", SUCCESS if hr_acc >= 70 else (WARNING if hr_acc >= 50 else DANGER)),
        _metric_cell("Correct", str(correct), SUCCESS),
        _metric_cell("Partial", str(partial), WARNING),
        _metric_cell("Wrong", str(wrong), DANGER),
        _metric_cell("Silent", str(silent), NEUTRAL),
    ]
    
    # Transpose: each metric is a column with 2 rows
    metrics_table_data = [
        [m[0] for m in metrics_row],  # Values
        [m[1] for m in metrics_row],  # Labels
    ]
    
    col_w = 170*mm / 6
    metrics_table = Table(metrics_table_data, colWidths=[col_w]*6)
    metrics_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 6),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
        ('LINEAFTER', (0, 0), (-2, -1), 0.5, HexColor("#e0e0e0")),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 10))
    
    # ════════════════════════════════════════════════════════════════════════
    # SECTION 4: ROUND-BY-ROUND Q&A FEEDBACK
    # ════════════════════════════════════════════════════════════════════════
    
    ROUND_COLORS = {
        "communication": HexColor("#0277bd"),  # Blue
        "technical": HexColor("#2e7d32"),       # Green
        "hr": HexColor("#6a1b9a"),              # Purple
    }
    
    # Get structured evaluation details if available
    rounds_data = eval_details.get("rounds", {}) if eval_details else {}
    
    # If no structured details, parse from the raw evaluation text
    if not rounds_data:
        rounds_data = _parse_evaluation_text_to_rounds(evaluation, result.get("conversation_log", []))
    
    for round_name, round_label in [("communication", "Communication Round"), ("technical", "Technical Round"), ("hr", "HR/Behavioral Round")]:
        round_qs = rounds_data.get(round_name, [])
        if not round_qs:
            continue
        
        round_color = ROUND_COLORS.get(round_name, PRIMARY)
        q_count = questions_per_round.get(round_name, len(round_qs))
        
        # Round header bar
        header_data = [[
            Paragraph(f"<b>{round_label}</b>  <font size='8' color='#e0e0e0'>({q_count} questions)</font>", 
                      ParagraphStyle('RH', fontName='Helvetica-Bold', fontSize=11, textColor=white))
        ]]
        header_tbl = Table(header_data, colWidths=[170*mm])
        header_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), round_color),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('ROUNDEDCORNERS', [4, 4, 0, 0]),
        ]))
        story.append(header_tbl)
        
        # Q&A cards
        for i, qa in enumerate(round_qs):
            question = qa.get("question", "")
            answer = qa.get("answer", "")
            feedback = qa.get("feedback", "")
            accuracy = qa.get("accuracy")
            is_silent = qa.get("is_silent", False)
            
            # Determine answer status color
            if is_silent or not answer or answer.startswith("[SILENT"):
                status_color = DANGER
                status_label = "SILENT"
            elif accuracy is not None:
                if accuracy >= 0.7:
                    status_color = SUCCESS
                    status_label = f"{accuracy:.0%}"
                elif accuracy >= 0.4:
                    status_color = WARNING
                    status_label = f"{accuracy:.0%}"
                else:
                    status_color = DANGER
                    status_label = f"{accuracy:.0%}"
            else:
                status_color = NEUTRAL
                status_label = ""
            
            # Truncate long answers for readability
            display_answer = answer[:300] + "..." if len(answer) > 300 else answer
            
            # Build Q&A card
            card_elements = []
            
            q_prefix = f"<font color='{round_color.hexval()}'><b>Q{i+1}.</b></font> "
            card_elements.append(Paragraph(f"{q_prefix}{_escape_xml(question)}", styles['QText']))
            
            if status_label:
                answer_line = f"<font color='{status_color.hexval()}'>[{status_label}]</font> {_escape_xml(display_answer)}"
            else:
                answer_line = _escape_xml(display_answer)
            card_elements.append(Paragraph(f"<b>A:</b> {answer_line}", styles['AText']))
            
            if feedback:
                card_elements.append(Paragraph(f"<i>Feedback:</i> {_escape_xml(feedback)}", styles['FeedbackText']))
            
            # Card with left accent border
            card_data = [[card_elements]]
            # We use a table trick: first column is thin colored bar, second is content
            inner_content = []
            for elem in card_elements:
                inner_content.append([elem])
            
            inner_table = Table(inner_content, colWidths=[165*mm])
            inner_table.setStyle(TableStyle([
                ('TOPPADDING', (0, 0), (-1, -1), 1),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ]))
            
            card_wrapper = Table([[" ", inner_table]], colWidths=[3*mm, 167*mm])
            card_wrapper.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), round_color),
                ('BACKGROUND', (1, 0), (1, -1), HexColor("#fafafa")),
                ('LEFTPADDING', (1, 0), (1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            # Alternate card bg
            if i % 2 == 1:
                card_wrapper.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), round_color),
                    ('BACKGROUND', (1, 0), (1, -1), white),
                    ('LEFTPADDING', (1, 0), (1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
            
            story.append(card_wrapper)
            story.append(Spacer(1, 2))
        
        story.append(Spacer(1, 8))
    
    # ════════════════════════════════════════════════════════════════════════
    # SECTION 5: OVERALL SUMMARY
    # ════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("Overall Summary", styles['SectionHeading']))
    
    # Extract just the overall summary part (after "OVERALL SUMMARY" header)
    summary_text = ""
    if eval_details and eval_details.get("overall_summary"):
        summary_text = eval_details["overall_summary"]
    else:
        # Parse from raw evaluation text
        if "OVERALL SUMMARY" in evaluation:
            parts = evaluation.split("OVERALL SUMMARY")
            if len(parts) > 1:
                summary_part = parts[1]
                # Get text before STATISTICS
                if "STATISTICS:" in summary_part:
                    summary_text = summary_part.split("STATISTICS:")[0]
                else:
                    summary_text = summary_part[:1500]
                # Clean up separator chars
                summary_text = summary_text.replace("=" * 60, "").replace("-" * 40, "").strip()
    
    if summary_text:
        for para in summary_text.split("\n\n"):
            para = para.strip()
            if para and len(para) > 10:
                story.append(Paragraph(_escape_xml(para), styles['BodyText2']))
                story.append(Spacer(1, 4))
    
    # ════════════════════════════════════════════════════════════════════════
    # SECTION 6: RECOMMENDATIONS (if available)
    # ════════════════════════════════════════════════════════════════════════
    recommendations = eval_details.get("recommendations", []) if eval_details else []
    if recommendations:
        story.append(Paragraph("Recommendations", styles['SectionHeading']))
        for i, rec in enumerate(recommendations, 1):
            story.append(Paragraph(
                f"<font color='{ACCENT.hexval()}'><b>{i}.</b></font> {_escape_xml(rec)}",
                styles['BodyText2']
            ))
            story.append(Spacer(1, 3))
    
    # ════════════════════════════════════════════════════════════════════════
    # FOOTER
    # ════════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#e0e0e0")))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"<font size='7' color='#9e9e9e'>Generated by Lanciere Technologies Pvt Ltd • {interview_date} • Report ID: {test_id}</font>",
        ParagraphStyle('Footer', alignment=TA_CENTER)
    ))
    
    # ── Build PDF ───────────────────────────────────────────────────────────
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer.read()


def _escape_xml(text: str) -> str:
    """Escape XML special characters for ReportLab Paragraphs"""
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
    )

def _parse_evaluation_text_to_rounds(evaluation: str, conversation_log: list) -> dict:
    """
    Parse the raw evaluation text into structured round data.
    
    Falls back to conversation_log if evaluation text doesn't have 
    clear Q&A sections (backward compatibility).
    """
    rounds = {"communication": [], "technical": [], "hr": []}
    
    # Try parsing from evaluation text first
    if evaluation:
        current_round = None
        lines = evaluation.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Detect round headers
            if "COMMUNICATION ROUND" in line.upper():
                current_round = "communication"
            elif "TECHNICAL ROUND" in line.upper():
                current_round = "technical"
            elif "HR" in line.upper() and "ROUND" in line.upper() and "FEEDBACK" in line.upper():
                current_round = "hr"
            elif "OVERALL SUMMARY" in line.upper():
                current_round = None
            
            # Parse Q&A blocks
            if current_round and line.startswith("Q") and ". AI Question:" in line:
                question = line.split("AI Question:", 1)[1].strip() if "AI Question:" in line else line
                answer = ""
                feedback = ""
                accuracy = None
                
                # Look ahead for answer and feedback
                j = i + 1
                while j < len(lines) and j < i + 5:
                    next_line = lines[j].strip()
                    if next_line.startswith("User Answer:"):
                        answer = next_line.split("User Answer:", 1)[1].strip()
                    elif next_line.startswith("Feedback:"):
                        fb_text = next_line.split("Feedback:", 1)[1].strip()
                        # Extract accuracy if present
                        import re
                        acc_match = re.search(r'\(Accuracy:\s*(\d+)%\)', fb_text)
                        if acc_match:
                            accuracy = int(acc_match.group(1)) / 100
                            fb_text = re.sub(r'\s*\(Accuracy:\s*\d+%\)', '', fb_text).strip()
                        feedback = fb_text
                    elif next_line.startswith("Q") and ". AI Question:" in next_line:
                        break
                    elif next_line.startswith("=" * 10):
                        break
                    j += 1
                
                is_silent = "[SILENT" in answer.upper() if answer else True
                
                rounds[current_round].append({
                    "question": question,
                    "answer": answer,
                    "feedback": feedback,
                    "accuracy": accuracy,
                    "is_silent": is_silent,
                })
            
            i += 1
    
    # If parsing didn't find anything, use conversation_log
    total_parsed = sum(len(v) for v in rounds.values())
    if total_parsed == 0 and conversation_log:
        for entry in conversation_log:
            stage = entry.get("stage", "").lower()
            if stage in rounds:
                rounds[stage].append({
                    "question": entry.get("ai_message", ""),
                    "answer": entry.get("user_response", ""),
                    "feedback": "",
                    "accuracy": None,
                    "is_silent": not entry.get("user_response"),
                })
    
    return rounds

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)