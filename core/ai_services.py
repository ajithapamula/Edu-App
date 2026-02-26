# Edu-app/core/ai_services.py
# Summary-based behavioral questions + Smart follow-ups + Improved evaluation with accuracy

import os, time, logging, asyncio, re, random, tempfile, subprocess
from typing import List, Tuple, Optional, Dict, Any
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import io
import wave

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

ROUND_DURATIONS = {
    "introduction": 60,
    "communication": 300,
    "technical": 1500,
    "hr": 600,
}

# If user gives no real response for 5 consecutive questions, auto-skip to next round
MAX_CONSECUTIVE_SILENCE = 5

TECHNICAL_QUESTION_TEMPLATES = [
    "Can you explain what {tech} is and how you've used it in your work?",
    "What are the key components or features of {tech} that you worked with?",
    "How does {tech} fit into the overall architecture of your projects?",
    "Walk me through the basic workflow when working with {tech}.",
    "What's the purpose of {tech} and why is it important in your domain?",
    "Describe a specific project where you implemented {tech}.",
    "What was your day-to-day work with {tech} like?",
    "How did you configure or set up {tech} in your environment?",
    "What tools, commands, or transactions did you use when working with {tech}?",
    "Can you give me an example of how you used {tech} to solve a real business problem?",
    "What was the most challenging issue you faced with {tech} and how did you resolve it?",
    "Describe a bug or error you encountered in {tech} and your debugging approach.",
    "How do you troubleshoot problems when {tech} isn't working correctly?",
    "Tell me about a time when {tech} failed unexpectedly. How did you handle it?",
    "What's the most complex problem you solved using {tech}?",
    "What best practices do you follow when working with {tech}?",
    "How do you ensure quality and avoid errors when implementing {tech}?",
    "What documentation or standards do you follow for {tech}?",
    "How do you test your work with {tech} before deploying to production?",
    "What common mistakes should be avoided when working with {tech}?",
    "How does {tech} integrate with other systems or components you've worked with?",
    "What performance considerations do you keep in mind when using {tech}?",
    "How do you handle security aspects when working with {tech}?",
    "What improvements or optimizations have you made to {tech} processes?",
    "How do you train or guide others on using {tech}?",
]

TECHNICAL_BEHAVIORAL_QUESTIONS = [
    "Tell me about the most difficult bug you encountered while working with {tech}. How did you debug it?",
    "Describe a situation where {tech} was not performing as expected. What steps did you take to identify the root cause?",
    "Walk me through a time when you had to troubleshoot a critical {tech} issue under pressure. What was your approach?",
    "Tell me about a {tech} problem that took you a long time to solve. What made it so challenging?",
    "Describe a scenario where you had to fix someone else's {tech} code or configuration. How did you approach it?",
    "Tell me about a technical decision you made regarding {tech} that you later had to reconsider. What did you learn?",
    "Describe a time when you had to choose between two different approaches in {tech}. How did you decide?",
    "Walk me through a situation where you disagreed with a colleague about how to implement something in {tech}. How was it resolved?",
    "Tell me about a time when you had to balance performance vs. maintainability in your {tech} work. What trade-offs did you make?",
    "Describe a {tech} implementation where you had to work within significant constraints. How did you handle it?",
    "Tell me about a time when you had to learn a new feature or version of {tech} quickly. How did you approach it?",
    "Describe a situation where you made a mistake with {tech} in production. How did you handle it and what did you learn?",
    "Walk me through how you stay updated with changes and best practices in {tech}.",
    "Tell me about a {tech} concept that was initially difficult for you to understand. How did you master it?",
    "Describe a time when you had to adapt your {tech} approach based on feedback or changing requirements. What changed?",
]

HR_QUESTIONS_POOL = [
    "Describe a time when you took the lead on a project.",
    "Tell me about a situation where you motivated your team during a difficult time.",
    "How do you prioritize tasks when you have multiple deadlines?",
    "Describe a time when you had to make a decision without all the information you needed.",
    "Tell me about a time you took ownership of a mistake and fixed it.",
    "How do you handle sudden changes in project requirements?",
    "Describe a time when you had to adapt to a new technology or process quickly.",
    "Tell me about a failure you experienced and what you learned from it.",
    "How do you handle criticism about your work?",
    "Where do you see yourself professionally in 5 years?",
    "How do you maintain work-life balance during demanding projects?",
    "Describe your ideal work environment.",
    "What motivates you to do your best work?",
    "How do you handle stress when facing tight deadlines?",
    "Tell me about a time you went above and beyond for a project or client.",
]

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

COMMUNICATION_TRANSITIONS = [
    "That's interesting! ", "Nice! ", "Great to know! ", "Thanks for sharing! ",
    "That sounds wonderful! ", "How lovely! ", "That's cool! ", "Awesome! ",
    "That's really nice! ", "Wonderful! ", "Oh, that's great! ", "I like that! ",
    "Sounds fun! ", "That's fantastic! ", "How interesting! ", "Good to know! ",
]
FOLLOWUP_ACKS = ["Oh interesting!", "That's nice!", "I see!", "That sounds great!", "Nice!", "Lovely!", "Oh really?", "That's cool!", "Wow!", "Fascinating!"]
TECHNICAL_GOOD_ACKS = ["Good explanation!", "That's correct!", "Nice approach!", "Well explained!", "Good point!", "Exactly right!", "Great understanding!", "Well done!", "Perfect!", "Excellent!"]
TECHNICAL_NEUTRAL_ACKS = ["I see.", "Okay.", "Alright.", "Got it.", "Understood.", "Fair enough."]
DONT_KNOW_RESPONSES = ["That's okay! Let me ask you something different.", "No problem at all! Here's another question.", "It's fine! Let's try a different one.", "No worries! Let me change the topic.", "That's alright! Moving to something else."]
WEAK_RESPONSE_ACKS = ["I see. Let me ask you something else.", "Okay, let's try a different question.", "Alright, let me move to another topic.", "Got it. Here's a different one.", "Understood. Let me ask something else."]
SKIP_RESPONSES = ["Sure! Let's move on.", "No problem, next one.", "Of course! Here's another.", "Got it, moving forward."]
REPEAT_RESPONSES = ["Of course! The question was:", "Sure, let me repeat:", "No problem! Here it is again:"]
HR_ACKS = ["Thank you for sharing.", "That's a good point.", "I appreciate that.", "Interesting.", "Good to know."]

# =============================================================================
# DAILY STANDUP (DS_*)
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

    def add_exchange(self, ai_message, user_response, quality=0.0, chunk_id=None, concept=None, is_followup=False):
        self.exchanges.append(DS_ConversationExchange(timestamp=time.time(), stage=self.current_stage, ai_message=ai_message, user_response=user_response, transcript_quality=quality, chunk_id=chunk_id, concept=concept, is_followup=is_followup))
        self.last_activity = time.time()

class DS_SharedClientManager:
    def __init__(self):
        self._groq_client = None
        self._openai_client = None
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
    @property
    def groq_client(self):
        if not self._groq_client: self._groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        return self._groq_client
    @property
    def openai_client(self):
        if not self._openai_client: self._openai_client = openai_sync.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return self._openai_client
    @property
    def executor(self): return self._executor
    async def close_connections(self):
        if self._executor: self._executor.shutdown(wait=True)

ds_shared_clients = DS_SharedClientManager()

class DS_FragmentManager:
    def __init__(self, client_manager, session_data):
        self.client_manager = client_manager
        self.session_data = session_data
    def initialize_fragments(self, summary):
        self.session_data.fragments = {"General": summary or "No content"}
        self.session_data.fragment_keys = list(self.session_data.fragments.keys())
        return True
    def get_active_fragment(self): return "General", self.session_data.fragments.get("General", "")
    def should_continue_test(self): return len(self.session_data.exchanges) < 10
    def add_question(self, question, concept=None, is_followup=False): self.session_data.question_index += 1

DS_SummaryManager = DS_FragmentManager

class DS_OptimizedAudioProcessor:
    def __init__(self, client_manager): self.client_manager = client_manager
    async def transcribe_audio_fast(self, audio_data): return "transcribed text", 0.8

class DS_OptimizedConversationManager:
    def __init__(self, client_manager): self.client_manager = client_manager
    def _sync_openai_call(self, prompt):
        try:
            response = self.client_manager.openai_client.chat.completions.create(model=config.OPENAI_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.3, max_tokens=500)
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"[DS] OpenAI call error: {e}")
            return "Evaluation could not be generated due to an error."
    async def generate_fast_response(self, session_data, user_input):
        try:
            concept, context = session_data.summary_manager.get_active_fragment() if session_data.summary_manager else ("General", "")
            history = "\n".join([f"Q: {ex.ai_message}\nA: {ex.user_response}" for ex in session_data.exchanges[-5:] if ex.user_response])
            prompt = f"""You are conducting a daily standup technical check-in.\nContext: {context[:500] if context else 'General technical discussion'}\nRecent conversation:\n{history}\nUser's latest response: {user_input}\n\nGenerate a brief, encouraging response and ask a follow-up question about their work.\nKeep it conversational and supportive. MAX 2 sentences."""
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(self.client_manager.executor, self._sync_openai_call, prompt)
            return response if response else "Thank you for sharing. Tell me more about your work."
        except Exception as e:
            logger.error(f"[DS] Response generation error: {e}")
            return "Thank you for your response. Can you tell me more?"
    async def generate_fast_evaluation(self, session_data):
        try:
            exchanges_text = "\n".join([f"Q{i+1}: {ex.ai_message}\nA{i+1}: {ex.user_response or '[No response]'}" for i, ex in enumerate(session_data.exchanges)])
            if not exchanges_text: return "Session had no exchanges to evaluate.", 5.0
            prompt = f"""Evaluate this daily standup session for {session_data.student_name}.\n\nCONVERSATION:\n{exchanges_text}\n\nProvide a brief evaluation including:\n1. Overall performance summary (2-3 sentences)\n2. Score out of 10\n3. Key strengths (2-3 points)\n4. Areas to improve (2-3 points)\n\nStart your response with "SCORE: X/10" followed by the evaluation."""
            loop = asyncio.get_event_loop()
            evaluation = await loop.run_in_executor(self.client_manager.executor, self._sync_openai_call, prompt)
            score = 7.0
            score_match = re.search(r'SCORE:\s*(\d+(?:\.\d+)?)', evaluation, re.IGNORECASE)
            if score_match: score = min(max(float(score_match.group(1)), 0.0), 10.0)
            logger.info(f"[DS] Evaluation complete - Score: {score}/10")
            return evaluation, score
        except Exception as e:
            logger.error(f"[DS] Evaluation error: {e}")
            return "Evaluation complete. Good effort in today's standup!", 7.0

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
    question_type: str = "general"

@dataclass
class WI_ConversationState:
    current_topic: str = ""
    last_question: str = ""
    last_pure_question: str = ""
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
    silent_topics: List[str] = field(default_factory=list)
    topic_attempt_count: Dict[str, int] = field(default_factory=dict)
    used_behavioral_questions: List[str] = field(default_factory=list)
    used_hr_questions: List[str] = field(default_factory=list)
    previously_asked_hr_questions: List[str]=field(default_factory=list)
    technical_question_count: int = 0
    behavioral_question_count: int = 0
    current_tech_index: int = 0
    current_hr_index: int = 0
    current_topic_index: int = 0
    tech_question_types_used: Dict[str, List[str]] = field(default_factory=dict)
    extracted_technologies: List[str] = field(default_factory=list)
    extracted_topics_for_questions: List[str] = field(default_factory=list)
    extracted_projects: List[str] = field(default_factory=list)
    extracted_challenges: List[str] = field(default_factory=list)
    extracted_team_info: List[str] = field(default_factory=list)
    technical_answers: List[Dict[str, Any]] = field(default_factory=list)
    correct_answers: int = 0
    partial_answers: int = 0
    wrong_answers: int = 0
    is_finalized: bool = False
    _last_real_question: str = ""  # Survives round transitions (unlike conversation_state.last_pure_question)
    consecutive_no_response: int = 0  # Tracks consecutive questions with no real answer — auto-skip after MAX
    
    def __post_init__(self):
        self.interview_start_time = self.created_at
        logger.info(f"[WI] Session initialized. Interview start time: {self.interview_start_time}")

    def start_round(self, stage):
        current_time = time.time()
        logger.info(f"[WI] ===== STARTING ROUND: {stage.value} =====")
        self.round_start_times[stage.value] = current_time
        self.current_stage = stage
        self.conversation_state = WI_ConversationState()
        self.silence_prompt_count = 0  # Reset so new round gets fresh silence prompts
        self.consecutive_no_response = 0  # Reset silence streak for new round

    def get_round_elapsed_time(self):
        current_stage_value = self.current_stage.value
        current_time = time.time()
        if current_stage_value not in self.round_start_times:
            self.round_start_times[current_stage_value] = current_time
            return 0.0
        return current_time - self.round_start_times[current_stage_value]

    def get_round_elapsed_minutes(self): return self.get_round_elapsed_time() / 60
    
    def get_total_interview_time_minutes(self):
        if not hasattr(self, 'interview_start_time') or self.interview_start_time is None:
            self.interview_start_time = self.created_at
        return (time.time() - self.interview_start_time) / 60
    
    def get_questions_in_current_round(self): return self.questions_per_round.get(self.current_stage.value, 0)

    def add_exchange(self, ai_message, user_response="", quality=0.0, concept="", is_followup=False, answer_quality="neutral", expected_keywords=None, technical_accuracy=None, question_type="general"):
        ex = WI_ConversationExchange(timestamp=time.time(), stage=self.current_stage, ai_message=ai_message, user_response=user_response, transcript_quality=quality, concept=concept, is_followup=is_followup, answer_quality=answer_quality, expected_keywords=expected_keywords or [], technical_accuracy=technical_accuracy, question_type=question_type)
        self.exchanges.append(ex)
        self.questions_per_round[self.current_stage.value] = self.questions_per_round.get(self.current_stage.value, 0) + 1
        self.questions_asked.append(ai_message)
        # Don't overwrite _last_real_question with non-question responses (gibberish/silence prompts)
        non_question_phrases = [
            "i'm sorry, i didn't catch", "could you please repeat your answer",
            "take your time", "i'm here when you're ready", "no rush",
            "whenever you're ready", "no hurry", "don't worry",
            "i'm listening", "think it through", "no pressure",
            "are you ready", "can i continue", "still thinking",
            "repeat your answer", "didn't catch that",
            "feel free to take", "you can answer whenever", "completely fine",
            "let me try a different question", "let's move on to something else",
            "i'll ask you something different",
            "that concludes", "concludes our hr round", "you did great",
            "great interview", "generate your detailed feedback",
        ]
        is_non_question = any(phrase in ai_message.lower() for phrase in non_question_phrases)
        if '?' in ai_message and not is_non_question:
            parts = ai_message.split('?')
            for i in range(len(parts) - 1, -1, -1):
                part = parts[i].strip()
                if len(part) > 10:
                    for sep in ['. ', '! ', '\n']:
                        if sep in part: part = part.split(sep)[-1].strip()
                    self.conversation_state.last_pure_question = part + '?'
                    self._last_real_question = part + '?'
                    break
        elif not is_non_question:
            self.conversation_state.last_pure_question = ai_message
            self._last_real_question = ai_message

    def update_last_response(self, user_response, quality, answer_quality="neutral", technical_accuracy=None):
        if self.exchanges:
            self.exchanges[-1].user_response = user_response
            self.exchanges[-1].answer_quality = answer_quality
            self.exchanges[-1].technical_accuracy = technical_accuracy
            if technical_accuracy is not None:
                if technical_accuracy >= 0.7: self.correct_answers += 1
                elif technical_accuracy >= 0.4: self.partial_answers += 1
                else: self.wrong_answers += 1
        self.last_answer_quality = answer_quality

    def get_stage_conversation_history(self, stage, limit=10):
        exs = [e for e in self.exchanges if e.stage == stage][-limit:]
        return "\n".join([f"Q: {e.ai_message}\nA: {e.user_response}" for e in exs if e.user_response])

    def get_questions_asked_in_round(self, stage):
        return [e.ai_message for e in self.exchanges if e.stage == stage]

    def get_last_user_response(self):
        for ex in reversed(self.exchanges):
            if ex.user_response: return ex.user_response
        return ""
    
    def get_conversation_by_round(self):
        result = {"communication": [], "technical": [], "hr": []}
        for ex in self.exchanges:
            exchange_data = {"question": ex.ai_message, "answer": ex.user_response or "[NO RESPONSE]", "timestamp": ex.timestamp, "answer_quality": ex.answer_quality, "is_followup": ex.is_followup, "technical_accuracy": ex.technical_accuracy}
            if ex.stage == WI_InterviewStage.COMMUNICATION: result["communication"].append(exchange_data)
            elif ex.stage == WI_InterviewStage.TECHNICAL: result["technical"].append(exchange_data)
            elif ex.stage == WI_InterviewStage.HR: result["hr"].append(exchange_data)
        return result

# =============================================================================
# WI CLIENT MANAGER & FRAGMENT MANAGER
# =============================================================================

class WI_SharedClientManager:
    def __init__(self):
        self.openai_client: Optional[AsyncOpenAI] = None
        self.groq_client: Optional[AsyncGroq] = None
        self.executor = ThreadPoolExecutor(max_workers=16)  # Support 16 concurrent audio processing tasks
        self._initialized = False
    async def initialize(self):
        if self._initialized: return
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        self._initialized = True
    async def close_connections(self):
        if self.openai_client: await self.openai_client.close()
        if self.groq_client: await self.groq_client.close()
        self.executor.shutdown(wait=True)

wi_shared_clients = WI_SharedClientManager()

class WI_EnhancedInterviewFragmentManager:
    def __init__(self, client_manager, session):
        self.client_manager = client_manager
        self.session = session
    def initialize_fragments(self, summaries):
        if not summaries: return False
        self.session.content_context = "\n".join([s.get("summary", "") for s in summaries])
        self._extract_summary_info(self.session.content_context)
        self.session.start_round(WI_InterviewStage.INTRODUCTION)
        return True
    def _extract_summary_info(self, content):
        content_lower = content.lower()
        sap_keywords = ["sap", "abap", "fiori", "hana", "s/4hana", "s4hana", "mm", "sd", "fico", "pp", "wm", "ewm", "ariba", "successfactors", "bw", "btp", "t-code", "tcode", "transaction", "idoc", "bapi", "rfc", "smartforms", "sapscript", "odata", "client administration", "scc4", "sccl", "scc3", "basis"]
        developer_keywords = ["python", "javascript", "react", "node", "fastapi", "django", "flask", "mongodb", "mysql", "postgresql", "docker", "kubernetes", "aws", "azure", "java", "spring", "typescript", "angular", "vue", "express", "api", "rest", "graphql"]
        sap_matches = [k for k in sap_keywords if k in content_lower]
        dev_matches = [k for k in developer_keywords if k in content_lower]
        self.session.extracted_topics_for_questions = []
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('#') or line.endswith(':') or any(word in line.lower() for word in ['understanding', 'creating', 'configuring', 'implementing', 'troubleshooting', 'best practices', 'types of', 'step-by-step'])):
                topic = line.strip('#').strip('0123456789.').strip(':').strip()
                if len(topic) > 5 and len(topic) < 100: self.session.extracted_topics_for_questions.append(topic)
        concept_patterns = [r"(?:about|understand|learn)\s+(.+?)(?:\.|,|and|$)", r"(?:creating|configuring|implementing)\s+(.+?)(?:\.|,|and|$)", r"(?:using|with)\s+([A-Z][a-zA-Z0-9\s]+)(?:\.|,|and|$)", r"(?:T-code|transaction)\s+([A-Z0-9]+)"]
        for pattern in concept_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match) > 3 and len(match) < 50: self.session.extracted_topics_for_questions.append(match.strip())
        seen = set()
        unique_topics = []
        for topic in self.session.extracted_topics_for_questions:
            topic_lower = topic.lower()
            if topic_lower not in seen and len(topic) > 5: seen.add(topic_lower); unique_topics.append(topic)
        self.session.extracted_topics_for_questions = unique_topics[:20]
        if len(sap_matches) > len(dev_matches): self.session.extracted_technologies = list(set(sap_matches))[:15]
        elif len(dev_matches) > 0: self.session.extracted_technologies = list(set(dev_matches))[:15]
        else: self.session.extracted_technologies = []
        project_patterns = [r"worked on (.+?)(?:\.|,|and)", r"built (.+?)(?:\.|,|and)", r"developed (.+?)(?:\.|,|and)", r"implemented (.+?)(?:\.|,|and)", r"created (.+?)(?:\.|,|and)", r"configured (.+?)(?:\.|,|and)", r"managed (.+?)(?:\.|,|and)"]
        projects = []
        for pattern in project_patterns: projects.extend(re.findall(pattern, content_lower))
        self.session.extracted_projects = list(set(projects))[:10]
        challenge_patterns = [r"challenge.*?was (.+?)(?:\.|,)", r"difficult.*?(.+?)(?:\.|,)", r"problem.*?(.+?)(?:\.|,)", r"issue.*?was (.+?)(?:\.|,)", r"troubleshoot.*?(.+?)(?:\.|,)"]
        challenges = []
        for pattern in challenge_patterns: challenges.extend(re.findall(pattern, content_lower))
        self.session.extracted_challenges = list(set(challenges))[:5]
        if any(word in content_lower for word in ["team", "collaborate", "together", "group", "lead"]): self.session.extracted_team_info = ["worked in team"]
        logger.info(f"[WI] Extracted Technologies: {self.session.extracted_technologies[:5]}")
    def should_continue_round(self, stage):
        if stage == WI_InterviewStage.INTRODUCTION: return not self.session.introduction_completed
        duration = ROUND_DURATIONS.get(stage.value, 600)
        return self.session.get_round_elapsed_time() < duration
    def get_round_time_remaining(self):
        duration = ROUND_DURATIONS.get(self.session.current_stage.value, 600)
        return max(0, duration - self.session.get_round_elapsed_time())
    def add_question(self, question, concept, is_followup=False): pass


# =============================================================================
# NEW: HUMAN VOICE DETECTION + AUDIO PREPROCESSING + DEVICE HEALTH MONITOR
# =============================================================================

class HumanVoiceDetector:
    """Detects human voice and rejects non-human sounds (TV, fan, traffic, music)."""
    VOICE_FREQ_LOW = 60
    VOICE_FREQ_HIGH = 4000
    VOICE_ENERGY_THRESHOLD = 0.025  # Raised from 0.015 — speaker echo has rms=0.02-0.05
    VOICE_RATIO_THRESHOLD = 0.20
    ZCR_LOW = 0.01
    ZCR_HIGH = 0.45
    MIN_CONFIDENCE = 0.30  # Was 0.20 — too lenient for voice confirmation
    def __init__(self, sample_rate=16000): self.sample_rate = sample_rate
    def audio_bytes_to_numpy(self, audio_data):
        try:
            try:
                with io.BytesIO(audio_data) as audio_io:
                    with wave.open(audio_io, 'rb') as wav:
                        self.sample_rate = wav.getframerate()
                        n_channels = wav.getnchannels()
                        sampwidth = wav.getsampwidth()
                        frames = wav.readframes(wav.getnframes())
                        if sampwidth == 2: samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                        elif sampwidth == 4: samples = np.frombuffer(frames, dtype=np.int32).astype(np.float32) / 2147483648.0
                        else: samples = np.frombuffer(frames, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0
                        if n_channels > 1: samples = samples.reshape(-1, n_channels).mean(axis=1)
                        logger.debug("[VAD] Decoded as WAV: %d samples, sr=%d", len(samples), self.sample_rate)
                        return samples
            except Exception:
                pass
            try:
                target_sr = 16000
                result = subprocess.run(
                    ['ffmpeg', '-i', 'pipe:0', '-f', 's16le', '-acodec', 'pcm_s16le', '-ar', str(target_sr), '-ac', '1', 'pipe:1'],
                    input=audio_data, capture_output=True, timeout=10
                )
                if result.returncode == 0 and len(result.stdout) > 0:
                    samples = np.frombuffer(result.stdout, dtype=np.int16).astype(np.float32) / 32768.0
                    self.sample_rate = target_sr
                    logger.debug("[VAD] Decoded with ffmpeg: %d samples, sr=%d", len(samples), target_sr)
                    return samples
                else:
                    logger.warning("[VAD] ffmpeg decode failed (rc=%d): %s", result.returncode, result.stderr[:200].decode(errors='replace'))
            except subprocess.TimeoutExpired:
                logger.warning("[VAD] ffmpeg decode timed out")
            except FileNotFoundError:
                logger.warning("[VAD] ffmpeg not found on system, cannot decode compressed audio")
            except Exception as e:
                logger.warning("[VAD] ffmpeg decode error: %s", e)
            logger.warning("[VAD] Could not decode audio data (%d bytes)", len(audio_data))
            return None
        except Exception as e:
            logger.error(f"[VAD] Audio conversion failed: {e}")
            return None
    def _spectral_voice_ratio(self, samples):
        try:
            window = np.hanning(len(samples))
            fft_result = np.abs(np.fft.rfft(samples * window))
            freqs = np.fft.rfftfreq(len(samples), 1.0 / self.sample_rate)
            total_energy = np.sum(fft_result ** 2)
            if total_energy < 1e-10: return 0.0
            voice_mask = (freqs >= self.VOICE_FREQ_LOW) & (freqs <= self.VOICE_FREQ_HIGH)
            return np.sum(fft_result[voice_mask] ** 2) / total_energy
        except Exception: return 0.0
    def _zero_crossing_rate(self, samples):
        try:
            if len(samples) < 2: return 0.0
            signs = np.sign(samples)
            return np.sum(np.abs(np.diff(signs)) > 0) / len(samples)
        except Exception: return 0.0
    def _speech_pattern_score(self, samples, frame_size=1024):
        try:
            n_frames = len(samples) // frame_size
            if n_frames < 3: return 0.5
            frame_energies = np.array([np.sqrt(np.mean(samples[i*frame_size:(i+1)*frame_size]**2)) for i in range(n_frames)])
            max_energy = np.max(frame_energies)
            if max_energy < 1e-6: return 0.0
            frame_energies /= max_energy
            energy_std = np.std(frame_energies)
            energy_mean = np.mean(frame_energies)
            voiced = frame_energies > (energy_mean * 0.5)
            transition_rate = np.sum(np.abs(np.diff(voiced.astype(int)))) / n_frames
            score = 0.0
            if 0.1 <= transition_rate <= 0.5: score += 0.5
            elif transition_rate < 0.1: score += 0.1
            else: score += 0.2
            if 0.15 <= energy_std <= 0.45: score += 0.5
            elif energy_std < 0.15: score += 0.1
            else: score += 0.2
            return score
        except Exception: return 0.5
    def is_human_voice(self, audio_data):
        samples = self.audio_bytes_to_numpy(audio_data)
        if samples is None or len(samples) < 1000: return False, 0.0, {"error": "too_short"}
        rms = float(np.sqrt(np.mean(samples ** 2)))
        if rms < self.VOICE_ENERGY_THRESHOLD: return False, 0.0, {"rms": rms, "reason": "silence"}
        voice_ratio = self._spectral_voice_ratio(samples)
        zcr = self._zero_crossing_rate(samples)
        pattern = self._speech_pattern_score(samples)
        vr_score = min(voice_ratio / 0.6, 1.0) * 0.35 if voice_ratio >= self.VOICE_RATIO_THRESHOLD else (voice_ratio * 0.2)
        zcr_score = 0.0
        if self.ZCR_LOW <= zcr <= self.ZCR_HIGH:
            center = (self.ZCR_LOW + self.ZCR_HIGH) / 2
            deviation = abs(zcr - center) / (self.ZCR_HIGH - self.ZCR_LOW)
            zcr_score = (1.0 - deviation) * 0.25
        elif zcr < self.ZCR_LOW * 3:
            zcr_score = 0.08
        pat_score = pattern * 0.40
        confidence = vr_score + zcr_score + pat_score
        is_voice = confidence >= self.MIN_CONFIDENCE
        logger.info(f"[VAD] is_voice={is_voice} conf={confidence:.2f} [ratio={voice_ratio:.2f} zcr={zcr:.3f} pattern={pattern:.2f} rms={rms:.4f}]")
        return is_voice, confidence, {"rms": round(rms, 4), "voice_ratio": round(voice_ratio, 3), "confidence": round(confidence, 3), "is_voice": is_voice}

class AudioPreprocessor:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self._vad = HumanVoiceDetector(sample_rate)
    def _normalize(self, samples):
        max_val = np.max(np.abs(samples))
        return samples * (0.8 / max_val) if max_val > 1e-6 else samples
    def _trim_silence(self, samples, threshold=0.003, pad=3200):
        above = np.where(np.abs(samples) > threshold)[0]
        if len(above) == 0: return samples
        start = max(0, above[0] - pad)
        end = min(len(samples), above[-1] + pad)
        if (end - start) < len(samples) * 0.5:
            logger.debug("[AUDIO] Trim would remove >50%% of audio, skipping trim")
            return samples
        return samples[start:end]
    def _to_wav_bytes(self, samples):
        pcm = (samples * 32767).astype(np.int16)
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(self.sample_rate)
            wav.writeframes(pcm.tobytes())
        return buf.getvalue()
    def preprocess(self, audio_data):
        try:
            samples = self._vad.audio_bytes_to_numpy(audio_data)
            if samples is None: return audio_data
            orig_len = len(samples)
            samples = self._trim_silence(samples)
            samples = self._normalize(samples)
            logger.info(f"[AUDIO] Preprocessed: {orig_len} -> {len(samples)} samples")
            return self._to_wav_bytes(samples)
        except Exception as e:
            logger.error(f"[AUDIO] Preprocessing failed: {e}")
            return audio_data

class AudioDeviceHealthMonitor:
    GRACE_PERIOD = 10
    MAX_BAD_BEFORE_WARN = 3
    def __init__(self): self.last_good_time = None; self.consecutive_bad = 0; self.disconnect_detected = False
    def check_audio_health(self, audio_data):
        try:
            if not audio_data or len(audio_data) < 50: self.consecutive_bad += 1; return self._decide("empty_audio")
            vad = HumanVoiceDetector(); samples = vad.audio_bytes_to_numpy(audio_data)
            if samples is None: self.consecutive_bad += 1; return self._decide("unreadable")
            rms = float(np.sqrt(np.mean(samples ** 2)))
            if rms < 0.0005: self.consecutive_bad += 1; return self._decide("dead_silence")
            if rms > 0.9: self.consecutive_bad += 1; return self._decide("static")
            self.consecutive_bad = 0; self.disconnect_detected = False; self.last_good_time = time.time()
            return {"healthy": True, "action": "continue"}
        except Exception as e:
            logger.error(f"[DEVICE] Health check error: {e}"); return {"healthy": True, "action": "continue"}
    def _decide(self, issue):
        if self.consecutive_bad >= self.MAX_BAD_BEFORE_WARN:
            self.disconnect_detected = True
            if self.last_good_time:
                elapsed = time.time() - self.last_good_time
                if elapsed < self.GRACE_PERIOD:
                    return {"healthy": False, "action": "wait_reconnect", "issue": issue, "message": f"Audio device may have disconnected. Waiting {int(self.GRACE_PERIOD - elapsed)}s..."}
            return {"healthy": False, "action": "warn_user", "issue": issue, "message": "Audio device disconnected. Please check your headphones/microphone. You can continue with your built-in microphone."}
        return {"healthy": True, "action": "continue", "issue": issue}
    def reset(self): self.last_good_time = time.time(); self.consecutive_bad = 0; self.disconnect_detected = False

# =============================================================================
# ENHANCED WI_OptimizedAudioProcessor
# =============================================================================

class WI_OptimizedAudioProcessor:
    def __init__(self, client_manager):
        self.client_manager = client_manager
        self.voice_detector = HumanVoiceDetector()
        self.audio_preprocessor = AudioPreprocessor()
        self.device_monitor = AudioDeviceHealthMonitor()
        self.HALLUCINATION_PHRASES = [
            # === Original hallucinations ===
            "the speaker is answering questions about their", "interview response",
            "the speaker is answering", "answering questions about their work",
            "work experience, technical skills", "technical skills, and projects",
            "thank you for watching", "thanks for watching", "please subscribe",
            "like and subscribe", "see you in the next", "bye bye", "goodbye",
            "thank you for listening", "the end", "music", "applause", "laughter",
            "silence", "inaudible", "unintelligible", "foreign",
            "speaking foreign language", "don't forget to subscribe", "hit the bell",
            "leave a comment", "check out my", "link in description", "sponsored by",
            # === Whisper silence hallucinations (generates fake speech from noise) ===
            "i'm doing great", "thanks for asking", "please continue",
            "i'm gonna say", "i'm gonna be", "i'm going to",
            "well, my friends", "bama aum", "aum", "om",
            "yar yar", "yar, yar", "blah blah", "la la la",
            "hmm hmm hmm", "mmm mmm", "uh huh uh huh",
            "gonna be thinking about it", "thinking about it",
            "i think so", "i guess so", "yeah yeah yeah",
            "okay okay", "alright alright", "right right right",
            "you know what i mean", "you know what i'm saying",
            "so so so", "um um um", "uh uh uh",
            "this is a test", "testing testing", "hello hello",
            "can you hear me", "is this on", "one two three",
            "the the the", "a a a", "and and and",
            "i don't know what to say", "i have nothing to say",
            "subtitles by", "translated by", "captioned by",
            "copyright", "all rights reserved", "narrator",
            "chapter", "verse", "ameen", "amen", "namaste",
            "shukriya", "dhanyavaad", "bahut", "accha",
            # === Whisper Indian accent artifacts ===
            "bhai", "yaar", "acha", "theek hai", "kya",
            "haan ji", "nahin", "ji haan",
        ]

    def _decode_to_wav(self, audio_data: bytes) -> bytes:
        if audio_data[:4] == b'RIFF' and audio_data[8:12] == b'WAVE':
            logger.debug("[DECODE] Audio is already WAV format")
            return audio_data
        try:
            result = subprocess.run(
                ['ffmpeg', '-i', 'pipe:0', '-f', 'wav', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', 'pipe:1'],
                input=audio_data, capture_output=True, timeout=10
            )
            if result.returncode == 0 and len(result.stdout) > 100:
                logger.info("[DECODE] Converted %d bytes -> %d bytes WAV (ffmpeg)", len(audio_data), len(result.stdout))
                return result.stdout
            else:
                logger.warning("[DECODE] ffmpeg conversion failed (rc=%d): %s", result.returncode, result.stderr[:300].decode(errors='replace'))
                return None
        except subprocess.TimeoutExpired:
            logger.warning("[DECODE] ffmpeg timed out converting audio"); return None
        except FileNotFoundError:
            logger.error("[DECODE] ffmpeg not found"); return None
        except Exception as e:
            logger.error("[DECODE] Audio decode error: %s", e); return None

    async def transcribe_audio_fast(self, audio_data: bytes) -> Tuple[str, float]:
        await self.client_manager.initialize()
        # Minimum ~1 second of audio (16kHz × 2 bytes × 1 sec = 32000 bytes raw)
        # Compressed webm is smaller, so 16000 bytes ≈ ~1 sec
        if len(audio_data) < 16000:
            logger.info(f"[WI] Audio too short ({len(audio_data)} bytes < 16000), skipping")
            return "", 0.0
        
        loop = asyncio.get_event_loop()
        
        # Run CPU-bound ffmpeg decode in executor (doesn't block event loop for other users)
        decoded_wav = await loop.run_in_executor(
            self.client_manager.executor, self._decode_to_wav, audio_data
        )
        if decoded_wav is None:
            logger.warning("[WI] Could not decode audio, skipping"); return "", 0.0
        
        # Check WAV duration — reject if < 1.5 seconds (likely speaker echo, not real speech)
        wav_samples = len(decoded_wav) / 2  # 16-bit = 2 bytes per sample
        wav_duration_sec = wav_samples / 16000  # 16kHz sample rate
        if wav_duration_sec < 1.5:
            logger.info(f"[WI] WAV too short ({wav_duration_sec:.1f}s < 1.5s), likely speaker echo — skipping")
            return "", 0.0
        
        # Run CPU-bound device health check in executor
        device_health = await loop.run_in_executor(
            self.client_manager.executor, self.device_monitor.check_audio_health, decoded_wav
        )
        if not device_health["healthy"]:
            if device_health["action"] == "warn_user":
                logger.warning(f"[WI] Device disconnect: {device_health.get('message', '')}"); return "__DEVICE_DISCONNECTED__", 0.0
            elif device_health["action"] == "wait_reconnect":
                logger.info(f"[WI] Waiting for device reconnect: {device_health.get('message', '')}"); return "__DEVICE_RECONNECTING__", 0.0
        
        # Run CPU-bound VAD (numpy FFT) in executor
        is_voice, vad_confidence, vad_details = await loop.run_in_executor(
            self.client_manager.executor, self.voice_detector.is_human_voice, decoded_wav
        )
        if not is_voice:
            logger.info(f"[WI] Non-human sound rejected (conf={vad_confidence:.2f}). Skipping transcription."); return "", 0.0
        logger.info(f"[WI] Human voice confirmed (confidence={vad_confidence:.2f})")
        
        # Run CPU-bound audio preprocessing in executor
        processed_audio = await loop.run_in_executor(
            self.client_manager.executor, self.audio_preprocessor.preprocess, decoded_wav
        )
        logger.info(f"[WI] Audio preprocessed: {len(audio_data)} -> {len(processed_audio)} bytes")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
            tf.write(processed_audio); temp_path = tf.name
        try:
            with open(temp_path, "rb") as f: audio_bytes = f.read()
            tr = await self.client_manager.groq_client.audio.transcriptions.create(
                file=(temp_path, audio_bytes), model="whisper-large-v3-turbo", language="en",
                prompt="Interview candidate speaking about SAP, technical projects, work experience, and professional skills."
            )
            raw_text = tr.text.strip() if hasattr(tr, 'text') else ""
            if not raw_text: return "", 0.0
            
            # Check if Whisper produced a hallucination from noise/speaker echo
            if self._is_whisper_hallucination(raw_text):
                logger.info(f"[WI] Whisper hallucination rejected: '{raw_text[:80]}...'")
                return "", 0.0
            
            cleaned_text = self._remove_hallucinations(raw_text)
            confidence = self._calculate_confidence(cleaned_text)
            confidence = (confidence + vad_confidence) / 2
            if confidence < 0.3: return "", confidence
            final_text = self._final_cleanup(cleaned_text)
            if len(final_text.split()) < 2: return "", 0.2
            self.device_monitor.consecutive_bad = 0; self.device_monitor.disconnect_detected = False
            return final_text, confidence
        except Exception as e:
            logger.error(f"[WI] Transcription error: {e}"); return "", 0.0
        finally:
            try: os.unlink(temp_path)
            except: pass

    def _is_whisper_hallucination(self, raw_text):
        """Detect Whisper hallucinations from speaker echo / background noise.
        
        Whisper generates confident-sounding but nonsensical text when fed:
        - AI's own speech leaking through speakers
        - Background noise (fan, AC, traffic)  
        - Very short audio clips with ambient sound
        
        Returns True if the text is likely a hallucination.
        """
        if not raw_text: return True
        text = raw_text.lower().strip()
        words = text.split()
        word_count = len(words)
        
        # 1. Check for exact hallucination phrases (Whisper generates these from noise)
        exact_hallucinations = [
            "thank you.", "thanks.", "bye.", "bye bye.", "goodbye.",
            "thank you for watching.", "thanks for watching.",
            "please subscribe.", "see you next time.",
            "you", "thank you", "thanks", "bye", "hmm", "huh",
            "okay", "ok", "oh", "ah", "um", "uh", "so", "yeah",
        ]
        if text.rstrip('.!?,') in exact_hallucinations:
            logger.info(f"[HALLUCINATION] Exact match: '{text}'")
            return True
        
        # 2. Repetitive word pattern (yar yar yar, hmm hmm hmm, etc.)
        if word_count >= 3:
            unique_words = set(w.strip('.,!?') for w in words)
            if len(unique_words) <= 2:
                logger.info(f"[HALLUCINATION] Repetitive: '{text}' ({len(unique_words)} unique words)")
                return True
        
        # 3. Very short with no real content (< 4 real words after removing fillers)
        fillers = {'uh', 'um', 'oh', 'ah', 'eh', 'hmm', 'huh', 'so', 'like', 'okay', 
                   'ok', 'yeah', 'well', 'right', 'and', 'but', 'the', 'a', 'i', 'im',
                   "i'm", 'gonna', 'going', 'to', 'be', 'its', "it's"}
        real_words = [w.strip('.,!?') for w in words if w.strip('.,!?') not in fillers and len(w.strip('.,!?')) > 1]
        if len(real_words) < 2 and word_count <= 8:
            logger.info(f"[HALLUCINATION] Too few real words: {len(real_words)} in '{text}'")
            return True
        
        # 4. Grammatically broken patterns (Whisper noise artifacts)
        broken_patterns = [
            r'\b(\w+)\s+\1\s+\1',  # Triple word: "yar yar yar"
            r'very\s+too\b',        # "very too" is never valid English
            r'\bfriends\s+are\s+very\s+too\b',  # Specific hallucination seen in logs
            r'\bgonna\s+(?:say|be)\s.*gonna\s+(?:say|be)',  # Repeated "gonna say/be"
            r'(?:hm+\s*){3,}',      # "hmm hmm hmm"
            r'(?:ya+r?\s*[,.]?\s*){3,}',  # "yar, yar, yar"
        ]
        for pattern in broken_patterns:
            if re.search(pattern, text):
                logger.info(f"[HALLUCINATION] Broken pattern in: '{text}'")
                return True
        
        # 5. Whisper "echo" detection — if transcript sounds like it's repeating the AI question
        # These are common when mic picks up AI's TTS playback
        ai_echo_phrases = [
            "please continue", "let me ask", "here's a question",
            "let's move on", "that's interesting", "good to know",
            "tell me about", "can you describe", "what do you think",
            "great to hear", "let's get to know", "nice chatting",
            "how are you doing", "ready to get started",
            "welcome to your", "weekly interview", "three rounds",
            "communication round", "technical round", "hr round",
            "behavioral questions",
        ]
        echo_matches = sum(1 for phrase in ai_echo_phrases if phrase in text)
        if echo_matches >= 2:
            logger.info(f"[HALLUCINATION] AI echo detected ({echo_matches} matches): '{text[:60]}'")
            return True
        
        # 6. Nonsense words commonly generated by Whisper from noise
        nonsense_words = [
            'bama', 'aum', 'namaste', 'shukriya', 'dhanyavaad',
            'hauptrablers', 'kafir', 'kristian', 'corazn', 'servicio',
            'kampf', 'anarchist', 'cornered', 'puppet', 'taser',
            'pewdiepie', 'morpheus', 'voldemort',
        ]
        nonsense_count = sum(1 for w in words if w.strip('.,!?') in nonsense_words)
        if nonsense_count >= 1 and word_count <= 5:
            logger.info(f"[HALLUCINATION] Nonsense words in short text: '{text}'")
            return True
        
        return False

    def _remove_hallucinations(self, text):
        if not text: return ""
        result = text.lower()
        for phrase in self.HALLUCINATION_PHRASES: result = result.replace(phrase, "")
        cleaned = ""
        for char in result:
            if char.isascii() or char in ".,?!'\"- ": cleaned += char
        cleaned = re.sub(r'[.]{2,}', '.', cleaned); cleaned = re.sub(r'[,]{2,}', ',', cleaned); cleaned = re.sub(r'\s+', ' ', cleaned)
        words = cleaned.split()
        if len(words) > 3:
            deduped = []; repeat_count = 0; last_word = ""
            for word in words:
                if word.lower() == last_word.lower():
                    repeat_count += 1
                    if repeat_count <= 1: deduped.append(word)
                else: repeat_count = 0; deduped.append(word)
                last_word = word
            cleaned = " ".join(deduped)
        return cleaned.strip()

    def _calculate_confidence(self, text):
        if not text: return 0.0
        words = text.split(); word_count = len(words)
        if word_count < 2: return 0.1
        real_speech_indicators = {'i', 'we', 'my', 'our', 'the', 'this', 'that', 'is', 'are', 'was', 'were', 'have', 'has', 'had', 'do', 'did', 'work', 'worked', 'use', 'used', 'project', 'system', 'data', 'client', 'team', 'experience', 'years', 'developed', 'created', 'managed', 'handled', 'implemented', 'configured', 'learned', 'know', 'think', 'believe', 'like', 'want', 'need', 'yes', 'no', 'because', 'so', 'and', 'but', 'or', 'for', 'with'}
        text_lower = text.lower()
        indicator_count = sum(1 for word in real_speech_indicators if word in text_lower)
        indicator_score = min(indicator_count / 5, 1.0); length_score = min(word_count / 10, 1.0)
        gibberish_penalty = 0.0
        unique_ratio = len(set(words)) / len(words) if words else 0
        if unique_ratio < 0.5: gibberish_penalty += 0.3
        if re.search(r'[a-z]{10,}', text_lower): gibberish_penalty += 0.2
        confidence = (indicator_score * 0.5 + length_score * 0.5) - gibberish_penalty
        return max(0.0, min(1.0, confidence))

    def _final_cleanup(self, text):
        if not text: return ""
        text = text.strip()
        if text: text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
        if text and text[-1] not in '.?!': text += '.'
        return text

# =============================================================================
# WI CONVERSATION MANAGER - Main Logic
# =============================================================================

class WI_OptimizedConversationManager:
    def __init__(self, client_manager): self.client_manager = client_manager
    def _detect_user_intent(self, user_response):
        r = user_response.lower().strip()
        skip_phrases = [
            "skip this question", "skip the question", "skip question",
            "next question", "next question please", "move on",
            "next one", "next one please", "pass this", "let's skip",
            "i want to skip", "can we skip", "please skip",
            "can you skip", "skip please", "go to next",
        ]
        if r in ["skip", "next", "pass", "next please", "skip please"]:
            return "skip"
        if any(phrase in r for phrase in skip_phrases):
            return "skip"
        repeat_phrases = [
            "repeat the question", "repeat that question", "repeat question",
            "can you repeat", "could you repeat", "please repeat",
            "repeat please", "repeat it please", "say that again",
            "say it again", "say again please", "what was the question",
            "what's the question", "i didn't hear", "i didn't catch",
            "can you say that again", "one more time", "come again",
            "tell me the question again", "ask me again", "repeat it",
        ]
        if r in ["repeat", "repeat please", "say again", "come again", "pardon"]:
            return "repeat"
        if any(phrase in r for phrase in repeat_phrases):
            negation_patterns = ["don't repeat", "dont repeat", "do not repeat",
                               "no need to repeat", "not repeat", "without repeat",
                               "don't want to repeat", "dont want to repeat",
                               "no repeat", "stop repeat"]
            if any(neg in r for neg in negation_patterns):
                return "normal"
            return "repeat"
        cant_answer_phrases = [
            "i don't know", "i dont know", "i'm not sure", "im not sure",
            "no idea", "can't answer", "cant answer", "don't remember",
            "dont remember", "not sure about that", "i have no idea",
            "i don't have any idea", "no clue",
        ]
        if any(phrase in r for phrase in cant_answer_phrases):
            return "dont_know"
        return "normal"

    def _is_gibberish(self, text):
        if not text: return True
        text_lower = text.lower().strip()
        words = text_lower.split()
        word_count = len(words)
        ascii_chars = sum(1 for c in text if c.isascii())
        if len(text) > 0 and (ascii_chars / len(text)) < 0.8: return True
        if word_count > 5:
            unique_ratio = len(set(words)) / word_count
            if unique_ratio < 0.3: return True
        nonsense_patterns = [r'(.)\1{4,}', r'\b(\w+)\s+\1\s+\1\s+\1']
        for pattern in nonsense_patterns:
            if re.search(pattern, text_lower): return True
        hallucinations = [
            "thank you for watching", "please subscribe", "like and subscribe",
            "see you next time", "bye bye bye", "youtube", "mcdonald",
            "link in description", "check out my", "sponsored by",
            "the speaker is answering", "interview response",
        ]
        if any(h in text_lower for h in hallucinations): return True
        fillers = ['uh', 'um', 'oh', 'ah', 'eh', 'so', 'yeah', 'like', 'okay', 'right', 'well']
        filler_count = sum(1 for w in words if w.strip('.,!?') in fillers)
        if word_count > 5 and filler_count / word_count > 0.35:
            logger.info(f"[GIBBERISH] Too many fillers: {filler_count}/{word_count} = {filler_count/word_count:.0%}")
            return True
        whisper_random_nouns = [
            'milk', 'bomb', 'taiwan', 'soviet', 'penguin', 'puppet', 'taser',
            'iphone', 'platinum', 'kiss', 'cornered', 'lung', 'dance',
            'cooking', 'cabinet', 'alcohol', 'armor', 'dynasty', 'camera',
            'buffet', 'elsa', 'puppy', 'napkins', 'iron', 'pits', 'legs',
            'weather pattern', 'body', 'nooks', 'kampf', 'anarchist',
            'corazn', 'servicio', 'hauptrablers', 'kafir', 'kristian',
        ]
        random_noun_count = sum(1 for noun in whisper_random_nouns if noun in text_lower)
        if random_noun_count >= 2:
            logger.info(f"[GIBBERISH] Whisper random nouns detected: {random_noun_count}")
            return True
        if word_count > 10:
            comma_count = text_lower.count(',')
            if comma_count > word_count * 0.25:
                tech_words = ['sap', 'client', 'transaction', 'system', 'data', 'server',
                             'config', 'table', 'module', 'basis', 'abap', 'fiori', 'user',
                             'scc4', 'sccl', 'scc3', 'rfc', 'sm50', 'su01', 'se09']
                has_any_tech = any(tw in text_lower for tw in tech_words)
                if not has_any_tech:
                    logger.info(f"[GIBBERISH] Too many commas ({comma_count}) with no tech content")
                    return True
        if word_count > 30:
            sentences = re.split(r'[.!?]', text_lower)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 3]
            if len(sentences) < 2:
                filler_ratio = filler_count / word_count if word_count > 0 else 0
                if filler_ratio > 0.2:
                    logger.info(f"[GIBBERISH] Long text, no sentences, high fillers")
                    return True
        if word_count > 8:
            gibberish_score = 0.0
            filler_ratio = filler_count / word_count
            if filler_ratio > 0.25: gibberish_score += 0.35
            elif filler_ratio > 0.15: gibberish_score += 0.2
            elif filler_ratio > 0.08: gibberish_score += 0.1
            if random_noun_count >= 2: gibberish_score += 0.4
            elif random_noun_count == 1: gibberish_score += 0.25
            tech_words = ['sap', 'client', 'transaction', 'system', 'data', 'server',
                         'config', 'table', 'module', 'basis', 'abap', 'fiori', 'user',
                         'scc4', 'sccl', 'scc3', 'rfc', 'sm50', 'su01', 'se09',
                         'copy', 'transport', 'login', 'authorization', 'profile',
                         'instance', 'dispatcher', 'kernel', 'parameter', 'landscape']
            has_any_tech = any(tw in text_lower for tw in tech_words)
            if not has_any_tech: gibberish_score += 0.3
            comma_count = text_lower.count(',')
            if comma_count > word_count * 0.2: gibberish_score += 0.15
            if gibberish_score >= 0.50:
                logger.info(f"[GIBBERISH] Combined score {gibberish_score:.2f} (fillers={filler_ratio:.0%}, random_nouns={random_noun_count}, tech={has_any_tech})")
                return True
        return False

    def _is_off_topic(self, user_response, stage, session=None):
        """Detect if user's answer is completely unrelated to the current round.
        
        Returns (True, detected_topic) if off-topic, (False, None) if on-topic.
        
        Rules:
        - Communication round: almost everything is on-topic (casual chat)
        - Technical round: must relate to tech/work/projects — NOT movies, food, shopping
        - HR round: must relate to work experiences, behavior, career — NOT random topics
        """
        if stage == WI_InterviewStage.COMMUNICATION:
            return False, None  # Casual round, anything goes
        
        if stage == WI_InterviewStage.INTRODUCTION:
            return False, None
        
        r = user_response.lower().strip()
        words = r.split()
        word_count = len(words)
        
        # Very short answers — handled by "weak" quality, not off-topic
        if word_count < 5:
            return False, None
        
        # ── Off-topic indicators: topics that NEVER belong in tech/HR answers ──
        off_topic_categories = {
            "movies/entertainment": ['movie', 'film', 'netflix', 'series', 'episode', 'actor', 'actress', 'bollywood', 'hollywood', 'avengers', 'marvel', 'dc comics', 'spider-man', 'batman'],
            "food/cooking": ['recipe', 'cooking', 'biryani', 'pizza', 'burger', 'restaurant', 'kitchen', 'ingredients', 'breakfast', 'lunch', 'dinner', 'snack', 'dessert', 'ice cream'],
            "shopping": ['shopping', 'mall', 'bought clothes', 'discount', 'sale', 'amazon order', 'flipkart', 'online shopping', 'market', 'grocery'],
            "sports/games": ['cricket match', 'ipl', 'football match', 'world cup', 'scored goals', 'batting', 'bowling', 'pubg', 'free fire', 'gaming'],
            "social media": ['instagram', 'snapchat', 'tiktok', 'reels', 'followers', 'viral video', 'trending', 'influencer'],
            "personal life": ['girlfriend', 'boyfriend', 'dating', 'wedding', 'party last night', 'went to beach', 'vacation photos', 'temple visit', 'pilgrimage'],
            "random topics": ['weather today', 'traffic jam', 'politics', 'election', 'petrol price', 'gold rate', 'stock market crash', 'lottery', 'horoscope', 'zodiac'],
        }
        
        detected_category = None
        off_topic_matches = 0
        
        for category, keywords in off_topic_categories.items():
            for kw in keywords:
                if kw in r:
                    off_topic_matches += 1
                    detected_category = category
        
        # Need at least 1 off-topic keyword match
        if off_topic_matches == 0:
            return False, None
        
        # ── On-topic indicators: if user mentions ANY of these, it's likely on-topic ──
        # (Even if they also mention food — e.g. "I configured the SAP system after lunch")
        if stage == WI_InterviewStage.TECHNICAL:
            tech_indicators = [
                'sap', 'abap', 'fiori', 'hana', 'basis', 'client', 'transaction', 'tcode',
                't-code', 'config', 'system', 'server', 'data', 'table', 'module', 'rfc',
                'bapi', 'idoc', 'odata', 'transport', 'landscape', 'kernel', 'profile',
                'python', 'javascript', 'react', 'node', 'api', 'database', 'mongodb',
                'docker', 'aws', 'code', 'function', 'class', 'error', 'debug', 'deploy',
                'project', 'implement', 'configure', 'develop', 'build', 'test', 'query',
                'algorithm', 'architecture', 'framework', 'library', 'repository', 'git',
                'sql', 'html', 'css', 'backend', 'frontend', 'microservice', 'pipeline',
                'work', 'team', 'task', 'requirement', 'sprint', 'agile', 'production',
            ]
            # Also check session-extracted technologies
            if session and session.extracted_technologies:
                tech_indicators.extend([t.lower() for t in session.extracted_technologies])
            
            has_tech = any(t in r for t in tech_indicators)
            if has_tech:
                return False, None  # Has tech content, not off-topic
            
        elif stage == WI_InterviewStage.HR:
            hr_indicators = [
                'team', 'lead', 'manage', 'project', 'deadline', 'challenge', 'conflict',
                'colleague', 'boss', 'manager', 'feedback', 'improve', 'learn', 'grow',
                'career', 'goal', 'strength', 'weakness', 'decision', 'responsibility',
                'initiative', 'collaborate', 'communicate', 'prioritize', 'pressure',
                'failure', 'success', 'achievement', 'experience', 'situation', 'approach',
                'problem', 'solution', 'work', 'office', 'company', 'organization',
                'professional', 'skill', 'role', 'position', 'interview', 'internship',
            ]
            has_hr = any(t in r for t in hr_indicators)
            if has_hr:
                return False, None  # Has HR-relevant content
        
        # Off-topic keyword found AND no on-topic content → it's off-topic
        logger.info(f"[OFF-TOPIC] Detected category: {detected_category}, matches: {off_topic_matches}")
        return True, detected_category

    def _assess_answer_quality(self, user_response, stage=None, session=None):
        if not user_response: return "silence"
        if self._is_gibberish(user_response): return "gibberish"
        intent = self._detect_user_intent(user_response)
        if intent != "normal": return "skip" if intent == "skip" else ("repeat" if intent == "repeat" else "cant_answer")
        # Check for off-topic content (only in technical/HR rounds)
        if stage and stage in [WI_InterviewStage.TECHNICAL, WI_InterviewStage.HR]:
            is_offtopic, category = self._is_off_topic(user_response, stage, session)
            if is_offtopic: return "off_topic"
        words = len(user_response.split())
        if words <= 3: return "weak"
        strong = ["because", "therefore", "for example", "specifically", "implemented", "experience", "i think", "used", "worked", "built", "designed", "configured", "created", "developed", "managed", "handled"]
        if words >= 20 and any(k in user_response.lower() for k in strong): return "strong"
        return "neutral" if words >= 10 else "weak"

    async def _evaluate_technical_accuracy(self, session, question, answer, expected_keywords):
        if not answer or len(answer.split()) < 3: return 0.0
        await self.client_manager.initialize()
        prompt = f"""Evaluate this technical interview answer.\n\nQuestion: {question}\nAnswer: {answer}\nContext (user's work): {session.content_context[:500] if session.content_context else 'General'}\n\nRate accuracy from 0.0 to 1.0:\n- 1.0 = Correct, detailed, shows understanding\n- 0.7 = Mostly correct, some details\n- 0.5 = Partially correct, missing key points\n- 0.3 = Vague or mostly incorrect\n- 0.0 = Wrong or no real answer\n\nReply with ONLY a number between 0.0 and 1.0"""
        try:
            resp = await self.client_manager.openai_client.chat.completions.create(model=config.OPENAI_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.1, max_tokens=10)
            score_text = resp.choices[0].message.content.strip()
            score = float(re.search(r"(\d+\.?\d*)", score_text).group(1))
            return min(max(score, 0.0), 1.0)
        except:
            answer_lower = answer.lower()
            if expected_keywords:
                matches = sum(1 for k in expected_keywords if k.lower() in answer_lower)
                return min(matches / len(expected_keywords), 1.0)
            return 0.5 if len(answer.split()) > 10 else 0.3

    def _extract_topics_from_response(self, response, session=None):
        response_lower = response.lower()
        if session and session.extracted_technologies: return [t for t in session.extracted_technologies if t in response_lower]
        all_tech = ["python", "javascript", "react", "node", "api", "database", "mongodb", "mysql", "docker", "aws", "frontend", "backend", "testing", "debugging", "git", "sap", "abap", "fiori", "hana", "mm", "sd", "fico"]
        return [t for t in all_tech if t in response_lower]

    def _get_unique_transition(self, session):
        used = session.conversation_state.used_transitions
        available = [t for t in COMMUNICATION_TRANSITIONS if t not in used] or COMMUNICATION_TRANSITIONS
        t = random.choice(available)
        session.conversation_state.used_transitions.append(t)
        if len(session.conversation_state.used_transitions) > 10: session.conversation_state.used_transitions = session.conversation_state.used_transitions[-10:]
        return t

    def _should_followup(self, session, quality):
        if quality in ["weak", "cant_answer", "silence", "skip", "repeat"]: return False
        if session.conversation_state.followups_on_topic >= 2: return False
        return random.random() < (0.6 if quality == "strong" else 0.4)

    def _extract_question_from_response(self, ai_message):
        if not ai_message: return "Could you please repeat your answer?"
        prefixes_to_remove = ["Of course! The question was:", "Sure, let me repeat:", "No problem! Here it is again:", "Let me repeat that:", "Here's the question again:"]
        cleaned = ai_message.strip()
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix): cleaned = cleaned[len(prefix):].strip()
        if '?' in cleaned:
            parts = cleaned.split('?')
            for i in range(len(parts) - 1, -1, -1):
                part = parts[i].strip()
                if len(part) > 10:
                    for sep in ['. ', '! ', '\n']:
                        if sep in part: part = part.split(sep)[-1].strip()
                    return part + '?'
            last_q_idx = cleaned.rfind('?')
            return cleaned[:last_q_idx + 1].strip()
        return cleaned

    def _adjust_difficulty(self, session, quality):
        if session.current_stage != WI_InterviewStage.TECHNICAL: return
        if quality == "strong": session.current_difficulty = "hard" if session.current_difficulty == "medium" else "medium"
        elif quality in ["weak", "cant_answer"]: session.current_difficulty = "easy"

    async def _generate_communication_question(self, session, is_first=False):
        await self.client_manager.initialize()
        asked = session.get_questions_asked_in_round(WI_InterviewStage.COMMUNICATION)
        topics = ["weekend plans", "favorite food", "travel dreams", "morning routine", "favorite movie or show", "music preferences", "childhood memories", "dream vacation", "favorite season", "cooking or eating out", "pets or animals", "sports or fitness", "books or reading", "family traditions", "city or countryside", "coffee or tea", "early bird or night owl", "relaxation methods", "learning something new", "favorite holiday", "hometown memories", "friends and social life", "dream job as a child", "favorite game", "weather preferences"]
        used_topics = session.communication_topics_covered
        available = [t for t in topics if t not in used_topics]
        if not available: available = topics
        chosen_topic = random.choice(available)
        session.communication_topics_covered.append(chosen_topic)
        prompt = f"""Generate ONE friendly casual question about: {chosen_topic}\nKeep it natural like a human conversation.\nAlready asked (DO NOT repeat): {asked[-5:]}\nMAX 12 words. Just the question."""
        resp = await self.client_manager.openai_client.chat.completions.create(model=config.OPENAI_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.9, max_tokens=30)
        q = resp.choices[0].message.content.strip()
        q_lower = q.lower()
        for asked_q in asked:
            if self._is_similar_question(q_lower, asked_q.lower()):
                q = random.choice([f"What do you think about {chosen_topic}?", f"Tell me about your {chosen_topic}?", f"How do you feel about {chosen_topic}?"]); break
        return q if '?' in q else q + "?"

    def _is_similar_question(self, q1, q2):
        q1_clean = q1.lower().strip().rstrip('?').strip(); q2_clean = q2.lower().strip().rstrip('?').strip()
        if q1_clean == q2_clean: return True
        words1 = set(q1_clean.split()); words2 = set(q2_clean.split())
        common_words = {'what', 'how', 'why', 'when', 'where', 'who', 'is', 'are', 'the', 'a', 'an', 'your', 'you', 'can', 'do', 'did', 'does', 'tell', 'me', 'about', 'describe', 'explain'}
        words1 = words1 - common_words; words2 = words2 - common_words
        if len(words1) == 0 or len(words2) == 0: return False
        overlap = len(words1 & words2); min_len = min(len(words1), len(words2))
        return overlap / min_len > 0.4

    def _get_off_topic_response(self, session=None, stage=None):
        """Return a context-aware off-topic redirect.
        
        - 1st off-topic: gentle redirect
        - 2nd off-topic: firmer redirect mentioning the round
        - 3rd+ off-topic: firm redirect + warning
        """
        if not hasattr(self, '_consecutive_off_topic'): self._consecutive_off_topic = 0
        self._consecutive_off_topic += 1
        
        # Get current round name for context
        round_name = "this topic"
        if stage == WI_InterviewStage.TECHNICAL:
            round_name = "your technical work"
            if session and session.extracted_technologies:
                current_techs = [t for t in session.extracted_technologies if t not in (session.silent_topics or [])]
                if current_techs:
                    round_name = f"your work with {current_techs[0]}"
        elif stage == WI_InterviewStage.HR:
            round_name = "your work experiences and professional situations"
        
        if self._consecutive_off_topic >= 3:
            # Firm warning
            responses = [
                f"I notice your answers aren't related to {round_name}. Please try to focus on the question. Let me ask another one.",
                f"We need to stay focused on {round_name}. Let me try a different question.",
                f"That's not related to what I asked. Let's get back to {round_name}.",
            ]
        elif self._consecutive_off_topic >= 2:
            # Medium redirect
            responses = [
                f"That doesn't seem related to {round_name}. No worries, let me ask something else.",
                f"I think that's a bit off-topic. Let me ask about {round_name} instead.",
                f"Let's focus on {round_name}. Here's a different question.",
            ]
        else:
            # Gentle redirect (1st time)
            responses = [
                "I think you might not be aware of that, let me ask you something different.",
                "No worries, let me move on to a different question.",
                "That's okay, I'll ask you something else instead.",
                "I see, let me try a different topic.",
                "Alright, let's switch to another question.",
                "No problem at all, let me ask you something you might be more familiar with.",
                "That's fine, I'll move on to a different one.",
                "Okay, don't worry about that, here's another question for you.",
                "Let me ask you something different instead.",
                "I understand, let's try a different question.",
            ]
        
        if not hasattr(self, '_last_off_topic_idx'): self._last_off_topic_idx = -1
        idx = random.randint(0, len(responses) - 1)
        while idx == self._last_off_topic_idx and len(responses) > 1:
            idx = random.randint(0, len(responses) - 1)
        self._last_off_topic_idx = idx
        return responses[idx]
    
    def _reset_off_topic_counter(self):
        """Reset consecutive off-topic counter when user gives an on-topic answer."""
        self._consecutive_off_topic = 0

    async def _generate_dynamic_ack(self, context, tone="friendly"):
        await self.client_manager.initialize()
        prompts = {
            "weak": "Generate ONE short understanding response when someone gives unclear answer. Like 'I see, let me try another question' or 'Okay, let's move on'. MAX 8 words.",
            "good": "Generate ONE short positive acknowledgment like 'That's nice!' or 'Good to know!' MAX 5 words.",
            "technical_good": "Generate ONE short acknowledgment for a good technical answer. Like 'Good point.' or 'Right.' or 'Okay, good.' MAX 4 words. Do NOT say 'impressive' or 'exactly right'.",
            "technical_weak": "Generate ONE short understanding response for unclear technical answer. Like 'I see.' or 'Okay.' MAX 5 words.",
            "cant_answer": "Generate ONE short supportive response when someone can't answer, like 'No problem, let's try something else'. MAX 10 words.",
            "transition": "Generate ONE short transition phrase like 'Okay!' or 'Alright.' MAX 3 words. Do NOT say 'impressive' or 'great insight'.",
            "hr": "Generate ONE short professional acknowledgment like 'Thank you for sharing' or 'Good point'. MAX 5 words.",
        }
        prompt = prompts.get(tone, prompts["good"])
        try:
            resp = await self.client_manager.openai_client.chat.completions.create(model=config.OPENAI_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.9, max_tokens=20)
            ack = resp.choices[0].message.content.strip().replace('"', '').replace("'", "")
            if not ack.endswith(('!', '.', '?')): ack += '!'
            return ack
        except:
            fallbacks = {"weak": "I see. Let me ask something else.", "good": "Nice!", "technical_good": "Good explanation!", "technical_weak": "Okay, let's try another one.", "cant_answer": "No problem! Let's move on.", "transition": "Interesting!", "hr": "Thank you."}
            return fallbacks.get(tone, "Okay!")

    async def _generate_communication_followup(self, session, user_response):
        await self.client_manager.initialize()
        prompt = f"""User said: "{user_response[:100]}"\nGenerate a short follow-up question. MAX 12 words."""
        resp = await self.client_manager.openai_client.chat.completions.create(model=config.OPENAI_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.8, max_tokens=30)
        q = resp.choices[0].message.content.strip()
        return q if '?' in q else q + "?"

    async def _generate_technical_question(self, session, user_response="", include_behavioral=False):
        await self.client_manager.initialize()
        if not hasattr(session, 'total_technical_questions_generated'): session.total_technical_questions_generated = 0
        session.total_technical_questions_generated += 1
        if not hasattr(session, 'used_technical_templates'): session.used_technical_templates = []
        if not hasattr(session, 'used_behavioral_templates'): session.used_behavioral_templates = []
        all_asked_questions = list(session.questions_asked)
        response_quality = "none"; should_followup = False; prefix = ""
        if user_response:
            response_lower = user_response.lower().strip(); word_count = len(response_lower.split())
            bad_indicators = ["thank you", "skip", "next", "i don't know", "no idea", "can't answer", "pass", "move on", "bye", "i can't", "don't understand", "not sure", "no clue", "don't remember", "hello", "hi", "okay", "ok", "yes", "no"]
            words = response_lower.split(); unique_words = set(words)
            is_repetitive = len(words) > 3 and len(unique_words) < len(words) * 0.4
            tech_keywords = ['sap', 'client', 'transaction', 't-code', 'config', 'system', 'data', 'user', 'table', 'module', 'basis', 'abap', 'fiori', 'report', 'program', 'function', 'process', 'implement', 'configure', 'setup', 'install', 'error', 'issue', 'problem', 'solution', 'project', 'team', 'work', 'experience', 'used', 'created', 'developed', 'managed', 'handled', 'deployed']
            has_tech_content = any(kw in response_lower for kw in tech_keywords)
            irrelevant = ['mcdonald', 'youtube', 'google', 'phone', 'rupee', 'otp', 'video', 'movie', 'song', 'food', 'hospital', 'cookie']
            has_irrelevant = any(irr in response_lower for irr in irrelevant)
            is_bad_answer = (word_count < 8 or is_repetitive or has_irrelevant or any(indicator == response_lower.strip() for indicator in bad_indicators) or (word_count < 15 and not has_tech_content))
            if is_bad_answer:
                response_quality = "bad"; prefix = self._get_off_topic_response(session=session, stage=WI_InterviewStage.TECHNICAL) + " "
                if session.exchanges:
                    last_q = session.exchanges[-1].ai_message.lower()
                    for tech in (session.extracted_technologies or []):
                        if tech.lower() in last_q and tech not in session.silent_topics: session.silent_topics.append(tech); break
            elif word_count >= 20 and has_tech_content:
                response_quality = "good"; should_followup = True; prefix = self._get_encouragement() + " "
        if should_followup and user_response:
            follow_up = await self._generate_followup_from_answer(session, user_response, all_asked_questions)
            if follow_up: return f"{prefix}{follow_up}", ["followup"]
        technologies = [t for t in (session.extracted_technologies or []) if t not in session.silent_topics]
        if not technologies: technologies = ["your work experience", "your daily tasks", "your technical skills"]
        total_qs = session.technical_question_count + session.behavioral_question_count
        should_be_behavioral = (include_behavioral and total_qs > 0 and total_qs % 4 == 3)
        if should_be_behavioral:
            session.behavioral_question_count += 1
            return await self._generate_technical_behavioral_question_dynamic(session, technologies, all_asked_questions, prefix)
        session.technical_question_count += 1
        tech_idx = session.current_tech_index % len(technologies); chosen_tech = technologies[tech_idx]; session.current_tech_index += 1
        question = await self._generate_dynamic_question_from_summary(session, chosen_tech, all_asked_questions)
        full_question = f"{prefix}{question}" if prefix else question
        if chosen_tech not in session.technical_topics_covered: session.technical_topics_covered.append(chosen_tech)
        return full_question, [chosen_tech]

    async def _generate_technical_behavioral_question_dynamic(self, session, technologies, all_asked, prefix=""):
        await self.client_manager.initialize()
        tech_idx = session.current_tech_index % len(technologies); chosen_tech = technologies[tech_idx]
        summary_context = session.content_context[:1000] if session.content_context else ""
        prompt = f"""Generate ONE technical behavioral interview question for a candidate who works with {chosen_tech}.

CANDIDATE'S BACKGROUND:
{summary_context}

Ask about a REAL TECHNICAL SCENARIO specifically related to {chosen_tech} as mentioned in the background above.
ONLY ask about topics that appear in the candidate's background — do NOT invent unrelated topics.

Vary the phrasing. Use ONE of these styles randomly:
- "Tell me about a time when..."
- "Walk me through how you handled..."
- "What was the most difficult part of working with..."
- "How did you approach [specific task] with..."
- "What would you do if [specific situation] happened with..."

DO NOT ask generic HR questions like "tell me about leadership".
DO NOT start every question with "Can you describe a challenge..."

ALREADY ASKED (DO NOT REPEAT):
{chr(10).join(all_asked[-15:])}

Generate ONE specific question (MAX 25 words):"""
        try:
            resp = await self.client_manager.openai_client.chat.completions.create(model=config.OPENAI_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.8, max_tokens=60)
            question = resp.choices[0].message.content.strip().strip('"').strip("'")
            if not question.endswith('?'): question += '?'
        except Exception as e:
            logger.error(f"Error generating technical behavioral question: {e}")
            question = f"Tell me about a challenging technical problem you solved with {chosen_tech}?"
        full_question = f"{prefix}{question}" if prefix else question
        session.used_behavioral_questions.append(question)
        logger.info(f"[WI] Technical Behavioral (Dynamic): {question[:60]}...")
        return full_question, [chosen_tech, "technical_behavioral"]

    async def _generate_dynamic_question_from_summary(self, session, tech, all_asked):
        await self.client_manager.initialize()
        summary = session.content_context or "General technical work"

        # ── FIX 1: Question Type Rotation (8 types, shuffled per session) ──
        # Each session gets a random order of 8 fundamentally different question types
        # This ensures variety at scale — no two interviews feel the same
        if not hasattr(session, '_question_type_order'):
            session._question_type_order = [
                "theory", "practical", "scenario", "troubleshooting",
                "comparison", "architecture", "best_practice", "real_world",
            ]
            random.shuffle(session._question_type_order)
            session._question_type_index = 0

        q_type = session._question_type_order[session._question_type_index % len(session._question_type_order)]
        session._question_type_index += 1

        # Track recent question starters to avoid repetitive phrasing
        if not hasattr(session, '_recent_q_starters'): session._recent_q_starters = []
        avoid_starters = ", ".join(session._recent_q_starters[-3:]) if session._recent_q_starters else "none"

        type_instructions = {
            "theory": f"Ask a CONCEPT KNOWLEDGE question about {tech}. Test what they know.\nExamples: 'What is {tech}?', 'What are the key features of {tech}?', 'Explain the purpose of {tech}.'\nDo NOT ask about challenges. Just test their understanding.",
            "practical": f"Ask a HOW-TO / STEPS question about {tech}. Ask about the PROCESS.\nExamples: 'How do you configure {tech}?', 'What steps do you follow to set up {tech}?', 'Walk me through using {tech}.'",
            "scenario": f"Ask a REAL EXPERIENCE question about {tech}. Ask about a SPECIFIC situation they faced.\nExamples: 'Tell me about a time you used {tech} to solve a problem.', 'Describe a project where {tech} was critical.'",
            "troubleshooting": f"Ask a DEBUGGING / ERROR HANDLING question about {tech}.\nExamples: 'What would you do if {tech} threw an error?', 'How do you troubleshoot issues with {tech}?', 'What common problems occur with {tech}?'",
            "comparison": f"Ask a COMPARE / DIFFERENTIATE question about {tech}.\nExamples: 'What is the difference between [X] and [Y] in {tech}?', 'When would you choose [approach A] over [approach B]?'",
            "architecture": f"Ask a SYSTEM DESIGN / ARCHITECTURE question about {tech}.\nExamples: 'How does {tech} fit into the overall system?', 'What components interact with {tech}?', 'How would you design a solution using {tech}?'",
            "best_practice": f"Ask a BEST PRACTICES / STANDARDS question about {tech}.\nExamples: 'What best practices do you follow with {tech}?', 'How do you ensure quality when working with {tech}?', 'What mistakes should be avoided?'",
            "real_world": f"Ask for a SPECIFIC REAL EXAMPLE from their work with {tech}.\nExamples: 'Give me a concrete example of how you used {tech}.', 'What was the output or result of your {tech} work?', 'Show me your understanding with a real example.'",
        }

        prompt = f"""Generate ONE technical interview question for a candidate.

CANDIDATE'S WORK SUMMARY:
{summary[:1500]}

TOPIC: {tech}

QUESTION TYPE: {q_type.upper()}
{type_instructions[q_type]}

STRICT RULES:
1. ONLY ask about topics that appear in the candidate's work summary above
2. Do NOT ask about topics NOT in the summary (no random SAP modules, no PP, no MM unless mentioned)
3. The question MUST be specifically about {tech} as mentioned in the summary
4. Do NOT start with "Can you describe a challenge..." — vary the phrasing

ALREADY ASKED (DO NOT REPEAT OR ASK SIMILAR):
{chr(10).join(all_asked[-15:])}

PHRASING RULE: Do NOT start the question with the same words as recent questions.
Recent question starters to AVOID: {avoid_starters}

MAX 20 words. Just the question:"""
        try:
            resp = await self.client_manager.openai_client.chat.completions.create(model=config.OPENAI_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.8, max_tokens=50)
            question = resp.choices[0].message.content.strip().strip('"').strip("'")
            if not question.endswith('?'): question += '?'
            # Track question starter for anti-repetition
            first_words = ' '.join(question.split()[:3])
            session._recent_q_starters.append(first_words)
            if len(session._recent_q_starters) > 6: session._recent_q_starters = session._recent_q_starters[-6:]
            logger.info(f"[WI] Technical Q ({q_type}): {question[:60]}...")
            return question
        except Exception as e:
            logger.error(f"Error generating dynamic question: {e}")
            return f"Tell me more about your experience with {tech}?"

    def _get_encouragement(self):
        responses = [
            "Good explanation.", "Well explained.", "Good answer.", "Right, good.",
            "That's correct.", "Good point.", "Nice, you know this well.",
            "Okay, good.", "That makes sense.", "Good understanding.",
            "Right.", "Yes, that's correct.", "Good, I can see you understand this.",
        ]
        if not hasattr(self, '_last_enc_idx'): self._last_enc_idx = -1
        idx = random.randint(0, len(responses) - 1)
        while idx == self._last_enc_idx and len(responses) > 1:
            idx = random.randint(0, len(responses) - 1)
        self._last_enc_idx = idx
        return responses[idx]

    async def _generate_followup_from_answer(self, session, user_response, all_asked):
        await self.client_manager.initialize()
        summary = session.content_context[:500] if session.content_context else ""
        prompt = f"""The candidate answered: "{user_response[:300]}"

Their work context: {summary}

Generate ONE short follow-up question to dig deeper into what they mentioned.
ONLY ask about topics that appear in their work context above.
Ask about: Specific details, How they did it, What tools they used, Results achieved.

ALREADY ASKED (DO NOT REPEAT):
{chr(10).join(all_asked[-10:])}

MAX 15 words. Just the question:"""
        try:
            resp = await self.client_manager.openai_client.chat.completions.create(model=config.OPENAI_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.7, max_tokens=40)
            question = resp.choices[0].message.content.strip()
            if not question.endswith('?'): question += '?'
            is_duplicate = any(self._is_similar_question(question.lower(), aq.lower()) for aq in all_asked)
            if not is_duplicate: return question
        except: pass
        return None

    def _normalize_question(self, question):
        if not question: return ""
        q = question.lower().strip().rstrip('?').strip()
        stop_words = {'what', 'how', 'why', 'when', 'where', 'who', 'is', 'are', 'the', 'a', 'an', 'your', 'you', 'can', 'do', 'did', 'does', 'tell', 'me', 'about', 'describe', 'explain', 'please', 'could', 'would', 'should', 'to', 'in', 'on', 'for', 'with'}
        words = [w for w in q.split() if w not in stop_words and len(w) > 2]
        return ' '.join(sorted(words))

    async def _generate_hr_question(self, session, db_manager=None):
        if not hasattr(session, 'asked_question_hashes'):
            session.asked_question_hashes = set()
            for q in session.questions_asked: session.asked_question_hashes.add(self._normalize_question(q))
        if not hasattr(session, 'hr_category_counts'): session.hr_category_counts = {'introduction': 0, 'behavioral': 0, 'leadership': 0, 'logical_thinking': 0}
        if not hasattr(session, 'hr_questions_by_category'): session.hr_questions_by_category = {}
        CATEGORY_LIMITS = {'introduction': 2, 'behavioral': 3, 'leadership': 3, 'logical_thinking': 2}
        if not session.previously_asked_hr_questions and db_manager:
            try:
                session.previously_asked_hr_questions = await db_manager.get_hr_questions_asked(session.student_id, limit=200)
                logger.info(f"[HR] Loaded {len(session.previously_asked_hr_questions)} previously asked HR questions")
                for q in session.previously_asked_hr_questions: session.asked_question_hashes.add(self._normalize_question(q))
            except Exception as e:
                logger.warning(f"[HR] Could not load previous HR questions: {e}"); session.previously_asked_hr_questions = []
        if not session.hr_questions_by_category:
            if db_manager:
                try: await self._load_hr_questions_by_category(session, db_manager)
                except Exception as e: logger.warning(f"[HR] Could not load from MongoDB: {e}")
            if not session.hr_questions_by_category:
                logger.warning("[HR] Using fallback questions")
                session.hr_questions_by_category = {'introduction': GENERIC_TECHNICAL_QUESTIONS[:5], 'behavioral': HR_QUESTIONS_POOL[:5], 'leadership': HR_QUESTIONS_POOL[5:10], 'logical_thinking': HR_QUESTIONS_POOL[10:15]}
        total_hr_asked = sum(session.hr_category_counts.values())
        logger.info(f"[HR] Total HR questions asked so far: {total_hr_asked}")
        logger.info(f"[HR] Category counts: {session.hr_category_counts}")
        target_category = None
        category_order = ['introduction', 'behavioral', 'leadership', 'logical_thinking']
        for category in category_order:
            if session.hr_category_counts[category] < CATEGORY_LIMITS[category]: target_category = category; break
        if target_category is None:
            logger.info("[HR] All category limits reached - HR round complete")
            return "Thank you! That concludes our HR round. You did great!", ["hr_complete"]
        logger.info(f"[HR] Asking from category: {target_category} (current: {session.hr_category_counts[target_category]}/{CATEGORY_LIMITS[target_category]})")
        category_questions = session.hr_questions_by_category.get(target_category, [])
        if not category_questions:
            logger.warning(f"[HR] No questions available for category: {target_category}")
            for fallback_cat in category_order:
                if fallback_cat != target_category and session.hr_questions_by_category.get(fallback_cat):
                    category_questions = session.hr_questions_by_category[fallback_cat]; target_category = fallback_cat; break
        all_asked = set(session.used_hr_questions) | set(session.previously_asked_hr_questions)
        selected_question = None
        shuffled = category_questions.copy(); random.shuffle(shuffled)
        for question in shuffled:
            q_normalized = self._normalize_question(question)
            if q_normalized not in session.asked_question_hashes:
                is_similar = False
                for asked_q in all_asked:
                    if self._is_similar_question(question.lower(), asked_q.lower()): is_similar = True; break
                if not is_similar: selected_question = question; break
        if not selected_question and category_questions:
            selected_question = random.choice(category_questions); logger.warning(f"[HR] All questions in {target_category} used, selecting random")
        if not selected_question:
            fallback_questions = {'introduction': "What motivated you to choose your career path?", 'behavioral': "Tell me about a challenging situation you faced at work.", 'leadership': "Describe a time when you took initiative on a project.", 'logical_thinking': "How do you approach solving complex problems?"}
            selected_question = fallback_questions.get(target_category, "What are your career goals?")
        session.asked_question_hashes.add(self._normalize_question(selected_question))
        session.used_hr_questions.append(selected_question)
        session.hr_category_counts[target_category] += 1
        if db_manager:
            try: await db_manager.store_hr_question_asked(student_id=session.student_id, question=selected_question, session_id=session.session_id)
            except Exception as e: logger.warning(f"[HR] Could not store question: {e}")
        logger.info(f"[HR] Selected [{target_category.upper()}] ({session.hr_category_counts[target_category]}/{CATEGORY_LIMITS[target_category]}): {selected_question[:60]}...")
        return selected_question, ["hr", target_category]

    async def _load_hr_questions_by_category(self, session, db_manager):
        try:
            from pymongo import MongoClient
            client = MongoClient(config.mongodb_connection_string, serverSelectionTimeoutMS=5000)
            db = client["ml_notes"]; collection = db["HR&Managerial_Interview_Questions"]
            logger.info("[HR] Loading questions from MongoDB by category...")
            doc = collection.find_one({"candidate_type": "fresher"})
            if not doc: logger.warning("[HR] No 'fresher' document found, trying any document"); doc = collection.find_one({})
            if not doc: logger.error("[HR] Collection is empty!"); client.close(); return
            session.hr_questions_by_category = {'introduction': [], 'behavioral': [], 'leadership': [], 'logical_thinking': []}
            for category in ['introduction', 'behavioral', 'leadership', 'logical_thinking']:
                if category in doc and isinstance(doc[category], dict):
                    category_data = doc[category]
                    if "questions" in category_data and isinstance(category_data["questions"], list):
                        questions = []
                        for q_obj in category_data["questions"]:
                            if isinstance(q_obj, dict) and "text" in q_obj:
                                q_text = str(q_obj["text"]).strip()
                                if len(q_text) > 10: questions.append(q_text)
                        session.hr_questions_by_category[category] = questions
                        logger.info(f"[HR] Loaded {len(questions)} questions from '{category}'")
                else: logger.warning(f"[HR] Category '{category}' not found in document")
            client.close()
            total = sum(len(qs) for qs in session.hr_questions_by_category.values())
            logger.info(f"[HR] Total questions loaded: {total}")
        except Exception as e:
            logger.error(f"[HR] Error loading questions by category: {e}")
            import traceback; traceback.print_exc(); raise
        
    async def _generate_smart_followup(self, session, user_response, current_stage):
        await self.client_manager.initialize()
        prompt = f"""User said: "{user_response[:80]}"\nGenerate a short follow-up question. MAX 12 words."""
        resp = await self.client_manager.openai_client.chat.completions.create(model=config.OPENAI_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.7, max_tokens=30)
        q = resp.choices[0].message.content.strip()
        return q if '?' in q else q + "?"

    async def generate_first_question(self, session): return await self.generate_introduction(session)

    async def generate_introduction(self, session):
        return f"""Hello {session.student_name}! Welcome to your weekly interview session. I'm excited to chat with you today!\n\nWe'll have three rounds:\n• First, a Communication round (about 5 minutes) where we'll have a casual conversation and get to know each other.\n• Then, a Technical round (about 25 minutes) where we'll discuss your recent work and technical knowledge.\n• Finally, an HR round (about 10 minutes) with some behavioral questions.\n\nSo, how are you doing today? Ready to get started?"""

    async def generate_silence_response(self, session):
        # Increment here — this is the single source of truth for silence counting
        session.silence_prompt_count += 1
        count = session.silence_prompt_count
        
        # Progressive responses — get more helpful as silence continues
        if count == 1:
            responses = [
                "No rush, just think about it and let me know.",
                "Take your time, I'm listening.",
                "It's okay, think it through and answer when ready.",
                "No pressure at all, just share your thoughts whenever you're ready.",
                "Take a moment to think, I'll wait.",
            ]
        elif count == 2:
            responses = [
                "Are you ready? I can repeat the question if that helps.",
                "Still thinking? That's totally fine. Want me to repeat it?",
                "Can I help? I can rephrase the question if you'd like.",
                "Should I move on to a different question, or would you like more time?",
                "No worries! Want me to repeat, or shall we try a different one?",
            ]
        else:
            responses = [
                "Let me try a different question, no problem at all.",
                "That's okay, let's move on to something else.",
                "No worries, I'll ask you something different.",
            ]
        
        if not hasattr(session, '_last_silence_idx'): session._last_silence_idx = -1
        idx = random.randint(0, len(responses) - 1)
        while idx == session._last_silence_idx and len(responses) > 1:
            idx = random.randint(0, len(responses) - 1)
        session._last_silence_idx = idx
        return responses[idx]

    async def generate_fast_response(self, session, user_response, db_manager=None):
        await self.client_manager.initialize()
        
        # ── ECHO DETECTION: If user "response" is just the AI's question echoed back ──
        # Speaker echo → Whisper transcribes AI's own words → comes back as user response
        if user_response and session.exchanges:
            last_ai_msg = session.exchanges[-1].ai_message.lower()
            user_lower = user_response.lower().strip()
            # Check word overlap between user response and last AI message
            user_words = set(user_lower.split())
            ai_words = set(last_ai_msg.split())
            if len(user_words) >= 3 and len(ai_words) >= 3:
                overlap = len(user_words & ai_words)
                overlap_ratio = overlap / max(len(user_words), 1)
                if overlap_ratio >= 0.85:  # FIX: Was 0.6 — caught legitimate answers restating question premises
                    logger.info(f"[WI] ECHO DETECTED: user response has {overlap_ratio:.0%} word overlap with last AI message — treating as silence")
                    user_response = ""  # Treat as silence
            # Also check if user response is a substring of AI message (partial echo)
            if len(user_lower) >= 15 and user_lower in last_ai_msg:
                logger.info(f"[WI] ECHO DETECTED: user response is substring of last AI message — treating as silence")
                user_response = ""
        
        quality = self._assess_answer_quality(user_response, stage=session.current_stage, session=session)
        logger.info(f"[WI] Quality: {quality}, Stage: {session.current_stage.value}")
        if quality != "silence": session.silence_prompt_count = 0
        # Track consecutive no-response streak (silence/gibberish = no real answer)
        if quality in ("silence", "gibberish"):
            session.consecutive_no_response += 1
            logger.info(f"[WI] Consecutive no-response: {session.consecutive_no_response}/{MAX_CONSECUTIVE_SILENCE}")
        elif quality not in ("repeat",):
            # For TECHNICAL and HR stages: defer counter reset until accuracy is evaluated.
            # This prevents garbage transcripts (quality="neutral" but 0% accuracy) from
            # resetting the silence streak. The counter will be managed after accuracy check.
            if session.current_stage not in (WI_InterviewStage.TECHNICAL, WI_InterviewStage.HR):
                session.consecutive_no_response = 0  # Real answer resets the streak
        session.conversation_state.last_user_response = user_response
        mentioned_tech = self._extract_topics_from_response(user_response, session)
        session.conversation_state.user_mentioned_tech.extend(mentioned_tech)

        # ── FIX 2: Pure question on repeat — no prefix, no add_exchange ──
        if quality == "repeat":
            if session.exchanges:
                # Priority 1: Session-level question (survives round transitions)
                if session._last_real_question:
                    original_question = session._last_real_question
                # Priority 2: Conversation state question (current round)
                elif session.conversation_state.last_pure_question: 
                    original_question = session.conversation_state.last_pure_question
                # Priority 3: Extract from last exchange
                else:
                    last_ai_msg = session.exchanges[-1].ai_message
                    original_question = self._extract_question_from_response(last_ai_msg)
                session.last_was_repeat = True
                # Return ONLY the pure question — no "Of course!" prefix
                # main.py will skip add_exchange so question number stays same
                logger.info(f"[WI] REPEAT detected - repeating ONLY question: {original_question[:80]}...")
                return original_question
            return "Let me start with a question!"

        session.last_was_repeat = False
        logger.info(f"[WI] Normal response - last_was_repeat=False")
        if session.current_stage == WI_InterviewStage.INTRODUCTION:
            session.introduction_completed = True
            session.start_round(WI_InterviewStage.COMMUNICATION)
            q = await self._generate_communication_question(session, True)
            return f"Great to hear! Let's get to know you. {q}"
        elapsed = session.get_round_elapsed_minutes()
        logger.info(f"[WI] Stage: {session.current_stage.value}, Elapsed: {elapsed:.2f} min")
        if session.current_stage == WI_InterviewStage.COMMUNICATION:
            if elapsed >= 5 or session.consecutive_no_response >= MAX_CONSECUTIVE_SILENCE:
                logger.info(f"[WI] TRANSITIONING: Communication -> Technical (elapsed={elapsed:.1f}min, silence_streak={session.consecutive_no_response})")
                session.start_round(WI_InterviewStage.TECHNICAL)
                q, keywords = await self._generate_technical_question(session)
                session.add_exchange(q, expected_keywords=keywords, question_type="technical_behavioral" if "technical_behavioral" in keywords else "technical")
                return f"Nice chatting! Now let's discuss your technical work. {q}"
        elif session.current_stage == WI_InterviewStage.TECHNICAL:
            if elapsed >= 25 or session.consecutive_no_response >= MAX_CONSECUTIVE_SILENCE:
                logger.info(f"[WI] TRANSITIONING: Technical -> HR (elapsed={elapsed:.1f}min, silence_streak={session.consecutive_no_response})")
                session.start_round(WI_InterviewStage.HR)
                q, keywords = await self._generate_hr_question(session, db_manager)
                session.add_exchange(q, expected_keywords=keywords, question_type="hr")
                return f"Great technical discussion! Now some behavioral questions. {q}"
        elif session.current_stage == WI_InterviewStage.HR:
            if elapsed >= 10 or session.consecutive_no_response >= MAX_CONSECUTIVE_SILENCE:
                logger.info(f"[WI] TRANSITIONING: HR -> Complete (elapsed={elapsed:.1f}min, silence_streak={session.consecutive_no_response})")
                session.current_stage = WI_InterviewStage.COMPLETE
                return "Thank you! Great interview. Let me generate your detailed feedback..."
        if session.current_stage == WI_InterviewStage.COMMUNICATION:
            if quality == "skip":
                q = await self._generate_communication_question(session); session.add_exchange(q, question_type="communication"); ack = await self._generate_dynamic_ack("skip", "transition"); return f"{ack} {q}"
            if quality == "silence": return await self.generate_silence_response(session)
            if quality == "gibberish": return "I'm sorry, I didn't catch that clearly. Could you please repeat your answer?"
            if quality == "cant_answer":
                q = await self._generate_communication_question(session); session.add_exchange(q, question_type="communication"); ack = await self._generate_dynamic_ack("cant answer", "cant_answer"); return f"{ack} {q}"
            if quality == "weak":
                q = await self._generate_communication_question(session); session.add_exchange(q, question_type="communication"); ack = await self._generate_dynamic_ack("weak response", "weak"); return f"{ack} {q}"
            if self._should_followup(session, quality):
                session.conversation_state.followups_on_topic += 1; q = await self._generate_communication_followup(session, user_response); session.add_exchange(q, question_type="communication", is_followup=True); ack = await self._generate_dynamic_ack("good response", "good"); return f"{ack} {q}"
            q = await self._generate_communication_question(session); session.add_exchange(q, question_type="communication"); session.conversation_state.followups_on_topic = 0; ack = await self._generate_dynamic_ack("transition", "transition"); return f"{ack} {q}"
        if session.current_stage == WI_InterviewStage.TECHNICAL:
            accuracy = 0.0
            accuracy_evaluated = False
            if session.exchanges and session.exchanges[-1].question_type == "technical":
                last_ex = session.exchanges[-1]
                accuracy = await self._evaluate_technical_accuracy(session, last_ex.ai_message, user_response, last_ex.expected_keywords)
                session.update_last_response(user_response, 0.8, quality, accuracy)
                logger.info(f"[WI] Technical accuracy: {accuracy:.2f} for quality: {quality}")
                accuracy_evaluated = True
            
            # ===== Counter management for technical round =====
            # Only runs for non-silence/gibberish/repeat responses (those are handled above)
            if quality not in ("silence", "gibberish", "skip", "cant_answer", "repeat"):
                if accuracy_evaluated and accuracy > 0.0:
                    session.consecutive_no_response = 0  # Real technical answer
                elif accuracy_evaluated and accuracy == 0.0:
                    session.consecutive_no_response += 1  # Garbage with 0% accuracy
                    logger.info(f"[WI] Zero-accuracy response — no-response streak: {session.consecutive_no_response}/{MAX_CONSECUTIVE_SILENCE}")
                elif not accuracy_evaluated:
                    # Behavioral question in technical round — quality-based check is sufficient
                    session.consecutive_no_response = 0
            self._adjust_difficulty(session, quality)
            if quality == "skip":
                q, keywords = await self._generate_technical_question(session, "", True); session.add_exchange(q, expected_keywords=keywords, question_type="technical_behavioral" if "technical_behavioral" in keywords else "technical"); ack = await self._generate_dynamic_ack("skip", "transition"); return f"{ack} {q}"
            if quality == "gibberish": return "I'm sorry, I didn't catch that clearly. Could you please repeat your answer?"
            if quality == "off_topic":
                logger.info(f"[WI] OFF-TOPIC detected in Technical round")
                if session.exchanges:
                    last_q = session.exchanges[-1].ai_message.lower()
                    for tech in (session.extracted_technologies or []):
                        if tech.lower() in last_q and tech not in session.silent_topics:
                            session.topic_attempt_count[tech] = session.topic_attempt_count.get(tech, 0) + 1
                            if session.topic_attempt_count[tech] >= 2: session.silent_topics.append(tech)
                            break
                session.current_difficulty = "easy"
                q, keywords = await self._generate_technical_question(session, "", True)
                session.add_exchange(q, expected_keywords=keywords, question_type="technical", answer_quality="off_topic")
                ack = self._get_off_topic_response(session=session, stage=WI_InterviewStage.TECHNICAL)
                return f"{ack} {q}"
            if quality == "silence":
                if session.exchanges:
                    last_q = session.exchanges[-1].ai_message.lower()
                    for tech in session.extracted_technologies:
                        if tech.lower() in last_q: session.topic_attempt_count[tech] = session.topic_attempt_count.get(tech, 0) + 1; (session.silent_topics.append(tech) if session.topic_attempt_count[tech] >= 2 and tech not in session.silent_topics else None); break
                # Check BEFORE incrementing — generate_silence_response will increment
                # Technical needs more patience (3 prompts ≈ 30s thinking time)
                if session.silence_prompt_count >= 3:
                    session.silence_prompt_count = 0; q, keywords = await self._generate_technical_question(session, "", True); session.add_exchange(q, expected_keywords=keywords, question_type="technical_behavioral" if "technical_behavioral" in keywords else "technical"); return f"Let's try something different. {q}"
                return await self.generate_silence_response(session)
            if quality == "cant_answer":
                if session.exchanges:
                    last_q = session.exchanges[-1].ai_message.lower()
                    for tech in session.extracted_technologies:
                        if tech.lower() in last_q: session.topic_attempt_count[tech] = session.topic_attempt_count.get(tech, 0) + 1; (session.silent_topics.append(tech) if session.topic_attempt_count[tech] >= 2 and tech not in session.silent_topics else None); break
                session.current_difficulty = "easy"; q, keywords = await self._generate_technical_question(session, "", True); session.add_exchange(q, expected_keywords=keywords, question_type="technical_behavioral" if "technical_behavioral" in keywords else "technical"); ack = await self._generate_dynamic_ack("cant answer technical", "cant_answer"); return f"{ack} {q}"
            # Reset off-topic counter on any on-topic answer
            self._reset_off_topic_counter()
            if accuracy >= 0.7:
                if random.random() < 0.3:
                    q = await self._generate_smart_followup(session, user_response, WI_InterviewStage.TECHNICAL)
                    session.add_exchange(q, question_type="technical", is_followup=True)
                    ack = self._get_encouragement()
                    return f"{ack} {q}"
                q, keywords = await self._generate_technical_question(session, user_response, True)
                session.add_exchange(q, expected_keywords=keywords, question_type="technical_behavioral" if "technical_behavioral" in keywords else "technical")
                ack = self._get_encouragement()
                return f"{ack} {q}"
            elif accuracy >= 0.4:
                q, keywords = await self._generate_technical_question(session, user_response, True)
                session.add_exchange(q, expected_keywords=keywords, question_type="technical_behavioral" if "technical_behavioral" in keywords else "technical")
                ack = await self._generate_dynamic_ack("partial technical", "transition")
                return f"{ack} {q}"
            else:
                if session.exchanges:
                    last_q = session.exchanges[-1].ai_message.lower()
                    for tech in (session.extracted_technologies or []):
                        if tech.lower() in last_q and tech not in session.silent_topics:
                            session.topic_attempt_count[tech] = session.topic_attempt_count.get(tech, 0) + 1
                            if session.topic_attempt_count[tech] >= 2:
                                session.silent_topics.append(tech)
                            break
                session.current_difficulty = "easy"
                q, keywords = await self._generate_technical_question(session, "", True)
                session.add_exchange(q, expected_keywords=keywords, question_type="technical_behavioral" if "technical_behavioral" in keywords else "technical")
                ack = self._get_off_topic_response(session=session, stage=WI_InterviewStage.TECHNICAL)
                return f"{ack} {q}"
        if session.current_stage == WI_InterviewStage.HR:
            # ===== FIX: End HR round immediately when all categories exhausted =====
            # Don't wait for 10-minute timer if we've asked all planned questions
            if hasattr(session, 'hr_category_counts'):
                HR_CATEGORY_LIMITS = {'introduction': 2, 'behavioral': 3, 'leadership': 3, 'logical_thinking': 2}
                all_categories_done = all(
                    session.hr_category_counts.get(cat, 0) >= limit 
                    for cat, limit in HR_CATEGORY_LIMITS.items()
                )
                if all_categories_done:
                    logger.info(f"[WI] All HR categories exhausted — ending HR round early at {elapsed:.1f} min")
                    session.current_stage = WI_InterviewStage.COMPLETE
                    return "Thank you! Great interview. Let me generate your detailed feedback..."
            
            accuracy = 0.0
            accuracy_evaluated = False
            if session.exchanges and session.exchanges[-1].question_type == "hr":
                last_ex = session.exchanges[-1]
                accuracy = await self._evaluate_technical_accuracy(session, last_ex.ai_message, user_response, last_ex.expected_keywords)
                session.update_last_response(user_response, 0.8, quality, accuracy)
                logger.info(f"[WI] HR accuracy: {accuracy:.2f} for quality: {quality}")
                accuracy_evaluated = True
            
            # ===== Counter management for HR round =====
            if quality not in ("silence", "gibberish", "skip", "cant_answer", "repeat"):
                if accuracy_evaluated and accuracy > 0.0:
                    session.consecutive_no_response = 0
                elif accuracy_evaluated and accuracy == 0.0:
                    session.consecutive_no_response += 1
                    logger.info(f"[WI] Zero-accuracy HR response — no-response streak: {session.consecutive_no_response}/{MAX_CONSECUTIVE_SILENCE}")
                elif not accuracy_evaluated:
                    session.consecutive_no_response = 0
            if quality == "skip":
                q, keywords = await self._generate_hr_question(session, db_manager); session.add_exchange(q, expected_keywords=keywords, question_type="hr"); ack = await self._generate_dynamic_ack("skip", "transition"); return f"{ack} {q}"
            if quality == "gibberish": return "I'm sorry, I didn't catch that clearly. Could you please repeat your answer?"
            if quality == "off_topic":
                logger.info(f"[WI] OFF-TOPIC detected in HR round")
                q, keywords = await self._generate_hr_question(session, db_manager)
                session.add_exchange(q, expected_keywords=keywords, question_type="hr", answer_quality="off_topic")
                ack = self._get_off_topic_response(session=session, stage=WI_InterviewStage.HR)
                return f"{ack} {q}"
            if quality == "silence":
                # Check BEFORE incrementing — generate_silence_response will increment
                if session.silence_prompt_count >= 2:
                    session.silence_prompt_count = 0; q, keywords = await self._generate_hr_question(session, db_manager); session.add_exchange(q, expected_keywords=keywords, question_type="hr"); return f"Let's try a different question. {q}"
                return await self.generate_silence_response(session)
            if quality == "cant_answer":
                q, keywords = await self._generate_hr_question(session, db_manager); session.add_exchange(q, expected_keywords=keywords, question_type="hr"); ack = await self._generate_dynamic_ack("cant answer hr", "cant_answer"); return f"{ack} {q}"
            # Reset off-topic counter on any on-topic answer
            self._reset_off_topic_counter()
            if accuracy >= 0.7:
                if random.random() < 0.25:
                    q = await self._generate_smart_followup(session, user_response, WI_InterviewStage.HR)
                    session.add_exchange(q, question_type="hr", is_followup=True)
                    ack = self._get_encouragement()
                    return f"{ack} {q}"
                q, keywords = await self._generate_hr_question(session, db_manager)
                session.add_exchange(q, expected_keywords=keywords, question_type="hr")
                ack = self._get_encouragement()
                return f"{ack} {q}"
            elif accuracy >= 0.4:
                q, keywords = await self._generate_hr_question(session, db_manager)
                session.add_exchange(q, expected_keywords=keywords, question_type="hr")
                ack = await self._generate_dynamic_ack("partial hr", "transition")
                return f"{ack} {q}"
            else:
                q, keywords = await self._generate_hr_question(session, db_manager)
                session.add_exchange(q, expected_keywords=keywords, question_type="hr")
                ack = self._get_off_topic_response(session=session, stage=WI_InterviewStage.HR)
                return f"{ack} {q}"
        return "That's interesting. Tell me more?"

    async def generate_fast_evaluation(self, session) -> Tuple[str, Dict[str, float]]:
        await self.client_manager.initialize()
        comm_exchanges = []; tech_exchanges = []; hr_exchanges = []; tech_accuracies = []; hr_accuracies = []
        for ex in session.exchanges:
            if ex.answer_quality in ["silence", "gibberish"] and not ex.user_response:
                continue
            exchange_data = {"question": ex.ai_message, "answer": ex.user_response if ex.user_response else "[SILENT - No response]", "is_silent": not ex.user_response or ex.answer_quality == "silence", "answer_quality": ex.answer_quality, "accuracy": ex.technical_accuracy}
            if ex.stage == WI_InterviewStage.COMMUNICATION: comm_exchanges.append(exchange_data)
            elif ex.stage == WI_InterviewStage.TECHNICAL:
                exchange_data["is_behavioral_in_tech"] = (ex.question_type == "technical_behavioral")
                tech_exchanges.append(exchange_data); (tech_accuracies.append(ex.technical_accuracy) if ex.technical_accuracy is not None else None)
            elif ex.stage == WI_InterviewStage.HR: hr_exchanges.append(exchange_data); (hr_accuracies.append(ex.technical_accuracy) if ex.technical_accuracy is not None else None)
        tech_accuracy_avg = sum(tech_accuracies) / len(tech_accuracies) if tech_accuracies else 0.5
        hr_accuracy_avg = sum(hr_accuracies) / len(hr_accuracies) if hr_accuracies else 0.5
        total_technical_qs = len(tech_exchanges); total_hr_qs = len(hr_exchanges); total_comm_qs = len(comm_exchanges)
        async def get_batch_feedback(exchanges, round_type):
            """Get feedback for ALL exchanges in one API call instead of one per question."""
            if not exchanges:
                return []
            qa_text = ""
            for i, ex in enumerate(exchanges, 1):
                if ex["is_silent"]:
                    qa_text += f"\nQ{i}: {ex['question']}\nA{i}: [SILENT - No response]\n"
                else:
                    qa_text += f"\nQ{i}: {ex['question']}\nA{i}: {ex['answer'][:200]}\n"
            prompt = f"""Give brief feedback (1 sentence each) for these {round_type} interview answers.
Reply in format:
Q1: feedback here
Q2: feedback here
...

{qa_text}

For silent responses, say "No response given. Try to attempt even partial answers."
Be constructive. If good, praise briefly. If weak, suggest improvement."""
            try:
                resp = await self.client_manager.openai_client.chat.completions.create(
                    model=config.OPENAI_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3, max_tokens=len(exchanges) * 60
                )
                result_text = resp.choices[0].message.content.strip()
                feedbacks = []
                lines = result_text.split('\n')
                current_fb = ""
                for line in lines:
                    line = line.strip()
                    if re.match(r'^Q\d+:', line):
                        if current_fb:
                            feedbacks.append(current_fb)
                        current_fb = re.sub(r'^Q\d+:\s*', '', line)
                    elif line and current_fb:
                        current_fb += " " + line
                if current_fb:
                    feedbacks.append(current_fb)
                # Pad if fewer feedbacks parsed than exchanges
                while len(feedbacks) < len(exchanges):
                    feedbacks.append("Response recorded.")
                return feedbacks[:len(exchanges)]
            except Exception as e:
                logger.error(f"[WI] Batch feedback error: {e}")
                return ["Response recorded." for _ in exchanges]

        evaluation_parts = []
        
        # Get feedback in batches (1 API call per round instead of 1 per question)
        if comm_exchanges:
            comm_feedbacks = await get_batch_feedback(comm_exchanges, "communication")
            evaluation_parts.append("=" * 60); evaluation_parts.append("COMMUNICATION ROUND FEEDBACK"); evaluation_parts.append("=" * 60)
            for i, (ex, feedback) in enumerate(zip(comm_exchanges, comm_feedbacks), 1):
                evaluation_parts.append(f"\nQ{i}. AI Question: {ex['question']}"); evaluation_parts.append(f"    User Answer: {ex['answer']}"); evaluation_parts.append(f"    Feedback: {feedback}"); evaluation_parts.append("-" * 40)
        if tech_exchanges:
            # Split pure technical from behavioral-in-technical
            pure_tech_exchanges = [ex for ex in tech_exchanges if not ex.get("is_behavioral_in_tech", False)]
            behavioral_tech_exchanges = [ex for ex in tech_exchanges if ex.get("is_behavioral_in_tech", False)]
            
            if pure_tech_exchanges:
                pure_tech_feedbacks = await get_batch_feedback(pure_tech_exchanges, "technical")
                evaluation_parts.append("\n" + "=" * 60); evaluation_parts.append(f"TECHNICAL ROUND FEEDBACK ({len(pure_tech_exchanges)} questions)"); evaluation_parts.append("=" * 60)
                for i, (ex, feedback) in enumerate(zip(pure_tech_exchanges, pure_tech_feedbacks), 1):
                    accuracy_str = f" (Accuracy: {ex['accuracy']:.0%})" if ex["accuracy"] is not None else ""
                    evaluation_parts.append(f"\nQ{i}. AI Question: {ex['question']}"); evaluation_parts.append(f"    User Answer: {ex['answer']}"); evaluation_parts.append(f"    Feedback: {feedback}{accuracy_str}"); evaluation_parts.append("-" * 40)
            
            if behavioral_tech_exchanges:
                beh_feedbacks = await get_batch_feedback(behavioral_tech_exchanges, "technical behavioral")
                evaluation_parts.append("\n" + "=" * 60); evaluation_parts.append(f"TECHNICAL BEHAVIORAL QUESTIONS ({len(behavioral_tech_exchanges)} questions)"); evaluation_parts.append("=" * 60)
                for i, (ex, feedback) in enumerate(zip(behavioral_tech_exchanges, beh_feedbacks), 1):
                    accuracy_str = f" (Accuracy: {ex['accuracy']:.0%})" if ex["accuracy"] is not None else ""
                    evaluation_parts.append(f"\nQ{i}. AI Question: {ex['question']}"); evaluation_parts.append(f"    User Answer: {ex['answer']}"); evaluation_parts.append(f"    Feedback: {feedback}{accuracy_str}"); evaluation_parts.append("-" * 40)
        if hr_exchanges:
            hr_feedbacks = await get_batch_feedback(hr_exchanges, "HR/behavioral")
            evaluation_parts.append("\n" + "=" * 60); evaluation_parts.append("HR/BEHAVIORAL ROUND FEEDBACK"); evaluation_parts.append("=" * 60)
            for i, (ex, feedback) in enumerate(zip(hr_exchanges, hr_feedbacks), 1):
                evaluation_parts.append(f"\nQ{i}. AI Question: {ex['question']}"); evaluation_parts.append(f"    User Answer: {ex['answer']}"); evaluation_parts.append(f"    Feedback: {feedback}"); evaluation_parts.append("-" * 40)
        evaluation_parts.append("\n" + "=" * 60); evaluation_parts.append("OVERALL SUMMARY"); evaluation_parts.append("=" * 60)
        silent_count = sum(1 for ex in comm_exchanges + tech_exchanges + hr_exchanges if ex["is_silent"])
        pure_tech_count = sum(1 for ex in tech_exchanges if not ex.get("is_behavioral_in_tech", False))
        behavioral_in_tech_count = len(tech_exchanges) - pure_tech_count
        summary_prompt = f"""Provide a brief overall interview summary (4-5 sentences) for {session.student_name}.\n\nMETRICS:\n- Communication Questions: {total_comm_qs}\n- Technical Questions: {pure_tech_count}\n- Technical Behavioral Questions: {behavioral_in_tech_count}\n- Technical Accuracy: {tech_accuracy_avg:.0%}\n- HR Questions: {total_hr_qs}\n- Correct Answers: {session.correct_answers}\n- Partial Answers: {session.partial_answers}\n- Weak Answers: {session.wrong_answers}\n- Silent/No Response: {silent_count}\n\nInclude: Overall performance, Key strengths (2-3), Areas to improve (2-3), Final recommendation"""
        summary_resp = await self.client_manager.openai_client.chat.completions.create(model=config.OPENAI_MODEL, messages=[{"role": "user", "content": summary_prompt}], temperature=0.3, max_tokens=400)
        overall_summary = summary_resp.choices[0].message.content.strip()
        evaluation_parts.append(f"\n{overall_summary}")
        evaluation_parts.append("\n" + "-" * 40); evaluation_parts.append("STATISTICS:")
        evaluation_parts.append(f"  Total Questions: {total_comm_qs + total_technical_qs + total_hr_qs}")
        evaluation_parts.append(f"  Technical Questions: {pure_tech_count} (+ {behavioral_in_tech_count} behavioral)")
        evaluation_parts.append(f"  Technical Accuracy: {tech_accuracy_avg:.0%}")
        evaluation_parts.append(f"  Questions Answered Well: {session.correct_answers}")
        evaluation_parts.append(f"  Partial Answers: {session.partial_answers}")
        evaluation_parts.append(f"  Needs Improvement: {session.wrong_answers}")
        evaluation_parts.append(f"  Silent Responses: {silent_count}")
        evaluation = "\n".join(evaluation_parts)
        score_prompt = f"""Score this interview candidate on a scale of 0-10 for each criteria.

ACTUAL PERFORMANCE METRICS (use these to determine scores):
- Technical Accuracy: {tech_accuracy_avg:.0%}
- Correct Answers: {session.correct_answers}
- Partial Answers: {session.partial_answers}
- Wrong/Weak Answers: {session.wrong_answers}
- Silent/No Response: {silent_count}
- Total Questions: {total_comm_qs + total_technical_qs + total_hr_qs}
- Communication Questions: {total_comm_qs}
- Technical Questions: {pure_tech_count}
- Technical Behavioral Questions: {behavioral_in_tech_count}
- HR Questions: {total_hr_qs}

STRICT SCORING RULES:
- If Technical Accuracy is below 20%, technical score MUST be 2 or below
- If Technical Accuracy is below 50%, technical score MUST be 4 or below
- If Correct Answers is 0, technical score MUST be 1 or 2
- If Wrong Answers > 10, overall scores should be LOW (1-4 range)
- If most responses were incoherent or gibberish, confidence and communication MUST be 3 or below
- Do NOT give generous scores. Be honest and accurate based on the metrics above.

Reply in EXACT format (just the scores, nothing else):
communication: X
technical: X
leadership: X
behaviour: X
confidence: X"""
        sc_resp = await self.client_manager.openai_client.chat.completions.create(model=config.OPENAI_MODEL, messages=[{"role": "user", "content": score_prompt}], temperature=0.1, max_tokens=200)
        score_text = sc_resp.choices[0].message.content.lower()
        scores = {}
        for key in ["communication", "technical", "leadership", "behaviour", "confidence"]:
            m = re.search(rf"{key}[:\s]*(\d+\.?\d*)", score_text)
            if m: scores[f"{key}_score"] = min(float(m.group(1)), 10.0)
            else:
                if key == "technical": scores[f"{key}_score"] = round(tech_accuracy_avg * 10, 1)
                else: scores[f"{key}_score"] = 5.0
        tech_cap = tech_accuracy_avg * 10
        if tech_cap < 2.0: tech_cap = max(tech_cap, 1.0)
        if scores.get("technical_score", 0) > tech_cap + 1.5:
            logger.info(f"[WI] Capping technical score from {scores['technical_score']} to {round(tech_cap + 1.0, 1)} (accuracy={tech_accuracy_avg:.0%})")
            scores["technical_score"] = round(tech_cap + 1.0, 1)
        if session.correct_answers == 0 and session.wrong_answers > 5:
            for key in ["communication", "technical", "leadership", "behaviour", "confidence"]:
                score_key = f"{key}_score"
                if scores.get(score_key, 0) > 4.0:
                    logger.info(f"[WI] Capping {key} from {scores[score_key]} to 4.0 (0 correct, {session.wrong_answers} wrong)")
                    scores[score_key] = min(scores[score_key], 4.0)
        gibberish_ratio = silent_count / max(total_comm_qs + total_technical_qs + total_hr_qs, 1)
        wrong_ratio = session.wrong_answers / max(total_comm_qs + total_technical_qs + total_hr_qs, 1)
        if wrong_ratio > 0.6 or gibberish_ratio > 0.4:
            for key in ["communication", "confidence"]:
                score_key = f"{key}_score"
                if scores.get(score_key, 0) > 3.0:
                    scores[score_key] = min(scores[score_key], 3.0)
        scores["technical_accuracy"] = round(tech_accuracy_avg * 100, 1)
        scores["hr_accuracy"] = round(hr_accuracy_avg * 100, 1)
        scores["questions_correct"] = session.correct_answers
        scores["questions_partial"] = session.partial_answers
        scores["questions_wrong"] = session.wrong_answers
        scores["questions_silent"] = silent_count
        scores["total_questions"] = total_technical_qs + total_hr_qs + total_comm_qs
        scores["communication_questions"] = total_comm_qs
        scores["technical_questions"] = pure_tech_count
        scores["behavioral_in_technical_questions"] = behavioral_in_tech_count
        scores["technical_questions_total"] = total_technical_qs
        scores["hr_questions"] = total_hr_qs
        w = {"communication_weight": 0.20, "technical_weight": 0.30, "leadership_weight": 0.15, "behaviour_weight": 0.20, "confidence_weight": 0.15}
        scores["weighted_overall"] = round(scores.get("communication_score", 5) * w.get("communication_weight", 0.2) + scores.get("technical_score", 5) * w.get("technical_weight", 0.3) + scores.get("leadership_score", 5) * w.get("leadership_weight", 0.15) + scores.get("behaviour_score", 5) * w.get("behaviour_weight", 0.2) + scores.get("confidence_score", 5) * w.get("confidence_weight", 0.15), 1)
        logger.info(f"[WI] Evaluation complete - Overall: {scores['weighted_overall']}/10, Tech Accuracy: {scores['technical_accuracy']}%")
        return evaluation, scores


# =============================================================================
# WEEKEND MOCK TEST
# =============================================================================

class AIService:
    def __init__(self):
        self.client = Groq(api_key=config.GROQ_API_KEY, timeout=60)
    def generate_questions_batch(self, user_type, context):
        prompt = PromptTemplates.create_batch_questions_prompt(user_type, context, 10)
        resp = self.client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}], temperature=0.7, max_completion_tokens=3000)
        return [{"question_number": i, "question": q} for i, q in enumerate(resp.choices[0].message.content.split("\n") if resp.choices else [], 1)]
    def evaluate_test_batch(self, user_type, qa_pairs):
        return {"scores": [1] * len(qa_pairs), "total_correct": len(qa_pairs)}

_ai_service_singleton = None
def get_ai_service():
    global _ai_service_singleton
    if not _ai_service_singleton: _ai_service_singleton = AIService()
    return _ai_service_singleton