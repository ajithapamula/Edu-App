# weekend_mocktest/core/ai_services.py
# ═══════════════════════════════════════════════════════════════════
# UPDATED: LOCAL SUBPROCESS execution + ROBUST question parsing
# 
# FIXES IN THIS VERSION:
#   1. Java version check: uses -version (writes to stderr)
#   2. MCQ max_tokens increased to 8000 (was 4000, caused truncation)
#   3. _parse_questions: 5 fallback parsing strategies
#   4. Debug logging when parser returns 0 questions
# ═══════════════════════════════════════════════════════════════════

import json
import logging
import os
import re
import random
import time
import asyncio
import subprocess
import tempfile
import shutil
from typing import Dict, List, Optional, Any

from groq import Groq

from .config import config
from .prompts import PromptTemplates

logger = logging.getLogger(__name__)


SUPPORTED_LANGUAGES = {
    "python":     {"ext": ".py",   "label": "Python 3",   "timeout": 10},
    "javascript": {"ext": ".js",   "label": "JavaScript", "timeout": 10},
    "java":       {"ext": ".java", "label": "Java",       "timeout": 15},
    "cpp":        {"ext": ".cpp",  "label": "C++",        "timeout": 10},
    "c":          {"ext": ".c",    "label": "C",          "timeout": 10},
    "typescript": {"ext": ".ts",   "label": "TypeScript", "timeout": 10},
}


class AIService:

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
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = config.GROQ_MODEL
        self._check_local_runtimes()
        logger.info(f"AIService initialized | Groq: {self.model} | Executor: LOCAL subprocess")

    # ═══════════════════════════════════════════════════════════
    # FIX 1: java -version writes to stderr, not stdout
    # ═══════════════════════════════════════════════════════════
    def _check_local_runtimes(self):
        checks = {
            "python": ["python3", "--version"],
            "node": ["node", "--version"],
            "g++": ["g++", "--version"],
            "gcc": ["gcc", "--version"],
            "java": ["java", "-version"],
        }
        for name, cmd in checks.items():
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=5)
                output = result.stdout.decode().strip() or result.stderr.decode().strip()
                ver = output.split('\n')[0] if output else "unknown"
                if result.returncode == 0 or (name == "java" and output):
                    logger.info(f"  ✅ {name}: {ver}")
                else:
                    logger.warning(f"  ⚠️ {name}: installed but returned error")
            except FileNotFoundError:
                logger.warning(f"  ❌ {name}: NOT FOUND")
            except Exception as e:
                logger.warning(f"  ⚠️ {name}: check failed — {e}")


    # ══════════════════════════════════════════════════════════
    #  CODE EXECUTION (LOCAL SUBPROCESS)
    # ══════════════════════════════════════════════════════════

    async def execute_code(self, language: str, code: str, stdin: str = "") -> Dict[str, Any]:
        start = time.time()
        lang = SUPPORTED_LANGUAGES.get(language)
        if not lang:
            return self._exec_error(f"Unsupported language: {language}", start)
        if not code or not code.strip():
            return self._exec_error("No code provided", start)
        if len(code) > 100_000:
            return self._exec_error("Code exceeds 100KB limit", start)

        timeout = lang["timeout"]
        tmp_dir = None
        try:
            tmp_dir = tempfile.mkdtemp(prefix="code_exec_")

            if language == "java":
                class_match = re.search(r'public\s+class\s+(\w+)', code)
                class_name = class_match.group(1) if class_match else "Main"
                src_file = os.path.join(tmp_dir, f"{class_name}.java")
            else:
                src_file = os.path.join(tmp_dir, f"main{lang['ext']}")

            with open(src_file, 'w') as f:
                f.write(code)

            compile_cmd = None
            run_cmd = None

            if language == "python":
                run_cmd = ["python3", src_file]
            elif language == "javascript":
                run_cmd = ["node", src_file]
            elif language == "typescript":
                js_file = os.path.join(tmp_dir, "main.js")
                compile_cmd = ["npx", "tsc", "--outDir", tmp_dir, "--target", "ES2020",
                               "--module", "commonjs", "--strict", "false",
                               "--esModuleInterop", "true", src_file]
                run_cmd = ["node", js_file]
            elif language == "cpp":
                out_file = os.path.join(tmp_dir, "a.out")
                compile_cmd = ["g++", "-o", out_file, src_file, "-std=c++17"]
                run_cmd = [out_file]
            elif language == "c":
                out_file = os.path.join(tmp_dir, "a.out")
                compile_cmd = ["gcc", "-o", out_file, src_file]
                run_cmd = [out_file]
            elif language == "java":
                compile_cmd = ["javac", src_file]
                run_cmd = ["java", "-cp", tmp_dir, class_name]

            if compile_cmd:
                try:
                    comp_result = await asyncio.to_thread(
                        subprocess.run, compile_cmd,
                        capture_output=True, timeout=timeout, cwd=tmp_dir
                    )
                    if comp_result.returncode != 0:
                        stderr = comp_result.stderr.decode('utf-8', errors='replace')
                        ms = int((time.time() - start) * 1000)
                        return {
                            "success": False, "stdout": "", "stderr": stderr,
                            "exit_code": comp_result.returncode, "execution_time_ms": ms,
                            "language": lang["label"],
                            "is_compile_error": True, "is_runtime_error": False,
                            "is_timeout": False, "overall_result": "Compilation Error",
                        }
                except subprocess.TimeoutExpired:
                    ms = int((time.time() - start) * 1000)
                    return {
                        "success": False, "stdout": "", "stderr": "Compilation timed out",
                        "exit_code": -1, "execution_time_ms": ms, "language": lang["label"],
                        "is_compile_error": True, "is_runtime_error": False,
                        "is_timeout": True, "overall_result": "Compilation Error",
                    }

            try:
                run_result = await asyncio.to_thread(
                    subprocess.run, run_cmd,
                    input=stdin.encode('utf-8') if stdin else None,
                    capture_output=True, timeout=timeout, cwd=tmp_dir
                )
                stdout = run_result.stdout.decode('utf-8', errors='replace')
                stderr = run_result.stderr.decode('utf-8', errors='replace')
                ms = int((time.time() - start) * 1000)
                has_err = bool(stderr.strip()) and run_result.returncode != 0
                overall = "Runtime Error" if (has_err or run_result.returncode != 0) else "Accepted"
                return {
                    "success": run_result.returncode == 0 and not has_err,
                    "stdout": stdout, "stderr": stderr,
                    "exit_code": run_result.returncode, "execution_time_ms": ms,
                    "language": lang["label"],
                    "is_compile_error": False, "is_runtime_error": has_err,
                    "is_timeout": False, "overall_result": overall,
                }
            except subprocess.TimeoutExpired:
                ms = int((time.time() - start) * 1000)
                return {
                    "success": False, "stdout": "",
                    "stderr": f"Time Limit Exceeded ({timeout}s)",
                    "exit_code": -1, "execution_time_ms": ms, "language": lang["label"],
                    "is_compile_error": False, "is_runtime_error": False,
                    "is_timeout": True, "overall_result": "Time Limit Exceeded",
                }
        except Exception as e:
            logger.error(f"[LOCAL EXEC] Unexpected error: {e}")
            return self._exec_error(f"Execution failed: {str(e)}", start)
        finally:
            if tmp_dir and os.path.exists(tmp_dir):
                try:
                    shutil.rmtree(tmp_dir, ignore_errors=True)
                except:
                    pass

    def _flexible_output_match(self, actual: str, expected: str) -> bool:
        if actual == expected:
            return True
        a_lines = [l.rstrip() for l in actual.split("\n") if l.strip()]
        e_lines = [l.rstrip() for l in expected.split("\n") if l.strip()]
        if a_lines == e_lines:
            return True
        if a_lines and e_lines:
            if len(e_lines) == 1:
                if a_lines[-1].strip() == e_lines[0].strip():
                    return True
                if a_lines[-1].strip().endswith(e_lines[0].strip()):
                    return True
            if len(a_lines) >= len(e_lines):
                tail = a_lines[-len(e_lines):]
                if [l.strip() for l in tail] == [l.strip() for l in e_lines]:
                    return True
        prompt_patterns = ['enter', 'input', 'type', 'provide', 'give', 'please', ':', '>>>', '> ', '? ']
        filtered_lines = []
        for line in a_lines:
            line_lower = line.lower().strip()
            is_prompt = any(line_lower.endswith(p) for p in prompt_patterns)
            if ':' in line and not line.split(':')[-1].strip():
                is_prompt = True
            if not is_prompt:
                filtered_lines.append(line)
        if filtered_lines:
            if [l.strip() for l in filtered_lines] == [l.strip() for l in e_lines]:
                return True
            if len(e_lines) == 1 and filtered_lines[-1].strip() == e_lines[0].strip():
                return True
        try:
            if len(e_lines) == 1 and a_lines:
                exp_num = float(e_lines[0].strip())
                num_match = re.search(r'[-+]?\d*\.?\d+\s*$', a_lines[-1].strip())
                if num_match and abs(float(num_match.group().strip()) - exp_num) < 0.01:
                    return True
        except (ValueError, TypeError):
            pass
        if [l.strip().lower() for l in a_lines] == [l.strip().lower() for l in e_lines]:
            return True
        return False

    async def run_test_cases(self, language: str, code: str, test_cases: List[Dict]) -> Dict[str, Any]:
        if not test_cases:
            return {"results": [], "total_passed": 0, "total_failed": 0,
                    "total_cases": 0, "all_passed": False, "score_percentage": 0.0,
                    "overall_result": "No Test Cases", "execution_summary": "No test cases provided"}
        sem = asyncio.Semaphore(5)
        async def _run_one(tc):
            async with sem:
                tc_id = tc.get("id", 0)
                tc_input = tc.get("input", "")
                expected = tc.get("expected_output", "").strip()
                is_hidden = tc.get("is_hidden", False)
                weight = tc.get("weight", 1)
                res = await self.execute_code(language, code, stdin=tc_input)
                actual = res.get("stdout", "").strip()
                passed = False
                if res.get("exit_code", -1) == 0 and not res.get("is_compile_error"):
                    passed = self._flexible_output_match(actual, expected)
                return {
                    "id": tc_id, "label": f"Test Case {tc_id}", "passed": passed,
                    "is_hidden": is_hidden, "weight": weight,
                    "input": tc_input if not is_hidden else "[Hidden]",
                    "expected_output": expected if not is_hidden else "[Hidden]",
                    "actual_output": actual if not is_hidden else ("[Hidden]" if not passed else actual),
                    "execution_time_ms": res.get("execution_time_ms", 0),
                    "stderr": res.get("stderr", "") if not is_hidden else "",
                    "is_compile_error": res.get("is_compile_error", False),
                    "is_runtime_error": res.get("is_runtime_error", False),
                    "is_timeout": res.get("is_timeout", False),
                }
        results = sorted(await asyncio.gather(*[_run_one(tc) for tc in test_cases]), key=lambda r: r["id"])
        total_passed = sum(1 for r in results if r["passed"])
        total_weight = sum(r["weight"] for r in results) or 1
        passed_weight = sum(r["weight"] for r in results if r["passed"])
        score_pct = round((passed_weight / total_weight) * 100, 1)
        if any(r["is_compile_error"] for r in results): overall = "Compilation Error"
        elif any(r["is_timeout"] for r in results): overall = "Time Limit Exceeded"
        elif any(r["is_runtime_error"] for r in results): overall = "Runtime Error"
        elif total_passed == len(results): overall = "Accepted"
        else: overall = "Wrong Answer"
        summary = (f"All {len(results)} test cases passed!" if total_passed == len(results)
                   else f"{total_passed}/{len(results)} test cases passed ({score_pct}%)")
        logger.info(f"Test run: {summary} | Result: {overall}")
        return {"results": results, "total_passed": total_passed,
                "total_failed": len(results) - total_passed, "total_cases": len(results),
                "all_passed": total_passed == len(results), "score_percentage": score_pct,
                "overall_result": overall, "execution_summary": summary}

    def _exec_error(self, msg: str, start: float) -> Dict[str, Any]:
        return {"success": False, "stdout": "", "stderr": msg, "exit_code": -1,
                "execution_time_ms": int((time.time() - start) * 1000), "language": "unknown",
                "is_compile_error": False, "is_runtime_error": False,
                "is_timeout": False, "overall_result": "System Error"}


    # ══════════════════════════════════════════════════════════
    #  TEST CASE PARSING & GENERATION
    # ══════════════════════════════════════════════════════════

    def _parse_test_cases_from_section(self, part: str) -> List[Dict]:
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
                "label": f"Test Case {tc_id}", "weight": 1,
            })
        return test_cases

    def generate_test_cases(self, question: str, num_cases: int = 5) -> List[Dict]:
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
                    "label": f"Test Case {tc_id}", "weight": 1,
                })
            logger.info(f"Generated {len(test_cases)} test cases for question")
            return test_cases
        except Exception as e:
            logger.error(f"Test case generation failed: {e}")
            return []


    # ══════════════════════════════════════════════════════════
    #  CONTENT FILTERING
    # ══════════════════════════════════════════════════════════

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
        for pattern in [r'def\s+\w+\s*\(', r'class\s+\w+\s*[:\(]', r'import\s+\w+',
                        r'from\s+\w+\s+import', r'print\s*\(["\']', r'\w+\s*=\s*\[',
                        r'for\s+\w+\s+in\s+', r'while\s+\w+\s*[:<]']:
            if re.search(pattern, combined):
                return True
        return False

    def _filter_coding_questions_for_nondev(self, questions: List[Dict]) -> List[Dict]:
        filtered = []
        blocked = 0
        for q in questions:
            if q.get("question_type") == "coding":
                blocked += 1; continue
            if self._is_coding_question(q):
                blocked += 1
            else:
                filtered.append(q)
        if blocked:
            logger.info(f"Blocked {blocked} programming questions for non-dev")
        return filtered


    # ══════════════════════════════════════════════════════════
    #  QUESTION GENERATION
    #  FIX 2: Debug logging + increased max_tokens for MCQ
    # ══════════════════════════════════════════════════════════

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

            # FIX: MCQ max_tokens increased from 4000 → 8000 to prevent truncation
            if question_type == "coding":
                max_tok = 6000
            elif question_type == "mcq":
                max_tok = 8000
            else:
                max_tok = 4000

            # Temperature: lower for aptitude (math accuracy), higher for creative MCQ/coding
            if question_type == "aptitude":
                temp = 0.4  # Lower = more accurate math
            elif question_type == "coding":
                temp = 0.6
            else:
                temp = 0.7

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert question generator. Follow the format exactly. Use === QUESTION N === markers for each question. Start IMMEDIATELY with === QUESTION 1 === — no introduction, no preamble, no explanation before the first question."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temp,
                max_tokens=max_tok,
            )
            content = response.choices[0].message.content
            questions = self._parse_questions(content, question_type)

            # FIX: Debug logging when parser returns 0 questions
            if not questions:
                logger.error(f"⚠️ PARSER RETURNED 0 QUESTIONS for {question_type}")
                logger.error(f"   AI response length: {len(content)} chars")
                logger.error(f"   First 800 chars:\n{content[:800]}")
                logger.error(f"   Last 200 chars:\n{content[-200:]}")

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


    # ══════════════════════════════════════════════════════════
    #  QUESTION PARSING
    #  FIX 3: 5 fallback strategies for robust parsing
    # ══════════════════════════════════════════════════════════

    def _parse_questions(self, content: str, question_type: str = "mcq") -> List[Dict]:
        """Parse AI-generated questions with multiple fallback strategies."""
        if not content or not content.strip():
            logger.warning("Empty content received from AI")
            return []

        questions = []

        # Strategy 1: === QUESTION N === markers (case-insensitive)
        try:
            parts = re.split(r'===\s*QUESTION\s*\d+\s*===', content, flags=re.IGNORECASE)
            for part in parts:
                if not part.strip():
                    continue
                q = self._extract_question_from_part(part, question_type)
                if q:
                    questions.append(q)
            if questions:
                logger.info(f"  Parser strategy 1 (=== markers): {len(questions)} questions")
                return questions
        except Exception as e:
            logger.warning(f"Strategy 1 error: {e}")

        # Strategy 2: **Question N** or ## Question N
        try:
            parts = re.split(r'(?:\*\*|##)\s*Question\s*\d+\s*\*?\*?', content, flags=re.IGNORECASE)
            for part in parts:
                if not part.strip():
                    continue
                q = self._extract_question_from_part(part, question_type)
                if q:
                    questions.append(q)
            if questions:
                logger.info(f"  Parser strategy 2 (** markers): {len(questions)} questions")
                return questions
        except Exception as e:
            logger.warning(f"Strategy 2 error: {e}")

        # Strategy 3: Numbered Q1. or Q1) or 1. patterns
        try:
            parts = re.split(r'\n\s*(?:Q?\d+[\.\):]|Question\s+\d+\s*[:\.])', content, flags=re.IGNORECASE)
            for part in parts:
                if not part.strip():
                    continue
                q = self._extract_question_from_part(part, question_type)
                if q:
                    questions.append(q)
            if questions:
                logger.info(f"  Parser strategy 3 (numbered): {len(questions)} questions")
                return questions
        except Exception as e:
            logger.warning(f"Strategy 3 error: {e}")

        # Strategy 4: JSON
        try:
            parsed = json.loads(content)
            if isinstance(parsed, list):
                return parsed
        except:
            pass
        try:
            match = re.search(r'\[[\s\S]*\]', content)
            if match:
                parsed = json.loads(match.group())
                if isinstance(parsed, list):
                    return parsed
        except:
            pass

        # Strategy 5: Find blocks with A) B) C) D) options
        try:
            questions = self._parse_by_options_blocks(content, question_type)
            if questions:
                logger.info(f"  Parser strategy 5 (options blocks): {len(questions)} questions")
                return questions
        except Exception as e:
            logger.warning(f"Strategy 5 error: {e}")

        logger.error(f"All parsing strategies failed for {question_type}")
        return []

    def _extract_question_from_part(self, part: str, question_type: str) -> Optional[Dict]:
        """Extract a single question from a text block."""
        q = {}

        # Title
        m = re.search(r'(?:##\s*)?Title:\s*(.+)', part, re.IGNORECASE)
        if m:
            q['title'] = m.group(1).strip().strip('*')

        # Difficulty
        m = re.search(r'(?:##\s*)?Difficulty:\s*(\w+)', part, re.IGNORECASE)
        if m:
            q['difficulty'] = m.group(1).strip()

        # Question text
        m = re.search(
            r'(?:##\s*)?Question:\s*\n(.+?)(?=(?:##\s*)?Options:|(?:##\s*)?TestCases:|(?:##\s*)?Correct:|$)',
            part, re.DOTALL | re.IGNORECASE
        )
        if m:
            q['question'] = m.group(1).strip()
        else:
            # Fallback: collect lines before options
            lines = part.strip().split('\n')
            text_lines = []
            for line in lines:
                ls = line.strip()
                if re.match(r'^[A-D]\)', ls):
                    break
                if not re.match(r'^(?:##|Title:|Difficulty:|Type:|Correct:|Options:)', ls, re.IGNORECASE):
                    if ls:
                        text_lines.append(ls)
            if text_lines:
                q['question'] = '\n'.join(text_lines)

        # Options
        m = re.search(
            r'(?:##\s*)?Options:\s*\n(.+?)(?=(?:##\s*)?Correct:|(?:##\s*)?TestCases:|$)',
            part, re.DOTALL | re.IGNORECASE
        )
        if m:
            options = [o.strip() for o in re.findall(r'[A-D]\)\s*(.+)', m.group(1))]
            if options:
                q['options'] = options
        else:
            options = [o.strip() for o in re.findall(r'[A-D]\)\s*(.+)', part)]
            if len(options) >= 4:
                q['options'] = options[:4]

        # Correct answer
        m = re.search(r'(?:##\s*)?Correct(?:\s*Answer)?:\s*([A-Da-d])', part, re.IGNORECASE)
        if not m:
            m = re.search(r'Answer:\s*([A-Da-d])\b', part, re.IGNORECASE)
        if m:
            letter = m.group(1).upper()
            q['correct_answer'] = letter
            if q.get('options'):
                idx = ord(letter) - ord('A')
                if 0 <= idx < len(q['options']):
                    q['correct_option_text'] = q['options'][idx]

        # Test cases for coding
        if question_type == "coding":
            tcs = self._parse_test_cases_from_section(part)
            if tcs:
                q['test_cases'] = tcs

        if q.get('question') and len(q['question']) > 10:
            # Reject preamble/intro text that isn't a real question
            q_lower = q['question'].lower()
            preamble_signals = [
                'here are', 'here is', 'below are', 'following are',
                'i will generate', 'i have generated', 'i\'ll create',
                'programming language detected', 'language detected',
                'based on the content', 'based on the course',
                'let me generate', 'let me create',
            ]
            if any(signal in q_lower for signal in preamble_signals):
                return None
            # For MCQ: must have options
            if question_type == "mcq" and not q.get('options'):
                return None
            return q
        return None

    def _parse_by_options_blocks(self, content: str, question_type: str) -> List[Dict]:
        """Find question blocks by looking for A) B) C) D) option patterns."""
        questions = []
        # Find all positions where options appear
        option_positions = [m.start() for m in re.finditer(r'\nA\)\s', content)]

        for i, pos in enumerate(option_positions):
            # Find the start of this question (look backward for question text)
            # Start from previous options block end, or beginning
            if i > 0:
                prev_end = content.rfind('\n\n', option_positions[i-1], pos)
                start = prev_end if prev_end > option_positions[i-1] else option_positions[i-1]
            else:
                start = max(0, content.rfind('\n\n', 0, pos))

            # Find the end (next question or end)
            if i + 1 < len(option_positions):
                next_start = content.rfind('\n\n', pos, option_positions[i+1])
                end = next_start if next_start > pos else option_positions[i+1]
            else:
                end = len(content)

            block = content[start:end]
            q = self._extract_question_from_part(block, question_type)
            if q:
                questions.append(q)

        return questions


    # ══════════════════════════════════════════════════════════
    #  CODE EVALUATION
    # ══════════════════════════════════════════════════════════

    def evaluate_code_with_test_results(self, question: str, user_code: str,
                                        test_results: Dict) -> Dict:
        all_passed = test_results.get("all_passed", False)
        correct_solution = self.generate_correct_code(question)
        explanation = self.generate_coding_explanation(
            question, user_code, correct_solution["code"], all_passed, test_results)
        return {"is_correct": all_passed, "correct_code": correct_solution["code"],
                "explanation": explanation, "test_case_results": test_results,
                "overall_result": test_results.get("overall_result", "Unknown")}

    def evaluate_code_answer(self, question: str, user_code: str) -> Dict:
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
                messages=[{"role": "system", "content": "You are a strict code evaluator."},
                          {"role": "user", "content": prompt}],
                temperature=0.2, max_tokens=300)
            content = response.choices[0].message.content.strip()
            is_correct = "IS_CORRECT: YES" in content.upper()
            explanation = self.generate_coding_explanation(question, user_code, correct_code, is_correct)
            return {"is_correct": is_correct, "correct_code": correct_code,
                    "explanation": explanation, "test_case_results": None,
                    "overall_result": "Accepted" if is_correct else "Wrong Answer"}
        except Exception as e:
            logger.error(f"Code evaluation failed: {e}")
            correct_solution = self.generate_correct_code(question)
            return {"is_correct": False, "correct_code": correct_solution["code"],
                    "explanation": "Evaluation failed.", "test_case_results": None,
                    "overall_result": "System Error"}


    # ══════════════════════════════════════════════════════════
    #  EXPLANATION GENERATION
    # ══════════════════════════════════════════════════════════

    def _detect_language_from_question(self, question: str) -> str:
        """Detect programming language from question text."""
        q_lower = question.lower()
        lang_signals = {
            "java": ["java program", "in java", "write a java", "using java", "scanner", "system.out", "public static void main", "arraylist", "hashmap"],
            "javascript": ["javascript", "in js", "node.js", "console.log", "readline", "const ", "let "],
            "cpp": ["c++ program", "in c++", "using c++", "cout", "cin", "#include", "iostream"],
            "c": ["c program", "in c language", "using c language", "printf", "scanf", "#include <stdio"],
            "typescript": ["typescript", "in ts"],
            "python": ["python program", "in python", "using python", "print(", "input(", "def "],
        }
        for lang, signals in lang_signals.items():
            for signal in signals:
                if signal in q_lower:
                    return lang
        return "python"  # default fallback

    def generate_correct_code(self, question: str) -> Dict[str, str]:
        try:
            lang = self._detect_language_from_question(question)
            lang_instructions = {
                "python": "Use input() for stdin, print() for stdout.",
                "java": "Use Scanner for stdin, System.out.println for stdout. Include a Main class.",
                "javascript": "Use readline or process.stdin for input, console.log for output.",
                "cpp": "Use cin for stdin, cout for stdout. Include necessary headers.",
                "c": "Use scanf for stdin, printf for stdout. Include necessary headers.",
                "typescript": "Use readline for input, console.log for output.",
            }
            instructions = lang_instructions.get(lang, "Read from stdin, write to stdout.")
            prompt = f"""Write correct {lang} code for:
{question}
Requirements: {instructions} Simple and clean.
Return ONLY code inside a ``` code block."""
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": f"Return only {lang} code in a ``` code block."},
                          {"role": "user", "content": prompt}],
                temperature=0.3, max_tokens=800)
            content = response.choices[0].message.content.strip()
            # Try language-specific block first, then generic
            code_match = re.search(r'```(?:python|java|javascript|cpp|c|typescript)?\s*(.*?)\s*```', content, re.DOTALL)
            if code_match:
                code = code_match.group(1).strip()
            else:
                code = content
            return {"code": code, "explanation": ""}
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return {"code": "# Unable to generate", "explanation": ""}

    def generate_explanation(self, question: str, user_answer: str, correct_answer: str,
                            question_type: str, options: List[str] = None) -> str:
        try:
            options_text = ""
            if options:
                options_text = "\nOptions:\n" + "\n".join(
                    [f"{chr(65+i)}) {opt}" for i, opt in enumerate(options)])
            prompt = f"""Question: {question}{options_text}
User's Answer: {user_answer}
Correct Answer: {correct_answer}

Give a brief explanation (2-3 sentences) of why the correct answer is right.
If the user got it wrong, briefly explain their likely mistake.
IMPORTANT: If this is a math question, show the key calculation step.
Do NOT contradict yourself — if your calculation gives a different number than the stated correct answer, go with your calculation."""
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "Brief, accurate educational explanations. For math questions, always verify the calculation."},
                          {"role": "user", "content": prompt}],
                temperature=0.3, max_tokens=200)
            return response.choices[0].message.content.strip()
        except:
            return f"The correct answer is: {correct_answer}"

    def generate_coding_explanation(self, question: str, user_code: str,
                                    correct_code: str, is_correct: bool,
                                    test_results: Dict = None) -> str:
        try:
            tc_context = ""
            if test_results:
                p = test_results.get("total_passed", 0)
                t = test_results.get("total_cases", 0)
                tc_context = f"\nTest Results: {p}/{t} passed. Overall: {test_results.get('overall_result', 'N/A')}"
                failed = [r for r in test_results.get("results", []) if not r["passed"] and not r.get("is_hidden")]
                if failed:
                    f = failed[0]
                    tc_context += f"\nFirst failing test case:"
                    tc_context += f"\n  Input: '{f.get('input', '')}'"
                    tc_context += f"\n  Expected output: '{f.get('expected_output', '')}'"
                    tc_context += f"\n  Actual output: '{f.get('actual_output', '')}'"
                    if f.get('stderr'):
                        tc_context += f"\n  Error: {f.get('stderr', '')[:200]}"
            if is_correct:
                prompt = f"Student's code passed all tests.{tc_context}\nBrief positive feedback (1-2 sentences)."
            else:
                prompt = f"""Student's code failed some test cases.{tc_context}

Question: {question[:300]}
Student Code (first 500 chars): {user_code[:500] if user_code else '(No answer submitted)'}

RULES FOR YOUR FEEDBACK:
1. Base your feedback ONLY on the test case results shown above
2. If there are failing test cases, explain WHY the output differs from expected
3. Do NOT claim there are syntax errors unless the error message explicitly says so
4. Do NOT claim code is incomplete unless the student submitted no code
5. Do NOT hallucinate or invent issues that aren't shown in the test results
6. Keep it brief: 2-3 sentences maximum

Explain what went wrong based on the actual test case failure:"""
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "You are a programming tutor. Give brief, ACCURATE feedback based ONLY on the test case results provided. Never invent or hallucinate code issues."},
                          {"role": "user", "content": prompt}],
                temperature=0.3, max_tokens=200)
            return response.choices[0].message.content.strip()
        except:
            return "Correct! All test cases passed." if is_correct else "Some test cases failed. Review the expected output format."

    def generate_batch_explanations(self, qa_pairs: List[Dict], question_type: str) -> List[str]:
        explanations = []
        for qa in qa_pairs:
            question = qa.get("question", "")
            user_answer = qa.get("answer", "No answer")
            correct_answer = qa.get("correct_option_text") or qa.get("correct_answer", "N/A")
            options = qa.get("options", [])
            is_correct = qa.get("is_correct", False)
            if question_type == "coding":
                explanation = self.generate_coding_explanation(
                    question, user_answer, qa.get("generated_correct_code", ""),
                    is_correct, qa.get("test_case_results"))
            elif is_correct:
                explanation = random.choice(["Correct! Well done.", "Excellent! Right answer.",
                                             "Correct! Good understanding.", "Well done!"])
            else:
                explanation = self.generate_explanation(question, user_answer, correct_answer, question_type, options)
            explanations.append(explanation)
        return explanations


    # ══════════════════════════════════════════════════════════
    #  SECTION-WISE EVALUATION
    # ══════════════════════════════════════════════════════════

    def evaluate_by_section(self, user_type: str, sections: Dict,
                            coding_test_results: Dict = None) -> Dict:
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

                if section_name == "coding":
                    tc_results = coding_test_results.get(q_number)
                    if tc_results:
                        code_eval = self.evaluate_code_with_test_results(question_text, user_answer, tc_results)
                    else:
                        code_eval = self.evaluate_code_answer(question_text, user_answer)
                    is_correct = code_eval["is_correct"]
                    qa["generated_correct_code"] = code_eval["correct_code"]
                    qa["is_correct"] = is_correct
                    qa["test_case_results"] = code_eval.get("test_case_results")
                    all_scores.append(1 if is_correct else 0)
                    if is_correct: section_correct += 1
                    section_results.append({
                        "question_number": idx + 1, "question": question_text[:200],
                        "user_answer": user_answer or "No answer",
                        "correct_answer": code_eval["correct_code"], "is_correct": is_correct,
                        "explanation": code_eval["explanation"],
                        "test_case_results": code_eval.get("test_case_results"),
                        "overall_result": code_eval.get("overall_result", "Unknown")})
                else:
                    is_correct = self._check_answer_correct(user_answer, correct_letter, correct_text, options)
                    qa["is_correct"] = is_correct
                    all_scores.append(1 if is_correct else 0)
                    if is_correct: section_correct += 1
                    section_results.append({
                        "question_number": idx + 1, "question": question_text[:200],
                        "user_answer": user_answer or "No answer",
                        "correct_answer": correct_text or correct_letter,
                        "is_correct": is_correct, "options": options, "explanation": ""})

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
            section_scores[section_name] = {"correct": section_correct, "total": section_total, "percentage": pct}
            section_details[section_name] = {"score": section_scores[section_name], "questions": section_results}

        total_correct = sum(all_scores)
        total_questions = len(all_scores)
        overall_pct = round((total_correct / total_questions) * 100, 1) if total_questions else 0

        return {"scores": all_scores, "feedbacks": all_feedbacks,
                "total_correct": total_correct, "total_questions": total_questions,
                "overall_percentage": overall_pct, "section_scores": section_scores,
                "section_details": section_details}


    # ══════════════════════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════════════════════

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
            if user_lower in correct_text.lower() or correct_text.lower() in user_lower:
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
        try:
            self.client.chat.completions.create(
                model=self.model, messages=[{"role": "user", "content": "ping"}], max_tokens=5)
            return {"status": "healthy", "model": self.model}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def executor_health_check(self) -> Dict:
        try:
            result = await self.execute_code("python", "print('ok')")
            if result.get("stdout", "").strip() == "ok":
                return {"status": "healthy", "executor": "local_subprocess"}
            return {"status": "error", "detail": result.get("stderr", "unknown")}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def close(self):
        pass


_ai_service = None

def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service