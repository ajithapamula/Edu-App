# Edu-app/core/ai_services.py
# Summary-based behavioral questions + Smart follow-ups + Improved evaluation with accuracy

import os, time, logging, asyncio, re, random, tempfile
from typing import List, Tuple, Optional, Dict, Any
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

import openai as openai_sync
from groq import Groq, AsyncGroq
from openai import AsyncOpenAI

from .config import config
from .prompts import (
    prompts as ds_prompts, build_evaluation_prompt, SCORING_PROMPT_TEMPLATE,
    build_technical_question_prompt, build_hr_question_prompt,
    build_communication_question_prompt, build_communication_followup_prompt,
    WRONG_ANSWER_RESPONSES, SILENCE_ENCOURAGEMENT_RESPONSES, PromptTemplates
)

logger = logging.getLogger(__name__)

# =============================================================================
# ROUND DURATIONS - Communication: 10 min, Technical: 25 min, HR: 10 min
# =============================================================================
ROUND_DURATIONS = {
    "introduction": 60,       # 1 minute
    "communication": 600,     # 10 minutes
    "technical": 1500,        # 25 minutes
    "hr": 600,                # 10 minutes
}

# =============================================================================
# TECHNICAL BEHAVIORAL QUESTIONS - Mix with pure technical questions
# =============================================================================
TECHNICAL_BEHAVIORAL_QUESTIONS = [
    "Tell me about a challenging technical problem you solved recently.",
    "Describe a time when you had to learn a new technology quickly.",
    "How do you approach debugging a complex issue?",
    "Tell me about a project where you had to collaborate with others.",
    "Describe a time you had to meet a tight deadline.",
    "How do you stay updated with new technologies?",
    "Tell me about a time you improved an existing process.",
    "Describe a situation where you had to explain technical concepts to non-technical people.",
    "How do you handle disagreements about technical decisions?",
    "Tell me about a time you received critical feedback on your work.",
    "Describe your approach to code reviews.",
    "How do you prioritize tasks when working on multiple projects?",
    "Tell me about a time you made a mistake and how you handled it.",
    "Describe a successful project you're proud of.",
    "How do you ensure quality in your work?",
]

# =============================================================================
# HR BEHAVIORAL QUESTIONS POOL - Never repeat
# =============================================================================
HR_QUESTIONS_POOL = [
    "Describe a time you overcame a significant challenge at work.",
    "Tell me about a time you demonstrated leadership.",
    "How do you handle conflict with a colleague?",
    "Describe a situation where you had to adapt to change.",
    "What motivates you at work?",
    "How do you handle criticism?",
    "Where do you see yourself in 5 years?",
    "Describe a time you took initiative.",
    "How do you manage stress?",
    "Tell me about a time you failed and what you learned.",
    "What's your biggest strength?",
    "What's an area you're working to improve?",
    "Describe your ideal work environment.",
    "How do you prioritize work-life balance?",
    "Tell me about a time you went above and beyond.",
]

# =============================================================================
# RESPONSE TEMPLATES
# =============================================================================

COMMUNICATION_TRANSITIONS = [
    "That's interesting! ", "Nice! ", "Great to know! ", "Thanks for sharing! ",
    "That sounds wonderful! ", "How lovely! ", "That's cool! ", "Awesome! ",
    "That's really nice! ", "Wonderful! ", "Oh, that's great! ", "I like that! ",
    "Sounds fun! ", "That's fantastic! ", "How interesting! ", "Good to know! ",
]

FOLLOWUP_ACKS = ["Oh interesting!", "That's nice!", "I see!", "That sounds great!", "Nice!", "Lovely!", "Oh really?", "That's cool!", "Wow!", "Fascinating!"]

TECHNICAL_GOOD_ACKS = ["Good explanation!", "That's correct!", "Nice approach!", "Well explained!", "Good point!", "Exactly right!", "Great understanding!", "Well done!", "Perfect!", "Excellent!"]

TECHNICAL_NEUTRAL_ACKS = ["I see.", "Okay.", "Alright.", "Got it.", "Understood.", "Fair enough."]

DONT_KNOW_RESPONSES = [
    "That's okay! Let me ask you something different.",
    "No problem at all! Here's another question.",
    "It's fine! Let's try a different one.",
    "No worries! Let me change the topic.",
    "That's alright! Moving to something else.",
]

WEAK_RESPONSE_ACKS = [
    "I see. Let me ask you something else.",
    "Okay, let's try a different question.",
    "Alright, let me move to another topic.",
    "Got it. Here's a different one.",
    "Understood. Let me ask something else.",
]

SKIP_RESPONSES = [
    "Sure! Let's move on.",
    "No problem, next one.",
    "Of course! Here's another.",
    "Got it, moving forward.",
]

REPEAT_RESPONSES = [
    "Of course! The question was:",
    "Sure, let me repeat:",
    "No problem! Here it is again:",
]

HR_ACKS = [
    "Thank you for sharing.",
    "That's a good point.",
    "I appreciate that.",
    "Interesting.",
    "Good to know.",
]

# =============================================================================
# DAILY STANDUP (DS_*) - Simplified
# =============================================================================

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
    conversation_window: deque = field(default_factory=lambda: deque(maxlen=10))
    greeting_count: int = 0
    is_active: bool = True
    websocket: Optional[Any] = None
    summary_manager: Optional[Any] = None
    fragments: Dict[str, str] = field(default_factory=dict)
    fragment_keys: List[str] = field(default_factory=list)
    concept_question_counts: Dict[str, int] = field(default_factory=dict)
    current_concept: str = ""
    question_index: int = 0
    followup_questions: int = 0

    def add_exchange(self, ai_message: str, user_response: str, quality: float = 0.0, chunk_id: Optional[int] = None, concept: Optional[str] = None, is_followup: bool = False):
        self.exchanges.append(DS_ConversationExchange(timestamp=time.time(), stage=self.current_stage, ai_message=ai_message, user_response=user_response, transcript_quality=quality, chunk_id=chunk_id, concept=concept, is_followup=is_followup))
        self.last_activity = time.time()

class DS_SharedClientManager:
    def __init__(self):
        self._groq_client = None
        self._openai_client = None
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    @property
    def groq_client(self):
        if not self._groq_client:
            self._groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        return self._groq_client

    @property
    def openai_client(self):
        if not self._openai_client:
            self._openai_client = openai_sync.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return self._openai_client

    @property
    def executor(self):
        return self._executor

    async def close_connections(self):
        if self._executor:
            self._executor.shutdown(wait=True)

ds_shared_clients = DS_SharedClientManager()

class DS_FragmentManager:
    def __init__(self, client_manager, session_data):
        self.client_manager = client_manager
        self.session_data = session_data

    def initialize_fragments(self, summary: str) -> bool:
        self.session_data.fragments = {"General": summary or "No content"}
        self.session_data.fragment_keys = list(self.session_data.fragments.keys())
        return True

    def get_active_fragment(self):
        return "General", self.session_data.fragments.get("General", "")

    def should_continue_test(self):
        return len(self.session_data.exchanges) < 10

    def add_question(self, question, concept=None, is_followup=False):
        self.session_data.question_index += 1

DS_SummaryManager = DS_FragmentManager

class DS_OptimizedAudioProcessor:
    def __init__(self, client_manager):
        self.client_manager = client_manager

    async def transcribe_audio_fast(self, audio_data: bytes) -> Tuple[str, float]:
        return "transcribed text", 0.8

class DS_OptimizedConversationManager:
    def __init__(self, client_manager):
        self.client_manager = client_manager

    async def generate_fast_response(self, session_data, user_input: str) -> str:
        return "Thank you for your response."

    async def generate_fast_evaluation(self, session_data) -> Tuple[str, float]:
        return "Evaluation complete.", 7.0

# =============================================================================
# WEEKLY INTERVIEW (WI_*) - DATACLASSES
# =============================================================================

class WI_InterviewStage(Enum):
    INTRODUCTION = "introduction"
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
    answer_quality: str = "neutral"
    topic_category: str = ""
    expected_keywords: List[str] = field(default_factory=list)
    technical_accuracy: Optional[float] = None
    question_type: str = "general"  # "technical", "behavioral", "hr"

@dataclass
class WI_ConversationState:
    current_topic: str = ""
    last_question: str = ""
    last_user_response: str = ""
    followups_on_topic: int = 0
    max_followups: int = 2
    topics_discussed: List[str] = field(default_factory=list)
    used_transitions: List[str] = field(default_factory=list)
    extracted_topics: List[str] = field(default_factory=list)
    user_mentioned_tech: List[str] = field(default_factory=list)

@dataclass
class WI_InterviewSession:
    session_id: str
    test_id: str
    student_id: int
    student_name: str
    session_key: str
    created_at: float
    last_activity: float
    current_stage: WI_InterviewStage = WI_InterviewStage.INTRODUCTION
    is_active: bool = True
    websocket: Optional[Any] = None
    content_context: str = ""
    fragment_keys: List[str] = field(default_factory=list)
    current_concept: Optional[str] = None
    fragment_manager: Optional[Any] = None
    exchanges: List[WI_ConversationExchange] = field(default_factory=list)
    round_start_times: Dict[str, float] = field(default_factory=dict)
    questions_per_round: Dict[str, int] = field(default_factory=lambda: {"introduction": 0, "communication": 0, "technical": 0, "hr": 0})
    concept_question_counts: Dict[str, int] = field(default_factory=dict)
    followup_questions: int = 0
    silence_prompt_count: int = 0
    current_difficulty: str = "medium"
    last_answer_quality: str = "neutral"
    conversation_state: WI_ConversationState = field(default_factory=WI_ConversationState)
    questions_asked: List[str] = field(default_factory=list)
    communication_topics_covered: List[str] = field(default_factory=list)
    technical_topics_covered: List[str] = field(default_factory=list)
    hr_topics_covered: List[str] = field(default_factory=list)
    introduction_completed: bool = False
    behavioral_questions_in_technical: int = 0
    last_was_repeat: bool = False
    
    # NEW: Track topics where user was silent - skip these entirely
    silent_topics: List[str] = field(default_factory=list)
    topic_attempt_count: Dict[str, int] = field(default_factory=dict)  # Track attempts per topic
    used_behavioral_questions: List[str] = field(default_factory=list)  # Track used behavioral Q's
    used_hr_questions: List[str] = field(default_factory=list)  # Track used HR Q's
    technical_question_count: int = 0  # Count pure technical questions
    behavioral_question_count: int = 0  # Count behavioral questions in technical
    
    # Extracted from summaries
    extracted_technologies: List[str] = field(default_factory=list)
    extracted_projects: List[str] = field(default_factory=list)
    extracted_challenges: List[str] = field(default_factory=list)
    extracted_team_info: List[str] = field(default_factory=list)
    
    # For evaluation accuracy
    technical_answers: List[Dict[str, Any]] = field(default_factory=list)
    correct_answers: int = 0
    partial_answers: int = 0
    wrong_answers: int = 0
    
    def __post_init__(self):
        """Initialize time tracking after object creation"""
        # Set interview start time to created_at (when session was created)
        self.interview_start_time = self.created_at
        logger.info(f"[WI] Session initialized. Interview start time: {self.interview_start_time}")

    def start_round(self, stage: WI_InterviewStage):
        current_time = time.time()
        logger.info(f"[WI] ===== STARTING ROUND: {stage.value} =====")
        logger.info(f"[WI] Current time: {current_time}")
        logger.info(f"[WI] Previous round_start_times: {self.round_start_times}")
        
        self.round_start_times[stage.value] = current_time
        self.current_stage = stage
        self.conversation_state = WI_ConversationState()
        
        logger.info(f"[WI] New round_start_times: {self.round_start_times}")
        logger.info(f"[WI] Current stage set to: {self.current_stage.value}")

    def get_round_elapsed_time(self) -> float:
        current_stage_value = self.current_stage.value
        current_time = time.time()
        
        if current_stage_value not in self.round_start_times:
            logger.warning(f"[WI] ⚠️ Round {current_stage_value} has no start time! Setting now.")
            self.round_start_times[current_stage_value] = current_time
            return 0.0
        
        start_time = self.round_start_times[current_stage_value]
        elapsed = current_time - start_time
        return elapsed

    def get_round_elapsed_minutes(self) -> float:
        return self.get_round_elapsed_time() / 60
    
    def get_total_interview_time_minutes(self) -> float:
        """Get total time since interview started"""
        if not hasattr(self, 'interview_start_time') or self.interview_start_time is None:
            self.interview_start_time = self.created_at
        return (time.time() - self.interview_start_time) / 60
    
    def get_questions_in_current_round(self) -> int:
        """Get number of questions asked in current round"""
        return self.questions_per_round.get(self.current_stage.value, 0)

    def add_exchange(self, ai_message: str, user_response: str = "", quality: float = 0.0, concept: str = "", is_followup: bool = False, answer_quality: str = "neutral", expected_keywords: List[str] = None, technical_accuracy: float = None, question_type: str = "general"):
        ex = WI_ConversationExchange(timestamp=time.time(), stage=self.current_stage, ai_message=ai_message, user_response=user_response, transcript_quality=quality, concept=concept, is_followup=is_followup, answer_quality=answer_quality, expected_keywords=expected_keywords or [], technical_accuracy=technical_accuracy, question_type=question_type)
        self.exchanges.append(ex)
        self.questions_per_round[self.current_stage.value] = self.questions_per_round.get(self.current_stage.value, 0) + 1
        self.questions_asked.append(ai_message)

    def update_last_response(self, user_response: str, quality: float, answer_quality: str = "neutral", technical_accuracy: float = None):
        if self.exchanges:
            self.exchanges[-1].user_response = user_response
            self.exchanges[-1].answer_quality = answer_quality
            self.exchanges[-1].technical_accuracy = technical_accuracy
            
            # Track accuracy
            if technical_accuracy is not None:
                if technical_accuracy >= 0.7:
                    self.correct_answers += 1
                elif technical_accuracy >= 0.4:
                    self.partial_answers += 1
                else:
                    self.wrong_answers += 1
        self.last_answer_quality = answer_quality

    def get_stage_conversation_history(self, stage: WI_InterviewStage, limit: int = 10) -> str:
        exs = [e for e in self.exchanges if e.stage == stage][-limit:]
        return "\n".join([f"Q: {e.ai_message}\nA: {e.user_response}" for e in exs if e.user_response])

    def get_questions_asked_in_round(self, stage: WI_InterviewStage) -> List[str]:
        return [e.ai_message for e in self.exchanges if e.stage == stage]

    def get_last_user_response(self) -> str:
        for ex in reversed(self.exchanges):
            if ex.user_response:
                return ex.user_response
        return ""

# =============================================================================
# WI CLIENT MANAGER & FRAGMENT MANAGER
# =============================================================================

class WI_SharedClientManager:
    def __init__(self):
        self.openai_client: Optional[AsyncOpenAI] = None
        self.groq_client: Optional[AsyncGroq] = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        self._initialized = True

    async def close_connections(self):
        if self.openai_client:
            await self.openai_client.close()
        if self.groq_client:
            await self.groq_client.close()
        self.executor.shutdown(wait=True)

wi_shared_clients = WI_SharedClientManager()


class WI_EnhancedInterviewFragmentManager:
    def __init__(self, client_manager, session):
        self.client_manager = client_manager
        self.session = session

    def initialize_fragments(self, summaries) -> bool:
        if not summaries:
            return False
        self.session.content_context = "\n".join([s.get("summary", "") for s in summaries])
        self._extract_summary_info(self.session.content_context)
        self.session.start_round(WI_InterviewStage.INTRODUCTION)
        return True

    def _extract_summary_info(self, content: str):
        """Extract technologies, projects, challenges from summaries for personalized questions"""
        content_lower = content.lower()
        
        # Detect user type: SAP/Non-Developer vs Developer
        sap_keywords = ["sap", "abap", "fiori", "hana", "s/4hana", "s4hana", "mm", "sd", "fico", "pp", "wm", "ewm", "ariba", "successfactors", "bw", "btp", "t-code", "tcode", "transaction", "idoc", "bapi", "rfc", "smartforms", "sapscript", "odata"]
        developer_keywords = ["python", "javascript", "react", "node", "fastapi", "django", "flask", "mongodb", "mysql", "postgresql", "docker", "kubernetes", "aws", "azure", "java", "spring", "typescript", "angular", "vue", "express", "api", "rest", "graphql"]
        
        # Count matches to determine user type
        sap_matches = [k for k in sap_keywords if k in content_lower]
        dev_matches = [k for k in developer_keywords if k in content_lower]
        
        # Determine primary track based on what's ACTUALLY in their summary
        if len(sap_matches) > len(dev_matches):
            # SAP/Non-Developer track - ONLY use SAP technologies
            self.session.extracted_technologies = sap_matches[:10]
            logger.info(f"[WI] Detected SAP track - Technologies: {self.session.extracted_technologies}")
        elif len(dev_matches) > 0:
            # Developer track - ONLY use developer technologies
            self.session.extracted_technologies = dev_matches[:10]
            logger.info(f"[WI] Detected Developer track - Technologies: {self.session.extracted_technologies}")
        else:
            # Fallback: extract any mentioned tech from content
            self.session.extracted_technologies = []
            logger.info(f"[WI] No specific tech detected, will use general questions")
        
        # Projects - extract from summary
        project_patterns = [r"worked on (.+?)(?:\.|,|and)", r"built (.+?)(?:\.|,|and)", r"developed (.+?)(?:\.|,|and)", r"implemented (.+?)(?:\.|,|and)", r"created (.+?)(?:\.|,|and)", r"configured (.+?)(?:\.|,|and)"]
        projects = []
        for pattern in project_patterns:
            projects.extend(re.findall(pattern, content_lower))
        self.session.extracted_projects = list(set(projects))[:5]
        
        # Challenges
        challenge_patterns = [r"challenge.*?was (.+?)(?:\.|,)", r"difficult.*?(.+?)(?:\.|,)", r"problem.*?(.+?)(?:\.|,)", r"issue.*?was (.+?)(?:\.|,)"]
        challenges = []
        for pattern in challenge_patterns:
            challenges.extend(re.findall(pattern, content_lower))
        self.session.extracted_challenges = list(set(challenges))[:3]
        
        # Team info
        if any(word in content_lower for word in ["team", "collaborate", "together", "group", "lead"]):
            self.session.extracted_team_info = ["worked in team"]
        
        logger.info(f"[WI] Final Extracted - Tech: {self.session.extracted_technologies}, Projects: {self.session.extracted_projects[:3]}")

    def should_continue_round(self, stage) -> bool:
        if stage == WI_InterviewStage.INTRODUCTION:
            return not self.session.introduction_completed
        duration = ROUND_DURATIONS.get(stage.value, 600)
        return self.session.get_round_elapsed_time() < duration

    def get_round_time_remaining(self) -> float:
        duration = ROUND_DURATIONS.get(self.session.current_stage.value, 600)
        return max(0, duration - self.session.get_round_elapsed_time())

    def add_question(self, question, concept, is_followup=False):
        pass


class WI_OptimizedAudioProcessor:
    def __init__(self, client_manager):
        self.client_manager = client_manager

    async def transcribe_audio_fast(self, audio_data: bytes) -> Tuple[str, float]:
        await self.client_manager.initialize()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
            tf.write(audio_data)
            temp_path = tf.name
        try:
            with open(temp_path, "rb") as f:
                tr = await self.client_manager.groq_client.audio.transcriptions.create(file=(temp_path, f.read()), model="whisper-large-v3-turbo", language="en")
            txt = tr.text.strip() if hasattr(tr, 'text') else ""
            logger.info(f"[WI] Transcript: {txt}")
            return txt, min(len(txt.split()) / 10, 1.0)
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

# =============================================================================
# WI CONVERSATION MANAGER - Main Logic
# =============================================================================

class WI_OptimizedConversationManager:
    def __init__(self, client_manager):
        self.client_manager = client_manager

    def _detect_user_intent(self, user_response: str) -> str:
        r = user_response.lower().strip()
        if any(p in r for p in ["skip", "next question", "move on", "next one", "pass"]):
            return "skip"
        if any(p in r for p in ["repeat", "say again", "can you repeat", "what was the question"]):
            return "repeat"
        if any(p in r for p in ["i don't know", "i'm not sure", "no idea", "can't answer", "don't remember"]):
            return "dont_know"
        return "normal"

    def _assess_answer_quality(self, user_response: str) -> str:
        if not user_response:
            return "silence"
        intent = self._detect_user_intent(user_response)
        if intent != "normal":
            return "skip" if intent == "skip" else ("repeat" if intent == "repeat" else "cant_answer")
        words = len(user_response.split())
        if words <= 3:
            return "weak"
        strong = ["because", "therefore", "for example", "specifically", "implemented", "experience", "i think", "used", "worked", "built", "designed"]
        if words >= 20 and any(k in user_response.lower() for k in strong):
            return "strong"
        return "neutral" if words >= 10 else "weak"

    async def _evaluate_technical_accuracy(self, session, question: str, answer: str, expected_keywords: List[str]) -> float:
        """Evaluate technical accuracy of answer using LLM"""
        if not answer or len(answer.split()) < 3:
            return 0.0
        
        await self.client_manager.initialize()
        
        prompt = f"""Evaluate this technical interview answer.

Question: {question}
Answer: {answer}
Context (user's work): {session.content_context[:500] if session.content_context else 'General'}

Rate accuracy from 0.0 to 1.0:
- 1.0 = Correct, detailed, shows understanding
- 0.7 = Mostly correct, some details
- 0.5 = Partially correct, missing key points
- 0.3 = Vague or mostly incorrect
- 0.0 = Wrong or no real answer

Reply with ONLY a number between 0.0 and 1.0"""

        try:
            resp = await self.client_manager.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1, max_tokens=10
            )
            score_text = resp.choices[0].message.content.strip()
            score = float(re.search(r"(\d+\.?\d*)", score_text).group(1))
            return min(max(score, 0.0), 1.0)
        except:
            # Fallback: keyword-based scoring
            answer_lower = answer.lower()
            if expected_keywords:
                matches = sum(1 for k in expected_keywords if k.lower() in answer_lower)
                return min(matches / len(expected_keywords), 1.0)
            return 0.5 if len(answer.split()) > 10 else 0.3

    def _extract_topics_from_response(self, response: str, session=None) -> List[str]:
        """Extract mentioned topics/technologies from user response - ONLY their known tech"""
        response_lower = response.lower()
        
        # If session available, only look for their technologies
        if session and session.extracted_technologies:
            return [t for t in session.extracted_technologies if t in response_lower]
        
        # Fallback: detect any tech
        all_tech = ["python", "javascript", "react", "node", "api", "database", "mongodb", "mysql", "docker", "aws", "frontend", "backend", "testing", "debugging", "git", "sap", "abap", "fiori", "hana", "mm", "sd", "fico"]
        return [t for t in all_tech if t in response_lower]

    def _get_unique_transition(self, session) -> str:
        used = session.conversation_state.used_transitions
        available = [t for t in COMMUNICATION_TRANSITIONS if t not in used] or COMMUNICATION_TRANSITIONS
        t = random.choice(available)
        session.conversation_state.used_transitions.append(t)
        if len(session.conversation_state.used_transitions) > 10:
            session.conversation_state.used_transitions = session.conversation_state.used_transitions[-10:]
        return t

    def _should_followup(self, session, quality) -> bool:
        if quality in ["weak", "cant_answer", "silence", "skip", "repeat"]:
            return False
        if session.conversation_state.followups_on_topic >= 2:
            return False
        return random.random() < (0.6 if quality == "strong" else 0.4)

    def _adjust_difficulty(self, session, quality):
        if session.current_stage != WI_InterviewStage.TECHNICAL:
            return
        if quality == "strong":
            session.current_difficulty = "hard" if session.current_difficulty == "medium" else "medium"
        elif quality in ["weak", "cant_answer"]:
            session.current_difficulty = "easy"

    # =========================================================================
    # QUESTION GENERATORS - Based on Summary & User Response
    # =========================================================================

    async def _generate_communication_question(self, session, is_first=False) -> str:
        await self.client_manager.initialize()
        asked = session.get_questions_asked_in_round(WI_InterviewStage.COMMUNICATION)
        
        # Wide variety of casual topics for natural conversation
        topics = [
            "weekend plans", "favorite food", "travel dreams", "morning routine",
            "favorite movie or show", "music preferences", "childhood memories",
            "dream vacation", "favorite season", "cooking or eating out",
            "pets or animals", "sports or fitness", "books or reading",
            "family traditions", "city or countryside", "coffee or tea",
            "early bird or night owl", "relaxation methods", "learning something new",
            "favorite holiday", "hometown memories", "friends and social life",
            "dream job as a child", "favorite game", "weather preferences"
        ]
        
        # Pick topic not yet discussed
        used_topics = session.communication_topics_covered
        available = [t for t in topics if t not in used_topics]
        if not available:
            available = topics
        
        chosen_topic = random.choice(available)
        session.communication_topics_covered.append(chosen_topic)
        
        prompt = f"""Generate ONE friendly casual question about: {chosen_topic}
Keep it natural like a human conversation.
Already asked (DO NOT repeat): {asked[-5:]}
MAX 12 words. Just the question."""

        resp = await self.client_manager.openai_client.chat.completions.create(
            model=config.OPENAI_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.9, max_tokens=30)
        q = resp.choices[0].message.content.strip()
        
        # Ensure not duplicate
        q_lower = q.lower()
        for asked_q in asked:
            if self._is_similar_question(q_lower, asked_q.lower()):
                # Generate fallback
                q = random.choice([
                    f"What do you think about {chosen_topic}?",
                    f"Tell me about your {chosen_topic}?",
                    f"How do you feel about {chosen_topic}?",
                ])
                break
        
        return q if '?' in q else q + "?"
    
    def _is_similar_question(self, q1: str, q2: str) -> bool:
        """Check if two questions are too similar - STRICTER check"""
        # Clean up questions
        q1_clean = q1.lower().strip().rstrip('?').strip()
        q2_clean = q2.lower().strip().rstrip('?').strip()
        
        # Exact match
        if q1_clean == q2_clean:
            return True
        
        # Word overlap check
        words1 = set(q1_clean.split())
        words2 = set(q2_clean.split())
        
        # Remove common words
        common_words = {'what', 'how', 'why', 'when', 'where', 'who', 'is', 'are', 'the', 'a', 'an', 'your', 'you', 'can', 'do', 'did', 'does', 'tell', 'me', 'about', 'describe', 'explain'}
        words1 = words1 - common_words
        words2 = words2 - common_words
        
        if len(words1) == 0 or len(words2) == 0:
            return False
        
        overlap = len(words1 & words2)
        min_len = min(len(words1), len(words2))
        
        # If more than 40% overlap, consider similar (stricter than before)
        return overlap / min_len > 0.4

    async def _generate_dynamic_ack(self, context: str, tone: str = "friendly") -> str:
        """Generate dynamic acknowledgment based on context"""
        await self.client_manager.initialize()
        
        prompts = {
            "weak": "Generate ONE short understanding response when someone gives unclear answer. Like 'I see, let me try another question' or 'Okay, let's move on'. MAX 8 words.",
            "good": "Generate ONE short positive acknowledgment like 'That's nice!' or 'Good to know!' MAX 5 words.",
            "technical_good": "Generate ONE short praise for good technical answer like 'Well explained!' or 'Good point!' MAX 5 words.",
            "technical_weak": "Generate ONE short understanding response for unclear technical answer. MAX 8 words.",
            "cant_answer": "Generate ONE short supportive response when someone can't answer, like 'No problem, let's try something else'. MAX 10 words.",
            "transition": "Generate ONE short transition phrase like 'Interesting!' or 'Nice!' MAX 3 words.",
            "hr": "Generate ONE short professional acknowledgment like 'Thank you for sharing' or 'Good point'. MAX 5 words.",
        }
        
        prompt = prompts.get(tone, prompts["good"])
        
        try:
            resp = await self.client_manager.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=20
            )
            ack = resp.choices[0].message.content.strip()
            # Clean up
            ack = ack.replace('"', '').replace("'", "")
            if not ack.endswith(('!', '.', '?')):
                ack += '!'
            return ack
        except:
            # Fallback
            fallbacks = {
                "weak": "I see. Let me ask something else.",
                "good": "Nice!",
                "technical_good": "Good explanation!",
                "technical_weak": "Okay, let's try another one.",
                "cant_answer": "No problem! Let's move on.",
                "transition": "Interesting!",
                "hr": "Thank you.",
            }
            return fallbacks.get(tone, "Okay!")

    async def _generate_communication_followup(self, session, user_response: str) -> str:
        """Generate follow-up based on what user just said"""
        await self.client_manager.initialize()
        
        prompt = f"""User said: "{user_response[:100]}"
Generate a short follow-up question. MAX 12 words."""

        resp = await self.client_manager.openai_client.chat.completions.create(
            model=config.OPENAI_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.8, max_tokens=30)
        q = resp.choices[0].message.content.strip()
        return q if '?' in q else q + "?"

    async def _generate_technical_question(self, session, user_response: str = "", include_behavioral: bool = False) -> Tuple[str, List[str]]:
        """Generate technical question - NEVER repeat, enforce behavioral mix"""
        await self.client_manager.initialize()
        
        # Calculate behavioral ratio: aim for 40% behavioral, 60% pure technical
        total_tech_questions = session.technical_question_count + session.behavioral_question_count
        current_behavioral_ratio = session.behavioral_question_count / max(total_tech_questions, 1)
        
        # Force behavioral if ratio is too low and we haven't used all behavioral questions
        should_be_behavioral = (
            include_behavioral and 
            current_behavioral_ratio < 0.4 and 
            len(session.used_behavioral_questions) < len(TECHNICAL_BEHAVIORAL_QUESTIONS) and
            random.random() < 0.5  # 50% chance when below ratio
        )
        
        # Also random 25% chance for behavioral
        if include_behavioral and random.random() < 0.25 and len(session.used_behavioral_questions) < len(TECHNICAL_BEHAVIORAL_QUESTIONS):
            should_be_behavioral = True
        
        if should_be_behavioral:
            return await self._generate_technical_behavioral_question(session)
        
        # Pure technical question
        session.technical_question_count += 1
        asked = session.get_questions_asked_in_round(WI_InterviewStage.TECHNICAL)
        all_asked = session.questions_asked  # ALL questions across entire interview
        
        # Build tech list, excluding topics where user was silent
        tech_list = session.extracted_technologies if session.extracted_technologies else ["general concepts"]
        available_tech = [t for t in tech_list if t not in session.silent_topics]
        
        if not available_tech:
            # All topics exhausted, reset but avoid recently asked
            available_tech = tech_list
        
        # Pick a technology not recently asked about (last 3 questions)
        recent_tech_asked = []
        for q in asked[-3:]:
            for t in available_tech:
                if t.lower() in q.lower():
                    recent_tech_asked.append(t)
        
        final_available = [t for t in available_tech if t not in recent_tech_asked]
        if not final_available:
            final_available = available_tech
        
        chosen_tech = random.choice(final_available)
        session.technical_topics_covered.append(chosen_tech)
        
        # Track attempt on this topic
        session.topic_attempt_count[chosen_tech] = session.topic_attempt_count.get(chosen_tech, 0) + 1
        
        # Different question types - rotate through them
        question_types = [
            f"explain the purpose of {chosen_tech}",
            f"how you implemented {chosen_tech}",
            f"benefits of using {chosen_tech}",
            f"challenges you faced with {chosen_tech}",
            f"when to use {chosen_tech}",
            f"key features of {chosen_tech}",
            f"how {chosen_tech} works",
            f"your experience configuring {chosen_tech}",
        ]
        
        # Remove question types already asked for this tech
        used_types_for_tech = []
        for q in all_asked:
            if chosen_tech.lower() in q.lower():
                for qt in question_types:
                    if any(word in q.lower() for word in qt.lower().split()[:3]):
                        used_types_for_tech.append(qt)
        
        available_types = [qt for qt in question_types if qt not in used_types_for_tech]
        if not available_types:
            available_types = question_types
        
        chosen_type = random.choice(available_types)
        
        prompt = f"""Generate ONE short technical question about: {chosen_type}
User's context: {session.content_context[:200] if session.content_context else 'General'}
NEVER ask these exact questions: {asked[-3:]}
Difficulty: {session.current_difficulty}
MAX 15 words. Just the question, no preamble."""

        resp = await self.client_manager.openai_client.chat.completions.create(
            model=config.OPENAI_MODEL, 
            messages=[{"role": "user", "content": prompt}], 
            temperature=0.8, max_tokens=40
        )
        
        question = resp.choices[0].message.content.strip()
        
        # Validate not casual topic
        casual_words = ["movie", "music", "hobby", "food", "travel", "weekend", "favorite"]
        if any(w in question.lower() for w in casual_words):
            question = f"Can you explain {chosen_tech} in simple terms?"
        
        # STRICT duplicate check against ALL questions
        is_duplicate = False
        for asked_q in all_asked:
            if self._is_similar_question(question.lower(), asked_q.lower()):
                is_duplicate = True
                break
        
        if is_duplicate:
            # Generate completely unique fallback
            fallback_templates = [
                f"What are the key steps in {chosen_tech}?",
                f"How did you configure {chosen_tech}?",
                f"What problems does {chosen_tech} solve?",
                f"Describe your workflow with {chosen_tech}.",
                f"What's important to know about {chosen_tech}?",
            ]
            # Find unused fallback
            for fb in fallback_templates:
                if not any(self._is_similar_question(fb.lower(), aq.lower()) for aq in all_asked):
                    question = fb
                    break
            else:
                # All fallbacks used, create unique one
                question = f"Tell me something new about {chosen_tech} that we haven't discussed."
        
        if '?' not in question:
            question += "?"
        
        keywords = [chosen_tech] if chosen_tech != "general concepts" else ["implementation"]
        return question, keywords

    async def _generate_technical_behavioral_question(self, session) -> Tuple[str, List[str]]:
        """Generate behavioral question for technical round - NEVER repeat"""
        session.behavioral_question_count += 1
        
        # Find unused behavioral question
        available_questions = [q for q in TECHNICAL_BEHAVIORAL_QUESTIONS if q not in session.used_behavioral_questions]
        
        if not available_questions:
            # All used, generate dynamic one
            await self.client_manager.initialize()
            tech = session.extracted_technologies[0] if session.extracted_technologies else "your work"
            
            prompt = f"""Generate ONE unique behavioral question about {tech} experience.
NEVER ask: {session.used_behavioral_questions[-3:]}
MAX 15 words. Just the question."""

            resp = await self.client_manager.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.9, max_tokens=40)
            
            question = resp.choices[0].message.content.strip()
        else:
            question = random.choice(available_questions)
        
        session.used_behavioral_questions.append(question)
        
        if '?' not in question:
            question += "?"
        
        keywords = ["experience", "challenge", "learned", "approach"]
        return question, keywords

    async def _generate_hr_question(self, session, db_manager=None) -> Tuple[str, List[str]]:
        """Generate HR question - NEVER repeat, use pool first"""
        
        # First, try to use questions from the pool that haven't been used
        available_pool = [q for q in HR_QUESTIONS_POOL if q not in session.used_hr_questions]
        
        if available_pool:
            question = random.choice(available_pool)
            session.used_hr_questions.append(question)
        else:
            # Pool exhausted, generate dynamic question
            await self.client_manager.initialize()
            asked = session.get_questions_asked_in_round(WI_InterviewStage.HR)
            all_hr_asked = session.used_hr_questions
            
            prompt = f"""Generate ONE unique HR/behavioral question.
NEVER ask these: {all_hr_asked[-5:]}
MAX 12 words. Just the question, no preamble."""

            resp = await self.client_manager.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.9, max_tokens=35)
            
            question = resp.choices[0].message.content.strip()
            
            # Check for duplicate
            is_duplicate = False
            for asked_q in all_hr_asked:
                if self._is_similar_question(question.lower(), asked_q.lower()):
                    is_duplicate = True
                    break
            
            if is_duplicate:
                # Create unique fallback
                fallback_options = [
                    "What's a recent accomplishment you're proud of?",
                    "How do you approach learning new skills?",
                    "Describe a time you helped a colleague.",
                    "What does success mean to you?",
                    "How do you stay organized?",
                ]
                for fb in fallback_options:
                    if fb not in all_hr_asked:
                        question = fb
                        break
                else:
                    question = "What else would you like me to know about you?"
            
            session.used_hr_questions.append(question)
        
        if '?' not in question:
            question += "?"
        
        keywords = ["strength", "motivation", "growth", "experience"]
        return question, keywords

    async def _generate_smart_followup(self, session, user_response: str, current_stage: WI_InterviewStage) -> str:
        """Generate short follow-up based on user's response"""
        await self.client_manager.initialize()
        
        prompt = f"""User said: "{user_response[:80]}"
Generate a short follow-up question. MAX 12 words."""

        resp = await self.client_manager.openai_client.chat.completions.create(
            model=config.OPENAI_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.7, max_tokens=30)
        
        q = resp.choices[0].message.content.strip()
        return q if '?' in q else q + "?"

    # =========================================================================
    # MAIN RESPONSE GENERATION
    # =========================================================================

    async def generate_first_question(self, session) -> str:
        return await self.generate_introduction(session)

    async def generate_introduction(self, session) -> str:
        """Generate the interview introduction message - OLD STYLE RESTORED"""
        return f"""Hello {session.student_name}! Welcome to your weekly interview session. I'm excited to chat with you today!

We'll have three rounds:
• First, a Communication round (about 10 minutes) where we'll have a casual conversation and get to know each other.
• Then, a Technical round (about 25 minutes) where we'll discuss your recent work and technical knowledge.
• Finally, an HR round (about 10 minutes) with some behavioral questions.

So, how are you doing today? Ready to get started?"""

    async def generate_silence_response(self, session) -> str:
        session.silence_prompt_count += 1
        return random.choice(["Take your time.", "I'm here when you're ready.", "Would you like me to repeat?", "No rush, think about it."])

    async def generate_fast_response(self, session, user_response: str, db_manager=None) -> str:
        await self.client_manager.initialize()
        
        quality = self._assess_answer_quality(user_response)
        logger.info(f"[WI] Quality: {quality}, Stage: {session.current_stage.value}")
        
        if quality != "silence":
            session.silence_prompt_count = 0
        
        # Update conversation state with user's response
        session.conversation_state.last_user_response = user_response
        mentioned_tech = self._extract_topics_from_response(user_response, session)
        session.conversation_state.user_mentioned_tech.extend(mentioned_tech)
        
        # Handle REPEAT - return special marker so main.py doesn't add exchange
        if quality == "repeat":
            if session.exchanges:
                repeat_response = f"{random.choice(REPEAT_RESPONSES)} {session.exchanges[-1].ai_message}"
                # Mark this as a repeat so question number doesn't increment
                session.last_was_repeat = True
                return repeat_response
            return "Let me start with a question!"
        
        # Not a repeat
        session.last_was_repeat = False
        
        # Introduction -> Communication
        if session.current_stage == WI_InterviewStage.INTRODUCTION:
            session.introduction_completed = True
            session.start_round(WI_InterviewStage.COMMUNICATION)
            q = await self._generate_communication_question(session, True)
            return f"Great to hear! Let's get to know you. {q}"
        
        # Get timing information
        elapsed = session.get_round_elapsed_minutes()
        total_elapsed = session.get_total_interview_time_minutes()
        questions_in_round = session.get_questions_in_current_round()
        
        # Detailed logging for debugging
        logger.info(f"[WI] ╔══════════════════════════════════════════════════════════")
        logger.info(f"[WI] ║ TIME CHECK FOR SESSION")
        logger.info(f"[WI] ╠══════════════════════════════════════════════════════════")
        logger.info(f"[WI] ║ Current Stage: {session.current_stage.value}")
        logger.info(f"[WI] ║ Round Elapsed: {elapsed:.2f} minutes")
        logger.info(f"[WI] ║ Total Interview Time: {total_elapsed:.2f} minutes")
        logger.info(f"[WI] ║ Questions in this round: {questions_in_round}")
        logger.info(f"[WI] ║ Round start times: {session.round_start_times}")
        logger.info(f"[WI] ║ Current time: {time.time()}")
        logger.info(f"[WI] ╚══════════════════════════════════════════════════════════")
        
        # =====================================================================
        # TIME-BASED TRANSITIONS
        # =====================================================================
        
        # Communication -> Technical after 10 minutes
        if session.current_stage == WI_InterviewStage.COMMUNICATION:
            logger.info(f"[WI] Checking Communication transition: {elapsed:.2f} >= 10 ? {elapsed >= 10}")
            if elapsed >= 10:
                logger.info(f"[WI] ⏰ TRANSITIONING: Communication -> Technical (elapsed: {elapsed:.2f}min >= 10min)")
                session.start_round(WI_InterviewStage.TECHNICAL)
                q, keywords = await self._generate_technical_question(session)
                session.add_exchange(q, expected_keywords=keywords, question_type="technical")
                return f"Nice chatting! Now let's discuss your technical work. {q}"
        
        # Technical -> HR after 25 minutes
        elif session.current_stage == WI_InterviewStage.TECHNICAL:
            logger.info(f"[WI] Checking Technical transition: {elapsed:.2f} >= 25 ? {elapsed >= 25}")
            if elapsed >= 25:
                logger.info(f"[WI] ⏰ TRANSITIONING: Technical -> HR (elapsed: {elapsed:.2f}min >= 25min)")
                session.start_round(WI_InterviewStage.HR)
                q, keywords = await self._generate_hr_question(session, db_manager)
                session.add_exchange(q, expected_keywords=keywords, question_type="hr")
                return f"Great technical discussion! Now some behavioral questions. {q}"
        
        # HR -> Complete after 10 minutes
        elif session.current_stage == WI_InterviewStage.HR:
            logger.info(f"[WI] Checking HR transition: {elapsed:.2f} >= 10 ? {elapsed >= 10}")
            if elapsed >= 10:
                logger.info(f"[WI] ⏰ TRANSITIONING: HR -> Complete (elapsed: {elapsed:.2f}min >= 10min)")
                session.current_stage = WI_InterviewStage.COMPLETE
                return "Thank you! Great interview. Let me generate your detailed feedback..."
        
        # === COMMUNICATION ROUND ===
        if session.current_stage == WI_InterviewStage.COMMUNICATION:
            if quality == "skip":
                q = await self._generate_communication_question(session)
                ack = await self._generate_dynamic_ack("skip", "transition")
                return f"{ack} {q}"
            
            if quality == "silence":
                return await self.generate_silence_response(session)
            
            if quality == "cant_answer":
                q = await self._generate_communication_question(session)
                ack = await self._generate_dynamic_ack("cant answer", "cant_answer")
                return f"{ack} {q}"
            
            # Weak response - acknowledge and ask something different
            if quality == "weak":
                q = await self._generate_communication_question(session)
                ack = await self._generate_dynamic_ack("weak response", "weak")
                return f"{ack} {q}"
            
            # Good response - follow up or new question
            if self._should_followup(session, quality):
                session.conversation_state.followups_on_topic += 1
                q = await self._generate_communication_followup(session, user_response)
                ack = await self._generate_dynamic_ack("good response", "good")
                return f"{ack} {q}"
            
            q = await self._generate_communication_question(session)
            session.conversation_state.followups_on_topic = 0
            ack = await self._generate_dynamic_ack("transition", "transition")
            return f"{ack} {q}"
        
        # === TECHNICAL ROUND ===
        if session.current_stage == WI_InterviewStage.TECHNICAL:
            # Evaluate accuracy of previous answer
            if session.exchanges and session.exchanges[-1].question_type == "technical":
                last_ex = session.exchanges[-1]
                accuracy = await self._evaluate_technical_accuracy(session, last_ex.ai_message, user_response, last_ex.expected_keywords)
                session.update_last_response(user_response, 0.8, quality, accuracy)
                logger.info(f"[WI] Technical accuracy: {accuracy:.2f}")
            
            self._adjust_difficulty(session, quality)
            
            if quality == "skip":
                q, keywords = await self._generate_technical_question(session, "", True)
                session.add_exchange(q, expected_keywords=keywords, question_type="technical")
                ack = await self._generate_dynamic_ack("skip", "transition")
                return f"{ack} {q}"
            
            if quality == "silence":
                # Track the topic user was silent on
                if session.exchanges:
                    last_q = session.exchanges[-1].ai_message.lower()
                    for tech in session.extracted_technologies:
                        if tech.lower() in last_q:
                            # Increment attempt count
                            session.topic_attempt_count[tech] = session.topic_attempt_count.get(tech, 0) + 1
                            # If 2+ attempts, mark as silent topic to skip
                            if session.topic_attempt_count[tech] >= 2:
                                if tech not in session.silent_topics:
                                    session.silent_topics.append(tech)
                                    logger.info(f"[WI] Marking topic '{tech}' as silent - will skip in future")
                            break
                
                # After silence, immediately ask a different topic question (don't just prompt)
                session.silence_prompt_count += 1
                if session.silence_prompt_count >= 2:
                    # Too many silences, move to a completely different question
                    session.silence_prompt_count = 0
                    q, keywords = await self._generate_technical_question(session, "", True)
                    session.add_exchange(q, expected_keywords=keywords, question_type="technical")
                    return f"Let's try something different. {q}"
                
                return await self.generate_silence_response(session)
            
            if quality == "cant_answer":
                # Track the topic they can't answer
                if session.exchanges:
                    last_q = session.exchanges[-1].ai_message.lower()
                    for tech in session.extracted_technologies:
                        if tech.lower() in last_q:
                            session.topic_attempt_count[tech] = session.topic_attempt_count.get(tech, 0) + 1
                            if session.topic_attempt_count[tech] >= 2 and tech not in session.silent_topics:
                                session.silent_topics.append(tech)
                            break
                
                session.current_difficulty = "easy"
                q, keywords = await self._generate_technical_question(session, "", True)
                session.add_exchange(q, expected_keywords=keywords, question_type="technical")
                ack = await self._generate_dynamic_ack("cant answer technical", "cant_answer")
                return f"{ack} {q}"
            
            # Weak response - be understanding and ask different question
            if quality == "weak":
                session.current_difficulty = "easy"
                q, keywords = await self._generate_technical_question(session, "", True)
                session.add_exchange(q, expected_keywords=keywords, question_type="technical")
                ack = await self._generate_dynamic_ack("weak technical", "technical_weak")
                return f"{ack} {q}"
            
            # Strong answer - follow up or acknowledge
            if quality == "strong" and random.random() < 0.3:
                q = await self._generate_smart_followup(session, user_response, WI_InterviewStage.TECHNICAL)
                session.add_exchange(q, question_type="technical", is_followup=True)
                ack = await self._generate_dynamic_ack("good technical", "technical_good")
                return f"{ack} {q}"
            
            # Normal flow
            q, keywords = await self._generate_technical_question(session, user_response, True)
            session.add_exchange(q, expected_keywords=keywords, question_type="technical")
            ack = await self._generate_dynamic_ack("technical", "technical_good" if quality == "strong" else "transition")
            return f"{ack} {q}"
        
        # === HR ROUND ===
        if session.current_stage == WI_InterviewStage.HR:
            # Evaluate HR answer
            if session.exchanges and session.exchanges[-1].question_type == "hr":
                last_ex = session.exchanges[-1]
                accuracy = await self._evaluate_technical_accuracy(session, last_ex.ai_message, user_response, last_ex.expected_keywords)
                session.update_last_response(user_response, 0.8, quality, accuracy)
            
            if quality == "skip":
                q, keywords = await self._generate_hr_question(session, db_manager)
                session.add_exchange(q, expected_keywords=keywords, question_type="hr")
                ack = await self._generate_dynamic_ack("skip", "transition")
                return f"{ack} {q}"
            
            if quality == "silence":
                return await self.generate_silence_response(session)
            
            if quality == "cant_answer":
                q, keywords = await self._generate_hr_question(session, db_manager)
                session.add_exchange(q, expected_keywords=keywords, question_type="hr")
                ack = await self._generate_dynamic_ack("cant answer hr", "cant_answer")
                return f"{ack} {q}"
            
            # Weak response - be understanding and ask different question
            if quality == "weak":
                q, keywords = await self._generate_hr_question(session, db_manager)
                session.add_exchange(q, expected_keywords=keywords, question_type="hr")
                ack = await self._generate_dynamic_ack("weak hr", "weak")
                return f"{ack} {q}"
            
            # Strong answer - might follow up
            if quality == "strong" and random.random() < 0.25:
                q = await self._generate_smart_followup(session, user_response, WI_InterviewStage.HR)
                session.add_exchange(q, question_type="hr", is_followup=True)
                ack = await self._generate_dynamic_ack("good hr", "hr")
                return f"{ack} {q}"
            
            # Normal flow
            q, keywords = await self._generate_hr_question(session, db_manager)
            session.add_exchange(q, expected_keywords=keywords, question_type="hr")
            ack = await self._generate_dynamic_ack("hr response", "hr")
            return f"{ack} {q}"
        
        return "That's interesting. Tell me more?"

    # =========================================================================
    # EVALUATION - With Q&A Feedback Format
    # =========================================================================

    async def generate_fast_evaluation(self, session) -> Tuple[str, Dict[str, float]]:
        """Generate comprehensive evaluation with Q&A feedback format per round"""
        await self.client_manager.initialize()
        
        # Collect exchanges by round
        comm_exchanges = []
        tech_exchanges = []
        hr_exchanges = []
        tech_accuracies = []
        hr_accuracies = []
        
        for ex in session.exchanges:
            # Include all exchanges (even silent ones)
            exchange_data = {
                "question": ex.ai_message,
                "answer": ex.user_response if ex.user_response else "[SILENT - No response]",
                "is_silent": not ex.user_response or ex.answer_quality == "silence",
                "answer_quality": ex.answer_quality,
                "accuracy": ex.technical_accuracy
            }
            
            if ex.stage == WI_InterviewStage.COMMUNICATION:
                comm_exchanges.append(exchange_data)
            elif ex.stage == WI_InterviewStage.TECHNICAL:
                tech_exchanges.append(exchange_data)
                if ex.technical_accuracy is not None:
                    tech_accuracies.append(ex.technical_accuracy)
            elif ex.stage == WI_InterviewStage.HR:
                hr_exchanges.append(exchange_data)
                if ex.technical_accuracy is not None:
                    hr_accuracies.append(ex.technical_accuracy)
        
        # Calculate accuracy metrics
        tech_accuracy_avg = sum(tech_accuracies) / len(tech_accuracies) if tech_accuracies else 0.5
        hr_accuracy_avg = sum(hr_accuracies) / len(hr_accuracies) if hr_accuracies else 0.5
        
        total_technical_qs = len(tech_exchanges)
        total_hr_qs = len(hr_exchanges)
        total_comm_qs = len(comm_exchanges)
        
        # Generate feedback for each Q&A using LLM
        async def get_feedback_for_qa(question: str, answer: str, round_type: str, is_silent: bool) -> str:
            if is_silent:
                return "Candidate remained silent. Try to respond even with partial thoughts."
            
            prompt = f"""Give brief feedback (1-2 sentences) for this {round_type} interview answer.

Question: {question}
Answer: {answer}

Be constructive. If good, praise briefly. If weak, suggest improvement."""

            try:
                resp = await self.client_manager.openai_client.chat.completions.create(
                    model=config.OPENAI_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3, max_tokens=100
                )
                return resp.choices[0].message.content.strip()
            except:
                return "Response recorded."
        
        # Build detailed evaluation with Q&A format
        evaluation_parts = []
        
        # ===== COMMUNICATION ROUND =====
        if comm_exchanges:
            evaluation_parts.append("=" * 60)
            evaluation_parts.append("COMMUNICATION ROUND FEEDBACK")
            evaluation_parts.append("=" * 60)
            
            for i, ex in enumerate(comm_exchanges, 1):
                feedback = await get_feedback_for_qa(ex["question"], ex["answer"], "communication", ex["is_silent"])
                
                evaluation_parts.append(f"\nQ{i}. AI Question: {ex['question']}")
                evaluation_parts.append(f"    User Answer: {ex['answer']}")
                evaluation_parts.append(f"    Feedback: {feedback}")
                evaluation_parts.append("-" * 40)
        
        # ===== TECHNICAL ROUND =====
        if tech_exchanges:
            evaluation_parts.append("\n" + "=" * 60)
            evaluation_parts.append("TECHNICAL ROUND FEEDBACK")
            evaluation_parts.append("=" * 60)
            
            for i, ex in enumerate(tech_exchanges, 1):
                feedback = await get_feedback_for_qa(ex["question"], ex["answer"], "technical", ex["is_silent"])
                accuracy_str = f" (Accuracy: {ex['accuracy']:.0%})" if ex["accuracy"] is not None else ""
                
                evaluation_parts.append(f"\nQ{i}. AI Question: {ex['question']}")
                evaluation_parts.append(f"    User Answer: {ex['answer']}")
                evaluation_parts.append(f"    Feedback: {feedback}{accuracy_str}")
                evaluation_parts.append("-" * 40)
        
        # ===== HR ROUND =====
        if hr_exchanges:
            evaluation_parts.append("\n" + "=" * 60)
            evaluation_parts.append("HR/BEHAVIORAL ROUND FEEDBACK")
            evaluation_parts.append("=" * 60)
            
            for i, ex in enumerate(hr_exchanges, 1):
                feedback = await get_feedback_for_qa(ex["question"], ex["answer"], "HR/behavioral", ex["is_silent"])
                
                evaluation_parts.append(f"\nQ{i}. AI Question: {ex['question']}")
                evaluation_parts.append(f"    User Answer: {ex['answer']}")
                evaluation_parts.append(f"    Feedback: {feedback}")
                evaluation_parts.append("-" * 40)
        
        # ===== OVERALL SUMMARY =====
        evaluation_parts.append("\n" + "=" * 60)
        evaluation_parts.append("OVERALL SUMMARY")
        evaluation_parts.append("=" * 60)
        
        # Count silent responses
        silent_count = sum(1 for ex in comm_exchanges + tech_exchanges + hr_exchanges if ex["is_silent"])
        
        summary_prompt = f"""Provide a brief overall interview summary (4-5 sentences) for {session.student_name}.

METRICS:
- Communication Questions: {total_comm_qs}
- Technical Questions: {total_technical_qs}
- Technical Accuracy: {tech_accuracy_avg:.0%}
- HR Questions: {total_hr_qs}
- Correct Answers: {session.correct_answers}
- Partial Answers: {session.partial_answers}
- Weak Answers: {session.wrong_answers}
- Silent/No Response: {silent_count}

Include:
1. Overall performance summary
2. Key strengths (2-3 points)
3. Areas to improve (2-3 points)
4. Final recommendation"""

        summary_resp = await self.client_manager.openai_client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.3, max_tokens=400
        )
        overall_summary = summary_resp.choices[0].message.content.strip()
        
        evaluation_parts.append(f"\n{overall_summary}")
        
        # Add metrics summary
        evaluation_parts.append("\n" + "-" * 40)
        evaluation_parts.append("SCORE BREAKDOWN:")
        evaluation_parts.append(f"  • Technical Accuracy: {tech_accuracy_avg:.0%}")
        evaluation_parts.append(f"  • Questions Answered Well: {session.correct_answers}/{total_technical_qs + total_hr_qs}")
        evaluation_parts.append(f"  • Partial Answers: {session.partial_answers}")
        evaluation_parts.append(f"  • Needs Improvement: {session.wrong_answers}")
        evaluation_parts.append(f"  • Silent Responses: {silent_count}")
        
        evaluation = "\n".join(evaluation_parts)
        
        # Generate numerical scores
        score_prompt = f"""Based on this interview, provide scores (0-10) for each criteria.

METRICS:
- Technical Accuracy: {tech_accuracy_avg:.0%}
- Correct Answers: {session.correct_answers}/{total_technical_qs}
- Communication Questions: {total_comm_qs}
- HR Questions: {total_hr_qs}
- Silent Responses: {silent_count}

SCORING CRITERIA:
1. Communication (20%): Clarity, engagement, listening skills
2. Technical (30%): Accuracy, depth, problem-solving - USE THE {tech_accuracy_avg:.0%} ACCURACY
3. Leadership (15%): Initiative, decision-making, examples
4. Behaviour (20%): Professionalism, attitude, self-awareness
5. Confidence (15%): Composure, conviction, handling pressure

IMPORTANT: 
- Technical score should reflect the {tech_accuracy_avg:.0%} accuracy rate.
- Deduct points for silent responses.
- 90%+ accuracy = 9-10 score
- 70-89% accuracy = 7-8 score
- 50-69% accuracy = 5-6 score
- Below 50% = 3-4 score

Reply in EXACT format:
communication: X
technical: X
leadership: X
behaviour: X
confidence: X"""

        sc_resp = await self.client_manager.openai_client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "user", "content": score_prompt}],
            temperature=0.1, max_tokens=200
        )
        score_text = sc_resp.choices[0].message.content.lower()
        
        # Parse scores
        scores = {}
        for key in ["communication", "technical", "leadership", "behaviour", "confidence"]:
            m = re.search(rf"{key}[:\s]*(\d+\.?\d*)", score_text)
            if m:
                scores[f"{key}_score"] = min(float(m.group(1)), 10.0)
            else:
                if key == "technical":
                    scores[f"{key}_score"] = round(tech_accuracy_avg * 10, 1)
                else:
                    scores[f"{key}_score"] = 5.0
        
        # Add accuracy metrics to scores
        scores["technical_accuracy"] = round(tech_accuracy_avg * 100, 1)
        scores["hr_accuracy"] = round(hr_accuracy_avg * 100, 1)
        scores["questions_correct"] = session.correct_answers
        scores["questions_partial"] = session.partial_answers
        scores["questions_wrong"] = session.wrong_answers
        scores["questions_silent"] = silent_count
        scores["total_questions"] = total_technical_qs + total_hr_qs + total_comm_qs
        
        # Calculate weighted overall
        w = getattr(config, 'EVALUATION_CRITERIA', {
            "communication_weight": 0.20,
            "technical_weight": 0.30,
            "leadership_weight": 0.15,
            "behaviour_weight": 0.20,
            "confidence_weight": 0.15
        })
        
        scores["weighted_overall"] = round(
            scores.get("communication_score", 5) * w.get("communication_weight", 0.2) +
            scores.get("technical_score", 5) * w.get("technical_weight", 0.3) +
            scores.get("leadership_score", 5) * w.get("leadership_weight", 0.15) +
            scores.get("behaviour_score", 5) * w.get("behaviour_weight", 0.2) +
            scores.get("confidence_score", 5) * w.get("confidence_weight", 0.15),
            1
        )
        
        logger.info(f"[WI] Evaluation complete - Overall: {scores['weighted_overall']}/10, Tech Accuracy: {scores['technical_accuracy']}%, Silent: {silent_count}")
        
        return evaluation, scores


# =============================================================================
# WEEKEND MOCK TEST
# =============================================================================

class AIService:
    def __init__(self):
        self.client = Groq(api_key=config.GROQ_API_KEY, timeout=60)

    def generate_questions_batch(self, user_type: str, context: str) -> List[Dict[str, Any]]:
        prompt = PromptTemplates.create_batch_questions_prompt(user_type, context, 10)
        resp = self.client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}], temperature=0.7, max_completion_tokens=3000)
        return [{"question_number": i, "question": q} for i, q in enumerate(resp.choices[0].message.content.split("\n") if resp.choices else [], 1)]

    def evaluate_test_batch(self, user_type: str, qa_pairs: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {"scores": [1] * len(qa_pairs), "total_correct": len(qa_pairs)}

_ai_service_singleton = None
def get_ai_service() -> AIService:
    global _ai_service_singleton
    if not _ai_service_singleton:
        _ai_service_singleton = AIService()
    return _ai_service_singleton