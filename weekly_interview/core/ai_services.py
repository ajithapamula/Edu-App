# weekly_interview/core/ai_services.py
"""
Enhanced AI Services - Clean, Fast, and Natural Interview Experience
Fixed Unicode issues and integrated with prompts.py for modular design
COMPLETE FILE - NO FALLBACKS, FAIL LOUDLY FOR DEBUGGING
"""

import os
import time
import logging
import asyncio
import random
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

from openai import AsyncOpenAI
from groq import AsyncGroq

from .config import config
from .prompts import (
    build_stage_prompt, build_conversation_prompt, build_evaluation_prompt,
    ACKNOWLEDGMENT_PHRASES, TRANSITION_PHRASES, ENCOURAGEMENT_PHRASES,
    CLARIFICATION_PROMPTS, GENTLE_REDIRECT_PROMPTS, SCORING_PROMPT_TEMPLATE
)

logger = logging.getLogger(__name__)

# =============================================================================
# SHARED CLIENT MANAGER - OPTIMIZED CONNECTION HANDLING
# =============================================================================

class SharedClientManager:
    """Shared client manager for AI services with connection pooling"""
    
    def __init__(self):
        self.openai_client = None
        self.groq_client = None
        self.executor = ThreadPoolExecutor(max_workers=config.THREAD_POOL_MAX_WORKERS)
        self._initialized = False
    
    async def initialize(self):
        """Initialize AI clients with API keys"""
        if self._initialized:
            return
        
        try:
            # Initialize OpenAI client
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                raise Exception("OPENAI_API_KEY not found in environment")
            self.openai_client = AsyncOpenAI(api_key=openai_key)
            
            # Initialize Groq client
            groq_key = os.getenv("GROQ_API_KEY")
            if not groq_key:
                raise Exception("GROQ_API_KEY not found in environment")
            self.groq_client = AsyncGroq(api_key=groq_key)
            
            self._initialized = True
            logger.info("? AI clients initialized successfully")
            
        except Exception as e:
            logger.error(f"? AI client initialization failed: {e}")
            raise Exception(f"AI client initialization failed: {e}")
    
    async def close_connections(self):
        """Cleanup method for graceful shutdown"""
        if self.openai_client:
            await self.openai_client.close()
        if self.groq_client:
            await self.groq_client.close()
        if self.executor:
            self.executor.shutdown(wait=True)
        logger.info("?? AI clients closed")

# Global shared clients instance
shared_clients = SharedClientManager()

# =============================================================================
# INTERVIEW SESSION MODELS
# =============================================================================

class InterviewStage(Enum):
    """Interview stages for structured progression"""
    GREETING = "greeting"
    TECHNICAL = "technical"
    COMMUNICATION = "communication"
    HR = "hr"
    COMPLETE = "complete"

@dataclass
class ConversationExchange:
    """Individual conversation exchange"""
    timestamp: float
    stage: InterviewStage
    ai_message: str
    user_response: str = ""
    transcript_quality: float = 0.0
    concept: str = ""
    is_followup: bool = False

@dataclass
class InterviewSession:
    """Complete interview session state"""
    session_id: str
    test_id: str
    student_id: int
    student_name: str
    session_key: str
    created_at: float
    last_activity: float
    current_stage: InterviewStage = InterviewStage.GREETING
    is_active: bool = True
    websocket: Optional[Any] = None
    
    # Content and fragments
    content_context: str = ""
    fragment_keys: List[str] = field(default_factory=list)
    current_concept: Optional[str] = None
    fragment_manager: Optional[Any] = None
    
    # Conversation tracking
    exchanges: List[ConversationExchange] = field(default_factory=list)
    questions_per_round: Dict[str, int] = field(default_factory=lambda: {
        "greeting": 0, "technical": 0, "communication": 0, "hr": 0
    })
    concept_question_counts: Dict[str, int] = field(default_factory=dict)
    followup_questions: int = 0
    
    def add_exchange(self, ai_message: str, user_response: str = "", quality: float = 0.0, 
                    concept: str = "", is_followup: bool = False):
        """Add new conversation exchange"""
        exchange = ConversationExchange(
            timestamp=time.time(),
            stage=self.current_stage,
            ai_message=ai_message,
            user_response=user_response,
            transcript_quality=quality,
            concept=concept,
            is_followup=is_followup
        )
        self.exchanges.append(exchange)
        
        # Update counters
        stage_key = self.current_stage.value
        self.questions_per_round[stage_key] = self.questions_per_round.get(stage_key, 0) + 1
        
        if is_followup:
            self.followup_questions += 1
        
        if concept:
            self.concept_question_counts[concept] = self.concept_question_counts.get(concept, 0) + 1
        
        self.last_activity = time.time()
    
    def update_last_response(self, user_response: str, quality: float):
        """Update the last exchange with user response"""
        if self.exchanges:
            self.exchanges[-1].user_response = user_response
            self.exchanges[-1].transcript_quality = quality
        self.last_activity = time.time()
    
    def get_conversation_history(self, limit: int = 5) -> str:
        """Get formatted conversation history"""
        recent_exchanges = self.exchanges[-limit:] if len(self.exchanges) > limit else self.exchanges
        
        history_parts = []
        for exchange in recent_exchanges:
            history_parts.append(f"Interviewer: {exchange.ai_message}")
            if exchange.user_response:
                history_parts.append(f"Candidate: {exchange.user_response}")
        
        return "\n".join(history_parts)

# =============================================================================
# ENHANCED FRAGMENT MANAGER - SIMPLIFIED AND EFFICIENT
# =============================================================================

class EnhancedInterviewFragmentManager:
    """Simplified fragment manager for interview content"""
    
    def __init__(self, client_manager: SharedClientManager, session: InterviewSession):
        self.client_manager = client_manager
        self.session = session
        self.fragments = {}
        self.used_concepts = set()
    
    def initialize_fragments(self, summaries: List[Dict[str, Any]]) -> bool:
        """Initialize fragments from 7-day summaries"""
        try:
            if not summaries:
                return False
            
            # Process summaries into fragments (keep your approach)
            all_content = []
            for summary in summaries:
                content = summary.get("summary", "")
                if content and len(content) > config.MIN_CONTENT_LENGTH:
                    all_content.append(content)
            
            if not all_content:
                return False
            
            # Create simple numbered fragments for easy management
            for i, content in enumerate(all_content[:config.MAX_INTERVIEW_FRAGMENTS]):
                fragment_key = f"fragment_{i+1}"
                self.fragments[fragment_key] = {
                    "content": content,
                    "used_count": 0,
                    "last_used": 0
                }
            
            self.session.fragment_keys = list(self.fragments.keys())
            self.session.content_context = "\n\n".join(all_content)
            
            logger.info(f"? Initialized {len(self.fragments)} fragments from {len(summaries)} summaries")
            return True
            
        except Exception as e:
            logger.error(f"? Fragment initialization failed: {e}")
            return False
    
    def get_next_concept(self, stage: InterviewStage) -> Optional[str]:
        """Get next concept for questioning"""
        try:
            # Simple round-robin concept selection
            available_fragments = [
                key for key, fragment in self.fragments.items()
                if fragment["used_count"] < config.MAX_QUESTIONS_PER_CONCEPT
            ]
            
            if not available_fragments:
                # Reset all fragments if we've exhausted them
                for fragment in self.fragments.values():
                    fragment["used_count"] = 0
                available_fragments = list(self.fragments.keys())
            
            if available_fragments:
                # Select least used fragment
                selected = min(available_fragments, 
                             key=lambda k: self.fragments[k]["used_count"])
                
                self.fragments[selected]["used_count"] += 1
                self.fragments[selected]["last_used"] = time.time()
                
                return selected
            
            return None
            
        except Exception as e:
            logger.warning(f"?? Concept selection error: {e}")
            return None
    
    def should_continue_round(self, stage: InterviewStage) -> bool:
        """Determine if current round should continue"""
        current_questions = self.session.questions_per_round.get(stage.value, 0)
        max_questions = config.QUESTIONS_PER_ROUND
        
        if stage == InterviewStage.GREETING:
            return current_questions < 2
        
        return current_questions < max_questions
    
    def add_question(self, question: str, concept: str, is_followup: bool = False):
        """Track question usage"""
        if concept in self.fragments:
            self.fragments[concept]["used_count"] += 1

# =============================================================================
# OPTIMIZED AUDIO PROCESSOR
# =============================================================================

class OptimizedAudioProcessor:
    """Fast audio transcription with Groq Whisper"""
    
    def __init__(self, client_manager: SharedClientManager):
        self.client_manager = client_manager
    
    async def transcribe_audio_fast(self, audio_data: bytes) -> Tuple[str, float]:
        """Fast audio transcription with quality assessment - FAIL LOUDLY"""
        try:
            if not audio_data or len(audio_data) < 100:
                raise Exception(f"Audio data too small: {len(audio_data)} bytes")
            
            await self.client_manager.initialize()
            
            # Create temporary file for Groq
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            try:
                # Transcribe with Groq Whisper - FAIL LOUDLY IF IT FAILS
                with open(temp_path, "rb") as audio_file:
                    logger.info(f"?? Calling Groq Whisper with model: {config.GROQ_MODEL}")
                    transcript = await self.client_manager.groq_client.audio.transcriptions.create(
                        file=(temp_path, audio_file.read()),
                        model=config.GROQ_MODEL,
                        language="en",
                        response_format="text"
                    )
                
                # Clean transcript
                if isinstance(transcript, str):
                    cleaned_transcript = transcript.strip()
                else:
                    cleaned_transcript = str(transcript).strip()
                
                if not cleaned_transcript:
                    raise Exception("Groq returned empty transcript")
                
                # Simple quality assessment
                quality = self._assess_transcript_quality(cleaned_transcript, len(audio_data))
                
                logger.info(f"? Transcribed: '{cleaned_transcript[:50]}...' (quality: {quality:.2f})")
                return cleaned_transcript, quality
                
            finally:
                # Cleanup temp file
                try:
                    os.unlink(temp_path)
                except Exception as cleanup_error:
                    logger.warning(f"?? Temp file cleanup failed: {cleanup_error}")
                    
        except Exception as e:
            logger.error(f"? CRITICAL: Transcription failed: {e}")
            logger.error(f"? Audio size: {len(audio_data) if audio_data else 0} bytes")
            raise Exception(f"Audio transcription failed: {e}")
    
    def _assess_transcript_quality(self, transcript: str, audio_size: int) -> float:
        """Simple transcript quality assessment"""
        if not transcript:
            return 0.0
        
        # Basic quality factors
        length_score = min(len(transcript) / 50, 1.0)  # Prefer longer responses
        word_count = len(transcript.split())
        word_score = min(word_count / 10, 1.0)  # Prefer more words
        
        # Audio size factor
        size_score = min(audio_size / 10000, 1.0)  # Prefer reasonable audio size
        
        # Avoid very short or repetitive responses
        if word_count < 2:
            return 0.2
        
        return (length_score + word_score + size_score) / 3

# =============================================================================
# OPTIMIZED CONVERSATION MANAGER - NATURAL HUMAN-LIKE FLOW
# =============================================================================

class OptimizedConversationManager:
    """Natural conversation management with human-like interviewer responses"""
    
    def __init__(self, client_manager: SharedClientManager):
        self.client_manager = client_manager
    
    async def generate_fast_response(self, session: InterviewSession, user_response: str) -> str:
        """Generate natural interviewer response - NO FALLBACKS, FAIL LOUDLY"""
        try:
            await self.client_manager.initialize()
            
            # Determine if this should be a follow-up or new question
            should_followup = self._should_ask_followup(user_response, session)
            
            # Select next concept if not following up
            if not should_followup and session.current_stage != InterviewStage.GREETING:
                next_concept = session.fragment_manager.get_next_concept(session.current_stage)
                session.current_concept = next_concept
            
            # Build conversation prompt
            conversation_history = session.get_conversation_history(3)
            stage_prompt = build_stage_prompt(session.current_stage.value, session.content_context)
            
            full_prompt = build_conversation_prompt(
                stage=session.current_stage.value,
                user_response=user_response,
                content_context=session.content_context,
                conversation_history=conversation_history
            )
            
            # Generate response with natural personality - FAIL LOUDLY IF IT FAILS
            logger.info(f"?? Calling OpenAI with model: {config.OPENAI_MODEL}")
            response = await self.client_manager.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": stage_prompt},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=config.OPENAI_TEMPERATURE,
                max_tokens=config.OPENAI_MAX_TOKENS
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            if not ai_response:
                raise Exception("OpenAI returned empty response")
            
            # Add natural personality touches
            ai_response = self._add_natural_personality(ai_response, user_response, should_followup)
            
            logger.info(f"? Generated response: '{ai_response[:100]}...'")
            return ai_response
            
        except Exception as e:
            logger.error(f"? CRITICAL: Response generation failed: {e}")
            logger.error(f"? OpenAI API Error Details: {str(e)}")
            # DON'T HIDE THE ERROR - Let it propagate up
            raise Exception(f"AI Response Generation Failed: {e}")
    
    def _should_ask_followup(self, user_response: str, session: InterviewSession) -> bool:
        """Determine if we should ask a follow-up question"""
        if not user_response or len(user_response.split()) < 5:
            return False
        
        # Ask follow-up if response is particularly interesting or incomplete
        interesting_keywords = [
            "challenging", "complex", "difficult", "innovative", "unique",
            "learned", "implemented", "designed", "optimized", "solved"
        ]
        
        has_interesting_content = any(keyword in user_response.lower() for keyword in interesting_keywords)
        
        # Follow up 30% of the time for interesting responses
        if has_interesting_content and random.random() < 0.3:
            return True
            
        # Follow up if response seems incomplete
        if len(user_response.split()) < 10 and random.random() < 0.2:
            return True
            
        return False
    
    def _add_natural_personality(self, response: str, user_response: str, is_followup: bool) -> str:
        """Add natural interviewer personality to responses"""
        try:
            # Add acknowledgment phrases for natural flow
            if not any(phrase.lower() in response.lower()[:20] for phrase in ["that's", "great", "interesting", "i see"]):
                if len(user_response.split()) > 10:  # Good detailed response
                    acknowledgment = random.choice(ACKNOWLEDGMENT_PHRASES + ENCOURAGEMENT_PHRASES[:3])
                else:
                    acknowledgment = random.choice(ACKNOWLEDGMENT_PHRASES)
                
                response = f"{acknowledgment} {response}"
            
            # Ensure response ends with a question
            if not response.strip().endswith('?'):
                if is_followup:
                    response += " Could you tell me more about that?"
                else:
                    response += " What are your thoughts on that?"
            
            return response
            
        except Exception as e:
            logger.error(f"? Personality enhancement failed: {e}")
            raise Exception(f"Response personality enhancement failed: {e}")
    
    async def generate_fast_evaluation(self, session: InterviewSession) -> Tuple[str, Dict[str, float]]:
        """Generate comprehensive interview evaluation - NO FALLBACKS"""
        try:
            await self.client_manager.initialize()
            
            # Build conversation log
            conversation_log = "\n".join([
                f"[{exchange.stage.value.upper()}] Interviewer: {exchange.ai_message}\n"
                f"Candidate: {exchange.user_response}\n"
                for exchange in session.exchanges if exchange.user_response
            ])
            
            if not conversation_log:
                raise Exception("No conversation data available for evaluation")
            
            # Generate evaluation - FAIL LOUDLY IF IT FAILS
            evaluation_prompt = build_evaluation_prompt(
                student_name=session.student_name,
                duration=(time.time() - session.created_at) / 60,
                stages_completed=[stage for stage, count in session.questions_per_round.items() if count > 0],
                conversation_log=conversation_log,
                content_context=session.content_context
            )
            
            logger.info(f"?? Generating evaluation with OpenAI")
            evaluation_response = await self.client_manager.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an experienced technical interviewer providing detailed feedback."},
                    {"role": "user", "content": evaluation_prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            evaluation = evaluation_response.choices[0].message.content.strip()
            
            if not evaluation:
                raise Exception("OpenAI returned empty evaluation")
            
            # Generate scores - FAIL LOUDLY IF IT FAILS
            logger.info(f"?? Generating scores with OpenAI")
            scoring_response = await self.client_manager.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are scoring an interview on a 1-10 scale."},
                    {"role": "user", "content": f"{SCORING_PROMPT_TEMPLATE}\n\nConversation:\n{conversation_log}"}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            if not scoring_response.choices[0].message.content:
                raise Exception("OpenAI returned empty scoring response")
            
            # Parse scores - FAIL LOUDLY IF PARSING FAILS
            scores = self._parse_scores(scoring_response.choices[0].message.content, session)
            
            logger.info(f"? Generated evaluation and scores for {session.test_id}")
            return evaluation, scores
            
        except Exception as e:
            logger.error(f"? CRITICAL: Evaluation generation failed: {e}")
            logger.error(f"? Session details: {session.test_id}, exchanges: {len(session.exchanges)}")
            # DON'T HIDE THE ERROR - Let it propagate up
            raise Exception(f"AI Evaluation Generation Failed: {e}")
    
    def _parse_scores(self, score_text: str, session: InterviewSession) -> Dict[str, float]:
        """Parse scores from AI response - FAIL LOUDLY IF PARSING FAILS"""
        try:
            # Simple score extraction (look for numbers after keywords)
            import re
            
            scores = {}
            patterns = {
                "technical_score": r"technical.*?(\d+(?:\.\d+)?)",
                "communication_score": r"communication.*?(\d+(?:\.\d+)?)",
                "behavioral_score": r"behavioral.*?(\d+(?:\.\d+)?)",
                "overall_score": r"overall.*?(\d+(?:\.\d+)?)"
            }
            
            for score_type, pattern in patterns.items():
                match = re.search(pattern, score_text.lower())
                if match:
                    score_value = float(match.group(1))
                    if 0 <= score_value <= 10:
                        scores[score_type] = score_value
                    else:
                        raise Exception(f"Invalid score value: {score_value} for {score_type}")
                else:
                    raise Exception(f"Could not extract {score_type} from AI response: {score_text[:200]}...")
            
            # Calculate weighted overall
            weights = config.EVALUATION_CRITERIA
            weighted_overall = (
                scores["technical_score"] * weights["technical_weight"] +
                scores["communication_score"] * weights["communication_weight"] +
                scores["behavioral_score"] * weights["behavioral_weight"] +
                scores["overall_score"] * weights["overall_presentation"]
            )
            
            scores["weighted_overall"] = round(weighted_overall, 1)
            
            return scores
            
        except Exception as e:
            logger.error(f"? CRITICAL: Score parsing failed: {e}")
            logger.error(f"? Score text received: {score_text}")
            raise Exception(f"Score parsing failed: {e}")