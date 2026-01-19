# weekend_mocktest/core/database.py
# PRODUCTION READY – FULL VERSION WITH WARNINGS

import logging
import pymongo
import random
import hashlib
import uuid
from datetime import datetime
from typing import List, Dict, Any
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
    # Warning types:
    # - multiple_faces: Multiple faces detected in camera
    # - object_detected: Objects/phone detected
    # - tab_switch: Tab/window switching
    # - face_turning: Face turned away from screen  
    # - face_not_visible: Face not detected
    # - screenshot: Screenshot attempt
    # ==========================================================
    
    VALID_WARNING_TYPES = [
        "multiple_faces",    # Multiple faces detected
        "object_detected",   # Objects like phone, book detected
        "tab_switch",        # Tab or window switching
        "face_turning",      # Face turned away
        "face_not_visible",  # Face not detected in camera
        "screenshot"         # Screenshot attempt
    ]
    
    MAX_WARNINGS = 3

    def add_warning(self, test_id: str, student_id: int, warning_type: str, 
                    details: Dict = None) -> Dict[str, Any]:
        """
        Add a proctoring warning.
        After 3 warnings, test is terminated.
        """
        import time
        
        if warning_type not in self.VALID_WARNING_TYPES:
            warning_type = "unknown"
        
        timestamp = time.time()
        
        warning_event = {
            "type": warning_type,
            "timestamp": timestamp,
            "timestamp_readable": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
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
        
        # User friendly messages
        messages = {
            "multiple_faces": "Multiple faces detected. Only the test taker should be visible.",
            "object_detected": "Suspicious object detected (phone/book). Please remove it.",
            "tab_switch": "Tab switching detected. Stay on the test window.",
            "face_turning": "Please face the screen directly.",
            "face_not_visible": "Your face is not visible. Adjust your camera.",
            "screenshot": "Screenshot attempt detected. This is not allowed."
        }
        
        message = messages.get(warning_type, "Warning recorded.")
        if new_count < self.MAX_WARNINGS:
            message += f" Warning {new_count}/{self.MAX_WARNINGS}. {self.MAX_WARNINGS - new_count} remaining."
        else:
            message += " Maximum warnings reached. Test terminated."
        
        logger.warning(f"⚠️ Warning #{new_count} for test {test_id}: {warning_type}")
        
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
        
        warning_summary = [f"{w['type']} at {w['timestamp_readable']}" for w in warnings_list]
        termination_reason = f"Test terminated after {self.MAX_WARNINGS} warnings: " + "; ".join(warning_summary)
        
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
        
        logger.error(f"🚫 Test {test_id} TERMINATED: {termination_reason}")

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
    def get_weekly_summaries(self, user_type: str):
        """
        Get summaries from MongoDB.
        
        ROUTING:
        - dev → Developer collection (Python/Coding content)
        - non_dev → Non-Developer collection (SAP/Business content)
        """
        if user_type == "dev":
            collection = self.developer_collection
            collection_name = "Developer"
            logger.info(f"📂 DB Query: {collection_name} collection (Python/Coding)")
        else:
            collection = self.non_developer_collection
            collection_name = "Non-Developer"
            logger.info(f"📂 DB Query: {collection_name} collection (SAP/Business)")
        
        # Query for documents with valid summary field
        result = list(
            collection.find(
                {"summary": {"$exists": True, "$ne": "", "$type": "string"}},
                {"summary": 1}
            ).limit(50)
        )
        
        logger.info(f"📂 DB Result: Found {len(result)} documents with 'summary' field in {collection_name}")
        
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
        """Get questions student has NOT seen yet"""
        seen_ids = self.get_seen_question_ids(student_id)
        
        cursor = self.question_bank_collection.find(
            {
                "user_type": user_type,
                "question_type": question_type,
                "active": True,
                "question_id": {"$nin": seen_ids}
            }
        ).sort("usage_count", 1).limit(count)  # Prefer less-used questions
        
        return list(cursor)

    def increment_question_usage(self, question_ids: List[str]):
        """Increment usage count for questions"""
        self.question_bank_collection.update_many(
            {"question_id": {"$in": question_ids}},
            {"$inc": {"usage_count": 1}}
        )

    # ==========================================================
    # WARNINGS (3 warnings = termination)
    # ==========================================================
    def add_warning(self, test_id: str, student_id: int, warning_type: str, 
                    details: Dict = None) -> Dict[str, Any]:
        """
        Add a proctoring warning.
        
        Warning types:
        - multiple_faces: Multiple faces detected
        - object_detected: Suspicious object detected
        - tab_switch: Tab/window switching
        - face_turning: Face turned away
        - face_not_visible: Face not detected
        - screenshot: Screenshot attempt detected
        """
        import time
        
        timestamp = time.time()
        
        warning_event = {
            "type": warning_type,
            "timestamp": timestamp,
            "timestamp_readable": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            "details": details or {}
        }
        
        # Find existing or create new
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
                "warnings": [warning_event],
                "first_warning_at": timestamp,
                "last_warning_at": timestamp,
                "last_warning_type": warning_type,
                "terminated": False,
                "termination_reason": None,
                "created_at": timestamp
            })
        
        # Check if should terminate (3 warnings)
        should_terminate = new_count >= 3
        
        if should_terminate:
            self._mark_test_terminated(test_id)
        
        logger.warning(f"⚠️ Warning #{new_count} for test {test_id}: {warning_type}")
        
        return {
            "warning_count": new_count,
            "max_warnings": 3,
            "warnings_remaining": max(0, 3 - new_count),
            "should_terminate": should_terminate,
            "warning_type": warning_type
        }

    def _mark_test_terminated(self, test_id: str):
        """Mark test as terminated due to warnings"""
        doc = self.warnings_collection.find_one({"test_id": test_id})
        warnings_list = doc.get("warnings", []) if doc else []
        
        # Build termination reason
        warning_summary = [f"{w['type']} at {w['timestamp_readable']}" for w in warnings_list]
        termination_reason = f"Session terminated after 3 warnings: " + "; ".join(warning_summary)
        
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
        
        logger.error(f"🚫 Test {test_id} TERMINATED: {termination_reason}")

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
        """Check if test is terminated due to warnings"""
        doc = self.warnings_collection.find_one({"test_id": test_id}, {"terminated": 1})
        return doc.get("terminated", False) if doc else False

    def get_termination_reason(self, test_id: str) -> str:
        """Get termination reason"""
        doc = self.warnings_collection.find_one({"test_id": test_id}, {"termination_reason": 1})
        return doc.get("termination_reason", "") if doc else ""

    # ==========================================================
    # TEST RESULTS (EVALUATION + PDF)
    # ==========================================================
    def save_test_results(
        self,
        test_id: str,
        test_data: Dict[str, Any],
        evaluation_result: Dict[str, Any]
    ):
        """Save test results with warning info"""
        
        # Get warnings info
        warnings_data = self.get_warnings(test_id)

        doc = {
            "test_id": test_id,
            "user_type": test_data.get("user_type"),
            "student_id": test_data.get("student_id"),
            "total_questions": test_data.get("total_questions"),

            # Scores
            "score": evaluation_result.get("total_correct", 0),
            "score_percentage": round(
                (evaluation_result.get("total_correct", 0) /
                 max(test_data.get("total_questions", 1), 1)) * 100, 1
            ),

            # Evaluation details
            "scores": evaluation_result.get("scores", []),
            "feedbacks": evaluation_result.get("feedbacks", []),
            "section_scores": evaluation_result.get("section_scores", {}),
            "evaluation_report": evaluation_result.get("evaluation_report", ""),

            "answers": test_data.get("answers", []),
            "created_at": datetime.utcnow().timestamp(),
            
            # WARNING INFO (audit trail)
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
    def _get_student_info(self):
        return {"student_id": random.randint(1000, 9999)}


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