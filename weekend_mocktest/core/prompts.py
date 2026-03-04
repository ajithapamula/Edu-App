# weekend_mocktest/core/prompts.py
# ═══════════════════════════════════════════════════════════════════
# UPDATED: Language-agnostic prompts — auto-detects from summaries
#
# WHAT CHANGED:
#   - _dev_mcq_prompt: Content-driven, no hardcoded language
#   - _dev_coding_prompt: Detects language from context (Java/Python/JS/etc.)
#   - Non-dev prompts: UNCHANGED
# ═══════════════════════════════════════════════════════════════════
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

    # ================================================================
    # DEVELOPER PROMPTS
    # ================================================================

    @staticmethod
    def _dev_aptitude_prompt(count: int) -> str:
        return f"""Generate exactly {count} aptitude MCQ questions.

These are GENERAL aptitude questions - math, logic, reasoning.
NOT programming questions.

Topics: Number series, Percentages, Profit/Loss, Time/Work, Ratios, Averages, Logical reasoning.

══════════════════════════════════════════════════════════════════
CRITICAL — MATHEMATICAL ACCURACY:
══════════════════════════════════════════════════════════════════
For EVERY question, you MUST:
1. Solve the problem yourself step-by-step BEFORE writing the options
2. Verify your answer is mathematically correct
3. Make sure the correct option EXACTLY matches your calculated answer
4. Double-check: plug your answer back into the problem to verify
5. All 4 options must be distinct numbers/values — no duplicates

COMMON MISTAKES TO AVOID:
❌ Saying average is 35 when calculation gives 36
❌ Having correct answer not match any option
❌ Division errors (always double-check division)
❌ Ratio problems where parts don't add up to total
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
Each must have 4 options (A, B, C, D) and one correct answer.
CRITICAL: Start your response IMMEDIATELY with === QUESTION 1 ===. No introduction or preamble."""

    @staticmethod
    def _dev_mcq_prompt(context: str, count: int) -> str:
        return f"""Generate exactly {count} MCQ questions based on this course content:

=== COURSE CONTENT (from MongoDB summaries) ===
{context}
=== END CONTENT ===

══════════════════════════════════════════════════════════════════
STRICT RULES — READ CAREFULLY:
══════════════════════════════════════════════════════════════════

1. Every question MUST test a SPECIFIC fact, concept, or detail from the content above.
2. If the content mentions specific classes, methods, syntax, APIs, frameworks, 
   or concepts — create questions about THOSE specific things.
3. Options must include specific technical details, NOT vague descriptions.

BANNED QUESTION PATTERNS (do NOT generate these):
❌ "What is the purpose of [language]?"
❌ "What is the purpose of a loop/function/class?"
❌ "What is a good practice for..."
❌ "Why is it important to..."
❌ "What is [language]'s focus on?"
❌ Any question that could be answered WITHOUT reading the content above
❌ Any question with options like "To build applications efficiently"

GOOD QUESTION PATTERNS:
✅ "What does the [specific method/class from content] do?"
✅ "What is the output of [specific code snippet from content]?"
✅ "Which [specific concept from content] is used when...?"
✅ "In [specific topic from content], what happens when...?"
✅ Questions about specific syntax, parameters, return types mentioned in content
✅ Questions about specific error types, exception classes mentioned in content

FORMAT:

=== QUESTION 1 ===
## Title: [Specific topic from content]
## Difficulty: Easy
## Type: mcq
## Question:
[Question testing a SPECIFIC fact from the content above]
## Options:
A) [Specific technical answer]
B) [Specific technical answer]
C) [Specific technical answer]
D) [Specific technical answer]
## Correct: [A/B/C/D]

Generate {count} MCQ questions from the content. Use === QUESTION N === markers.
CRITICAL: Start your response IMMEDIATELY with === QUESTION 1 ===. No introduction or preamble text."""

    # ================================================================
    # DEVELOPER CODING — LANGUAGE-AGNOSTIC WITH TEST CASES
    # ================================================================

    @staticmethod
    def _dev_coding_prompt(context: str, count: int) -> str:
        return f"""Generate exactly {count} coding problems with test cases, like HackerRank/LeetCode.

=== COURSE CONTENT (for reference) ===
{context}
=== END CONTENT ===

══════════════════════════════════════════════════════════════════
LANGUAGE DETECTION (do NOT output this reasoning — just apply it):
══════════════════════════════════════════════════════════════════

Silently detect the language from the content above and use it:
- Java content → Java problems (Scanner for input, System.out.println for output)
- Python content → Python problems (input() and print())
- JavaScript content → JavaScript problems (readline and console.log)
- Multiple languages → mix problems across those languages
- No clear language → default to Python

CRITICAL: Do NOT write any introduction, preamble, or explanation.
Start your response IMMEDIATELY with === QUESTION 1 ===
No text before the first === QUESTION 1 === marker.

══════════════════════════════════════════════════════════════════
STEP 2: GENERATE TESTABLE PROBLEMS
══════════════════════════════════════════════════════════════════

IMPORTANT: DO NOT generate questions about file I/O, web scraping,
downloads, threading, networking, or database operations.
These CANNOT be tested in an automated environment.

Instead, extract the PROGRAMMING CONCEPTS from the content
(OOP, error handling, data structures, functions, loops, etc.)
and create ALGORITHMIC problems that test those concepts.

TOPIC CONVERSION TABLE:

If content mentions...          → Generate problems about...
─────────────────────────────────────────────────────────
File handling, reading files    → String parsing, processing text input from stdin
File writing                    → Formatting and printing structured output
Threading / concurrency         → Processing lists, parallel task simulation with data
Web scraping / requests         → Parsing structured text (CSV, key:value pairs)
Database operations             → Dictionary/HashMap/Map CRUD operations
Exception handling              → Input validation with try/catch or try/except
OOP / Classes                   → Class design (BankAccount, StudentGrades, ShoppingCart)
Functions / methods             → Writing reusable functions with clear I/O
Data structures                 → List/Array/Map operations and algorithms
Collections framework           → ArrayList, HashMap, TreeSet operations

══════════════════════════════════════════════════════════════════
QUESTION CATEGORIES (pick from these):
══════════════════════════════════════════════════════════════════

1. STRING PROCESSING
   - Reverse words, count vowels, check palindrome
   - Caesar cipher, remove duplicates, most frequent character

2. MATH & ALGORITHMS
   - Factorial, Fibonacci, prime check
   - Sum of digits, GCD/LCM, number patterns

3. LIST / ARRAY OPERATIONS
   - Sort, filter, find min/max/second-largest
   - Remove duplicates, merge sorted lists, frequency count

4. MAP / DICTIONARY OPERATIONS
   - Word frequency counter
   - Student grade calculator, inventory management

5. CLASS DESIGN (read data from stdin)
   - BankAccount: deposit, withdraw, check balance
   - StudentReport: add scores, calculate average, grade
   - ShoppingCart: add items, calculate total, apply discount

6. INPUT VALIDATION & ERROR HANDLING
   - Validate and process mixed input
   - Calculate with graceful error handling

══════════════════════════════════════════════════════════════════
STRICT RULES:
══════════════════════════════════════════════════════════════════
1. MUST read ALL input from stdin
2. MUST print output to stdout
3. SELF-CONTAINED — no files, no network, no external libraries
4. DETERMINISTIC — same input = same output always
5. NO: file operations, web requests, threading, database, GUI
6. Questions must be CLEAR with explicit Input/Output format
7. Each question must have 4-6 test cases
8. State which language the solution should be written in

FORBIDDEN KEYWORDS IN QUESTIONS:
❌ "download", "upload", "file", "read from file", "write to file"
❌ "web", "scrape", "crawl", "URL", "HTTP", "API"
❌ "database", "SQL", "connect", "server"
❌ "thread", "concurrent", "parallel" (as actual implementation)
❌ "GUI", "window", "button", "click"

══════════════════════════════════════════════════════════════════
FORMAT (follow EXACTLY):
══════════════════════════════════════════════════════════════════

=== QUESTION 1 ===
## Title: Calculate Student Average
## Difficulty: Easy
## Type: coding
## Question:
Write a program that reads a student's name and their scores in 3 subjects, then prints their average score rounded to 2 decimal places.

**Input Format:**
- Line 1: Student name (string)
- Line 2: Math score (integer)
- Line 3: Science score (integer)
- Line 4: English score (integer)

**Output Format:**
- A single line: the average score rounded to 2 decimal places

**Example:**
Input:
Alice
85
90
78
Output:
84.33

## TestCases:
TC1|VISIBLE|Alice\n85\n90\n78|84.33
TC2|VISIBLE|Bob\n100\n100\n100|100.0
TC3|HIDDEN|Charlie\n0\n0\n0|0.0
TC4|HIDDEN|Dave\n70\n80\n90|80.0
TC5|HIDDEN|Eve\n99\n98\n97|98.0

══════════════════════════════════════════════════════════════════
TEST CASE FORMAT:
══════════════════════════════════════════════════════════════════
- TC<N>|VISIBLE or HIDDEN|<input>|<expected_output>
- Use \\n for newlines in both input and expected output
- Expected output = EXACT stdout output, no prompts, no labels unless specified
- First 2 VISIBLE, rest HIDDEN
- HIDDEN should include edge cases (zero, empty, large, boundary)

Generate exactly {count} coding problems with === QUESTION N === markers.
Make them DIVERSE — pick different categories from the list above.
Each MUST have ## TestCases: with 4-6 test cases.
CRITICAL: Start your response IMMEDIATELY with === QUESTION 1 ===. No introduction or preamble text."""

    # ================================================================
    # STANDALONE TEST CASE GENERATION
    # ================================================================

    @staticmethod
    def create_test_cases_prompt(question: str, num_cases: int = 5) -> str:
        return f"""Generate exactly {num_cases} test cases for this coding problem.

CODING QUESTION:
{question}

══════════════════════════════════════════════════════════════════
CRITICAL RULES:
══════════════════════════════════════════════════════════════════

1. The program reads ALL data from stdin
2. The program prints results to stdout
3. Test cases must be deterministic (same input = same output)
4. First 2 = VISIBLE, remaining = HIDDEN

IMPORTANT — Expected output rules:
- Expected output is ONLY the final computed result
- Do NOT include input prompts in expected output
- Do NOT include labels unless the question specifically asks for it
- For numbers: just the number (e.g., "42")
- For strings: just the string (e.g., "hello")
- For booleans: language-appropriate ("True"/"False" or "true"/"false")

FORMAT (output ONLY these lines, nothing else):
TC1|VISIBLE|<input>|<expected_output>
TC2|VISIBLE|<input>|<expected_output>
TC3|HIDDEN|<input>|<expected_output>
TC4|HIDDEN|<input>|<expected_output>
TC5|HIDDEN|<input>|<expected_output>

Use \\n for multi-line input (e.g., 3\\n5 means line 1 is "3", line 2 is "5").
Output ONLY the TC lines. No explanations, no code blocks, no extra text."""

    # ================================================================
    # NON-DEVELOPER PROMPTS - NO PROGRAMMING!
    # ================================================================

    @staticmethod
    def _non_dev_aptitude_prompt(count: int) -> str:
        return f"""Generate exactly {count} aptitude MCQ questions.

RULES:
- General aptitude only: math, logic, reasoning
- NO programming, coding, Python, Java questions
- NO technical IT questions

Topics: Number series, Percentages, Profit/Loss, Time/Work, Ratios, Age problems, Speed/Distance.

══════════════════════════════════════════════════════════════════
CRITICAL — MATHEMATICAL ACCURACY:
══════════════════════════════════════════════════════════════════
For EVERY question:
1. Solve the problem yourself step-by-step BEFORE writing options
2. Verify your answer is mathematically correct
3. Double-check: plug your answer back into the problem
4. The correct option must EXACTLY match your calculated answer
5. All 4 options must be distinct — no duplicates
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
DO NOT include any programming questions.
CRITICAL: Start your response IMMEDIATELY with === QUESTION 1 ===. No introduction or preamble."""

    @staticmethod
    def _non_dev_mcq_prompt(context: str, count: int) -> str:
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
✓ NO "primary goal" or "main purpose" questions
✓ Options are specific facts, not vague phrases
✓ Start IMMEDIATELY with === QUESTION 1 === — no introduction or preamble"""

    # ================================================================
    # EVALUATION PROMPTS (UNCHANGED)
    # ================================================================

    @staticmethod
    def create_section_evaluation_prompt(section_type: str, qa_pairs: List[Dict[str, Any]]) -> str:
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








