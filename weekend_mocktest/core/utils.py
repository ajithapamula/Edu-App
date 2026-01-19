# weekend_mocktest/core/utils.py
"""Utilities - Memory Manager for active tests"""

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
    In-memory test session manager.
    Stores active tests temporarily during session.
    """
    
    def __init__(self):
        self.tests: Dict[str, Dict[str, Any]] = {}
        self.answers: Dict[str, List[Dict[str, Any]]] = {}
        logger.info("📦 MemoryManager initialized")

    def create_test(self, user_type: str, questions: List[Dict], student_id: int = None) -> str:
        """Create a new test session"""
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
        
        logger.info(f"📝 Test created: {test_id} ({len(questions)} questions)")
        return test_id

    def get_test(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get test data"""
        return self.tests.get(test_id)

    def get_current_question(self, test_id: str) -> Dict[str, Any]:
        """Get current question for test"""
        test = self.tests.get(test_id)
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
        """Submit answer for a question"""
        test = self.tests.get(test_id)
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
        while len(self.answers.get(test_id, [])) < question_number:
            self.answers[test_id].append({})
        
        self.answers[test_id][question_number - 1] = answer_data
        
        # Move to next question
        test["current_question"] = question_number + 1
        
        return True

    def get_test_answers(self, test_id: str) -> List[Dict[str, Any]]:
        """Get all answers for a test"""
        return self.answers.get(test_id, [])

    def is_test_complete(self, test_id: str) -> bool:
        """Check if test is complete"""
        test = self.tests.get(test_id)
        if not test:
            return False
        
        current = test.get("current_question", 1)
        total = test.get("total_questions", 0)
        
        return current > total

    def cleanup_test(self, test_id: str):
        """Cleanup test data"""
        if test_id in self.tests:
            del self.tests[test_id]
        if test_id in self.answers:
            del self.answers[test_id]
        logger.info(f"🧹 Test cleaned up: {test_id}")

    def cleanup_expired_data(self):
        """Cleanup expired tests"""
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
    expired_count = len(memory_manager.tests)
    memory_manager.tests.clear()
    memory_manager.answers.clear()
    logger.info(f"🧹 Cleaned up all {expired_count} active tests")