"""
Creative Varied Prompts for Daily Standup
Makes LLM be creative and different every single time
"""

from typing import List, Dict
from .config import config

class Prompts:
    """Creative prompts that force LLM to be original and varied"""
    
    @staticmethod
    def summary_splitting_prompt(summary: str) -> str:
        """Get LLM to think creatively about topics"""
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
        """Make LLM ask unique questions each time"""
        return f"""You just heard about this work from your teammate:

{chunk_content}

You're genuinely curious and want to know more. Ask {config.BASE_QUESTIONS_PER_CHUNK} questions that show real interest.

BE CREATIVE - don't use boring standard questions. Make each question unique and natural. Think about what you'd really want to know if this was your friend's project.

Mix different types:
- Some about the technical details
- Some about challenges they faced  
- Some about what they learned
- Some about what's coming next

Just give numbered questions. Be original."""

    @staticmethod
    def followup_analysis_prompt(chunk_content: str, user_response: str) -> str:
        """Make LLM decide naturally about follow-ups"""
        return f"""You asked about: "{chunk_content[:100]}..."

They replied: "{user_response}"

Put yourself in a real conversation. What would you naturally do?

If you're satisfied with their answer → say: COMPLETE
If you're still curious and would naturally ask more → create 1-2 follow-up questions

Be creative with follow-ups. Don't use standard boring questions. Think about what a real curious person would ask based on what they actually said.

FORMAT:
FOLLOWUP: [Your creative question]
FOLLOWUP: [Another creative one if needed]"""

    @staticmethod
    def dynamic_greeting_response(user_input: str, greeting_count: int, context: Dict = None) -> str:
        """Make greetings feel real and different each time"""
        conversation_history = context.get('recent_exchanges', []) if context else []
        is_final_greeting = (greeting_count + 1) >= config.GREETING_EXCHANGES

        if is_final_greeting:
            next_instruction = "Now smoothly move to asking about their work. Be natural about the transition - like how you'd really shift topics with a friend."
        else:
            next_instruction = "Just have friendly small talk. Respond to what they said like a real person would."

        return f"""You're chatting with a teammate at work. They just said: "{user_input}"

Chat so far: {conversation_history[-2:] if conversation_history else "Just started"}

{next_instruction}

BE CREATIVE AND VARIED:
- Don't use the same response style as before
- React to what they actually said
- Sound like a real person, not a template
- Keep it short (10-15 words)
- Make it feel genuine

Every response should sound different. Be original."""

    @staticmethod
    def dynamic_technical_response(context: str, user_input: str, next_question: str, session_state: Dict = None) -> str:
        """Make transitions creative and natural"""
        
        return f"""You're having a good work chat. Here's what happened:

{context}

They just said: "{user_input}"
You want to ask: "{next_question}"

Connect their response to your question in a CREATIVE way. Every transition should be different.

BE ORIGINAL:
- Don't use boring standard phrases
- Reference something specific they mentioned
- Make the connection feel natural
- Sound interested in their work
- Keep it short (max 20 words)

Make each transition unique. Think like a real curious colleague."""

    @staticmethod
    def dynamic_followup_response(current_concept_title: str, concept_content: str, 
                                 history: str, previous_question: str, user_response: str,
                                 current_question_number: int, questions_for_concept: int) -> str:
        """FIXED prompt - normal English with bullets for easy streaming"""
        
        return f"""You're a friendly team lead having standup chat with your team member. Keep it normal and conversational.

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

    @staticmethod
    def dynamic_concept_transition(user_response: str, next_question: str, progress_info: Dict) -> str:
        """Creative topic transitions"""
        
        return f"""You're moving to a new topic in your chat.

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

    @staticmethod
    def dynamic_fragment_evaluation(concepts_covered: List[str], conversation_exchanges: List[Dict],
                                   session_stats: Dict) -> str:
        """Creative evaluation like a real manager"""
        
        concepts_text = "\n".join([f"- {concept}" for concept in concepts_covered])
        
        conversation_summary = []
        for exchange in conversation_exchanges[-6:]:
            conversation_summary.append(
                f"Q: {exchange['ai_message'][:80]}...\n"
                f"A: {exchange['user_response'][:80]}...\n"
            )
        
        conversation_text = "\n".join(conversation_summary)
        
        return f"""You're a team lead writing feedback for your team member after a good standup chat.

**THEIR PERFORMANCE:**
- Topics covered: {session_stats['concepts_covered']}/{session_stats['total_concepts']} ({session_stats['coverage_percentage']}%)
- Main questions: {session_stats['main_questions']}
- Follow-ups: {session_stats['followup_questions']}  
- Time: {session_stats['duration_minutes']} minutes

**TOPICS THEY TALKED ABOUT:**
{concepts_text}

**SAMPLE CONVERSATION:**
{conversation_text}

**WRITE CREATIVE FEEDBACK**: Don't use boring template language. Write like you actually care about helping them grow.

Cover these areas creatively:
1. **Coverage**: How well they covered different topics
2. **Communication**: How clearly they explained things
3. **Strengths**: What they did really well (be specific)
4. **Growth areas**: What they can improve (be helpful)
5. **Overall**: Your honest assessment

**STYLE**: 
- Write like a real manager who cares
- Use simple English
- Be encouraging but honest
- Make it personal, not generic
- Keep under 250 words

End with: Score: X/10

Be creative and genuine in your feedback."""

    @staticmethod
    def dynamic_session_completion(conversation_summary: Dict, user_final_response: str = None) -> str:
        """End conversations creatively"""
        
        topics_discussed = conversation_summary.get('topics_covered', [])
        total_exchanges = conversation_summary.get('total_exchanges', 0)
        
        return f"""You're ending a good standup chat with your teammate.

**CHAT SUMMARY:**
- Talked about: {len(topics_discussed)} different topics
- Total questions: {total_exchanges}
- Their final words: "{user_final_response}"

**BE CREATIVE**: End this naturally like a real conversation. Don't use boring standard endings.

Think about:
- What you learned about their work
- How the conversation went
- How you'd really thank a teammate

Make it genuine and different each time. Sound like you actually enjoyed the chat.

Max 25 words. Be original."""

    @staticmethod
    def dynamic_clarification_request(context: Dict) -> str:
        """Creative clarification requests"""
        
        attempts = context.get('clarification_attempts', 0)
        
        return f"""You need them to speak more clearly.

**SITUATION**: You've asked for clarity {attempts} times already.

**BE CREATIVE**: Ask for clarification in a different way each time. Don't use the same boring phrases.

Make it:
- Natural and friendly
- Different from previous attempts  
- Not repetitive or annoying
- Understanding and patient

One creative sentence. Make it feel real."""

    @staticmethod
    def dynamic_conclusion_response(user_input: str, session_context: Dict) -> str:
        """Creative final responses"""
        
        return f"""They just said: "{user_input}"

You're wrapping up the chat about their work.

**BE CREATIVE**: Respond to what they said and end naturally. Don't use boring standard endings.

Make it:
- Personal to what they shared
- Appreciative of their time
- Natural like a real conversation ending
- Unique and genuine

Max 20 words. Be original every time."""

# Global prompts instance  
prompts = Prompts()