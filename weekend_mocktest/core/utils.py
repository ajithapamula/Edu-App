# weekend_mocktest/core/utils.py
import logging
import time
import gc
import threading
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .config import config

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Streamlined memory management for active tests.
    
    Features:
    - Active test session management (with MongoDB backup)
    - Answer storage
    - Question caching (legacy)
    - Automatic cleanup
    """
    
    def __init__(self):
        self.tests = {}           # Active test sessions (in-memory cache)
        self.answers = {}         # Test answers
        self.question_cache = {}  # Generated questions cache (legacy)
        self._cleanup_thread = None
        self._db_manager = None   # Lazy loaded
        self._start_cleanup_thread()
    
    @property
    def db_manager(self):
        """Lazy load database manager"""
        if self._db_manager is None:
            from .database import get_db_manager
            self._db_manager = get_db_manager()
        return self._db_manager
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return
        
        self._cleanup_thread = threading.Thread(
            target=self._periodic_cleanup, 
            daemon=True
        )
        self._cleanup_thread.start()
        logger.info("🧹 Cleanup thread started")
    
    def _periodic_cleanup(self):
        """Periodic cleanup of expired data"""
        while True:
            try:
                time.sleep(1800)  # 30 minutes
                self.cleanup_expired_data()
            except Exception as e:
                logger.error(f"Cleanup thread error: {e}")
    
    def cleanup_expired_data(self):
        """Clean up expired tests and cache"""
        try:
            current_time = time.time()
            
            # Clean expired tests
            expired_tests = []
            for test_id, test_data in list(self.tests.items()):
                age = current_time - test_data.get("created_at", 0)
                if age > config.TEST_SESSION_TIMEOUT:
                    expired_tests.append(test_id)
            
            for test_id in expired_tests:
                self.cleanup_test(test_id)
            
            # Clean expired cache
            cache_expiry = config.QUESTION_CACHE_DURATION_HOURS * 3600
            expired_cache = []
            for cache_key, cache_data in list(self.question_cache.items()):
                age = current_time - cache_data.get("created_at", 0)
                if age > cache_expiry:
                    expired_cache.append(cache_key)
            
            for cache_key in expired_cache:
                self.question_cache.pop(cache_key, None)
            
            # Force garbage collection
            gc.collect()
            
            if expired_tests or expired_cache:
                logger.info(f"🧹 Cleaned: {len(expired_tests)} tests, {len(expired_cache)} cache entries")
        
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    def create_test(self, user_type: str, questions: List[Dict[str, Any]], 
                   student_id: int = None) -> str:
        """
        Create new test session.
        
        Args:
            user_type: 'dev' or 'non_dev'
            questions: List of question dictionaries
            student_id: Optional student ID
        
        Returns:
            Unique test ID
        """
        test_id = str(uuid.uuid4())
        
        # Calculate section breakdowns
        sections = {"aptitude": 0, "theory": 0, "coding": 0, "mcq": 0}
        for q in questions:
            q_type = q.get("question_type", "theory")
            if q_type in sections:
                sections[q_type] += 1
        
        test_data = {
            "test_id": test_id,
            "user_type": user_type,
            "student_id": student_id,
            "total_questions": len(questions),
            "current_question": 1,
            "questions": questions,
            "sections": {k: v for k, v in sections.items() if v > 0},
            "created_at": time.time(),
            "started_at": time.time(),
            "answers": []
        }
        
        # Store in memory
        self.tests[test_id] = test_data
        self.answers[test_id] = []
        
        # Also persist to MongoDB for reliability
        try:
            self.db_manager.active_tests_collection.update_one(
                {"test_id": test_id},
                {"$set": test_data},
                upsert=True
            )
            logger.info(f"📝 Test created & persisted: {test_id}")
        except Exception as e:
            logger.warning(f"⚠️ MongoDB persist failed (test still in memory): {e}")
        
        logger.info(f"📝 Test created: {test_id} ({len(questions)} questions, sections: {sections})")
        return test_id
    
    def get_test(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get test data by ID (checks memory first, then MongoDB)"""
        # Check memory first
        test_data = self.tests.get(test_id)
        if test_data:
            return test_data
        
        # Not in memory - check MongoDB
        try:
            mongo_test = self.db_manager.active_tests_collection.find_one(
                {"test_id": test_id},
                {"_id": 0}
            )
            if mongo_test:
                # Restore to memory
                self.tests[test_id] = mongo_test
                self.answers[test_id] = mongo_test.get("answers", [])
                logger.info(f"📥 Test restored from MongoDB: {test_id}")
                return mongo_test
        except Exception as e:
            logger.warning(f"⚠️ MongoDB lookup failed: {e}")
        
        return None
    
    def update_test(self, test_id: str, updates: Dict[str, Any]) -> bool:
        """Update test data in memory and MongoDB"""
        test = self.get_test(test_id)
        if not test:
            return False
        
        # Update memory
        test.update(updates)
        self.tests[test_id] = test
        
        # Update MongoDB
        try:
            self.db_manager.active_tests_collection.update_one(
                {"test_id": test_id},
                {"$set": updates}
            )
        except Exception as e:
            logger.warning(f"⚠️ MongoDB update failed: {e}")
        
        return True
    
    def get_current_question(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get current question for test"""
        test = self.get_test(test_id)  # This now checks MongoDB too
        if not test:
            return None
        
        current_q_num = test["current_question"]
        questions = test["questions"]
        
        if 1 <= current_q_num <= len(questions):
            question_data = questions[current_q_num - 1]
            return {
                "question_number": current_q_num,
                "total_questions": len(questions),
                "question_html": question_data["question"],
                "options": question_data.get("options"),
                "difficulty": question_data.get("difficulty", "Medium"),
                "type": question_data.get("question_type", "General"),
                "question_id": question_data.get("question_id", "")
            }
        
        return None
    
    def submit_answer(self, test_id: str, question_number: int, answer: str,
                     time_taken: int = None) -> bool:
        """
        Submit answer for test question.
        
        Args:
            test_id: Test session ID
            question_number: Question number (1-indexed)
            answer: User's answer
            time_taken: Optional time taken in seconds
        
        Returns:
            True if successful
        """
        test = self.get_test(test_id)  # This now checks MongoDB too
        if not test or question_number != test["current_question"]:
            logger.warning(f"⚠️ Submit failed: test={bool(test)}, q={question_number}, current={test.get('current_question') if test else 'N/A'}")
            return False
        
        questions = test["questions"]
        if 1 <= question_number <= len(questions):
            question_data = questions[question_number - 1]
            
            # Store answer with metadata
            answer_data = {
                "question_number": question_number,
                "question_id": question_data.get("question_id", ""),
                "question_type": question_data.get("question_type", "unknown"),
                "question": question_data["question"],
                "answer": answer,
                "options": question_data.get("options", []),
                "submitted_at": time.time(),
                "time_taken": time_taken
            }
            
            # Initialize answers list if needed
            if test_id not in self.answers:
                self.answers[test_id] = []
            
            self.answers[test_id].append(answer_data)
            
            # Move to next question
            test["current_question"] += 1
            self.tests[test_id] = test  # Update memory
            
            # Persist to MongoDB
            try:
                self.db_manager.active_tests_collection.update_one(
                    {"test_id": test_id},
                    {
                        "$set": {"current_question": test["current_question"]},
                        "$push": {"answers": answer_data}
                    }
                )
            except Exception as e:
                logger.warning(f"⚠️ MongoDB update failed: {e}")
            
            logger.info(f"✅ Answer submitted: {test_id} Q{question_number} ({question_data.get('question_type', 'unknown')})")
            return True
        
        return False
    
    def is_test_complete(self, test_id: str) -> bool:
        """Check if test is completed"""
        test = self.get_test(test_id)
        if not test:
            return False
        
        return test["current_question"] > test["total_questions"]
    
    def get_test_answers(self, test_id: str) -> List[Dict[str, Any]]:
        """Get all answers for test"""
        # Check memory first
        if test_id in self.answers and self.answers[test_id]:
            return self.answers[test_id]
        
        # Check MongoDB
        try:
            test_data = self.db_manager.active_tests_collection.find_one(
                {"test_id": test_id},
                {"answers": 1, "_id": 0}
            )
            if test_data and test_data.get("answers"):
                self.answers[test_id] = test_data["answers"]
                return test_data["answers"]
        except Exception as e:
            logger.warning(f"⚠️ Failed to get answers from MongoDB: {e}")
        
        return []
    
    def get_answers_by_section(self, test_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get answers organized by question type/section"""
        answers = self.answers.get(test_id, [])
        
        sections = {
            "aptitude": [],
            "theory": [],
            "coding": [],
            "mcq": []
        }
        
        for answer in answers:
            q_type = answer.get("question_type", "theory")
            if q_type in sections:
                sections[q_type].append(answer)
            else:
                sections["theory"].append(answer)
        
        return {k: v for k, v in sections.items() if v}
    
    def cache_questions(self, cache_key: str, questions: List[Dict[str, Any]]):
        """Cache generated questions (legacy support)"""
        self.question_cache[cache_key] = {
            "questions": questions,
            "created_at": time.time()
        }
        logger.info(f"💾 Questions cached: {cache_key}")
    
    def get_cached_questions(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached questions if not expired (legacy support)"""
        cache_data = self.question_cache.get(cache_key)
        if not cache_data:
            return None
        
        # Check expiry
        age = time.time() - cache_data["created_at"]
        max_age = config.QUESTION_CACHE_DURATION_HOURS * 3600
        
        if age > max_age:
            self.question_cache.pop(cache_key, None)
            return None
        
        return cache_data["questions"]
    
    def cleanup_test(self, test_id: str):
        """Clean up specific test from memory and MongoDB"""
        self.tests.pop(test_id, None)
        self.answers.pop(test_id, None)
        
        # Also clean from MongoDB
        try:
            self.db_manager.active_tests_collection.delete_one({"test_id": test_id})
        except Exception as e:
            logger.warning(f"⚠️ MongoDB cleanup failed: {e}")
        
        logger.info(f"🗑️ Test cleaned: {test_id}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        return {
            "active_tests": len(self.tests),
            "cached_questions": len(self.question_cache),
            "total_answers": sum(len(answers) for answers in self.answers.values()),
            "cleanup_thread_alive": self._cleanup_thread.is_alive() if self._cleanup_thread else False
        }
    
    def get_test_progress(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get test progress information"""
        test = self.tests.get(test_id)
        if not test:
            return None
        
        answers = self.answers.get(test_id, [])
        
        return {
            "test_id": test_id,
            "user_type": test["user_type"],
            "current_question": test["current_question"],
            "total_questions": test["total_questions"],
            "questions_answered": len(answers),
            "sections": test.get("sections", {}),
            "elapsed_time": time.time() - test["started_at"],
            "is_complete": test["current_question"] > test["total_questions"]
        }


class ValidationUtils:
    """Utility functions for data validation"""
    
    @staticmethod
    def validate_user_type(user_type: str) -> bool:
        """Validate user type"""
        return user_type in ["dev", "non_dev"]
    
    @staticmethod
    def validate_test_id(test_id: str) -> bool:
        """Validate test ID format (UUID)"""
        try:
            uuid.UUID(test_id)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_question_number(question_number: Any, total_questions: int) -> bool:
        """Validate question number"""
        try:
            q_num = int(question_number)
            return 1 <= q_num <= total_questions
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_answer(answer: str, user_type: str) -> bool:
        """Validate answer format"""
        if not answer or not answer.strip():
            return False
        
        # All non-empty answers are valid
        return len(answer.strip()) > 0
    
    @staticmethod
    def sanitize_input(input_str: str, max_length: int = 10000) -> str:
        """Sanitize user input"""
        if not input_str:
            return ""
        
        sanitized = input_str.strip()
        
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    @staticmethod
    def validate_student_id(student_id: Any) -> bool:
        """Validate student ID"""
        try:
            sid = int(student_id)
            return sid > 0
        except (ValueError, TypeError):
            return False


class DateTimeUtils:
    """Utility functions for date/time operations"""
    
    @staticmethod
    def get_current_timestamp() -> float:
        """Get current timestamp"""
        return time.time()
    
    @staticmethod
    def format_timestamp(timestamp: float, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format timestamp to string"""
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime(format_str)
        except (ValueError, OSError):
            return "Invalid timestamp"
    
    @staticmethod
    def get_cache_key_date() -> str:
        """Get date string for cache key"""
        return datetime.now().strftime("%Y-%m-%d")
    
    @staticmethod
    def get_week_key() -> str:
        """Get week identifier for question bank batches"""
        now = datetime.now()
        return f"{now.year}-W{now.isocalendar()[1]}"
    
    @staticmethod
    def is_same_day(timestamp1: float, timestamp2: float) -> bool:
        """Check if two timestamps are on the same day"""
        try:
            dt1 = datetime.fromtimestamp(timestamp1)
            dt2 = datetime.fromtimestamp(timestamp2)
            return dt1.date() == dt2.date()
        except (ValueError, OSError):
            return False
    
    @staticmethod
    def seconds_to_hms(seconds: int) -> str:
        """Convert seconds to HH:MM:SS format"""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, secs = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"


# Global instances
memory_manager = MemoryManager()


# Helper functions
def generate_test_id() -> str:
    """Generate unique test ID"""
    return str(uuid.uuid4())


def validate_request_data(test_id: str, question_number: int, answer: str, 
                         user_type: str, total_questions: int) -> List[str]:
    """Validate all request data and return list of errors"""
    errors = []
    
    if not ValidationUtils.validate_test_id(test_id):
        errors.append("Invalid test ID format")
    
    if not ValidationUtils.validate_question_number(question_number, total_questions):
        errors.append("Invalid question number")
    
    if not ValidationUtils.validate_answer(answer, user_type):
        errors.append("Invalid answer format")
    
    if not ValidationUtils.validate_user_type(user_type):
        errors.append("Invalid user type")
    
    return errors


def cleanup_all():
    """Clean up all resources"""
    try:
        memory_manager.cleanup_expired_data()
        logger.info("✅ All resources cleaned")
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")