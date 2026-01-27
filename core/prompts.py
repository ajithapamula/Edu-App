# core/prompts.py
"""
Unified prompts module - ALL questions generated dynamically via LLM
NO hardcoded questions anywhere - everything is generated fresh each time
"""

from __future__ import annotations

from typing import List, Dict, Any
from .config import config

# ---- Reusable boundary policy for Daily Standup ----
BOUNDARY_POLICY = f"""
BOUNDARIES:
- Stay strictly on the CURRENT project/work topics in this conversation.
- If the user goes off-topic: give one brief, courteous redirect (≤ {getattr(config, 'REDIRECT_MAX_WORDS', 18)} words) and then ask ONE on-topic question.
- If the user uses vulgar/abusive language: do not repeat it; issue a short warning and restate the topic.
- After {getattr(config, 'MAX_VULGAR_STRIKES', 2)} warnings for vulgar language, end politely.
- Never generate sexual or hateful content. Tone is {getattr(config, 'BOUNDARY_TONE', 'calm, brief, professional')}.
""".strip()

def _append_boundaries(block: str) -> str:
    return f"{block.rstrip()}\n\n{BOUNDARY_POLICY}"

# =============================================================================
# RESPONSE PHRASES FOR DIFFERENT SITUATIONS
# =============================================================================

# When user gives wrong/unclear answer
WRONG_ANSWER_RESPONSES = [
    "No worries, that's okay.",
    "That's alright, let me ask it differently.",
    "No problem, try to explain a bit more clearly.",
    "That's fine, take your time.",
    "Okay, don't worry about that.",
    "That's okay, let's try another approach.",
    "No issues, we can move on.",
    "Alright, no problem at all.",
]

# When user is silent
SILENCE_ENCOURAGEMENT_RESPONSES = [
    "Take your time, there's no rush.",
    "I noticed you're quiet - would you like me to rephrase?",
    "No pressure, just share what comes to mind.",
    "It's okay to think out loud.",
    "Would you like to skip this one?",
    "Take a moment if you need.",
    "Feel free to ask if you need clarification.",
    "No worries, we can come back to this.",
]

# When user says "I don't know" / "can't answer" / "skip"
CANT_ANSWER_RESPONSES = [
    "No worries, let's move to a different question.",
    "That's perfectly fine, let me ask something else.",
    "No problem at all, here's another one.",
    "Okay, let's try a different topic.",
    "That's alright, moving on.",
    "No issues, let's continue with something else.",
]

# =============================================================================
# DAILY STANDUP PROMPTS (UNCHANGED)
# =============================================================================

class DailyStandupPrompts:
    """Creative prompts that force LLM to be original and varied"""

    @staticmethod
    def summary_splitting_prompt(summary: str) -> str:
        return f"""You're a curious person who wants to chat about this project work. Break it into {config.SUMMARY_CHUNKS} interesting topics.

PROJECT WORK:
{summary}

Think like you're genuinely interested:
- What sounds cool or challenging?
- What would you be curious about?
- What technical stuff catches your attention?
- What problems or solutions interest you?

Give me topics separated by '###CHUNK###' only."""

    @staticmethod
    def base_questions_prompt(chunk_content: str) -> str:
        core = f"""You just read this project/work chunk:

    {chunk_content}

    TASK:
    Ask {config.BASE_QUESTIONS_PER_CHUNK} questions that show real technical curiosity about THIS chunk only.

    STRICT RULES:
    - Only ask questions directly related to THIS chunk/topic.
    - No personal or off-topic questions.
    - Vary phrasing so nothing feels repetitive.
    - Be professional, concise, human (not poetic).

    Mix question types:
    - Technical details / design choices
    - Challenges faced / trade-offs
    - Learnings / debugging insights
    - What's next / roadmap

    FORMAT:
    - Numbered list of unique questions (no answers)."""
        return _append_boundaries(core)

    @staticmethod
    def followup_analysis_prompt(chunk_content: str, user_response: str) -> str:
        core = f"""You asked about: "{chunk_content[:100]}..."

They replied: "{user_response}"

Put yourself in a real conversation. What would you naturally do?

If you're satisfied with their answer → say: COMPLETE
If you're still curious and would naturally ask more → create 1-2 follow-up questions

Be creative with follow-ups. Don't use standard boring questions. Think about what a real curious person would ask based on what they actually said.

FORMAT:
FOLLOWUP: [Your creative question]
FOLLOWUP: [Another creative one if needed]"""
        return _append_boundaries(core)

    @staticmethod
    def dynamic_greeting_response(user_input: str, greeting_count: int, context: Dict = None) -> str:
        ctx = context or {}
        conversation_history = ctx.get('recent_exchanges', [])
        user_name = (ctx.get('user_name') or ctx.get('name') or '').strip()
        time_of_day = (ctx.get('time_of_day') or '').strip()
        domain = ctx.get('domain', "today's technical topic")
        is_final_greeting = (greeting_count + 1) >= config.GREETING_EXCHANGES

        sentiment_hint = (ctx.get("sentiment_hint") or "").lower()
        simple_english = bool(ctx.get("simple_english", False))
        suppress_salutation = bool(ctx.get("suppress_salutation", False))

        simple_note = "Use very simple words. No fancy phrases." if simple_english else ""
        salutation_rule = "Do NOT say hello/hi/good morning again." if suppress_salutation else \
                        "You MAY greet once using time-of-day and name."

        core = f"""You're in the GREETING phase of a technical interview.

    User just said: "{user_input}"
    Recent chat: {conversation_history[-2:] if conversation_history else "Just started"}
    Candidate name (optional): {user_name or "N/A"}
    Time-of-day (optional): {time_of_day or "N/A"}
    Target domain: {domain}

    SENTIMENT HINT: {sentiment_hint or "unknown"}
    {simple_note}
    {salutation_rule}

    GOAL
    - If sentiment is POSITIVE:
    * Short confirmation, then move to {domain} now.
    - If sentiment is NEGATIVE:
    * One empathy line + one motivation line, then ask: "Shall we start?"
    - If sentiment is NEUTRAL:
    * Short check-in, then suggest starting {domain}.
    - If this is the final greeting turn: {('YES' if is_final_greeting else 'NO')}, you MUST transition to {domain} now.

    STYLE
    - 10–18 words, human, professional.
    - No small-talk loops. Stay strictly on the interview topic.
    - Output exactly ONE line.

    OUTPUT
    One concise line following the rules above."""
        return _append_boundaries(core)

    @staticmethod
    def dynamic_technical_response(context_text: str, user_input: str, next_question: str, session_state: Dict = None) -> str:
        domain = (session_state or {}).get('domain', 'the interview topic')

        core = f"""You're in the TECHNICAL round of a {domain} interview.

    User said: "{user_input}"
    Next planned question: "{next_question}"

    RULES:
    - If user_input is ON-TOPIC → connect naturally and ask the next question.
    - If OFF-TOPIC (e.g., water tank, food, movies):
    * Do NOT follow that.
    * Say one short polite redirect: "Let's stay on {domain}".
    * Then immediately ask the planned technical question.

    STYLE:
    - Simple English, short and clear.
    - Max 15–18 words.
    - No modern or fancy talk.

    OUTPUT:
    One short line, either connecting naturally or redirecting then asking {domain} question."""
        return _append_boundaries(core)

    @staticmethod
    def dynamic_followup_response(current_concept_title: str, concept_content: str, 
                             history: str, previous_question: str, user_response: str,
                             current_question_number: int, questions_for_concept: int) -> str:
        core = f"""You're a friendly team lead having standup chat with your team member. Keep it normal and conversational.

**Topic**: {current_concept_title}
**They said**: "{user_response}"
**Your last question**: "{previous_question}"

**RULES:**
1. Talk like a NORMAL person - no weird fancy phrases
2. Use SIMPLE English that sounds natural
3. Keep responses SHORT - max 15-20 words each
4. Sound interested but not fake
5. Be different each time but stay normal

**RESPONSE STYLE**: 
- Normal conversational English
- Show you're listening to what they said
- Ask good follow-up questions
- Don't use weird phrases like "data stew" or "sentence acrobatics"
- Sound like a real colleague, not a poet

**TASK**: 
1. Decide if their answer is good enough (YES/NO)
2. Give ONE natural response with next question

**FORMAT** (EXACTLY like this):
UNDERSTANDING: [YES or NO]
CONCEPT: [{current_concept_title}]
QUESTION: [Your normal, short response with next question - max 20 words]

Keep it simple, natural, and conversational. No weird creative phrases."""
        return _append_boundaries(core)

    @staticmethod
    def dynamic_concept_transition(user_response: str, next_question: str, progress_info: Dict) -> str:
        core = f"""You're moving to a new topic in your chat.

**They said**: "{user_response}"
**New topic**: "{progress_info.get('current_concept', 'next thing')}"
**Next question**: "{next_question}"

**BE CREATIVE**: Make this transition feel natural and different. Don't use boring standard phrases.

Think about:
- What they just told you
- How to smoothly shift topics
- How a real person would change subjects

Make it feel like a real conversation where you're genuinely moving from one interesting topic to another.

Max 20 words. Be original every time."""
        return _append_boundaries(core)

    @staticmethod
    def dynamic_fragment_evaluation(concepts_covered: List[str], conversation_exchanges: List[Dict],
                                    session_stats: Dict) -> str:
        concepts_text = "\n".join([f"- {concept}" for concept in concepts_covered])

        conversation_summary = []
        for exchange in conversation_exchanges[-6:]:
            conversation_summary.append(
                f"Q: {exchange['ai_message'][:80]}...\n"
                f"A: {exchange['user_response'][:80]}...\n"
            )
        conversation_text = "\n".join(conversation_summary)

        core = f"""You're evaluating a technical standup.

    SESSION METRICS:
    - Topics covered: {session_stats['concepts_covered']}/{session_stats['total_concepts']} ({session_stats['coverage_percentage']}%)
    - Duration: {session_stats['duration_minutes']} minutes
    - Main questions: {session_stats['main_questions']}, Follow-ups: {session_stats['followup_questions']}

    TOPICS:
    {concepts_text}

    RECENT EXCHANGES:
    {conversation_text}

    TASK:
    Score ONLY these categories:
    - Communication (clarity, flow): 0–2
    - Confidence (tone, assertiveness): 0–2
    - Technical (topics covered & accuracy): 0–6

    Then write short feedback (≤120 words) that is concrete and helpful.

    OUTPUT FORMAT (exactly):
    COMMUNICATION: X/2
    CONFIDENCE: X/2
    TECHNICAL: X/6
    TOTAL: Y/10
    FEEDBACK: [short, human, specific feedback]"""
        return _append_boundaries(core)

    @staticmethod
    def dynamic_session_completion(conversation_summary: Dict, user_final_response: str = None) -> str:
        topics_discussed = conversation_summary.get('topics_covered', [])
        total_exchanges = conversation_summary.get('total_exchanges', 0)

        core = f"""You're ending a good standup chat with your teammate.

    **CHAT SUMMARY:**
    - Talked about: {len(topics_discussed)} different topics
    - Total questions: {total_exchanges}
    - Their final words: "{user_final_response}"

    **GOAL**: Give ONE short, natural closing line that includes a brief thanks and ends the session.

    **STYLE**
    - Very short (12–20 words), natural, human.
    - Must include "Thanks" or "Thank you".
    - No follow-up questions.
    - No bullets, no headings, no extra lines.

    **OUTPUT**
    Output exactly ONE sentence only, nothing else."""
        return _append_boundaries(core)

    @staticmethod
    def dynamic_clarification_request(context: Dict) -> str:
        attempts = context.get('clarification_attempts', 0)
        core = f"""You need them to speak more clearly.

**SITUATION**: You've asked for clarity {attempts} times already.

**BE CREATIVE**: Ask for clarification in a different way each time. Don't use the same boring phrases.

Make it:
- Natural and friendly
- Different from previous attempts
- Not repetitive or annoying
- Understanding and patient

One creative sentence. Make it feel real."""
        return _append_boundaries(core)

    @staticmethod
    def dynamic_conclusion_response(user_input: str, session_context: Dict) -> str:
        core = f"""They just said: "{user_input}"

You're wrapping up the chat about their work.

**BE CREATIVE**: Respond to what they said and end naturally. Don't use boring standard endings.

Make it:
- Personal to what they shared
- Appreciative of their time
- Natural like a real conversation ending
- Unique and genuine

Max 20 words. Be original every time."""
        return _append_boundaries(core)

    @staticmethod
    def boundary_offtopic_prompt(topic: str, subtask: str = "") -> str:
        ask = f"What progress since yesterday on {subtask or topic}?"
        core = f"""User is off-topic (e.g., talking about unrelated things like movies, sports, random analogies).
    TASK:
    - Do NOT follow the off-topic content.
    - Politely redirect in one short line (≤ {getattr(config, 'REDIRECT_MAX_WORDS', 18)} words).
    - Immediately ask ONE question about THIS topic: {ask}.

    STYLE:
    - Professional, concise, interview-focused.
    - Never expand on or question the off-topic subject.
    - Always bring the user back to the interview topic."""
        return _append_boundaries(core)

    @staticmethod
    def dynamic_silence_response(session_context: Dict) -> str:
        domain = session_context.get("domain", "your topic")
        core = f"""The user has been silent for a while in this standup session.
        Be gentle and encouraging.
        - Ask if they are comfortable or okay to continue.
        - Use very simple and polite language.
        - Keep it short and friendly (max 18 words).
        Respond with just ONE line, keeping it warm and professional."""
        return _append_boundaries(core)
    
    @staticmethod
    def boundary_vulgar_prompt(topic: str) -> str:
        core = f"User used inappropriate language. Give ONE short warning and restate the topic: {topic}. Do not repeat the language."
        return _append_boundaries(core)

    @staticmethod
    def off_topic_redirect(topic: str, subtask: str = "") -> str:
        if subtask:
            return f"Let's keep this about {topic}. What's the status of {subtask}?"
        return f"Let's keep this about {topic}. What progress did you make since yesterday?"

    @staticmethod
    def off_topic_firm(topic: str, subtask: str = "") -> str:
        if subtask:
            return f"We need to stay on {topic}. What blockers are you facing on {subtask}?"
        return f"We need to stay on {topic}. Any blockers or progress since yesterday?"

    @staticmethod
    def off_topic_move_on(next_topic: str) -> str:
        return f"I'll move to the next item: {next_topic}. What changed since last update?"

    @staticmethod
    def vulgar_warning_1(topic: str) -> str:
        return f"Let's keep language respectful. Can you summarize your update on {topic}?"

    @staticmethod
    def vulgar_warning_2(topic: str) -> str:
        return f"This needs to stay respectful. Last chance—please share your update on {topic}."

    @staticmethod
    def end_due_to_vulgarity() -> str:
        return "I'm ending this standup due to repeated inappropriate language. We can resume when it's respectful."

    @staticmethod
    def refuse_nsfw_and_redirect(topic: str) -> str:
        return f"I can't discuss that. Let's focus on your {topic} update: progress, blockers, next steps?"

    @staticmethod
    def harassment_block_and_redirect(topic: str) -> str:
        return f"That language isn't okay here. Please share your concrete update on {topic}—progress, blockers, next steps."

# Backward compatibility aliases
Prompts = DailyStandupPrompts
prompts = DailyStandupPrompts()

# =============================================================================
# WEEKEND MOCKTEST PROMPTS (UNCHANGED)
# =============================================================================

class PromptTemplates:
    """Optimized prompt templates for AI question generation and evaluation"""

    @staticmethod
    def create_batch_questions_prompt(user_type: str, context: str, question_count: int = None) -> str:
        if question_count is None:
            question_count = config.QUESTIONS_PER_TEST
        if user_type == "dev":
            return PromptTemplates._dev_batch_prompt(context, question_count)
        else:
            return PromptTemplates._non_dev_batch_prompt(context, question_count)

    @staticmethod
    def _dev_batch_prompt(context: str, question_count: int) -> str:
        return f"""Generate {question_count} high-quality programming questions based on the provided context.

CONTEXT:
{context}

REQUIREMENTS:
- Generate exactly {question_count} questions numbered sequentially
- Mix question types: 40% practical coding, 30% system design, 30% debugging/optimization
- Progressive difficulty: start easier, increase complexity
- Each question must be complete and standalone

FORMAT each question exactly as shown:
=== QUESTION 1 ===
## Title: [Clear, descriptive title]
## Difficulty: [Easy/Medium/Hard]
## Type: [Practical/Algorithm/System Design/Debugging]
## Question:
[Complete question with detailed requirements]

Continue this exact pattern for all {question_count} questions."""

    @staticmethod
    def _non_dev_batch_prompt(context: str, question_count: int) -> str:
        return f"""Generate {question_count} high-quality multiple-choice questions based on the provided context.

CONTEXT:
{context}

REQUIREMENTS:
- Generate exactly {question_count} questions numbered sequentially
- Each question must have exactly 4 options (A, B, C, D) with only 1 correct answer
- Mix question types: 40% conceptual, 30% analytical, 30% practical application

FORMAT each question exactly as shown:
=== QUESTION 1 ===
## Title: [Clear, descriptive title]
## Difficulty: [Easy/Medium/Hard]
## Type: [Conceptual/Analytical/Applied]
## Question:
[Clear, specific question]
## Options:
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]

Continue this exact pattern for all {question_count} questions."""

    @staticmethod
    def create_evaluation_prompt(user_type: str, qa_pairs: List[Dict[str, Any]]) -> str:
        qa_text = []
        for i, qa in enumerate(qa_pairs, 1):
            question = qa['question'][:300] + "..." if len(qa['question']) > 300 else qa['question']
            answer = qa['answer'][:200] + "..." if len(qa['answer']) > 200 else qa['answer']
            qa_text.append(f"QUESTION {i}:\n{question}\n\nSTUDENT ANSWER:\n{answer}")
        qa_content = "\n\n" + "="*50 + "\n\n".join(qa_text)
        if user_type == "dev":
            return PromptTemplates._dev_evaluation_prompt(qa_content, len(qa_pairs))
        else:
            return PromptTemplates._non_dev_evaluation_prompt(qa_content, len(qa_pairs))

    @staticmethod
    def _dev_evaluation_prompt(qa_content: str, question_count: int) -> str:
        return f"""Evaluate this developer assessment.

ASSESSMENT CONTENT:
{qa_content}

INSTRUCTIONS:
1. Score each question as 1 (correct) or 0 (incorrect)
2. Provide feedback for each question

REQUIRED OUTPUT FORMAT:
SCORES: [1,0,1,1,0]
FEEDBACK: [Question 1: feedback|Question 2: feedback|...]

Score each of the {question_count} questions."""

    @staticmethod
    def _non_dev_evaluation_prompt(qa_content: str, question_count: int) -> str:
        return f"""Evaluate this non-developer assessment.

ASSESSMENT CONTENT:
{qa_content}

INSTRUCTIONS:
1. Score each question as 1 (correct) or 0 (incorrect)
2. For multiple choice: only exact correct answers get 1 point

REQUIRED OUTPUT FORMAT:
SCORES: [1,0,1,1,0]
FEEDBACK: [Question 1: feedback|Question 2: feedback|...]

Score each of the {question_count} questions."""

    @staticmethod
    def optimize_context_prompt(context: str) -> str:
        return f"""Analyze and enhance this technical content for question generation.

ORIGINAL CONTEXT:
{context}

Provide enhanced context with key concepts, practical applications, and difficulty progression."""


class PromptValidator:
    """Validation utilities for prompts and responses"""

    @staticmethod
    def validate_question_response(response: str, user_type: str, expected_count: int) -> Dict[str, Any]:
        validation = {"valid": True, "issues": [], "question_count": 0, "format_correct": True}
        question_markers = response.count("=== QUESTION")
        validation["question_count"] = question_markers
        if question_markers != expected_count:
            validation["valid"] = False
            validation["issues"].append(f"Expected {expected_count} questions, found {question_markers}")
        return validation

    @staticmethod
    def validate_evaluation_response(response: str, expected_count: int) -> Dict[str, Any]:
        validation = {"valid": True, "issues": [], "has_scores": False, "has_feedback": False}
        if "SCORES:" in response:
            validation["has_scores"] = True
        else:
            validation["valid"] = False
            validation["issues"].append("Missing SCORES section")
        if "FEEDBACK:" in response:
            validation["has_feedback"] = True
        return validation

# =============================================================================
# WEEKLY INTERVIEW - DYNAMIC QUESTION GENERATION PROMPTS
# =============================================================================

SYSTEM_CONTEXT_BASE = """You are a professional AI interviewer conducting a Weekly Interview session. Your goal is to simulate a real-world interview with natural conversation flow.

PERSONALITY:
- Professional, calm, supportive
- Genuinely interested in responses
- Patient and encouraging
- Natural conversational flow

STYLE:
- Ask ONE clear question at a time
- Listen actively and respond to what was said
- Build contextual follow-ups
- Keep responses concise (2-3 sentences max)"""


def build_communication_question_prompt(
    student_name: str,
    conversation_history: str,
    topics_already_covered: List[str],
    questions_already_asked: List[str],
    is_first_question: bool = False
) -> str:
    """Build prompt for generating dynamic communication questions"""
    
    topics_str = ", ".join(topics_already_covered) if topics_already_covered else "none yet"
    questions_str = "\n".join([f"- {q}" for q in questions_already_asked[-5:]]) if questions_already_asked else "none yet"
    
    if is_first_question:
        return f"""Generate a friendly, casual FIRST question to start a conversation with {student_name}.

This is the COMMUNICATION round - we want to get to know them personally, NOT test technical skills.

RULES:
- Ask about their interests, hobbies, favorites, or personality
- Be warm and welcoming
- Make them feel comfortable
- DO NOT ask technical questions
- Keep it casual and friendly

GOOD TOPICS: favorite places, hobbies, interests, music, movies, travel, food, weekend activities, personality traits

Generate ONE casual, friendly opening question (MAX 12 words):"""
    
    return f"""Generate a NEW casual conversation question for the COMMUNICATION round.

CONVERSATION SO FAR:
{conversation_history if conversation_history else "Just started"}

TOPICS ALREADY COVERED: {topics_str}
QUESTIONS ALREADY ASKED:
{questions_str}

RULES:
1. Ask about something DIFFERENT from topics already covered
2. Keep it casual and friendly - this is NOT a technical round
3. DO NOT ask about work, coding, programming, or technical topics
4. Ask about personal interests, hobbies, favorites, experiences, or personality
5. Generate a UNIQUE question not similar to ones already asked
6. Make it natural and conversational

GOOD TOPICS TO EXPLORE:
- Favorite places, cities, travel destinations
- Hobbies and interests
- Music, movies, books
- Food and cuisine
- Weekend activities
- Personal goals and dreams
- Memorable experiences
- How they relax or unwind

Generate ONE new, casual question (MAX 12 words):"""


def build_communication_followup_prompt(
    user_response: str,
    original_question: str,
    current_topic: str,
    followup_count: int
) -> str:
    """Build prompt for generating natural follow-up on same topic"""
    
    return f"""The candidate just answered a question. Generate a NATURAL follow-up that shows interest.

ORIGINAL QUESTION: "{original_question}"
TOPIC: {current_topic}
CANDIDATE'S RESPONSE: "{user_response}"
FOLLOW-UPS ALREADY ASKED ON THIS TOPIC: {followup_count}

YOUR TASK:
Generate ONE natural follow-up question that:
1. Shows GENUINE interest in what they said
2. Digs deeper into the SAME topic (don't change topics)
3. References something SPECIFIC they mentioned
4. Is casual and friendly, not formal
5. Is short (under 15 words)

EXAMPLE GOOD FOLLOW-UPS:
- If they mentioned a place: "What do you like most about it?"
- If they mentioned an activity: "How did you get into that?"
- If they mentioned people: "That sounds fun! Do you do that often?"
- If they shared a feeling: "What makes it so special to you?"

BAD FOLLOW-UPS (avoid):
- Changing to a completely different topic
- Asking technical questions
- Being too formal or interview-like
- Generic questions that ignore what they said

Generate ONE short, natural follow-up question that BUILDS ON what they said:"""


def build_technical_question_prompt(
    content_context: str,
    previous_questions: List[str],
    user_last_response: str,
    difficulty: str,
    conversation_history: str
) -> str:
    """Build prompt for generating dynamic technical questions from summaries"""
    
    prev_q_text = "\n".join([f"- {q}" for q in previous_questions[-5:]]) if previous_questions else "None yet"
    
    # If no content context, provide fallback technical topics
    if not content_context or len(content_context) < 50:
        content_context = "General software development, coding, debugging, databases, APIs, web development"
    
    return f"""Generate ONE TECHNICAL interview question based on the candidate's work.

CANDIDATE'S TECHNICAL WORK:
{content_context[:2000]}

QUESTIONS ALREADY ASKED (DO NOT REPEAT):
{prev_q_text}

DIFFICULTY: {difficulty}

⚠️ CRITICAL RULES - MUST FOLLOW:
1. Ask ONLY about technical topics: programming, coding, databases, APIs, frameworks, debugging
2. Base question on technologies mentioned in their work above
3. DO NOT REPEAT previous questions
4. Match difficulty: easy=basics, medium=how/why, hard=optimization

❌ FORBIDDEN - NEVER ASK ABOUT:
- Movies, TV shows, books, music
- Hobbies, free time, relaxation
- Favorites, preferences, feelings
- Travel, places, food
- Personal life, friends, family
- Anything NOT related to their technical work

✅ GOOD TECHNICAL QUESTIONS:
- "How did you handle authentication in your project?"
- "What database did you use and why?"
- "How would you optimize this query?"
- "Explain your approach to error handling."

Generate ONE TECHNICAL question (MAX 15 words only):"""


def build_hr_question_prompt(
    previously_asked_questions: List[str],
    conversation_history: str,
    student_context: str
) -> str:
    """Build prompt for generating unique HR/behavioral questions"""
    
    prev_q_text = "\n".join([f"- {q}" for q in previously_asked_questions[-15:]]) if previously_asked_questions else "None"
    
    return f"""Generate ONE unique behavioral/HR interview question.

QUESTIONS ALREADY ASKED (DO NOT REPEAT OR ASK SIMILAR):
{prev_q_text}

RECENT CONVERSATION:
{conversation_history[-400:] if conversation_history else 'Starting HR round'}

CANDIDATE BACKGROUND:
{student_context[:300] if student_context else 'General candidate'}

QUESTION GENERATION RULES:
1. Generate a COMPLETELY NEW question not similar to any in the list
2. Focus on behavioral situations, leadership, teamwork, or personal growth
3. Ask for SPECIFIC examples (use STAR method style)
4. Make it professional but conversational
5. Avoid generic yes/no questions

QUESTION CATEGORIES TO VARY:
- Leadership: "Tell me about a time you led/took initiative..."
- Teamwork: "Describe a situation where you collaborated/worked with others..."
- Challenges: "Share an experience where you faced a difficult situation..."
- Conflict: "Tell me about a time you had a disagreement..."
- Growth: "What feedback have you received that helped you improve..."
- Motivation: "What drives you / what are you passionate about..."
- Ethics: "What would you do if..."
- Strengths/Weaknesses: Different angles on self-awareness
- Goals: Career aspirations and personal development
- Failure: Learning from mistakes

AVOID:
- Questions already in the list above
- Questions too similar to asked ones
- Generic questions without asking for examples
- Technical questions (this is HR round)

Generate ONE short HR/behavioral question (MAX 15 words only):"""


# =============================================================================
# ROUND TRANSITION MESSAGES
# =============================================================================

ROUND_TRANSITION_TO_TECHNICAL = """Great conversation! I've enjoyed getting to know you better.

Now let's move on to the Technical round. For the next 20 minutes, I'll ask you some questions based on your recent work and technical knowledge.

Don't worry if you don't know something - just share your thought process. Ready?"""

ROUND_TRANSITION_TO_HR = """Excellent work on the technical questions! You handled that well.

For our final round, we'll spend about 15 minutes on some HR and behavioral questions. I'd love to hear about your experiences and how you handle different situations.

Shall we continue?"""

INTERVIEW_COMPLETION_MESSAGE = """That brings us to the end of our interview session!

Thank you so much for your time and thoughtful responses. You did a great job engaging with the questions.

I'll now generate your detailed feedback covering all three rounds. Give me just a moment..."""


# =============================================================================
# STANDARD PHRASE COLLECTIONS
# =============================================================================

ACKNOWLEDGMENT_PHRASES = [
    "That's a good point.",
    "I see what you mean.",
    "Interesting perspective.",
    "Thank you for sharing that.",
    "That's helpful to understand.",
    "Good explanation.",
    "That makes sense.",
]

TRANSITION_PHRASES = [
    "Building on that,",
    "Following up on what you mentioned,",
    "That brings up an interesting question:",
    "Related to that,",
    "Given your experience with that,",
]

ENCOURAGEMENT_PHRASES = [
    "That's exactly the kind of thinking we're looking for.",
    "Great explanation.",
    "You've clearly thought about this.",
    "Good problem-solving approach.",
    "Your reasoning is sound.",
]

CLARIFICATION_PROMPTS = [
    "Could you elaborate on that a bit more?",
    "Can you give me a specific example?",
    "What was your reasoning there?",
    "Could you walk me through your thought process?",
]

GENTLE_REDIRECT_PROMPTS = [
    "That's helpful context. Let me ask about",
    "Good to know. Moving on to",
    "Thanks for sharing. Let's explore",
]

SILENCE_GENTLE_PROMPTS = [
    "Take your time, there's no rush.",
    "Would you like me to rephrase the question?",
    "Feel free to think out loud if that helps.",
    "No pressure - take a moment if you need.",
]


# =============================================================================
# EVALUATION PROMPTS
# =============================================================================

EVALUATION_PROMPT_TEMPLATE = """Evaluate interview for {student_name}.
Duration: {duration} minutes | Rounds: {stages_completed}

TRANSCRIPT:
{conversation_log}

BACKGROUND:
{content_context}

Generate evaluation with QUESTION-BY-QUESTION feedback in this EXACT format:

=== OVERALL SUMMARY ===
(2-3 sentences about overall performance)

=== COMMUNICATION ROUND ===
For EACH question in communication round:

Q1: [AI's question]
A1: [User's answer]
Feedback: [1 sentence - what was good or needs improvement]

Q2: [AI's question]
A2: [User's answer]
Feedback: [1 sentence feedback]

(continue for all communication questions...)

Round Summary: [1 sentence overall communication assessment]

=== TECHNICAL ROUND ===
For EACH question in technical round:

Q1: [AI's question]
A1: [User's answer]
Feedback: [Was answer correct? What was missing? 1-2 sentences]

Q2: [AI's question]
A2: [User's answer]
Feedback: [1-2 sentences]

(continue for all technical questions...)

Round Summary: [1 sentence overall technical assessment]

=== HR ROUND ===
For EACH question in HR round:

Q1: [AI's question]
A1: [User's answer]
Feedback: [Did they give specific example? Quality of response? 1-2 sentences]

Q2: [AI's question]
A2: [User's answer]
Feedback: [1-2 sentences]

(continue for all HR questions...)

Round Summary: [1 sentence overall HR assessment]

=== KEY STRENGTHS ===
1. [strength 1]
2. [strength 2]
3. [strength 3]

=== AREAS TO IMPROVE ===
1. [improvement 1]
2. [improvement 2]
3. [improvement 3]

=== TIPS FOR NEXT TIME ===
1. [actionable tip 1]
2. [actionable tip 2]

IMPORTANT: Include EVERY question and answer from the transcript. If user's answer was unclear or garbage text, mention that in feedback."""


SCORING_PROMPT_TEMPLATE = """Score this interview (1-10 scale):

COMMUNICATION (25%): Clarity, fluency, confidence
TECHNICAL (30%): Knowledge, problem-solving, explanations
LEADERSHIP (15%): Initiative, collaboration, decision-making
BEHAVIOUR (15%): Professionalism, ethics, maturity
CONFIDENCE (15%): Self-awareness, composure, growth mindset

OUTPUT FORMAT:
COMMUNICATION: X/10
TECHNICAL: X/10
LEADERSHIP: X/10
BEHAVIOUR: X/10
CONFIDENCE: X/10
WEIGHTED_OVERALL: X/10"""


SILENCE_PROMPT_TEMPLATE = """The candidate has been silent.
STAGE: {stage}
LAST QUESTION: "{last_question}"
SILENCE PROMPTS GIVEN: {silence_count}

Generate a gentle, encouraging prompt (max 15 words):"""


CONVERSATION_PROMPT_TEMPLATE = """Stage: {stage}
Time Elapsed: {time_elapsed} minutes
Questions Asked: {questions_asked}
Response: "{user_response}"

History:
{conversation_history}

Answer Quality: {answer_quality}

Generate a natural response that acknowledges what they said and asks ONE follow-up question."""


INTRODUCTION_PROMPT_TEMPLATE = """Generate a warm introduction for {student_name}'s interview.
Explain the 3 rounds: Communication (10min), Technical (20min), HR (15min).
Ask how they're doing today."""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def build_introduction_prompt(student_name: str) -> str:
    return INTRODUCTION_PROMPT_TEMPLATE.format(student_name=student_name)


def build_stage_prompt(stage: str, content_context: str = "") -> str:
    """Build stage-specific system prompt"""
    base = SYSTEM_CONTEXT_BASE
    
    if stage == "communication":
        base += "\n\nCURRENT STAGE: Communication Round - casual conversation, NO technical questions."
    elif stage == "technical":
        base += f"\n\nCURRENT STAGE: Technical Round\nCANDIDATE'S WORK:\n{content_context[:1500]}"
    elif stage == "hr":
        base += "\n\nCURRENT STAGE: HR/Behavioral Round - focus on experiences and situational questions."
    
    return base


def build_conversation_prompt(
    stage: str, user_response: str, content_context: str, conversation_history: str,
    round_duration: int = 10, time_elapsed: float = 0, questions_asked: int = 0,
    answer_quality: str = "neutral"
) -> str:
    return CONVERSATION_PROMPT_TEMPLATE.format(
        stage=stage,
        round_duration=round_duration,
        time_elapsed=round(time_elapsed, 1),
        questions_asked=questions_asked,
        user_response=user_response,
        content_context=content_context[:500] if stage == "technical" else "",
        conversation_history=conversation_history[-1000:],
        answer_quality=answer_quality
    )


def build_silence_prompt(stage: str, last_question: str, silence_count: int) -> str:
    return SILENCE_PROMPT_TEMPLATE.format(
        stage=stage,
        last_question=last_question,
        silence_count=silence_count
    )


def build_evaluation_prompt(
    student_name: str, duration: float, stages_completed: list,
    conversation_log: str, content_context: str
) -> str:
    return EVALUATION_PROMPT_TEMPLATE.format(
        student_name=student_name,
        duration=f"{duration:.1f}",
        stages_completed=", ".join(stages_completed),
        conversation_log=conversation_log,
        content_context=content_context[:800]
    )


def get_round_transition_message(next_stage: str) -> str:
    transitions = {
        "technical": ROUND_TRANSITION_TO_TECHNICAL,
        "hr": ROUND_TRANSITION_TO_HR,
        "complete": INTERVIEW_COMPLETION_MESSAGE
    }
    return transitions.get(next_stage, "Let's continue.")


def validate_prompts() -> bool:
    """Validate required prompts exist"""
    required = [SYSTEM_CONTEXT_BASE, EVALUATION_PROMPT_TEMPLATE, SCORING_PROMPT_TEMPLATE]
    for p in required:
        if not p or len(p.strip()) < 50:
            raise ValueError("Invalid prompt detected")
    return True


validate_prompts()

__all__ = [
    # Daily standup
    "DailyStandupPrompts", "Prompts", "prompts",
    # Weekend mocktest
    "PromptTemplates", "PromptValidator",
    # Weekly interview
    "SYSTEM_CONTEXT_BASE", "EVALUATION_PROMPT_TEMPLATE", "SCORING_PROMPT_TEMPLATE",
    "ROUND_TRANSITION_TO_TECHNICAL", "ROUND_TRANSITION_TO_HR", "INTERVIEW_COMPLETION_MESSAGE",
    "ACKNOWLEDGMENT_PHRASES", "TRANSITION_PHRASES", "ENCOURAGEMENT_PHRASES",
    "CLARIFICATION_PROMPTS", "GENTLE_REDIRECT_PROMPTS", "SILENCE_GENTLE_PROMPTS",
    # Dynamic generation
    "WRONG_ANSWER_RESPONSES", "SILENCE_ENCOURAGEMENT_RESPONSES", "CANT_ANSWER_RESPONSES",
    "build_communication_question_prompt", "build_communication_followup_prompt",
    "build_technical_question_prompt", "build_hr_question_prompt",
    # Helpers
    "build_introduction_prompt", "build_stage_prompt", "build_conversation_prompt",
    "build_evaluation_prompt", "build_silence_prompt", "get_round_transition_message",
    "validate_prompts",
]