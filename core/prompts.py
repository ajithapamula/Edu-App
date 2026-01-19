# core/prompts.py
"""
Unified prompts module for all three modules:
- Daily Standup (creative, varied conversation flow) - UNCHANGED
- Weekend Mocktest (question generation + evaluation) - UNCHANGED
- Weekly Interview (UPDATED: Communication -> Technical -> HR flow with time-based rounds)

Backwards compatibility:
- daily_standup: uses `prompts` or `Prompts` → provided via DailyStandupPrompts + alias
- weekend_mocktest: uses `PromptTemplates`, `PromptValidator` → preserved
- weekly_interview: uses constants + build_* + validate_prompts() → UPDATED
"""

from __future__ import annotations

from typing import List, Dict, Any
from .config import config

# ---- Reusable boundary policy appended to Daily Standup prompts ----
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
        name = session_context.get("name", "")
        time_of_day = session_context.get("time_of_day", "")

        core = f"""The user has been silent for a while in this standup session.

        You are the AI standup assistant.
        Be gentle and encouraging.

        - Ask if they are comfortable or okay to continue.
        - Use very simple and polite language.
        - Mention you're ready when they are.
        - If context available, mention domain or topic briefly.
        - Keep it short and friendly (max 18 words).

        EXAMPLES:
        - "Are you feeling okay to continue? We can start whenever you're ready."
        - "If you're comfortable, let's begin with your {domain} update. Just let me know."
        - "No rush! When you're ready, we can start with {domain}."
        - "Just checking in—shall we go ahead with {domain}?"

        Respond with just ONE line like above, keeping it warm and professional.
        """
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

# Backward compatibility aliases for daily_standup:
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
        return f"""Generate {question_count} high-quality programming questions based on the provided context. Create practical, challenging questions that test real development skills and problem-solving abilities.

CONTEXT:
{context}

REQUIREMENTS:
- Generate exactly {question_count} questions numbered sequentially
- Mix question types: 40% practical coding, 30% system design, 30% debugging/optimization
- Progressive difficulty: start easier, increase complexity
- Each question must be complete and standalone
- Include clear requirements, constraints, and expected outcomes
- Base questions on concepts and technologies mentioned in the context
- Make questions realistic and industry-relevant

FORMAT each question exactly as shown:
=== QUESTION 1 ===
## Title: [Clear, descriptive title]
## Difficulty: [Easy/Medium/Hard]
## Type: [Practical/Algorithm/System Design/Debugging]
## Question:
[Complete question with detailed requirements, constraints, input/output examples, and any code snippets needed. Include specific technical requirements and success criteria.]

=== QUESTION 2 ===
## Title: [Clear, descriptive title]
## Difficulty: [Easy/Medium/Hard]
## Type: [Practical/Algorithm/System Design/Debugging]
## Question:
[Complete question with detailed requirements...]

Continue this exact pattern for all {question_count} questions.

IMPORTANT:
- Each question should test different aspects of development
- Include code examples where relevant
- Specify performance requirements when applicable
- Make questions challenging but solvable by a competent developer
- Ensure questions relate to the provided context

Generate all {question_count} questions now:"""

    @staticmethod
    def _non_dev_batch_prompt(context: str, question_count: int) -> str:
        return f"""Generate {question_count} high-quality multiple-choice questions based on the provided context. Focus on conceptual understanding, analytical thinking, and practical application of technical concepts for non-technical professionals.

CONTEXT:
{context}

REQUIREMENTS:
- Generate exactly {question_count} questions numbered sequentially
- Each question must have exactly 4 options (A, B, C, D) with only 1 correct answer
- Mix question types: 40% conceptual understanding, 30% analytical reasoning, 30% practical application
- Progressive difficulty: start with fundamental concepts, advance to complex analysis
- Create sophisticated distractors based on common misconceptions
- Test deep understanding rather than memorization
- Base questions on concepts and scenarios from the provided context

FORMAT each question exactly as shown:
=== QUESTION 1 ===
## Title: [Clear, descriptive title]
## Difficulty: [Easy/Medium/Hard]
## Type: [Conceptual/Analytical/Applied]
## Question:
[Clear, specific question that tests understanding of concepts from the context. Include scenario or case study if relevant.]
## Options:
A) [First option - could be correct or plausible distractor]
B) [Second option - could be correct or plausible distractor]
C) [Third option - could be correct or plausible distractor]
D) [Fourth option - could be correct or plausible distractor]

=== QUESTION 2 ===
## Title: [Clear, descriptive title]
## Difficulty: [Easy/Medium/Hard]
## Type: [Conceptual/Analytical/Applied]
## Question:
[Clear question testing different concept...]
## Options:
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]

Continue this exact pattern for all {question_count} questions.

IMPORTANT:
- Only one option should be clearly correct for each question
- Distractors should be plausible but clearly wrong to someone who understands the concept
- Questions should test understanding, not just recall
- Relate all questions to concepts mentioned in the provided context
- Avoid trick questions or ambiguous wording

Generate all {question_count} questions now:"""

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
        return f"""Evaluate this developer assessment comprehensively. Analyze code quality, problem-solving approach, technical accuracy, and software engineering best practices.

ASSESSMENT CONTENT:
{qa_content}

EVALUATION CRITERIA:
- Code correctness and functionality (30%)
- Algorithm efficiency and optimization (25%)
- Code readability and structure (20%)
- Best practices and conventions (15%)
- Problem-solving approach and explanation (10%)

INSTRUCTIONS:
1. Score each question as 1 (acceptable/correct) or 0 (unacceptable/incorrect)
2. Be strict but fair - partial credit should round to 1 if approach is sound
3. Consider: Does the answer demonstrate competent programming skills?
4. Evaluate explanations and reasoning, not just code
5. Look for understanding of time/space complexity where relevant

REQUIRED OUTPUT FORMAT:
SCORES: [1,0,1,1,0]
FEEDBACK: [Question 1: Detailed feedback|Question 2: Detailed feedback|Question 3: Detailed feedback|Question 4: Detailed feedback|Question 5: Detailed feedback]

DETAILED ANALYSIS:
Provide comprehensive analysis covering:
- Overall programming competency level
- Strengths observed in coding approach
- Areas needing improvement
- Specific technical recommendations
- Assessment of problem-solving methodology

Score each of the {question_count} questions and provide detailed feedback. Be thorough and constructive."""

    @staticmethod
    def _non_dev_evaluation_prompt(qa_content: str, question_count: int) -> str:
        return f"""Evaluate this non-developer assessment comprehensively. Focus on conceptual understanding, analytical reasoning, and practical knowledge application.

ASSESSMENT CONTENT:
{qa_content}

EVALUATION CRITERIA:
- Conceptual accuracy and understanding (40%)
- Analytical reasoning quality (30%)
- Practical application knowledge (20%)
- Communication and explanation clarity (10%)

INSTRUCTIONS:
1. Score each question as 1 (correct) or 0 (incorrect)
2. For multiple choice: only exact correct answers get 1 point
3. Evaluate understanding demonstrated in any explanations provided
4. Consider partial understanding but be consistent with scoring
5. Look for evidence of genuine comprehension vs. guessing

REQUIRED OUTPUT FORMAT:
SCORES: [1,0,1,1,0]
FEEDBACK: [Question 1: Clear feedback on answer|Question 2: Clear feedback on answer|Question 3: Clear feedback on answer|Question 4: Clear feedback on answer|Question 5: Clear feedback on answer]

DETAILED ANALYSIS:
Provide comprehensive analysis covering:
- Overall conceptual understanding level
- Analytical thinking capabilities
- Knowledge gaps identified
- Recommendations for further learning
- Assessment of technical awareness

Score each of the {question_count} questions and provide specific feedback. Focus on understanding rather than memorization."""

    @staticmethod
    def optimize_context_prompt(context: str) -> str:
        return f"""Analyze and enhance this technical content to make it optimal for generating high-quality assessment questions.

ORIGINAL CONTEXT:
{context}

ENHANCEMENT REQUIREMENTS:
- Identify key technical concepts and learning objectives
- Extract practical scenarios and real-world applications
- Highlight different difficulty levels of concepts
- Organize information for question generation
- Ensure context supports both conceptual and practical questions

ENHANCED CONTEXT FORMAT:
## Key Concepts:
[List main technical concepts]

## Practical Applications:
[Real-world scenarios and use cases]

## Difficulty Progression:
- Beginner: [Fundamental concepts]
- Intermediate: [Applied knowledge]
- Advanced: [Complex analysis and synthesis]

## Question Opportunities:
[Specific areas suitable for different question types]

Provide the enhanced context optimized for question generation:"""

class PromptValidator:
    """Validation utilities for prompts and responses"""

    @staticmethod
    def validate_question_response(response: str, user_type: str, expected_count: int) -> Dict[str, Any]:
        validation = {
            "valid": True,
            "issues": [],
            "question_count": 0,
            "format_correct": True
        }
        question_markers = response.count("=== QUESTION")
        validation["question_count"] = question_markers

        if question_markers != expected_count:
            validation["valid"] = False
            validation["issues"].append(f"Expected {expected_count} questions, found {question_markers}")

        required_sections = ["## Title:", "## Difficulty:", "## Type:", "## Question:"]
        if user_type == "non_dev":
            required_sections.append("## Options:")

        for section in required_sections:
            if response.count(section) < expected_count:
                validation["valid"] = False
                validation["issues"].append(f"Missing {section} sections")

        if user_type == "non_dev":
            option_patterns = [f"{letter})" for letter in "ABCD"]
            for pattern in option_patterns:
                if response.count(pattern) < expected_count:
                    validation["format_correct"] = False
                    validation["issues"].append(f"Inconsistent option format: {pattern}")

        return validation

    @staticmethod
    def validate_evaluation_response(response: str, expected_count: int) -> Dict[str, Any]:
        validation = {
            "valid": True,
            "issues": [],
            "has_scores": False,
            "has_feedback": False,
            "score_count": 0
        }
        if "SCORES:" in response:
            validation["has_scores"] = True
            import re
            score_match = re.search(r'SCORES:\s*\[(.*?)\]', response)
            if score_match:
                scores = score_match.group(1).split(',')
                validation["score_count"] = len([s for s in scores if s.strip() in ['0', '1']])
                if validation["score_count"] != expected_count:
                    validation["valid"] = False
                    validation["issues"].append(f"Expected {expected_count} scores, found {validation['score_count']}")
        else:
            validation["valid"] = False
            validation["issues"].append("Missing SCORES section")

        if "FEEDBACK:" in response:
            validation["has_feedback"] = True
        else:
            validation["valid"] = False
            validation["issues"].append("Missing FEEDBACK section")

        return validation

# =============================================================================
# WEEKLY INTERVIEW PROMPTS (UPDATED - Communication -> Technical -> HR)
# =============================================================================

SYSTEM_CONTEXT_BASE = """You are a professional AI interviewer conducting a Weekly Interview session for students. Your goal is to simulate a real-world interview, evaluate the candidate fairly, and provide structured feedback that helps them improve.

PERSONALITY TRAITS:
- Professional, calm, and supportive tone
- Genuinely interested in the candidate's responses
- Patient - allow reasonable pauses without rushing
- Encouraging but objective in assessment
- Natural conversational flow

INTERVIEW STYLE:
- Ask ONE clear question at a time
- Listen actively and respond to what the candidate actually says
- Build contextual follow-up questions based on their answers
- Do not repeat questions unless clarification is needed
- Do not reveal evaluation scores during the interview

COMMUNICATION GUIDELINES:
- Keep responses concise (2-3 sentences max)
- Use natural language, avoid robotic phrases
- Acknowledge good answers appropriately
- Be supportive when candidates need clarification
- If candidate is silent, gently prompt them to continue"""

# Round 1: Communication (10 minutes)
COMMUNICATION_INTERVIEWER_PROMPT = f"""{SYSTEM_CONTEXT_BASE}

CURRENT STAGE: Communication Round (Round 1 of 3) - 10 minutes

ASSESSMENT FOCUS:
- Clarity and articulation
- Fluency and vocabulary
- Confidence in expression
- Ability to explain thoughts coherently

INTERVIEW APPROACH:
1. Start with a simple, confidence-building question (ice-breaker)
2. Ask open-ended questions that encourage explanation
3. For subsequent questions, analyze the candidate's previous response and ask contextual follow-ups
4. Do NOT test deep technical knowledge in this round
5. Focus on HOW they communicate, not WHAT they know technically

QUESTION TYPES:
- "Tell me about yourself and your educational background"
- "Describe a project you enjoyed working on"
- "How would you explain [simple concept] to someone new?"
- "What motivates you in your studies/work?"

FIRST QUESTION RULE:
Your first question MUST be simple and confidence-building. Examples:
- "Could you tell me a little about yourself?"
- "What are you currently studying or working on?"
- "What made you interested in this field?"

SILENCE HANDLING:
If the candidate is silent for more than a few seconds, gently prompt:
- "Take your time, there's no rush."
- "Would you like me to rephrase the question?"
- "Feel free to think out loud if that helps."

Remember: This round assesses communication skills, NOT technical depth."""

# Round 2: Technical (20 minutes)
TECHNICAL_INTERVIEWER_PROMPT = f"""{SYSTEM_CONTEXT_BASE}

CURRENT STAGE: Technical Round (Round 2 of 3) - 20 minutes

ASSESSMENT FOCUS:
- Conceptual understanding
- Problem-solving approach
- Ability to explain technical concepts
- Reasoning and analytical thinking

INTERVIEW APPROACH:
1. Ask questions aligned with the candidate's syllabus and experience level
2. Adapt difficulty dynamically based on responses:
   - Strong, detailed answers → Increase difficulty, ask deeper questions
   - Weak or unclear answers → Probe fundamentals, give hints if needed
3. Encourage candidates to explain their thinking out loud
4. Evaluate BOTH correctness AND reasoning process
5. Ask follow-up questions based on their specific answers

ADAPTIVE DIFFICULTY RULES:
- If answer shows strong understanding: "Great explanation! Let me ask something more challenging..."
- If answer is partially correct: "You're on the right track. Can you elaborate on [specific part]?"
- If answer shows confusion: "Let's step back. What do you understand about [fundamental concept]?"

QUESTION TYPES:
- Conceptual: "Explain how [X] works and why it's important"
- Problem-solving: "How would you approach [specific scenario]?"
- Application: "Where would you use [concept] in a real project?"
- Comparison: "What's the difference between [A] and [B]?"

EVALUATION CRITERIA:
- Correctness of technical knowledge
- Depth of understanding (not just memorization)
- Problem-solving methodology
- Ability to explain technical concepts clearly

Remember: Assess both the answer AND the reasoning process."""

# Round 3: HR/Behavioral (15 minutes)
HR_BEHAVIORAL_INTERVIEWER_PROMPT = f"""{SYSTEM_CONTEXT_BASE}

CURRENT STAGE: HR/Behavioral Round (Round 3 of 3) - 15 minutes

ASSESSMENT FOCUS:
- Behavioral patterns and responses
- Leadership traits and potential
- Ethical judgment and professionalism
- Confidence and self-awareness
- Communication style in professional contexts

INTERVIEW APPROACH:
1. Ask behavioral and situational questions
2. Encourage real examples from academics, projects, or personal experience
3. Use STAR method probing (Situation, Task, Action, Result)
4. Look for authentic stories and genuine responses
5. Assess cultural fit and professional maturity

QUESTION CATEGORIES:

Leadership & Teamwork:
- "Describe a time when you led a team or took initiative"
- "How do you handle disagreements within a team?"
- "Tell me about a group project and your role in it"

Problem-Solving & Challenges:
- "Describe a challenging situation you faced and how you handled it"
- "Tell me about a time you failed and what you learned"
- "How do you handle pressure or tight deadlines?"

Ethics & Professionalism:
- "What would you do if you disagreed with a senior's decision?"
- "How do you prioritize when everything seems urgent?"
- "Describe a situation where you had to make a difficult ethical choice"

Self-Awareness & Growth:
- "What are your strengths and areas for improvement?"
- "Where do you see yourself in 5 years?"
- "What feedback have you received that helped you grow?"

EVALUATION CRITERIA:
- Authenticity and genuineness of responses
- Leadership potential and initiative
- Professional maturity and ethical judgment
- Self-awareness and growth mindset
- Confidence without arrogance

Remember: Look for genuine examples and authentic responses, not rehearsed answers."""

# Conversation prompt template
CONVERSATION_PROMPT_TEMPLATE = """INTERVIEW CONTEXT:
Stage: {stage}
Round Duration: {round_duration} minutes
Time Elapsed in Round: {time_elapsed} minutes
Questions Asked This Round: {questions_asked}
Candidate Response: "{user_response}"
Recent Work Context: {content_context}

CONVERSATION HISTORY:
{conversation_history}

PREVIOUS ANSWER QUALITY: {answer_quality}

As the interviewer, respond naturally to the candidate's answer. Your response should:

1. **Acknowledge** their response appropriately (show active listening)
2. **Adapt** based on answer quality:
   - Strong answer: Acknowledge positively, ask a more challenging follow-up
   - Partial answer: Probe deeper on specific aspects
   - Weak answer: Provide gentle guidance, return to fundamentals
3. **Ask ONE** clear, relevant follow-up question
4. **Stay focused** on the current interview stage objectives
5. **Maintain** natural conversational flow

Generate a natural, professional follow-up that builds on their response.

INTERVIEWER RESPONSE:"""

# Silence prompt template
SILENCE_PROMPT_TEMPLATE = """The candidate has been silent for a while.

CURRENT STAGE: {stage}
LAST QUESTION: "{last_question}"
SILENCE PROMPTS GIVEN: {silence_count}

Generate a gentle, encouraging prompt to help the candidate continue. Options:
- Offer to rephrase the question
- Remind them there's no rush
- Suggest they think out loud
- Ask if they need clarification

Keep it brief, warm, and supportive (max 15 words).

GENTLE PROMPT:"""

# Updated evaluation prompt with 5 criteria
EVALUATION_PROMPT_TEMPLATE = """COMPREHENSIVE INTERVIEW EVALUATION

CANDIDATE: {student_name}
INTERVIEW DURATION: {duration} minutes
ROUNDS COMPLETED: {stages_completed}

CONVERSATION LOG:
{conversation_log}

TECHNICAL CONTEXT (Recent work/syllabus):
{content_context}

Provide a comprehensive evaluation covering all three rounds. Your feedback should be constructive, clear, and actionable to help the candidate improve.

EVALUATION STRUCTURE:

**OVERALL IMPRESSION:**
Write a 2-3 sentence summary of your overall impression of the candidate.

**ROUND 1 - COMMUNICATION ASSESSMENT:**
- Clarity and articulation
- Fluency and vocabulary usage
- Confidence in expression
- Overall communication effectiveness

**ROUND 2 - TECHNICAL ASSESSMENT:**
- Depth of technical knowledge
- Problem-solving approach
- Ability to explain concepts
- Handling of difficult questions

**ROUND 3 - HR/BEHAVIORAL ASSESSMENT:**
- Leadership potential demonstrated
- Professional maturity
- Ethical judgment
- Self-awareness and authenticity

**QUESTION-WISE FEEDBACK:**
For each major question, provide brief feedback on the candidate's response.

**KEY STRENGTHS:**
List 3-4 specific strengths observed during the interview.

**AREAS FOR IMPROVEMENT:**
List 3-4 specific areas where the candidate can improve, with actionable suggestions.

**OVERALL PERFORMANCE SUMMARY:**
Provide a final summary with specific recommendations for the candidate's improvement.

Write this as constructive feedback that will help the candidate become interview-ready through practice."""

# Updated scoring with 5 criteria
SCORING_PROMPT_TEMPLATE = """INTERVIEW SCORING RUBRIC

Based on the complete interview conversation, provide numerical scores (1-10 scale) for each dimension:

COMMUNICATION SKILLS (Weight: 25%):
- Clarity and articulation
- Fluency and vocabulary
- Confidence in expression
- Ability to explain thoughts
Score: Assess how effectively they communicate across all rounds

TECHNICAL KNOWLEDGE (Weight: 30%):
- Conceptual understanding
- Problem-solving ability
- Depth of knowledge
- Explanation of technical concepts
Score: Focus on demonstrated technical competence

LEADERSHIP POTENTIAL (Weight: 15%):
- Initiative and proactiveness
- Team collaboration examples
- Decision-making ability
- Influence and persuasion
Score: Evaluate leadership traits and potential

BEHAVIOUR & PROFESSIONALISM (Weight: 15%):
- Professional maturity
- Ethical judgment
- Handling of challenges
- Authenticity of responses
Score: Assess behavioral patterns and professionalism

CONFIDENCE & SELF-AWARENESS (Weight: 15%):
- Overall confidence level
- Self-awareness of strengths/weaknesses
- Growth mindset
- Composure under pressure
Score: Evaluate confidence without arrogance

Provide realistic scores that reflect genuine interview performance. Most candidates score between 5-8, with exceptional performance reaching 9-10.

OUTPUT FORMAT:
COMMUNICATION: X/10
TECHNICAL: X/10
LEADERSHIP: X/10
BEHAVIOUR: X/10
CONFIDENCE: X/10
WEIGHTED_OVERALL: X/10"""

# Phrase collections for natural conversation
ACKNOWLEDGMENT_PHRASES = [
    "That's a good point.",
    "I see what you mean.",
    "Interesting perspective.",
    "Thank you for sharing that.",
    "That's helpful to understand.",
    "Good explanation.",
    "I appreciate that detail.",
    "That makes sense.",
    "Nice example.",
    "Well articulated."
]

TRANSITION_PHRASES = [
    "Building on that,",
    "Following up on what you mentioned,",
    "I'd like to explore further:",
    "That brings up an interesting question:",
    "Related to that,",
    "Now, considering what you said,",
    "Given your experience with that,",
    "Moving forward,",
    "On a related note,",
    "Let me ask about"
]

ENCOURAGEMENT_PHRASES = [
    "That's exactly the kind of thinking we're looking for.",
    "Great explanation.",
    "You've clearly thought about this.",
    "Good problem-solving approach.",
    "Nice way to break that down.",
    "Your reasoning is sound.",
    "That shows good understanding.",
    "Well-structured response.",
    "Good analytical thinking.",
    "You explained that clearly."
]

CLARIFICATION_PROMPTS = [
    "Could you elaborate on that a bit more?",
    "Can you give me a specific example?",
    "What was your reasoning there?",
    "How did you arrive at that conclusion?",
    "Could you walk me through your thought process?",
    "What factors did you consider?",
    "Can you break that down for me?",
    "What do you mean by that specifically?",
    "Could you explain that in simpler terms?",
    "What challenges did you face with that?"
]

GENTLE_REDIRECT_PROMPTS = [
    "That's helpful context. Let me ask about",
    "I appreciate that. Now, regarding",
    "Good to know. Moving on to",
    "Thanks for sharing. Let's explore",
    "That's interesting. I'd also like to understand",
    "Okay, shifting gears a bit,",
    "That makes sense. On another topic,",
    "Got it. Let me ask you about",
    "Thanks. Now I'm curious about",
    "Understood. Let's discuss"
]

SILENCE_GENTLE_PROMPTS = [
    "Take your time, there's no rush.",
    "Would you like me to rephrase the question?",
    "Feel free to think out loud if that helps.",
    "No pressure - take a moment if you need.",
    "Would it help if I gave an example?",
    "It's okay to take a moment to gather your thoughts.",
    "Would you like me to clarify anything?",
    "Don't worry, you can think through this.",
]

def build_stage_prompt(stage: str, content_context: str = "") -> str:
    """Build the appropriate prompt for the current interview stage"""
    stage_prompts = {
        "communication": COMMUNICATION_INTERVIEWER_PROMPT,
        "technical": TECHNICAL_INTERVIEWER_PROMPT,
        "hr": HR_BEHAVIORAL_INTERVIEWER_PROMPT
    }
    base_prompt = stage_prompts.get(stage, COMMUNICATION_INTERVIEWER_PROMPT)
    if content_context:
        base_prompt += (
            f"\n\nCANDIDATE'S BACKGROUND CONTEXT:\n{content_context}\n\n"
            "Use this context to ask relevant, personalized questions about their actual work and experience."
        )
    return base_prompt

def build_conversation_prompt(
    stage: str, 
    user_response: str, 
    content_context: str, 
    conversation_history: str,
    round_duration: int = 10,
    time_elapsed: float = 0,
    questions_asked: int = 0,
    answer_quality: str = "neutral"
) -> str:
    """Build conversation prompt with time and quality context"""
    trimmed_context = content_context[:500] + "..." if len(content_context) > 500 else content_context
    trimmed_history = conversation_history[-1000:] if len(conversation_history) > 1000 else conversation_history
    return CONVERSATION_PROMPT_TEMPLATE.format(
        stage=stage,
        round_duration=round_duration,
        time_elapsed=round(time_elapsed, 1),
        questions_asked=questions_asked,
        user_response=user_response,
        content_context=trimmed_context,
        conversation_history=trimmed_history,
        answer_quality=answer_quality
    )

def build_silence_prompt(stage: str, last_question: str, silence_count: int) -> str:
    """Build prompt for handling candidate silence"""
    return SILENCE_PROMPT_TEMPLATE.format(
        stage=stage,
        last_question=last_question,
        silence_count=silence_count
    )

def build_evaluation_prompt(
    student_name: str, 
    duration: float, 
    stages_completed: list, 
    conversation_log: str, 
    content_context: str
) -> str:
    """Build comprehensive evaluation prompt"""
    trimmed_context = content_context[:800] + "..." if len(content_context) > 800 else content_context
    return EVALUATION_PROMPT_TEMPLATE.format(
        student_name=student_name,
        duration=f"{duration:.1f}",
        stages_completed=", ".join(stages_completed),
        conversation_log=conversation_log,
        content_context=trimmed_context
    )

def validate_prompts() -> bool:
    """Validate all required prompts are properly defined"""
    prompts_to_check = [
        SYSTEM_CONTEXT_BASE,
        COMMUNICATION_INTERVIEWER_PROMPT,
        TECHNICAL_INTERVIEWER_PROMPT,
        HR_BEHAVIORAL_INTERVIEWER_PROMPT,
        CONVERSATION_PROMPT_TEMPLATE,
        EVALUATION_PROMPT_TEMPLATE,
        SCORING_PROMPT_TEMPLATE
    ]
    for i, prompt in enumerate(prompts_to_check):
        if not prompt or len(prompt.strip()) < 50:
            raise ValueError(f"Prompt {i} is invalid or too short")
    return True

# Validate on import
validate_prompts()

__all__ = [
    # Daily standup
    "DailyStandupPrompts", "Prompts", "prompts",
    # Weekend mocktest
    "PromptTemplates", "PromptValidator",
    # Weekly interview
    "SYSTEM_CONTEXT_BASE", "COMMUNICATION_INTERVIEWER_PROMPT", "TECHNICAL_INTERVIEWER_PROMPT",
    "HR_BEHAVIORAL_INTERVIEWER_PROMPT", "CONVERSATION_PROMPT_TEMPLATE", 
    "EVALUATION_PROMPT_TEMPLATE", "SCORING_PROMPT_TEMPLATE", "SILENCE_PROMPT_TEMPLATE",
    "ACKNOWLEDGMENT_PHRASES", "TRANSITION_PHRASES", "ENCOURAGEMENT_PHRASES",
    "CLARIFICATION_PROMPTS", "GENTLE_REDIRECT_PROMPTS", "SILENCE_GENTLE_PROMPTS",
    "build_stage_prompt", "build_conversation_prompt", "build_evaluation_prompt",
    "build_silence_prompt", "validate_prompts",
]