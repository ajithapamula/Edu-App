# weekend_mocktest/core/prompts.py
from typing import List, Dict, Any
from .config import config


class PromptTemplates:

    @staticmethod
    def create_bank_generation_prompt(user_type: str, question_type: str,
                                      context: str, count: int) -> str:
        if user_type == "dev":
            if question_type == "aptitude":
                return PromptTemplates._dev_aptitude_prompt(count)
            elif question_type == "mcq":
                return PromptTemplates._dev_mcq_prompt(context, count)
            elif question_type == "coding":
                return PromptTemplates._dev_coding_prompt(context, count)
        else:
            if question_type == "aptitude":
                return PromptTemplates._non_dev_aptitude_prompt(count)
            elif question_type == "mcq":
                return PromptTemplates._non_dev_mcq_prompt(context, count)
            else:
                return ""
        return ""

    # ════════════════════════════════════════════════════════════
    # DEVELOPER APTITUDE
    # ════════════════════════════════════════════════════════════

    @staticmethod
    def _dev_aptitude_prompt(count: int) -> str:
        return f"""Generate exactly {count} aptitude MCQ questions.

GENERAL aptitude only — math, logic, reasoning. NOT programming.

Topics: Number series, Percentages, Profit/Loss, Time/Work, Ratios, Averages, Logical reasoning.

══════════════════════════════════════════════════════════════════
CRITICAL — MATHEMATICAL ACCURACY:
══════════════════════════════════════════════════════════════════
For EVERY question:
1. Solve step-by-step BEFORE writing options
2. Verify answer is mathematically correct
3. Plug answer back into problem to verify
4. Correct option MUST exactly match your calculated answer
5. All 4 options must be distinct — no duplicates
6. NEVER repeat a question concept already used in this batch

COMMON MISTAKES TO AVOID:
❌ Saying average is 35 when calculation gives 36
❌ Correct answer not matching any option
❌ Division errors
❌ Ratio parts not adding up to total
══════════════════════════════════════════════════════════════════

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

Generate {count} DIFFERENT aptitude questions. Each question must test a DIFFERENT concept.
CRITICAL: Start IMMEDIATELY with === QUESTION 1 ===. No introduction."""

    # ════════════════════════════════════════════════════════════
    # DEVELOPER MCQ — CONTENT-SPECIFIC, NO GENERIC QUESTIONS
    # ════════════════════════════════════════════════════════════

    @staticmethod
    def _dev_mcq_prompt(context: str, count: int) -> str:
        return f"""Generate exactly {count} MCQ questions based STRICTLY on this course content.

=== COURSE CONTENT ===
{context}
=== END CONTENT ===

══════════════════════════════════════════════════════════════════
ABSOLUTE RULES — VIOLATIONS WILL MAKE QUESTIONS USELESS:
══════════════════════════════════════════════════════════════════

RULE 1 — EVERY question must test a SPECIFIC fact from the content above.
RULE 2 — NO two questions can test the same concept. All {count} must be unique.
RULE 3 — Options must be specific technical facts, not vague phrases.

COMPLETELY BANNED — do NOT generate any of these:
❌ "What is the purpose of [language/loop/function/class/method]?"
❌ "What is the main focus/goal/benefit of [language]?"
❌ "What is a good practice for [anything]?"
❌ "Why is it important to [anything]?"
❌ "What are the prerequisites for [anything]?"
❌ "What is [language] primarily used for?"
❌ "What is [language]'s focus on?"
❌ Questions answerable without reading the content above
❌ Questions with options like "To improve performance" or "To organize code"
❌ Generic Java/Python intro questions (installing JDK, writing first program, etc.)

ALSO BANNED — duplicate concept questions:
❌ If Q3 asks about control structures, Q7 CANNOT also ask about control structures
❌ Each question must cover a completely different topic

GOOD QUESTION PATTERNS (use these):
✅ "What does [specific method/class from content] return when called with [input]?"
✅ "What is the output of this code: [specific snippet from content]?"
✅ "Which [specific exception from content] is thrown when [condition]?"
✅ "What is the correct syntax for [specific operation from content]?"
✅ "In [specific topic from content], what is the difference between X and Y?"
✅ "What parameter does [specific method from content] accept?"
✅ Questions about specific T-codes, transaction types, module names from content
✅ Questions about specific error codes, return values, data types from content

══════════════════════════════════════════════════════════════════
BEFORE WRITING EACH QUESTION, ASK YOURSELF:
══════════════════════════════════════════════════════════════════
1. "Can this question ONLY be answered by someone who read the content?" → If NO, discard it
2. "Did I already write a question about this concept?" → If YES, pick a different concept
3. "Are my options specific technical details?" → If NO, make them specific
══════════════════════════════════════════════════════════════════

FORMAT:

=== QUESTION 1 ===
## Title: [Specific topic from content]
## Difficulty: Easy
## Type: mcq
## Question:
[Specific question about a fact in the content above]
## Options:
A) [Specific technical answer]
B) [Specific technical answer]
C) [Specific technical answer]
D) [Specific technical answer]
## Correct: [A/B/C/D]

Generate {count} questions. Use === QUESTION N === markers.
CRITICAL: Start IMMEDIATELY with === QUESTION 1 ===. No preamble."""

    # ════════════════════════════════════════════════════════════
    # DEVELOPER CODING
    # ════════════════════════════════════════════════════════════

    @staticmethod
    def _dev_coding_prompt(context: str, count: int) -> str:
        return f"""Generate exactly {count} coding problems with test cases, like HackerRank/LeetCode.

=== COURSE CONTENT (for language detection only) ===
{context}
=== END CONTENT ===

══════════════════════════════════════════════════════════════════
STEP 1: DETECT LANGUAGE (do NOT write this in output)
══════════════════════════════════════════════════════════════════
Silently detect from content above:
- Java content → Java problems
- Python content → Python problems
- JavaScript → JavaScript problems
- No clear language → Python

CRITICAL: Start IMMEDIATELY with === QUESTION 1 ===. No introduction whatsoever.

══════════════════════════════════════════════════════════════════
STEP 2: GENERATE TESTABLE PROBLEMS
══════════════════════════════════════════════════════════════════

FORBIDDEN — cannot be auto-tested:
❌ File I/O, web scraping, downloads, threading, networking, GUI, database

REQUIRED — all problems must:
✅ Read ALL input from stdin
✅ Print output to stdout only
✅ Be deterministic (same input = same output)
✅ Be self-contained (no external libraries beyond standard)
✅ State clearly which language to use

PICK FROM THESE CATEGORIES (use variety, no repeats):
1. String processing (reverse, palindrome, frequency, cipher)
2. Math/algorithms (factorial, fibonacci, prime, patterns)
3. Array/list operations (sort, filter, min/max, duplicates)
4. Map/dictionary operations (frequency count, lookup)
5. Class design with stdin (BankAccount, StudentGrades, ShoppingCart)
6. Input validation and error handling

══════════════════════════════════════════════════════════════════
FORMAT (follow EXACTLY):
══════════════════════════════════════════════════════════════════

=== QUESTION 1 ===
## Title: Reverse a String
## Difficulty: Easy
## Type: coding
## Question:
Write a Java program that reads a string from stdin and prints its reverse.

**Input Format:**
- Line 1: A string

**Output Format:**
- The reversed string

**Example:**
Input:
hello
Output:
olleh

## TestCases:
TC1|VISIBLE|hello|olleh
TC2|VISIBLE|Java|avaJ
TC3|HIDDEN|racecar|racecar
TC4|HIDDEN|12345|54321
TC5|HIDDEN|a|a

TEST CASE FORMAT:
- TC<N>|VISIBLE or HIDDEN|<input>|<expected_output>
- Use \\n for newlines in input
- Expected output = EXACT stdout, no labels or prompts
- First 2 VISIBLE, rest HIDDEN
- HIDDEN = edge cases (empty, single char, numbers, special chars)

Generate exactly {count} problems using === QUESTION N === markers.
Each MUST have ## TestCases: with 4-6 test cases.
CRITICAL: Start IMMEDIATELY with === QUESTION 1 ===."""

    # ════════════════════════════════════════════════════════════
    # STANDALONE TEST CASE GENERATION
    # ════════════════════════════════════════════════════════════

    @staticmethod
    def create_test_cases_prompt(question: str, num_cases: int = 5) -> str:
        return f"""Generate exactly {num_cases} test cases for this coding problem.

CODING QUESTION:
{question}

══════════════════════════════════════════════════════════════════
RULES:
══════════════════════════════════════════════════════════════════
1. All input read from stdin, all output to stdout
2. Deterministic — same input = same output
3. First 2 = VISIBLE, remaining = HIDDEN
4. Expected output = ONLY the computed result, no prompts or labels
5. For numbers: just the number (e.g., "42" not "Answer: 42")
6. HIDDEN cases must test edge cases (zero, empty, large, negative, boundary)

FORMAT — output ONLY these lines, nothing else:
TC1|VISIBLE|<input>|<expected_output>
TC2|VISIBLE|<input>|<expected_output>
TC3|HIDDEN|<input>|<expected_output>
TC4|HIDDEN|<input>|<expected_output>
TC5|HIDDEN|<input>|<expected_output>

Use \\n for multi-line input (e.g., 3\\n5 = line1 is "3", line2 is "5").
Output ONLY the TC lines. No explanations, no code, no extra text."""

    # ════════════════════════════════════════════════════════════
    # NON-DEVELOPER APTITUDE
    # ════════════════════════════════════════════════════════════

    @staticmethod
    def _non_dev_aptitude_prompt(count: int) -> str:
        return f"""Generate exactly {count} aptitude MCQ questions.

RULES:
- General aptitude ONLY: math, logic, reasoning
- NO programming, coding, Python, Java questions whatsoever
- Each question must test a DIFFERENT concept — no repeats

Topics: Number series, Percentages, Profit/Loss, Time/Work, Ratios, Age problems, Speed/Distance.

══════════════════════════════════════════════════════════════════
CRITICAL — MATHEMATICAL ACCURACY:
══════════════════════════════════════════════════════════════════
For EVERY question:
1. Solve step-by-step BEFORE writing options
2. Verify answer is correct — plug it back in
3. Correct option MUST exactly match calculated answer
4. All 4 options must be distinct — no duplicates
══════════════════════════════════════════════════════════════════

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

Generate {count} questions. Use === QUESTION N === markers.
CRITICAL: Start IMMEDIATELY with === QUESTION 1 ===. No introduction."""

    # ════════════════════════════════════════════════════════════
    # NON-DEVELOPER MCQ
    # ════════════════════════════════════════════════════════════

    @staticmethod
    def _non_dev_mcq_prompt(context: str, count: int) -> str:
        return f"""Generate exactly {count} MCQ questions STRICTLY based on the summary content below.

══════════════════════════════════════════════════════════════════
CRITICAL RULE: ALL QUESTIONS MUST COME FROM THE SUMMARY BELOW.
No two questions can test the same concept — all {count} must be unique.
══════════════════════════════════════════════════════════════════

COMPLETELY BANNED:
❌ "What is the primary goal of...?"
❌ "What is the main purpose of...?"
❌ Generic options like "maximize/minimize/optimize X"
❌ Python, Java, programming questions
❌ Questions not answerable from the summary below
❌ Duplicate concept questions (if Q3 covers topic X, no other question can)

HOW TO CREATE QUESTIONS — extract from summary:
- Definitions → "What is X defined as in this context?"
- Numbers/Ranges → "How many X are there according to the content?"
- T-codes/Transactions → "Which T-code is used for X?"
- Types/Categories → "What are the types of X mentioned?"
- Steps/Processes → "What is the first/last step in X?"
- Tools/Prerequisites → "What is required before X?"

══════════════════════════════════════════════════════════════════
SUMMARY CONTENT:
══════════════════════════════════════════════════════════════════
{context}
══════════════════════════════════════════════════════════════════

FORMAT:

=== QUESTION 1 ===
## Title: [Specific topic from summary]
## Difficulty: Easy
## Type: mcq
## Question:
[Question about SPECIFIC fact from summary]
## Options:
A) [Specific answer]
B) [Specific answer]
C) [Specific answer]
D) [Specific answer]
## Correct: [A/B/C/D]

Generate {count} questions using === QUESTION N === markers.
CRITICAL: Start IMMEDIATELY with === QUESTION 1 ===. No preamble."""

    # ════════════════════════════════════════════════════════════
    # EVALUATION PROMPTS
    # ════════════════════════════════════════════════════════════

    @staticmethod
    def create_section_evaluation_prompt(section_type: str, qa_pairs: List[Dict[str, Any]]) -> str:
        question_count = len(qa_pairs)
        formatted = []
        for i, qa in enumerate(qa_pairs, 1):
            q       = qa.get("question", "")
            a       = qa.get("answer", "")
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
        question_count = len(qa_pairs)
        formatted = []
        for i, qa in enumerate(qa_pairs, 1):
            q      = qa.get("question", "")
            a      = qa.get("answer", "")
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