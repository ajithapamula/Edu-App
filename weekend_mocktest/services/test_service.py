# weekend_mocktest/services/test_service.py
import logging
import markdown
from typing import Dict, Any, List, Optional
from ..core.config import config
from ..core.database import get_db_manager
from ..core.ai_services import get_ai_service
from ..core.content_service import get_content_service
from ..core.utils import memory_manager, ValidationUtils, DateTimeUtils

logger = logging.getLogger(__name__)


class TestService:
    """Production test service with real AI integration"""

    def __init__(self):
        self.db_manager = get_db_manager()
        self.ai_service = get_ai_service()
        self.content_service = get_content_service()
        logger.info("🚀 Test service initialized")

    async def start_test(self, user_type: str):
        logger.info(f"🎯 Starting {user_type} test")

        if not ValidationUtils.validate_user_type(user_type):
            raise ValueError("Invalid user type")

        try:
            cache_key = f"questions_{user_type}_{DateTimeUtils.get_cache_key_date()}"
            cached_questions = memory_manager.get_cached_questions(cache_key)

            if cached_questions:
                logger.info(f"📋 Using cached questions: {len(cached_questions)}")
                questions = cached_questions
            else:
                logger.info("🤖 Generating new questions with AI")

                context = self.content_service.get_context_for_questions(user_type)

                # ✅ Now exists again in content_service.py (compat fix)
                context_quality = self.content_service.validate_context_quality(context)
                if not context_quality.get("is_high_quality", True):
                    logger.warning(f"Low quality context: {context_quality}")

                questions_data = self.ai_service.generate_questions_batch(user_type, context)
                questions = self._standardize_questions(questions_data)

                memory_manager.cache_questions(cache_key, questions)
                logger.info(f"💾 Cached {len(questions)} questions")

            test_id = memory_manager.create_test(user_type, questions)

            current_question = memory_manager.get_current_question(test_id)
            if not current_question:
                raise Exception("Failed to retrieve first question")

            current_question["question_html"] = markdown.markdown(
                current_question["question_html"],
                extensions=['codehilite', 'fenced_code']
            )

            test_data = memory_manager.get_test(test_id)

            time_limit = self._get_time_limit(
                user_type,
                current_question.get("type", "theory")
            )

            response = self._create_test_response(
                test_id, test_data, current_question, time_limit
            )

            logger.info(f"✅ Test started: {test_id}")
            return response

        except Exception as e:
            logger.error(f"❌ Test start failed: {e}")
            raise

    def _standardize_questions(self, questions_data):
        standardized = []

        for i, q_data in enumerate(questions_data, 1):
            raw_type = (q_data.get("type") or "theory").lower()

            # Normalize type
            if "aptitude" in raw_type or "logical" in raw_type:
                q_type = "aptitude"
                time_limit = config.APTITUDE_Q_MIN * 60
            elif "coding" in raw_type or "code" in raw_type:
                q_type = "coding"
                time_limit = config.CODING_Q_MIN * 60
            else:
                q_type = "theory"
                time_limit = config.THEORY_Q_MIN * 60

            standardized.append({
                "question_number": i,
                "title": q_data.get("title", f"Question {i}"),
                "difficulty": q_data.get("difficulty", "Medium"),
                "type": q_type,
                "question": q_data["question"],
                "options": q_data.get("options"),
                "time_limit": time_limit   # ⭐ THIS IS THE KEY
            })

        return standardized

    def _create_test_response(self, test_id: str, test_data: Dict[str, Any],
                              current_question: Dict[str, Any], time_limit: int):
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
        logger.info(f"📝 Submitting answer: {test_id} Q{question_number}")

        try:
            test_data = memory_manager.get_test(test_id)
            if not test_data:
                raise ValueError("Test not found or expired")

            self._validate_submission(test_id, question_number, answer, test_data)

            processed_answer = self._process_answer(
                answer, test_data["user_type"], test_id, question_number
            )

            success = memory_manager.submit_answer(test_id, question_number, processed_answer)
            if not success:
                raise Exception("Failed to submit answer to memory")

            if memory_manager.is_test_complete(test_id):
                logger.info(f"🏁 Test completed: {test_id}")
                return await self._complete_test(test_id, test_data)

            next_question = memory_manager.get_current_question(test_id)
            if not next_question:
                raise Exception("Failed to get next question")

            next_question["question_html"] = markdown.markdown(
                next_question["question_html"],
                extensions=['codehilite', 'fenced_code']
            )

            time_limit = self._get_time_limit(
                test_data["user_type"],
                next_question.get("type", "theory")
            )

            response = self._create_next_question_response(next_question, time_limit)

            logger.info(f"➡️ Next question ready: Q{next_question['question_number']}")
            return response

        except Exception as e:
            logger.error(f"❌ Answer submission failed: {e}")
            raise

    def _validate_submission(self, test_id: str, question_number: int, answer: str, test_data: Dict[str, Any]):
        if not ValidationUtils.validate_test_id(test_id):
            raise ValueError("Invalid test ID format")

        if not ValidationUtils.validate_question_number(question_number, test_data["total_questions"]):
            raise ValueError("Invalid question number")

        if not ValidationUtils.validate_answer(answer, test_data["user_type"]):
            raise ValueError("Invalid answer format")

        if question_number != test_data["current_question"]:
            raise ValueError("Question number mismatch")

    def _process_answer(self, answer: str, user_type: str, test_id: str, question_number: int) -> str:
        if user_type == "non_dev" and answer.isdigit():
            try:
                option_index = int(answer)
                test_data = memory_manager.get_test(test_id)
                questions = test_data["questions"]

                if 1 <= question_number <= len(questions):
                    question = questions[question_number - 1]
                    options = question.get("options", [])

                    # NOTE: your UI might send 0-based or 1-based.
                    # If UI sends "1..4", uncomment the next line:
                    # option_index = option_index - 1

                    if 0 <= option_index < len(options):
                        return options[option_index]
            except Exception:
                pass

        return ValidationUtils.sanitize_input(answer)

    def _create_next_question_response(self, next_question: Dict[str, Any], time_limit: int):
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
        logger.info(f"🎯 Completing test: {test_id}")

        answers = memory_manager.get_test_answers(test_id)
        if not answers:
            raise Exception("No answers found")

        qa_pairs = []
        for answer_data in answers:
            qa_pairs.append({
                "question": answer_data["question"],
                "answer": answer_data["answer"],
                "options": answer_data.get("options", [])
            })

        logger.info(f"🤖 Evaluating {len(qa_pairs)} answers with AI")
        evaluation_result = self.ai_service.evaluate_test_batch(test_data["user_type"], qa_pairs)

        await self._save_test_results(test_id, test_data, evaluation_result, answers)

        memory_manager.cleanup_test(test_id)

        return self._create_completion_response(evaluation_result, test_data["total_questions"])

    def _create_completion_response(self, evaluation_result: Dict[str, Any], total_questions: int):
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
        for i, answer in enumerate(answers):
            if i < len(evaluation_result.get("scores", [])):
                answer["correct"] = bool(evaluation_result["scores"][i])
            if i < len(evaluation_result.get("feedbacks", [])):
                answer["feedback"] = evaluation_result["feedbacks"][i]

        save_data = {
            "user_type": test_data["user_type"],
            "total_questions": test_data["total_questions"],
            "answers": answers
        }

        self.db_manager.save_test_results(test_id, save_data, evaluation_result)
        logger.info(f"💾 Results saved: {test_id}")

    def _get_time_limit(self, user_type: str, question_type: str) -> int:
        if user_type == "dev":
            if question_type == "coding":
                return 300
            if question_type == "aptitude":
                return 90
            return 120
        return 60


# ✅ MUST be at module-level (no indentation)
_test_service = None

def get_test_service() -> TestService:
    global _test_service
    if _test_service is None:
        _test_service = TestService()
    return _test_service
