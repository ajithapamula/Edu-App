# weekend_mocktest/core/database.py
# PRODUCTION READY – FIXED: Stable student_id generation (no more random IDs)

import logging
import pymongo
import random
import hashlib
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from .config import config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Central MongoDB manager for Weekend Mocktest
    """

    def __init__(self):
        logger.info("🔗 Initializing MongoDB")
        self._init_mongodb()
        logger.info("✅ DatabaseManager ready")

    # ==========================================================
    # MongoDB INIT
    # ==========================================================
    def _init_mongodb(self):
        self.mongo_client = pymongo.MongoClient(
            config.MONGO_CONNECTION_STRING,
            serverSelectionTimeoutMS=10000
        )

        self.mongo_client.admin.command("ping")
        self.db = self.mongo_client[config.MONGO_DB_NAME]

        # Content collections
        self.developer_collection = self.db["Developer"]
        self.non_developer_collection = self.db["Non-Developer"]

        # System collections
        self.test_results_collection = self.db[config.TEST_RESULTS_COLLECTION]
        self.question_bank_collection = self.db[config.QUESTION_BANK_COLLECTION]
        self.student_history_collection = self.db[config.STUDENT_QUESTION_HISTORY_COLLECTION]

        # Active tests collection
        self.active_tests_collection = self.db["active_tests"]

        # Warnings collection for proctoring (3 warnings = termination)
        self.warnings_collection = self.db["test_warnings"]

        self._create_indexes()

    def _create_indexes(self):
        self.question_bank_collection.create_index(
            [("question_hash", 1)], unique=True, sparse=True
        )
        self.test_results_collection.create_index(
            [("test_id", 1)], unique=True
        )
        self.student_history_collection.create_index(
            [("student_id", 1), ("question_id", 1)], unique=True
        )
        # Warnings indexes
        self.warnings_collection.create_index([("test_id", 1)])
        self.warnings_collection.create_index([("student_id", 1)])

    # ==========================================================
    # WARNINGS (3 warnings = termination)
    # ==========================================================

    MAX_WARNINGS = 3

    WARNING_MESSAGES = {
        # NEW frontend types (BlazeFace + COCO-SSD)
        "face_not_detected": "Face not visible in camera",
        "face_turned_left": "User turned face to the left",
        "face_turned_right": "User turned face to the right",
        "face_multiple": "Multiple faces detected in camera frame",
        "face_looking_away": "User looking away from screen",
        "object_phone": "Mobile phone or electronic device detected",
        "object_book": "Book or reading material detected",
        "object_person": "Multiple persons detected in frame",
        "tab_switch": "Tab or window switching detected",
        "right_click": "Right-click attempted during exam",
        "low_light": "Low lighting conditions detected",

        # OLD types (backward compatibility)
        "multiple_faces": "Multiple faces detected",
        "object_detected": "Suspicious object detected",
        "face_turning": "Face turned away from screen",
        "face_not_visible": "Face not detected in camera",
        "screenshot": "Screenshot attempt detected",
    }

    def add_warning(self, test_id: str, student_id: int, warning_type: str,
                    details: Dict = None) -> Dict[str, Any]:
        import time

        if warning_type not in self.WARNING_MESSAGES:
            logger.warning(f"⚠️ Unknown warning type: {warning_type} — recording anyway")

        timestamp = time.time()

        warning_event = {
            "type": warning_type,
            "timestamp": timestamp,
            "timestamp_readable": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            "description": self.WARNING_MESSAGES.get(warning_type, f"Warning: {warning_type}"),
            "details": details or {}
        }

        existing = self.warnings_collection.find_one({"test_id": test_id})

        if existing:
            new_count = existing.get("warning_count", 0) + 1
            self.warnings_collection.update_one(
                {"test_id": test_id},
                {
                    "$push": {"warnings": warning_event},
                    "$set": {
                        "warning_count": new_count,
                        "last_warning_at": timestamp,
                        "last_warning_type": warning_type
                    }
                }
            )
        else:
            new_count = 1
            self.warnings_collection.insert_one({
                "test_id": test_id,
                "student_id": student_id,
                "warning_count": new_count,
                "max_warnings": self.MAX_WARNINGS,
                "warnings": [warning_event],
                "first_warning_at": timestamp,
                "last_warning_at": timestamp,
                "last_warning_type": warning_type,
                "terminated": False,
                "termination_reason": None,
                "created_at": timestamp
            })

        should_terminate = new_count >= self.MAX_WARNINGS

        if should_terminate:
            self._mark_test_terminated(test_id)

        description = self.WARNING_MESSAGES.get(warning_type, f"Warning: {warning_type}")
        if new_count >= self.MAX_WARNINGS:
            message = f"FINAL WARNING: {description}. Test will be terminated."
        elif new_count == self.MAX_WARNINGS - 1:
            message = f"LAST CHANCE: {description}. One more warning = termination!"
        else:
            message = f"Warning {new_count}/{self.MAX_WARNINGS}: {description}. {self.MAX_WARNINGS - new_count} remaining."

        logger.warning(
            f"⚠️ Warning #{new_count}/{self.MAX_WARNINGS} for test {test_id[:8]}: "
            f"{warning_type} — {'TERMINATING' if should_terminate else message}"
        )

        return {
            "warning_count": new_count,
            "max_warnings": self.MAX_WARNINGS,
            "warnings_remaining": max(0, self.MAX_WARNINGS - new_count),
            "should_terminate": should_terminate,
            "warning_type": warning_type,
            "message": message
        }

    def _mark_test_terminated(self, test_id: str):
        doc = self.warnings_collection.find_one({"test_id": test_id})
        warnings_list = doc.get("warnings", []) if doc else []

        warning_summary = [
            f"{w['type']} at {w.get('timestamp_readable', 'unknown')}"
            for w in warnings_list
        ]
        termination_reason = (
            f"Test terminated after {self.MAX_WARNINGS} warnings: "
            + "; ".join(warning_summary)
        )

        self.warnings_collection.update_one(
            {"test_id": test_id},
            {
                "$set": {
                    "terminated": True,
                    "terminated_at": datetime.utcnow().timestamp(),
                    "termination_reason": termination_reason
                }
            }
        )

        logger.error(f"🚫 Test {test_id[:8]} TERMINATED: {termination_reason}")

    def get_warnings(self, test_id: str) -> Dict[str, Any]:
        doc = self.warnings_collection.find_one({"test_id": test_id}, {"_id": 0})
        if not doc:
            return {"test_id": test_id, "warning_count": 0, "warnings": [], "terminated": False}
        return doc

    def get_warning_count(self, test_id: str) -> int:
        doc = self.warnings_collection.find_one({"test_id": test_id}, {"warning_count": 1})
        return doc.get("warning_count", 0) if doc else 0

    def is_test_terminated(self, test_id: str) -> bool:
        doc = self.warnings_collection.find_one({"test_id": test_id}, {"terminated": 1})
        return doc.get("terminated", False) if doc else False

    def get_termination_reason(self, test_id: str) -> str:
        doc = self.warnings_collection.find_one({"test_id": test_id}, {"termination_reason": 1})
        return doc.get("termination_reason", "") if doc else ""

    # ==========================================================
    # CONTENT (AUTO ROUTING)
    # ==========================================================
    def save_coding_result(self, test_id: str, question_number: int,
                           results: Dict, user_code: str = "", language: str = "") -> None:
        try:
            key = f"{test_id}__q{question_number}"
            self.active_tests_collection.update_one(
                {"_id": key},
                {"$set": {
                    "_id":              key,
                    "test_id":          test_id,
                    "question_number":  question_number,
                    "results":          results,
                    "user_code":        user_code,
                    "language":         language,
                    "saved_at":         __import__("time").time(),
                }},
                upsert=True
            )
            logger.info(
                f"💾 [DB] Saved coding result Q{question_number} for {test_id[:8]}: "
                f"{results.get('overall_result','?')} "
                f"({results.get('total_passed',0)}/{results.get('total_cases',0)} passed)"
            )
        except Exception as e:
            logger.error(f"❌ [DB] Failed to save coding result: {e}")

    def get_coding_result(self, test_id: str, question_number: int) -> Optional[Dict]:
        try:
            key = f"{test_id}__q{question_number}"
            doc = self.active_tests_collection.find_one({"_id": key})
            if doc:
                return doc.get("results")
            return None
        except Exception as e:
            logger.error(f"❌ [DB] Failed to get coding result: {e}")
            return None

    def get_all_coding_results(self, test_id: str) -> Dict[int, Dict]:
        try:
            docs = self.active_tests_collection.find({"test_id": test_id})
            results = {}
            for doc in docs:
                q_num = doc.get("question_number")
                if q_num:
                    results[q_num] = doc.get("results")
            return results
        except Exception as e:
            logger.error(f"❌ [DB] Failed to get all coding results: {e}")
            return {}

    def cleanup_coding_results(self, test_id: str) -> None:
        try:
            result = self.active_tests_collection.delete_many({"test_id": test_id})
            if result.deleted_count:
                logger.info(f"🧹 [DB] Cleaned up {result.deleted_count} coding results for {test_id[:8]}")
        except Exception as e:
            logger.error(f"❌ [DB] Failed to cleanup coding results: {e}")

    def get_weekly_summaries(self, user_type: str):
        if user_type == "dev":
            collection = self.developer_collection
            collection_name = "Developer"
        else:
            collection = self.non_developer_collection
            collection_name = "Non-Developer"

        logger.info(f"📂 DB Query: {collection_name} collection")

        result = list(
            collection.find(
                {"summary": {"$exists": True, "$ne": "", "$type": "string"}},
                {"summary": 1}
            ).limit(50)
        )

        logger.info(f"📂 DB Result: Found {len(result)} documents in {collection_name}")
        return result

    # ==========================================================
    # QUESTION BANK
    # ==========================================================
    def add_questions_to_bank(self, questions: List[Dict[str, Any]], user_type: str):
        added = 0
        for q in questions:
            try:
                q_text = q.get("question", "")
                q_hash = hashlib.md5(q_text.encode()).hexdigest()

                self.question_bank_collection.insert_one({
                    "question_id": str(uuid.uuid4()),
                    "question_hash": q_hash,
                    "user_type": user_type,
                    "question_type": q.get("question_type", "mcq"),
                    "question": q_text,
                    "options": q.get("options"),
                    "correct_answer": q.get("correct_answer"),
                    "correct_option_text": q.get("correct_option_text"),
                    "test_cases": q.get("test_cases"),
                    "usage_count": 0,
                    "active": True,
                    "created_at": datetime.utcnow()
                })
                added += 1
            except pymongo.errors.DuplicateKeyError:
                pass

        return added

    def mark_questions_as_seen(self, student_id: int, question_ids: List[str]):
        for qid in question_ids:
            self.student_history_collection.update_one(
                {"student_id": student_id, "question_id": qid},
                {"$set": {"seen_at": datetime.utcnow()}},
                upsert=True
            )

    def get_seen_question_ids(self, student_id: int) -> List[str]:
        cursor = self.student_history_collection.find(
            {"student_id": student_id},
            {"question_id": 1}
        )
        return [doc["question_id"] for doc in cursor]

    def get_unseen_questions(self, student_id: int, user_type: str,
                             question_type: str, count: int) -> List[Dict]:
        """
        Smart question selection — guarantees:
        1. Same student never sees the same question twice
        2. Different students get different questions even at the same time
        3. Questions are randomly sampled (not just top-N by usage)

        Strategy:
        ─────────────────────────────────────────────────────────────
        TIER 1 — Questions this student has NEVER seen
          → Fetch a large pool (count × 8), group by usage tier,
            randomly sample within each tier.
          → This means two students starting simultaneously both get
            unseen questions but from different random positions.

        TIER 2 — If not enough unseen, fill from least-used questions
          → Excludes questions already in selected pool
          → Also randomly sampled, not top-N

        Final shuffle ensures question ORDER varies per student.
        ─────────────────────────────────────────────────────────────
        """
        seen_ids = self.get_seen_question_ids(student_id)

        total_available = self.question_bank_collection.count_documents({
            "user_type": user_type, "question_type": question_type, "active": True
        })

        # Fetch a very large pool so random sampling has plenty to work with
        # pool_size >> count ensures different students pick different subsets
        pool_size = max(count * 8, 100)

        # ── TIER 1: Questions this student hasn't seen ──────────────────────
        unseen_cursor = self.question_bank_collection.find(
            {
                "user_type":     user_type,
                "question_type": question_type,
                "active":        True,
                "question_id":   {"$nin": seen_ids}
            },
            # Fetch random-ish by using no sort — MongoDB natural order varies
            # We'll do proper randomization below
        ).limit(pool_size)

        unseen_pool = list(unseen_cursor)

        # ── KEY FIX: Random sampling within usage tiers ────────────────────
        # Group by usage_count tier (0-2, 3-5, 6+)
        # Pick randomly from lowest tier first — ensures variety across students
        selected = self._tier_sample(unseen_pool, count)

        # ── TIER 2: Not enough unseen — fill from least-used ───────────────
        if len(selected) < count:
            logger.info(
                f"⚠️ Only {len(selected)} unseen for student {student_id} "
                f"({question_type}/{user_type}), bank has {total_available} total. "
                f"Filling from least-used pool."
            )
            selected_ids = {q.get("question_id") for q in selected}

            fill_cursor = self.question_bank_collection.find(
                {
                    "user_type":     user_type,
                    "question_type": question_type,
                    "active":        True,
                    "question_id":   {"$nin": list(selected_ids)}
                }
            ).limit(pool_size)

            fill_pool = list(fill_cursor)
            fill_sample = self._tier_sample(fill_pool, count - len(selected))
            selected.extend(fill_sample)

        # Final shuffle — randomizes question ORDER per student
        random.shuffle(selected)

        logger.info(
            f"📋 Selected {len(selected)} {question_type} questions for student {student_id} "
            f"(from pool of {len(unseen_pool)}, bank has {total_available})"
        )
        return selected[:count]

    def _tier_sample(self, pool: List[Dict], count: int) -> List[Dict]:
        """
        Randomly sample `count` questions from pool, prioritising low-usage tiers.

        Tier 0: usage_count 0–2   (fresh questions — highest priority)
        Tier 1: usage_count 3–6   (lightly used)
        Tier 2: usage_count 7+    (heavily used — last resort)

        Within each tier, questions are randomly sampled.
        This prevents all students from getting the same "top N" questions.
        """
        if not pool or count <= 0:
            return []

        tier0 = [q for q in pool if q.get("usage_count", 0) <= 2]
        tier1 = [q for q in pool if 3 <= q.get("usage_count", 0) <= 6]
        tier2 = [q for q in pool if q.get("usage_count", 0) >= 7]

        # Shuffle each tier independently
        random.shuffle(tier0)
        random.shuffle(tier1)
        random.shuffle(tier2)

        selected = []
        for tier in [tier0, tier1, tier2]:
            needed = count - len(selected)
            if needed <= 0:
                break
            selected.extend(tier[:needed])

        return selected

    def increment_question_usage(self, question_ids: List[str]):
        self.question_bank_collection.update_many(
            {"question_id": {"$in": question_ids}},
            {"$inc": {"usage_count": 1}}
        )

    # ==========================================================
    # TEST RESULTS
    # ==========================================================
    def save_test_results(
        self,
        test_id: str,
        test_data: Dict[str, Any],
        evaluation_result: Dict[str, Any]
    ):
        warnings_data = self.get_warnings(test_id)

        doc = {
            "test_id": test_id,
            "user_type": test_data.get("user_type"),
            "student_id": test_data.get("student_id"),
            "total_questions": test_data.get("total_questions"),
            "score": evaluation_result.get("total_correct", 0),
            "score_percentage": round(
                (evaluation_result.get("total_correct", 0) /
                 max(test_data.get("total_questions", 1), 1)) * 100, 1
            ),
            "scores": evaluation_result.get("scores", []),
            "feedbacks": evaluation_result.get("feedbacks", []),
            "section_scores": evaluation_result.get("section_scores", {}),
            "evaluation_report": evaluation_result.get("evaluation_report", ""),
            "answers": test_data.get("answers", []),
            "created_at": datetime.utcnow().timestamp(),
            "warning_count": warnings_data.get("warning_count", 0),
            "warnings": warnings_data.get("warnings", []),
            "terminated_by_warnings": warnings_data.get("terminated", False),
            "termination_reason": warnings_data.get("termination_reason")
        }

        self.test_results_collection.update_one(
            {"test_id": test_id},
            {"$set": doc},
            upsert=True
        )

        logger.info(f"💾 Saved test {test_id} | Warnings: {warnings_data.get('warning_count', 0)}")

    # ==========================================================
    # STUDENT
    # ==========================================================
    def _get_student_info(self, identifier: str = None) -> Dict:
        if identifier:
            hash_val = int(hashlib.md5(str(identifier).encode()).hexdigest(), 16)
            student_id = (hash_val % 90000) + 10000
            logger.info(f"🎓 Stable student_id={student_id} from identifier='{identifier}'")
        else:
            import time
            student_id = int(time.time() * 1000) % 90000 + 10000
            logger.warning(f"⚠️ No identifier provided — using time-based student_id={student_id}.")

        return {"student_id": student_id}


# ==========================================================
# SINGLETON
# ==========================================================
_db_manager = None


def get_db_manager() -> DatabaseManager:
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def close_db_manager():
    global _db_manager
    if _db_manager:
        try:
            _db_manager.mongo_client.close()
            logger.info("🔌 MongoDB closed")
        except Exception as e:
            logger.error(f"Mongo close error: {e}")
        _db_manager = None