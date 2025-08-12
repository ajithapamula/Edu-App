"""
AI Services module for Daily Standup application
Handles all AI-related operations: LLM calls, STT, and conversation management
"""

import os
import time
import logging
import asyncio
import openai
import re
import uuid
from groq import Groq
from typing import List, AsyncGenerator, Tuple, Optional, Dict, Any
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
import concurrent.futures

from .config import config
from .prompts import prompts

logger = logging.getLogger(__name__)

# =============================================================================
# DYNAMIC FRAGMENT PARSING (From Old System)
# =============================================================================

def parse_summary_into_fragments(summary: str) -> Dict[str, str]:
    """
    Parse summary text into fragments based on top-level numbered sections.
    Returns dict with concept titles as keys and content blocks as values.
    """
    if not summary or not summary.strip():
        return {"General": summary or "No content available"}
    
    # Split into lines for processing
    lines = summary.strip().split('\n')
    
    # Pattern to match top-level sections: digit(s) followed by period and space
    section_pattern = re.compile(r'^\s*(\d+)\.\s+(.+)')
    
    fragments = {}
    current_section = None
    current_content = []
    
    for line in lines:
        match = section_pattern.match(line)
        
        if match:
            # Save previous section if exists
            if current_section and current_content:
                fragments[current_section] = '\n'.join(current_content).strip()
            
            # Start new section
            section_num = match.group(1)
            section_title = match.group(2).strip()
            current_section = f"{section_num}. {section_title}"
            current_content = [line]  # Include the header line
        else:
            # Add line to current section
            if current_section:
                current_content.append(line)
            else:
                # Content before any numbered section - treat as introduction
                if "Introduction" not in fragments:
                    fragments["Introduction"] = line
                else:
                    fragments["Introduction"] += '\n' + line
    
    # Don't forget the last section
    if current_section and current_content:
        fragments[current_section] = '\n'.join(current_content).strip()
    
    # Fallback if no numbered sections found
    if not fragments:
        fragments["General"] = summary
    
    logger.info(f"Parsed summary into {len(fragments)} concept fragments: {list(fragments.keys())}")
    return fragments

# =============================================================================
# DATA MODELS
# =============================================================================

class SessionStage(Enum):
    GREETING = "greeting"
    TECHNICAL = "technical"
    COMPLETE = "complete"
    ERROR = "error"

@dataclass
class ConversationExchange:
    timestamp: float
    stage: SessionStage
    ai_message: str
    user_response: str
    transcript_quality: float = 0.0
    chunk_id: Optional[int] = None
    concept: Optional[str] = None
    is_followup: bool = False

@dataclass
class SessionData:
    session_id: str
    test_id: str
    student_id: int
    student_name: str
    session_key: str
    created_at: float
    last_activity: float
    current_stage: SessionStage
    exchanges: List[ConversationExchange] = field(default_factory=list)
    conversation_window: deque = field(default_factory=lambda: deque(maxlen=config.CONVERSATION_WINDOW_SIZE))
    greeting_count: int = 0
    is_active: bool = True
    websocket: Optional[Any] = field(default=None)
    summary_manager: Optional[Any] = field(default=None)
    clarification_attempts: int = field(default=0)
    
    # Fragment-based attributes
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
        exchange = ConversationExchange(
            timestamp=time.time(),
            stage=self.current_stage,
            ai_message=ai_message,
            user_response=user_response,
            transcript_quality=quality,
            chunk_id=chunk_id,
            concept=concept,
            is_followup=is_followup
        )
        self.exchanges.append(exchange)
        self.conversation_window.append(exchange)
        self.last_activity = time.time()

@dataclass
class SummaryChunk:
    id: int
    content: str
    base_questions: List[str]
    current_question_count: int = 0
    completed: bool = False
    follow_up_questions: List[str] = field(default_factory=list)

# =============================================================================
# SHARED CLIENT MANAGER
# =============================================================================

class SharedClientManager:
    """Optimized client management with connection pooling"""
    
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
            logger.info("?? Groq client initialized")
        return self._groq_client
    
    @property 
    def openai_client(self) -> openai.OpenAI:
        if self._openai_client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise Exception("OPENAI_API_KEY not found in environment variables")
            self._openai_client = openai.OpenAI(api_key=api_key)
            logger.info("?? OpenAI client initialized")
        return self._openai_client
    
    @property
    def executor(self):
        return self._executor
    
    async def close_connections(self):
        """Cleanup method for graceful shutdown"""
        if self._executor:
            self._executor.shutdown(wait=True)
        logger.info("?? AI client connections closed")

# Global shared client manager
shared_clients = SharedClientManager()

# =============================================================================
# DYNAMIC FRAGMENT MANAGEMENT SYSTEM (Replacing Fixed Chunk System)
# =============================================================================

class FragmentManager:
    """Dynamic fragment-based question management (from old system)"""
    
    def __init__(self, client_manager, session_data: SessionData):
        self.client_manager = client_manager
        self.session_data = session_data
    
    @property
    def openai_client(self):
        return self.client_manager.openai_client
    
    def initialize_fragments(self, summary: str) -> bool:
        """Initialize fragments and calculate dynamic question targets"""
        try:
            # Parse summary into fragments
            self.session_data.fragments = parse_summary_into_fragments(summary)
            self.session_data.fragment_keys = list(self.session_data.fragments.keys())
            
            # Initialize concept question counts
            self.session_data.concept_question_counts = {
                key: 0 for key in self.session_data.fragment_keys
            }
            
            # Calculate dynamic questions per concept
            self.session_data.questions_per_concept = max(
                config.MIN_QUESTIONS_PER_CONCEPT,
                min(config.MAX_QUESTIONS_PER_CONCEPT,
                    config.TOTAL_QUESTIONS // len(self.session_data.fragment_keys) 
                    if self.session_data.fragment_keys else 1)
            )
            
            logger.info(f"?? Initialized {len(self.session_data.fragment_keys)} fragments, "
                       f"target {self.session_data.questions_per_concept} questions per concept")
            return True
            
        except Exception as e:
            logger.error(f"? Fragment initialization failed: {e}")
            raise Exception(f"Fragment initialization failed: {e}")
    
    def get_active_fragment(self) -> Tuple[str, str]:
        """
        Get the current active concept fragment based on intelligent scheduling.
        Returns (concept_title, concept_content)
        """
        if not self.session_data.fragment_keys:
            return "General", self.session_data.fragments.get("General", "No content available")
        
        # Intelligent concept selection based on coverage and balance
        # Priority: concepts with fewer questions asked
        min_questions = min(self.session_data.concept_question_counts.values())
        underutilized_concepts = [
            concept for concept, count in self.session_data.concept_question_counts.items() 
            if count == min_questions
        ]
        
        # If we have underutilized concepts, pick one
        if underutilized_concepts:
            # Pick the next underutilized concept in order
            for concept in self.session_data.fragment_keys:
                if concept in underutilized_concepts:
                    return concept, self.session_data.fragments[concept]
        
        # If all concepts have been covered equally, cycle through them
        concept_index = self.session_data.question_index % len(self.session_data.fragment_keys)
        selected_concept = self.session_data.fragment_keys[concept_index]
        
        return selected_concept, self.session_data.fragments[selected_concept]
    
    def should_continue_test(self) -> bool:
        """Determine if test should continue using dynamic coverage logic"""
        # Count only non-greeting questions for test logic
        actual_test_questions = len([
            exchange for exchange in self.session_data.exchanges 
            if exchange.concept and not exchange.concept.startswith('greeting')
        ])
        
        # If no test questions yet, continue
        if actual_test_questions == 0:
            return True
            
        # Check for uncovered concepts
        uncovered_concepts = [
            concept for concept, count in self.session_data.concept_question_counts.items() 
            if count == 0
        ]
        if uncovered_concepts:
            logger.info(f"Continuing test: uncovered concepts {uncovered_concepts}")
            return True
            
        # Check for underdeveloped concepts (less than target)
        underdeveloped_concepts = [
            concept for concept, count in self.session_data.concept_question_counts.items() 
            if count < self.session_data.questions_per_concept
        ]
        if len(underdeveloped_concepts) > len(self.session_data.fragment_keys) * 0.3:
            logger.info(f"Continuing test: {len(underdeveloped_concepts)} underdeveloped concepts")
            return True
            
        # Hard limit based on actual test questions
        hard_limit = config.TOTAL_QUESTIONS + (config.TOTAL_QUESTIONS // 2)
        if actual_test_questions >= hard_limit:
            logger.info(f"Stopping test: reached hard limit {hard_limit}")
            return False
            
        # Balance check - if we've reached baseline questions
        if actual_test_questions >= config.TOTAL_QUESTIONS:
            max_questions_any_concept = max(self.session_data.concept_question_counts.values())
            min_questions_any_concept = min(self.session_data.concept_question_counts.values())
            if max_questions_any_concept - min_questions_any_concept <= 1:
                logger.info(f"Stopping test: balanced coverage achieved")
                return False
        
        return True
    
    def get_concept_conversation_history(self, concept: str, window_size: int = 5) -> str:
        """
        Returns conversation history for a specific concept only.
        """
        entries = [
            exchange for exchange in reversed(self.session_data.exchanges)
            if exchange.concept == concept and exchange.user_response
        ]
        last_entries = list(reversed(entries[:window_size]))

        history = []
        for entry in last_entries:
            q = f"Q: {entry.ai_message}"
            a = f"A: {entry.user_response}"
            history.append(f"{q}\n{a}")
        return "\n\n".join(history)
    
    def add_question(self, question: str, concept: str = None, is_followup: bool = False):
        """Add a question with enhanced tracking"""
        # Track concept usage (skip for greeting concepts)
        if concept and concept in self.session_data.concept_question_counts and not concept.startswith('greeting'):
            self.session_data.concept_question_counts[concept] += 1
        
        # Track follow-up questions separately (skip greeting)
        if is_followup and concept and not concept.startswith('greeting'):
            self.session_data.followup_questions += 1
        
        # Set current concept
        self.session_data.current_concept = concept
        
        # Only increment question_index for actual test questions
        if concept and not concept.startswith('greeting'):
            self.session_data.question_index += 1
        
        logger.info(f"Added question (concept: '{concept}', followup: {is_followup}) "
                   f"Question index: {self.session_data.question_index}")
    
    def add_answer(self, answer: str):
        """Add an answer to the last question"""
        if self.session_data.exchanges:
            # Update the last exchange with the answer
            last_exchange = self.session_data.exchanges[-1]
            last_exchange.user_response = answer
    
    def get_progress_info(self) -> Dict[str, Any]:
        """Get current test progress information"""
        return {
            "current_question": self.session_data.question_index,
            "total_concepts": len(self.session_data.fragment_keys),
            "concept_coverage": self.session_data.concept_question_counts,
            "questions_per_concept_target": self.session_data.questions_per_concept,
            "followup_questions": self.session_data.followup_questions,
            "main_questions": self.session_data.question_index - self.session_data.followup_questions
        }

# =============================================================================
# SUMMARY MANAGER (For backward compatibility)
# =============================================================================

# Alias FragmentManager as SummaryManager for backward compatibility
SummaryManager = FragmentManager

# =============================================================================
# AUDIO PROCESSING
# =============================================================================

class OptimizedAudioProcessor:
    def __init__(self, client_manager: SharedClientManager):
        self.client_manager = client_manager
    
    @property
    def groq_client(self):
        return self.client_manager.groq_client
    
    async def transcribe_audio_fast(self, audio_data: bytes) -> Tuple[str, float]:
        """Ultra-fast transcription with improved error handling for small audio"""
        try:
            audio_size = len(audio_data)
            logger.info(f"?? Transcribing {audio_size} bytes of audio")
            
            # More lenient size check - try transcription even with smaller files
            if audio_size < 50:  # Only reject extremely small chunks
                raise Exception(f"Audio data too small for transcription ({audio_size} bytes)")
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.client_manager.executor,
                self._sync_transcribe,
                audio_data
            )
            
            return result
            
        except Exception as e:
            logger.error(f"? Fast transcription error: {e}")
            raise Exception(f"Transcription failed: {e}")
    
    def _sync_transcribe(self, audio_data: bytes) -> Tuple[str, float]:
        """Synchronous transcription for thread pool with better error handling"""
        try:
            audio_size = len(audio_data)
            temp_file = config.TEMP_DIR / f"audio_{int(time.time() * 1000000)}.webm"
            
            with open(temp_file, "wb") as f:
                f.write(audio_data)
            
            logger.info(f"?? Sending {audio_size} bytes to Groq for transcription")
            
            with open(temp_file, "rb") as file:
                result = self.groq_client.audio.transcriptions.create(
                    file=(temp_file.name, file.read()),
                    model=config.GROQ_TRANSCRIPTION_MODEL,
                    response_format="verbose_json",
                    # Add these parameters for better handling of short/quiet audio
                    prompt="Please transcribe this audio clearly, even if it's short or quiet."
                )
            
            try:
                os.remove(temp_file)
            except:
                pass
            
            transcript = result.text.strip() if result.text else ""
            
            if not transcript:
                logger.warning(f"?? Groq returned empty transcript for {audio_size} bytes")
                return "", 0.0
            
            # Fast quality assessment
            quality = min(len(transcript) / 30, 1.0)  # Lowered threshold for shorter responses
            if hasattr(result, 'segments') and result.segments:
                confidences = [seg.get('confidence', 0.8) for seg in result.segments[:3]]
                if confidences:
                    avg_confidence = sum(confidences) / len(confidences)
                    quality = (quality + avg_confidence) / 2
            
            logger.info(f"? Transcription: '{transcript}' (quality: {quality:.2f})")
            return transcript, quality
            
        except Exception as e:
            logger.error(f"? Sync transcription error: {e}")
            # Try to be more specific about the error
            if "file" in str(e).lower() and "format" in str(e).lower():
                raise Exception("Audio format not supported - please check microphone settings")
            elif "timeout" in str(e).lower():
                raise Exception("Transcription service timeout - please try again")
            else:
                raise Exception(f"Groq transcription failed: {e}")

# =============================================================================
# CONVERSATION MANAGEMENT
# =============================================================================

class OptimizedConversationManager:
    def __init__(self, client_manager: SharedClientManager):
        self.client_manager = client_manager
    
    @property
    def openai_client(self):
        return self.client_manager.openai_client
    
    async def generate_fast_response(self, session_data: SessionData, user_input: str) -> str:
        """Generate ultra-fast AI responses with context awareness"""
        try:
            if session_data.current_stage == SessionStage.GREETING:
                return await self._generate_greeting_response(session_data, user_input)
            elif session_data.current_stage == SessionStage.TECHNICAL:
                return await self._generate_technical_response(session_data, user_input)
            else:
                return await self._generate_conclusion_response(session_data, user_input)
                
        except Exception as e:
            logger.error(f"? Fast response generation error: {e}")
            raise Exception(f"AI response generation failed: {e}")
    
    async def _generate_greeting_response(self, session_data: SessionData, user_input: str) -> str:
        """Dynamic greeting responses with context awareness"""
        context = {
            'recent_exchanges': [
                f"AI: {ex.ai_message}, User: {ex.user_response}" 
                for ex in list(session_data.conversation_window)[-2:]
            ]
        }
        
        prompt = prompts.dynamic_greeting_response(user_input, session_data.greeting_count, context)
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            self.client_manager.executor,
            self._sync_openai_call,
            prompt
        )
        
        return response
    
    async def _generate_technical_response(self, session_data: SessionData, user_input: str) -> str:
        """Generate dynamic technical responses - FIXED TO SINGLE API CALL"""
        if not session_data.summary_manager:
            raise Exception("Fragment manager not initialized")
        
        fragment_manager = session_data.summary_manager
        
        # Check if test should continue FIRST
        if not fragment_manager.should_continue_test():
            session_data.current_stage = SessionStage.COMPLETE
            conversation_summary = fragment_manager.get_progress_info()
            
            prompt = prompts.dynamic_session_completion(conversation_summary)
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.client_manager.executor,
                self._sync_openai_call,
                prompt
            )
            return response
        
        # Get current concept information
        current_concept_title, current_concept_content = fragment_manager.get_active_fragment()
        
        # Get conversation history for this concept only
        history = fragment_manager.get_concept_conversation_history(current_concept_title)
        
        # Get the last question asked
        last_question = session_data.exchanges[-1].ai_message if session_data.exchanges else ""
        
        # Get questions count for current concept
        questions_for_concept = session_data.concept_question_counts.get(current_concept_title, 0)
        
        # SINGLE API CALL ONLY - No more double calls
        prompt = prompts.dynamic_followup_response(
            current_concept_title=current_concept_title,
            concept_content=current_concept_content,
            history=history,
            previous_question=last_question,
            user_response=user_input,
            current_question_number=session_data.question_index + 1,
            questions_for_concept=questions_for_concept
        )
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            self.client_manager.executor,
            self._sync_openai_call,
            prompt
        )
        
        # SIMPLE parsing - no additional API calls
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
        
        # Simple decision logic
        if understanding == "YES":
            # Move to next concept
            next_concept_title, _ = fragment_manager.get_active_fragment()
            fragment_manager.add_question(actual_response, next_concept_title, False)
        else:
            # Stay with current concept  
            fragment_manager.add_question(actual_response, current_concept_title, True)
        
        return actual_response
    
    def _parse_llm_response(self, response: str, keys: List[str]) -> Dict[str, str]:
        """Parse structured responses from the LLM"""
        result = {}
        lines = response.strip().split('\n')
        for line in lines:
            for key in keys:
                prefix = f"{key.upper()}:"
                if line.upper().startswith(prefix):
                    result[key.lower()] = line[len(prefix):].strip()
                    break
        return result
    
    async def _generate_conclusion_response(self, session_data: SessionData, user_input: str) -> str:
        """Dynamic conclusion responses with session context"""
        session_context = {
            'key_topics': list(set(ex.chunk_id for ex in session_data.exchanges if ex.chunk_id))[:3],
            'total_exchanges': len(session_data.exchanges)
        }
        
        prompt = prompts.dynamic_conclusion_response(user_input, session_context)
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            self.client_manager.executor,
            self._sync_openai_call,
            prompt
        )
        
        return response
    
    def _build_conversation_context(self, session_data: SessionData) -> str:
        """Build context from sliding window of conversation"""
        context = ""
        for exchange in list(session_data.conversation_window)[-3:]:
            context += f"AI: {exchange.ai_message}\nUser: {exchange.user_response}\n\n"
        return context.strip()
    
    def _sync_openai_call(self, prompt: str) -> str:
        """Synchronous OpenAI call for thread pool"""
        try:
            response = self.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=config.OPENAI_TEMPERATURE,
                max_tokens=config.OPENAI_MAX_TOKENS
            )
            result = response.choices[0].message.content.strip()
            if not result:
                raise Exception("OpenAI returned empty response")
            return result
        except Exception as e:
            logger.error(f"? OpenAI API call failed: {e}")
            raise Exception(f"OpenAI API failed: {e}")
    
    async def generate_fast_evaluation(self, session_data: SessionData) -> Tuple[str, float]:
        """Generate dynamic evaluation based on actual conversation"""
        try:
            conversation_exchanges = []
            for exchange in session_data.exchanges[-10:]:
                if exchange.stage == SessionStage.TECHNICAL:
                    conversation_exchanges.append({
                        'ai_message': exchange.ai_message,
                        'user_response': exchange.user_response,
                        'chunk_id': exchange.chunk_id,
                        'quality': exchange.transcript_quality,
                        'concept': exchange.concept,
                        'is_followup': exchange.is_followup
                    })
            
            if not conversation_exchanges:
                raise Exception("No technical exchanges found for evaluation")
            
            session_stats = {
                'duration_minutes': round((time.time() - session_data.created_at) / 60, 1),
                'avg_response_length': sum(len(ex['user_response']) for ex in conversation_exchanges) // len(conversation_exchanges),
                'total_concepts': len(session_data.fragment_keys),
                'concepts_covered': len([c for c, count in session_data.concept_question_counts.items() if count > 0]),
                'coverage_percentage': round(
                    (len([c for c, count in session_data.concept_question_counts.items() if count > 0]) 
                     / len(session_data.fragment_keys) * 100) 
                    if session_data.fragment_keys else 0, 1
                ),
                'main_questions': session_data.question_index - session_data.followup_questions,
                'followup_questions': session_data.followup_questions,
                'questions_per_concept': dict(session_data.concept_question_counts)
            }
            
            concepts_covered = [c for c, count in session_data.concept_question_counts.items() if count > 0]
            
            prompt = prompts.dynamic_fragment_evaluation(concepts_covered, conversation_exchanges, session_stats)
            
            loop = asyncio.get_event_loop()
            evaluation = await loop.run_in_executor(
                self.client_manager.executor,
                self._sync_openai_call,
                prompt
            )
            
            score_match = re.search(r'Score:\s*(\d+(?:\.\d+)?)/10', evaluation)
            if not score_match:
                raise Exception(f"Could not extract score from evaluation: {evaluation}")
                
            score = float(score_match.group(1))
            
            return evaluation, score
            
        except Exception as e:
            logger.error(f"? Fast evaluation error: {e}")
            raise Exception(f"Evaluation generation failed: {e}")