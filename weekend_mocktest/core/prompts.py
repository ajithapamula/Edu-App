# weekend_mocktest/core/prompts.py
from typing import List, Dict, Any
from .config import config


class PromptTemplates:
    """
    Optimized prompt templates for AI question generation and evaluation.
    
    Supports:
    - Question bank population with diverse questions
    - Developer exam: aptitude, theory, coding
    - Non-developer exam: MCQ only
    - Evaluation with detailed feedback
    """

    # ================================================================
    # QUESTION BANK GENERATION (NEW)
    # ================================================================
    
    @staticmethod
    def create_bank_generation_prompt(user_type: str, question_type: str,
                                      context: str, count: int) -> str:
        """Create prompt for generating questions for the question bank"""
        
        if user_type == "dev":
            if question_type == "aptitude":
                return PromptTemplates._dev_aptitude_bank_prompt(context, count)
            elif question_type == "theory":
                return PromptTemplates._dev_theory_bank_prompt(context, count)
            elif question_type == "coding":
                return PromptTemplates._dev_coding_bank_prompt(context, count)
        else:
            # Non-developer
            if question_type == "aptitude":
                return PromptTemplates._non_dev_aptitude_bank_prompt(count)
            else:
                return PromptTemplates._non_dev_mcq_bank_prompt(context, count)
        
        raise ValueError(f"Unknown question type: {question_type}")
    
    @staticmethod
    def _non_dev_aptitude_bank_prompt(count: int) -> str:
        """Generate aptitude questions for non-developer (general logical reasoning)"""
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
        """Generate aptitude/logical reasoning questions for developer bank"""
        return f"""You are creating a QUESTION BANK for a developer assessment platform.

Generate EXACTLY {count} UNIQUE aptitude and logical reasoning questions.
These questions test problem-solving ability relevant to a developer's work.

WEEKLY LEARNING CONTEXT:
{context}

IMPORTANT: Create questions that relate to the technologies, concepts, and scenarios 
mentioned in the weekly summaries above. The questions should feel relevant to what 
developers are learning.

QUESTION TYPES TO INCLUDE:
1. Logic puzzles using programming concepts (e.g., "If function A calls B, and B calls C...")
2. Data structure reasoning (e.g., "Given a list of tasks with dependencies...")
3. Algorithm complexity comparison without code
4. System design logic (e.g., "If server X can handle 100 requests...")
5. Pattern recognition with tech scenarios
6. Resource allocation problems
7. Time estimation for development tasks
8. Debugging logic (finding errors through reasoning)

EXAMPLE QUESTION STYLES:
- "A development team has 3 sprints. Sprint 1 completes 40% of features, Sprint 2 completes 35% more..."
- "If a cache hit ratio is 80% and each cache miss costs 50ms, while hits cost 5ms..."
- "A deployment pipeline has 4 stages. If stage 1 fails 10% of the time..."

DIFFICULTY DISTRIBUTION:
- Easy: ~30% (straightforward calculations)
- Medium: ~50% (multi-step reasoning)
- Hard: ~20% (complex scenarios)

FORMAT (STRICT):

=== QUESTION 1 ===
## Title: [Descriptive title related to tech/dev context]
## Difficulty: [Easy/Medium/Hard]
## Type: aptitude
## Tags: [logic, pattern, math, analysis, tech-relevant-tag]
## Question:
[Clear question with all data needed to solve. Make it relevant to developer context.]

=== QUESTION 2 ===
...

CRITICAL RULES:
1. Questions MUST relate to the weekly learning topics when possible
2. Use developer/tech scenarios (sprints, deployments, servers, databases, APIs)
3. Solvable in 2 minutes - no coding required
4. Each question completely unique
5. Include all numbers/data needed to solve

Generate all {count} context-relevant aptitude questions now:"""

    @staticmethod
    def _dev_theory_bank_prompt(context: str, count: int) -> str:
        """Generate theory/conceptual questions for developer bank"""
        return f"""You are creating a QUESTION BANK for a developer assessment platform.

Generate EXACTLY {count} UNIQUE theory and conceptual understanding questions.
These questions test technical knowledge and understanding.

CONTEXT (Weekly Developer Summaries):
{context}

QUESTION REQUIREMENTS:
- Software engineering concepts
- System design principles
- Architecture patterns
- Best practices and conventions
- Technology comparisons
- Debugging strategies
- Performance optimization concepts
- Security principles
- Database concepts
- API design principles

DIFFICULTY DISTRIBUTION:
- Easy: ~30% (fundamental concepts)
- Medium: ~50% (applied understanding)
- Hard: ~20% (deep technical analysis)

CRITICAL RULES:
1. Each question MUST be completely unique
2. Questions should require explanation, not just one-word answers
3. Questions should be answerable in 2 minutes
4. Base questions on concepts from the context
5. Include "why" and "how" questions, not just "what"

FORMAT (STRICT):

=== QUESTION 1 ===
## Title: [Descriptive title]
## Difficulty: [Easy/Medium/Hard]
## Type: theory
## Tags: [architecture, design, security, database, api]
## Question:
[Clear question that requires conceptual understanding to answer]

=== QUESTION 2 ===
## Title: ...
## Difficulty: ...
## Type: theory
## Tags: ...
## Question:
...

Continue for all {count} questions.

IMPORTANT:
- Do NOT include answers
- Questions should test understanding, not memorization
- Vary topics significantly across questions
- Include scenario-based questions
- Make questions practical and relevant

Generate all {count} theory questions now:"""

    @staticmethod
    def _dev_coding_bank_prompt(context: str, count: int) -> str:
        """Generate coding questions for developer bank"""
        return f"""You are creating a QUESTION BANK for a developer assessment platform.

Generate EXACTLY {count} UNIQUE coding challenge questions.
These questions test actual programming and problem-solving skills.

CONTEXT (Weekly Developer Summaries):
{context}

QUESTION REQUIREMENTS:
- Single-function problems (no multi-file setups)
- Clear input/output specifications
- Specific constraints mentioned
- Solvable in 5 minutes
- Language-agnostic (unless context specifies)

QUESTION CATEGORIES:
- Array/string manipulation
- Data structure operations
- Algorithm implementation
- Logic problems
- Pattern-based coding
- Utility function creation
- Bug fixing (provide buggy code to fix)
- Code optimization

DIFFICULTY DISTRIBUTION:
- Easy: ~20% (straightforward implementation)
- Medium: ~60% (requires algorithmic thinking)
- Hard: ~20% (optimization or complex logic)

CRITICAL RULES:
1. Each question MUST be completely unique
2. Clearly specify: Input format, Output format, Constraints
3. Provide at least 2 example test cases
4. No framework-specific questions
5. No database or API questions (pure logic)

FORMAT (STRICT):

=== QUESTION 1 ===
## Title: [Descriptive function name or problem name]
## Difficulty: [Easy/Medium/Hard]
## Type: coding
## Tags: [array, string, algorithm, optimization]
## Question:
[Problem description]

**Input:**
[Describe input format and types]

**Output:**
[Describe expected output format]

**Constraints:**
[List any constraints like array size, value ranges]

**Examples:**
Input: [example input]
Output: [example output]

Input: [another example]
Output: [another output]

=== QUESTION 2 ===
## Title: ...
...

Continue for all {count} questions.

IMPORTANT:
- Do NOT include solutions
- Make problems interesting and practical
- Vary the data structures and algorithms tested
- Include edge cases in examples
- Questions should be solvable in 5 minutes by a competent developer

Generate all {count} coding questions now:"""

    @staticmethod
    def _non_dev_mcq_bank_prompt(context: str, count: int) -> str:
        """Generate MCQ questions from the provided content - content at END for better attention"""
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

    # ================================================================
    # LEGACY: BATCH QUESTIONS PROMPT
    # ================================================================
    
    @staticmethod
    def create_batch_questions_prompt(user_type: str, context: str, 
                                      question_count: int = None) -> str:
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
        theory_count = config.DEV_THEORY_COUNT
        coding_count = config.DEV_CODING_COUNT
        total = aptitude_count + theory_count + coding_count

        return f"""You are conducting a REAL developer technical interview.

Generate EXACTLY {total} questions based on the provided weekly summaries.

CONTEXT (Weekly Developer Summaries):
{context}

MANDATORY QUESTION DISTRIBUTION (STRICT):
- Exactly {aptitude_count} Aptitude / Logical problem-solving questions
- Exactly {theory_count} Theory / Conceptual understanding questions
- Exactly {coding_count} Coding questions (5 minutes each)

TIME CONSTRAINTS:
- Total exam: {config.EXAM_TOTAL_MINUTES} minutes
- Aptitude: {config.APTITUDE_TIME_PER_Q} min/question
- Theory: {config.THEORY_TIME_PER_Q} min/question
- Coding: {config.CODING_TIME_PER_Q} min/question

QUESTION QUALITY RULES:
- REAL interview standards (not academic)
- Progressive difficulty
- Each question must be standalone

CODING QUESTION RULES:
- Single-function problems
- Clear input/output/constraints
- Include 2 examples
- Solvable in 5 minutes

FORMAT (STRICT):

=== QUESTION 1 ===
## Title: [Title]
## Difficulty: [Easy/Medium/Hard]
## Type: [Aptitude/Theory/Coding]
## Question:
[Complete question]

Continue for all {total} questions.

Generate all questions now:"""

    @staticmethod
    def _non_dev_batch_prompt(context: str, question_count: int) -> str:
        """Non-developer MCQ generation prompt"""
        return f"""Generate EXACTLY {question_count} MCQs for non-developer assessment.

CONTEXT:
{context}

RULES:
- ALL questions must be MCQs with 4 options (A, B, C, D)
- Only ONE correct answer
- Mix: Testing (30%), SDLC (30%), Analysis (40%)

FORMAT:

=== QUESTION 1 ===
## Title: [Title]
## Difficulty: [Easy/Medium/Hard]
## Type: [Aptitude/Theory/Process]
## Question:
[MCQ question]
## Options:
A) [Option]
B) [Option]
C) [Option]
D) [Option]

Continue for all {question_count} questions.

Generate now:"""

    # ================================================================
    # SECTION-WISE EVALUATION PROMPTS (NEW)
    # ================================================================
    
    @staticmethod
    def create_section_evaluation_prompt(section_type: str, 
                                         qa_pairs: List[Dict[str, Any]]) -> str:
        """Create evaluation prompt for specific section type"""
        
        question_count = len(qa_pairs)
        
        # Format Q&A pairs - CLEARLY label user's answer
        formatted = []
        for i, qa in enumerate(qa_pairs, 1):
            q = qa.get("question", "")
            a = qa.get("answer", "")
            # Make it VERY clear what the user wrote
            formatted.append(f"""
════════════════════════════════════════
QUESTION {i}:
════════════════════════════════════════
{q}

┌──────────────────────────────────────┐
│ USER'S SUBMITTED ANSWER:             │
└──────────────────────────────────────┘
{a if a.strip() else "[USER LEFT THIS BLANK - SCORE 0]"}
""")
        
        qa_content = "\n".join(formatted)
        
        if section_type == "aptitude":
            return PromptTemplates._aptitude_evaluation_prompt(qa_content, question_count)
        elif section_type == "theory":
            return PromptTemplates._theory_evaluation_prompt(qa_content, question_count)
        elif section_type == "coding":
            return PromptTemplates._coding_evaluation_prompt(qa_content, question_count)
        else:
            return PromptTemplates._general_evaluation_prompt(qa_content, question_count)
    
    @staticmethod
    def _aptitude_evaluation_prompt(qa_content: str, question_count: int) -> str:
        """Evaluation prompt for APTITUDE section - with correct answers"""
        return f"""You are a STRICT evaluator. Evaluate the user's submitted answers.

⚠️ CRITICAL: Evaluate what the USER wrote, NOT generate your own answers first.

{qa_content}

═══════════════════════════════════════════════════════════════
EVALUATION TASK
═══════════════════════════════════════════════════════════════

For EACH question:
1. Calculate the CORRECT answer
2. Compare with USER'S answer
3. Score: 1 if correct (or very close), 0 if wrong

OUTPUT FORMAT:

SCORES: [{','.join(['0 or 1'] * question_count)}]

DETAILED FEEDBACK:

------- Question 1 -------
📝 Question: [Brief question summary]
✅ Correct Answer: [The correct answer with brief explanation]
👤 User's Answer: [What user wrote]
📊 Score: [0 or 1]
💡 Explanation: [Why correct/incorrect, how to solve]

------- Question 2 -------
📝 Question: [Brief question summary]
✅ Correct Answer: [The correct answer]
👤 User's Answer: [What user wrote]
📊 Score: [0 or 1]
💡 Explanation: [Why correct/incorrect]

(Continue for all {question_count} questions)

═══════════════════════════════════════════════════════════════
SECTION SUMMARY
═══════════════════════════════════════════════════════════════
📈 Total Score: X/{question_count}
🎯 Percentage: X%
💪 Strengths: [What user did well]
📚 Areas to Improve: [Topics to study]
🔑 Key Concepts: [Important formulas/methods to remember]

Evaluate now:"""

    @staticmethod
    def _theory_evaluation_prompt(qa_content: str, question_count: int) -> str:
        """Evaluation prompt for THEORY section - with correct answers"""
        return f"""You are a STRICT evaluator. Evaluate the user's submitted answers.

⚠️ CRITICAL: Evaluate what the USER wrote, check if they covered key concepts.

{qa_content}

═══════════════════════════════════════════════════════════════
EVALUATION TASK
═══════════════════════════════════════════════════════════════

For EACH question:
1. Identify KEY POINTS a correct answer should have
2. Check if USER's answer covers those points
3. Score: 1 if demonstrates understanding, 0 if wrong/incomplete

OUTPUT FORMAT:

SCORES: [{','.join(['0 or 1'] * question_count)}]

DETAILED FEEDBACK:

------- Question 1 -------
📝 Question: [Brief question summary]
✅ Expected Answer: [Complete correct answer with key points]
👤 User's Answer: [Summary of what user wrote]
📊 Score: [0 or 1]
💡 Feedback: [What was right/wrong, missing points]

------- Question 2 -------
📝 Question: [Brief question summary]
✅ Expected Answer: [Complete correct answer]
👤 User's Answer: [Summary of what user wrote]
📊 Score: [0 or 1]
💡 Feedback: [What was right/wrong]

(Continue for all {question_count} questions)

═══════════════════════════════════════════════════════════════
SECTION SUMMARY
═══════════════════════════════════════════════════════════════
📈 Total Score: X/{question_count}
🎯 Percentage: X%
💪 Topics Understood: [List topics user knows well]
📚 Topics to Study: [List topics user needs to review]
🔑 Key Concepts: [Important definitions/concepts to remember]

Evaluate now:"""

    @staticmethod
    def _coding_evaluation_prompt(qa_content: str, question_count: int) -> str:
        """Evaluation prompt for CODING section - with correct answers"""
        return f"""You are a STRICT evaluator. Evaluate the user's submitted code.

⚠️ CRITICAL: Check if USER's code would actually work correctly.

{qa_content}

═══════════════════════════════════════════════════════════════
EVALUATION TASK
═══════════════════════════════════════════════════════════════

For EACH question:
1. Understand what the problem requires
2. Check if USER's code solves it correctly
3. Score: 1 if code would work (or minor bugs), 0 if wrong logic

OUTPUT FORMAT:

SCORES: [{','.join(['0 or 1'] * question_count)}]

DETAILED FEEDBACK:

------- Question 1 -------
📝 Problem: [Brief problem description]
✅ Correct Approach: [Explain the right algorithm/approach]
✅ Sample Solution:
```
[Provide a correct code solution]
```
👤 User's Code: [Summary of user's approach]
📊 Score: [0 or 1]
💡 Feedback: [What was right/wrong, bugs found, improvements]

------- Question 2 -------
📝 Problem: [Brief problem description]
✅ Correct Approach: [Explain the right algorithm]
✅ Sample Solution:
```
[Provide a correct code solution]
```
👤 User's Code: [Summary of user's approach]
📊 Score: [0 or 1]
💡 Feedback: [What was right/wrong]

(Continue for all {question_count} questions)

═══════════════════════════════════════════════════════════════
SECTION SUMMARY
═══════════════════════════════════════════════════════════════
📈 Total Score: X/{question_count}
🎯 Percentage: X%
💪 Coding Strengths: [What user did well]
📚 Areas to Improve: [Concepts to practice]
🔑 Tips: [Coding tips and best practices]

Evaluate now:"""

    @staticmethod
    def _general_evaluation_prompt(qa_content: str, question_count: int) -> str:
        """General evaluation prompt fallback"""
        return f"""Evaluate these assessment answers.

QUESTIONS & ANSWERS:
{qa_content}

SCORING: 1 = Correct/Acceptable, 0 = Incorrect

OUTPUT FORMAT:
SCORES: [{','.join(['0 or 1'] * question_count)}]

FEEDBACK:
Q1: [Feedback]
Q2: [Feedback]
...

Evaluate all {question_count} questions:"""

    # ================================================================
    # EVALUATION PROMPTS (EXISTING)
    # ================================================================
    
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

        if user_type == "dev":
            return PromptTemplates._dev_evaluation_prompt(qa_content, question_count)
        else:
            return PromptTemplates._non_dev_evaluation_prompt(qa_content, question_count)

    @staticmethod
    def _dev_evaluation_prompt(qa_content: str, question_count: int) -> str:
        """Developer answers evaluation prompt"""
        return f"""Evaluate this developer assessment comprehensively.

ASSESSMENT CONTENT:
{qa_content}

EVALUATION BY QUESTION TYPE:
- APTITUDE: Logical reasoning, problem-solving approach (30%)
- THEORY: Conceptual accuracy, depth of understanding (30%)
- CODING: Correctness, efficiency, code quality (40%)

SCORING RULES:
- 1 = Acceptable/Correct (demonstrates competency)
- 0 = Unacceptable/Incorrect

REQUIRED OUTPUT FORMAT:
SCORES: [{','.join(['0 or 1'] * question_count)}]
FEEDBACK: [Q1 feedback|Q2 feedback|Q3 feedback|...]

DETAILED ANALYSIS:
- Section-wise performance
- Strengths observed
- Areas for improvement
- Overall assessment

Evaluate all {question_count} questions:"""

    @staticmethod
    def _non_dev_evaluation_prompt(qa_content: str, question_count: int) -> str:
        """Non-developer evaluation prompt - STRICT MCQ evaluation"""
        return f"""You are evaluating a professional MCQ assessment. Be STRICT with scoring.

{qa_content}

═══════════════════════════════════════════════════════════════
STRICT EVALUATION RULES
═══════════════════════════════════════════════════════════════

FOR MCQ QUESTIONS:
- Score 1 ONLY if user selected the EXACT correct option
- Score 0 if user selected wrong option, even if "close"
- NO partial credit for MCQ - it's either right (1) or wrong (0)

FOR APTITUDE QUESTIONS:
- Score 1 ONLY if the numerical answer is EXACTLY correct
- Score 0 if answer is wrong, even if the approach was good
- "Close" answers still get 0

SAP T-CODE REFERENCE (if SAP questions are present):
- SCC4 = Client Administration
- SCCL = Local Client Copy
- SCC3 = View Client Copy Logs

OUTPUT FORMAT:

SCORES: [{','.join(['0 or 1'] * question_count)}]

DETAILED FEEDBACK:

------- Question 1 -------
📝 Question: [Question text]
✅ Correct Answer: [The EXACT correct answer]
👤 User Selected: [What user chose]
📊 Score: [1 if EXACTLY correct, 0 if wrong]
💡 Explanation: [Why correct/incorrect]

------- Question 2 -------
📝 Question: [Question text]
✅ Correct Answer: [The EXACT correct answer]
👤 User Selected: [What user chose]
📊 Score: [1 if EXACTLY correct, 0 if wrong]
💡 Explanation: [Brief explanation]

(Continue for all {question_count} questions)

═══════════════════════════════════════════════════════════════
SUMMARY
═══════════════════════════════════════════════════════════════
📈 Total Score: X/{question_count}
🎯 Percentage: X%
💪 Strong Areas: [List specific topics from questions user answered correctly]
📚 Areas to Improve: [List specific topics from questions user got wrong]
🔑 Key Concepts from This Test: [Extract 3-5 important concepts based on the ACTUAL questions in this test]

Be STRICT - only give 1 for EXACT correct answers!

Evaluate now:"""


class PromptValidator:
    """Validation utilities for prompts and responses"""
    
    @staticmethod
    def validate_question_response(response: str, user_type: str, 
                                   expected_count: int) -> Dict[str, Any]:
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
            validation["issues"].append(
                f"Expected {expected_count} questions, found {question_markers}"
            )
        
        required_sections = ["## Title:", "## Difficulty:", "## Type:", "## Question:"]
        if user_type == "non_dev":
            required_sections.append("## Options:")
        
        for section in required_sections:
            count = response.count(section)
            if count < expected_count:
                validation["issues"].append(f"Missing {section} ({count}/{expected_count})")
        
        return validation
    
    @staticmethod
    def validate_evaluation_response(response: str, expected_count: int) -> Dict[str, Any]:
        """Validate evaluation response"""
        import re
        
        validation = {
            "valid": True,
            "issues": [],
            "has_scores": False,
            "has_feedback": False,
            "score_count": 0
        }
        
        if "SCORES:" in response:
            validation["has_scores"] = True
            score_match = re.search(r'SCORES:\s*\[(.*?)\]', response)
            if score_match:
                scores = score_match.group(1).split(',')
                validation["score_count"] = len([s for s in scores if s.strip() in ['0', '1']])
                
                if validation["score_count"] != expected_count:
                    validation["valid"] = False
                    validation["issues"].append(
                        f"Expected {expected_count} scores, found {validation['score_count']}"
                    )
        else:
            validation["valid"] = False
            validation["issues"].append("Missing SCORES section")
        
        if "FEEDBACK:" in response:
            validation["has_feedback"] = True
        else:
            validation["issues"].append("Missing FEEDBACK section (non-critical)")
        
        return validation