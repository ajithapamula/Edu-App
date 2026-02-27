# weekend_mocktest/core/prompts.py
# FIXED: Questions generated from MongoDB summaries, NO hard-coded questions
# Non-dev: STRICTLY blocks Python/programming content
# UPDATED: Coding questions now generate TEST CASES (HackerRank-style)
from typing import List, Dict, Any
from .config import config


class PromptTemplates:
    """
    Prompt templates for AI question generation.
    
    IMPORTANT:
    - Questions are generated from MongoDB summaries (context parameter)
    - NO hard-coded questions
    - Non-dev: NO Python/programming questions
    - Coding questions now include test cases for Piston execution
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

    # ================================================================
    # DEVELOPER CODING — WITH TEST CASES (HackerRank-style)
    # ================================================================

    @staticmethod
    def _dev_coding_prompt(context: str, count: int) -> str:
        """Developer coding - Python problems with test cases for Piston execution"""
        return f"""Generate exactly {count} Python coding problems with test cases, like HackerRank.

=== COURSE CONTENT ===
{context}
=== END CONTENT ===

Create practical Python coding problems testing concepts from the content.

RULES:
1. Program MUST read from stdin using input() and print output using print()
2. Each problem MUST have 4-6 test cases with EXACT input and expected output
3. Include 2 VISIBLE test cases (shown to student) and 2-4 HIDDEN test cases (for final grading)
4. Test cases MUST be deterministic (same input = same output always)
5. Keep problems beginner to intermediate level

FORMAT (follow EXACTLY):

=== QUESTION 1 ===
## Title: Sum of Two Numbers
## Difficulty: Easy
## Type: coding
## Question:
Write a Python program that reads two integers from input (one per line) and prints their sum.

**Input Format:**
- Line 1: First integer
- Line 2: Second integer

**Output Format:**
- A single integer: the sum

**Example:**
Input:
3
5
Output:
8

## TestCases:
TC1|VISIBLE|3\\n5|8
TC2|VISIBLE|10\\n20|30
TC3|HIDDEN|0\\n0|0
TC4|HIDDEN|-5\\n10|5
TC5|HIDDEN|1000\\n2000|3000

══════════════════════════════════════════════════════════════════
TEST CASE FORMAT RULES:
══════════════════════════════════════════════════════════════════
- Each line: TC<number>|VISIBLE or HIDDEN|<input>|<expected_output>
- Use \\n for newlines in input (e.g., 3\\n5 means two lines: 3 and 5)
- Expected output = EXACT print() output (what Python prints)
- No trailing spaces or extra newlines
- VISIBLE = shown to student during practice
- HIDDEN = only used during final submission grading
- First 2 test cases MUST be VISIBLE, rest HIDDEN
- Include edge cases in HIDDEN (zero, negative, large numbers, empty)

Generate exactly {count} coding problems with === QUESTION N === markers.
Each problem MUST have a ## TestCases: section."""

    # ================================================================
    # STANDALONE TEST CASE GENERATION
    # (for existing coding questions that don't have test cases yet)
    # ================================================================

    @staticmethod
    def create_test_cases_prompt(question: str, num_cases: int = 5) -> str:
        """Generate test cases for an existing coding question that has none"""
        return f"""Generate exactly {num_cases} test cases for this coding problem.

CODING QUESTION:
{question}

RULES:
1. Program reads from stdin using input() and writes to stdout using print()
2. Test cases must be deterministic (same input = same output)
3. Include edge cases (empty input, zero, negative numbers, large values)
4. First 2 test cases = VISIBLE (shown to student)
5. Remaining test cases = HIDDEN (for final grading only)
6. Expected output = EXACT output of print() statement

FORMAT (output ONLY these lines, nothing else):
TC1|VISIBLE|<input>|<expected_output>
TC2|VISIBLE|<input>|<expected_output>
TC3|HIDDEN|<input>|<expected_output>
TC4|HIDDEN|<input>|<expected_output>
TC5|HIDDEN|<input>|<expected_output>

Use \\n for multi-line input (e.g., 3\\n5 means line 1 is 3, line 2 is 5).
Output ONLY the TC lines. No explanations, no code blocks, no extra text."""

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
        return f"""You are an expert SAP/Business instructor. Generate exactly {count} MCQ questions STRICTLY based on the summary content provided below.

══════════════════════════════════════════════════════════════════
CRITICAL RULE: ALL QUESTIONS MUST COME FROM THE SUMMARY BELOW!
- Read the summary carefully
- Extract ALL key facts, numbers, T-codes, terms, processes
- Create questions that test knowledge of THAT SPECIFIC content
- Do NOT create generic business questions
══════════════════════════════════════════════════════════════════

FORBIDDEN (never use):
❌ "What is the primary goal of...?"
❌ "What is the main purpose of...?"
❌ Generic options like "maximize/minimize/optimize X"
❌ Python, Java, coding, programming questions

══════════════════════════════════════════════════════════════════
HOW TO CREATE QUESTIONS FROM THE SUMMARY:
══════════════════════════════════════════════════════════════════

Step 1: EXTRACT from summary:
- Definitions (What is X?)
- Numbers/Ranges (How many? What range?)
- T-codes/Transactions (Which T-code for X?)
- Types/Categories (What are the types of X?)
- Steps/Processes (What is step 1/2/3?)
- Tools/Prerequisites (What is required for X?)
- Best Practices (Why is X recommended?)
- Troubleshooting (What causes X? How to fix?)

Step 2: CREATE one question for each extracted fact

Example - If summary says:
"SAP supports up to 1,000 clients per system, identified by a three-digit number ranging from 000 to 999"

Generate questions like:
- "How many clients can SAP support per system?" → Answer: 1,000
- "What is the valid range for SAP client numbers?" → Answer: 000 to 999
- "How many digits are used to identify an SAP client?" → Answer: Three digits

Example - If summary says:
"Use T-code SCC4 to access client administration"

Generate:
- "Which transaction code is used for client administration?" → Answer: SCC4
- "What is T-code SCC4 used for?" → Answer: Client administration

══════════════════════════════════════════════════════════════════
SUMMARY CONTENT (Generate questions ONLY from this):
══════════════════════════════════════════════════════════════════
{context}
══════════════════════════════════════════════════════════════════

FORMAT (follow exactly):

=== QUESTION 1 ===
## Title: [Topic from summary]
## Difficulty: Easy
## Type: mcq
## Question:
[Question based on SPECIFIC fact from summary above]
## Options:
A) [Correct or incorrect specific answer]
B) [Correct or incorrect specific answer]
C) [Correct or incorrect specific answer]
D) [Correct or incorrect specific answer]
## Correct: [A/B/C/D]

=== QUESTION 2 ===
...continue...

Generate exactly {count} questions using === QUESTION N === markers.

CHECKLIST before responding:
✓ Every question is based on a SPECIFIC fact from the summary
✓ No two questions test the same concept
✓ If summary has numbers → include number questions
✓ If summary has T-codes → include T-code questions  
✓ If summary has types/categories → include type questions
✓ If summary has steps → include 1-2 process questions (not more)
✓ If summary has troubleshooting → include troubleshooting questions
✓ If summary has best practices → include best practice questions
✓ NO "primary goal" or "main purpose" questions
✓ Options are specific facts, not vague phrases"""

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