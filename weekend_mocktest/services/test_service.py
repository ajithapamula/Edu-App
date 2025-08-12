# weekend_mocktest/services/test_service.py
import logging
import markdown
import time
from typing import Dict, Any, List, Optional
from ..core.config import config
from ..core.database import get_db_manager
from ..core.ai_services import get_ai_service
from ..core.content_service import get_content_service
from ..core.utils import memory_manager, generate_test_id, ValidationUtils, DateTimeUtils

logger = logging.getLogger(__name__)

class TestService:
    """Production test service with real AI integration"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.ai_service = get_ai_service()
        self.content_service = get_content_service()
        logger.info("🚀 Test service initialized")
    
    async def start_test(self, user_type: str):
        """Start new test with AI-generated questions"""
        logger.info(f"🎯 Starting {user_type} test")
        
        if not ValidationUtils.validate_user_type(user_type):
            raise ValueError("Invalid user type")
        
        try:
            # Check cache first
            cache_key = f"questions_{user_type}_{DateTimeUtils.get_cache_key_date()}"
            cached_questions = memory_manager.get_cached_questions(cache_key)
            
            if cached_questions:
                logger.info(f"📋 Using cached questions: {len(cached_questions)}")
                questions = cached_questions
            else:
                # Generate fresh questions
                logger.info("🤖 Generating new questions with AI")
                
                # Get context from summaries
                context = self.content_service.get_context_for_questions(user_type)
                
                # Validate context quality
                context_quality = self.content_service.validate_context_quality(context)
                if not context_quality["is_high_quality"]:
                    logger.warning(f"Low quality context: {context_quality}")
                
                # Generate questions using AI
                questions_data = self.ai_service.generate_questions_batch(user_type, context)
                
                # Convert to standardized format
                questions = self._standardize_questions(questions_data)
                
                # Cache for future use
                memory_manager.cache_questions(cache_key, questions)
                logger.info(f"💾 Cached {len(questions)} questions")
            
            # Create test session
            test_id = memory_manager.create_test(user_type, questions)
            
            # Get first question
            current_question = memory_manager.get_current_question(test_id)
            if not current_question:
                raise Exception("Failed to retrieve first question")
            
            # Convert markdown to HTML
            current_question["question_html"] = markdown.markdown(
                current_question["question_html"], 
                extensions=['codehilite', 'fenced_code']
            )
            
            # Create response
            test_data = memory_manager.get_test(test_id)
            time_limit = config.DEV_TIME_LIMIT if user_type == "dev" else config.NON_DEV_TIME_LIMIT
            
            response = self._create_test_response(
                test_id, test_data, current_question, time_limit
            )
            
            logger.info(f"✅ Test started: {test_id}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Test start failed: {e}")
            raise
    
    def _standardize_questions(self, questions_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert AI-generated questions to standard format"""
        standardized = []
        
        for i, q_data in enumerate(questions_data, 1):
            question = {
                "question_number": i,
                "title": q_data.get("title", f"Question {i}"),
                "difficulty": q_data.get("difficulty", "Medium"),
                "type": q_data.get("type", "General"),
                "question": q_data["question"],
                "options": q_data.get("options")
            }
            standardized.append(question)
        
        return standardized
    
    def _create_test_response(self, test_id: str, test_data: Dict[str, Any], 
                            current_question: Dict[str, Any], time_limit: int):
        """Create standardized test response object"""
        class TestResponse:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        return TestResponse(
            test_id=test_id,
            user_type=test_data["user_type"],
            question_number=current_question["question_number"],
            total_questions=current_question["total_questions"],
            question_html=current_question["question_html"],
            options=current_question.get("options"),
            time_limit=time_limit
        )
    
    async def submit_answer(self, test_id: str, question_number: int, answer: str):
        """Submit answer and proceed to next question or complete test"""
        logger.info(f"📝 Submitting answer: {test_id} Q{question_number}")
        
        try:
            # Validate test exists
            test_data = memory_manager.get_test(test_id)
            if not test_data:
                raise ValueError("Test not found or expired")
            
            # Validate input
            self._validate_submission(test_id, question_number, answer, test_data)
            
            # Process answer (convert MCQ indices to text)
            processed_answer = self._process_answer(answer, test_data["user_type"], test_id, question_number)
            
            # Submit to memory
            success = memory_manager.submit_answer(test_id, question_number, processed_answer)
            if not success:
                raise Exception("Failed to submit answer to memory")
            
            # Check if test complete
            if memory_manager.is_test_complete(test_id):
                logger.info(f"🏁 Test completed: {test_id}")
                return await self._complete_test(test_id, test_data)
            
            # Get next question
            next_question = memory_manager.get_current_question(test_id)
            if not next_question:
                raise Exception("Failed to get next question")
            
            # Convert markdown to HTML
            next_question["question_html"] = markdown.markdown(
                next_question["question_html"],
                extensions=['codehilite', 'fenced_code']
            )
            
            # Create response
            time_limit = config.DEV_TIME_LIMIT if test_data["user_type"] == "dev" else config.NON_DEV_TIME_LIMIT
            
            response = self._create_next_question_response(next_question, time_limit)
            
            logger.info(f"➡️ Next question ready: Q{next_question['question_number']}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Answer submission failed: {e}")
            raise
    
    def _validate_submission(self, test_id: str, question_number: int, answer: str, test_data: Dict[str, Any]):
        """Validate answer submission"""
        if not ValidationUtils.validate_test_id(test_id):
            raise ValueError("Invalid test ID format")
        
        if not ValidationUtils.validate_question_number(question_number, test_data["total_questions"]):
            raise ValueError("Invalid question number")
        
        if not ValidationUtils.validate_answer(answer, test_data["user_type"]):
            raise ValueError("Invalid answer format")
        
        if question_number != test_data["current_question"]:
            raise ValueError("Question number mismatch")
    
    def _process_answer(self, answer: str, user_type: str, test_id: str, question_number: int) -> str:
        """Process answer based on user type (convert MCQ indices to text)"""
        if user_type == "non_dev" and answer.isdigit():
            try:
                option_index = int(answer)
                test_data = memory_manager.get_test(test_id)
                questions = test_data["questions"]
                
                if 1 <= question_number <= len(questions):
                    question = questions[question_number - 1]
                    options = question.get("options", [])
                    
                    if 0 <= option_index < len(options):
                        return options[option_index]
            except (ValueError, IndexError, KeyError):
                pass
        
        return ValidationUtils.sanitize_input(answer)
    
    def _create_next_question_response(self, next_question: Dict[str, Any], time_limit: int):
        """Create next question response"""
        class NextQuestionResponse:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        class SubmitResponse:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        next_q = NextQuestionResponse(
            question_number=next_question["question_number"],
            total_questions=next_question["total_questions"],
            question_html=next_question["question_html"],
            options=next_question.get("options"),
            time_limit=time_limit
        )
        
        return SubmitResponse(
            test_completed=False,
            next_question=next_q
        )
    
    async def _complete_test(self, test_id: str, test_data: Dict[str, Any]):
        """Complete test and generate evaluation using AI"""
        logger.info(f"🎯 Completing test: {test_id}")
        
        try:
            # Get all answers
            answers = memory_manager.get_test_answers(test_id)
            if not answers:
                raise Exception("No answers found")
            
            # Prepare QA pairs for AI evaluation
            qa_pairs = []
            for answer_data in answers:
                qa_pairs.append({
                    "question": answer_data["question"],
                    "answer": answer_data["answer"],
                    "options": answer_data.get("options", [])
                })
            
            # Evaluate using AI
            logger.info(f"🤖 Evaluating {len(qa_pairs)} answers with AI")
            evaluation_result = self.ai_service.evaluate_test_batch(test_data["user_type"], qa_pairs)
            
            # Save results to database
            await self._save_test_results(test_id, test_data, evaluation_result, answers)
            
            # Cleanup memory
            memory_manager.cleanup_test(test_id)
            
            # Create completion response
            response = self._create_completion_response(evaluation_result, test_data["total_questions"])
            
            logger.info(f"✅ Test completed: {test_id}, Score: {evaluation_result['total_correct']}/{test_data['total_questions']}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Test completion failed: {e}")
            raise
    
    def _create_completion_response(self, evaluation_result: Dict[str, Any], total_questions: int):
        """Create test completion response"""
        class CompletionResponse:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        return CompletionResponse(
            test_completed=True,
            score=evaluation_result["total_correct"],
            total_questions=total_questions,
            analytics=evaluation_result["evaluation_report"]
        )
    
    async def _save_test_results(self, test_id: str, test_data: Dict[str, Any], 
                               evaluation_result: Dict[str, Any], answers: List[Dict[str, Any]]):
        """Save test results to database"""
        try:
            # Enhance answers with evaluation data
            for i, answer in enumerate(answers):
                if i < len(evaluation_result.get("scores", [])):
                    answer["correct"] = bool(evaluation_result["scores"][i])
                if i < len(evaluation_result.get("feedbacks", [])):
                    answer["feedback"] = evaluation_result["feedbacks"][i]
            
            # Prepare save data
            save_data = {
                "user_type": test_data["user_type"],
                "total_questions": test_data["total_questions"],
                "answers": answers
            }
            
            # Save to database
            self.db_manager.save_test_results(test_id, save_data, evaluation_result)
            logger.info(f"💾 Results saved: {test_id}")
            
        except Exception as e:
            logger.error(f"❌ Save failed: {e}")
            # Re-raise to let caller handle
            raise Exception(f"Failed to save results: {e}")
    
    async def get_test_results(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve test results by ID"""
        try:
            if not ValidationUtils.validate_test_id(test_id):
                raise ValueError("Invalid test ID format")
            
            results = self.db_manager.get_test_results(test_id)
            if not results:
                raise ValueError("Test results not found")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to get results: {e}")
            raise
    
    async def get_all_tests(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all test results"""
        try:
            results = self.db_manager.get_all_test_results(limit)
            return results
        except Exception as e:
            logger.error(f"❌ Failed to get all tests: {e}")
            raise
    
    async def get_students(self) -> List[Dict[str, Any]]:
        """Get student list"""
        try:
            students = self.db_manager.get_student_list()
            return students
        except Exception as e:
            logger.error(f"❌ Failed to get students: {e}")
            raise
    
    async def get_student_tests(self, student_id: str) -> List[Dict[str, Any]]:
        """Get tests for specific student"""
        try:
            tests = self.db_manager.get_student_tests(student_id)
            return tests
        except Exception as e:
            logger.error(f"❌ Failed to get student tests: {e}")
            raise
    
    def cleanup_expired_tests(self) -> Dict[str, Any]:
        """Clean up expired test sessions"""
        try:
            memory_manager.cleanup_expired_data()
            stats = memory_manager.get_memory_stats()
            
            return {
                "message": "Cleanup completed",
                "active_tests": stats["active_tests"],
                "cached_questions": stats["cached_questions"],
                "timestamp": DateTimeUtils.get_current_timestamp()
            }
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Service health check"""
        try:
            stats = memory_manager.get_memory_stats()
            ai_health = self.ai_service.health_check()
            
            return {
                "status": "healthy",
                "active_tests": stats["active_tests"],
                "cached_questions": stats["cached_questions"],
                "ai_service": ai_health["status"],
                "timestamp": DateTimeUtils.get_current_timestamp()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": DateTimeUtils.get_current_timestamp()
            }

# Singleton instance
_test_service = None

def get_test_service() -> TestService:
    """Get test service singleton"""
    global _test_service
    if _test_service is None:
        _test_service = TestService()
    return _test_service