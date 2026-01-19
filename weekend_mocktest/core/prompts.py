# weekend_mocktest/core/prompts.py
# FIXED: Questions generated from MongoDB summaries, NO hard-coded questions
# Non-dev: STRICTLY blocks Python/programming content
from typing import List, Dict, Any
from .config import config


class PromptTemplates:
    """
    Prompt templates for AI question generation.
    
    IMPORTANT:
    - Questions are generated from MongoDB summaries (context parameter)
    - NO hard-coded questions
    - Non-dev: NO Python/programming questions
    """

    @staticmethod
    def create_bank_generation_prompt(user_type: str, question_type: str,
                                      context: str, count: int) -> str:
        """Create prompt for generating questions from MongoDB summaries"""
        
        if user_type == "dev":
            if question_type == "aptitude":
                return PromptTemplates._dev_aptitude_prompt(count)
            elif question_type == "mcq":
                return PromptTemplates._dev_mcq_prompt(context, count)
            elif question_type == "coding":
                return PromptTemplates._dev_coding_prompt(context, count)
        else:
            # NON-DEVELOPER: Only aptitude and mcq, NO CODING EVER
            if question_type == "aptitude":
                return PromptTemplates._non_dev_aptitude_prompt(count)
            elif question_type == "mcq":
                return PromptTemplates._non_dev_mcq_prompt(context, count)
            else:
                # If somehow coding is requested for non-dev, return empty
                return ""
        
        return ""

    # ================================================================
    # DEVELOPER PROMPTS
    # ================================================================
    
    @staticmethod
    def _dev_aptitude_prompt(count: int) -> str:
        """Developer aptitude - general math/logic (no context needed)"""
        return f"""Generate exactly {count} aptitude MCQ questions.

These are GENERAL aptitude questions - math, logic, reasoning.
NOT programming questions.

Topics: Number series, Percentages, Profit/Loss, Time/Work, Ratios, Averages, Logical reasoning.

FORMAT (follow exactly):

=== QUESTION 1 ===
## Title: Number Series
## Difficulty: Easy
## Type: aptitude
## Question:
What is the next number: 2, 6, 12, 20, 30, ?
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
If price increases from Rs.200 to Rs.250, what is the percentage increase?
## Options:
A) 20%
B) 25%
C) 30%
D) 15%
## Correct: B

Generate {count} different aptitude questions with === QUESTION N === markers.
Each must have 4 options (A, B, C, D) and one correct answer."""

    @staticmethod
    def _dev_mcq_prompt(context: str, count: int) -> str:
        """Developer MCQ - from Python/programming summaries"""
        return f"""Generate exactly {count} MCQ questions based on this course content:

=== COURSE CONTENT (from MongoDB summaries) ===
{context}
=== END CONTENT ===

Create questions that test understanding of the content above.
Questions should be about Python, programming concepts mentioned in the content.

FORMAT:

=== QUESTION 1 ===
## Title: [Topic from content]
## Difficulty: Easy
## Type: mcq
## Question:
[Question based on the content above]
## Options:
A) [Option]
B) [Option]
C) [Option]
D) [Option]
## Correct: [A/B/C/D]

Generate {count} MCQ questions from the content. Use === QUESTION N === markers."""

    @staticmethod
    def _dev_coding_prompt(context: str, count: int) -> str:
        """Developer coding - Python problems from summaries"""
        return f"""Generate exactly {count} Python coding problems based on this content:

=== COURSE CONTENT ===
{context}
=== END CONTENT ===

Create practical Python coding problems testing concepts from the content.

FORMAT:

=== QUESTION 1 ===
## Title: [Problem Name]
## Difficulty: Easy
## Type: coding
## Question:
Write a Python function/program to [problem description].

**Input:** [describe]
**Output:** [describe]
**Example:** Input: [x] → Output: [y]

Generate {count} coding problems with === QUESTION N === markers."""

    # ================================================================
    # NON-DEVELOPER PROMPTS - NO PYTHON/PROGRAMMING!
    # ================================================================

    @staticmethod
    def _non_dev_aptitude_prompt(count: int) -> str:
        """Non-dev aptitude - general math/logic, NO programming"""
        return f"""Generate exactly {count} aptitude MCQ questions.

RULES:
- General aptitude only: math, logic, reasoning
- NO programming, coding, Python, Java questions
- NO technical IT questions

Topics: Number series, Percentages, Profit/Loss, Time/Work, Ratios, Age problems, Speed/Distance.

FORMAT:

=== QUESTION 1 ===
## Title: Number Series
## Difficulty: Easy
## Type: aptitude
## Question:
Find the next number: 3, 9, 27, 81, ?
## Options:
A) 162
B) 243
C) 324
D) 108
## Correct: B

=== QUESTION 2 ===
## Title: Percentage
## Difficulty: Medium
## Type: aptitude
## Question:
A shopkeeper buys an item for Rs.400 and sells for Rs.500. What is the profit percentage?
## Options:
A) 20%
B) 25%
C) 30%
D) 15%
## Correct: B

Generate {count} aptitude questions. Use === QUESTION N === markers.
Each must have 4 options and one correct answer.
DO NOT include any programming questions."""

    @staticmethod
    def _non_dev_mcq_prompt(context: str, count: int) -> str:
        """Non-dev MCQ - from SAP/Business summaries, NO PYTHON"""
        return f"""Generate exactly {count} MCQ questions for NON-TECHNICAL professionals.

╔════════════════════════════════════════════════════════════════╗
║  CRITICAL: ABSOLUTELY NO PROGRAMMING QUESTIONS!                 ║
║                                                                 ║
║  FORBIDDEN (do not mention):                                    ║
║  - Python, Java, JavaScript, C++, any programming language      ║
║  - Coding, functions, variables, loops, arrays, classes         ║
║  - GIL, interpreter, compiler, debugging, syntax                ║
║  - Algorithms, data structures, API                             ║
║                                                                 ║
║  If content below has programming topics, SKIP them completely! ║
╚════════════════════════════════════════════════════════════════╝

ONLY create questions about:
- SAP modules (MM, SD, FICO, HR, PP)
- Business processes, ERP concepts
- Sales, procurement, inventory, finance, HR
- Management, organizational topics
- Any NON-PROGRAMMING topics from the content

=== COURSE CONTENT (from MongoDB summaries) ===
{context}
=== END CONTENT ===

FORMAT:

=== QUESTION 1 ===
## Title: [Business/SAP Topic]
## Difficulty: Easy
## Type: mcq
## Question:
[Question about business/SAP - NOT programming]
## Options:
A) [Option]
B) [Option]
C) [Option]
D) [Option]
## Correct: [A/B/C/D]

Generate {count} business/SAP MCQ questions.
Use === QUESTION N === markers.
If no valid non-programming content, create general business questions.

FINAL CHECK: Delete any question mentioning Python, coding, functions, or programming!"""

    # ================================================================
    # EVALUATION PROMPTS
    # ================================================================

    @staticmethod
    def create_section_evaluation_prompt(section_type: str, qa_pairs: List[Dict[str, Any]]) -> str:
        """Create evaluation prompt for a section"""
        question_count = len(qa_pairs)
        
        formatted = []
        for i, qa in enumerate(qa_pairs, 1):
            q = qa.get("question", "")
            a = qa.get("answer", "")
            options = qa.get("options", [])
            correct = qa.get("correct_answer") or qa.get("correct_option_text", "")
            
            opts_str = ""
            if options:
                for j, opt in enumerate(options):
                    opts_str += f"\n   {chr(65+j)}) {opt}"
            
            formatted.append(f"""
QUESTION {i}:
{q}{opts_str}

CORRECT ANSWER: {correct}
USER'S ANSWER: {a if a and a.strip() else "[NO ANSWER]"}
""")
        
        qa_content = "\n".join(formatted)
        
        return f"""Evaluate these {section_type.upper()} answers.

{qa_content}

SCORING:
- Compare USER'S ANSWER with CORRECT ANSWER
- Score 1 if correct, 0 if wrong or no answer

OUTPUT FORMAT (required):
SCORES: [{','.join(['0 or 1'] * question_count)}]

Example: SCORES: [1, 0, 1, 1, 0]

Evaluate all {question_count} questions now:"""

    @staticmethod
    def create_evaluation_prompt(user_type: str, qa_pairs: List[Dict[str, Any]]) -> str:
        """Create full evaluation prompt"""
        question_count = len(qa_pairs)

        formatted = []
        for i, qa in enumerate(qa_pairs, 1):
            q = qa.get("question", "")
            a = qa.get("answer", "")
            q_type = qa.get("question_type", "mcq")
            correct = qa.get("correct_answer") or qa.get("correct_option_text", "")
            formatted.append(f"""
Q{i} [{q_type.upper()}]:
{q}
CORRECT: {correct}
USER ANSWER: {a if a else "[BLANK]"}
""")

        qa_content = "\n---\n".join(formatted)

        return f"""Evaluate this test.

{qa_content}

SCORING: 1 = Correct, 0 = Wrong/Blank

OUTPUT FORMAT:
SCORES: [{','.join(['0 or 1'] * question_count)}]

Evaluate all {question_count} questions:"""