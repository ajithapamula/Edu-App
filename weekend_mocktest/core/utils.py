# weekend_mocktest/core/utils.py
# ═══════════════════════════════════════════════════════════════════
# UPDATED: MongoDB-backed MemoryManager
#
# WHY: In-memory storage loses active tests on server restart.
#      Students get "Test not found" errors mid-test.
#
# HOW: Active tests stored in MongoDB collection 'active_tests'.
#      In-memory cache for fast access, MongoDB as fallback.
#      On restart, tests are recovered from MongoDB automatically.
#      After completion, cleared from both cache and MongoDB
#      (results are already saved separately).
# ═══════════════════════════════════════════════════════════════════

import uuid
import time
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ValidationUtils:
    """Validation utilities"""
    
    @staticmethod
    def validate_user_type(user_type: str) -> bool:
        return user_type in ["dev", "non_dev", "developer", "non-developer"]


class DateTimeUtils:
    """DateTime utilities"""
    
    @staticmethod
    def get_current_timestamp() -> float:
        return time.time()


class MemoryManager:
    """
    MongoDB-backed test session manager.
    
    - In-memory dict for fast reads (cache)
    - MongoDB 'active_tests' collection as persistent store
    - On cache miss → check MongoDB (handles server restarts)
    - On test complete → clear from both (results saved separately)
    """

    def __init__(self):
        self.tests: Dict[str, Dict[str, Any]] = {}
        self.answers: Dict[str, List[Dict[str, Any]]] = {}
        self._db = None  # Lazy init to avoid circular imports
        self._collection = None
        logger.info("📦 MemoryManager initialized (MongoDB-backed)")

    def _get_collection(self):
        """Lazy-load MongoDB collection to avoid circular imports"""
        if self._collection is None:
            try:
                from .database import get_db_manager
                db_manager = get_db_manager()
                self._db = db_manager.db
                self._collection = self._db["active_tests"]
                # Index for fast lookups and auto-expiry
                self._collection.create_index("test_id", unique=True)
                self._collection.create_index("expires_at", expireAfterSeconds=0)
                logger.info("✅ MemoryManager connected to MongoDB 'active_tests' collection")
            except Exception as e:
                logger.warning(f"⚠️ MongoDB not available for MemoryManager: {e}")
                logger.warning("   Falling back to in-memory only mode")
                self._collection = None
        return self._collection

    def _save_to_db(self, test_id: str):
        """Save test state to MongoDB"""
        col = self._get_collection()
        if col is None:
            return
        
        try:
            test_data = self.tests.get(test_id)
            answers_data = self.answers.get(test_id, [])
            
            if not test_data:
                return
            
            from datetime import datetime, timezone
            expires_at = datetime.fromtimestamp(
                test_data.get("expires_at", time.time() + 7200),
                tz=timezone.utc
            )
            
            doc = {
                "test_id": test_id,
                "test_data": test_data,
                "answers": answers_data,
                "expires_at": expires_at,
                "updated_at": time.time(),
            }
            
            col.update_one(
                {"test_id": test_id},
                {"$set": doc},
                upsert=True
            )
        except Exception as e:
            logger.warning(f"⚠️ Failed to save test {test_id} to MongoDB: {e}")

    def _load_from_db(self, test_id: str) -> bool:
        """Load test from MongoDB into cache. Returns True if found."""
        col = self._get_collection()
        if col is None:
            return False
        
        try:
            doc = col.find_one({"test_id": test_id})
            if doc:
                self.tests[test_id] = doc["test_data"]
                self.answers[test_id] = doc.get("answers", [])
                logger.info(f"🔄 Recovered test {test_id[:8]}... from MongoDB")
                return True
        except Exception as e:
            logger.warning(f"⚠️ Failed to load test {test_id} from MongoDB: {e}")
        
        return False

    def _delete_from_db(self, test_id: str):
        """Remove test from MongoDB"""
        col = self._get_collection()
        if col is None:
            return
        
        try:
            col.delete_one({"test_id": test_id})
        except Exception as e:
            logger.warning(f"⚠️ Failed to delete test {test_id} from MongoDB: {e}")

    # ════════════════════════════════════════════════════════════
    # PUBLIC API (same interface as before)
    # ════════════════════════════════════════════════════════════

    def create_test(self, user_type: str, questions: List[Dict], student_id: int = None) -> str:
        """Create a new test session — saved to both cache and MongoDB"""
        test_id = str(uuid.uuid4())
        
        self.tests[test_id] = {
            "test_id": test_id,
            "user_type": user_type,
            "student_id": student_id,
            "questions": questions,
            "total_questions": len(questions),
            "current_question": 1,
            "created_at": time.time(),
            "expires_at": time.time() + 7200  # 2 hour expiry
        }
        
        self.answers[test_id] = []
        
        # Persist to MongoDB
        self._save_to_db(test_id)
        
        logger.info(f"📝 Test created: {test_id} ({len(questions)} questions)")
        return test_id

    def get_test(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get test data — checks cache first, then MongoDB"""
        # Check cache
        if test_id in self.tests:
            return self.tests[test_id]
        
        # Cache miss → try MongoDB (handles server restart)
        if self._load_from_db(test_id):
            return self.tests.get(test_id)
        
        return None

    def get_current_question(self, test_id: str) -> Dict[str, Any]:
        """Get current question for test"""
        test = self.get_test(test_id)  # Uses cache + MongoDB fallback
        if not test:
            return {}
        
        q_num = test.get("current_question", 1)
        questions = test.get("questions", [])
        
        if q_num > len(questions):
            return {}
        
        question = questions[q_num - 1]
        
        return {
            "question_number": q_num,
            "total_questions": len(questions),
            "question_html": question.get("question", ""),
            "options": question.get("options"),
            "is_mcq": question.get("is_mcq", True),
            "time_limit": 120
        }

    def submit_answer(self, test_id: str, question_number: int, answer: str) -> bool:
        """Submit answer — updates cache and persists to MongoDB"""
        test = self.get_test(test_id)  # Auto-recovers from MongoDB if needed
        if not test:
            return False
        
        questions = test.get("questions", [])
        if question_number > len(questions):
            return False
        
        question = questions[question_number - 1]
        
        # Store answer
        answer_data = {
            "question_number": question_number,
            "question": question.get("question", ""),
            "answer": answer,
            "submitted_at": time.time()
        }
        
        # Ensure answer list is correct size
        if test_id not in self.answers:
            self.answers[test_id] = []
        while len(self.answers[test_id]) < question_number:
            self.answers[test_id].append({})
        
        self.answers[test_id][question_number - 1] = answer_data
        
        # Move to next question
        test["current_question"] = question_number + 1
        
        # Persist updated state to MongoDB
        self._save_to_db(test_id)
        
        return True

    def get_test_answers(self, test_id: str) -> List[Dict[str, Any]]:
        """Get all answers for a test"""
        # Check cache first
        if test_id in self.answers:
            return self.answers[test_id]
        
        # Try loading from MongoDB
        if self._load_from_db(test_id):
            return self.answers.get(test_id, [])
        
        return []

    def is_test_complete(self, test_id: str) -> bool:
        """Check if test is complete"""
        test = self.get_test(test_id)
        if not test:
            return False
        
        current = test.get("current_question", 1)
        total = test.get("total_questions", 0)
        
        return current > total

    def cleanup_test(self, test_id: str):
        """Cleanup test from both cache and MongoDB (called after completion)"""
        # Remove from cache
        if test_id in self.tests:
            del self.tests[test_id]
        if test_id in self.answers:
            del self.answers[test_id]
        
        # Remove from MongoDB (results already saved separately)
        self._delete_from_db(test_id)
        
        logger.info(f"🧹 Test cleaned up: {test_id}")

    def cleanup_expired_data(self):
        """Cleanup expired tests from cache (MongoDB TTL handles DB cleanup)"""
        now = time.time()
        expired = []
        
        for test_id, test in self.tests.items():
            if test.get("expires_at", 0) < now:
                expired.append(test_id)
        
        for test_id in expired:
            self.cleanup_test(test_id)
        
        if expired:
            logger.info(f"🧹 Cleaned up {len(expired)} expired tests")


# Singleton
memory_manager = MemoryManager()


def cleanup_all():
    """Cleanup all active tests - called on shutdown"""
    global memory_manager
    # Don't clear MongoDB on shutdown — that's the whole point!
    # Only clear the in-memory cache
    expired_count = len(memory_manager.tests)
    memory_manager.tests.clear()
    memory_manager.answers.clear()
    logger.info(f"🧹 Cleared {expired_count} tests from memory cache (MongoDB preserved)")