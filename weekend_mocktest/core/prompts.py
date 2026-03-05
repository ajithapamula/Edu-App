# weekend_mocktest/core/prompts.py
from typing import List, Dict, Any
from .config import config
import random


class PromptTemplates:

    # All available aptitude topics — used to enforce diversity
    APTITUDE_TOPICS = [
        "Number Series",
        "Percentages",
        "Profit and Loss",
        "Time and Work",
        "Pipes and Cisterns",
        "Ratios and Proportions",
        "Averages",
        "Age Problems",
        "Speed Distance Time",
        "Simple Interest",
        "Compound Interest",
        "Logical Reasoning",
        "Blood Relations",
        "Coding and Decoding",
        "Direction Sense",
        "Clocks and Calendars",
        "Probability",
        "Permutation and Combination",
        "Mixtures and Allegations",
        "Data Sufficiency",
        "Boats and Streams",
        "Trains and Platforms",
        "Partnership",
        "Number System",
        "HCF and LCM",
        "Simplification",
        "Mensuration",
        "Trigonometry Basics",
        "Inequalities",
        "Seating Arrangement",
        "Syllogism",
        "Statement and Conclusions",
        "Series Completion",
        "Analogy",
        "Calendar Problems",
    ]

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

    @staticmethod
    def _pick_aptitude_topics(count: int) -> list:
        """Pick `count` unique topics randomly — guarantees variety each batch."""
        pool = PromptTemplates.APTITUDE_TOPICS.copy()
        random.shuffle(pool)
        # Cycle if count > pool size
        topics = []
        while len(topics) < count:
            topics.extend(pool)
        return topics[:count]

    # ════════════════════════════════════════════════════════════
    # DEVELOPER APTITUDE
    # ════════════════════════════════════════════════════════════

    @staticmethod
    def _dev_aptitude_prompt(count: int) -> str:
        topics = PromptTemplates._pick_aptitude_topics(count)
        topic_assignments = "\n".join(
            f"  Question {i+1}: {topic}" for i, topic in enumerate(topics)
        )
        return f"""Generate exactly {count} aptitude MCQ questions.

GENERAL aptitude only — math, logic, reasoning. NOT programming.

══════════════════════════════════════════════════════════════════
MANDATORY TOPIC ASSIGNMENT — follow this EXACTLY:
══════════════════════════════════════════════════════════════════
{topic_assignments}

Each question MUST cover its assigned topic above.
Do NOT swap, skip, or repeat topics.
══════════════════════════════════════════════════════════════════

══════════════════════════════════════════════════════════════════
CRITICAL — USE DIFFERENT QUESTION FORMATS PER TOPIC:
══════════════════════════════════════════════════════════════════
Every topic below has 8-10 different formats. Pick a DIFFERENT one each time.
NEVER repeat the same format even if the numbers change.

─────────────────────────────────────────────────────────────────
TIME & WORK (pick one each time):
  1. "A and B together finish in X days. A alone takes Y days. How long for B alone?"
  2. "A is twice as efficient as B. Together they finish in X days. How long for A alone?"
  3. "A can do a job in X days. After Y days, B joins. They finish in Z more days. Find B's rate."
  4. "A, B, C together finish in X days. A+B take Y days, B+C take Z days. Find A alone."
  5. "Pipe A fills tank in X hrs. Pipe B drains it in Y hrs. If both open, when is tank full?"
  6. "A and B together do X fraction of work per day. They work for Y days then A leaves. B finishes in Z more days."
  7. "A can do 40% of a job in 8 days. B can do 60% in 9 days. How long together?"
  8. "20 men finish a project in 30 days. After 10 days, 5 men leave. How many more days to finish?"

─────────────────────────────────────────────────────────────────
PERCENTAGES (pick one each time):
  1. "Price increased by X% then decreased by Y%. Net percentage change?"
  2. "Salary of A is X% more than B. By what % is B's salary less than A?"
  3. "A number after 20% increase becomes 480. What is 35% of the original number?"
  4. "In an election, winner gets 60% of votes and wins by 1200 votes. Find total votes."
  5. "Population of a city is 2,00,000. It grows 10% in year 1 and 5% in year 2. New population?"
  6. "A shopkeeper gives 3 items free on purchase of 12. What is effective discount %?"
  7. "Ravi spends 30% on rent, 25% on food, 15% on travel. He saves ₹6000. Find income."
  8. "If X% of Y = Y% of Z, find the relationship between X and Z."
  9. "A student gets 40% in exam and fails by 20 marks. Pass mark is 50%. Find total marks."

─────────────────────────────────────────────────────────────────
PROFIT & LOSS (pick one each time):
  1. "Sold at X% loss. If sold for ₹Y more, profit would be Z%. Find cost price."
  2. "Two articles sold at ₹1200 each — one at 20% profit, other 20% loss. Net profit or loss?"
  3. "Marked price ₹800. Successive discounts of 10% and 5%. Final selling price?"
  4. "A trader uses 900g weight instead of 1kg. What is his actual profit %?"
  5. "CP of 15 items = SP of 12 items. Find profit or loss %."
  6. "A buys at ₹X, sells to B at 20% profit. B sells to C at 10% loss. C pays ₹Y. Find X."
  7. "By selling 8 mangoes for ₹1, a man loses 20%. How many should he sell for ₹1 to gain 20%?"
  8. "A machine depreciates 10% per year. After 2 years its value is ₹16200. Original price?"

─────────────────────────────────────────────────────────────────
SPEED, DISTANCE & TIME (pick one each time):
  1. "Two trains 200m and 150m long approach each other at 60 and 40 kmph. Time to cross?"
  2. "Boat goes 24km upstream in 4hrs and 36km downstream in 3hrs. Speed of current?"
  3. "A person travels first half of journey at 40kmph and second half at 60kmph. Average speed?"
  4. "A reaches office 30 min late travelling at 2/3 normal speed. Find normal travel time."
  5. "Two cyclists start from same point in opposite directions at 20 and 25 kmph. Distance after 3hrs?"
  6. "A car travels A to B in 4 hrs. Returns B to A with 25% more speed. Total journey time?"
  7. "Train passes a standing man in 10sec and a 200m platform in 20sec. Find train length."
  8. "A and B start running at same time toward each other from 120km apart. A at 30kmph, B at 40kmph. When do they meet?"

─────────────────────────────────────────────────────────────────
AVERAGES (pick one each time):
  1. "Average of 20 students is 45. 5 new students join with average 50. New class average?"
  2. "Average of A, B, C is 30. Average of A, B is 25. What is C's value?"
  3. "Batting average after 20 innings is 45. After 21st inning it becomes 46. Score in 21st?"
  4. "Average of 5 consecutive even numbers is 52. Find the largest number."
  5. "Average weight of 8 people is 65kg. If heaviest leaves, average becomes 62kg. Heaviest weight?"
  6. "Average monthly salary of 12 employees is ₹8000. Manager's salary is ₹20000. Average with manager?"
  7. "Mean of X numbers is 40. Two numbers 20 and 30 are removed. New mean is 42. Find X."

─────────────────────────────────────────────────────────────────
RATIOS & PROPORTIONS (pick one each time):
  1. "Divide ₹1200 among A, B, C in ratio 3:4:5. Find B's share."
  2. "Ratio of A:B = 2:3. If 4 is added to each, ratio becomes 3:4. Find A and B."
  3. "Mixture of milk and water is 5:2. Add 14L water. New ratio 5:4. Find original milk."
  4. "A:B = 3:5 and B:C = 4:7. Find A:B:C."
  5. "Gold and copper alloy — 3:1 ratio. Second alloy — 5:3 ratio. Mix equal parts. Final ratio?"
  6. "Income of A and B in ratio 3:2. Expenses in ratio 5:3. Each saves ₹1000. Find A's income."
  7. "If 3A = 4B = 6C, find A:B:C."

─────────────────────────────────────────────────────────────────
SIMPLE & COMPOUND INTEREST (pick one each time):
  1. "CI on ₹5000 at 10% for 2 years compounded annually. Find interest."
  2. "Difference between CI and SI on ₹X at 10% for 2 years is ₹50. Find X."
  3. "A sum doubles in 8 years at SI. In how many years will it become 5 times?"
  4. "₹2000 invested at 5% SI for 4 years. At what rate CI gives same return in 2 years?"
  5. "Principal is ₹10000. At 20% CI annually, find amount after 3 years."
  6. "Anita invested ₹5000 at 8% SI for 3 years and ₹3000 at 10% SI for 2 years. Total interest?"

─────────────────────────────────────────────────────────────────
AGE PROBLEMS (pick one each time):
  1. "Present ratio of father to son = 4:1. After 5 years ratio = 3:1. Find present ages."
  2. "Sum of ages of A and B is 50. 5 years ago A was twice B's age. Find current ages."
  3. "Ratio of A to B's age = 3:5. After 10 years ratio = 5:7. Find A's current age."
  4. "Average age of 5 children is 8. Youngest is 4. Average of remaining 4 before youngest born?"
  5. "Mother is 3 times her daughter's age. 10 years later she will be twice. Current ages?"
  6. "A is 2 years older than B who is twice as old as C. Sum of all three ages is 27. Find A."

─────────────────────────────────────────────────────────────────
PROBABILITY (pick one each time):
  1. "Bag has 5 red, 3 blue, 2 green balls. Probability of picking non-red ball?"
  2. "Two dice rolled. Probability sum = 8?"
  3. "Card drawn from standard deck. P(face card or red card)?"
  4. "Box has 4 defective and 6 good items. 2 drawn randomly. P(both good)?"
  5. "P(A) = 1/3, P(B) = 1/4. A and B independent. P(at least one occurs)?"
  6. "Letters of RANDOM arranged randomly. P(vowels together)?"
  7. "From group of 5 men and 4 women, committee of 3 selected. P(at least 1 woman)?"

─────────────────────────────────────────────────────────────────
NUMBER SERIES (pick one each time):
  1. "2, 6, 18, 54, __ (multiply pattern)"
  2. "1, 4, 9, 16, 25, __ (squares)"
  3. "100, 91, 83, 76, 70, __ (decreasing difference)"
  4. "3, 5, 9, 17, 33, __ (double previous + pattern)"
  5. "1, 2, 6, 24, 120, __ (factorial)"
  6. "2, 3, 5, 8, 13, 21, __ (Fibonacci)"
  7. "144, 121, 100, 81, __ (squares descending)"
  8. "1, 8, 27, 64, __ (cubes)"

─────────────────────────────────────────────────────────────────
BLOOD RELATIONS (pick one each time):
  1. "A is B's sister. B is C's mother. C is D's brother. How is A related to D?"
  2. "Pointing to a photo, Ramesh says 'She is the daughter of my grandfather's only son.' Who is she?"
  3. "X says 'Y's mother is the only daughter of my mother.' How is X related to Y?"
  4. "A+B are a couple. C is A's sister. D is C's husband. E is B's brother. How is E related to D?"

─────────────────────────────────────────────────────────────────
DIRECTION SENSE (pick one each time):
  1. "Walk N 5km, turn right 3km, turn right 4km, turn left 2km. Final direction from start?"
  2. "Start facing East, turn 90° clockwise 3 times. Now facing which direction?"
  3. "A walks 10km North, turns right 5km, turns right 10km. Distance from start?"
  4. "Facing North, turn left 3 times, walk 4km. Which direction are you now facing?"

─────────────────────────────────────────────────────────────────
LOGICAL REASONING (pick one each time):
  1. "All A are B. Some B are C. Conclusions: Some A are C? All C are A?"
  2. "All dogs are animals. Some animals are white. Conclusions: Some dogs are white?"
  3. "No pen is paper. All papers are books. Conclusion: No pen is book?"
  4. "Statement: All fruits are vegetables. Some vegetables are sweet. Find valid conclusion."

HARD RULE: Same format TWICE in one batch = WRONG. Always vary format.
BANNED FOREVER: "X workers/men build a wall in Y days" — never use.
BANNED FOREVER: Changing only numbers while keeping exact same question structure.
══════════════════════════════════════════════════════════════════

══════════════════════════════════════════════════════════════════
CRITICAL — MATHEMATICAL ACCURACY:
══════════════════════════════════════════════════════════════════
For EVERY question:
1. Solve step-by-step BEFORE writing options
2. Verify answer is mathematically correct
3. Plug answer back into problem to verify
4. Correct option MUST exactly match your calculated answer
5. All 4 options must be distinct — no duplicates
6. Options must be close in value to make the question challenging

COMMON MISTAKES TO AVOID:
❌ Correct answer not matching any option
❌ Division errors — double check all divisions
❌ Rounding errors — if result is 21.6, round up to 22 men (can't have half a person)
❌ Ratio parts not adding up to total
❌ Average * count ≠ sum (always verify)
══════════════════════════════════════════════════════════════════

FORMAT (follow exactly):

=== QUESTION 1 ===
## Title: [Assigned topic for Q1]
## Difficulty: Easy
## Type: aptitude
## Question:
[Complete problem scenario with all numbers/data on one line]
Select the correct answer from the options below.
## Options:
A) [value]
B) [value]
C) [value]
D) [value]
## Correct: [A/B/C/D]

QUESTION TEXT RULES:
- Write 3 to 5 lines for each question
- Line 1: Setup/context — introduce the scenario with background details
- Line 2-3: All numbers, conditions, and specific data needed to solve
- Second-to-last line: The actual question being asked ("Find X", "How many Y", "What is Z?")
- Last line: "Select the correct answer from the options below."
- NEVER write incomplete phrases like "The average of" or "If X workers"
- Options must be specific numbers/values — never "Option A"
- Make questions feel real — use names, places, and practical scenarios

EXAMPLE of good question length:
A shopkeeper bought 120 notebooks at ₹15 each and spent ₹200 on transportation.
He sold 100 notebooks at ₹22 each and the remaining at ₹10 each.
Calculate the overall profit or loss made by the shopkeeper.
Select the correct answer from the options below.

Generate {count} questions using === QUESTION N === markers.
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
[Specific question about a fact in the content above — MUST be a complete sentence]
Choose the correct answer from the options below.
## Options:
A) [Specific technical answer — not "Option A"]
B) [Specific technical answer — not "Option B"]
C) [Specific technical answer — not "Option C"]
D) [Specific technical answer — not "Option D"]
## Correct: [A/B/C/D]

QUESTION TEXT RULES:
- Write 2 to 4 lines for each question
- For concept questions: Line 1 context/scenario, Line 2 specific question, Last line directive
- For code output questions: show the code block across 2-3 lines, then ask the question
- Last line: "Choose the correct answer from the options below."
- Options must be REAL answers, never placeholder text like "Option A", "Option B"
- Make questions specific and technical — reference actual class names, method names, values

EXAMPLE of good question length:
A Java developer writes the following code: ArrayList<Integer> list = new ArrayList<>();
list.add(10); list.add(20); list.add(30); list.remove(1);
What will be the contents of the list after executing this code?
Choose the correct answer from the options below.

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
STEP 1: DETECT ONE LANGUAGE FOR ALL QUESTIONS (do NOT write this in output)
══════════════════════════════════════════════════════════════════
Look at the content above and pick EXACTLY ONE language for ALL {count} questions.
Count language signals: Java keywords (Scanner, System.out, public class, ArrayList, HashMap)
vs Python keywords (def, print(, input(, import numpy, list comprehension)
vs JavaScript (console.log, const, let, require).

Pick the language with the MOST signals. If tied, pick Java.

ALL {count} questions MUST use the SAME language — never mix languages in one batch.
Do NOT write "Java" or "Python" as part of your output — just apply it silently.

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
STRICT RULES:
══════════════════════════════════════════════════════════════════
1. All input read from stdin, all output to stdout
2. Deterministic — same input = same output every time
3. TC1 and TC2 MUST be VISIBLE — no exceptions
4. TC3 and beyond MUST be HIDDEN
5. Expected output = ONLY the exact stdout output, nothing else
6. For numbers: just the number (e.g., "42" not "Answer: 42")
7. HIDDEN cases must test edge cases (zero, empty, large, negative, boundary)
8. Do NOT use "->" or "=>" in expected output
9. Input and expected output must NOT be identical

MANDATORY FORMAT — output ONLY these exact lines:
TC1|VISIBLE|<input>|<expected_output>
TC2|VISIBLE|<input>|<expected_output>
TC3|HIDDEN|<input>|<expected_output>
TC4|HIDDEN|<input>|<expected_output>
TC5|HIDDEN|<input>|<expected_output>

Use \\n for multi-line input (e.g., "5\\n1 2 3 4 5" means line1="5", line2="1 2 3 4 5").
Output ONLY the TC lines. No explanations, no code, no extra text, no blank lines."""

    # ════════════════════════════════════════════════════════════
    # NON-DEVELOPER APTITUDE
    # ════════════════════════════════════════════════════════════

    @staticmethod
    def _non_dev_aptitude_prompt(count: int) -> str:
        topics = PromptTemplates._pick_aptitude_topics(count)
        topic_assignments = "\n".join(
            f"  Question {i+1}: {topic}" for i, topic in enumerate(topics)
        )
        return f"""Generate exactly {count} aptitude MCQ questions.

RULES:
- General aptitude ONLY: math, logic, reasoning
- NO programming, coding, Python, Java questions whatsoever

══════════════════════════════════════════════════════════════════
MANDATORY TOPIC ASSIGNMENT — follow this EXACTLY:
══════════════════════════════════════════════════════════════════
{topic_assignments}

Each question MUST cover its assigned topic above.
Do NOT swap, skip, or repeat topics.
══════════════════════════════════════════════════════════════════

══════════════════════════════════════════════════════════════════
CRITICAL — USE DIFFERENT QUESTION FORMATS PER TOPIC:
══════════════════════════════════════════════════════════════════
Every topic has MANY formats — pick a different one each time.

Time & Work: "A+B together X days", "A twice as fast as B", "A does 1/3 then B joins", "pipe fill/drain"
Percentages: "successive change", "A earns X% more than B", "find original from result", "population"
Profit/Loss: "find CP from loss%", "two items same SP opposite %", "discount on marked price"
Speed: "two trains meeting", "boat upstream/downstream", "arrives late at 2/3 speed"
Averages: "new member joins", "one replaced", "weighted group average"
Ratios: "divide sum in ratio", "ratio after adding value", "A:B:C comparison"
Interest: "find principal", "SI vs CI difference", "find rate or time"
Ages: "ratio X years ago", "sum of ages now vs later", "three people relationship"
Probability: "deck of cards", "balls from bag", "two dice sum", "at least one event"
Series: "find missing term", "difference pattern", "ratio pattern", "square/cube"

HARD RULE: Same format TWICE in one batch = WRONG. Always vary the format.
BANNED FOREVER: "X men/workers build a wall in Y days" — never use this format.
BANNED FOREVER: Changing only numbers while keeping the same question structure.
══════════════════════════════════════════════════════════════════

══════════════════════════════════════════════════════════════════
CRITICAL — MATHEMATICAL ACCURACY:
══════════════════════════════════════════════════════════════════
For EVERY question:
1. Solve step-by-step BEFORE writing options
2. Verify answer is correct — plug it back in
3. Correct option MUST exactly match calculated answer
4. All 4 options must be distinct — no duplicates
5. If result has decimals and context requires whole number, round correctly
══════════════════════════════════════════════════════════════════

FORMAT:

=== QUESTION 1 ===
## Title: [Assigned topic for Q1]
## Difficulty: Easy
## Type: aptitude
## Question:
[Complete problem with all data — one full sentence with all numbers]
Select the correct answer from the options below.
## Options:
A) [value]
B) [value]
C) [value]
D) [value]
## Correct: [A/B/C/D]

QUESTION TEXT RULES:
- Write 3 to 5 lines for each question
- Line 1: Setup/context — introduce the scenario with background details
- Line 2-3: All numbers, conditions, and specific data needed to solve
- Second-to-last line: The actual question being asked ("Find X", "How many Y", "What is Z?")
- Last line: "Select the correct answer from the options below."
- NEVER write a one-line question — always provide enough context
- Options must be distinct numbers or values — never "Option A" etc
- Use real-world scenarios: shops, trains, workers, ages, investments

EXAMPLE of good question length:
Priya invested ₹8,000 in a scheme offering 12% simple interest per annum.
After 3 years, she withdrew the entire amount and reinvested the interest earned
into another scheme at 10% per annum for 2 more years.
What is the total interest earned from both investments combined?
Select the correct answer from the options below.

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
[Complete question about a SPECIFIC fact from summary — never a sentence fragment]
Choose the correct answer from the options below.
## Options:
A) [Real specific answer — not "Option A"]
B) [Real specific answer — not "Option B"]
C) [Real specific answer — not "Option C"]
D) [Real specific answer — not "Option D"]
## Correct: [A/B/C/D]

QUESTION TEXT RULES:
- Write 2 to 4 lines for each question
- Line 1: Provide context or scenario from the content
- Line 2-3: Additional details or conditions if needed
- Last line: "Choose the correct answer from the options below."
- Options: real values from the content, never placeholder labels
- Never write a one-line question — always add enough context

EXAMPLE of good question length:
In SAP MM module, a purchase order is raised for 500 units of raw material.
The goods receipt is posted for only 300 units due to partial delivery.
Which document is automatically created during goods receipt posting in SAP?
Choose the correct answer from the options below.

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
SCORES: [{",".join(["0 or 1"] * question_count)}]

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
SCORES: [{",".join(["0 or 1"] * question_count)}]

Evaluate all {question_count} questions:"""