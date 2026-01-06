# weekend_mocktest/core/prompts.py
# Changed: theory -> mcq throughout
from typing import List, Dict, Any
from .config import config


class PromptTemplates:
    """
    Optimized prompt templates for AI question generation and evaluation.
    Developer exam: aptitude, mcq, coding
    Non-developer exam: aptitude + MCQ
    """

    @staticmethod
    def create_bank_generation_prompt(user_type: str, question_type: str,
                                      context: str, count: int) -> str:
        """Create prompt for generating questions for the question bank"""
        
        if user_type == "dev":
            if question_type == "aptitude":
                return PromptTemplates._dev_aptitude_bank_prompt(context, count)
            elif question_type == "mcq":  # Changed from theory
                return PromptTemplates._dev_mcq_bank_prompt(context, count)
            elif question_type == "coding":
                return PromptTemplates._dev_coding_bank_prompt(context, count)
        else:
            if question_type == "aptitude":
                return PromptTemplates._non_dev_aptitude_bank_prompt(count)
            else:
                return PromptTemplates._non_dev_mcq_bank_prompt(context, count)
        
        raise ValueError(f"Unknown question type: {question_type}")
    
    @staticmethod
    def _non_dev_aptitude_bank_prompt(count: int) -> str:
        """Generate aptitude questions for non-developer"""
        return f"""Generate {count} aptitude and logical reasoning questions for a professional assessment.

These are GENERAL aptitude questions (not course-specific).

QUESTION TYPES TO INCLUDE:
1. Number series and patterns
2. Logical reasoning (if-then statements)
3. Percentage and ratio problems
4. Time and work problems
5. Simple data interpretation
6. Verbal reasoning (analogies, odd one out)
7. Basic arithmetic word problems

FORMAT FOR EACH QUESTION:

=== QUESTION 1 ===
## Title: Number Series
## Difficulty: Easy
## Type: aptitude
## Question:
What is the next number in the series: 2, 6, 12, 20, 30, ?
## Options:
A) 40
B) 42
C) 44
D) 36
## Correct: B

=== QUESTION 2 ===
## Title: Percentage
## Difficulty: Medium
## Type: aptitude
## Question:
If a product's price increased from Rs. 200 to Rs. 250, what is the percentage increase?
## Options:
A) 20%
B) 25%
C) 30%
D) 50%
## Correct: B

Continue for all {count} questions.

DIFFICULTY MIX:
- Easy (40%): Simple calculations, direct patterns
- Medium (40%): Multi-step problems
- Hard (20%): Complex reasoning

RULES:
✓ Each question must have 4 options with exactly 1 correct answer
✓ Questions should be solvable in ~1 minute
✓ Use realistic numbers and scenarios
✓ Include variety of question types

Generate {count} aptitude questions now:"""
    
    @staticmethod
    def _dev_aptitude_bank_prompt(context: str, count: int) -> str:
        """Generate aptitude questions for developer bank - GENERAL not from content"""
        return f"""Generate {count} aptitude and logical reasoning MCQ questions.

IMPORTANT: These are GENERAL aptitude questions - math, logic, reasoning only.
Do NOT include programming, coding, or any technical questions.

Topics to cover:
1. Number Series (patterns)
2. Percentage calculations
3. Profit & Loss
4. Time & Work
5. Ratio & Proportion
6. Simple/Compound Interest
7. Age Problems
8. Averages
9. Logical Reasoning
10. Odd One Out

STRICT FORMAT - Follow exactly:

=== QUESTION 1 ===
## Title: Number Series
## Difficulty: Easy
## Type: aptitude
## Question:
What is the next number in the series: 2, 6, 12, 20, 30, ?
## Options:
A) 40
B) 42
C) 44
D) 36
## Correct: B

=== QUESTION 2 ===
## Title: Percentage
## Difficulty: Medium
## Type: aptitude
## Question:
If the price of an item increases from Rs. 200 to Rs. 250, what is the percentage increase?
## Options:
A) 20%
B) 25%
C) 30%
D) 15%
## Correct: B

Generate exactly {count} aptitude MCQ questions following this EXACT format.
Each question MUST have exactly 4 options (A, B, C, D) and one correct answer.
Use === QUESTION N === markers for each question."""

    @staticmethod
    def _dev_mcq_bank_prompt(context: str, count: int) -> str:
        """Generate MCQ questions from course content for developer bank (renamed from theory)"""
        return f"""Generate {count} multiple choice questions based on this content:

=== CONTENT START ===
{context}
=== CONTENT END ===

Create questions that test understanding of the content above.
Each question MUST have exactly 4 options with 1 correct answer.

STRICT FORMAT - Follow exactly:

=== QUESTION 1 ===
## Title: [Topic from content]
## Difficulty: Easy
## Type: mcq
## Question:
[Question about the content]
## Options:
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
## Correct: [A/B/C/D]

=== QUESTION 2 ===
## Title: [Another topic]
## Difficulty: Medium
## Type: mcq
## Question:
[Another question]
## Options:
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
## Correct: [A/B/C/D]

Generate exactly {count} MCQ questions from the content.
Use === QUESTION N === markers for each question.
Each question MUST have exactly 4 options (A, B, C, D)."""

    @staticmethod
    def _dev_coding_bank_prompt(context: str, count: int) -> str:
        """Generate coding questions for developer bank"""
        return f"""Generate {count} coding problems based on this content:

=== CONTENT START ===
{context}
=== CONTENT END ===

Create practical coding problems that test the concepts in the content.

STRICT FORMAT - Follow exactly:

=== QUESTION 1 ===
## Title: [Problem Name]
## Difficulty: Easy
## Type: coding
## Question:
[Problem description with clear requirements]

**Input Format:** [describe input]
**Output Format:** [describe output]

**Example:**
Input: [example input]
Output: [expected output]

**Constraints:**
- [constraint 1]
- [constraint 2]

=== QUESTION 2 ===
## Title: [Another Problem]
## Difficulty: Medium
## Type: coding
## Question:
[Another problem description]

Generate exactly {count} coding problems using === QUESTION N === markers."""

    @staticmethod
    def _non_dev_mcq_bank_prompt(context: str, count: int) -> str:
        """Generate MCQ questions from content for non-developer"""
        return f"""Generate {count} multiple choice questions.

FORMAT - Use this exact format for each question:

=== QUESTION 1 ===
## Title: [Topic]
## Difficulty: Easy
## Type: mcq
## Question: [Your question here]
## Options:
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
## Correct: [A/B/C/D]

=== QUESTION 2 ===
## Title: [Topic]
## Difficulty: Medium
## Type: mcq
## Question: [Your question here]
## Options:
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
## Correct: [A/B/C/D]

RULES:
- Create questions ONLY from the content below
- Ask about specific facts, terms, codes, numbers mentioned
- Do NOT create generic questions
- Each question needs exactly 4 options
- Only 1 correct answer per question

Now read this content and create {count} questions about it:

=== CONTENT START ===
{context}
=== CONTENT END ===

Create {count} MCQ questions about the content above. Start with "=== QUESTION 1 ===" now:"""

    @staticmethod
    def create_batch_questions_prompt(user_type: str, context: str, question_count: int = None) -> str:
        """Create prompt for batch question generation (legacy)"""
        if question_count is None:
            question_count = config.QUESTIONS_PER_TEST
        
        if user_type == "dev":
            return PromptTemplates._dev_batch_prompt(context, question_count)
        else:
            return PromptTemplates._non_dev_batch_prompt(context, question_count)
    
    @staticmethod
    def _dev_batch_prompt(context: str, question_count: int) -> str:
        """Developer interview questions generation prompt"""
        aptitude_count = config.DEV_APTITUDE_COUNT
        mcq_count = config.DEV_MCQ_COUNT
        coding_count = config.DEV_CODING_COUNT
        total = aptitude_count + mcq_count + coding_count

        return f"""Generate EXACTLY {total} questions based on the provided content.

CONTEXT:
{context}

MANDATORY QUESTION DISTRIBUTION:
- Exactly {aptitude_count} Aptitude questions
- Exactly {mcq_count} MCQ questions (from content)
- Exactly {coding_count} Coding questions

FORMAT:

=== QUESTION 1 ===
## Title: [Title]
## Difficulty: [Easy/Medium/Hard]
## Type: [Aptitude/MCQ/Coding]
## Question:
[Complete question]
## Options: (for MCQ/Aptitude)
A) [Option]
B) [Option]
C) [Option]
D) [Option]
## Correct: [A/B/C/D]

Generate all {total} questions now:"""

    @staticmethod
    def _non_dev_batch_prompt(context: str, question_count: int) -> str:
        """Non-developer MCQ generation prompt"""
        return f"""Generate EXACTLY {question_count} MCQs for non-developer assessment.

CONTEXT:
{context}

RULES:
- ALL questions must be MCQs with 4 options (A, B, C, D)
- Only ONE correct answer

FORMAT:

=== QUESTION 1 ===
## Title: [Title]
## Difficulty: [Easy/Medium/Hard]
## Type: mcq
## Question:
[MCQ question]
## Options:
A) [Option]
B) [Option]
C) [Option]
D) [Option]
## Correct: [A/B/C/D]

Generate {question_count} questions now:"""

    @staticmethod
    def create_section_evaluation_prompt(section_type: str, qa_pairs: List[Dict[str, Any]]) -> str:
        """Create evaluation prompt for specific section type"""
        question_count = len(qa_pairs)
        
        formatted = []
        for i, qa in enumerate(qa_pairs, 1):
            q = qa.get("question", "")
            a = qa.get("answer", "")
            formatted.append(f"""
QUESTION {i}:
{q}

USER'S ANSWER:
{a if a.strip() else "[NO ANSWER]"}
""")
        
        qa_content = "\n".join(formatted)
        
        if section_type == "aptitude":
            return PromptTemplates._aptitude_evaluation_prompt(qa_content, question_count)
        elif section_type == "mcq":
            return PromptTemplates._mcq_evaluation_prompt(qa_content, question_count)
        elif section_type == "coding":
            return PromptTemplates._coding_evaluation_prompt(qa_content, question_count)
        else:
            return PromptTemplates._general_evaluation_prompt(qa_content, question_count)
    
    @staticmethod
    def _aptitude_evaluation_prompt(qa_content: str, question_count: int) -> str:
        """Evaluation prompt for APTITUDE section"""
        return f"""Evaluate the user's aptitude answers.

{qa_content}

For EACH question:
1. Calculate the CORRECT answer
2. Compare with USER'S answer
3. Score: 1 if correct, 0 if wrong

OUTPUT FORMAT:
SCORES: [{','.join(['0 or 1'] * question_count)}]

FEEDBACK for each question explaining correct answer.

Evaluate now:"""

    @staticmethod
    def _mcq_evaluation_prompt(qa_content: str, question_count: int) -> str:
        """Evaluation prompt for MCQ section"""
        return f"""Evaluate the user's MCQ answers.

{qa_content}

For EACH question:
1. Identify the CORRECT answer
2. Compare with USER'S answer
3. Score: 1 if correct, 0 if wrong

OUTPUT FORMAT:
SCORES: [{','.join(['0 or 1'] * question_count)}]

FEEDBACK for each question explaining correct answer.

Evaluate now:"""

    @staticmethod
    def _coding_evaluation_prompt(qa_content: str, question_count: int) -> str:
        """Evaluation prompt for CODING section"""
        return f"""Evaluate the user's code.

{qa_content}

For EACH question:
1. Check if code would work correctly
2. Score: 1 if code would work, 0 if wrong logic

OUTPUT FORMAT:
SCORES: [{','.join(['0 or 1'] * question_count)}]

FEEDBACK for each question explaining issues or confirming correctness.

Evaluate now:"""

    @staticmethod
    def _general_evaluation_prompt(qa_content: str, question_count: int) -> str:
        """General evaluation prompt fallback"""
        return f"""Evaluate these answers.

{qa_content}

SCORING: 1 = Correct, 0 = Incorrect

OUTPUT FORMAT:
SCORES: [{','.join(['0 or 1'] * question_count)}]

Evaluate all {question_count} questions:"""

    @staticmethod
    def create_evaluation_prompt(user_type: str, qa_pairs: List[Dict[str, Any]]) -> str:
        """Create evaluation prompt for submitted answers"""
        question_count = len(qa_pairs)

        formatted = []
        for i, qa in enumerate(qa_pairs, 1):
            q = qa.get("question", "")
            a = qa.get("answer", "")
            q_type = qa.get("question_type", "unknown")
            formatted.append(f"QUESTION {i} [{q_type.upper()}]:\n{q}\n\nANSWER:\n{a}")

        qa_content = "\n\n---\n\n".join(formatted)

        return f"""Evaluate this assessment.

{qa_content}

SCORING RULES:
- 1 = Correct
- 0 = Incorrect

REQUIRED OUTPUT FORMAT:
SCORES: [{','.join(['0 or 1'] * question_count)}]
FEEDBACK: [Q1 feedback|Q2 feedback|...]

Evaluate all {question_count} questions:"""


class PromptValidator:
    """Validation utilities for prompts and responses"""
    
    @staticmethod
    def validate_question_response(response: str, user_type: str, expected_count: int) -> Dict[str, Any]:
        """Validate question generation response"""
        import re
        
        validation = {
            "valid": True,
            "issues": [],
            "question_count": 0,
            "format_correct": True
        }
        
        question_markers = response.count("=== QUESTION")
        validation["question_count"] = question_markers
        
        if question_markers < expected_count:
            validation["valid"] = False
            validation["issues"].append(f"Expected {expected_count} questions, found {question_markers}")
        
        return validation
    
    @staticmethod
    def validate_evaluation_response(response: str, expected_count: int) -> Dict[str, Any]:
        """Validate evaluation response"""
        import re
        
        validation = {
            "valid": True,
            "issues": [],
            "has_scores": False,
            "score_count": 0
        }
        
        if "SCORES:" in response:
            validation["has_scores"] = True
            score_match = re.search(r'SCORES:\s*\[(.*?)\]', response)
            if score_match:
                scores = score_match.group(1).split(',')
                validation["score_count"] = len([s for s in scores if s.strip() in ['0', '1']])
        else:
            validation["valid"] = False
            validation["issues"].append("Missing SCORES section")
        
        return validation