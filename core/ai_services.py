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
    
    def __post_init__(self):
        self.interview_start_time = self.created_at
        logger.info(f"[WI] Session initialized. Interview start time: {self.interview_start_time}")

    def start_round(self, stage):
        current_time = time.time()
        logger.info(f"[WI] ===== STARTING ROUND: {stage.value} =====")
        self.round_start_times[stage.value] = current_time
        self.current_stage = stage
        self.conversation_state = WI_ConversationState()

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
        if '?' in ai_message:
            parts = ai_message.split('?')
            for i in range(len(parts) - 1, -1, -1):
                part = parts[i].strip()
                if len(part) > 10:
                    for sep in ['. ', '! ', '\n']:
                        if sep in part: part = part.split(sep)[-1].strip()
                    self.conversation_state.last_pure_question = part + '?'
                    break
        else:
            self.conversation_state.last_pure_question = ai_message

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
        self.executor = ThreadPoolExecutor(max_workers=4)
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
    VOICE_FREQ_LOW = 60          # Lower for Bluetooth codec compression
    VOICE_FREQ_HIGH = 4000       # Wider range for Bluetooth harmonics
    VOICE_ENERGY_THRESHOLD = 0.005  # Lower - Bluetooth mics are quieter
    VOICE_RATIO_THRESHOLD = 0.20    # Lower - Bluetooth compresses voice frequencies
    ZCR_LOW = 0.01               # Wider range for Bluetooth artifacts
    ZCR_HIGH = 0.45              # Wider range for Bluetooth artifacts
    MIN_CONFIDENCE = 0.20        # Lower - Bluetooth audio scores lower on all metrics
    def __init__(self, sample_rate=16000): self.sample_rate = sample_rate
    def audio_bytes_to_numpy(self, audio_data):
        """Convert audio bytes (WAV, WebM/Opus, OGG, MP4, etc.) to numpy float32 array.

        The frontend sends audio/webm;codecs=opus — NOT raw PCM or WAV.
        We MUST decode compressed formats properly using ffmpeg, otherwise
        the raw compressed bytes get misinterpreted as PCM and produce
        garbage/near-zero values causing VAD to randomly fail.

        Decode priority:
          1. Try WAV (fast, no subprocess)
          2. Try ffmpeg for any format (WebM, Opus, OGG, MP4, etc.)
          3. Return None if all fail
        """
        try:
            # --- Attempt 1: Parse as WAV (raw PCM already decoded) ---
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

            # --- Attempt 2: Decode with ffmpeg (handles WebM/Opus, OGG, MP4, etc.) ---
            try:
                target_sr = 16000
                result = subprocess.run(
                    [
                        'ffmpeg', '-i', 'pipe:0',     # read from stdin
                        '-f', 's16le',                 # output raw PCM signed 16-bit little-endian
                        '-acodec', 'pcm_s16le',        # PCM codec
                        '-ar', str(target_sr),          # resample to 16kHz
                        '-ac', '1',                     # mono
                        'pipe:1'                        # write to stdout
                    ],
                    input=audio_data,
                    capture_output=True,
                    timeout=10
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

            # --- No fallback to raw int16 — that produces garbage for compressed formats ---
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
        elif zcr < self.ZCR_LOW * 3:  # Still give partial score for near-range
            zcr_score = 0.08
        pat_score = pattern * 0.40
        confidence = vr_score + zcr_score + pat_score
        is_voice = confidence >= self.MIN_CONFIDENCE
        logger.info(f"[VAD] is_voice={is_voice} conf={confidence:.2f} [ratio={voice_ratio:.2f} zcr={zcr:.3f} pattern={pattern:.2f} rms={rms:.4f}]")
        return is_voice, confidence, {"rms": round(rms, 4), "voice_ratio": round(voice_ratio, 3), "confidence": round(confidence, 3), "is_voice": is_voice}

class AudioPreprocessor:
    """Gently cleans audio before Whisper: trim leading/trailing silence + normalize.

    IMPORTANT: Whisper is trained on noisy audio and handles background noise
    well on its own. Aggressive preprocessing (spectral noise gates, etc.)
    actually HURTS transcription accuracy because it removes speech harmonics
    that Whisper relies on. The previous spectral noise gate was estimating
    "noise" from the first few audio frames — which often contained speech,
    causing it to subtract the speaker's own voice from the entire clip.

    Evidence from logs:
      Preprocessed: 91200 -> 18409 samples  (80% of speech removed!)
      Preprocessed: 91200 -> 15594 samples  (83% of speech removed!)
    Result: Whisper got tiny mangled fragments and hallucinated random text.

    Now we only do:
      1. Gentle trim of leading/trailing dead silence (threshold=0.003)
      2. Normalize volume to consistent level
      3. That's it — let Whisper handle the rest
    """
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self._vad = HumanVoiceDetector(sample_rate)

    def _normalize(self, samples):
        """Normalize audio to consistent volume level."""
        max_val = np.max(np.abs(samples))
        return samples * (0.8 / max_val) if max_val > 1e-6 else samples

    def _trim_silence(self, samples, threshold=0.003, pad=3200):
        """Trim only dead silence from start/end. Very gentle threshold.

        threshold=0.003 (was 0.01) — only trims true silence, not quiet speech
        pad=3200 (was 1600) — keeps 200ms padding so speech edges aren't clipped
        """
        above = np.where(np.abs(samples) > threshold)[0]
        if len(above) == 0: return samples
        start = max(0, above[0] - pad)
        end = min(len(samples), above[-1] + pad)
        # Safety: never trim more than 50% of audio — if we would, skip trimming
        if (end - start) < len(samples) * 0.5:
            logger.debug("[AUDIO] Trim would remove >50%% of audio, skipping trim")
            return samples
        return samples[start:end]

    def _to_wav_bytes(self, samples):
        """Convert float32 samples back to WAV bytes."""
        pcm = (samples * 32767).astype(np.int16)
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(self.sample_rate)
            wav.writeframes(pcm.tobytes())
        return buf.getvalue()

    def preprocess(self, audio_data):
        """Preprocess audio: gentle trim + normalize. No spectral manipulation."""
        try:
            samples = self._vad.audio_bytes_to_numpy(audio_data)
            if samples is None: return audio_data
            orig_len = len(samples)
            samples = self._trim_silence(samples)
            # NO spectral noise gate — Whisper handles noise better than we can
            samples = self._normalize(samples)
            logger.info(f"[AUDIO] Preprocessed: {orig_len} -> {len(samples)} samples")
            return self._to_wav_bytes(samples)
        except Exception as e:
            logger.error(f"[AUDIO] Preprocessing failed: {e}")
            return audio_data

class AudioDeviceHealthMonitor:
    """Detects Bluetooth/headphone disconnect. Keeps interview alive."""
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
# ENHANCED WI_OptimizedAudioProcessor with Voice Detection + Device Monitor
# =============================================================================

class WI_OptimizedAudioProcessor:
    def __init__(self, client_manager):
        self.client_manager = client_manager
        self.voice_detector = HumanVoiceDetector()
        self.audio_preprocessor = AudioPreprocessor()
        self.device_monitor = AudioDeviceHealthMonitor()
        self.HALLUCINATION_PHRASES = [
            # Whisper prompt echoes (old prompt that was leaking into transcripts)
            "the speaker is answering questions about their",
            "interview response",
            "the speaker is answering",
            "answering questions about their work",
            "work experience, technical skills",
            "technical skills, and projects",
            # Standard Whisper hallucinations
            "thank you for watching", "thanks for watching", "please subscribe",
            "like and subscribe", "see you in the next", "bye bye", "goodbye",
            "thank you for listening", "the end", "music", "applause", "laughter",
            "silence", "inaudible", "unintelligible", "foreign",
            "speaking foreign language", "don't forget to subscribe", "hit the bell",
            "leave a comment", "check out my", "link in description", "sponsored by",
        ]

    def _decode_to_wav(self, audio_data: bytes) -> bytes:
        """Decode any audio format (WebM/Opus, OGG, MP4, WAV) to WAV PCM bytes.

        The frontend sends audio/webm;codecs=opus. We decode once upfront and
        pass the resulting WAV bytes to all subsequent pipeline steps (device
        health check, VAD, preprocessor, Whisper) so ffmpeg only runs once.
        """
        # Already WAV? Return as-is.
        if audio_data[:4] == b'RIFF' and audio_data[8:12] == b'WAVE':
            logger.debug("[DECODE] Audio is already WAV format")
            return audio_data

        # Use ffmpeg to convert to 16kHz mono WAV
        try:
            result = subprocess.run(
                [
                    'ffmpeg', '-i', 'pipe:0',
                    '-f', 'wav',
                    '-acodec', 'pcm_s16le',
                    '-ar', '16000',
                    '-ac', '1',
                    'pipe:1'
                ],
                input=audio_data,
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0 and len(result.stdout) > 100:
                logger.info("[DECODE] Converted %d bytes -> %d bytes WAV (ffmpeg)", len(audio_data), len(result.stdout))
                return result.stdout
            else:
                logger.warning("[DECODE] ffmpeg conversion failed (rc=%d): %s",
                             result.returncode, result.stderr[:300].decode(errors='replace'))
                return None
        except subprocess.TimeoutExpired:
            logger.warning("[DECODE] ffmpeg timed out converting audio")
            return None
        except FileNotFoundError:
            logger.error("[DECODE] ffmpeg not found — cannot decode WebM/Opus audio")
            return None
        except Exception as e:
            logger.error("[DECODE] Audio decode error: %s", e)
            return None

    async def transcribe_audio_fast(self, audio_data: bytes) -> Tuple[str, float]:
        await self.client_manager.initialize()
        if len(audio_data) < 2000: return "", 0.0

        # DECODE ONCE: Convert WebM/Opus to WAV PCM upfront (avoids running ffmpeg 3x)
        decoded_wav = self._decode_to_wav(audio_data)
        if decoded_wav is None:
            logger.warning("[WI] Could not decode audio, skipping")
            return "", 0.0

        # STEP 1: Device Health Check (using decoded WAV)
        device_health = self.device_monitor.check_audio_health(decoded_wav)
        if not device_health["healthy"]:
            if device_health["action"] == "warn_user":
                logger.warning(f"[WI] Device disconnect: {device_health.get('message', '')}")
                return "__DEVICE_DISCONNECTED__", 0.0
            elif device_health["action"] == "wait_reconnect":
                logger.info(f"[WI] Waiting for device reconnect: {device_health.get('message', '')}")
                return "__DEVICE_RECONNECTING__", 0.0

        # STEP 2: Human Voice Detection (using decoded WAV)
        is_voice, vad_confidence, vad_details = self.voice_detector.is_human_voice(decoded_wav)
        if not is_voice:
            logger.info(f"[WI] Non-human sound rejected (conf={vad_confidence:.2f}). Skipping transcription.")
            return "", 0.0
        logger.info(f"[WI] Human voice confirmed (confidence={vad_confidence:.2f})")

        # STEP 3: Preprocess Audio (using decoded WAV — already in WAV format)
        processed_audio = self.audio_preprocessor.preprocess(decoded_wav)
        logger.info(f"[WI] Audio preprocessed: {len(audio_data)} -> {len(processed_audio)} bytes")

        # STEP 4: Transcribe with Groq Whisper (using processed audio)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
            tf.write(processed_audio)
            temp_path = tf.name
        try:
            with open(temp_path, "rb") as f: audio_bytes = f.read()
            # FIXED: Use short vocabulary hints instead of full sentences.
            # Whisper's "prompt" is meant for spelling/vocabulary guidance, NOT
            # context sentences. Full sentences get echoed back as hallucinations
            # when audio is short or unclear (e.g. "The speaker is answering
            # questions about their wor" was the prompt being echoed).
            tr = await self.client_manager.groq_client.audio.transcriptions.create(
                file=(temp_path, audio_bytes),
                model="whisper-large-v3-turbo",
                language="en",
                prompt="um, uh, like, okay, so, yeah, right, actually, basically"
            )
            raw_text = tr.text.strip() if hasattr(tr, 'text') else ""
            if not raw_text: return "", 0.0
            cleaned_text = self._remove_hallucinations(raw_text)
            confidence = self._calculate_confidence(cleaned_text)
            confidence = (confidence + vad_confidence) / 2
            if confidence < 0.3: return "", confidence
            final_text = self._final_cleanup(cleaned_text)
            if len(final_text.split()) < 2: return "", 0.2
            self.device_monitor.consecutive_bad = 0
            self.device_monitor.disconnect_detected = False
            return final_text, confidence
        except Exception as e:
            logger.error(f"[WI] Transcription error: {e}"); return "", 0.0
        finally:
            try: os.unlink(temp_path)
            except: pass

    def _remove_hallucinations(self, text):
        if not text: return ""
        result = text.lower()
        for phrase in self.HALLUCINATION_PHRASES: result = result.replace(phrase, "")
        cleaned = ""
        for char in result:
            if char.isascii() or char in ".,?!'\"- ": cleaned += char
        cleaned = re.sub(r'[.]{2,}', '.', cleaned)
        cleaned = re.sub(r'[,]{2,}', ',', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
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
        indicator_score = min(indicator_count / 5, 1.0)
        length_score = min(word_count / 10, 1.0)
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
# WI CONVERSATION MANAGER - Main Logic (UNCHANGED)
# =============================================================================

class WI_OptimizedConversationManager:
    def __init__(self, client_manager): self.client_manager = client_manager
    def _detect_user_intent(self, user_response):
        r = user_response.lower().strip()
        if any(p in r for p in ["skip", "next question", "move on", "next one", "pass"]): return "skip"
        if any(p in r for p in ["repeat", "say again", "can you repeat", "what was the question"]): return "repeat"
        if any(p in r for p in ["i don't know", "i'm not sure", "no idea", "can't answer", "don't remember"]): return "dont_know"
        return "normal"
    def _is_gibberish(self, text):
        if not text: return True
        ascii_chars = sum(1 for c in text if c.isascii())
        if len(text) > 0 and (ascii_chars / len(text)) < 0.8: return True
        words = text.lower().split()
        if len(words) > 5:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3: return True
        nonsense_patterns = [r'(.)\1{4,}', r'\b(\w+)\s+\1\s+\1\s+\1']
        for pattern in nonsense_patterns:
            if re.search(pattern, text.lower()): return True
        hallucinations = ["thank you for watching", "please subscribe", "like and subscribe", "see you next time", "bye bye bye", "youtube", "mcdonald"]
        text_lower = text.lower()
        if any(h in text_lower for h in hallucinations): return True
        return False
    def _assess_answer_quality(self, user_response):
        if not user_response: return "silence"
        if self._is_gibberish(user_response): return "gibberish"
        intent = self._detect_user_intent(user_response)
        if intent != "normal": return "skip" if intent == "skip" else ("repeat" if intent == "repeat" else "cant_answer")
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
    async def _generate_dynamic_ack(self, context, tone="friendly"):
        await self.client_manager.initialize()
        prompts = {"weak": "Generate ONE short understanding response when someone gives unclear answer. Like 'I see, let me try another question' or 'Okay, let's move on'. MAX 8 words.", "good": "Generate ONE short positive acknowledgment like 'That's nice!' or 'Good to know!' MAX 5 words.", "technical_good": "Generate ONE short praise for good technical answer like 'Well explained!' or 'Good point!' MAX 5 words.", "technical_weak": "Generate ONE short understanding response for unclear technical answer. MAX 8 words.", "cant_answer": "Generate ONE short supportive response when someone can't answer, like 'No problem, let's try something else'. MAX 10 words.", "transition": "Generate ONE short transition phrase like 'Interesting!' or 'Nice!' MAX 3 words.", "hr": "Generate ONE short professional acknowledgment like 'Thank you for sharing' or 'Good point'. MAX 5 words."}
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
                response_quality = "bad"; prefix = "I think you might not be familiar with that topic. No worries, let me ask you something different. "
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
        prompt = f"""Generate ONE technical behavioral interview question for a candidate who works with {chosen_tech}.\n\nCANDIDATE'S BACKGROUND:\n{summary_context}\n\nThe question should ask about a REAL TECHNICAL SCENARIO like:\n- Debugging a difficult issue with {chosen_tech}\n- Making a technical decision about {chosen_tech}\n- Solving a complex problem using {chosen_tech}\n- Learning something challenging about {chosen_tech}\n- Handling a technical failure or mistake with {chosen_tech}\n\nDO NOT ask generic HR questions like "tell me about leadership" or "describe teamwork".\nThe question MUST be about a specific technical situation involving {chosen_tech}.\n\nALREADY ASKED (DO NOT REPEAT):\n{chr(10).join(all_asked[-10:])}\n\nGenerate ONE specific question (MAX 25 words):"""
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
        prompt = f"""Generate ONE unique technical interview question based on this candidate's work.\n\nCANDIDATE'S WORK SUMMARY:\n{summary[:1500]}\n\nTOPIC TO FOCUS ON: {tech}\n\nALREADY ASKED (DO NOT REPEAT):\n{chr(10).join(all_asked[-10:])}\n\nGenerate a specific question about their practical experience with {tech}.\nAsk about HOW they used it, WHAT they built, or CHALLENGES they faced.\nNOT theoretical definitions.\n\nMAX 20 words. Just the question:"""
        try:
            resp = await self.client_manager.openai_client.chat.completions.create(model=config.OPENAI_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.8, max_tokens=50)
            question = resp.choices[0].message.content.strip().strip('"').strip("'")
            if not question.endswith('?'): question += '?'
            return question
        except Exception as e:
            logger.error(f"Error generating dynamic question: {e}")
            return f"Tell me more about your experience with {tech}?"
    def _get_encouragement(self):
        return random.choice(["That's a great explanation!", "Excellent point!", "Well explained!", "Good answer!", "That's exactly right!", "Nice! You clearly have good experience with this.", "Great insight!", "That's impressive!"])
    async def _generate_followup_from_answer(self, session, user_response, all_asked):
        await self.client_manager.initialize()
        prompt = f"""The candidate gave this good answer: "{user_response[:300]}"\n\nGenerate ONE short follow-up question to dig deeper into what they mentioned.\nAsk about: Specific details, Challenges faced, How they solved problems, Results\n\nALREADY ASKED (DO NOT REPEAT):\n{chr(10).join(all_asked[-5:])}\n\nMAX 15 words. Just the question:"""
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
        return f"""Hello {session.student_name}! Welcome to your weekly interview session. I'm excited to chat with you today!\n\nWe'll have three rounds:\n• First, a Communication round (about 10 minutes) where we'll have a casual conversation and get to know each other.\n• Then, a Technical round (about 25 minutes) where we'll discuss your recent work and technical knowledge.\n• Finally, an HR round (about 10 minutes) with some behavioral questions.\n\nSo, how are you doing today? Ready to get started?"""
    async def generate_silence_response(self, session):
        session.silence_prompt_count += 1
        return random.choice(["Take your time.", "I'm here when you're ready.", "Would you like me to repeat?", "No rush, think about it."])

    async def generate_fast_response(self, session, user_response, db_manager=None):
        await self.client_manager.initialize()
        quality = self._assess_answer_quality(user_response)
        logger.info(f"[WI] Quality: {quality}, Stage: {session.current_stage.value}")
        if quality != "silence": session.silence_prompt_count = 0
        session.conversation_state.last_user_response = user_response
        mentioned_tech = self._extract_topics_from_response(user_response, session)
        session.conversation_state.user_mentioned_tech.extend(mentioned_tech)
        if quality == "repeat":
            if session.exchanges:
                if session.conversation_state.last_pure_question: original_question = session.conversation_state.last_pure_question
                else:
                    last_ai_msg = session.exchanges[-1].ai_message
                    original_question = self._extract_question_from_response(last_ai_msg)
                repeat_response = f"{random.choice(REPEAT_RESPONSES)} {original_question}"
                session.last_was_repeat = True
                logger.info(f"[WI] REPEAT detected - repeating question: {original_question[:50]}...")
                return repeat_response
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
            if elapsed >= 5:
                logger.info(f"[WI] TRANSITIONING: Communication -> Technical")
                session.start_round(WI_InterviewStage.TECHNICAL)
                q, keywords = await self._generate_technical_question(session)
                session.add_exchange(q, expected_keywords=keywords, question_type="technical")
                return f"Nice chatting! Now let's discuss your technical work. {q}"
        elif session.current_stage == WI_InterviewStage.TECHNICAL:
            if elapsed >= 25:
                logger.info(f"[WI] TRANSITIONING: Technical -> HR")
                session.start_round(WI_InterviewStage.HR)
                q, keywords = await self._generate_hr_question(session, db_manager)
                session.add_exchange(q, expected_keywords=keywords, question_type="hr")
                return f"Great technical discussion! Now some behavioral questions. {q}"
        elif session.current_stage == WI_InterviewStage.HR:
            if elapsed >= 10:
                logger.info(f"[WI] TRANSITIONING: HR -> Complete")
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
            if session.exchanges and session.exchanges[-1].question_type == "technical":
                last_ex = session.exchanges[-1]; accuracy = await self._evaluate_technical_accuracy(session, last_ex.ai_message, user_response, last_ex.expected_keywords); session.update_last_response(user_response, 0.8, quality, accuracy)
            self._adjust_difficulty(session, quality)
            if quality == "skip":
                q, keywords = await self._generate_technical_question(session, "", True); session.add_exchange(q, expected_keywords=keywords, question_type="technical"); ack = await self._generate_dynamic_ack("skip", "transition"); return f"{ack} {q}"
            if quality == "gibberish": return "I'm sorry, I didn't catch that clearly. Could you please repeat your answer?"
            if quality == "silence":
                if session.exchanges:
                    last_q = session.exchanges[-1].ai_message.lower()
                    for tech in session.extracted_technologies:
                        if tech.lower() in last_q: session.topic_attempt_count[tech] = session.topic_attempt_count.get(tech, 0) + 1; (session.silent_topics.append(tech) if session.topic_attempt_count[tech] >= 2 and tech not in session.silent_topics else None); break
                session.silence_prompt_count += 1
                if session.silence_prompt_count >= 2:
                    session.silence_prompt_count = 0; q, keywords = await self._generate_technical_question(session, "", True); session.add_exchange(q, expected_keywords=keywords, question_type="technical"); return f"Let's try something different. {q}"
                return await self.generate_silence_response(session)
            if quality == "cant_answer":
                if session.exchanges:
                    last_q = session.exchanges[-1].ai_message.lower()
                    for tech in session.extracted_technologies:
                        if tech.lower() in last_q: session.topic_attempt_count[tech] = session.topic_attempt_count.get(tech, 0) + 1; (session.silent_topics.append(tech) if session.topic_attempt_count[tech] >= 2 and tech not in session.silent_topics else None); break
                session.current_difficulty = "easy"; q, keywords = await self._generate_technical_question(session, "", True); session.add_exchange(q, expected_keywords=keywords, question_type="technical"); ack = await self._generate_dynamic_ack("cant answer technical", "cant_answer"); return f"{ack} {q}"
            if quality == "weak":
                session.current_difficulty = "easy"; q, keywords = await self._generate_technical_question(session, "", True); session.add_exchange(q, expected_keywords=keywords, question_type="technical"); ack = await self._generate_dynamic_ack("weak technical", "technical_weak"); return f"{ack} {q}"
            if quality == "strong" and random.random() < 0.3:
                q = await self._generate_smart_followup(session, user_response, WI_InterviewStage.TECHNICAL); session.add_exchange(q, question_type="technical", is_followup=True); ack = await self._generate_dynamic_ack("good technical", "technical_good"); return f"{ack} {q}"
            q, keywords = await self._generate_technical_question(session, user_response, True); session.add_exchange(q, expected_keywords=keywords, question_type="technical"); ack = await self._generate_dynamic_ack("technical", "technical_good" if quality == "strong" else "transition"); return f"{ack} {q}"
        if session.current_stage == WI_InterviewStage.HR:
            if session.exchanges and session.exchanges[-1].question_type == "hr":
                last_ex = session.exchanges[-1]; accuracy = await self._evaluate_technical_accuracy(session, last_ex.ai_message, user_response, last_ex.expected_keywords); session.update_last_response(user_response, 0.8, quality, accuracy)
            if quality == "skip":
                q, keywords = await self._generate_hr_question(session, db_manager); session.add_exchange(q, expected_keywords=keywords, question_type="hr"); ack = await self._generate_dynamic_ack("skip", "transition"); return f"{ack} {q}"
            if quality == "gibberish": return "I'm sorry, I didn't catch that clearly. Could you please repeat your answer?"
            if quality == "silence":
                session.silence_prompt_count += 1
                if session.silence_prompt_count >= 2:
                    session.silence_prompt_count = 0; q, keywords = await self._generate_hr_question(session, db_manager); session.add_exchange(q, expected_keywords=keywords, question_type="hr"); return f"Let's try a different question. {q}"
                return await self.generate_silence_response(session)
            if quality == "cant_answer":
                q, keywords = await self._generate_hr_question(session, db_manager); session.add_exchange(q, expected_keywords=keywords, question_type="hr"); ack = await self._generate_dynamic_ack("cant answer hr", "cant_answer"); return f"{ack} {q}"
            if quality == "weak":
                q, keywords = await self._generate_hr_question(session, db_manager); session.add_exchange(q, expected_keywords=keywords, question_type="hr"); ack = await self._generate_dynamic_ack("weak hr", "weak"); return f"{ack} {q}"
            if quality == "strong" and random.random() < 0.25:
                q = await self._generate_smart_followup(session, user_response, WI_InterviewStage.HR); session.add_exchange(q, question_type="hr", is_followup=True); ack = await self._generate_dynamic_ack("good hr", "hr"); return f"{ack} {q}"
            q, keywords = await self._generate_hr_question(session, db_manager); session.add_exchange(q, expected_keywords=keywords, question_type="hr"); ack = await self._generate_dynamic_ack("hr response", "hr"); return f"{ack} {q}"
        return "That's interesting. Tell me more?"

    async def generate_fast_evaluation(self, session) -> Tuple[str, Dict[str, float]]:
        """Generate comprehensive evaluation with Q&A feedback format per round"""
        await self.client_manager.initialize()
        comm_exchanges = []; tech_exchanges = []; hr_exchanges = []; tech_accuracies = []; hr_accuracies = []
        for ex in session.exchanges:
            exchange_data = {"question": ex.ai_message, "answer": ex.user_response if ex.user_response else "[SILENT - No response]", "is_silent": not ex.user_response or ex.answer_quality == "silence", "answer_quality": ex.answer_quality, "accuracy": ex.technical_accuracy}
            if ex.stage == WI_InterviewStage.COMMUNICATION: comm_exchanges.append(exchange_data)
            elif ex.stage == WI_InterviewStage.TECHNICAL: tech_exchanges.append(exchange_data); (tech_accuracies.append(ex.technical_accuracy) if ex.technical_accuracy is not None else None)
            elif ex.stage == WI_InterviewStage.HR: hr_exchanges.append(exchange_data); (hr_accuracies.append(ex.technical_accuracy) if ex.technical_accuracy is not None else None)
        tech_accuracy_avg = sum(tech_accuracies) / len(tech_accuracies) if tech_accuracies else 0.5
        hr_accuracy_avg = sum(hr_accuracies) / len(hr_accuracies) if hr_accuracies else 0.5
        total_technical_qs = len(tech_exchanges); total_hr_qs = len(hr_exchanges); total_comm_qs = len(comm_exchanges)
        async def get_feedback_for_qa(question, answer, round_type, is_silent):
            if is_silent: return "Candidate remained silent. Try to respond even with partial thoughts."
            prompt = f"""Give brief feedback (1-2 sentences) for this {round_type} interview answer.\nQuestion: {question}\nAnswer: {answer}\nBe constructive. If good, praise briefly. If weak, suggest improvement."""
            try:
                resp = await self.client_manager.openai_client.chat.completions.create(model=config.OPENAI_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.3, max_tokens=100)
                return resp.choices[0].message.content.strip()
            except: return "Response recorded."
        evaluation_parts = []
        if comm_exchanges:
            evaluation_parts.append("=" * 60); evaluation_parts.append("COMMUNICATION ROUND FEEDBACK"); evaluation_parts.append("=" * 60)
            for i, ex in enumerate(comm_exchanges, 1):
                feedback = await get_feedback_for_qa(ex["question"], ex["answer"], "communication", ex["is_silent"])
                evaluation_parts.append(f"\nQ{i}. AI Question: {ex['question']}"); evaluation_parts.append(f"    User Answer: {ex['answer']}"); evaluation_parts.append(f"    Feedback: {feedback}"); evaluation_parts.append("-" * 40)
        if tech_exchanges:
            evaluation_parts.append("\n" + "=" * 60); evaluation_parts.append("TECHNICAL ROUND FEEDBACK"); evaluation_parts.append("=" * 60)
            for i, ex in enumerate(tech_exchanges, 1):
                feedback = await get_feedback_for_qa(ex["question"], ex["answer"], "technical", ex["is_silent"])
                accuracy_str = f" (Accuracy: {ex['accuracy']:.0%})" if ex["accuracy"] is not None else ""
                evaluation_parts.append(f"\nQ{i}. AI Question: {ex['question']}"); evaluation_parts.append(f"    User Answer: {ex['answer']}"); evaluation_parts.append(f"    Feedback: {feedback}{accuracy_str}"); evaluation_parts.append("-" * 40)
        if hr_exchanges:
            evaluation_parts.append("\n" + "=" * 60); evaluation_parts.append("HR/BEHAVIORAL ROUND FEEDBACK"); evaluation_parts.append("=" * 60)
            for i, ex in enumerate(hr_exchanges, 1):
                feedback = await get_feedback_for_qa(ex["question"], ex["answer"], "HR/behavioral", ex["is_silent"])
                evaluation_parts.append(f"\nQ{i}. AI Question: {ex['question']}"); evaluation_parts.append(f"    User Answer: {ex['answer']}"); evaluation_parts.append(f"    Feedback: {feedback}"); evaluation_parts.append("-" * 40)
        evaluation_parts.append("\n" + "=" * 60); evaluation_parts.append("OVERALL SUMMARY"); evaluation_parts.append("=" * 60)
        silent_count = sum(1 for ex in comm_exchanges + tech_exchanges + hr_exchanges if ex["is_silent"])
        summary_prompt = f"""Provide a brief overall interview summary (4-5 sentences) for {session.student_name}.\n\nMETRICS:\n- Communication Questions: {total_comm_qs}\n- Technical Questions: {total_technical_qs}\n- Technical Accuracy: {tech_accuracy_avg:.0%}\n- HR Questions: {total_hr_qs}\n- Correct Answers: {session.correct_answers}\n- Partial Answers: {session.partial_answers}\n- Weak Answers: {session.wrong_answers}\n- Silent/No Response: {silent_count}\n\nInclude: Overall performance, Key strengths (2-3), Areas to improve (2-3), Final recommendation"""
        summary_resp = await self.client_manager.openai_client.chat.completions.create(model=config.OPENAI_MODEL, messages=[{"role": "user", "content": summary_prompt}], temperature=0.3, max_tokens=400)
        overall_summary = summary_resp.choices[0].message.content.strip()
        evaluation_parts.append(f"\n{overall_summary}")
        evaluation_parts.append("\n" + "-" * 40); evaluation_parts.append("STATISTICS:")
        evaluation_parts.append(f"  Total Questions: {total_comm_qs + total_technical_qs + total_hr_qs}")
        evaluation_parts.append(f"  Technical Accuracy: {tech_accuracy_avg:.0%}")
        evaluation_parts.append(f"  Questions Answered Well: {session.correct_answers}")
        evaluation_parts.append(f"  Partial Answers: {session.partial_answers}")
        evaluation_parts.append(f"  Needs Improvement: {session.wrong_answers}")
        evaluation_parts.append(f"  Silent Responses: {silent_count}")
        evaluation = "\n".join(evaluation_parts)
        score_prompt = f"""Based on this interview, provide scores (0-10) for each criteria.\nTechnical Accuracy: {tech_accuracy_avg:.0%}\nReply in EXACT format:\ncommunication: X\ntechnical: X\nleadership: X\nbehaviour: X\nconfidence: X"""
        sc_resp = await self.client_manager.openai_client.chat.completions.create(model=config.OPENAI_MODEL, messages=[{"role": "user", "content": score_prompt}], temperature=0.1, max_tokens=200)
        score_text = sc_resp.choices[0].message.content.lower()
        scores = {}
        for key in ["communication", "technical", "leadership", "behaviour", "confidence"]:
            m = re.search(rf"{key}[:\s]*(\d+\.?\d*)", score_text)
            if m: scores[f"{key}_score"] = min(float(m.group(1)), 10.0)
            else:
                if key == "technical": scores[f"{key}_score"] = round(tech_accuracy_avg * 10, 1)
                else: scores[f"{key}_score"] = 5.0
        scores["technical_accuracy"] = round(tech_accuracy_avg * 100, 1)
        scores["hr_accuracy"] = round(hr_accuracy_avg * 100, 1)
        scores["questions_correct"] = session.correct_answers
        scores["questions_partial"] = session.partial_answers
        scores["questions_wrong"] = session.wrong_answers
        scores["questions_silent"] = silent_count
        scores["total_questions"] = total_technical_qs + total_hr_qs + total_comm_qs
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