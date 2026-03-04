# weekend_mocktest/services/test_service.py
"""
Mock Test Service - AUTO QUESTION BANK REFRESH

After every test completes, a background task automatically generates
fresh questions to replenish the bank. No manual deletion needed.

REFRESH LOGIC:
- After test completes → background asyncio task fires
- Checks each section question count in bank
- If any section has < REFRESH_THRESHOLD questions → generates fresh batch
- High-usage questions (used >= MAX_USAGE_COUNT times) are deactivated
- Bank stays perpetually fresh, questions never repeat
"""

import logging
import markdown
import time
import hashlib
import uuid
import asyncio
import random
from typing import Dict, Any, List, Optional

# NOTE: core imports are done lazily inside __init__ to avoid circular imports.
# Do NOT move them back to module level.

logger = logging.getLogger(__name__)


class TestService:

    # ── Bank refresh config ──────────────────────────────────────
    # Keep a large bank so shuffle has enough variety to prevent repeats.
    # With 100 questions per section and tests needing 10,
    # the chance of two students getting the same 10 is very low.
    REFRESH_THRESHOLD  = 60   # trigger refresh when bank drops below 60 per section
    REFRESH_BATCH_SIZE = 30   # generate 30 new questions per refresh
    MAX_USAGE_COUNT    = 10   # retire questions after 10 uses (seen by ~10 students)
    # ─────────────────────────────────────────────────────────────

    PROGRAMMING_KEYWORDS = [
        'write a program', 'write a function', 'write code', 'write python',
        'implement a function', 'create a function', 'code to',
        'python program', 'python code', 'python function',
        'in python', 'using python', 'java program',
        'def ', 'import ', 'from ', 'class ', 'return ',
        'print(', 'input(', 'len(', 'range(',
        '__init__', '__name__', '__main__', 'self.',
        'try:', 'except:', 'finally:', 'lambda',
        'for i in range', '>>>', '```python',
        '.py', 'pip install', 'pip ', 'npm ',
        'pandas', 'numpy', 'tensorflow', 'pytorch', 'sklearn',
        'django', 'flask', 'react', 'angular', 'vue'
    ]

    SAP_WHITELIST = [
        'sap', 'erp', 'enterprise', 'procurement', 'sales', 'distribution',
        'finance', 'accounting', 'hr', 'human resources', 'production',
        'material', 'vendor', 'customer', 'invoice', 'payment', 'billing',
        'purchase order', 'sales order', 'master data', 'transaction',
        'mm', 'sd', 'fico', 'pp', 'wm', 'qm', 'pm',
        'general ledger', 'cost center', 'profit center',
        'business process', 'organizational'
    ]

    def __init__(self):
        # Lazy imports — prevents circular import at module load time
        from ..core.config import config
        from ..core.database import get_db_manager
        from ..core.ai_services import get_ai_service
        from ..core.content_service import get_content_service
        from ..core.utils import memory_manager, ValidationUtils

        self.config           = config
        self.memory_manager   = memory_manager
        self.ValidationUtils  = ValidationUtils
        self.db_manager       = get_db_manager()
        self.ai_service       = get_ai_service()
        self.content_service  = get_content_service()
        logger.info("🚀 Test Service initialized with Auto Bank Refresh")
        # Warmup bank on startup so first tests never hit a tiny bank
        asyncio.ensure_future(self._warmup_bank())

    async def _warmup_bank(self):
        """
        On startup:
        1. Auto-clean all generic/banned questions from existing bank
        2. Fill any sections that dropped below threshold after cleanup
        No manual MongoDB deletion needed — this handles it automatically.
        """
        try:
            await asyncio.sleep(5)  # let app fully start first
            logger.info("🔥 Bank warmup starting...")
            for user_type in ["dev", "non_dev"]:
                # Step 1: clean bad questions first
                bad = self._deactivate_bad_questions(user_type)
                over = self._deactivate_overused_questions(user_type)
                if bad or over:
                    logger.info(f"🧹 Startup cleanup: removed {bad} generic + {over} overused ({user_type})")
                # Step 2: refill whatever was removed
                await self._refresh_question_bank(user_type)
            logger.info("✅ Bank warmup complete")
        except Exception as e:
            logger.error(f"❌ Bank warmup failed: {e}")

    # ════════════════════════════════════════════════════════════
    # AUTO BANK REFRESH
    # ════════════════════════════════════════════════════════════

    async def _refresh_question_bank(self, user_type: str):
        """
        Background task: replenish question bank after a test completes.
        1. Deactivate over-used questions
        2. Count available questions per section
        3. Generate fresh batch for any section below threshold
        """
        try:
            logger.info(f"🔄 [BG] Bank refresh starting for {user_type}...")

            deactivated = self._deactivate_overused_questions(user_type)
            if deactivated:
                logger.info(f"🗑️  [BG] Deactivated {deactivated} over-used questions")

            # Auto-clean generic/banned questions — no manual DB cleanup needed
            bad_removed = self._deactivate_bad_questions(user_type)
            if bad_removed:
                logger.info(f"🧹 [BG] Removed {bad_removed} generic questions — will regenerate")

            context  = self.content_service.get_context_for_questions(user_type)
            sections = ["aptitude", "mcq", "coding"] if user_type == "dev" else ["aptitude", "mcq"]

            # Detect dominant language ONCE for the whole batch
            # so all coding questions in this refresh use the same language
            dominant_lang = self._detect_dominant_language(context)
            logger.info(f"🔤 [BG] Dominant language detected: {dominant_lang}")

            for section in sections:
                available = self._count_available_questions(user_type, section)
                logger.info(f"📊 [BG] {user_type}/{section}: {available} available")

                if available < self.REFRESH_THRESHOLD:
                    needed = self.REFRESH_THRESHOLD - available + self.REFRESH_BATCH_SIZE
                    logger.info(f"⚡ [BG] Generating {needed} new {section} questions...")

                    section_context = "" if section == "aptitude" else context
                    # For coding, prepend language hint so AI stays consistent
                    if section == "coding" and dominant_lang:
                        section_context = f"PRIMARY LANGUAGE: {dominant_lang}\n\n{section_context}"
                    new_qs = self.ai_service.generate_questions_for_bank(
                        user_type, section, section_context, needed
                    )

                    if new_qs:
                        for q in new_qs:
                            q["question_id"]   = str(uuid.uuid4())
                            q["question_hash"] = hashlib.md5(q.get("question", "").encode()).hexdigest()
                        added = self.db_manager.add_questions_to_bank(new_qs, user_type)
                        logger.info(f"✅ [BG] Added {added} fresh questions to {user_type}/{section}")
                    else:
                        logger.warning(f"⚠️  [BG] AI returned 0 questions for {section}")

            logger.info(f"✅ [BG] Bank refresh complete for {user_type}")

        except Exception as e:
            logger.error(f"❌ [BG] Bank refresh failed: {e}")

    # ── Generic/banned question patterns ────────────────────────
    # These are detected and deactivated automatically on every refresh
    BANNED_MCQ_PATTERNS = [
        "what is the purpose of",
        "what is the main focus",
        "what is a good practice",
        "why is it important",
        "what are the prerequisites",
        "what is java primarily used for",
        "what is the goal of",
        "what is the benefit of",
        "what is the best practice",
        "what is a best practice",
        "what type of programming language is java",
        "what type of programming concepts does java",
        "what is the design of java",
        "what is the last step in writing",
        "what is the file extension",
        "what is the first step",
    ]
    # ─────────────────────────────────────────────────────────────

    def _deactivate_overused_questions(self, user_type: str) -> int:
        """Deactivate questions used >= MAX_USAGE_COUNT times so they stop appearing."""
        result = self.db_manager.question_bank_collection.update_many(
            {"user_type": user_type, "active": True, "usage_count": {"$gte": self.MAX_USAGE_COUNT}},
            {"$set": {"active": False}}
        )
        return result.modified_count

    def _deactivate_bad_questions(self, user_type: str) -> int:
        """
        Auto-detect and deactivate generic/banned MCQ questions.
        Runs on every bank refresh — no manual MongoDB cleanup needed.
        Matches against BANNED_MCQ_PATTERNS (case-insensitive substring match).
        """
        deactivated = 0
        try:
            # Fetch all active MCQ questions for this user_type
            cursor = self.db_manager.question_bank_collection.find({
                "user_type":     user_type,
                "question_type": "mcq",
                "active":        True
            }, {"_id": 1, "question": 1})

            bad_ids = []
            for doc in cursor:
                q_text = doc.get("question", "").lower().strip()
                if any(pattern in q_text for pattern in self.BANNED_MCQ_PATTERNS):
                    bad_ids.append(doc["_id"])

            if bad_ids:
                result = self.db_manager.question_bank_collection.update_many(
                    {"_id": {"$in": bad_ids}},
                    {"$set": {"active": False}}
                )
                deactivated = result.modified_count
                logger.info(f"🧹 Auto-deactivated {deactivated} generic/banned MCQ questions for {user_type}")

        except Exception as e:
            logger.error(f"❌ _deactivate_bad_questions failed: {e}")

        return deactivated

    def _count_available_questions(self, user_type: str, question_type: str) -> int:
        return self.db_manager.question_bank_collection.count_documents({
            "user_type":     user_type,
            "question_type": question_type,
            "active":        True
        })

    def _trigger_background_refresh(self, user_type: str):
        """Fire-and-forget bank refresh — never blocks the response."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self._refresh_question_bank(user_type))
                logger.info(f"🔄 Bank refresh scheduled in background for {user_type}")
        except Exception as e:
            logger.error(f"[BG] Failed to schedule refresh: {e}")

    # ════════════════════════════════════════════════════════════
    # HELPERS
    # ════════════════════════════════════════════════════════════

    def _is_programming_question(self, question_data: Dict) -> bool:
        text_parts = [str(question_data.get("question", "")), str(question_data.get("title", ""))]
        options = question_data.get("options", [])
        if isinstance(options, list):
            text_parts.extend([str(o) for o in options])
        elif isinstance(options, dict):
            text_parts.extend([str(v) for v in options.values()])
        combined = " ".join(text_parts).lower()
        for t in self.SAP_WHITELIST:
            if t in combined:
                return False
        for k in self.PROGRAMMING_KEYWORDS:
            if k.lower() in combined:
                return True
        return False

    def _filter_programming_questions(self, questions: List[Dict], user_type: str) -> List[Dict]:
        if user_type == "dev":
            return questions
        filtered, removed = [], 0
        for q in questions:
            if q.get("question_type") == "coding" or self._is_programming_question(q):
                removed += 1
            else:
                filtered.append(q)
        if removed:
            logger.info(f"✅ Filtered {removed} programming questions for non-dev")
        return filtered

    def _normalize_student_id(self, student_id) -> int:
        if student_id is None:
            fb = int(time.time() * 1000) % 90000 + 10000
            logger.warning(f"⚠️ No student_id — using fallback {fb}")
            return fb
        if isinstance(student_id, int):
            return student_id
        s = str(student_id).strip()
        if s.isdigit():
            return int(s)
        return (int(hashlib.md5(s.encode()).hexdigest(), 16) % 90000) + 10000

    # ════════════════════════════════════════════════════════════
    # START TEST
    # ════════════════════════════════════════════════════════════

    async def start_test(self, user_type: str, student_id=None, student_profile: dict = None):
        logger.info("=" * 70)
        logger.info(f"🟢 STARTING {'DEVELOPER' if user_type == 'dev' else 'NON-DEVELOPER'} TEST")
        if student_profile:
            logger.info(
                f"   Student: [{student_profile.get('student_id')}] "
                f"{student_profile.get('student_name')} | "
                f"Course: {student_profile.get('course')} | "
                f"Batch: {student_profile.get('batch')}"
            )
        logger.info("=" * 70)

        if not self.ValidationUtils.validate_user_type(user_type):
            raise ValueError("Invalid user type. Use 'dev' or 'non_dev'")

        try:
            student_id     = self._normalize_student_id(student_id)
            exam_structure = self.config.get_exam_structure(user_type)
            questions      = self._generate_questions_no_repeat(user_type, exam_structure, student_id)

            if not questions:
                raise Exception("Failed to generate questions")

            if user_type == "non_dev":
                questions = self._filter_programming_questions(questions, user_type)

            test_id   = self.memory_manager.create_test(user_type, questions, student_id)
            test_data = self.memory_manager.get_test(test_id)
            test_data["student_id"]     = student_id
            test_data["exam_structure"] = exam_structure

            # Store full student profile so results carry name/course/batch/role
            # This enables large-scale queries like:
            #   "show all Batch-2025 Java students who scored > 60%"
            #   "show results for student ID 35280"
            if student_profile:
                test_data["student_profile"] = {
                    "student_id":   student_profile.get("student_id"),
                    "student_name": student_profile.get("student_name"),
                    "email":        student_profile.get("email"),
                    "course":       student_profile.get("course"),
                    "batch":        student_profile.get("batch"),
                    "role_type":    student_profile.get("role_type"),
                    "experience":   student_profile.get("experience"),
                    "org_id":       student_profile.get("org_id"),
                }

            question_ids = [q.get("question_id") for q in questions if q.get("question_id")]
            if question_ids:
                self.db_manager.mark_questions_as_seen(student_id, question_ids)
                self.db_manager.increment_question_usage(question_ids)

            current_question = self.memory_manager.get_current_question(test_id)
            current_question["question_html"] = markdown.markdown(
                current_question["question_html"], extensions=['fenced_code']
            )

            first_q    = questions[0]
            time_limit = self._get_time_limit(first_q.get("question_type", "aptitude"), user_type)

            logger.info(f"✅ Test started: {test_id} | student={student_id} | {len(questions)} questions")
            return self._create_start_response(test_id, test_data, current_question, time_limit, exam_structure, user_type)

        except Exception as e:
            logger.error(f"❌ Test start failed: {e}")
            raise

    def _generate_questions_no_repeat(self, user_type, exam_structure, student_id):
        questions = []
        sections  = exam_structure.get("sections", {})
        context   = self.content_service.get_context_for_questions(user_type)

        if user_type == "dev":
            section_config = [
                ("aptitude", sections.get("aptitude", {}).get("question_count", 10), True),
                ("mcq",      sections.get("mcq",      {}).get("question_count", 10), True),
                ("coding",   sections.get("coding",   {}).get("question_count", 5),  False),
            ]
        else:
            section_config = [
                ("aptitude", sections.get("aptitude", {}).get("question_count", 10), True),
                ("mcq",      sections.get("mcq",      {}).get("question_count", 20), True),
            ]

        dominant_lang = self._detect_dominant_language(context)
        logger.info(f"🔤 Dominant language for this test: {dominant_lang}")

        for q_type, count, is_mcq in section_config:
            if user_type == "non_dev" and q_type == "coding":
                continue
            # For coding, prepend language hint so all questions use same language
            if q_type == "coding" and dominant_lang:
                section_context = f"PRIMARY LANGUAGE: {dominant_lang}\n\n{context}"
            elif q_type == "aptitude":
                section_context = ""
            else:
                section_context = context
            section_qs = self._get_section_questions_no_repeat(
                student_id, user_type, q_type, count, is_mcq,
                section_context
            )
            if user_type == "non_dev":
                section_qs = self._filter_programming_questions(section_qs, user_type)
            questions.extend(section_qs)

        for i, q in enumerate(questions, 1):
            q["question_number"] = i
        return questions

    def _get_section_questions_no_repeat(self, student_id, user_type, question_type, count, is_mcq, context):
        if user_type == "non_dev" and question_type == "coding":
            return []

        unseen = self.db_manager.get_unseen_questions(student_id, user_type, question_type, count * 2)

        if user_type == "non_dev" and unseen:
            unseen = [q for q in unseen if not self._is_programming_question(q)]

        logger.info(f"📚 {question_type}: {len(unseen)} unseen for student {student_id}")

        if len(unseen) < count:
            needed = count - len(unseen) + self.REFRESH_BATCH_SIZE
            logger.info(f"🤖 Generating {needed} new {question_type} questions on-demand")

            new_qs = self.ai_service.generate_questions_for_bank(user_type, question_type, context, needed)
            if user_type == "non_dev" and new_qs:
                new_qs = [q for q in new_qs if not self._is_programming_question(q)]

            if new_qs:
                for q in new_qs:
                    q["question_id"]   = str(uuid.uuid4())
                    q["question_hash"] = hashlib.md5(q.get("question", "").encode()).hexdigest()
                added = self.db_manager.add_questions_to_bank(new_qs, user_type)
                logger.info(f"✅ Added {added} questions to bank")

                unseen = self.db_manager.get_unseen_questions(student_id, user_type, question_type, count * 2)
                if user_type == "non_dev":
                    unseen = [q for q in unseen if not self._is_programming_question(q)]

        return self._format_questions(unseen[:count], question_type, is_mcq)

    def _format_questions(self, questions, q_type, is_mcq):
        formatted = []
        for q in questions:
            fq = {
                "question_id":         q.get("question_id", str(uuid.uuid4())),
                "question_number":     0,
                "title":               q.get("title", "Question"),
                "difficulty":          q.get("difficulty", "Medium"),
                "question_type":       q_type,
                "question":            q.get("question", ""),
                "options":             q.get("options") if is_mcq else None,
                "correct_answer":      q.get("correct_answer"),
                "correct_option_text": q.get("correct_option_text"),
                "is_mcq":              is_mcq,
            }
            if is_mcq and (not fq["options"] or len(fq["options"]) < 4):
                fq["options"] = ["Option A", "Option B", "Option C", "Option D"]
            formatted.append(fq)
        return formatted

    # ════════════════════════════════════════════════════════════
    # SUBMIT
    # ════════════════════════════════════════════════════════════

    async def submit_answer(self, test_id: str, question_number: int, answer: str, test_results: Dict = None):
        try:
            if self.db_manager.is_test_terminated(test_id):
                raise ValueError(f"Test terminated: {self.db_manager.get_termination_reason(test_id)}")

            test_data = self.memory_manager.get_test(test_id)
            if not test_data:
                raise ValueError("Test not found")

            user_type = test_data.get("user_type", "dev")
            processed = self._process_answer(answer, test_id, question_number)
            self.memory_manager.submit_answer(test_id, question_number, processed)

            # Store coding test results so evaluation uses actual results, not AI guessing
            if test_results and test_data.get("questions"):
                q = test_data["questions"][question_number - 1] if question_number <= len(test_data["questions"]) else {}
                if q.get("question_type") == "coding":
                    if "coding_test_results" not in test_data:
                        test_data["coding_test_results"] = {}
                    test_data["coding_test_results"][str(question_number)] = test_results
                    logger.info(f"💾 Stored test results for Q{question_number}: {test_results.get('overall_result', '?')} ({test_results.get('total_passed', 0)}/{test_results.get('total_cases', 0)} passed)")

            if self.memory_manager.is_test_complete(test_id):
                return await self._complete_test(test_id, test_data)

            next_q = self.memory_manager.get_current_question(test_id)
            next_q["question_html"] = markdown.markdown(next_q["question_html"], extensions=['fenced_code'])
            questions = test_data.get("questions", [])
            q_num     = next_q["question_number"]
            q_data    = questions[q_num - 1] if q_num <= len(questions) else {}
            time_limit = self._get_time_limit(q_data.get("question_type", "mcq"), user_type)
            return self._create_next_response(next_q, time_limit, test_data)

        except Exception as e:
            logger.error(f"❌ Submit failed: {e}")
            raise

    # Sentinel values the frontend sends when student skips or uses final submit
    SENTINEL_VALUES = {"__SKIPPED__", "__FINAL_SUBMIT__", "__SKIP__", "__TIMEOUT__", ""}

    def _detect_dominant_language(self, context: str) -> str:
        """
        Count language signals in course content and return the dominant one.
        Used to ensure all coding questions in a test use the same language.
        """
        if not context:
            return "python"
        ctx = context.lower()
        scores = {
            "java":       sum(ctx.count(s) for s in [
                              "scanner", "system.out", "public class", "arraylist",
                              "hashmap", "import java", "void main", "string[]",
                              "integer", "bufferedreader", "throws", ".java"]),
            "python":     sum(ctx.count(s) for s in [
                              "def ", "print(", "input(", "import numpy", "import pandas",
                              "elif ", "list(", "dict(", "tuple(", ".py", "python"]),
            "javascript": sum(ctx.count(s) for s in [
                              "console.log", "const ", "let ", "var ", "require(",
                              "node.js", "javascript", "async/await", "=>"]),
            "cpp":        sum(ctx.count(s) for s in [
                              "cout", "cin", "#include", "std::", "iostream", ".cpp"]),
        }
        dominant = max(scores, key=scores.get)
        # Only return a language if it has a clear signal, else default python
        if scores[dominant] == 0:
            return "python"
        logger.debug(f"Language scores: {scores} → {dominant}")
        return dominant

    def _process_answer(self, answer, test_id, q_num):
        # Treat frontend sentinel values as empty (no answer given)
        if not answer or answer.strip() in self.SENTINEL_VALUES:
            # For coding questions, try to recover actual code from stored user_code
            try:
                q = self.memory_manager.get_test(test_id)["questions"][q_num - 1]
                if q.get("question_type") == "coding" and q.get("user_code"):
                    logger.info(f"♻️  Recovering stored code for Q{q_num} (sentinel answer)")
                    return q["user_code"]
            except:
                pass
            return ""   # empty = skipped

        if answer.isdigit():
            try:
                q       = self.memory_manager.get_test(test_id)["questions"][q_num - 1]
                options = q.get("options", [])
                idx     = int(answer)
                if 0 <= idx < len(options):
                    return options[idx]
            except:
                pass
        return answer.strip()

    def add_warning(self, test_id, student_id, warning_type, details=None):
        result = self.db_manager.add_warning(test_id, student_id, warning_type, details)
        if result.get("should_terminate"):
            logger.warning(f"🚫 Auto-terminating {test_id} after 3 warnings")
        return result

    def get_warning_status(self, test_id):
        w = self.db_manager.get_warnings(test_id)
        return {
            "test_id":            test_id,
            "warning_count":      w.get("warning_count", 0),
            "max_warnings":       3,
            "warnings_remaining": max(0, 3 - w.get("warning_count", 0)),
            "is_terminated":      w.get("terminated", False),
            "termination_reason": w.get("termination_reason"),
            "warnings":           w.get("warnings", [])
        }

    # ════════════════════════════════════════════════════════════
    # COMPLETE TEST — triggers background bank refresh
    # ════════════════════════════════════════════════════════════

    async def _complete_test(self, test_id: str, test_data: Dict):
        logger.info(f"🎯 Completing test: {test_id}")

        answers   = self.memory_manager.get_test_answers(test_id)
        user_type = test_data.get("user_type", "dev")
        questions = test_data.get("questions", [])

        sections = {"aptitude": [], "mcq": [], "coding": []} if user_type == "dev" \
                   else {"aptitude": [], "mcq": []}

        for i, ans_data in enumerate(answers):
            q      = questions[i] if i < len(questions) else {}
            q_type = q.get("question_type", "mcq")
            if user_type == "non_dev" and q_type not in ["aptitude", "mcq"]:
                q_type = "mcq"
            if q_type in sections:
                stored_answer = ans_data.get("answer", "")
                # For coding: if answer is empty/sentinel, recover from user_code
                if q_type == "coding" and (not stored_answer or stored_answer in self.SENTINEL_VALUES):
                    stored_answer = q.get("user_code", "")
                    if stored_answer:
                        logger.info(f"♻️  Recovered code from user_code for Q{i+1}")
                sections[q_type].append({
                    "question":            q.get("question", ans_data.get("question", "")),
                    "answer":              stored_answer,
                    "question_number":     q.get("question_number", i + 1),
                    "question_type":       q_type,
                    "options":             q.get("options", []),
                    "correct_answer":      q.get("correct_answer"),
                    "correct_option_text": q.get("correct_option_text"),
                })

        # ── Run test cases for any coding questions that weren't pre-run ──────
        # If student submitted without clicking "Run Tests", no results are stored.
        # Run them now so we always score on actual execution, never AI guessing.
        coding_test_results = test_data.get("coding_test_results", {})

        if user_type == "dev":
            for i, ans_data in enumerate(answers):
                q      = questions[i] if i < len(questions) else {}
                q_num  = q.get("question_number", i + 1)
                q_type = q.get("question_type", "mcq")

                if q_type == "coding" and str(q_num) not in coding_test_results:
                    user_code = ans_data.get("answer", "").strip()
                    all_tc    = q.get("test_cases", [])

                    if user_code and all_tc:
                        # Detect language from question or default java (dev track)
                        lang = q.get("user_language") or                                self.ai_service._detect_language_from_question(q.get("question", ""))
                        logger.info(f"🔄 Running test cases for Q{q_num} ({lang}) — not pre-run by student")
                        try:
                            import asyncio
                            tc_results = await self.ai_service.run_test_cases(lang, user_code, all_tc)
                            coding_test_results[str(q_num)] = tc_results
                            logger.info(
                                f"✅ Q{q_num} test results: {tc_results['overall_result']} "
                                f"({tc_results['total_passed']}/{tc_results['total_cases']} passed)"
                            )
                        except Exception as e:
                            logger.error(f"❌ Failed to run test cases for Q{q_num}: {e}")
                    elif not user_code:
                        logger.info(f"⏭️  Q{q_num}: no code submitted — marking as 0")
                    elif not all_tc:
                        logger.warning(f"⚠️  Q{q_num}: no test cases stored — falling back to AI")

        if coding_test_results:
            logger.info(f"✅ Passing {len(coding_test_results)} coding test results to evaluator")
        # ─────────────────────────────────────────────────────────────────────

        eval_result = self.ai_service.evaluate_by_section(user_type, sections, coding_test_results)
        logger.info(f"✅ {eval_result.get('total_correct', 0)}/{len(answers)} correct")

        await self._save_results(test_id, test_data, eval_result, answers)
        self.memory_manager.cleanup_test(test_id)

        # ── KEY LINE: auto-refresh bank in background ──────────
        self._trigger_background_refresh(user_type)
        # ───────────────────────────────────────────────────────

        return self._create_complete_response(eval_result, test_data["total_questions"], user_type, test_id)

    async def force_complete_test(self, test_id: str, reason: str, warnings: int = 0):
        logger.warning(f"🚨 Force complete: {test_id} — {reason}")
        try:
            test_data = self.memory_manager.get_test(test_id)
            if not test_data:
                return {"status": "not_found"}

            answers   = self.memory_manager.get_test_answers(test_id) or []
            user_type = test_data.get("user_type", "dev")
            questions = test_data.get("questions", [])

            sections = {"aptitude": [], "mcq": [], "coding": []} if user_type == "dev" \
                       else {"aptitude": [], "mcq": []}

            for i, ans in enumerate(answers):
                q  = questions[i] if i < len(questions) else {}
                qt = q.get("question_type", "mcq")
                if user_type == "non_dev" and qt not in ["aptitude", "mcq"]:
                    qt = "mcq"
                if qt in sections:
                    sections[qt].append({
                        "question":          q.get("question", ans.get("question", "")),
                        "answer":            ans.get("answer", ""),
                        "question_type":     qt,
                        "options":           q.get("options", []),
                        "correct_answer":    q.get("correct_answer"),
                        "correct_option_text": q.get("correct_option_text"),
                    })

            eval_result = self.ai_service.evaluate_by_section(user_type, sections)
            eval_result["terminated"]         = True
            eval_result["termination_reason"] = reason

            await self._save_results(test_id, test_data, eval_result, answers)
            self.memory_manager.cleanup_test(test_id)
            self._trigger_background_refresh(user_type)

            return {"status": "terminated", "reason": reason}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _create_complete_response(self, eval_result, total_q, user_type, test_id):
        correct = eval_result.get("total_correct", 0)
        pct     = round((correct / total_q) * 100, 1) if total_q else 0
        if pct >= 80:   status, msg = "Excellent",        "Excellent performance!"
        elif pct >= 50: status, msg = "Good",              "Good attempt, room for improvement."
        else:           status, msg = "Needs Improvement", "Please practice more."
        warnings = self.db_manager.get_warnings(test_id)

        class Response:
            def __init__(self, **kw):
                for k, v in kw.items(): setattr(self, k, v)

        return Response(
            test_completed=True, score=correct, total_questions=total_q,
            score_percentage=pct, analytics=eval_result.get("evaluation_report", ""),
            section_scores=eval_result.get("section_scores", {}),
            section_details=eval_result.get("section_details", {}),
            warning_count=warnings.get("warning_count", 0),
            terminated_by_warnings=warnings.get("terminated", False),
            summary={"status": status, "percentage": pct, "final_message": msg}
        )

    async def _save_results(self, test_id, test_data, eval_result, answers):
        questions       = test_data.get("questions", [])
        scores          = eval_result.get("scores", [])
        feedbacks       = eval_result.get("feedbacks", [])
        section_details = eval_result.get("section_details", {})
        total_correct   = eval_result.get("total_correct", 0)
        total_q         = test_data.get("total_questions", len(questions))
        pct             = round((total_correct / total_q) * 100, 1) if total_q else 0

        conversation_pairs = []
        for idx, ans in enumerate(answers):
            q  = questions[idx] if idx < len(questions) else {}
            conversation_pairs.append({
                "question_number": idx + 1,
                "question_id":     q.get("question_id"),
                "question":        q.get("question"),
                "question_type":   q.get("question_type"),
                "answer":          ans.get("answer"),
                "correct":         bool(scores[idx]) if idx < len(scores) else False,
                "correct_answer":  q.get("correct_option_text") or q.get("correct_answer", "N/A"),
                "feedback":        feedbacks[idx] if idx < len(feedbacks) else "",
                "options":         q.get("options", []),
            })

        if pct >= 80:   final_msg = "Excellent performance!"
        elif pct >= 50: final_msg = "Good attempt, room for improvement."
        else:           final_msg = "Needs Improvement. Please practice more."

        wd = self.db_manager.get_warnings(test_id)

        # Build student info for storage
        # student_profile comes from MySQL (name, course, batch, role_type etc.)
        # This is what enables large-scale reporting:
        #   - Filter by batch, course, role_type
        #   - Track individual student progress over multiple tests
        #   - Compare dev vs non-dev performance
        student_profile = test_data.get("student_profile", {})

        self.db_manager.test_results_collection.update_one(
            {"test_id": test_id},
            {"$set": {
                # ── Test identity ──────────────────────────────────
                "test_id":   test_id,
                "user_type": test_data.get("user_type"),

                # ── Student identity (from MySQL) ──────────────────
                # Stored here so MongoDB results are self-contained.
                # No need to join MySQL at query time.
                "student_id":   test_data.get("student_id"),
                "student_name": student_profile.get("student_name", ""),
                "email":        student_profile.get("email", ""),
                "course":       student_profile.get("course", ""),
                "batch":        student_profile.get("batch", ""),
                "role_type":    student_profile.get("role_type", ""),
                "experience":   student_profile.get("experience", ""),
                "org_id":       student_profile.get("org_id"),

                # ── Scores ─────────────────────────────────────────
                "score":              total_correct,
                "total_questions":    total_q,
                "score_percentage":   pct,
                "final_message":      final_msg,
                "section_scores":     eval_result.get("section_scores", {}),
                "section_details":    section_details,
                "evaluation_report":  eval_result.get("evaluation_report", ""),
                "scores":             scores,
                "feedbacks":          feedbacks,
                "conversation_pairs": conversation_pairs,

                # ── Meta ───────────────────────────────────────────
                "test_completed":        True,
                "timestamp":             time.time(),
                "warning_count":         wd.get("warning_count", 0),
                "warnings":              wd.get("warnings", []),
                "terminated_by_warnings": wd.get("terminated", False),
                "termination_reason":    wd.get("termination_reason"),
            }},
            upsert=True
        )
        logger.info(
            f"💾 Saved: {test_id} | "
            f"student={test_data.get('student_id')} ({student_profile.get('student_name', 'unknown')}) | "
            f"{total_correct}/{total_q} ({pct}%) | "
            f"course={student_profile.get('course')} batch={student_profile.get('batch')}"
        )

    # ════════════════════════════════════════════════════════════
    # RESPONSE BUILDERS
    # ════════════════════════════════════════════════════════════

    def _get_time_limit(self, q_type, user_type):
        if user_type == "non_dev":
            return {"aptitude": 60, "mcq": 60}.get(q_type, 60)
        return {"aptitude": 60, "mcq": 60, "coding": 600}.get(q_type, 60)

    def _create_start_response(self, test_id, test_data, current_q, time_limit, exam_structure, user_type):
        questions       = test_data.get("questions", [])
        section_info    = self._get_section_info(questions, user_type)
        current_section = self._get_current_section(1, section_info)
        first_q         = questions[0] if questions else {}

        class R:
            def __init__(self, **kw):
                for k, v in kw.items(): setattr(self, k, v)

        return R(
            test_id=test_id, user_type=user_type,
            question_number=current_q["question_number"],
            total_questions=current_q["total_questions"],
            question_html=current_q["question_html"],
            question_type=first_q.get("question_type", "aptitude"),
            title=first_q.get("title", ""), options=first_q.get("options"),
            is_mcq=first_q.get("is_mcq", True), time_limit=time_limit,
            exam_structure=exam_structure, current_section=current_section,
            section_info=section_info,
            section_progress=self._get_section_progress(1, section_info)
        )

    def _create_next_response(self, next_q, time_limit, test_data):
        user_type    = test_data.get("user_type", "dev")
        questions    = test_data.get("questions", [])
        section_info = self._get_section_info(questions, user_type)
        q_num        = next_q["question_number"]
        curr_sec     = self._get_current_section(q_num, section_info)
        q            = questions[q_num - 1] if q_num <= len(questions) else {}
        prev_sec     = self._get_current_section(q_num - 1, section_info) if q_num > 1 else curr_sec
        sec_completed = prev_sec["display_name"] if prev_sec["name"] != curr_sec["name"] else None

        class R:
            def __init__(self, **kw):
                for k, v in kw.items(): setattr(self, k, v)

        return R(
            test_completed=False,
            next_question=R(
                question_number=next_q["question_number"],
                total_questions=next_q["total_questions"],
                question_html=next_q["question_html"],
                question_type=q.get("question_type", "mcq"),
                title=q.get("title", ""), options=q.get("options"),
                is_mcq=q.get("is_mcq", True), time_limit=time_limit
            ),
            current_section=curr_sec,
            section_info=section_info,
            section_progress=self._get_section_progress(q_num, section_info),
            section_just_completed=sec_completed,
            next_section_starting=curr_sec["display_name"] if sec_completed else None
        )

    def _get_section_info(self, questions, user_type):
        if user_type == "non_dev":
            secs  = {"aptitude": {"start": None, "end": None, "count": 0},
                     "mcq":      {"start": None, "end": None, "count": 0}}
            order = ["aptitude", "mcq"]
        else:
            secs  = {"aptitude": {"start": None, "end": None, "count": 0},
                     "mcq":      {"start": None, "end": None, "count": 0},
                     "coding":   {"start": None, "end": None, "count": 0}}
            order = ["aptitude", "mcq", "coding"]

        for i, q in enumerate(questions, 1):
            qt = q.get("question_type", "mcq")
            if qt in secs:
                if secs[qt]["start"] is None: secs[qt]["start"] = i
                secs[qt]["end"]    = i
                secs[qt]["count"] += 1

        return {
            "sections": [
                {"name": n, "display_name": n.upper(),
                 "start": secs[n]["start"], "end": secs[n]["end"], "count": secs[n]["count"]}
                for n in order if secs[n]["count"] > 0
            ],
            "total_sections": sum(1 for n in order if secs[n]["count"] > 0)
        }

    def _get_current_section(self, q_num, section_info):
        for i, sec in enumerate(section_info.get("sections", [])):
            if sec["start"] <= q_num <= sec["end"]:
                return {"index": i, "name": sec["name"], "display_name": sec["display_name"],
                        "start": sec["start"], "end": sec["end"], "count": sec["count"]}
        return {"name": "unknown", "index": 0}

    def _get_section_progress(self, q_num, section_info):
        curr   = self._get_current_section(q_num, section_info)
        in_sec = q_num - curr.get("start", 1) + 1
        total  = curr.get("count", 1)
        return {"current_in_section": in_sec, "total_in_section": total,
                "is_last_question_in_section": in_sec >= total}

    def _get_question_time_limit(self, q_type, user_type):
        return self._get_time_limit(q_type, user_type)

    # ════════════════════════════════════════════════════════════
    # DATA RETRIEVAL
    # ════════════════════════════════════════════════════════════

    async def get_test_results(self, test_id: str) -> Optional[Dict]:
        doc = self.db_manager.test_results_collection.find_one({"test_id": test_id}, {"_id": 0})
        if doc:
            return {
                "test_id":                doc.get("test_id"),
                "score":                  doc.get("score", 0),
                "total_questions":        doc.get("total_questions", 0),
                "score_percentage":       doc.get("score_percentage", 0),
                "analytics":              doc.get("evaluation_report", ""),
                "section_scores":         doc.get("section_scores", {}),
                "section_details":        doc.get("section_details", {}),
                "timestamp":              doc.get("timestamp", 0),
                "warning_count":          doc.get("warning_count", 0),
                "terminated_by_warnings": doc.get("terminated_by_warnings", False),
            }
        return None

    async def get_all_tests(self) -> List[Dict]:
        return list(self.db_manager.test_results_collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(100))

    async def get_students(self) -> List[Dict]:
        return list(self.db_manager.test_results_collection.aggregate([
            {"$group": {"_id": "$Student_ID"}},
            {"$project": {"Student_ID": "$_id", "_id": 0}}
        ]))

    async def get_student_tests(self, student_id: str) -> List[Dict]:
        return list(self.db_manager.test_results_collection.find(
            {"Student_ID": int(student_id)}, {"_id": 0}
        ).sort("timestamp", -1))

    def cleanup_expired_tests(self) -> Dict:
        self.memory_manager.cleanup_expired_data()
        return {"message": "Cleanup complete", "active_tests": len(self.memory_manager.tests)}

    def health_check(self) -> Dict:
        return {"status": "healthy"}


_test_service = None

def get_test_service() -> TestService:
    global _test_service
    if _test_service is None:
        _test_service = TestService()
    return _test_service