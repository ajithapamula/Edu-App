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

FIX: force_complete_test now uses _score_sections_fast() — instant MCQ scoring,
     no LLM call, no timeout, no ERR_EMPTY_RESPONSE on /api/warnings.
FIX: force_complete_test CASE 1 & 2 use test_completed check instead of score > 0
     so 0-score terminated results are never overwritten.
FIX: _save_results detects boilerplate/skipped coding answers and stores None
     so Question Review tab shows "Not answered" instead of template code.
FIX: _save_results now calls Groq to generate real per-question step-by-step
     explanations for all wrong/skipped questions before saving to MongoDB.
     Options are included in the prompt for MCQ questions.
FIX: _sanitize_result() strips all known bad/hardcoded feedback strings before
     every MongoDB write — "No code submitted before termination" etc. are
     replaced with "" so Groq generates proper explanations on next PDF load.

STARTUP: Call test_service.run_startup_migrations() in your FastAPI startup event:
    @app.on_event("startup")
    async def startup():
        test_service.run_startup_migrations()
"""

import logging
import markdown
import time
import hashlib
import uuid
import asyncio
import random
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class TestService:

    REFRESH_THRESHOLD  = 60
    REFRESH_BATCH_SIZE = 30
    MAX_USAGE_COUNT    = 10

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

    # Common boilerplate patterns injected by the code editor when student skips
    _BOILERPLATE_PATTERNS = [
        # Python
        "# write your solution here\ndef solution():\n    # your code here\n    pass\n\n# test your solution\nif __name__ == \"__main__\":\n    solution()",
        "# write your solution here\ndef solution():\n    # your code here\n    pass",
        # JavaScript
        "// write your solution here\nfunction solution() {\n    // your code here\n}",
        # Java
        "public class solution {\n    public static void main(string[] args) {\n        // write your solution here\n    }\n}",
        # Go variants
        "// write your solution here\n// write your go solution here",
        # The exact Go boilerplate the editor injects with Hello World
        "package main\nimport \"fmt\"\n// write your solution here\nfunc solution() {\n// your code here\nfmt.println(\"hello, world!\")\n}\nfunc main() {\nsolution()\n}",
        "package main\nimport \"fmt\"\nfunc solution() {\nfmt.println(\"hello, world!\")\n}\nfunc main() {\nsolution()\n}",
    ]

    def __init__(self):
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
        asyncio.ensure_future(self._warmup_bank())

    async def _warmup_bank(self):
        try:
            await asyncio.sleep(5)
            logger.info("🔥 Bank warmup starting...")
            for user_type in ["dev", "non_dev"]:
                bad  = self._deactivate_bad_questions(user_type)
                over = self._deactivate_overused_questions(user_type)
                if bad or over:
                    logger.info(f"🧹 Startup cleanup: removed {bad} generic + {over} overused ({user_type})")
                await self._refresh_question_bank(user_type)
            logger.info("✅ Bank warmup complete")
        except Exception as e:
            logger.error(f"❌ Bank warmup failed: {e}")

    # ════════════════════════════════════════════════════════════
    # AUTO BANK REFRESH
    # ════════════════════════════════════════════════════════════

    async def _refresh_question_bank(self, user_type: str):
        try:
            logger.info(f"🔄 [BG] Bank refresh starting for {user_type}...")

            deactivated = self._deactivate_overused_questions(user_type)
            if deactivated:
                logger.info(f"🗑️  [BG] Deactivated {deactivated} over-used questions")

            bad_removed = self._deactivate_bad_questions(user_type)
            if bad_removed:
                logger.info(f"🧹 [BG] Removed {bad_removed} generic questions — will regenerate")

            context      = self.content_service.get_context_for_questions(user_type)
            sections     = ["aptitude", "mcq", "coding"] if user_type == "dev" else ["aptitude", "mcq"]
            dominant_lang = self._detect_dominant_language(context)
            logger.info(f"🔤 [BG] Dominant language detected: {dominant_lang}")

            for section in sections:
                available = self._count_available_questions(user_type, section)
                logger.info(f"📊 [BG] {user_type}/{section}: {available} available")

                if available < self.REFRESH_THRESHOLD:
                    needed = self.REFRESH_THRESHOLD - available + self.REFRESH_BATCH_SIZE
                    logger.info(f"⚡ [BG] Generating {needed} new {section} questions...")

                    section_context = "" if section == "aptitude" else context
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

    def _deactivate_overused_questions(self, user_type: str) -> int:
        result = self.db_manager.question_bank_collection.update_many(
            {"user_type": user_type, "active": True, "usage_count": {"$gte": self.MAX_USAGE_COUNT}},
            {"$set": {"active": False}}
        )
        return result.modified_count

    def _deactivate_bad_questions(self, user_type: str) -> int:
        deactivated = 0
        try:
            cursor = self.db_manager.question_bank_collection.find({
                "user_type": user_type, "question_type": "mcq", "active": True
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
            "user_type": user_type, "question_type": question_type, "active": True
        })

    def _trigger_background_refresh(self, user_type: str):
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

    def _is_boilerplate_code(self, code: str, question: Dict) -> bool:
        """
        Returns True if the submitted code is just the editor's default boilerplate
        (meaning the student never typed anything — treat as skipped).

        Uses pattern-based detection instead of exact match so whitespace/
        indentation differences don't matter.
        """
        if not code:
            return False

        # Normalize: lowercase + collapse all whitespace to single spaces
        normalized = ' '.join(code.strip().lower().split())

        # Check against question's own stored boilerplate first
        stored_bp = (
            question.get("boilerplate_code") or question.get("starter_code") or
            question.get("template_code") or question.get("default_code") or ""
        )
        if stored_bp:
            stored_normalized = ' '.join(stored_bp.strip().lower().split())
            if normalized == stored_normalized:
                return True

        # ── Pattern-based detection (language agnostic) ──────────────────
        # A submission is boilerplate if it contains a template comment
        # AND the only real output is Hello World or nothing

        TEMPLATE_COMMENT_SIGNALS = [
            '// write your solution here',
            '// your code here',
            '// write code here',
            '# write your solution here',
            '# your code here',
            '# write code here',
            '/* write your solution here */',
        ]

        HELLO_WORLD_SIGNALS = [
            'hello, world!',
            'hello world',
            '"hello, world!"',
            '"hello world"',
            "'hello, world!'",
            "'hello world'",
        ]

        has_template_comment = any(sig in normalized for sig in TEMPLATE_COMMENT_SIGNALS)
        has_hello_world      = any(sig in normalized for sig in HELLO_WORLD_SIGNALS)

        if has_template_comment:
            logger.info(f"🚫 Boilerplate detected (template comment found)")
            return True

        if has_hello_world:
            # Hello World with no real logic = boilerplate
            # Strip all comments and boilerplate structure, check if anything real remains
            import re
            code_lower = code.lower()
            # Remove all comment lines
            no_comments = re.sub(r'//.*|#.*|/\*.*?\*/', '', code_lower, flags=re.DOTALL)
            # Remove known boilerplate structure keywords
            for kw in [
                'package main', 'import "fmt"', "import 'fmt'",
                'func main()', 'func solution()', 'def solution():',
                'public static void main', 'public class solution', 'public class main',
                'function solution()', 'fmt.println', 'system.out.println',
                'console.log', 'print(', 'println(',
                'hello, world!', 'hello world',
                '{', '}', '(', ')', ';', '\n', '\t',
            ]:
                no_comments = no_comments.replace(kw, ' ')
            remaining = no_comments.strip()
            if not remaining or len(remaining.replace(' ', '')) < 10:
                logger.info(f"🚫 Boilerplate detected (Hello World only, no real logic)")
                return True

        # ── Exact normalized match against known patterns ────────────────
        KNOWN_BOILERPLATE_NORMALIZED = [
            # Python
            '# write your solution here def solution(): # your code here pass # test your solution if __name__ == "__main__": solution()',
            '# write your solution here def solution(): # your code here pass',
            # JavaScript
            '// write your solution here function solution() { // your code here }',
            # Java
            'public class solution { public static void main(string[] args) { // write your solution here } }',
            # Go
            '// write your solution here // write your go solution here',
        ]
        for bp in KNOWN_BOILERPLATE_NORMALIZED:
            bp_norm = ' '.join(bp.strip().lower().split())
            if normalized == bp_norm:
                return True

        return False

    # ════════════════════════════════════════════════════════════
    # STARTUP MIGRATION — auto-clean bad data on server start
    # ════════════════════════════════════════════════════════════

    def run_startup_migrations(self):
        """
        Auto-clean known bad/hardcoded strings from existing MongoDB records.
        Call this once on server startup — idempotent and fast.
        """
        try:
            # 1. Clean bad feedback strings from conversation_pairs
            result = self.db_manager.test_results_collection.update_many(
                {"conversation_pairs.feedback": {"$in": [
                    "No code submitted before termination",
                    "Not Attempted", "Skipped",
                    "No answer submitted", "N/A",
                ]}},
                {"$set": {"conversation_pairs.$[elem].feedback": ""}},
                array_filters=[{"elem.feedback": {"$in": [
                    "No code submitted before termination",
                    "Not Attempted", "Skipped",
                    "No answer submitted", "N/A",
                ]}}]
            )
            if result.modified_count:
                logger.info(f"🧹 Startup migration: cleaned {result.modified_count} bad feedback strings")

            # 2. Unset cached PDF paths so stale PDFs regenerate with correct data
            self.db_manager.test_results_collection.update_many(
                {"$or": [
                    {"conversation_pairs.feedback": ""},
                    {"conversation_pairs": {"$elemMatch": {
                        "question_type": "coding",
                        "correct_answer": {"$in": ["N/A", "", None]}
                    }}}
                ]},
                {"$unset": {"pdf_path": "", "pdf_url": ""}}
            )
            logger.info("✅ Startup migrations complete")

        except Exception as e:
            logger.warning(f"⚠️ Startup migration failed (non-fatal): {e}")



    # Known stale/hardcoded strings that should never reach MongoDB
    _BAD_FEEDBACK_STRINGS = {
        "no code submitted before termination",
        "not attempted",
        "skipped",
        "no answer submitted",
        "test terminated",
        "n/a",
        "na",
    }

    def _sanitize_result(self, data: dict) -> dict:
        """
        Strip known bad/hardcoded feedback strings from conversation_pairs
        and section_details before saving to MongoDB.
        Any bad string is replaced with "" so Groq fills it on next PDF load.
        """
        def _clean(text) -> str:
            if not text:
                return ""
            if str(text).strip().lower() in self._BAD_FEEDBACK_STRINGS:
                return ""
            return text

        # Clean conversation_pairs feedbacks
        for cp in data.get("conversation_pairs", []):
            cp["feedback"] = _clean(cp.get("feedback"))

        # Clean section_details explanations
        for sec in data.get("section_details", {}).values():
            for q in sec.get("questions", []):
                q["explanation"] = _clean(q.get("explanation"))

        # Clean top-level feedbacks list
        if "feedbacks" in data:
            data["feedbacks"] = [_clean(f) for f in data["feedbacks"]]

        return data



    async def _generate_explanations_batch(self, wrong_pairs: List[Dict]) -> Dict[int, str]:
        """
        Call Groq once to generate step-by-step explanations for all
        wrong/skipped questions. Returns {question_number: explanation_text}.

        Works for both Developer and Non-Developer tracks.
        Includes options in the prompt for MCQ questions.

        wrong_pairs: list of conversation_pair dicts where is_correct=False or skipped.
        """
        if not wrong_pairs:
            return {}

        explanations = {}
        try:
            # Build a compact prompt listing all wrong questions with options
            lines = []
            for item in wrong_pairs:
                q_num    = item["question_number"]
                question = item["question"] or ""
                correct  = item["correct_answer"] or ""
                user_ans = item.get("answer") or "No answer (skipped)"
                options  = item.get("options", [])

                # Include options for MCQ context
                opts_text = ""
                if options:
                    opts_text = "\nOptions: " + " / ".join(
                        f"{chr(65+i)}) {o}" for i, o in enumerate(options)
                    )

                lines.append(
                    f"Q{q_num}:\n"
                    f"Question: {question}{opts_text}\n"
                    f"Student answered: {user_ans}\n"
                    f"Correct answer: {correct}"
                )

            prompt = (
                "You are an expert tutor reviewing a student's test. "
                "For each question below, write a step-by-step explanation showing HOW to reach the correct answer.\n\n"
                "RULES:\n"
                "- Show calculation steps for math/aptitude (Step 1: ... Step 2: ... Step 3: ...)\n"
                "- For MCQ/theory: explain WHY the correct option is right and what the wrong option actually means\n"
                "- Point out exactly where the student's answer went wrong\n"
                "- End each explanation with: Therefore, the correct answer is [answer]\n"
                "- Keep each explanation under 5 lines — concise but complete\n"
                "- NEVER just restate the answer — always show the WHY and HOW\n\n"
                "Respond in this EXACT format for each question:\n"
                "Q<number>: <explanation>\n\n"
                + "\n\n".join(lines)
            )

            # Use the Groq client from ai_service
            client = getattr(self.ai_service, "client", None) or getattr(self.ai_service, "groq_client", None)

            if client is None:
                logger.warning("⚠️ No Groq client found on ai_service — skipping explanation generation")
                return {}

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert tutor. Give step-by-step explanations. "
                            "For math questions show calculations. For theory questions explain why. "
                            "Be concise and educational. Respond only with Q<n>: <explanation> lines."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1200,
            )

            raw = response.choices[0].message.content.strip()
            logger.info(f"💡 Groq explanations generated for {len(wrong_pairs)} questions")

            # Parse "Q<n>: <text>" lines
            import re
            for match in re.finditer(r"Q(\d+):\s*(.+?)(?=\nQ\d+:|\Z)", raw, re.DOTALL):
                q_num = int(match.group(1))
                text  = match.group(2).strip().replace("\n", " ")
                explanations[q_num] = text

            logger.info(f"✅ Groq returned {len(explanations)} explanations")

        except Exception as e:
            logger.error(f"❌ Explanation batch generation failed: {e}")

        return explanations

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
            if q_type == "coding" and dominant_lang:
                section_context = f"PRIMARY LANGUAGE: {dominant_lang}\n\n{context}"
            elif q_type == "aptitude":
                section_context = ""
            else:
                section_context = context
            section_qs = self._get_section_questions_no_repeat(
                student_id, user_type, q_type, count, is_mcq, section_context
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

            if test_results and test_data.get("questions"):
                q = test_data["questions"][question_number - 1] if question_number <= len(test_data["questions"]) else {}
                if q.get("question_type") == "coding":
                    if "coding_test_results" not in test_data:
                        test_data["coding_test_results"] = {}
                    test_data["coding_test_results"][str(question_number)] = test_results
                    logger.info(
                        f"💾 Stored test results for Q{question_number}: "
                        f"{test_results.get('overall_result', '?')} "
                        f"({test_results.get('total_passed', 0)}/{test_results.get('total_cases', 0)} passed)"
                    )

            if self.memory_manager.is_test_complete(test_id):
                return await self._complete_test(test_id, test_data)

            next_q = self.memory_manager.get_current_question(test_id)
            next_q["question_html"] = markdown.markdown(next_q["question_html"], extensions=['fenced_code'])
            questions  = test_data.get("questions", [])
            q_num      = next_q["question_number"]
            q_data     = questions[q_num - 1] if q_num <= len(questions) else {}
            time_limit = self._get_time_limit(q_data.get("question_type", "mcq"), user_type)
            return self._create_next_response(next_q, time_limit, test_data)

        except Exception as e:
            logger.error(f"❌ Submit failed: {e}")
            raise

    SENTINEL_VALUES = {"__SKIPPED__", "__FINAL_SUBMIT__", "__SKIP__", "__TIMEOUT__", ""}

    def _detect_dominant_language(self, context: str) -> str:
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
            "go":         sum(ctx.count(s) for s in [
                              "golang", "go lang", "package main", "fmt.println",
                              "fmt.scan", "func main", "goroutine", "defer ",
                              "interface{}", "import \"fmt\"", ":= ",
                              "go programming", "the go language", "written in go"]),
        }
        dominant = max(scores, key=scores.get)
        if scores[dominant] == 0:
            return "python"
        logger.debug(f"Language scores: {scores} → {dominant}")
        return dominant

    def _process_answer(self, answer, test_id, q_num):
        if not answer or answer.strip() in self.SENTINEL_VALUES:
            try:
                q = self.memory_manager.get_test(test_id)["questions"][q_num - 1]
                if q.get("question_type") == "coding" and q.get("user_code"):
                    logger.info(f"♻️  Recovering stored code for Q{q_num} (sentinel answer)")
                    return q["user_code"]
            except:
                pass
            return ""

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
    # COMPLETE TEST
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
                if q_type == "coding" and (not stored_answer or stored_answer in self.SENTINEL_VALUES):
                    stored_answer = q.get("user_code", "")
                    if stored_answer:
                        logger.info(f"♻️  Recovered code from user_code for Q{i+1}")
                    if not stored_answer:
                        db_result = self.db_manager.get_coding_result(test_id, q.get("question_number", i+1))
                        if db_result and db_result.get("total_passed", 0) > 0:
                            stored_answer = f"[Code run — {db_result.get('total_passed',0)}/{db_result.get('total_cases',0)} passed]"
                            logger.info(f"♻️  Recovered result summary for Q{i+1} from DB")
                sections[q_type].append({
                    "question":            q.get("question", ans_data.get("question", "")),
                    "answer":              stored_answer,
                    "question_number":     q.get("question_number", i + 1),
                    "question_type":       q_type,
                    "options":             q.get("options", []),
                    "correct_answer":      q.get("correct_answer"),
                    "correct_option_text": q.get("correct_option_text"),
                })

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
                        lang = q.get("user_language") or \
                               self.ai_service._detect_language_from_question(q.get("question", ""))
                        logger.info(f"🔄 Running test cases for Q{q_num} ({lang}) — not pre-run by student")
                        try:
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

        eval_result = await self.ai_service.evaluate_by_section(user_type, sections, coding_test_results)
        logger.info(f"✅ {eval_result.get('total_correct', 0)}/{len(answers)} correct")

        await self._save_results(test_id, test_data, eval_result, answers)
        self.memory_manager.cleanup_test(test_id)
        self._trigger_background_refresh(user_type)

        return self._create_complete_response(eval_result, test_data["total_questions"], user_type, test_id)

    # ════════════════════════════════════════════════════════════
    # FAST MCQ SCORER — no LLM, instant scoring for termination
    # ════════════════════════════════════════════════════════════

    def _score_sections_fast(self, sections: dict, user_type: str) -> dict:
        """
        Score MCQ/aptitude instantly by comparing answer vs correct_answer.
        NO LLM call — prevents timeout and ERR_EMPTY_RESPONSE on /api/warnings.

        Coding: uses stored test case results if available, else 0.
        """
        total_correct  = 0
        section_scores = {}
        scores         = []
        feedbacks      = []

        for section_name, qs in sections.items():
            correct = 0
            for q in qs:
                q_type = q.get("question_type", "mcq")
                answer = (q.get("answer") or "").strip()

                if q_type == "coding":
                    tc = q.get("coding_result")
                    if tc and isinstance(tc, dict):
                        passed     = tc.get("total_passed", 0)
                        total_tc   = tc.get("total_cases", 1)
                        score      = round((passed / total_tc), 2) if total_tc else 0
                        if score > 0:
                            score = max(score, 0.1)
                        correct += score
                        scores.append(score >= 0.1)
                        feedbacks.append(f"Coding: {passed}/{total_tc} test cases passed")
                    else:
                        scores.append(False)
                        feedbacks.append("")  # Groq will generate "here's how to solve it" explanation
                    continue

                # MCQ / Aptitude — instant comparison
                is_correct   = False
                correct_text = (q.get("correct_option_text") or "").strip()
                correct_idx  = q.get("correct_answer")
                options      = q.get("options") or []

                if answer and correct_text and answer.lower() == correct_text.lower():
                    is_correct = True
                elif answer and correct_idx is not None:
                    try:
                        idx = int(correct_idx)
                        if 0 <= idx < len(options) and answer.lower() == str(options[idx]).lower():
                            is_correct = True
                    except (ValueError, TypeError):
                        if answer.lower() == str(correct_idx).lower():
                            is_correct = True

                if is_correct:
                    correct += 1
                scores.append(is_correct)
                # Store empty feedback — Groq will fill these in _save_results
                feedbacks.append("" if not is_correct else "Correct")

            total_in_section = len(qs)
            section_scores[section_name] = {
                "correct":    round(correct),
                "total":      total_in_section,
                "percentage": round((correct / total_in_section) * 100, 1) if total_in_section else 0,
            }
            total_correct += correct

        return {
            "total_correct":     round(total_correct),
            "section_scores":    section_scores,
            "section_details":   {},
            "evaluation_report": "Test was terminated due to proctoring violations. Scores reflect answered questions only.",
            "scores":            scores,
            "feedbacks":         feedbacks,
        }

    # ════════════════════════════════════════════════════════════
    # FORCE COMPLETE — fast scorer, no LLM, no timeout
    # ════════════════════════════════════════════════════════════

    async def force_complete_test(self, test_id: str, reason: str, warnings: int = 0):
        logger.warning(f"🚨 Force complete: {test_id} — {reason}")
        try:
            test_data = self.memory_manager.get_test(test_id)

            # ── CASE 1: Session gone from memory ─────────────────────────────
            if not test_data:
                logger.warning(f"⚠️ Session {test_id[:8]} not in memory — saving terminated record")

                wd         = self.db_manager.get_warnings(test_id)
                student_id = wd.get("student_id")

                student_name = course = batch = role_type = email = experience = ""
                org_id = None

                if student_id:
                    try:
                        import pymysql, pymysql.cursors, os
                        conn = pymysql.connect(
                            host=os.getenv("DB_HOST", "192.168.48.201"),
                            port=int(os.getenv("DB_PORT", "3306")),
                            user=os.getenv("DB_USER", "sa"),
                            password=os.getenv("DB_PASSWORD", "Welcome@123"),
                            database=os.getenv("DB_NAME", "SuperDB"),
                            cursorclass=pymysql.cursors.DictCursor,
                            connect_timeout=5, read_timeout=5,
                        )
                        with conn:
                            with conn.cursor() as cursor:
                                cursor.execute("""
                                    SELECT CONCAT(First_Name,' ',Last_Name) AS student_name,
                                           Email AS email, Course AS course, Batch AS batch,
                                           Role_Type AS role_type, Experience_Category AS experience,
                                           Org_ID AS org_id
                                    FROM tbl_Student WHERE ID=%s AND status=1 LIMIT 1
                                """, (int(student_id),))
                                row = cursor.fetchone()
                                if row:
                                    student_name = row.get("student_name", "")
                                    email        = row.get("email", "")
                                    course       = row.get("course", "")
                                    batch        = row.get("batch", "")
                                    role_type    = row.get("role_type", "")
                                    experience   = row.get("experience", "")
                                    org_id       = row.get("org_id")
                    except Exception as mysql_err:
                        logger.warning(f"⚠️ Could not fetch student profile: {mysql_err}")

                existing = self.db_manager.test_results_collection.find_one(
                    {"test_id": test_id}, {"_id": 0}
                )
                if existing and existing.get("test_completed"):
                    logger.info(f"✅ Result already exists score={existing.get('score', 0)} — skipping")
                    return {
                        "status":           "already_saved",
                        "reason":           reason,
                        "score":            existing.get("score", 0),
                        "total_questions":  existing.get("total_questions", 0),
                        "score_percentage": existing.get("score_percentage", 0),
                        "section_scores":   existing.get("section_scores", {}),
                        "section_details":  existing.get("section_details", {}),
                    }

                # ── Try to rescue question data from any existing partial record ──
                # When session expires from memory but MongoDB has a partial record
                # (e.g. auto-saved during test), use that to build proper results.
                rescued_pairs    = existing.get("conversation_pairs", []) if existing else []
                rescued_sections = existing.get("section_details", {})    if existing else {}

                if rescued_pairs:
                    logger.info(f"♻️ Rescued {len(rescued_pairs)} questions from existing partial record")

                    # Re-score rescued pairs quickly
                    rescued_correct  = sum(1 for p in rescued_pairs if p.get("correct"))
                    rescued_total    = len(rescued_pairs)
                    rescued_pct      = round((rescued_correct / rescued_total) * 100, 1) if rescued_total else 0

                    # Build section_scores from rescued pairs
                    sec_counts: dict = {}
                    for p in rescued_pairs:
                        qt = p.get("question_type", "mcq")
                        if qt not in sec_counts:
                            sec_counts[qt] = {"correct": 0, "total": 0}
                        sec_counts[qt]["total"]   += 1
                        sec_counts[qt]["correct"] += 1 if p.get("correct") else 0
                    rescued_section_scores = {
                        k: {
                            "correct":    v["correct"],
                            "total":      v["total"],
                            "percentage": round((v["correct"] / v["total"]) * 100, 1) if v["total"] else 0,
                        }
                        for k, v in sec_counts.items()
                    }

                    # Generate Groq explanations for all wrong questions in rescued pairs
                    needs_exp = [
                        p for p in rescued_pairs
                        if not p.get("correct")
                        and p.get("question_type") != "coding"
                        and not (p.get("feedback") and len(str(p.get("feedback", ""))) > 30)
                    ]
                    if needs_exp:
                        logger.info(f"💡 Generating explanations for {len(needs_exp)} rescued wrong questions...")
                        try:
                            exp_map = await self._generate_explanations_batch(needs_exp)
                            for p in rescued_pairs:
                                if p.get("question_number") in exp_map:
                                    p["feedback"] = exp_map[p["question_number"]]
                        except Exception as exp_err:
                            logger.warning(f"⚠️ Explanation gen failed: {exp_err}")

                    clean = self._sanitize_result({
                        "conversation_pairs": rescued_pairs,
                        "section_details":    rescued_sections,
                        "feedbacks":          [],
                    })

                    self.db_manager.test_results_collection.update_one(
                        {"test_id": test_id},
                        {"$set": {
                            "test_id": test_id, "user_type": existing.get("user_type", "dev"),
                            "student_id": student_id or existing.get("student_id"),
                            "student_name": student_name or existing.get("student_name", ""),
                            "email": email or existing.get("email", ""),
                            "course": course or existing.get("course", ""),
                            "batch":  batch  or existing.get("batch", ""),
                            "role_type": role_type or existing.get("role_type", ""),
                            "score":            rescued_correct,
                            "total_questions":  rescued_total,
                            "score_percentage": rescued_pct,
                            "section_scores":   rescued_section_scores,
                            "section_details":  clean["section_details"],
                            "conversation_pairs": clean["conversation_pairs"],
                            "final_message":    "Test terminated due to proctoring violations.",
                            "evaluation_report": "Test terminated — scores based on answered questions.",
                            "test_completed": True, "terminated": True,
                            "terminated_by_warnings": True, "termination_reason": reason,
                            "warning_count": warnings or wd.get("warning_count", 0),
                            "warnings": wd.get("warnings", []),
                            "timestamp": time.time(),
                        }},
                        upsert=True
                    )
                    logger.info(f"✅ Saved rescued terminated record: {rescued_correct}/{rescued_total} for {test_id[:8]}")
                    return {
                        "status": "terminated", "reason": reason,
                        "score": rescued_correct, "total_questions": rescued_total,
                        "score_percentage": rescued_pct,
                        "section_scores": rescued_section_scores,
                        "section_details": rescued_sections,
                    }

                # ── No existing data at all — save blank terminated record ────
                self.db_manager.test_results_collection.update_one(
                    {"test_id": test_id},
                    {"$set": {
                        "test_id": test_id, "user_type": "dev",
                        "student_id": student_id, "student_name": student_name,
                        "email": email, "course": course, "batch": batch,
                        "role_type": role_type, "experience": experience, "org_id": org_id,
                        "score": 0, "total_questions": 0, "score_percentage": 0,
                        "final_message": "Test terminated due to proctoring violations.",
                        "section_scores": {}, "section_details": {},
                        "evaluation_report": "Test was terminated before evaluation could complete.",
                        "scores": [], "feedbacks": [], "conversation_pairs": [],
                        "test_completed": True, "terminated": True,
                        "terminated_by_warnings": True, "termination_reason": reason,
                        "warning_count": warnings or wd.get("warning_count", 0),
                        "warnings": wd.get("warnings", []),
                        "timestamp": time.time(),
                    }},
                    upsert=True
                )
                logger.info(f"💾 Saved terminated record (no session) for {test_id[:8]}")
                return {
                    "status": "terminated", "reason": reason,
                    "score": 0, "total_questions": 0, "score_percentage": 0,
                    "section_scores": {}, "section_details": {},
                }

            # ── CASE 2: Session in memory — score instantly, no LLM ──────────
            existing = self.db_manager.test_results_collection.find_one(
                {"test_id": test_id}, {"score": 1, "test_completed": 1, "total_questions": 1,
                                       "score_percentage": 1, "section_scores": 1, "section_details": 1}
            )
            if existing and existing.get("test_completed"):
                logger.info(f"✅ Result already exists score={existing.get('score', 0)} — skipping")
                return {
                    "status":           "already_saved",
                    "reason":           reason,
                    "score":            existing.get("score", 0),
                    "total_questions":  existing.get("total_questions", 0),
                    "score_percentage": existing.get("score_percentage", 0),
                    "section_scores":   existing.get("section_scores", {}),
                    "section_details":  existing.get("section_details", {}),
                    "analytics":        existing.get("evaluation_report", ""),
                }

            answers             = self.memory_manager.get_test_answers(test_id) or []
            user_type           = test_data.get("user_type", "dev")
            questions           = test_data.get("questions", [])
            coding_test_results = test_data.get("coding_test_results", {})

            sections = {"aptitude": [], "mcq": [], "coding": []} if user_type == "dev" \
                       else {"aptitude": [], "mcq": []}

            for i, ans in enumerate(answers):
                q  = questions[i] if i < len(questions) else {}
                qt = q.get("question_type", "mcq")
                if user_type == "non_dev" and qt not in ["aptitude", "mcq"]:
                    qt = "mcq"
                if qt in sections:
                    q_num = q.get("question_number", i + 1)
                    sections[qt].append({
                        "question":            q.get("question", ans.get("question", "")),
                        "answer":              ans.get("answer", ""),
                        "question_number":     q_num,
                        "question_type":       qt,
                        "options":             q.get("options", []),
                        "correct_answer":      q.get("correct_answer"),
                        "correct_option_text": q.get("correct_option_text"),
                        # Attach stored coding result for fast scorer
                        "coding_result":       coding_test_results.get(str(q_num)),
                    })

            # ── INSTANT SCORING — no LLM, no timeout ─────────────────────────
            logger.info(f"⚡ Fast-scoring {sum(len(v) for v in sections.values())} partial answers")
            eval_result = self._score_sections_fast(sections, user_type)
            # ─────────────────────────────────────────────────────────────────

            eval_result["terminated"]         = True
            eval_result["termination_reason"] = reason

            await self._save_results(test_id, test_data, eval_result, answers)
            self.memory_manager.cleanup_test(test_id)
            self._trigger_background_refresh(user_type)

            total_correct = eval_result.get("total_correct", 0)
            total_q       = test_data.get("total_questions", len(questions))
            pct           = round((total_correct / total_q) * 100, 1) if total_q else 0

            logger.info(f"✅ Terminated test {test_id[:8]} scored: {total_correct}/{total_q} ({pct}%)")

            return {
                "status":           "terminated",
                "reason":           reason,
                "score":            total_correct,
                "total_questions":  total_q,
                "score_percentage": pct,
                "section_scores":   eval_result.get("section_scores", {}),
                "section_details":  eval_result.get("section_details", {}),
                "analytics":        eval_result.get("evaluation_report", ""),
            }

        except Exception as e:
            logger.error(f"❌ Force complete failed: {e}", exc_info=True)
            try:
                self.db_manager.test_results_collection.update_one(
                    {"test_id": test_id},
                    {"$set": {
                        "test_id": test_id, "score": 0, "total_questions": 0,
                        "score_percentage": 0, "test_completed": True,
                        "terminated": True, "terminated_by_warnings": True,
                        "termination_reason": reason, "warning_count": warnings,
                        "timestamp": time.time(),
                        "final_message": "Test terminated due to proctoring violations.",
                        "evaluation_report": f"Force complete error: {str(e)}",
                    }},
                    upsert=True
                )
                logger.info(f"💾 Emergency save for {test_id[:8]}")
            except Exception as save_err:
                logger.error(f"❌ Emergency save failed: {save_err}")
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

        # Build conversation_pairs — for coding questions, detect boilerplate/skipped
        # answers and store None so the frontend shows "Not answered" instead of
        # the editor's default template code.
        conversation_pairs = []
        for idx, ans in enumerate(answers):
            q      = questions[idx] if idx < len(questions) else {}
            q_type = q.get("question_type", "")
            raw_answer = ans.get("answer")

            if q_type == "coding" and raw_answer:
                if self._is_boilerplate_code(raw_answer, q):
                    logger.info(f"🚫 Q{idx+1}: boilerplate detected — storing as skipped")
                    raw_answer = None

            conversation_pairs.append({
                "question_number": idx + 1,
                "question_id":     q.get("question_id"),
                "question":        q.get("question"),
                "question_type":   q_type,
                "answer":          raw_answer,
                "correct":         bool(scores[idx]) if idx < len(scores) else False,
                "correct_answer":  q.get("correct_option_text") or q.get("correct_answer", "N/A"),
                "feedback":        feedbacks[idx] if idx < len(feedbacks) else "",
                "options":         q.get("options", []),
            })

        # ════════════════════════════════════════════════════════════
        # GROQ EXPLANATIONS — generate step-by-step for all wrong/skipped
        # questions (aptitude + MCQ only; coding has its own explanation system)
        # ════════════════════════════════════════════════════════════
        wrong_pairs = [
            p for p in conversation_pairs
            if not p["correct"] and p.get("question_type") != "coding"
        ]

        if wrong_pairs:
            logger.info(f"💡 Generating step-by-step Groq explanations for {len(wrong_pairs)} wrong/skipped questions...")
            try:
                explanation_map = await self._generate_explanations_batch(wrong_pairs)

                # Inject explanations back into conversation_pairs
                for pair in conversation_pairs:
                    q_num = pair["question_number"]
                    if q_num in explanation_map:
                        pair["feedback"] = explanation_map[q_num]

                # Also inject into section_details if present (normal test path)
                for sec_name, sec_data in section_details.items():
                    for q in sec_data.get("questions", []):
                        q_num = q.get("question_number")
                        if q_num in explanation_map:
                            q["explanation"] = explanation_map[q_num]

                logger.info(f"✅ Step-by-step explanations injected for {len(explanation_map)} questions")
            except Exception as exp_err:
                logger.error(f"❌ Explanation injection failed (non-fatal): {exp_err}")

        # ════════════════════════════════════════════════════════════
        # CODING CORRECT ANSWERS — generate solution code for wrong/skipped
        # coding questions so "Correct Answer" is never "N/A" in the UI/PDF
        # ════════════════════════════════════════════════════════════
        wrong_coding_pairs = [
            p for p in conversation_pairs
            if p.get("question_type") == "coding"
            and not p["correct"]
            and (not p.get("correct_answer") or str(p.get("correct_answer", "")).strip() in ("", "N/A", "None"))
        ]

        if wrong_coding_pairs:
            logger.info(f"💡 Generating correct solution code for {len(wrong_coding_pairs)} coding questions...")
            import asyncio as _asyncio
            loop = _asyncio.get_event_loop()
            for pair in wrong_coding_pairs:
                try:
                    question_text = pair.get("question", "")
                    result = await loop.run_in_executor(
                        None,
                        lambda qt=question_text: self.ai_service._generate_correct_code_sync(qt)
                    )
                    correct_code = result.get("code", "")
                    if correct_code and correct_code.strip() and correct_code != "# Unable to generate":
                        pair["correct_answer"] = correct_code
                        logger.info(f"  ✅ Correct code generated for coding Q{pair['question_number']}")
                    else:
                        pair["correct_answer"] = "# See the approach hint in the explanation above"
                except Exception as ce:
                    logger.warning(f"  ⚠️ Correct code gen failed for Q{pair['question_number']}: {ce}")
                    pair["correct_answer"] = "# See the approach hint in the explanation above"
        # ════════════════════════════════════════════════════════════
        # ════════════════════════════════════════════════════════════

        if pct >= 80:   final_msg = "Excellent performance!"
        elif pct >= 50: final_msg = "Good attempt, room for improvement."
        else:           final_msg = "Needs Improvement. Please practice more."

        wd              = self.db_manager.get_warnings(test_id)
        student_profile = test_data.get("student_profile", {})

        # ── Sanitize before writing — strip all known bad feedback strings ──
        clean_pairs = self._sanitize_result({
            "conversation_pairs": conversation_pairs,
            "section_details": section_details,
            "feedbacks": feedbacks,
        })
        conversation_pairs = clean_pairs["conversation_pairs"]
        section_details    = clean_pairs["section_details"]
        feedbacks          = clean_pairs["feedbacks"]
        # ────────────────────────────────────────────────────────────────────

        self.db_manager.test_results_collection.update_one(
            {"test_id": test_id},
            {"$set": {
                "test_id":   test_id,
                "user_type": test_data.get("user_type"),
                "student_id":   test_data.get("student_id"),
                "student_name": student_profile.get("student_name", ""),
                "email":        student_profile.get("email", ""),
                "course":       student_profile.get("course", ""),
                "batch":        student_profile.get("batch", ""),
                "role_type":    student_profile.get("role_type", ""),
                "experience":   student_profile.get("experience", ""),
                "org_id":       student_profile.get("org_id"),
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
        if not doc:
            return None

        # ── Heal missing/bad explanations on the fly ─────────────────────
        # Covers old terminated records that were saved before Groq fixes.
        conversation_pairs = doc.get("conversation_pairs", [])
        section_details    = doc.get("section_details", {})

        BAD = {"", "n/a", "na", "skipped", "not attempted",
               "no answer submitted", "no code submitted before termination",
               "review this concept"}

        def _is_bad(text) -> bool:
            if not text:
                return True
            t = str(text).strip().lower()
            if t in BAD:
                return True
            # Old hardcoded fallback pattern
            if t.startswith("review this concept") or t.startswith("the correct answer is"):
                return True
            return False

        # Collect wrong non-coding questions that need explanations
        needs_explanation = []
        for cp in conversation_pairs:
            if cp.get("question_type") == "coding":
                continue
            if not cp.get("correct") and _is_bad(cp.get("feedback")):
                needs_explanation.append({
                    "question_number": cp.get("question_number"),
                    "question":        cp.get("question", ""),
                    "answer":          cp.get("answer") or "No answer (skipped)",
                    "correct_answer":  cp.get("correct_answer", ""),
                    "options":         cp.get("options", []),
                })

        # Also from section_details
        for sec_name, sec_data in section_details.items():
            if sec_name == "coding":
                continue
            for q in sec_data.get("questions", []):
                if not q.get("is_correct") and _is_bad(q.get("explanation")):
                    needs_explanation.append({
                        "question_number": q.get("question_number"),
                        "question":        q.get("question", ""),
                        "answer":          q.get("user_answer") or "No answer (skipped)",
                        "correct_answer":  q.get("correct_answer", ""),
                        "options":         q.get("options", []),
                    })

        if needs_explanation:
            logger.info(f"🔧 Healing {len(needs_explanation)} missing explanations for {test_id[:8]}...")
            try:
                explanation_map = await self._generate_explanations_batch(needs_explanation)

                updated = False
                # Patch conversation_pairs
                for cp in conversation_pairs:
                    q_num = cp.get("question_number")
                    if q_num in explanation_map and _is_bad(cp.get("feedback")):
                        cp["feedback"] = explanation_map[q_num]
                        updated = True

                # Patch section_details
                for sec_name, sec_data in section_details.items():
                    for q in sec_data.get("questions", []):
                        q_num = q.get("question_number")
                        if q_num in explanation_map and _is_bad(q.get("explanation")):
                            q["explanation"] = explanation_map[q_num]
                            updated = True

                if updated:
                    # Persist healed data back to MongoDB + clear stale PDF
                    self.db_manager.test_results_collection.update_one(
                        {"test_id": test_id},
                        {"$set": {
                            "conversation_pairs": conversation_pairs,
                            "section_details":    section_details,
                        },
                        "$unset": {"pdf_path": "", "pdf_url": ""}}
                    )
                    logger.info(f"✅ Healed + saved explanations for {test_id[:8]}")
            except Exception as heal_err:
                logger.warning(f"⚠️ Explanation healing failed (non-fatal): {heal_err}")
        # ─────────────────────────────────────────────────────────────────

        return {
            "test_id":                doc.get("test_id"),
            "student_id":             doc.get("student_id"),
            "student_name":           doc.get("student_name", ""),
            "email":                  doc.get("email", ""),
            "course":                 doc.get("course", ""),
            "batch":                  doc.get("batch", ""),
            "role_type":              doc.get("role_type", ""),
            "user_type":              doc.get("user_type", "dev"),
            "score":                  doc.get("score", 0),
            "total_questions":        doc.get("total_questions", 0),
            "score_percentage":       doc.get("score_percentage", 0),
            "analytics":              doc.get("evaluation_report", ""),
            "evaluation_report":      doc.get("evaluation_report", ""),
            "section_scores":         doc.get("section_scores", {}),
            "section_details":        section_details,
            "conversation_pairs":     conversation_pairs,
            "timestamp":              doc.get("timestamp", 0),
            "completed_at":           doc.get("timestamp", 0),
            "warning_count":          doc.get("warning_count", 0),
            "warnings":               doc.get("warnings", []),
            "terminated_by_warnings": doc.get("terminated_by_warnings", False),
            "termination_reason":     doc.get("termination_reason"),
            "terminated":             doc.get("terminated", False),
            "final_message":          doc.get("final_message", ""),
            "pdf_path":               doc.get("pdf_path", ""),
        }

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
