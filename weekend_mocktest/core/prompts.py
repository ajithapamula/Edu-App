# weekend_mocktest/core/prompts.py
from typing import List, Dict, Any
from .config import config

class PromptTemplates:
    """Optimized prompt templates for AI question generation and evaluation"""
    
    @staticmethod
    def create_batch_questions_prompt(user_type: str, context: str, question_count: int = None) -> str:
        """Create prompt for batch question generation"""
        if question_count is None:
            question_count = config.QUESTIONS_PER_TEST
        
        if user_type == "dev":
            return PromptTemplates._dev_batch_prompt(context, question_count)
        else:
            return PromptTemplates._non_dev_batch_prompt(context, question_count)
    
    @staticmethod
    def _dev_batch_prompt(context: str, question_count: int) -> str:
        """Developer interview questions generation prompt"""
        aptitude_count = int(question_count * 0.3)
        theory_count = int(question_count * 0.3)
        coding_count = question_count - aptitude_count - theory_count

        return f"""
    You are conducting a REAL developer technical interview for an MNC-level company.

    Generate EXACTLY {question_count} questions based on the provided WEEKLY developer summaries.

    CONTEXT (Weekly Developer Summaries):
    {context}

    MANDATORY QUESTION DISTRIBUTION (STRICT):
    - Exactly {aptitude_count} Aptitude / Logical problem-solving questions
    - Exactly {theory_count} Theory / Conceptual understanding questions
    - Exactly {coding_count} Coding questions

    TIME CONSTRAINTS:
    - Coding questions must be solvable in ~5 minutes
    - Aptitude questions: short, logic-based, fast to answer
    - Theory questions: concept clarity, not memorization
    - Total test duration ≈ 1 hour

    QUESTION QUALITY RULES:
    - Questions must reflect REAL interview standards (not academic)
    - Avoid trivia or definition-only questions
    - Use only technologies, concepts, and tools mentioned in the context
    - Progressive difficulty is MANDATORY
    - Each question must be complete and standalone

    CODING QUESTION RULES (VERY IMPORTANT):
    - Single-function or small logic problems only
    - No frameworks or project setup
    - No multi-file systems
    - Clearly specify:
    - Input
    - Output
    - Constraints
    - Language-agnostic unless context requires a specific language
    - Focus on problem-solving, not boilerplate

    FORMAT (STRICT — DO NOT CHANGE):

    === QUESTION 1 ===
    ## Title: [Short, clear title]
    ## Difficulty: [Easy / Medium / Hard]
    ## Type: [Aptitude / Theory / Coding]
    ## Question:
    [Complete question description]

    === QUESTION 2 ===
    ## Title: ...
    ## Difficulty: ...
    ## Type: ...
    ## Question:
    ...

    Continue this EXACT format for all {question_count} questions.

    IMPORTANT RULES (NO EXCEPTIONS):
    - Do NOT include answers
    - Do NOT include hints or explanations
    - Do NOT repeat questions
    - Do NOT mention percentages or distribution in output
    - Coding questions MUST be concise and time-bound
    - Ensure the distribution EXACTLY matches the counts above

    Generate all {question_count} questions now.
    """

    @staticmethod
    def _non_dev_batch_prompt(context: str, question_count: int) -> str:
        """Non-developer MCQ-only interview questions generation prompt"""
        return f"""
    You are conducting a REAL non-developer interview (QA / BA / Analyst / Functional roles).
    Generate EXACTLY {question_count} high-quality MULTIPLE-CHOICE QUESTIONS (MCQs)
    based strictly on the provided weekly summaries.

    CONTEXT (Weekly Summaries from MongoDB):
    {context}

    MANDATORY RULES (NO EXCEPTIONS):
    - ALL questions MUST be MCQs
    - EACH question MUST have exactly 4 options (A, B, C, D)
    - ONLY ONE option must be correct
    - NO descriptive answers
    - NO coding questions
    - NO open-ended questions

    QUESTION DISTRIBUTION:
    - Aptitude / Logical reasoning → ~30%
    - Theory / Conceptual understanding → ~40%
    - Process / Scenario-based decision making → ~30%

    QUESTION GUIDELINES:
    - Questions must reflect real workplace understanding
    - Prefer “best choice” questions over factual recall
    - Distractors must be realistic and commonly mistaken options
    - Avoid guessable or trivial questions
    - Use concepts mentioned in the context only

    FORMAT (STRICT — DO NOT CHANGE):

    === QUESTION 1 ===
    ## Title: [Short, clear title]
    ## Difficulty: [Easy / Medium / Hard]
    ## Type: [Aptitude / Theory / Process]
    ## Question:
    [Clear and precise MCQ question]
    ## Options:
    A) [Option A]
    B) [Option B]
    C) [Option C]
    D) [Option D]

    === QUESTION 2 ===
    ## Title: ...
    ## Difficulty: ...
    ## Type: ...
    ## Question:
    ...
    ## Options:
    A) ...
    B) ...
    C) ...
    D) ...

    Continue this EXACT format for all {question_count} questions.

    IMPORTANT:
    - Do NOT mention summaries, MongoDB, or context source
    - Do NOT add explanations
    - Do NOT reveal the correct answer
    - Keep language professional and interview-appropriate
    - Maintain progressive difficulty

    Generate all {question_count} MCQ questions now.
    """

    @staticmethod
    def _dev_evaluation_prompt(qa_content: str, question_count: int) -> str:
        """Developer answers evaluation prompt"""
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
        """Non-developer answers evaluation prompt"""
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
    def create_evaluation_prompt(user_type: str, qa_pairs: List[Dict[str, Any]]) -> str:
        question_count = len(qa_pairs)

        formatted = []
        for i, qa in enumerate(qa_pairs, 1):
            q = qa.get("question", "")
            a = qa.get("answer", "")
            formatted.append(f"QUESTION {i}:\n{q}\n\nANSWER:\n{a}")

        qa_content = "\n\n".join(formatted)

        if user_type == "dev":
            return PromptTemplates._dev_evaluation_prompt(qa_content, question_count)
        else:
            return PromptTemplates._non_dev_evaluation_prompt(qa_content, question_count)


    @staticmethod
    def optimize_context_prompt(context: str) -> str:
        """Optimize context for better question generation"""
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
        """Validate question generation response"""
        validation = {
            "valid": True,
            "issues": [],
            "question_count": 0,
            "format_correct": True
        }
        
        # Count questions
        question_markers = response.count("=== QUESTION")
        validation["question_count"] = question_markers
        
        if question_markers != expected_count:
            validation["valid"] = False
            validation["issues"].append(f"Expected {expected_count} questions, found {question_markers}")
        
        # Check required sections
        required_sections = ["## Title:", "## Difficulty:", "## Type:", "## Question:"]
        if user_type == "non_dev":
            required_sections.append("## Options:")
        
        for section in required_sections:
            if response.count(section) < expected_count:
                validation["valid"] = False
                validation["issues"].append(f"Missing {section} sections")
        
        # Check format consistency
        if user_type == "non_dev":
            option_patterns = [f"{letter})" for letter in "ABCD"]
            for pattern in option_patterns:
                if response.count(pattern) < expected_count:
                    validation["format_correct"] = False
                    validation["issues"].append(f"Inconsistent option format: {pattern}")
        
        return validation
    

    @staticmethod
    def validate_evaluation_response(response: str, expected_count: int) -> Dict[str, Any]:
        """Validate evaluation response"""
        validation = {
            "valid": True,
            "issues": [],
            "has_scores": False,
            "has_feedback": False,
            "score_count": 0
        }
        
        # Check for scores
        if "SCORES:" in response:
            validation["has_scores"] = True
            # Extract and count scores
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
        
        # Check for feedback
        if "FEEDBACK:" in response:
            validation["has_feedback"] = True
        else:
            validation["valid"] = False
            validation["issues"].append("Missing FEEDBACK section")
        
        return validation