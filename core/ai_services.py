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
# 40 QUESTION TEMPLATES - Works for ANY subject (SAP, Python, Java, etc.)
# {tech} = technology/topic from user's MongoDB summary
# {project} = project context from summary
# =============================================================================

# TECHNICAL QUESTIONS (25 templates) - Practical experience with {tech}
TECHNICAL_QUESTION_TEMPLATES = [
    # ===== Basic Understanding (Q1-Q5) =====
    "Can you explain what {tech} is and how you've used it in your work?",
    "What are the key components or features of {tech} that you worked with?",
    "How does {tech} fit into the overall architecture of your projects?",
    "Walk me through the basic workflow when working with {tech}.",
    "What's the purpose of {tech} and why is it important in your domain?",
    
    # ===== Practical Experience (Q6-Q10) =====
    "Describe a specific project where you implemented {tech}.",
    "What was your day-to-day work with {tech} like?",
    "How did you configure or set up {tech} in your environment?",
    "What tools, commands, or transactions did you use when working with {tech}?",
    "Can you give me an example of how you used {tech} to solve a real business problem?",
    
    # ===== Problem Solving (Q11-Q15) =====
    "What was the most challenging issue you faced with {tech} and how did you resolve it?",
    "Describe a bug or error you encountered in {tech} and your debugging approach.",
    "How do you troubleshoot problems when {tech} isn't working correctly?",
    "Tell me about a time when {tech} failed unexpectedly. How did you handle it?",
    "What's the most complex problem you solved using {tech}?",
    
    # ===== Best Practices (Q16-Q20) =====
    "What best practices do you follow when working with {tech}?",
    "How do you ensure quality and avoid errors when implementing {tech}?",
    "What documentation or standards do you follow for {tech}?",
    "How do you test your work with {tech} before deploying to production?",
    "What common mistakes should be avoided when working with {tech}?",
    
    # ===== Advanced & Integration (Q21-Q25) =====
    "How does {tech} integrate with other systems or components you've worked with?",
    "What performance considerations do you keep in mind when using {tech}?",
    "How do you handle security aspects when working with {tech}?",
    "What improvements or optimizations have you made to {tech} processes?",
    "How do you train or guide others on using {tech}?",
]

# BEHAVIORAL QUESTIONS (15 templates) - Soft skills in context of {tech}
TECHNICAL_BEHAVIORAL_QUESTIONS = [
    # ===== Problem Solving & Challenges (Q26-Q30) =====
    "Tell me about a challenging problem you solved while working on {tech}.",
    "Describe a situation where you had to learn {tech} quickly under pressure.",
    "Tell me about a time when your {tech} implementation didn't go as planned. What did you do?",
    "Describe a difficult decision you had to make regarding {tech}.",
    "Tell me about a time you identified and fixed a critical issue in {tech}.",
    
    # ===== Teamwork & Communication (Q31-Q35) =====
    "Describe a time when you had to explain {tech} concepts to someone non-technical.",
    "Tell me about a project where you collaborated with others on {tech}.",
    "How did you handle a disagreement with a colleague about {tech} implementation?",
    "Describe a time when you received feedback on your {tech} work. How did you respond?",
    "Tell me about a time you helped a team member who was struggling with {tech}.",
    
    # ===== Initiative & Growth (Q36-Q40) =====
    "Tell me about a time you took initiative to improve a {tech} process.",
    "Describe how you stay updated with new developments in {tech}.",
    "Tell me about a time you went beyond your responsibilities for a {tech} project.",
    "Describe a {tech} skill you developed on your own. How did you learn it?",
    "Tell me about a time you proposed a new approach or solution for {tech}.",
]

# HR/SOFT SKILL QUESTIONS (15 templates) - General professional questions
HR_QUESTIONS_POOL = [
    # ===== Leadership & Initiative =====
    "Describe a time when you took the lead on a project.",
    "Tell me about a situation where you motivated your team during a difficult time.",
    "How do you prioritize tasks when you have multiple deadlines?",
    "Describe a time when you had to make a decision without all the information you needed.",
    "Tell me about a time you took ownership of a mistake and fixed it.",
    
    # ===== Adaptability & Growth =====
    "How do you handle sudden changes in project requirements?",
    "Describe a time when you had to adapt to a new technology or process quickly.",
    "Tell me about a failure you experienced and what you learned from it.",
    "How do you handle criticism about your work?",
    "Where do you see yourself professionally in 5 years?",
    
    # ===== Work Style & Values =====
    "How do you maintain work-life balance during demanding projects?",
    "Describe your ideal work environment.",
    "What motivates you to do your best work?",
    "How do you handle stress when facing tight deadlines?",
    "Tell me about a time you went above and beyond for a project or client.",
]

# GENERIC FALLBACK QUESTIONS - When no specific tech context
GENERIC_TECHNICAL_QUESTIONS = [
    "Can you describe your typical day at work?",
    "What technical skills are you most proud of?",
    "Tell me about a project you're particularly proud of.",
    "How do you approach learning new technologies?",
    "What's the most interesting technical problem you've solved recently?",
    "How do you stay current with industry trends?",
    "Describe your experience with system troubleshooting.",
    "What development or administration tools are you most comfortable with?",
    "How do you document your work?",
    "What's your approach to testing and quality assurance?",
]

GENERIC_BEHAVIORAL_QUESTIONS = [
    "Tell me about a time you overcame a significant challenge at work.",
    "Describe a situation where you had to work with a difficult team member.",
    "Tell me about a time you had to meet a very tight deadline.",
    "Describe a project that didn't go as planned and how you handled it.",
    "Tell me about a time you received constructive criticism.",
    "How do you approach debugging a complex issue?",
    "Tell me about a project where you had to collaborate with others.",
    "Describe a time you had to explain technical concepts to non-technical people.",
    "How do you handle disagreements about technical decisions?",
    "Tell me about a time you improved an existing process.",
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
    
    # Track topics where user was silent - skip these entirely
    silent_topics: List[str] = field(default_factory=list)
    topic_attempt_count: Dict[str, int] = field(default_factory=dict)
    used_behavioral_questions: List[str] = field(default_factory=list)
    used_hr_questions: List[str] = field(default_factory=list)
    technical_question_count: int = 0
    behavioral_question_count: int = 0
    
    # SEQUENTIAL TRACKING - ensures no repeats and ordered coverage
    current_tech_index: int = 0  # Index for sequential technology selection
    current_hr_index: int = 0    # Index for sequential HR question selection
    current_topic_index: int = 0  # Index for sequential topic selection from summaries
    tech_question_types_used: Dict[str, List[str]] = field(default_factory=dict)  # Track question types per tech
    
    # Extracted from summaries - DETAILED TOPICS
    extracted_technologies: List[str] = field(default_factory=list)
    extracted_topics_for_questions: List[str] = field(default_factory=list)  # Specific topics from summary sections
    extracted_projects: List[str] = field(default_factory=list)
    extracted_challenges: List[str] = field(default_factory=list)
    extracted_team_info: List[str] = field(default_factory=list)
    
    # For evaluation accuracy
    technical_answers: List[Dict[str, Any]] = field(default_factory=list)
    correct_answers: int = 0
    partial_answers: int = 0
    wrong_answers: int = 0
    
    # Flag to prevent double finalization
    is_finalized: bool = False
    
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
        """
        Extract DETAILED topics from summaries for personalized questions.
        This parses the actual content to find specific things the user worked on.
        """
        content_lower = content.lower()
        
        # =====================================================================
        # STEP 1: Detect user type (SAP vs Developer)
        # =====================================================================
        sap_keywords = ["sap", "abap", "fiori", "hana", "s/4hana", "s4hana", "mm", "sd", "fico", "pp", "wm", "ewm", "ariba", "successfactors", "bw", "btp", "t-code", "tcode", "transaction", "idoc", "bapi", "rfc", "smartforms", "sapscript", "odata", "client administration", "scc4", "sccl", "scc3", "basis"]
        developer_keywords = ["python", "javascript", "react", "node", "fastapi", "django", "flask", "mongodb", "mysql", "postgresql", "docker", "kubernetes", "aws", "azure", "java", "spring", "typescript", "angular", "vue", "express", "api", "rest", "graphql"]
        
        sap_matches = [k for k in sap_keywords if k in content_lower]
        dev_matches = [k for k in developer_keywords if k in content_lower]
        
        # =====================================================================
        # STEP 2: Extract SPECIFIC topics from the summary content
        # These become the basis for questions
        # =====================================================================
        self.session.extracted_topics_for_questions = []
        
        # Extract section headings and key concepts
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            # Look for numbered sections, headings, or key phrases
            if line and (
                line[0].isdigit() or 
                line.startswith('#') or 
                line.endswith(':') or
                any(word in line.lower() for word in ['understanding', 'creating', 'configuring', 'implementing', 'troubleshooting', 'best practices', 'types of', 'step-by-step'])
            ):
                # Clean up the topic
                topic = line.strip('#').strip('0123456789.').strip(':').strip()
                if len(topic) > 5 and len(topic) < 100:
                    self.session.extracted_topics_for_questions.append(topic)
        
        # Also extract key concepts mentioned after "about", "for", "using"
        concept_patterns = [
            r"(?:about|understand|learn)\s+(.+?)(?:\.|,|and|$)",
            r"(?:creating|configuring|implementing)\s+(.+?)(?:\.|,|and|$)",
            r"(?:using|with)\s+([A-Z][a-zA-Z0-9\s]+)(?:\.|,|and|$)",
            r"(?:T-code|transaction)\s+([A-Z0-9]+)",
        ]
        
        for pattern in concept_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match) > 3 and len(match) < 50:
                    self.session.extracted_topics_for_questions.append(match.strip())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_topics = []
        for topic in self.session.extracted_topics_for_questions:
            topic_lower = topic.lower()
            if topic_lower not in seen and len(topic) > 5:
                seen.add(topic_lower)
                unique_topics.append(topic)
        self.session.extracted_topics_for_questions = unique_topics[:20]
        
        # =====================================================================
        # STEP 3: Set technologies based on track
        # =====================================================================
        if len(sap_matches) > len(dev_matches):
            self.session.extracted_technologies = list(set(sap_matches))[:15]
            logger.info(f"[WI] Detected SAP track - Technologies: {self.session.extracted_technologies}")
        elif len(dev_matches) > 0:
            self.session.extracted_technologies = list(set(dev_matches))[:15]
            logger.info(f"[WI] Detected Developer track - Technologies: {self.session.extracted_technologies}")
        else:
            self.session.extracted_technologies = []
            logger.info(f"[WI] No specific tech detected")
        
        # =====================================================================
        # STEP 4: Extract projects/implementations
        # =====================================================================
        project_patterns = [
            r"worked on (.+?)(?:\.|,|and)", 
            r"built (.+?)(?:\.|,|and)", 
            r"developed (.+?)(?:\.|,|and)", 
            r"implemented (.+?)(?:\.|,|and)", 
            r"created (.+?)(?:\.|,|and)", 
            r"configured (.+?)(?:\.|,|and)",
            r"managed (.+?)(?:\.|,|and)",
        ]
        projects = []
        for pattern in project_patterns:
            projects.extend(re.findall(pattern, content_lower))
        self.session.extracted_projects = list(set(projects))[:10]
        
        # =====================================================================
        # STEP 5: Extract challenges mentioned
        # =====================================================================
        challenge_patterns = [
            r"challenge.*?was (.+?)(?:\.|,)", 
            r"difficult.*?(.+?)(?:\.|,)", 
            r"problem.*?(.+?)(?:\.|,)", 
            r"issue.*?was (.+?)(?:\.|,)",
            r"troubleshoot.*?(.+?)(?:\.|,)",
        ]
        challenges = []
        for pattern in challenge_patterns:
            challenges.extend(re.findall(pattern, content_lower))
        self.session.extracted_challenges = list(set(challenges))[:5]
        
        # Team info
        if any(word in content_lower for word in ["team", "collaborate", "together", "group", "lead"]):
            self.session.extracted_team_info = ["worked in team"]
        
        logger.info(f"[WI] Extracted Topics for Questions: {self.session.extracted_topics_for_questions[:5]}")
        logger.info(f"[WI] Extracted Technologies: {self.session.extracted_technologies[:5]}")
        logger.info(f"[WI] Extracted Projects: {self.session.extracted_projects[:3]}")

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
        
        # Known Whisper hallucinations - these appear when audio is unclear
        self.HALLUCINATION_PHRASES = [
            "thank you for watching",
            "thanks for watching", 
            "please subscribe",
            "like and subscribe",
            "see you in the next",
            "bye bye",
            "goodbye",
            "thank you for listening",
            "the end",
            "music",
            "applause",
            "laughter",
            "silence",
            "inaudible",
            "unintelligible",
            "foreign",
            "speaking foreign language",
            # YouTube/podcast hallucinations
            "don't forget to subscribe",
            "hit the bell",
            "leave a comment",
            "check out my",
            "link in description",
            "sponsored by",
        ]

    async def transcribe_audio_fast(self, audio_data: bytes) -> Tuple[str, float]:
        """
        Transcribe audio with STRONG hallucination prevention.
        
        STRATEGY:
        1. Check audio size (too small = no real speech)
        2. Use context prompt to guide Whisper
        3. Clean known hallucination phrases
        4. Validate result is meaningful
        5. Return empty string if confidence too low (triggers "please repeat")
        """
        await self.client_manager.initialize()
        
        # ===== CHECK 1: Minimum audio size =====
        if len(audio_data) < 2000:  # ~0.1 seconds of audio
            logger.warning(f"[WI] Audio too small: {len(audio_data)} bytes - likely no speech")
            return "", 0.0
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
            tf.write(audio_data)
            temp_path = tf.name
        
        try:
            with open(temp_path, "rb") as f:
                audio_bytes = f.read()
            
            # ===== TRANSCRIBE with context prompt =====
            # The prompt helps Whisper understand expected content
            tr = await self.client_manager.groq_client.audio.transcriptions.create(
                file=(temp_path, audio_bytes), 
                model="whisper-large-v3-turbo", 
                language="en",
                prompt="Interview response. The speaker is answering questions about their work experience, technical skills, and projects."
            )
            
            raw_text = tr.text.strip() if hasattr(tr, 'text') else ""
            logger.info(f"[WI] Raw transcript: {raw_text[:150]}...")
            
            # ===== CHECK 2: Empty result =====
            if not raw_text:
                return "", 0.0
            
            # ===== CHECK 3: Remove hallucinations =====
            cleaned_text = self._remove_hallucinations(raw_text)
            
            # ===== CHECK 4: Validate result =====
            confidence = self._calculate_confidence(cleaned_text)
            
            if confidence < 0.3:
                logger.warning(f"[WI] Low confidence ({confidence:.2f}), treating as no response: {raw_text[:80]}")
                return "", confidence
            
            # ===== CHECK 5: Final cleanup =====
            final_text = self._final_cleanup(cleaned_text)
            
            if len(final_text.split()) < 2:
                logger.warning(f"[WI] Too short after cleanup: '{final_text}'")
                return "", 0.2
            
            logger.info(f"[WI] Final transcript (conf={confidence:.2f}): {final_text[:100]}")
            return final_text, confidence
            
        except Exception as e:
            logger.error(f"[WI] Transcription error: {e}")
            return "", 0.0
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def _remove_hallucinations(self, text: str) -> str:
        """Remove known Whisper hallucination phrases"""
        if not text:
            return ""
        
        result = text.lower()
        
        # Remove known hallucination phrases
        for phrase in self.HALLUCINATION_PHRASES:
            result = result.replace(phrase, "")
        
        # Remove non-English characters (Cyrillic, Chinese, Japanese, Korean, Arabic)
        # Keep only ASCII letters, numbers, spaces, and basic punctuation
        cleaned = ""
        for char in result:
            if char.isascii() or char in ".,?!'\"- ":
                cleaned += char
        
        # Remove excessive punctuation
        cleaned = re.sub(r'[.]{2,}', '.', cleaned)  # Multiple dots
        cleaned = re.sub(r'[,]{2,}', ',', cleaned)  # Multiple commas
        cleaned = re.sub(r'\s+', ' ', cleaned)       # Multiple spaces
        
        # Remove repeated words (like "hello hello hello hello")
        words = cleaned.split()
        if len(words) > 3:
            deduped = []
            repeat_count = 0
            last_word = ""
            for word in words:
                if word.lower() == last_word.lower():
                    repeat_count += 1
                    if repeat_count <= 1:  # Allow max 1 repetition
                        deduped.append(word)
                else:
                    repeat_count = 0
                    deduped.append(word)
                last_word = word
            cleaned = " ".join(deduped)
        
        return cleaned.strip()

    def _calculate_confidence(self, text: str) -> float:
        """Calculate confidence that this is real speech, not hallucination"""
        if not text:
            return 0.0
        
        words = text.split()
        word_count = len(words)
        
        # Too short = low confidence
        if word_count < 2:
            return 0.1
        
        # Check for meaningful content
        # Common English words that indicate real speech
        real_speech_indicators = {
            'i', 'we', 'my', 'our', 'the', 'this', 'that', 'is', 'are', 'was', 'were',
            'have', 'has', 'had', 'do', 'did', 'work', 'worked', 'use', 'used',
            'project', 'system', 'data', 'client', 'team', 'experience', 'years',
            'developed', 'created', 'managed', 'handled', 'implemented', 'configured',
            'learned', 'know', 'think', 'believe', 'like', 'want', 'need',
            'yes', 'no', 'because', 'so', 'and', 'but', 'or', 'for', 'with'
        }
        
        text_lower = text.lower()
        indicator_count = sum(1 for word in real_speech_indicators if word in text_lower)
        
        # Calculate scores
        indicator_score = min(indicator_count / 5, 1.0)  # Max 1.0 if 5+ indicators
        length_score = min(word_count / 10, 1.0)         # Max 1.0 if 10+ words
        
        # Check for gibberish patterns
        gibberish_penalty = 0.0
        
        # Repeated words penalty
        unique_ratio = len(set(words)) / len(words) if words else 0
        if unique_ratio < 0.5:
            gibberish_penalty += 0.3
        
        # Random character sequences penalty
        if re.search(r'[a-z]{10,}', text_lower):  # 10+ consecutive letters without space
            gibberish_penalty += 0.2
        
        # Calculate final confidence
        confidence = (indicator_score * 0.5 + length_score * 0.5) - gibberish_penalty
        
        return max(0.0, min(1.0, confidence))

    def _final_cleanup(self, text: str) -> str:
        """Final cleanup of transcription"""
        if not text:
            return ""
        
        # Capitalize first letter
        text = text.strip()
        if text:
            text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
        
        # Ensure ends with punctuation
        if text and text[-1] not in '.?!':
            text += '.'
        
        return text

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

    def _is_gibberish(self, text: str) -> bool:
        """Check if text is gibberish (bad transcription)"""
        if not text:
            return True
        
        # Check for non-ASCII ratio
        ascii_chars = sum(1 for c in text if c.isascii())
        if len(text) > 0 and (ascii_chars / len(text)) < 0.8:
            return True
        
        # Check for excessive repetition
        words = text.lower().split()
        if len(words) > 5:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3:  # Less than 30% unique words
                return True
        
        # Check for nonsense patterns
        nonsense_patterns = [
            r'(.)\1{4,}',  # Same character 5+ times (like "aaaaa")
            r'\b(\w+)\s+\1\s+\1\s+\1',  # Same word 4+ times
        ]
        for pattern in nonsense_patterns:
            if re.search(pattern, text.lower()):
                return True
        
        # Check for known hallucination phrases
        hallucinations = [
            "thank you for watching", "please subscribe", "like and subscribe",
            "see you next time", "bye bye bye", "youtube", "mcdonald"
        ]
        text_lower = text.lower()
        if any(h in text_lower for h in hallucinations):
            return True
        
        return False

    def _assess_answer_quality(self, user_response: str) -> str:
        if not user_response:
            return "silence"
        
        # Check for gibberish FIRST
        if self._is_gibberish(user_response):
            logger.warning(f"[WI] Detected gibberish: {user_response[:100]}...")
            return "gibberish"
        
        intent = self._detect_user_intent(user_response)
        if intent != "normal":
            return "skip" if intent == "skip" else ("repeat" if intent == "repeat" else "cant_answer")
        
        words = len(user_response.split())
        if words <= 3:
            return "weak"
        
        strong = ["because", "therefore", "for example", "specifically", "implemented", 
                  "experience", "i think", "used", "worked", "built", "designed", 
                  "configured", "created", "developed", "managed", "handled"]
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
        """
        Generate technical question using 40 TEMPLATES based on MongoDB summary.
        
        TEMPLATE POOLS:
        - 25 Technical templates (TECHNICAL_QUESTION_TEMPLATES)
        - 15 Behavioral templates (TECHNICAL_BEHAVIORAL_QUESTIONS)
        
        RULES:
        1. Use templates filled with {tech} from user's summary
        2. Rotate through ALL templates before repeating
        3. If user gives wrong answer → Skip that topic
        4. If user gives correct answer → Encourage + Follow-up
        5. 70% technical, 30% behavioral mix
        """
        await self.client_manager.initialize()
        
        # Track total technical questions
        if not hasattr(session, 'total_technical_questions_generated'):
            session.total_technical_questions_generated = 0
        session.total_technical_questions_generated += 1
        
        # Initialize template tracking
        if not hasattr(session, 'used_technical_templates'):
            session.used_technical_templates = []  # List of (template_index, tech) tuples
        if not hasattr(session, 'used_behavioral_templates'):
            session.used_behavioral_templates = []
        if not hasattr(session, 'current_tech_index'):
            session.current_tech_index = 0
        if not hasattr(session, 'current_template_index'):
            session.current_template_index = 0
        
        # Get questions asked
        all_asked_questions = list(session.questions_asked)
        
        # =====================================================================
        # STEP 1: Analyze user's last response
        # =====================================================================
        response_quality = "none"
        should_followup = False
        prefix = ""
        
        if user_response:
            response_lower = user_response.lower().strip()
            word_count = len(response_lower.split())
            
            # Bad answer indicators
            bad_indicators = [
                "thank you", "skip", "next", "i don't know", "no idea", 
                "can't answer", "pass", "move on", "bye", "i can't", 
                "don't understand", "not sure", "no clue", "don't remember",
                "hello", "hi", "okay", "ok", "yes", "no"
            ]
            
            # Check for repetitive/gibberish
            words = response_lower.split()
            unique_words = set(words)
            is_repetitive = len(words) > 3 and len(unique_words) < len(words) * 0.4
            
            # Tech keywords for good answer detection
            tech_keywords = ['sap', 'client', 'transaction', 't-code', 'config', 'system', 
                           'data', 'user', 'table', 'module', 'basis', 'abap', 'fiori',
                           'report', 'program', 'function', 'process', 'implement', 
                           'configure', 'setup', 'install', 'error', 'issue', 'problem',
                           'solution', 'project', 'team', 'work', 'experience', 'used',
                           'created', 'developed', 'managed', 'handled', 'deployed']
            has_tech_content = any(kw in response_lower for kw in tech_keywords)
            
            # Irrelevant content
            irrelevant = ['mcdonald', 'youtube', 'google', 'phone', 'rupee', 'otp', 
                         'video', 'movie', 'song', 'food', 'hospital', 'cookie']
            has_irrelevant = any(irr in response_lower for irr in irrelevant)
            
            is_bad_answer = (
                word_count < 8 or
                is_repetitive or
                has_irrelevant or
                any(indicator == response_lower.strip() for indicator in bad_indicators) or
                (word_count < 15 and not has_tech_content)
            )
            
            if is_bad_answer:
                response_quality = "bad"
                prefix = "I think you might not be familiar with that topic. No worries, let me ask you something different. "
                # Mark topic to skip
                if session.exchanges:
                    last_q = session.exchanges[-1].ai_message.lower()
                    for tech in (session.extracted_technologies or []):
                        if tech.lower() in last_q and tech not in session.silent_topics:
                            session.silent_topics.append(tech)
                            logger.info(f"[WI] Skipping topic '{tech}' - user doesn't know it")
                            break
            elif word_count >= 20 and has_tech_content:
                response_quality = "good"
                should_followup = True
                prefix = self._get_encouragement() + " "
        
        # =====================================================================
        # STEP 2: If good answer, ask follow-up based on their response
        # =====================================================================
        if should_followup and user_response:
            follow_up = await self._generate_followup_from_answer(session, user_response, all_asked_questions)
            if follow_up:
                return f"{prefix}{follow_up}", ["followup"]
        
        # =====================================================================
        # STEP 3: Get available technologies from summary
        # =====================================================================
        technologies = [t for t in (session.extracted_technologies or []) if t not in session.silent_topics]
        
        if not technologies:
            technologies = ["your work experience", "your daily tasks", "your technical skills"]
        
        # =====================================================================
        # STEP 4: Decide - Technical (70%) or Behavioral (30%)
        # =====================================================================
        total_qs = session.technical_question_count + session.behavioral_question_count
        
        # Every 4th question is behavioral (Q4, Q8, Q12...)
        should_be_behavioral = (
            include_behavioral and 
            total_qs > 0 and 
            total_qs % 4 == 3 and
            len(session.used_behavioral_templates) < len(TECHNICAL_BEHAVIORAL_QUESTIONS)
        )
        
        if should_be_behavioral:
            session.behavioral_question_count += 1
            return await self._generate_behavioral_from_template(session, technologies, all_asked_questions, prefix)
        
        # =====================================================================
        # STEP 5: Generate TECHNICAL question from template
        # =====================================================================
        session.technical_question_count += 1
        
        # Rotate through technologies
        tech_idx = session.current_tech_index % len(technologies)
        chosen_tech = technologies[tech_idx]
        session.current_tech_index += 1
        
        # Find unused template for this tech
        question = None
        for i, template in enumerate(TECHNICAL_QUESTION_TEMPLATES):
            template_key = (i, chosen_tech.lower())
            if template_key not in session.used_technical_templates:
                question = template.format(tech=chosen_tech)
                
                # Check not duplicate
                if not any(self._is_similar_question(question.lower(), aq.lower()) for aq in all_asked_questions):
                    session.used_technical_templates.append(template_key)
                    break
                else:
                    question = None
        
        # If all templates used for this tech, try next tech or generate dynamic
        if not question:
            # Reset template index and try another tech
            session.current_template_index = 0
            
            # Try other technologies
            for tech in technologies:
                if tech != chosen_tech:
                    for i, template in enumerate(TECHNICAL_QUESTION_TEMPLATES):
                        template_key = (i, tech.lower())
                        if template_key not in session.used_technical_templates:
                            question = template.format(tech=tech)
                            chosen_tech = tech
                            if not any(self._is_similar_question(question.lower(), aq.lower()) for aq in all_asked_questions):
                                session.used_technical_templates.append(template_key)
                                break
                            else:
                                question = None
                    if question:
                        break
        
        # If still no question, generate dynamic one from summary
        if not question:
            question = await self._generate_dynamic_question_from_summary(session, chosen_tech, all_asked_questions)
        
        # Add prefix if needed
        full_question = f"{prefix}{question}" if prefix else question
        
        if chosen_tech not in session.technical_topics_covered:
            session.technical_topics_covered.append(chosen_tech)
        
        return full_question, [chosen_tech]

    async def _generate_behavioral_from_template(self, session, technologies: List[str], all_asked: List[str], prefix: str = "") -> Tuple[str, List[str]]:
        """Generate behavioral question from template pool"""
        
        # Pick a technology
        tech_idx = session.current_tech_index % len(technologies)
        chosen_tech = technologies[tech_idx]
        
        # Find unused behavioral template
        question = None
        for i, template in enumerate(TECHNICAL_BEHAVIORAL_QUESTIONS):
            if i not in session.used_behavioral_templates:
                question = template.format(tech=chosen_tech, project=chosen_tech)
                
                if not any(self._is_similar_question(question.lower(), aq.lower()) for aq in all_asked):
                    session.used_behavioral_templates.append(i)
                    break
                else:
                    question = None
        
        # Fallback
        if not question:
            question = f"Tell me about a challenging experience you had while working with {chosen_tech}."
        
        full_question = f"{prefix}{question}" if prefix else question
        return full_question, [chosen_tech]

    async def _generate_dynamic_question_from_summary(self, session, tech: str, all_asked: List[str]) -> str:
        """Generate dynamic question when templates are exhausted"""
        await self.client_manager.initialize()
        
        summary = session.content_context or "General technical work"
        
        prompt = f"""Generate ONE unique technical interview question.

CANDIDATE'S WORK SUMMARY:
{summary[:1500]}

TOPIC: {tech}

ALREADY ASKED (DO NOT REPEAT):
{chr(10).join(all_asked[-10:])}

Generate a specific question about their practical experience.
MAX 20 words. Just the question:"""

        try:
            resp = await self.client_manager.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=50
            )
            question = resp.choices[0].message.content.strip().strip('"').strip("'")
            if not question.endswith('?'):
                question += '?'
            return question
        except Exception as e:
            logger.error(f"Error generating dynamic question: {e}")
            return f"Tell me more about your experience with {tech}?"
        
        # =====================================================================
        # STEP 1: Analyze user's last response - STRICT VALIDATION
        # =====================================================================
        response_quality = "none"
        should_followup = False
        encouragement = ""
        
        if user_response:
            response_lower = user_response.lower().strip()
            word_count = len(response_lower.split())
            
            # Detect bad/unrelated answer
            bad_indicators = [
                "thank you", "skip", "next", "i don't know", "no idea", 
                "can't answer", "pass", "move on", "bye", "i can't", 
                "don't understand", "not sure", "no clue", "don't remember",
                "hello", "hi", "okay", "ok", "yes", "no", "good", "fine"
            ]
            
            # Check for repetitive words (like "java java java" or "hello hello")
            words = response_lower.split()
            unique_words = set(words)
            is_repetitive = len(words) > 3 and len(unique_words) < len(words) * 0.4
            
            # Check for gibberish - too many non-ASCII or random characters
            ascii_chars = sum(1 for c in response_lower if c.isascii() and c.isalpha())
            total_alpha = sum(1 for c in response_lower if c.isalpha())
            is_gibberish = total_alpha > 0 and (ascii_chars / max(total_alpha, 1)) < 0.7
            
            # Check for meaningful content - must have actual SAP/tech related words
            tech_keywords = ['sap', 'client', 'transaction', 't-code', 'config', 'system', 
                           'data', 'user', 'table', 'module', 'basis', 'abap', 'fiori',
                           'report', 'program', 'function', 'process', 'implement', 
                           'configure', 'setup', 'install', 'error', 'issue', 'problem',
                           'solution', 'project', 'team', 'work', 'experience']
            has_tech_content = any(kw in response_lower for kw in tech_keywords)
            
            is_bad_answer = (
                word_count < 8 or                    # Too short
                is_repetitive or                     # Repetitive words
                is_gibberish or                      # Garbled text
                any(indicator == response_lower.strip() for indicator in bad_indicators) or  # Just "ok", "yes", etc.
                (word_count < 15 and not has_tech_content)  # Short without tech content
            )
            
            # Check for clearly irrelevant content
            irrelevant_indicators = [
                "mcdonald", "youtube", "google", "phone", "rupee", "otp", "payment",
                "video", "movie", "song", "food", "hospital", "japan", "cookie",
                "grok", "python", "django", "michael jackson", "brooklyn"
            ]
            has_irrelevant = any(irr in response_lower for irr in irrelevant_indicators)
            
            if is_bad_answer or has_irrelevant:
                response_quality = "bad"
                # Mark topic as one user doesn't know
                if session.exchanges:
                    last_q = session.exchanges[-1].ai_message.lower()
                    for tech in (session.extracted_technologies or []):
                        if tech.lower() in last_q and tech not in session.silent_topics:
                            session.silent_topics.append(tech)
                            logger.info(f"[WI] User doesn't know '{tech}' - will ask different topic")
                            break
            elif word_count >= 20 and has_tech_content and not is_repetitive:
                # GOOD answer - must be substantial AND have tech content
                response_quality = "good"
                should_followup = True
                encouragement = self._get_encouragement()
        
        # =====================================================================
        # STEP 2: If bad answer, acknowledge and change topic
        # =====================================================================
        if response_quality == "bad":
            prefix = "I think you might not be familiar with that topic. No worries, let me ask you something different. "
        elif response_quality == "good" and encouragement:
            prefix = f"{encouragement} "
        else:
            prefix = ""
        
        # =====================================================================
        # STEP 3: If good answer, ask follow-up based on their response
        # =====================================================================
        if should_followup and user_response:
            follow_up = await self._generate_followup_from_answer(session, user_response, all_asked_questions)
            if follow_up:
                question = f"{prefix}{follow_up}"
                return question, ["followup"]
        
        # =====================================================================
        # STEP 4: Generate question FROM SUMMARY content
        # =====================================================================
        summary_content = session.content_context or ""
        
        # Get topics user knows (not in silent_topics)
        available_topics = [t for t in (session.extracted_technologies or []) if t not in session.silent_topics]
        
        if not available_topics:
            # User doesn't know any extracted topics - ask general from summary
            available_topics = ["your work", "your experience", "your projects"]
        
        # Pick next topic (rotate through)
        if not hasattr(session, 'topic_index'):
            session.topic_index = 0
        
        topic_idx = session.topic_index % len(available_topics)
        chosen_topic = available_topics[topic_idx]
        session.topic_index += 1
        
        # Generate question using LLM based on ACTUAL summary
        prompt = f"""You are a technical interviewer. Generate ONE specific question based on this candidate's work summary.

CANDIDATE'S WORK SUMMARY:
{summary_content[:2000]}

TOPIC TO ASK ABOUT: {chosen_topic}

ALREADY ASKED QUESTIONS (DO NOT REPEAT):
{chr(10).join(all_asked_questions[-10:])}

RULES:
1. Ask about something SPECIFIC mentioned in the summary
2. Question must be related to "{chosen_topic}"
3. Ask about their PRACTICAL experience, not theoretical definitions
4. Make it conversational
5. DO NOT ask "What is X?" - ask "How did you use X?" or "Tell me about your experience with X"
6. MAX 20 words

Generate ONLY the question:"""

        try:
            resp = await self.client_manager.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=50
            )
            question = resp.choices[0].message.content.strip()
            question = question.strip('"').strip("'").strip()
            
            if not question.endswith('?'):
                question += '?'
            
            # Check for duplicate
            is_duplicate = any(
                self._is_similar_question(question.lower(), aq.lower()) 
                for aq in all_asked_questions
            )
            
            if is_duplicate:
                # Fallback to different phrasing
                question = f"Tell me about your hands-on experience with {chosen_topic}."
                
        except Exception as e:
            logger.error(f"Error generating question: {e}")
            question = f"Can you share your experience working with {chosen_topic}?"
        
        # Add prefix if needed
        full_question = f"{prefix}{question}" if prefix else question
        
        return full_question, [chosen_topic]

    def _get_encouragement(self) -> str:
        """Get random encouraging response for good answer"""
        import random
        encouragements = [
            "That's a great explanation!",
            "Excellent point!",
            "Well explained!",
            "Good answer!",
            "That's exactly right!",
            "Nice! You clearly have good experience with this.",
            "Great insight!",
            "That's impressive!",
        ]
        return random.choice(encouragements)

    async def _generate_followup_from_answer(self, session, user_response: str, all_asked: List[str]) -> Optional[str]:
        """Generate follow-up question based on what user said in their GOOD answer"""
        await self.client_manager.initialize()
        
        prompt = f"""The candidate gave this good answer: "{user_response[:300]}"

Generate ONE short follow-up question to dig deeper into what they mentioned.
Ask about:
- Specific details they mentioned
- Challenges they faced
- How they solved problems
- Results or outcomes

ALREADY ASKED (DO NOT REPEAT):
{chr(10).join(all_asked[-5:])}

MAX 15 words. Just the question:"""

        try:
            resp = await self.client_manager.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=40
            )
            question = resp.choices[0].message.content.strip()
            
            if not question.endswith('?'):
                question += '?'
            
            # Check not duplicate
            is_duplicate = any(
                self._is_similar_question(question.lower(), aq.lower()) 
                for aq in all_asked
            )
            
            if not is_duplicate:
                return question
        except:
            pass
        
        return None

    def _normalize_question(self, question: str) -> str:
        """Normalize question for comparison - remove common words, lowercase, sort"""
        if not question:
            return ""
        q = question.lower().strip().rstrip('?').strip()
        # Remove common words
        stop_words = {'what', 'how', 'why', 'when', 'where', 'who', 'is', 'are', 'the', 'a', 'an', 
                      'your', 'you', 'can', 'do', 'did', 'does', 'tell', 'me', 'about', 'describe', 
                      'explain', 'please', 'could', 'would', 'should', 'to', 'in', 'on', 'for', 'with'}
        words = [w for w in q.split() if w not in stop_words and len(w) > 2]
        return ' '.join(sorted(words))

    async def _generate_technical_behavioral_question(self, session) -> Tuple[str, List[str]]:
        """Generate follow-up question based on what user just said"""
        await self.client_manager.initialize()
        
        # Don't follow up on weak responses
        if len(user_response.split()) < 5:
            return None
        
        prompt = f"""The candidate said: "{user_response[:200]}"

Generate ONE short follow-up question to dig deeper.
Ask about: specifics, challenges, examples, or learnings.

MAX 12 words. Just the question."""

        try:
            resp = await self.client_manager.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=35
            )
            question = resp.choices[0].message.content.strip()
            
            if not question.endswith('?'):
                question += '?'
            
            # Check not duplicate
            q_hash = self._normalize_question(question)
            if hasattr(session, 'asked_question_hashes') and q_hash in session.asked_question_hashes:
                return None
            
            return question, ["followup"]
        except:
            pass
        
        return None

    async def _generate_technical_behavioral_question(self, session) -> Tuple[str, List[str]]:
        """
        Generate behavioral question for technical round.
        SEQUENTIAL selection from pool, NEVER repeat.
        """
        
        # Get ALL questions asked
        all_asked = list(session.questions_asked)
        
        # Initialize hash set if needed
        if not hasattr(session, 'asked_question_hashes'):
            session.asked_question_hashes = set()
            for q in all_asked:
                session.asked_question_hashes.add(self._normalize_question(q))
        
        # Get user's primary technology for context
        primary_tech = "your technical work"
        if session.extracted_technologies:
            primary_tech = session.extracted_technologies[0]
        
        project_context = "your projects"
        if session.extracted_projects:
            project_context = session.extracted_projects[0]
        
        # Initialize behavioral question tracker
        if not hasattr(session, 'behavioral_question_idx'):
            session.behavioral_question_idx = 0
        
        # Try TECHNICAL_BEHAVIORAL_QUESTIONS first (with {tech} placeholder)
        while session.behavioral_question_idx < len(TECHNICAL_BEHAVIORAL_QUESTIONS):
            template = TECHNICAL_BEHAVIORAL_QUESTIONS[session.behavioral_question_idx]
            session.behavioral_question_idx += 1
            
            # Format with user's tech
            try:
                question = template.format(tech=primary_tech, project=project_context)
            except:
                question = template.replace("{tech}", primary_tech).replace("{project}", project_context)
            
            # Check if duplicate
            q_hash = self._normalize_question(question)
            if q_hash not in session.asked_question_hashes:
                session.asked_question_hashes.add(q_hash)
                session.used_behavioral_questions.append(question)
                return question, ["behavioral"]
        
        # Try GENERIC_BEHAVIORAL_QUESTIONS next
        if not hasattr(session, 'generic_behavioral_idx'):
            session.generic_behavioral_idx = 0
        
        while session.generic_behavioral_idx < len(GENERIC_BEHAVIORAL_QUESTIONS):
            question = GENERIC_BEHAVIORAL_QUESTIONS[session.generic_behavioral_idx]
            session.generic_behavioral_idx += 1
            
            q_hash = self._normalize_question(question)
            if q_hash not in session.asked_question_hashes:
                session.asked_question_hashes.add(q_hash)
                session.used_behavioral_questions.append(question)
                return question, ["behavioral"]
        
        # All pool questions exhausted, generate dynamic one
        await self.client_manager.initialize()
        
        question_num = len(session.used_behavioral_questions) + 1
        
        prompt = f"""Generate ONE unique behavioral interview question.

Candidate works with: {primary_tech}

ALREADY ASKED - DO NOT REPEAT:
{chr(10).join(session.used_behavioral_questions[-10:])}

Ask about: challenges, learning, teamwork, problem-solving
MAX 15 words. Just the question."""

        try:
            resp = await self.client_manager.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=40
            )
            question = resp.choices[0].message.content.strip()
            if not question.endswith('?'):
                question += '?'
                
            # Check duplicate
            q_hash = self._normalize_question(question)
            if q_hash in session.asked_question_hashes:
                question = f"Share an experience where you overcame a challenge. (Q#{question_num})"
        except:
            question = f"Tell me about a learning experience in your career. (Q#{question_num})"
        
        session.asked_question_hashes.add(self._normalize_question(question))
        session.used_behavioral_questions.append(question)
        return question, ["behavioral"]

    async def _generate_hr_question(self, session, db_manager=None) -> Tuple[str, List[str]]:
        """
        Generate HR question - SEQUENTIAL from templates, NEVER repeat.
        Uses HR_QUESTIONS_POOL and GENERIC_HR_QUESTIONS.
        """
        
        # Initialize hash set if needed
        if not hasattr(session, 'asked_question_hashes'):
            session.asked_question_hashes = set()
            for q in session.questions_asked:
                session.asked_question_hashes.add(self._normalize_question(q))
        
        # Get user's context for template filling
        primary_tech = "your work"
        if session.extracted_technologies:
            primary_tech = session.extracted_technologies[0]
        
        project_context = "your projects"
        if session.extracted_projects:
            project_context = session.extracted_projects[0]
        
        # Initialize HR question tracker
        if not hasattr(session, 'hr_question_idx'):
            session.hr_question_idx = 0
        
        # Try HR_QUESTIONS_POOL first (15 templates)
        while session.hr_question_idx < len(HR_QUESTIONS_POOL):
            template = HR_QUESTIONS_POOL[session.hr_question_idx]
            session.hr_question_idx += 1
            
            try:
                question = template.format(tech=primary_tech, project=project_context)
            except:
                question = template.replace("{tech}", primary_tech).replace("{project}", project_context)
            
            q_hash = self._normalize_question(question)
            if q_hash not in session.asked_question_hashes:
                session.asked_question_hashes.add(q_hash)
                session.used_hr_questions.append(question)
                logger.info(f"[HR] Question from pool: {question[:60]}...")
                return question, ["hr"]
        
        # Try GENERIC_HR_QUESTIONS (10 questions)
        if not hasattr(session, 'generic_hr_idx'):
            session.generic_hr_idx = 0
        
        while session.generic_hr_idx < len(GENERIC_HR_QUESTIONS):
            question = GENERIC_HR_QUESTIONS[session.generic_hr_idx]
            session.generic_hr_idx += 1
            
            q_hash = self._normalize_question(question)
            if q_hash not in session.asked_question_hashes:
                session.asked_question_hashes.add(q_hash)
                session.used_hr_questions.append(question)
                logger.info(f"[HR] Question from generic: {question[:60]}...")
                return question, ["hr"]
        
        # All exhausted, generate dynamic question
        await self.client_manager.initialize()
        question_num = len(session.used_hr_questions) + 1
        
        prompt = f"""Generate ONE unique HR/behavioral question.

ALREADY ASKED - DO NOT REPEAT:
{chr(10).join(session.used_hr_questions[-10:])}

Ask about: career goals, teamwork, leadership, stress management, motivation
MAX 15 words. Just the question."""

        try:
            resp = await self.client_manager.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=40
            )
            question = resp.choices[0].message.content.strip()
            if not question.endswith('?'):
                question += '?'
            
            q_hash = self._normalize_question(question)
            if q_hash in session.asked_question_hashes:
                question = f"What else would you like to share about yourself?"
        except:
            question = f"What are your career aspirations?"
        
        session.asked_question_hashes.add(self._normalize_question(question))
        session.used_hr_questions.append(question)
        logger.info(f"[HR] Dynamic question: {question[:60]}...")
        return question, ["hr"]

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
                session.add_exchange(q, question_type="communication")  # FIXED: Add exchange
                ack = await self._generate_dynamic_ack("skip", "transition")
                return f"{ack} {q}"
            
            if quality == "silence":
                return await self.generate_silence_response(session)
            
            # Handle gibberish - ask to repeat
            if quality == "gibberish":
                return "I'm sorry, I didn't catch that clearly. Could you please repeat your answer?"
            
            if quality == "cant_answer":
                q = await self._generate_communication_question(session)
                session.add_exchange(q, question_type="communication")  # FIXED: Add exchange
                ack = await self._generate_dynamic_ack("cant answer", "cant_answer")
                return f"{ack} {q}"
            
            # Weak response - acknowledge and ask something different
            if quality == "weak":
                q = await self._generate_communication_question(session)
                session.add_exchange(q, question_type="communication")  # FIXED: Add exchange
                ack = await self._generate_dynamic_ack("weak response", "weak")
                return f"{ack} {q}"
            
            # Good response - follow up or new question
            if self._should_followup(session, quality):
                session.conversation_state.followups_on_topic += 1
                q = await self._generate_communication_followup(session, user_response)
                session.add_exchange(q, question_type="communication", is_followup=True)  # FIXED: Add exchange
                ack = await self._generate_dynamic_ack("good response", "good")
                return f"{ack} {q}"
            
            q = await self._generate_communication_question(session)
            session.add_exchange(q, question_type="communication")  # FIXED: Add exchange
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
            
            # Handle gibberish - ask to repeat
            if quality == "gibberish":
                return "I'm sorry, I didn't catch that clearly. Could you please repeat your answer?"
            
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
            
            # Handle gibberish - ask to repeat
            if quality == "gibberish":
                return "I'm sorry, I didn't catch that clearly. Could you please repeat your answer?"
            
            if quality == "silence":
                # After silence in HR, ask a new question instead of just prompting
                session.silence_prompt_count += 1
                if session.silence_prompt_count >= 2:
                    session.silence_prompt_count = 0
                    q, keywords = await self._generate_hr_question(session, db_manager)
                    session.add_exchange(q, expected_keywords=keywords, question_type="hr")
                    return f"Let's try a different question. {q}"
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
        
        # Get total technical questions generated
        total_tech_generated = getattr(session, 'total_technical_questions_generated', total_technical_qs)
        
        summary_prompt = f"""Provide a brief overall interview summary (4-5 sentences) for {session.student_name}.

METRICS:
- Communication Questions: {total_comm_qs}
- Technical Questions Generated: {total_tech_generated}
- Technical Questions Answered: {total_technical_qs}
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
        evaluation_parts.append("STATISTICS:")
        evaluation_parts.append(f"  • Total Technical Questions Generated: {total_tech_generated}")
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