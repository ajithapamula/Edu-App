# weekend_mocktest/core/ai_services.py
# ═══════════════════════════════════════════════════════════════════
# REPLACE your existing ai_services.py with this file
#
# WHAT'S NEW (all inside AIService class, no new files):
#   - execute_code()          → Run code via Piston API
#   - run_test_cases()        → HackerRank-style test runner
#   - generate_test_cases()   → AI generates test cases for existing Qs
#   - _parse_test_cases_from_section() → Parse TC lines from AI response
#   - evaluate_code_with_test_results() → Score based on Piston results
#   - Overall result: Accepted/Wrong Answer/Runtime Error/Compilation Error/TLE
#
# REQUIRES: pip install httpx
# ═══════════════════════════════════════════════════════════════════

import json
import logging
import os
import re
import random
import time
import asyncio
from typing import Dict, List, Optional, Any

import httpx
from groq import Groq

from .config import config
from .prompts import PromptTemplates

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# PISTON LANGUAGE CONFIG (matches frontend compilerService.js)
# ═══════════════════════════════════════════════════════════════════

SUPPORTED_LANGUAGES = {
    "python":     {"piston_id": "python",     "version": "3.10.0",  "ext": ".py",   "label": "Python 3",   "run_timeout": 5000,  "compile_timeout": 10000},
    "javascript": {"piston_id": "javascript", "version": "18.15.0", "ext": ".js",   "label": "JavaScript", "run_timeout": 5000,  "compile_timeout": 10000},
    "java":       {"piston_id": "java",       "version": "15.0.2",  "ext": ".java", "label": "Java",       "run_timeout": 10000, "compile_timeout": 15000},
    "cpp":        {"piston_id": "c++",        "version": "10.2.0",  "ext": ".cpp",  "label": "C++",        "run_timeout": 5000,  "compile_timeout": 15000},
    "c":          {"piston_id": "c",          "version": "10.2.0",  "ext": ".c",    "label": "C",          "run_timeout": 5000,  "compile_timeout": 15000},
    "typescript": {"piston_id": "typescript", "version": "5.0.3",   "ext": ".ts",   "label": "TypeScript", "run_timeout": 5000,  "compile_timeout": 10000},
}


class AIService:
    """
    AI service: Groq for question generation/evaluation + Piston for code execution.
    Everything in one class — no new files needed.
    """

    CODING_QUESTION_INDICATORS = [
        'write a program', 'write a function', 'write a script',
        'write code', 'write python', 'implement a function',
        'create a function', 'create a program', 'create a class',
        'code to', 'program to', 'script to',
        'in python', 'in java', 'in javascript', 'using python',
        'python program', 'python function', 'python code',
        'java program', 'javascript function',
        'def ', 'class ', 'import ', 'from ', 'return ',
        'print(', 'input(', 'len(', 'range(', 'for i in',
        '>>>', '```python', '```java', '```',
        'if __name__', 'try:', 'except:', 'lambda',
        '__init__', 'self.', '.py',
        'recursion', 'algorithm', 'data structure',
        'loop', 'iterate', 'compile', 'debug',
        'syntax error', 'runtime error', 'exception handling',
        'output:', 'input:', 'expected output',
    ]

    SAP_BUSINESS_TERMS = [
        'sap', 'erp', 'enterprise', 'business', 'company', 'organization',
        'mm', 'sd', 'fico', 'hr', 'pp', 'wm', 'qm', 'pm',
        'procurement', 'purchase', 'vendor', 'supplier',
        'sales', 'customer', 'billing', 'invoice', 'payment',
        'finance', 'accounting', 'ledger', 'cost', 'profit',
        'material', 'inventory', 'stock', 'warehouse',
        'master data', 'transaction', 'document',
    ]

    def __init__(self):
        # ─── Groq AI client ───
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = config.GROQ_MODEL

        # ─── Piston API client (code execution) ───
        self.piston_primary = os.getenv("PISTON_API_URL", "").rstrip("/")
        self.piston_fallback = "https://emkc.org/api/v2/piston"
        self.piston_url = self.piston_primary if self.piston_primary else self.piston_fallback
        self.piston_primary_healthy = bool(self.piston_primary)
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            verify=False,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )

        logger.info(f"AIService initialized | Groq: {self.model} | Piston: {self.piston_url}")


    # ══════════════════════════════════════════════════════════════════
    #  SECTION 1: PISTON CODE EXECUTION
    # ══════════════════════════════════════════════════════════════════

    async def execute_code(self, language: str, code: str, stdin: str = "") -> Dict[str, Any]:
        """
        Execute code via Piston API with primary/fallback.

        Returns:
        {
            "success": bool,
            "stdout": "output text",
            "stderr": "error text",
            "exit_code": 0,
            "execution_time_ms": 45,
            "language": "Python 3",
            "is_compile_error": false,
            "is_runtime_error": false,
            "is_timeout": false,
            "overall_result": "Accepted" | "Compilation Error" | "Runtime Error" | "Time Limit Exceeded"
        }
        """
        start = time.time()

        lang = SUPPORTED_LANGUAGES.get(language)
        if not lang:
            return self._exec_error(f"Unsupported language: {language}", start)
        if not code or not code.strip():
            return self._exec_error("No code provided", start)
        if len(code) > 100_000:
            return self._exec_error("Code exceeds 100KB limit", start)

        payload = {
            "language": lang["piston_id"],
            "version": lang["version"],
            "files": [{"name": f"main{lang['ext']}", "content": code}],
            "stdin": stdin or "",
            "compile_timeout": lang["compile_timeout"],
            "run_timeout": lang["run_timeout"],
            "compile_memory_limit": -1,
            "run_memory_limit": -1,
        }

        # Try primary Piston server, fallback to public emkc.org
        urls = []
        if self.piston_primary_healthy and self.piston_primary:
            urls.append(self.piston_primary)
        urls.append(self.piston_fallback)

        last_err = "No Piston URL available"
        for url in urls:
            try:
                resp = await self.http_client.post(
                    f"{url}/api/v2/execute", json=payload,
                    headers={"Content-Type": "application/json"},
                )
                if resp.status_code != 200:
                    last_err = f"Piston HTTP {resp.status_code}"
                    if url == self.piston_primary:
                        self.piston_primary_healthy = False
                    continue

                data = resp.json()
                ms = int((time.time() - start) * 1000)

                run = data.get("run", {})
                comp = data.get("compile", {})

                # ─── Compilation Error ───
                if comp.get("stderr") and comp.get("code", 0) != 0:
                    return {
                        "success": False,
                        "stdout": "",
                        "stderr": comp["stderr"],
                        "exit_code": comp.get("code", 1),
                        "execution_time_ms": ms,
                        "language": lang["label"],
                        "is_compile_error": True,
                        "is_runtime_error": False,
                        "is_timeout": False,
                        "overall_result": "Compilation Error",
                    }

                has_err = bool(run.get("stderr", "").strip())
                is_timeout = (run.get("signal") == "SIGKILL" or
                              "timed out" in run.get("stderr", ""))

                # ─── Determine overall result ───
                if is_timeout:
                    overall = "Time Limit Exceeded"
                elif has_err or run.get("code", -1) != 0:
                    overall = "Runtime Error"
                else:
                    overall = "Accepted"

                return {
                    "success": run.get("code", -1) == 0 and not has_err,
                    "stdout": run.get("stdout", ""),
                    "stderr": run.get("stderr", ""),
                    "exit_code": run.get("code", -1),
                    "execution_time_ms": ms,
                    "language": lang["label"],
                    "is_compile_error": False,
                    "is_runtime_error": has_err and not is_timeout,
                    "is_timeout": is_timeout,
                    "overall_result": overall,
                }

            except httpx.TimeoutException:
                last_err = "Piston timeout"
                if url == self.piston_primary:
                    self.piston_primary_healthy = False
            except Exception as e:
                last_err = str(e)
                if url == self.piston_primary:
                    self.piston_primary_healthy = False

        return self._exec_error(f"Execution failed: {last_err}", start)

    async def run_test_cases(self, language: str, code: str,
                             test_cases: List[Dict]) -> Dict[str, Any]:
        """
        HackerRank-style test runner: execute code per test case, compare stdout.

        Input test_cases format:
        [
            {
                "id": 1,
                "input": "3\\n5",
                "expected_output": "8",
                "is_hidden": false,
                "label": "Test Case 1",
                "weight": 1
            }
        ]

        Returns:
        {
            "results": [
                {
                    "id": 1, "label": "Test Case 1", "passed": true,
                    "input": "3\\n5", "expected_output": "8", "actual_output": "8",
                    "execution_time_ms": 45, "stderr": "",
                    "is_compile_error": false, "is_runtime_error": false,
                    "is_timeout": false, "is_hidden": false, "weight": 1
                }
            ],
            "total_passed": 4, "total_failed": 1, "total_cases": 5,
            "all_passed": false, "score_percentage": 80.0,
            "overall_result": "Wrong Answer",
            "execution_summary": "4/5 test cases passed (80.0%)"
        }
        """
        if not test_cases:
            return {
                "results": [], "total_passed": 0, "total_failed": 0,
                "total_cases": 0, "all_passed": False, "score_percentage": 0.0,
                "overall_result": "No Test Cases",
                "execution_summary": "No test cases provided",
            }

        sem = asyncio.Semaphore(5)  # max 5 concurrent executions

        async def _run_one(tc):
            async with sem:
                tc_id = tc.get("id", 0)
                tc_input = tc.get("input", "")
                expected = tc.get("expected_output", "").strip()
                is_hidden = tc.get("is_hidden", False)
                weight = tc.get("weight", 1)
                label = tc.get("label", f"Test Case {tc_id}")

                res = await self.execute_code(language, code, stdin=tc_input)
                actual = res.get("stdout", "").strip()

                passed = False
                if res.get("exit_code", -1) == 0 and not res.get("is_compile_error"):
                    # Exact match first
                    if actual == expected:
                        passed = True
                    else:
                        # Line-by-line comparison (strip trailing whitespace)
                        a_lines = [l.rstrip() for l in actual.split("\n")]
                        e_lines = [l.rstrip() for l in expected.split("\n")]
                        passed = a_lines == e_lines

                return {
                    "id": tc_id,
                    "label": label,
                    "passed": passed,
                    "is_hidden": is_hidden,
                    "weight": weight,
                    "input": tc_input if not is_hidden else "[Hidden]",
                    "expected_output": expected if not is_hidden else "[Hidden]",
                    "actual_output": actual if not is_hidden else (
                        "[Hidden]" if not passed else actual
                    ),
                    "execution_time_ms": res.get("execution_time_ms", 0),
                    "stderr": res.get("stderr", "") if not is_hidden else "",
                    "is_compile_error": res.get("is_compile_error", False),
                    "is_runtime_error": res.get("is_runtime_error", False),
                    "is_timeout": res.get("is_timeout", False),
                }

        results = await asyncio.gather(*[_run_one(tc) for tc in test_cases])
        results = sorted(results, key=lambda r: r["id"])

        total_passed = sum(1 for r in results if r["passed"])
        total_weight = sum(r["weight"] for r in results) or 1
        passed_weight = sum(r["weight"] for r in results if r["passed"])
        score_pct = round((passed_weight / total_weight) * 100, 1)

        # Determine overall result
        has_compile = any(r["is_compile_error"] for r in results)
        has_runtime = any(r["is_runtime_error"] for r in results)
        has_timeout = any(r["is_timeout"] for r in results)

        if has_compile:
            overall = "Compilation Error"
        elif has_timeout:
            overall = "Time Limit Exceeded"
        elif has_runtime:
            overall = "Runtime Error"
        elif total_passed == len(results):
            overall = "Accepted"
        else:
            overall = "Wrong Answer"

        summary = (
            f"All {len(results)} test cases passed!"
            if total_passed == len(results)
            else f"{total_passed}/{len(results)} test cases passed ({score_pct}%)"
        )

        logger.info(f"Test run: {summary} | Result: {overall}")

        return {
            "results": results,
            "total_passed": total_passed,
            "total_failed": len(results) - total_passed,
            "total_cases": len(results),
            "all_passed": total_passed == len(results),
            "score_percentage": score_pct,
            "overall_result": overall,
            "execution_summary": summary,
        }

    def _exec_error(self, msg: str, start: float) -> Dict[str, Any]:
        return {
            "success": False, "stdout": "", "stderr": msg,
            "exit_code": -1,
            "execution_time_ms": int((time.time() - start) * 1000),
            "language": "unknown",
            "is_compile_error": False, "is_runtime_error": False,
            "is_timeout": False, "overall_result": "System Error",
        }


    # ══════════════════════════════════════════════════════════════════
    #  SECTION 2: TEST CASE PARSING & GENERATION
    # ══════════════════════════════════════════════════════════════════

    def _parse_test_cases_from_section(self, part: str) -> List[Dict]:
        """
        Parse ## TestCases: block from AI-generated coding question.
        Format: TC1|VISIBLE|3\\n5|8
        """
        test_cases = []

        tc_match = re.search(r'##\s*TestCases:\s*\n(.+?)(?=\n\n|===|$)', part, re.DOTALL)
        if not tc_match:
            return test_cases

        for line in tc_match.group(1).strip().split('\n'):
            line = line.strip()
            if not line.startswith('TC'):
                continue
            parts = line.split('|', 3)
            if len(parts) < 4:
                continue

            id_match = re.search(r'(\d+)', parts[0])
            tc_id = int(id_match.group(1)) if id_match else len(test_cases) + 1

            test_cases.append({
                "id": tc_id,
                "input": parts[2].strip().replace('\\n', '\n'),
                "expected_output": parts[3].strip().replace('\\n', '\n'),
                "is_hidden": parts[1].strip().upper() == "HIDDEN",
                "label": f"Test Case {tc_id}",
                "weight": 1,
            })

        return test_cases

    def generate_test_cases(self, question: str, num_cases: int = 5) -> List[Dict]:
        """
        Generate test cases for an existing coding question that has none.
        Called when a question was created before test case support was added.
        """
        try:
            prompt = PromptTemplates.create_test_cases_prompt(question, num_cases)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Output ONLY test case lines in TC format. Nothing else."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3, max_tokens=1000,
            )
            content = response.choices[0].message.content.strip()

            test_cases = []
            for line in content.split('\n'):
                line = line.strip()
                if not line.startswith('TC'):
                    continue
                parts = line.split('|', 3)
                if len(parts) < 4:
                    continue
                id_match = re.search(r'(\d+)', parts[0])
                tc_id = int(id_match.group(1)) if id_match else len(test_cases) + 1
                test_cases.append({
                    "id": tc_id,
                    "input": parts[2].strip().replace('\\n', '\n'),
                    "expected_output": parts[3].strip().replace('\\n', '\n'),
                    "is_hidden": parts[1].strip().upper() == "HIDDEN",
                    "label": f"Test Case {tc_id}",
                    "weight": 1,
                })

            logger.info(f"Generated {len(test_cases)} test cases for question")
            return test_cases
        except Exception as e:
            logger.error(f"Test case generation failed: {e}")
            return []


    # ══════════════════════════════════════════════════════════════════
    #  SECTION 3: CONTENT FILTERING (unchanged from your original)
    # ══════════════════════════════════════════════════════════════════

    def _is_coding_question(self, question_data: Dict) -> bool:
        question_text = str(question_data.get("question", "")).lower()
        title = str(question_data.get("title", "")).lower()
        options = question_data.get("options", [])
        options_text = ""
        if isinstance(options, list):
            options_text = " ".join([str(opt) for opt in options]).lower()
        elif isinstance(options, dict):
            options_text = " ".join([str(v) for v in options.values()]).lower()
        combined = f"{question_text} {title} {options_text}"

        for sap_term in self.SAP_BUSINESS_TERMS:
            if sap_term in combined:
                return False
        for indicator in self.CODING_QUESTION_INDICATORS:
            if indicator in combined:
                return True
        code_patterns = [
            r'def\s+\w+\s*\(', r'class\s+\w+\s*[:\(]',
            r'import\s+\w+', r'from\s+\w+\s+import',
            r'print\s*\(["\']', r'\w+\s*=\s*\[',
            r'for\s+\w+\s+in\s+', r'while\s+\w+\s*[:<]',
        ]
        for pattern in code_patterns:
            if re.search(pattern, combined):
                return True
        return False

    def _filter_coding_questions_for_nondev(self, questions: List[Dict]) -> List[Dict]:
        filtered = []
        blocked = 0
        for q in questions:
            if q.get("question_type") == "coding":
                blocked += 1
                continue
            if self._is_coding_question(q):
                blocked += 1
            else:
                filtered.append(q)
        if blocked:
            logger.info(f"Blocked {blocked} programming questions for non-dev")
        return filtered


    # ══════════════════════════════════════════════════════════════════
    #  SECTION 4: QUESTION GENERATION (coding now parses test cases)
    # ══════════════════════════════════════════════════════════════════

    def generate_questions_for_bank(self, user_type: str, question_type: str,
                                    context: str, count: int) -> List[Dict]:
        if user_type == "non_dev" and question_type == "coding":
            logger.warning("Blocked coding generation for non-dev")
            return []

        logger.info(f"Generating {count} {question_type} questions for {user_type}")

        try:
            prompt = PromptTemplates.create_bank_generation_prompt(
                user_type, question_type, context, count
            )
            if not prompt:
                return []

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert question generator. Follow the format exactly."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=6000 if question_type == "coding" else 4000,
            )

            content = response.choices[0].message.content
            questions = self._parse_questions(content, question_type)

            for q in questions:
                q["question_type"] = question_type
                q["user_type"] = user_type

            if user_type == "non_dev":
                questions = self._filter_coding_questions_for_nondev(questions)

            logger.info(f"Generated {len(questions)} {question_type} questions")
            return questions

        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return []


    # ══════════════════════════════════════════════════════════════════
    #  SECTION 5: QUESTION PARSING (now handles ## TestCases:)
    # ══════════════════════════════════════════════════════════════════

    def _parse_questions(self, content: str, question_type: str = "mcq") -> List[Dict]:
        questions = []

        try:
            parts = re.split(r'===\s*QUESTION\s*\d+\s*===', content)

            for part in parts:
                if not part.strip():
                    continue

                q = {}

                title_match = re.search(r'##\s*Title:\s*(.+)', part)
                if title_match:
                    q['title'] = title_match.group(1).strip()

                diff_match = re.search(r'##\s*Difficulty:\s*(\w+)', part)
                if diff_match:
                    q['difficulty'] = diff_match.group(1).strip()

                q_match = re.search(
                    r'##\s*Question:\s*\n(.+?)(?=##\s*Options:|##\s*TestCases:|$)',
                    part, re.DOTALL
                )
                if q_match:
                    q['question'] = q_match.group(1).strip()

                # MCQ options
                opts_match = re.search(
                    r'##\s*Options:\s*\n(.+?)(?=##\s*Correct:|$)',
                    part, re.DOTALL
                )
                if opts_match:
                    options = []
                    for opt in re.findall(r'[A-D]\)\s*(.+)', opts_match.group(1)):
                        options.append(opt.strip())
                    if options:
                        q['options'] = options

                correct_match = re.search(r'##\s*Correct:\s*([A-Da-d])', part)
                if correct_match:
                    letter = correct_match.group(1).upper()
                    q['correct_answer'] = letter
                    if q.get('options'):
                        idx = ord(letter) - ord('A')
                        if 0 <= idx < len(q['options']):
                            q['correct_option_text'] = q['options'][idx]

                # ─── NEW: Parse test cases for coding questions ───
                if question_type == "coding":
                    test_cases = self._parse_test_cases_from_section(part)
                    if test_cases:
                        q['test_cases'] = test_cases

                if q.get('question'):
                    questions.append(q)

            if questions:
                return questions
        except Exception as e:
            logger.warning(f"Parse error: {e}")

        # Fallback: try JSON
        try:
            return json.loads(content)
        except:
            pass
        try:
            match = re.search(r'\[[\s\S]*\]', content)
            if match:
                return json.loads(match.group())
        except:
            pass

        return []


    # ══════════════════════════════════════════════════════════════════
    #  SECTION 6: CODE EVALUATION
    # ══════════════════════════════════════════════════════════════════

    def evaluate_code_with_test_results(self, question: str, user_code: str,
                                        test_results: Dict) -> Dict:
        """
        Evaluate coding answer using actual Piston test execution results.
        Score = passed_test_cases / total_test_cases
        """
        all_passed = test_results.get("all_passed", False)
        correct_solution = self.generate_correct_code(question)

        explanation = self.generate_coding_explanation(
            question, user_code, correct_solution["code"],
            all_passed, test_results
        )

        return {
            "is_correct": all_passed,
            "correct_code": correct_solution["code"],
            "explanation": explanation,
            "test_case_results": test_results,
            "overall_result": test_results.get("overall_result", "Unknown"),
        }

    def evaluate_code_answer(self, question: str, user_code: str) -> Dict:
        """Fallback: AI-only code evaluation (when Piston not used)."""
        try:
            correct_solution = self.generate_correct_code(question)
            correct_code = correct_solution["code"]

            prompt = f"""Compare the student's code with the correct solution.

Question: {question}

Student's Code:
{user_code if user_code else "(No answer)"}

Correct Code:
{correct_code}

Respond EXACTLY:
IS_CORRECT: YES or NO
ISSUES: List issues or "None" """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a strict code evaluator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2, max_tokens=300,
            )

            content = response.choices[0].message.content.strip()
            is_correct = "IS_CORRECT: YES" in content.upper()

            explanation = self.generate_coding_explanation(
                question, user_code, correct_code, is_correct
            )

            return {
                "is_correct": is_correct,
                "correct_code": correct_code,
                "explanation": explanation,
                "test_case_results": None,
                "overall_result": "Accepted" if is_correct else "Wrong Answer",
            }
        except Exception as e:
            logger.error(f"Code evaluation failed: {e}")
            correct_solution = self.generate_correct_code(question)
            return {
                "is_correct": False,
                "correct_code": correct_solution["code"],
                "explanation": "Evaluation failed.",
                "test_case_results": None,
                "overall_result": "System Error",
            }


    # ══════════════════════════════════════════════════════════════════
    #  SECTION 7: EXPLANATION GENERATION
    # ══════════════════════════════════════════════════════════════════

    def generate_correct_code(self, question: str) -> Dict[str, str]:
        """Generate correct Python solution for a coding question."""
        try:
            prompt = f"""Write correct Python code for:
{question}

Requirements: Use input() for stdin, print() for stdout. Simple and clean.
Return ONLY code inside ```python``` block."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Return only code in ```python``` block."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3, max_tokens=600,
            )

            content = response.choices[0].message.content.strip()
            code_match = re.search(r'```python\s*(.*?)\s*```', content, re.DOTALL)
            if code_match:
                code = code_match.group(1).strip()
            else:
                code_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
                code = code_match.group(1).strip() if code_match else content

            return {"code": code, "explanation": ""}
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return {"code": "# Unable to generate", "explanation": ""}

    def generate_explanation(self, question: str, user_answer: str, correct_answer: str,
                            question_type: str, options: List[str] = None) -> str:
        """Generate AI explanation for MCQ/aptitude questions."""
        try:
            options_text = ""
            if options:
                options_text = "\nOptions:\n" + "\n".join(
                    [f"{chr(65+i)}) {opt}" for i, opt in enumerate(options)]
                )

            prompt = f"""Question: {question}{options_text}
User's Answer: {user_answer}
Correct Answer: {correct_answer}

Brief explanation (2-3 sentences): why correct answer is right, user's mistake if wrong."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Brief educational explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5, max_tokens=200,
            )
            return response.choices[0].message.content.strip()
        except:
            return f"The correct answer is: {correct_answer}"

    def generate_coding_explanation(self, question: str, user_code: str,
                                    correct_code: str, is_correct: bool,
                                    test_results: Dict = None) -> str:
        """Generate AI explanation for coding questions (with test result context)."""
        try:
            tc_context = ""
            if test_results:
                p = test_results.get("total_passed", 0)
                t = test_results.get("total_cases", 0)
                tc_context = f"\nTest Results: {p}/{t} passed. Overall: {test_results.get('overall_result', 'N/A')}"
                # Show first failing test for better AI feedback
                failed = [r for r in test_results.get("results", [])
                          if not r["passed"] and not r.get("is_hidden")]
                if failed:
                    f = failed[0]
                    tc_context += (f"\nFirst fail: input='{f.get('input','')}', "
                                   f"expected='{f.get('expected_output','')}', "
                                   f"got='{f.get('actual_output','')}'")

            if is_correct:
                prompt = f"Student's code passed all tests.{tc_context}\nBrief positive feedback (1-2 sentences)."
            else:
                prompt = f"""Student's code failed.{tc_context}
Question: {question}
Student: {user_code[:400]}
Correct: {correct_code[:400]}
Brief explanation (2-3 sentences): what's wrong and how to fix."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Python tutor. Brief feedback."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5, max_tokens=200,
            )
            return response.choices[0].message.content.strip()
        except:
            return ("Correct! All test cases passed." if is_correct
                    else "Review the correct solution.")

    def generate_batch_explanations(self, qa_pairs: List[Dict],
                                    question_type: str) -> List[str]:
        """Generate explanations for a batch of questions."""
        explanations = []
        for qa in qa_pairs:
            question = qa.get("question", "")
            user_answer = qa.get("answer", "No answer")
            correct_answer = (qa.get("correct_option_text") or
                              qa.get("correct_answer", "N/A"))
            options = qa.get("options", [])
            is_correct = qa.get("is_correct", False)

            if question_type == "coding":
                correct_code = qa.get("generated_correct_code", "")
                tc_results = qa.get("test_case_results")
                explanation = self.generate_coding_explanation(
                    question, user_answer, correct_code, is_correct, tc_results
                )
            elif is_correct:
                explanation = random.choice([
                    "Correct! Well done.", "Excellent! Right answer.",
                    "Correct! Good understanding.", "Well done!",
                ])
            else:
                explanation = self.generate_explanation(
                    question, user_answer, correct_answer, question_type, options
                )
            explanations.append(explanation)
        return explanations


    # ══════════════════════════════════════════════════════════════════
    #  SECTION 8: SECTION-WISE EVALUATION (coding uses test results)
    # ══════════════════════════════════════════════════════════════════

    def evaluate_by_section(self, user_type: str, sections: Dict,
                            coding_test_results: Dict = None) -> Dict:
        """
        Evaluate all sections with AI explanations.
        
        Args:
            sections: {"aptitude": [qa_pairs], "mcq": [qa_pairs], "coding": [qa_pairs]}
            coding_test_results: {question_number: run_test_cases() result dict}
                                 Passed from routes.py when student submitted code.
        """
        all_scores = []
        all_feedbacks = []
        section_scores = {}
        section_details = {}
        coding_test_results = coding_test_results or {}

        for section_name, qa_pairs in sections.items():
            if not qa_pairs:
                continue

            section_correct = 0
            section_total = len(qa_pairs)
            section_results = []

            for idx, qa in enumerate(qa_pairs):
                user_answer = str(qa.get("answer", "")).strip()
                correct_letter = str(qa.get("correct_answer", "")).strip().upper()
                correct_text = str(qa.get("correct_option_text", "")).strip()
                question_text = qa.get("question", "")
                options = qa.get("options", [])
                q_number = qa.get("question_number", idx + 1)

                # ─── CODING: Use Piston test execution results ───
                if section_name == "coding":
                    tc_results = coding_test_results.get(q_number)
                    if tc_results:
                        code_eval = self.evaluate_code_with_test_results(
                            question_text, user_answer, tc_results
                        )
                    else:
                        code_eval = self.evaluate_code_answer(
                            question_text, user_answer
                        )

                    is_correct = code_eval["is_correct"]
                    qa["generated_correct_code"] = code_eval["correct_code"]
                    qa["is_correct"] = is_correct
                    qa["test_case_results"] = code_eval.get("test_case_results")

                    all_scores.append(1 if is_correct else 0)
                    if is_correct:
                        section_correct += 1

                    section_results.append({
                        "question_number": idx + 1,
                        "question": question_text[:200],
                        "user_answer": user_answer or "No answer",
                        "correct_answer": code_eval["correct_code"],
                        "is_correct": is_correct,
                        "explanation": code_eval["explanation"],
                        "test_case_results": code_eval.get("test_case_results"),
                        "overall_result": code_eval.get("overall_result", "Unknown"),
                    })

                # ─── MCQ/APTITUDE: Standard evaluation ───
                else:
                    is_correct = self._check_answer_correct(
                        user_answer, correct_letter, correct_text, options
                    )
                    qa["is_correct"] = is_correct
                    all_scores.append(1 if is_correct else 0)
                    if is_correct:
                        section_correct += 1

                    section_results.append({
                        "question_number": idx + 1,
                        "question": question_text[:200],
                        "user_answer": user_answer or "No answer",
                        "correct_answer": correct_text or correct_letter,
                        "is_correct": is_correct,
                        "options": options,
                        "explanation": "",
                    })

            # Generate AI explanations for non-coding sections
            if section_name != "coding":
                explanations = self.generate_batch_explanations(qa_pairs, section_name)
                for i, exp in enumerate(explanations):
                    if i < len(section_results):
                        section_results[i]["explanation"] = exp
                    all_feedbacks.append(exp)
            else:
                for r in section_results:
                    all_feedbacks.append(r.get("explanation", ""))

            pct = round((section_correct / section_total) * 100, 1) if section_total else 0
            section_scores[section_name] = {
                "correct": section_correct,
                "total": section_total,
                "percentage": pct,
            }
            section_details[section_name] = {
                "score": section_scores[section_name],
                "questions": section_results,
            }

        total_correct = sum(all_scores)
        total_questions = len(all_scores)
        overall_pct = (round((total_correct / total_questions) * 100, 1)
                       if total_questions else 0)

        return {
            "scores": all_scores,
            "feedbacks": all_feedbacks,
            "total_correct": total_correct,
            "total_questions": total_questions,
            "overall_percentage": overall_pct,
            "section_scores": section_scores,
            "section_details": section_details,
        }


    # ══════════════════════════════════════════════════════════════════
    #  SECTION 9: HELPERS (unchanged from your original)
    # ══════════════════════════════════════════════════════════════════

    def _check_answer_correct(self, user_answer: str, correct_letter: str,
                              correct_text: str, options: List) -> bool:
        if not user_answer:
            return False
        user_lower = user_answer.lower().strip()

        if user_lower == correct_letter.lower():
            return True
        if correct_text and user_lower == correct_text.lower().strip():
            return True
        if correct_text and len(correct_text) > 3:
            if (user_lower in correct_text.lower() or
                    correct_text.lower() in user_lower):
                return True
        if user_answer.isdigit() and options:
            idx = int(user_answer)
            if 0 <= idx < len(options):
                selected = str(options[idx]).lower().strip()
                if correct_text and selected == correct_text.lower().strip():
                    return True
                expected_idx = ord(correct_letter.upper()) - ord('A')
                if idx == expected_idx:
                    return True
        if options:
            for i, opt in enumerate(options):
                if user_lower == str(opt).lower().strip():
                    expected_idx = ord(correct_letter.upper()) - ord('A')
                    if i == expected_idx:
                        return True
        return False

    def health_check(self) -> Dict:
        """Health check for Groq AI."""
        try:
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return {"status": "healthy", "model": self.model}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def piston_health_check(self) -> Dict:
        """Health check for Piston code execution."""
        out = {}
        for name, url in [("primary", self.piston_primary), ("fallback", self.piston_fallback)]:
            if not url:
                out[name] = {"status": "not_configured"}
                continue
            try:
                r = await self.http_client.get(f"{url}/api/v2/runtimes", timeout=5.0)
                out[name] = {"status": "healthy", "runtimes": len(r.json())} if r.status_code == 200 else {"status": "error"}
            except Exception as e:
                out[name] = {"status": "unreachable", "error": str(e)}
        return out

    async def close(self):
        """Call on app shutdown to close Piston HTTP client."""
        await self.http_client.aclose()


# ─── Singleton ───
_ai_service = None

def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service