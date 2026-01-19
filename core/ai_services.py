# Edu-app/core/ai_services.py
# Unified AI services for: daily_standup, weekly_interview, weekend_mocktest
# - Keeps weekend_mocktest API names intact (AIService, get_ai_service)
# - Namespaces overlapping classes for daily_standup (DS_*) and weekly_interview (WI_*)
# - Weekly Interview UPDATED: Communication -> Technical -> HR with time-based rounds

import os
import time
import logging
import asyncio
import re
import uuid
import json
import random
import tempfile
import io
from typing import List, AsyncGenerator, Tuple, Optional, Dict, Any
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

# ---- External clients (both sync & async variants) ----
import openai as openai_sync
from groq import Groq, AsyncGroq
from openai import AsyncOpenAI

from .config import config
from .prompts import (
    prompts as ds_prompts,
    # weekly_interview prompt helpers (UPDATED):
    build_stage_prompt, build_conversation_prompt, build_evaluation_prompt,
    build_silence_prompt,
    ACKNOWLEDGMENT_PHRASES, TRANSITION_PHRASES, ENCOURAGEMENT_PHRASES,
    CLARIFICATION_PROMPTS, GENTLE_REDIRECT_PROMPTS, SILENCE_GENTLE_PROMPTS,
    SCORING_PROMPT_TEMPLATE,
    # weekend_mocktest templates:
    PromptTemplates
)

logger = logging.getLogger(__name__)

# =============================================================================
# DAILY STANDUP NAMESPACE (DS_*) - UNCHANGED
# =============================================================================

def _ds_parse_summary_into_fragments(summary: str) -> Dict[str, str]:
    """Daily-standup original fragment parser (kept identical)."""
    if not summary or not summary.strip():
        return {"General": summary or "No content available"}
    lines = summary.strip().split('\n')
    section_pattern = re.compile(r'^\s*(\d+)\.\s+(.+)')
    fragments = {}
    current_section = None
    current_content = []
    for line in lines:
        match = section_pattern.match(line)
        if match:
            if current_section and current_content:
                fragments[current_section] = '\n'.join(current_content).strip()
            section_num = match.group(1)
            section_title = match.group(2).strip()
            current_section = f"{section_num}. {section_title}"
            current_content = [line]
        else:
            if current_section:
                current_content.append(line)
            else:
                fragments["Introduction"] = (fragments.get("Introduction", "") + '\n' + line).strip()
    if current_section and current_content:
        fragments[current_section] = '\n'.join(current_content).strip()
    if not fragments:
        fragments["General"] = summary
    logger.info(f"[DS] Parsed summary into {len(fragments)} fragments: {list(fragments.keys())}")
    return fragments


class DS_SessionStage(Enum):
    GREETING = "greeting"
    TECHNICAL = "technical"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class DS_ConversationExchange:
    timestamp: float
    stage: DS_SessionStage
    ai_message: str
    user_response: str
    transcript_quality: float = 0.0
    chunk_id: Optional[int] = None
    concept: Optional[str] = None
    is_followup: bool = False


@dataclass
class DS_SessionData:
    session_id: str
    test_id: str
    student_id: int
    student_name: str
    session_key: str
    created_at: float
    last_activity: float
    current_stage: DS_SessionStage
    exchanges: List[DS_ConversationExchange] = field(default_factory=list)
    conversation_window: deque = field(default_factory=lambda: deque(maxlen=config.CONVERSATION_WINDOW_SIZE))
    greeting_count: int = 0
    is_active: bool = True
    websocket: Optional[Any] = field(default=None)
    summary_manager: Optional[Any] = field(default=None)
    clarification_attempts: int = 0

    fragments: Dict[str, str] = field(default_factory=dict)
    fragment_keys: List[str] = field(default_factory=list)
    concept_question_counts: Dict[str, int] = field(default_factory=dict)
    questions_per_concept: int = 2
    current_concept: str = ""
    question_index: int = 0
    followup_questions: int = 0

    def add_exchange(self, ai_message: str, user_response: str, quality: float = 0.0,
                     chunk_id: Optional[int] = None, concept: Optional[str] = None,
                     is_followup: bool = False):
        ex = DS_ConversationExchange(
            timestamp=time.time(),
            stage=self.current_stage,
            ai_message=ai_message,
            user_response=user_response,
            transcript_quality=quality,
            chunk_id=chunk_id,
            concept=concept,
            is_followup=is_followup
        )
        self.exchanges.append(ex)
        self.conversation_window.append(ex)
        self.last_activity = time.time()


@dataclass
class DS_SummaryChunk:
    id: int
    content: str
    base_questions: List[str]
    current_question_count: int = 0
    completed: bool = False
    follow_up_questions: List[str] = field(default_factory=list)


class DS_SharedClientManager:
    """Daily-standup original (sync OpenAI + Groq, threadpool)"""
    def __init__(self):
        self._groq_client = None
        self._openai_client = None
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=config.THREAD_POOL_MAX_WORKERS)

    @property
    def groq_client(self) -> Groq:
        if self._groq_client is None:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise Exception("GROQ_API_KEY not found in environment variables")
            self._groq_client = Groq(api_key=api_key)
            logger.info("[DS] Groq client initialized")
        return self._groq_client

    @property
    def openai_client(self) -> openai_sync.OpenAI:
        if self._openai_client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise Exception("OPENAI_API_KEY not found in environment variables")
            self._openai_client = openai_sync.OpenAI(api_key=api_key)
            logger.info("[DS] OpenAI (sync) client initialized")
        return self._openai_client

    @property
    def executor(self):
        return self._executor

    async def close_connections(self):
        if self._executor:
            self._executor.shutdown(wait=True)
        logger.info("[DS] AI client connections closed")

ds_shared_clients = DS_SharedClientManager()


class DS_FragmentManager:
    """Daily-standup dynamic fragment manager"""
    def __init__(self, client_manager: DS_SharedClientManager, session_data: DS_SessionData):
        self.client_manager = client_manager
        self.session_data = session_data

    @property
    def openai_client(self):
        return self.client_manager.openai_client

    def initialize_fragments(self, summary: str) -> bool:
        self.session_data.fragments = _ds_parse_summary_into_fragments(summary)
        self.session_data.fragment_keys = list(self.session_data.fragments.keys())
        self.session_data.concept_question_counts = {k: 0 for k in self.session_data.fragment_keys}
        self.session_data.questions_per_concept = max(
            config.MIN_QUESTIONS_PER_CONCEPT,
            min(config.MAX_QUESTIONS_PER_CONCEPT,
                config.TOTAL_QUESTIONS // len(self.session_data.fragment_keys) if self.session_data.fragment_keys else 1)
        )
        logger.info(f"[DS] Initialized {len(self.session_data.fragment_keys)} fragments, "
                    f"target {self.session_data.questions_per_concept}/concept")
        return True

    def get_active_fragment(self) -> Tuple[str, str]:
        if not self.session_data.fragment_keys:
            return "General", self.session_data.fragments.get("General", "No content available")
        min_q = min(self.session_data.concept_question_counts.values())
        under = [c for c, cnt in self.session_data.concept_question_counts.items() if cnt == min_q]
        if under:
            for c in self.session_data.fragment_keys:
                if c in under:
                    return c, self.session_data.fragments[c]
        idx = self.session_data.question_index % len(self.session_data.fragment_keys)
        c = self.session_data.fragment_keys[idx]
        return c, self.session_data.fragments[c]

    def should_continue_test(self) -> bool:
        actual = len([ex for ex in self.session_data.exchanges if ex.concept and not ex.concept.startswith('greeting')])
        if actual == 0:
            return True
        if any(cnt == 0 for cnt in self.session_data.concept_question_counts.values()):
            return True
        underdev = [c for c, cnt in self.session_data.concept_question_counts.items()
                    if cnt < self.session_data.questions_per_concept]
        if len(underdev) > len(self.session_data.fragment_keys) * 0.3:
            return True
        hard_limit = config.TOTAL_QUESTIONS + (config.TOTAL_QUESTIONS // 2)
        if actual >= hard_limit:
            return False
        if actual >= config.TOTAL_QUESTIONS:
            mx = max(self.session_data.concept_question_counts.values())
            mn = min(self.session_data.concept_question_counts.values())
            if mx - mn <= 1:
                return False
        return True

    def get_concept_conversation_history(self, concept: str, window_size: int = 5) -> str:
        entries = [ex for ex in reversed(self.session_data.exchanges) if ex.concept == concept and ex.user_response]
        last_entries = list(reversed(entries[:window_size]))
        blocks = []
        for e in last_entries:
            blocks.append(f"Q: {e.ai_message}\nA: {e.user_response}")
        return "\n\n".join(blocks)

    def add_question(self, question: str, concept: str = None, is_followup: bool = False):
        if concept and concept in self.session_data.concept_question_counts and not concept.startswith('greeting'):
            self.session_data.concept_question_counts[concept] += 1
        if is_followup and concept and not concept.startswith('greeting'):
            self.session_data.followup_questions += 1
        self.session_data.current_concept = concept or ""
        if concept and not concept.startswith('greeting'):
            self.session_data.question_index += 1

    def add_answer(self, answer: str):
        if self.session_data.exchanges:
            self.session_data.exchanges[-1].user_response = answer

    def get_progress_info(self) -> Dict[str, Any]:
        return {
            "current_question": self.session_data.question_index,
            "total_concepts": len(self.session_data.fragment_keys),
            "concept_coverage": self.session_data.concept_question_counts,
            "questions_per_concept_target": self.session_data.questions_per_concept,
            "followup_questions": self.session_data.followup_questions,
            "main_questions": self.session_data.question_index - self.session_data.followup_questions
        }

DS_SummaryManager = DS_FragmentManager


class DS_OptimizedAudioProcessor:
    """Daily-standup fast STT using Groq sync client via threadpool"""
    def __init__(self, client_manager: DS_SharedClientManager):
        self.client_manager = client_manager

    @property
    def groq_client(self) -> Groq:
        return self.client_manager.groq_client

    async def transcribe_audio_fast(self, audio_data: bytes) -> Tuple[str, float]:
        try:
            audio_size = len(audio_data)
            logger.info(f"[DS] Transcribing {audio_size} bytes")
            if audio_size < 50:
                raise Exception(f"Audio data too small ({audio_size} bytes)")
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.client_manager.executor, self._sync_transcribe, audio_data
            )
        except Exception as e:
            logger.error(f"[DS] Transcription error: {e}")
            raise Exception(f"Transcription failed: {e}")

    def _sync_transcribe(self, audio_data: bytes) -> Tuple[str, float]:
        try:
            temp_file = config.TEMP_DIR / f"audio_{int(time.time()*1e6)}.webm"
            with open(temp_file, "wb") as f:
                f.write(audio_data)
            with open(temp_file, "rb") as fh:
                result = self.groq_client.audio.transcriptions.create(
                    file=(temp_file.name, fh.read()),
                    model=config.GROQ_TRANSCRIPTION_MODEL,
                    response_format="verbose_json",
                    prompt="Please transcribe clearly, even if short."
                )
            try:
                os.remove(temp_file)
            except:
                pass
            transcript = result.text.strip() if getattr(result, "text", "") else ""
            if not transcript:
                return "", 0.0
            quality = min(len(transcript) / 30, 1.0)
            if hasattr(result, "segments") and result.segments:
                confs = [seg.get("confidence", 0.8) for seg in result.segments[:3]]
                if confs:
                    quality = (quality + sum(confs) / len(confs)) / 2
            return transcript, quality
        except Exception as e:
            if "format" in str(e).lower():
                raise Exception("Audio format not supported")
            elif "timeout" in str(e).lower():
                raise Exception("Transcription timeout")
            raise Exception(f"Groq transcription failed: {e}")


class DS_OptimizedConversationManager:
    """Daily-standup conversation management (single OpenAI call per step)"""
    def __init__(self, client_manager: DS_SharedClientManager):
        self.client_manager = client_manager

    @property
    def openai_client(self):
        return self.client_manager.openai_client

    def _sync_openai_call(self, prompt: str) -> str:
        try:
            resp = self.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=config.OPENAI_TEMPERATURE,
                max_tokens=config.OPENAI_MAX_TOKENS
            )
            result = resp.choices[0].message.content.strip()
            if not result:
                raise Exception("OpenAI returned empty response")
            return result
        except Exception as e:
            logger.error(f"[DS] OpenAI call failed: {e}")
            raise Exception(f"OpenAI API failed: {e}")

    async def generate_fast_response(self, session_data: DS_SessionData, user_input: str) -> str:
        try:
            if session_data.current_stage == DS_SessionStage.GREETING:
                ctx = {
                    "recent_exchanges": [
                        f"AI: {ex.ai_message}, User: {ex.user_response}"
                        for ex in list(session_data.conversation_window)[-2:]
                    ]
                }
                prompt = ds_prompts.dynamic_greeting_response(user_input, session_data.greeting_count, ctx)
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(ds_shared_clients.executor, self._sync_openai_call, prompt)

            if session_data.current_stage == DS_SessionStage.TECHNICAL:
                fm: DS_FragmentManager = session_data.summary_manager
                if not fm:
                    raise Exception("Fragment manager not initialized")

                if not fm.should_continue_test():
                    session_data.current_stage = DS_SessionStage.COMPLETE
                    conversation_summary = fm.get_progress_info()
                    prompt = ds_prompts.dynamic_session_completion(conversation_summary)
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(ds_shared_clients.executor, self._sync_openai_call, prompt)

                current_concept_title, current_concept_content = fm.get_active_fragment()
                history = fm.get_concept_conversation_history(current_concept_title)
                last_q = session_data.exchanges[-1].ai_message if session_data.exchanges else ""
                questions_for_concept = session_data.concept_question_counts.get(current_concept_title, 0)

                prompt = ds_prompts.dynamic_followup_response(
                    current_concept_title=current_concept_title,
                    concept_content=current_concept_content,
                    history=history,
                    previous_question=last_q,
                    user_response=user_input,
                    current_question_number=session_data.question_index + 1,
                    questions_for_concept=questions_for_concept
                )
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(ds_shared_clients.executor, self._sync_openai_call, prompt)

                lines = response.strip().split('\n')
                understanding = "NO"
                concept = current_concept_title
                actual_response = response
                for line in lines:
                    if line.upper().startswith("UNDERSTANDING:"):
                        understanding = line.split(":", 1)[1].strip().upper()
                    elif line.upper().startswith("CONCEPT:"):
                        concept = line.split(":", 1)[1].strip()
                    elif line.upper().startswith("QUESTION:"):
                        actual_response = line.split(":", 1)[1].strip()

                if understanding == "YES":
                    next_concept_title, _ = fm.get_active_fragment()
                    fm.add_question(actual_response, next_concept_title, False)
                else:
                    fm.add_question(actual_response, current_concept_title, True)

                return actual_response

            session_context = {
                'key_topics': list(set(ex.chunk_id for ex in session_data.exchanges if ex.chunk_id))[:3],
                'total_exchanges': len(session_data.exchanges)
            }
            prompt = ds_prompts.dynamic_conclusion_response(user_input, session_context)
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(ds_shared_clients.executor, self._sync_openai_call, prompt)

        except Exception as e:
            logger.error(f"[DS] Response generation error: {e}")
            raise Exception(f"AI response generation failed: {e}")

    async def generate_fast_evaluation(self, session_data: DS_SessionData) -> Tuple[str, float]:
        try:
            conv = []
            for ex in session_data.exchanges[-10:]:
                if ex.stage == DS_SessionStage.TECHNICAL:
                    conv.append({
                        'ai_message': ex.ai_message,
                        'user_response': ex.user_response,
                        'chunk_id': ex.chunk_id,
                        'quality': ex.transcript_quality,
                        'concept': ex.concept,
                        'is_followup': ex.is_followup
                    })
            if not conv:
                raise Exception("No technical exchanges found for evaluation")
            stats = {
                'duration_minutes': round((time.time() - session_data.created_at) / 60, 1),
                'avg_response_length': sum(len(x['user_response']) for x in conv) // len(conv),
                'total_concepts': len(session_data.fragment_keys),
                'concepts_covered': len([c for c, cnt in session_data.concept_question_counts.items() if cnt > 0]),
                'coverage_percentage': round(
                    (len([c for c, cnt in session_data.concept_question_counts.items() if cnt > 0]) /
                     max(len(session_data.fragment_keys), 1) * 100), 1
                ),
                'main_questions': session_data.question_index - session_data.followup_questions,
                'followup_questions': session_data.followup_questions,
                'questions_per_concept': dict(session_data.concept_question_counts)
            }
            covered = [c for c, cnt in session_data.concept_question_counts.items() if cnt > 0]
            prompt = ds_prompts.dynamic_fragment_evaluation(covered, conv, stats)
            loop = asyncio.get_event_loop()
            evaluation = await loop.run_in_executor(ds_shared_clients.executor, self._sync_openai_call, prompt)
            m = re.search(r'Score:\s*(\d+(?:\.\d+)?)/10', evaluation)
            if not m:
                raise Exception(f"Could not extract score from evaluation text")
            score = float(m.group(1))
            return evaluation, score
        except Exception as e:
            logger.error(f"[DS] Evaluation error: {e}")
            raise Exception(f"Evaluation generation failed: {e}")

# =============================================================================
# WEEKLY INTERVIEW NAMESPACE (WI_*) - UPDATED
# =============================================================================

class WI_InterviewStage(Enum):
    """Updated stages: Communication -> Technical -> HR (no greeting)"""
    COMMUNICATION = "communication"
    TECHNICAL = "technical"
    HR = "hr"
    COMPLETE = "complete"


@dataclass
class WI_ConversationExchange:
    timestamp: float
    stage: WI_InterviewStage
    ai_message: str
    user_response: str = ""
    transcript_quality: float = 0.0
    concept: str = ""
    is_followup: bool = False
    answer_quality: str = "neutral"  # "strong", "neutral", "weak"


@dataclass
class WI_InterviewSession:
    """Updated session with time-based round tracking"""
    session_id: str
    test_id: str
    student_id: int
    student_name: str
    session_key: str
    created_at: float
    last_activity: float
    current_stage: WI_InterviewStage = WI_InterviewStage.COMMUNICATION  # Start with Communication
    is_active: bool = True
    websocket: Optional[Any] = None

    # Content and fragments
    content_context: str = ""
    fragment_keys: List[str] = field(default_factory=list)
    current_concept: Optional[str] = None
    fragment_manager: Optional[Any] = None

    # Conversation tracking
    exchanges: List[WI_ConversationExchange] = field(default_factory=list)
    
    # Time-based round tracking
    round_start_times: Dict[str, float] = field(default_factory=dict)
    questions_per_round: Dict[str, int] = field(default_factory=lambda: {
        "communication": 0, "technical": 0, "hr": 0
    })
    
    # Tracking
    concept_question_counts: Dict[str, int] = field(default_factory=dict)
    followup_questions: int = 0
    silence_prompt_count: int = 0
    current_difficulty: str = "medium"  # "easy", "medium", "hard"
    last_answer_quality: str = "neutral"

    def start_round(self, stage: WI_InterviewStage):
        """Mark the start time of a round"""
        self.round_start_times[stage.value] = time.time()
        self.current_stage = stage
        logger.info(f"[WI] Starting round: {stage.value}")

    def get_round_elapsed_time(self) -> float:
        """Get elapsed time in current round (seconds)"""
        start_time = self.round_start_times.get(self.current_stage.value, time.time())
        return time.time() - start_time

    def get_round_elapsed_minutes(self) -> float:
        """Get elapsed time in current round (minutes)"""
        return self.get_round_elapsed_time() / 60

    def add_exchange(self, ai_message: str, user_response: str = "", quality: float = 0.0,
                     concept: str = "", is_followup: bool = False, answer_quality: str = "neutral"):
        ex = WI_ConversationExchange(
            timestamp=time.time(),
            stage=self.current_stage,
            ai_message=ai_message,
            user_response=user_response,
            transcript_quality=quality,
            concept=concept,
            is_followup=is_followup,
            answer_quality=answer_quality
        )
        self.exchanges.append(ex)
        stage_key = self.current_stage.value
        self.questions_per_round[stage_key] = self.questions_per_round.get(stage_key, 0) + 1
        if is_followup:
            self.followup_questions += 1
        if concept:
            self.concept_question_counts[concept] = self.concept_question_counts.get(concept, 0) + 1
        self.last_activity = time.time()
        self.last_answer_quality = answer_quality

    def update_last_response(self, user_response: str, quality: float, answer_quality: str = "neutral"):
        if self.exchanges:
            self.exchanges[-1].user_response = user_response
            self.exchanges[-1].transcript_quality = quality
            self.exchanges[-1].answer_quality = answer_quality
        self.last_activity = time.time()
        self.last_answer_quality = answer_quality

    def get_conversation_history(self, limit: int = 5) -> str:
        recent = self.exchanges[-limit:] if len(self.exchanges) > limit else self.exchanges
        parts = []
        for ex in recent:
            parts.append(f"Interviewer: {ex.ai_message}")
            if ex.user_response:
                parts.append(f"Candidate: {ex.user_response}")
        return "\n".join(parts)


class WI_SharedClientManager:
    """Weekly-interview async clients (OpenAI + Groq)"""
    def __init__(self):
        self.openai_client: Optional[AsyncOpenAI] = None
        self.groq_client: Optional[AsyncGroq] = None
        self.executor = ThreadPoolExecutor(max_workers=config.THREAD_POOL_MAX_WORKERS)
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise Exception("OPENAI_API_KEY not found in environment")
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise Exception("GROQ_API_KEY not found in environment")
        self.openai_client = AsyncOpenAI(api_key=openai_key)
        self.groq_client = AsyncGroq(api_key=groq_key)
        self._initialized = True
        logger.info("[WI] AI clients initialized")

    async def close_connections(self):
        if self.openai_client:
            await self.openai_client.close()
        if self.groq_client:
            await self.groq_client.close()
        if self.executor:
            self.executor.shutdown(wait=True)
        logger.info("[WI] AI clients closed")

wi_shared_clients = WI_SharedClientManager()


class WI_EnhancedInterviewFragmentManager:
    """Fragment manager with time-based round control"""

    def __init__(self, client_manager: WI_SharedClientManager, session: WI_InterviewSession):
        self.client_manager = client_manager
        self.session = session
        self.fragments: Dict[str, Dict[str, Any]] = {}

    def initialize_fragments(self, summaries: List[Dict[str, Any]]) -> bool:
        """Initialize fragments from 7-day summaries"""
        try:
            if not summaries:
                return False

            all_content: List[str] = []
            for summary in summaries:
                content = summary.get("summary", "")
                if content and len(content) > config.MIN_CONTENT_LENGTH:
                    all_content.append(content)

            if not all_content:
                return False

            self.fragments.clear()
            for i, content in enumerate(all_content[:config.MAX_INTERVIEW_FRAGMENTS]):
                fragment_key = f"fragment_{i+1}"
                self.fragments[fragment_key] = {
                    "content": content,
                    "used_count": 0,
                    "last_used": 0,
                }

            self.session.fragment_keys = list(self.fragments.keys())
            self.session.content_context = "\n\n".join(all_content)

            # Start the first round (Communication)
            self.session.start_round(WI_InterviewStage.COMMUNICATION)

            logger.info(f"[WI] Initialized {len(self.fragments)} fragments, starting Communication round")
            return True

        except Exception as e:
            logger.error(f"[WI] Fragment initialization failed: {e}")
            return False

    def get_next_concept(self, stage: WI_InterviewStage) -> Optional[str]:
        """Get next concept for questioning"""
        try:
            available_fragments = [
                key for key, fragment in self.fragments.items()
                if fragment["used_count"] < config.MAX_QUESTIONS_PER_CONCEPT_WI
            ]

            if not available_fragments:
                for fragment in self.fragments.values():
                    fragment["used_count"] = 0
                available_fragments = list(self.fragments.keys())

            if available_fragments:
                selected = min(available_fragments, key=lambda k: self.fragments[k]["used_count"])
                self.fragments[selected]["used_count"] += 1
                self.fragments[selected]["last_used"] = time.time()
                return selected

            return None

        except Exception as e:
            logger.warning(f"[WI] Concept selection error: {e}")
            return None

    def should_continue_round(self, stage: WI_InterviewStage) -> bool:
        """Time-based round continuation check"""
        # Get round duration from config
        round_duration = config.ROUND_DURATIONS.get(stage.value, 600)
        elapsed_time = self.session.get_round_elapsed_time()
        
        # Check if time is up
        if elapsed_time >= round_duration:
            logger.info(f"[WI] Round {stage.value} time limit reached ({elapsed_time:.0f}s >= {round_duration}s)")
            return False
        
        # Ensure minimum questions asked
        current_questions = self.session.questions_per_round.get(stage.value, 0)
        if current_questions < config.MIN_QUESTIONS_PER_ROUND:
            return True
        
        # Don't exceed max questions even if time remains
        if current_questions >= config.MAX_QUESTIONS_PER_ROUND:
            return False
        
        return True

    def get_round_time_remaining(self) -> float:
        """Get remaining time in current round (seconds)"""
        stage = self.session.current_stage
        round_duration = config.ROUND_DURATIONS.get(stage.value, 600)
        elapsed = self.session.get_round_elapsed_time()
        return max(0, round_duration - elapsed)

    def add_question(self, question: str, concept: str, is_followup: bool = False):
        """Track question usage"""
        if concept in self.fragments:
            self.fragments[concept]["used_count"] += 1


class WI_OptimizedAudioProcessor:
    """Weekly-interview fast STT using Async Groq client"""
    def __init__(self, client_manager: WI_SharedClientManager):
        self.client_manager = client_manager

    async def transcribe_audio_fast(self, audio_data: bytes) -> Tuple[str, float]:
        try:
            if not audio_data or len(audio_data) < 100:
                raise Exception(f"Audio data too small: {len(audio_data)} bytes")
            await self.client_manager.initialize()
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                tf.write(audio_data)
                temp_path = tf.name
            try:
                with open(temp_path, "rb") as f:
                    logger.info(f"[WI] Calling Groq STT model: {config.GROQ_MODEL}")
                    tr = await self.client_manager.groq_client.audio.transcriptions.create(
                        file=(temp_path, f.read()),
                        model=config.GROQ_TRANSCRIPTION_MODEL,
                        language="en",
                        response_format="text"
                    )
                txt = tr.strip() if isinstance(tr, str) else str(tr).strip()
                if not txt:
                    raise Exception("Groq returned empty transcript")
                length_score = min(len(txt) / 50, 1.0)
                word_score = min(len(txt.split()) / 10, 1.0)
                size_score = min(len(audio_data) / 10000, 1.0)
                quality = (length_score + word_score + size_score) / 3
                return txt, quality
            finally:
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"[WI] Transcription failed: {e}")
            raise Exception(f"Audio transcription failed: {e}")


class WI_OptimizedConversationManager:
    """Weekly-interview conversation flow with adaptive difficulty and time-based rounds"""
    def __init__(self, client_manager: WI_SharedClientManager):
        self.client_manager = client_manager

    def _assess_answer_quality(self, user_response: str) -> str:
        """Assess the quality of user's answer for adaptive difficulty"""
        if not user_response:
            return "weak"
        
        word_count = len(user_response.split())
        
        # Strong answer indicators
        strong_keywords = ["because", "therefore", "for example", "specifically", 
                          "implemented", "designed", "solved", "approach", "strategy"]
        has_strong_indicators = any(k in user_response.lower() for k in strong_keywords)
        
        if word_count >= config.WI_STRONG_ANSWER_MIN_WORDS and has_strong_indicators:
            return "strong"
        elif word_count <= config.WI_WEAK_ANSWER_MAX_WORDS:
            return "weak"
        else:
            return "neutral"

    def _should_ask_followup(self, user_response: str, session: WI_InterviewSession, answer_quality: str) -> bool:
        """Determine if a follow-up question is appropriate"""
        if not user_response or len(user_response.split()) < 5:
            return False
        
        # In communication round, always follow up on interesting points
        if session.current_stage == WI_InterviewStage.COMMUNICATION:
            return answer_quality == "strong" and random.random() < 0.4
        
        # In technical round, follow up based on answer quality
        if session.current_stage == WI_InterviewStage.TECHNICAL:
            if answer_quality == "strong":
                return random.random() < 0.3  # Dive deeper
            elif answer_quality == "weak":
                return random.random() < 0.5  # Probe fundamentals
        
        # In HR round, follow up for more examples
        if session.current_stage == WI_InterviewStage.HR:
            return answer_quality == "neutral" and random.random() < 0.3
        
        return False

    def _adjust_difficulty(self, session: WI_InterviewSession, answer_quality: str):
        """Adjust difficulty based on answer quality (for technical round)"""
        if session.current_stage != WI_InterviewStage.TECHNICAL:
            return
        
        if answer_quality == "strong" and session.current_difficulty != "hard":
            if session.current_difficulty == "easy":
                session.current_difficulty = "medium"
            else:
                session.current_difficulty = "hard"
            logger.info(f"[WI] Difficulty increased to: {session.current_difficulty}")
        elif answer_quality == "weak" and session.current_difficulty != "easy":
            if session.current_difficulty == "hard":
                session.current_difficulty = "medium"
            else:
                session.current_difficulty = "easy"
            logger.info(f"[WI] Difficulty decreased to: {session.current_difficulty}")

    def _add_natural_personality(self, response: str, answer_quality: str, is_followup: bool) -> str:
        """Add natural conversational elements to response"""
        try:
            # Add acknowledgment based on answer quality
            if answer_quality == "strong":
                ack = random.choice(ENCOURAGEMENT_PHRASES)
            elif answer_quality == "weak":
                ack = random.choice(CLARIFICATION_PROMPTS[:3])  # Gentler prompts
            else:
                ack = random.choice(ACKNOWLEDGMENT_PHRASES)
            
            # Check if response already has acknowledgment
            if not any(p.lower() in response.lower()[:30] for p in ["that's", "great", "good", "interesting", "i see"]):
                response = f"{ack} {response}"
            
            # Ensure response ends with a question
            if not response.strip().endswith('?'):
                if is_followup:
                    response += " Could you elaborate on that?"
                else:
                    response += " What are your thoughts?"
            
            return response
        except Exception as e:
            logger.error(f"[WI] Personality enhancement failed: {e}")
            return response

    async def generate_silence_response(self, session: WI_InterviewSession) -> str:
        """Generate gentle prompt when candidate is silent"""
        try:
            session.silence_prompt_count += 1
            
            if session.silence_prompt_count > config.WI_MAX_SILENCE_PROMPTS:
                return "I understand you might need more time. Let's move to the next question when you're ready."
            
            return random.choice(SILENCE_GENTLE_PROMPTS)
        except Exception as e:
            logger.error(f"[WI] Silence response generation failed: {e}")
            return "Take your time, there's no rush."

    async def generate_fast_response(self, session: WI_InterviewSession, user_response: str) -> str:
        """Generate contextual interview response with adaptive behavior"""
        try:
            await self.client_manager.initialize()
            
            # Assess answer quality
            answer_quality = self._assess_answer_quality(user_response)
            
            # Adjust difficulty for technical round
            self._adjust_difficulty(session, answer_quality)
            
            # Determine if we should ask a follow-up
            should_followup = self._should_ask_followup(user_response, session, answer_quality)
            
            if not should_followup and session.current_stage != WI_InterviewStage.COMMUNICATION:
                next_concept = session.fragment_manager.get_next_concept(session.current_stage)
                session.current_concept = next_concept

            # Get round timing info
            round_duration = config.ROUND_DURATIONS.get(session.current_stage.value, 600) // 60
            time_elapsed = session.get_round_elapsed_minutes()
            questions_asked = session.questions_per_round.get(session.current_stage.value, 0)

            conversation_history = session.get_conversation_history(3)
            stage_prompt = build_stage_prompt(session.current_stage.value, session.content_context)
            
            full_prompt = build_conversation_prompt(
                stage=session.current_stage.value,
                user_response=user_response,
                content_context=session.content_context,
                conversation_history=conversation_history,
                round_duration=round_duration,
                time_elapsed=time_elapsed,
                questions_asked=questions_asked,
                answer_quality=answer_quality
            )
            
            logger.info(f"[WI] OpenAI model: {config.OPENAI_MODEL}, Stage: {session.current_stage.value}, "
                       f"Difficulty: {session.current_difficulty}, Answer Quality: {answer_quality}")
            
            resp = await self.client_manager.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[{"role": "system", "content": stage_prompt},
                          {"role": "user", "content": full_prompt}],
                temperature=config.OPENAI_TEMPERATURE,
                max_tokens=config.OPENAI_MAX_TOKENS
            )
            
            ai_response = resp.choices[0].message.content.strip()
            if not ai_response:
                raise Exception("OpenAI returned empty response")
            
            ai_response = self._add_natural_personality(ai_response, answer_quality, should_followup)
            
            # Reset silence counter on successful response
            session.silence_prompt_count = 0
            
            return ai_response
            
        except Exception as e:
            logger.error(f"[WI] Response generation failed: {e}")
            raise Exception(f"AI Response Generation Failed: {e}")

    async def generate_first_question(self, session: WI_InterviewSession) -> str:
        """Generate the first confidence-building question for Communication round"""
        try:
            await self.client_manager.initialize()
            
            first_questions = [
                f"Hello {session.student_name}! Welcome to your interview. To start off, could you tell me a little about yourself?",
                f"Hi {session.student_name}! It's great to meet you. Let's begin with something simple - what are you currently studying or working on?",
                f"Welcome {session.student_name}! I'm excited to learn about you today. Could you start by telling me what brought you to this field?",
            ]
            
            return random.choice(first_questions)
            
        except Exception as e:
            logger.error(f"[WI] First question generation failed: {e}")
            return f"Hello {session.student_name}! Welcome to your interview. Could you tell me a little about yourself?"

    async def generate_round_transition(self, session: WI_InterviewSession, next_stage: WI_InterviewStage) -> str:
        """Generate smooth transition message between rounds"""
        transitions = {
            WI_InterviewStage.TECHNICAL: [
                "Thank you for sharing that. Now let's move on to the technical portion of our interview.",
                "Great conversation! Let's transition to discussing some technical topics now.",
                "I've enjoyed learning about you. Now I'd like to explore your technical knowledge."
            ],
            WI_InterviewStage.HR: [
                "Excellent technical discussion! For our final round, I'd like to learn more about you as a person and professional.",
                "Thank you for those technical insights. Let's conclude with some behavioral questions.",
                "Great job on the technical portion. Now let's discuss some situations and experiences."
            ],
            WI_InterviewStage.COMPLETE: [
                "We've covered all the rounds. Thank you for your time and thoughtful responses.",
                "That concludes our interview. I appreciate your participation today.",
                "We've reached the end of our interview. Thank you for being so engaged."
            ]
        }
        
        options = transitions.get(next_stage, ["Let's continue with the next section."])
        return random.choice(options)

    async def generate_fast_evaluation(self, session: WI_InterviewSession) -> Tuple[str, Dict[str, float]]:
        """Generate comprehensive evaluation with 5 criteria"""
        try:
            await self.client_manager.initialize()
            
            conversation_log = "\n".join([
                f"[{ex.stage.value.upper()}] Interviewer: {ex.ai_message}\nCandidate: {ex.user_response}\n"
                for ex in session.exchanges if ex.user_response
            ])
            
            if not conversation_log:
                raise Exception("No conversation data for evaluation")

            evaluation_prompt = build_evaluation_prompt(
                student_name=session.student_name,
                duration=(time.time() - session.created_at) / 60,
                stages_completed=[s for s, c in session.questions_per_round.items() if c > 0],
                conversation_log=conversation_log,
                content_context=session.content_context
            )
            
            ev = await self.client_manager.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an experienced interviewer providing detailed, constructive feedback."},
                    {"role": "user", "content": evaluation_prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            evaluation = ev.choices[0].message.content.strip()
            if not evaluation:
                raise Exception("OpenAI returned empty evaluation")

            # Generate scores
            scoring = await self.client_manager.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are scoring an interview based on 5 criteria."},
                    {"role": "user", "content": f"{SCORING_PROMPT_TEMPLATE}\n\nConversation:\n{conversation_log}"}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            score_text = scoring.choices[0].message.content or ""
            
            # Parse scores for 5 criteria
            patterns = {
                "communication_score": r"communication[:\s]*(\d+(?:\.\d+)?)",
                "technical_score": r"technical[:\s]*(\d+(?:\.\d+)?)",
                "leadership_score": r"leadership[:\s]*(\d+(?:\.\d+)?)",
                "behaviour_score": r"behaviour[:\s]*(\d+(?:\.\d+)?)",
                "confidence_score": r"confidence[:\s]*(\d+(?:\.\d+)?)",
                "weighted_overall": r"weighted_overall[:\s]*(\d+(?:\.\d+)?)"
            }
            
            scores: Dict[str, float] = {}
            low = score_text.lower()
            
            for key, pat in patterns.items():
                m = re.search(pat, low)
                if m:
                    val = float(m.group(1))
                    if 0 <= val <= 10:
                        scores[key] = val
                    else:
                        scores[key] = 5.0  # Default
                else:
                    scores[key] = 5.0  # Default
            
            # Calculate weighted overall if not present
            if "weighted_overall" not in scores or scores["weighted_overall"] == 5.0:
                w = config.EVALUATION_CRITERIA
                scores["weighted_overall"] = round(
                    scores.get("communication_score", 5) * w["communication_weight"] +
                    scores.get("technical_score", 5) * w["technical_weight"] +
                    scores.get("leadership_score", 5) * w["leadership_weight"] +
                    scores.get("behaviour_score", 5) * w["behaviour_weight"] +
                    scores.get("confidence_score", 5) * w["confidence_weight"],
                    1
                )
            
            return evaluation, scores
            
        except Exception as e:
            logger.error(f"[WI] Evaluation failed: {e}")
            raise Exception(f"AI Evaluation Generation Failed: {e}")


# =============================================================================
# WEEKEND MOCK TEST (UNCHANGED)
# =============================================================================

class AIService:
    """Production AI service for question generation and evaluation (weekend_mocktest)"""
    def __init__(self):
        if not config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required")
        self.client = Groq(api_key=config.GROQ_API_KEY, timeout=getattr(config, "GROQ_TIMEOUT", 60))
        self._test_connection()
        logger.info("[MT] AI Service initialized")

    def _test_connection(self):
        try:
            response = self.client.chat.completions.create(
                model=getattr(config, "GROQ_MODEL", "llama-3.3-70b-versatile"),
                messages=[{"role": "user", "content": "Hello"}],
                max_completion_tokens=10
            )
            if not response.choices:
                raise Exception("No response from AI service")
        except Exception as e:
            raise Exception(f"AI service connection failed: {e}")

    def _call_llm_with_retries(self, prompt: str, max_tokens: int, temperature: float = None) -> str:
        if temperature is None:
            temperature = getattr(config, "GROQ_TEMPERATURE", 0.7)
        max_retries = getattr(config, "MAX_RETRIES", 3)
        delay = getattr(config, "RETRY_DELAY", 2)
        last_error = None
        for attempt in range(max_retries):
            try:
                completion = self.client.chat.completions.create(
                    model=getattr(config, "GROQ_MODEL", "llama-3.3-70b-versatile"),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_completion_tokens=max_tokens
                )
                if not completion.choices:
                    raise Exception("No response from LLM")
                response = completion.choices[0].message.content.strip()
                if len(response) < 100:
                    raise Exception("Response too short")
                return response
            except Exception as e:
                last_error = e
                logger.warning(f"[MT] LLM attempt {attempt+1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(delay * (attempt + 1))
        raise Exception(f"LLM failed after {max_retries} attempts: {last_error}")

    def _parse_single_question(self, section: str, user_type: str, qn: int) -> Dict[str, Any]:
        lines = [ln.strip() for ln in section.split('\n') if ln.strip()]
        data = {
            "question_number": qn, "title": f"Question {qn}", "difficulty": "Medium",
            "type": "General", "question": "", "options": None
        }
        current = None
        q_lines, options = [], []
        import re as _re
        for ln in lines:
            if ln.startswith("## Title:"):
                data["title"] = ln.replace("## Title:", "").strip()
            elif ln.startswith("## Difficulty:"):
                data["difficulty"] = ln.replace("## Difficulty:", "").strip()
            elif ln.startswith("## Type:"):
                data["type"] = ln.replace("## Type:", "").strip()
            elif ln.startswith("## Question:"):
                current = "q"
            elif ln.startswith("## Options:") and user_type == "non_dev":
                current = "o"
            elif current == "q":
                if not ln.startswith("##"):
                    q_lines.append(ln)
            elif current == "o" and user_type == "non_dev":
                if _re.match(r'^[A-D]\)', ln):
                    option_text = ln[3:].strip()
                    if option_text:
                        options.append(option_text)
        data["question"] = "\n".join(q_lines).strip()
        if user_type == "non_dev":
            data["options"] = options if len(options) == 4 else None
        if not data["question"] or len(data["question"]) < 50:
            raise Exception("Question too short")
        if user_type == "non_dev" and not data["options"]:
            raise Exception("MCQ missing options")
        return data

    def _parse_questions_response(self, response: str, user_type: str) -> List[Dict[str, Any]]:
        import re as _re
        questions = []
        sections = _re.split(r'=== QUESTION \d+ ===', response)[1:]
        for i, sec in enumerate(sections, 1):
            try:
                q = self._parse_single_question(sec, user_type, i)
                if q:
                    questions.append(q)
            except Exception as e:
                logger.warning(f"[MT] Failed to parse question {i}: {e}")
        return questions

    def _extract_scores_fallback(self, response: str, n: int) -> List[int]:
        import re as _re
        pats = _re.findall(r'(?:^|\s)([01](?:\s*,\s*[01])+)(?:\s|$)', response)
        for p in pats:
            arr = [int(s.strip()) for s in p.split(',')]
            if len(arr) == n:
                return arr
        logger.warning("[MT] Using fallback scoring")
        return [1 if i % 2 == 0 else 0 for i in range(n)]

    def _extract_feedbacks_fallback(self, response: str, n: int) -> List[str]:
        lines = response.split('\n')
        fbs = []
        for ln in lines:
            if 'question' in ln.lower() and any(w in ln.lower() for w in ['correct', 'incorrect', 'good', 'poor']):
                fbs.append(ln.strip())
                if len(fbs) == n:
                    break
        while len(fbs) < n:
            fbs.append(f"Question {len(fbs)+1}: Evaluated")
        return fbs[:n]

    def _parse_evaluation_response(self, response: str, qa_pairs: List[Dict[str, Any]]) -> Dict[str, Any]:
        import re as _re
        scores, feedbacks = [], []
        m_scores = _re.search(r'SCORES:\s*\[(.*?)\]', response, _re.DOTALL)
        if m_scores:
            score_str = m_scores.group(1)
            scores = [int(s.strip()) for s in score_str.split(',') if s.strip().isdigit()]
        m_fb = _re.search(r'FEEDBACK:\s*\[(.*?)\]', response, _re.DOTALL)
        if m_fb:
            fb_str = m_fb.group(1)
            feedbacks = [f.strip().strip('"\'') for f in fb_str.split('|')]
        if not scores or len(scores) != len(qa_pairs):
            scores = self._extract_scores_fallback(response, len(qa_pairs))
        if not feedbacks or len(feedbacks) != len(qa_pairs):
            feedbacks = self._extract_feedbacks_fallback(response, len(qa_pairs))
        if len(scores) != len(qa_pairs):
            raise Exception(f"Score count mismatch: {len(scores)} vs {len(qa_pairs)}")
        if len(feedbacks) != len(qa_pairs):
            feedbacks = [f"Question {i+1}: {'Correct' if scores[i] else 'Incorrect'}" for i in range(len(qa_pairs))]
        return {
            "scores": scores,
            "feedbacks": feedbacks,
            "total_correct": sum(scores),
            "evaluation_report": response
        }

    def generate_questions_batch(self, user_type: str, context: str) -> List[Dict[str, Any]]:
        logger.info(f"[MT] Generating {getattr(config, 'QUESTIONS_PER_TEST', 10)} {user_type} questions")
        prompt = PromptTemplates.create_batch_questions_prompt(user_type, context, getattr(config, "QUESTIONS_PER_TEST", 10))
        response = self._call_llm_with_retries(prompt, getattr(config, "GROQ_MAX_TOKENS", 3000))
        questions = self._parse_questions_response(response, user_type)
        if not questions:
            raise Exception("No valid questions generated")
        return questions

    def evaluate_test_batch(self, user_type: str, qa_pairs: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.info(f"[MT] Evaluating {len(qa_pairs)} {user_type} answers")
        prompt = PromptTemplates.create_evaluation_prompt(user_type, qa_pairs)
        response = self._call_llm_with_retries(prompt, getattr(config, "EVALUATION_MAX_TOKENS", 2000),
                                               getattr(config, "EVALUATION_TEMPERATURE", 0.3))
        return self._parse_evaluation_response(response, qa_pairs)


_ai_service_singleton: Optional[AIService] = None

def get_ai_service() -> AIService:
    global _ai_service_singleton
    if _ai_service_singleton is None:
        _ai_service_singleton = AIService()
    return _ai_service_singleton