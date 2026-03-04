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
        """
        Add a proctoring warning.
        After 3 warnings, test is terminated.
        """
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
        """Mark test as terminated due to warnings"""
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
        """Get all warnings for a test"""
        doc = self.warnings_collection.find_one({"test_id": test_id}, {"_id": 0})
        if not doc:
            return {"test_id": test_id, "warning_count": 0, "warnings": [], "terminated": False}
        return doc

    def get_warning_count(self, test_id: str) -> int:
        """Get current warning count"""
        doc = self.warnings_collection.find_one({"test_id": test_id}, {"warning_count": 1})
        return doc.get("warning_count", 0) if doc else 0

    def is_test_terminated(self, test_id: str) -> bool:
        """Check if test is terminated"""
        doc = self.warnings_collection.find_one({"test_id": test_id}, {"terminated": 1})
        return doc.get("terminated", False) if doc else False

    def get_termination_reason(self, test_id: str) -> str:
        """Get termination reason"""
        doc = self.warnings_collection.find_one({"test_id": test_id}, {"termination_reason": 1})
        return doc.get("termination_reason", "") if doc else ""

    # ==========================================================
    # CONTENT (AUTO ROUTING)
    # ==========================================================
    # ═══════════════════════════════════════════════════════════
    # CODING TEST RESULTS — persisted to MongoDB
    # So results survive server restarts and are always available
    # at evaluation time regardless of whether student ran tests.
    # ═══════════════════════════════════════════════════════════

    def save_coding_result(self, test_id: str, question_number: int, 
                           results: Dict, user_code: str = "", language: str = "") -> None:
        """
        Persist coding test results to MongoDB when student runs tests.
        Called by /api/code/submit — survives server restarts.
        """
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
        """
        Retrieve stored coding test results from MongoDB.
        Returns None if not found (student didn't run tests).
        """
        try:
            key = f"{test_id}__q{question_number}"
            doc = self.active_tests_collection.find_one({"_id": key})
            if doc:
                logger.debug(f"📖 [DB] Found coding result Q{question_number} for {test_id[:8]}")
                return doc.get("results")
            return None
        except Exception as e:
            logger.error(f"❌ [DB] Failed to get coding result: {e}")
            return None

    def get_all_coding_results(self, test_id: str) -> Dict[int, Dict]:
        """
        Get all stored coding results for a test, keyed by question_number.
        Used at evaluation time to gather all pre-run results at once.
        """
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
        """Delete stored coding results after test is fully evaluated."""
        try:
            result = self.active_tests_collection.delete_many({"test_id": test_id})
            if result.deleted_count:
                logger.info(f"🧹 [DB] Cleaned up {result.deleted_count} coding results for {test_id[:8]}")
        except Exception as e:
            logger.error(f"❌ [DB] Failed to cleanup coding results: {e}")

    def get_weekly_summaries(self, user_type: str):
        """
        Get summaries from MongoDB.
        dev → Developer collection
        non_dev → Non-Developer collection
        """
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
        """Get question IDs this student has already seen"""
        cursor = self.student_history_collection.find(
            {"student_id": student_id},
            {"question_id": 1}
        )
        return [doc["question_id"] for doc in cursor]

    def get_unseen_questions(self, student_id: int, user_type: str,
                             question_type: str, count: int) -> List[Dict]:
        """
        Smart question rotation to minimise repetition.

        Strategy:
        1. Priority 1 — questions this student has NEVER seen (seen_ids excluded)
        2. Priority 2 — if not enough unseen, fill from LEAST-used questions
           (usage_count ascending), excluding those used in last test
        3. Always shuffle the final pool so order varies

        Why this works:
        - Student-level tracking prevents same student seeing same question twice
        - usage_count rotation ensures DIFFERENT students get different questions
        - Large shuffle pool (count * 5) means each test gets a unique subset
        """
        seen_ids  = self.get_seen_question_ids(student_id)
        # How many total questions are in the bank for this section?
        total_available = self.question_bank_collection.count_documents({
            "user_type": user_type, "question_type": question_type, "active": True
        })

        # Use a large pool — at least 5x requested count or 50, whichever bigger
        # This gives shuffle enough room so different tests don't get same subset
        pool_size = max(count * 5, 50)

        # Priority 1: questions this student hasn't seen
        unseen_cursor = self.question_bank_collection.find(
            {
                "user_type":     user_type,
                "question_type": question_type,
                "active":        True,
                "question_id":   {"$nin": seen_ids}
            }
        ).sort("usage_count", 1).limit(pool_size)

        pool = list(unseen_cursor)

        # Priority 2: bank too small or student has seen everything
        # Fill remaining slots from least-used questions (different usage tier)
        if len(pool) < count:
            logger.info(
                f"⚠️ Only {len(pool)} unseen questions for student {student_id} "
                f"({question_type}/{user_type}), bank has {total_available} total. "
                f"Filling from least-used pool."
            )
            # Get least-used questions (student may have seen them, but long ago)
            # Exclude questions already in pool to avoid duplicates
            pool_ids    = {q.get("question_id") for q in pool}
            fill_cursor = self.question_bank_collection.find(
                {
                    "user_type":     user_type,
                    "question_type": question_type,
                    "active":        True,
                    "question_id":   {"$nin": list(pool_ids)}
                }
            ).sort("usage_count", 1).limit(pool_size - len(pool))
            pool.extend(list(fill_cursor))

        # Always shuffle — this is what prevents same-order repetition
        random.shuffle(pool)
        return pool[:count]

    def increment_question_usage(self, question_ids: List[str]):
        """Increment usage count for questions"""
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
        """Save test results with warning info"""
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
    # STUDENT — FIX: Stable ID from identifier, not random
    # ==========================================================
    def _get_student_info(self, identifier: str = None) -> Dict:
        """
        Generate a STABLE student_id.

        - If identifier is given (e.g. from localStorage): hash it → consistent 5-digit ID
        - If no identifier: use time-based ID (consistent within session via test_service)

        This fixes the question repetition bug where random IDs broke seen-question tracking.
        """
        if identifier:
            hash_val = int(hashlib.md5(str(identifier).encode()).hexdigest(), 16)
            student_id = (hash_val % 90000) + 10000  # Always 5-digit, always same for same input
            logger.info(f"🎓 Stable student_id={student_id} from identifier='{identifier}'")
        else:
            import time
            # Time-based: not truly stable across restarts, but test_service
            # should pass student_id from frontend to avoid hitting this path
            student_id = int(time.time() * 1000) % 90000 + 10000
            logger.warning(f"⚠️ No identifier provided — using time-based student_id={student_id}. "
                           f"Pass student_id from frontend localStorage for true persistence.")

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