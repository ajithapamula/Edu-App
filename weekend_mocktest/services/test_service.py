# weekend_mocktest/services/test_service.py
import logging
import markdown
import time
from typing import Dict, Any, List, Optional
from ..core.config import config
from ..core.database import get_db_manager
from ..core.ai_services import get_ai_service
from ..core.content_service import get_content_service
from ..core.utils import memory_manager, ValidationUtils, DateTimeUtils

logger = logging.getLogger(__name__)


class TestService:
    """
    Production test service with Question Bank integration.
    
    Features:
    - Fetches questions from bank (no repetition for users)
    - Auto-populates bank when running low
    - Developer exam: aptitude → theory → coding (1 hour)
    - Non-developer exam: MCQ only
    - Section-wise evaluation
    """

    def __init__(self):
        self.db_manager = get_db_manager()
        self.ai_service = get_ai_service()
        self.content_service = get_content_service()
        
        # Check and populate question bank on startup
        self._ensure_question_bank_ready()
        
        logger.info("🚀 Test service initialized with Question Bank")

    def _ensure_question_bank_ready(self):
        """Ensure question bank has enough questions"""
        try:
            for user_type in ["dev", "non_dev"]:
                needs = self.db_manager.check_bank_needs_refill(user_type)
                
                if needs:
                    logger.info(f"📦 Question bank needs refill for {user_type}: {needs}")
                    self._populate_question_bank(user_type, needs)
                else:
                    logger.info(f"✅ Question bank ready for {user_type}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Bank check failed (will use on-demand generation): {e}")

    def _populate_question_bank(self, user_type: str, needs: Dict[str, int]):
        """Populate question bank with new questions"""
        try:
            logger.info(f"🏭 Populating question bank for {user_type}")
            
            # Get context from weekly summaries
            context = self.content_service.get_context_for_questions(user_type)
            
            for question_type, count in needs.items():
                if count <= 0:
                    continue
                
                logger.info(f"  Generating {count} {question_type} questions...")
                
                questions = self.ai_service.generate_questions_for_bank(
                    user_type, question_type, context, count
                )
                
                if questions:
                    added = self.db_manager.add_questions_to_bank(
                        questions, user_type
                    )
                    logger.info(f"  ✅ Added {added} {question_type} questions to bank")
            
            # Retire overused questions
            self.db_manager.retire_overused_questions()
            
        except Exception as e:
            logger.error(f"❌ Bank population failed: {e}")

    # ================================================================
    # START TEST
    # ================================================================

    async def start_test(self, user_type: str, student_id: int = None):
        """
        Start a new test for the user.
        
        Args:
            user_type: 'dev' or 'non_dev'
            student_id: Optional student ID (will fetch from MySQL if not provided)
        
        Returns:
            Test response with first question
        """
        logger.info(f"🎯 Starting {user_type} test")

        if not ValidationUtils.validate_user_type(user_type):
            raise ValueError("Invalid user type. Use 'dev' or 'non_dev'")

        try:
            # Get or generate student ID
            if student_id is None:
                student_info = self.db_manager._get_student_info()
                student_id = student_info["student_id"]
            
            # Get exam structure
            exam_structure = config.get_exam_structure(user_type)
            logger.info(f"📋 Exam structure: {exam_structure}")
            
            # Fetch questions from bank (no repetition)
            questions = self._get_questions_for_test(user_type, student_id, exam_structure)
            
            if not questions:
                raise Exception("Failed to get questions for test")
            
            # Mark questions as seen by this student
            question_ids = [q.get("question_id") for q in questions if q.get("question_id")]
            if question_ids:
                self.db_manager.mark_questions_as_seen(student_id, question_ids)
            
            # Create test session
            test_id = memory_manager.create_test(user_type, questions)
            
            # Store student_id in test data
            test_data = memory_manager.get_test(test_id)
            test_data["student_id"] = student_id
            test_data["exam_structure"] = exam_structure
            
            # Get first question
            current_question = memory_manager.get_current_question(test_id)
            if not current_question:
                raise Exception("Failed to retrieve first question")
            
            # Format question HTML
            current_question["question_html"] = markdown.markdown(
                current_question["question_html"],
                extensions=['codehilite', 'fenced_code']
            )
            
            # Get time limit for this question
            time_limit = self._get_question_time_limit(
                questions[0].get("question_type", "theory")
            )
            
            response = self._create_test_response(
                test_id, test_data, current_question, time_limit, exam_structure
            )
            
            logger.info(f"✅ Test started: {test_id} ({len(questions)} questions)")
            return response

        except Exception as e:
            logger.error(f"❌ Test start failed: {e}")
            raise

    def _get_questions_for_test(self, user_type: str, student_id: int,
                                exam_structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get questions for a test from the question bank.
        Ensures no repetition for the student.
        Questions are organized: Aptitude → Theory → Coding (for developer)
        """
        questions = []
        
        try:
            if user_type == "dev":
                # Developer exam: Aptitude → Theory → Coding (in this order)
                sections = exam_structure.get("sections", {})
                
                # 1. APTITUDE SECTION
                aptitude_count = sections.get("aptitude", {}).get("question_count", 0)
                if aptitude_count > 0:
                    logger.info(f"  📋 Fetching {aptitude_count} APTITUDE questions")
                    aptitude_qs = self.db_manager.get_unseen_questions_for_student(
                        student_id, "dev", "aptitude", aptitude_count,
                        difficulty_mix={
                            "Easy": max(1, aptitude_count // 3), 
                            "Medium": aptitude_count // 2,
                            "Hard": max(1, aptitude_count - aptitude_count // 3 - aptitude_count // 2)
                        }
                    )
                    # Explicitly tag as aptitude
                    questions.extend(self._standardize_questions(aptitude_qs, "aptitude"))
                    logger.info(f"    ✓ Got {len(aptitude_qs)} aptitude questions")
                
                # 2. THEORY SECTION
                theory_count = sections.get("theory", {}).get("question_count", 0)
                if theory_count > 0:
                    logger.info(f"  📋 Fetching {theory_count} THEORY questions")
                    theory_qs = self.db_manager.get_unseen_questions_for_student(
                        student_id, "dev", "theory", theory_count
                    )
                    # Explicitly tag as theory
                    questions.extend(self._standardize_questions(theory_qs, "theory"))
                    logger.info(f"    ✓ Got {len(theory_qs)} theory questions")
                
                # 3. CODING SECTION
                coding_count = sections.get("coding", {}).get("question_count", 0)
                if coding_count > 0:
                    logger.info(f"  📋 Fetching {coding_count} CODING questions")
                    coding_qs = self.db_manager.get_unseen_questions_for_student(
                        student_id, "dev", "coding", coding_count
                    )
                    # Explicitly tag as coding
                    questions.extend(self._standardize_questions(coding_qs, "coding"))
                    logger.info(f"    ✓ Got {len(coding_qs)} coding questions")
            
            else:
                # Non-developer exam: MCQ only
                mcq_count = exam_structure.get("total_questions", 30)
                mcq_qs = self.db_manager.get_unseen_questions_for_student(
                    student_id, "non_dev", "mcq", mcq_count
                )
                questions.extend(self._standardize_questions(mcq_qs, "mcq"))
            
            # If not enough questions from bank, generate on-demand
            required_count = exam_structure.get("total_questions", 10)
            if len(questions) < required_count:
                logger.warning(f"⚠️ Only {len(questions)} questions from bank, need {required_count}")
                additional = self._generate_additional_questions(
                    user_type, required_count - len(questions), exam_structure
                )
                questions.extend(additional)
            
            # Re-number all questions sequentially
            for i, q in enumerate(questions, 1):
                q["question_number"] = i
            
            # Log final breakdown
            type_counts = {}
            for q in questions:
                qt = q.get("question_type", "unknown")
                type_counts[qt] = type_counts.get(qt, 0) + 1
            logger.info(f"📝 Final question breakdown: {type_counts}")
            
            return questions
            
        except Exception as e:
            logger.error(f"❌ Failed to get questions from bank: {e}")
            # NO FALLBACK - propagate error with clear message
            raise Exception(f"Cannot start test: {str(e)}")

    def _standardize_questions(self, questions: List[Dict[str, Any]], 
                               question_type: str) -> List[Dict[str, Any]]:
        """
        Standardize questions from bank format to test format.
        Ensures question_type is explicitly set for proper section grouping.
        """
        standardized = []
        
        for q in questions:
            # Normalize question type
            q_type = question_type.lower()
            if q_type in ["aptitude", "logical"]:
                q_type = "aptitude"
            elif q_type in ["coding", "code", "programming"]:
                q_type = "coding"
            elif q_type in ["theory", "conceptual", "concept"]:
                q_type = "theory"
            elif q_type in ["mcq", "multiple_choice"]:
                q_type = "mcq"
            
            std_q = {
                "question_id": q.get("question_id", ""),
                "question_number": len(standardized) + 1,
                "title": q.get("title", "Question"),
                "difficulty": q.get("difficulty", "Medium"),
                "question_type": q_type,  # Explicitly set for section grouping
                "question": q.get("question", ""),
                "options": q.get("options"),
                "time_limit": self._get_question_time_limit(q_type)
            }
            standardized.append(std_q)
        
        return standardized

    def _get_question_time_limit(self, question_type: str) -> int:
        """Get time limit in seconds for question type"""
        time_map = {
            "aptitude": config.APTITUDE_TIME_PER_Q * 60,
            "theory": config.THEORY_TIME_PER_Q * 60,
            "coding": config.CODING_TIME_PER_Q * 60,
            "mcq": config.NON_DEV_TIME_PER_Q * 60
        }
        return time_map.get(question_type, 120)

    def _generate_additional_questions(self, user_type: str, count: int,
                                        exam_structure: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Generate additional questions on-demand when bank is low.
        Maintains proper section types (aptitude, theory, coding).
        
        Raises Exception if no summaries available for user_type.
        """
        # This will raise an error if no summaries available - NO FALLBACK
        context = self.content_service.get_context_for_questions(user_type)
        questions = []
        
        if user_type == "dev":
            # Distribute based on exam structure percentages
            sections = exam_structure.get("sections", {}) if exam_structure else {}
            
            # Calculate proportions
            apt_pct = sections.get("aptitude", {}).get("percentage", 30) / 100
            theory_pct = sections.get("theory", {}).get("percentage", 30) / 100
            coding_pct = sections.get("coding", {}).get("percentage", 40) / 100
            
            apt_count = max(1, int(count * apt_pct))
            theory_count = max(1, int(count * theory_pct))
            coding_count = count - apt_count - theory_count
            
            # Generate aptitude
            if apt_count > 0:
                apt_qs = self.ai_service.generate_questions_for_bank(
                    "dev", "aptitude", context, apt_count
                )
                questions.extend(self._standardize_questions(apt_qs, "aptitude"))
            
            # Generate theory
            if theory_count > 0:
                theory_qs = self.ai_service.generate_questions_for_bank(
                    "dev", "theory", context, theory_count
                )
                questions.extend(self._standardize_questions(theory_qs, "theory"))
            
            # Generate coding
            if coding_count > 0:
                coding_qs = self.ai_service.generate_questions_for_bank(
                    "dev", "coding", context, coding_count
                )
                questions.extend(self._standardize_questions(coding_qs, "coding"))
            
        else:
            # Non-dev: all MCQ
            mcq_qs = self.ai_service.generate_questions_for_bank(
                "non_dev", "mcq", context, count
            )
            questions.extend(self._standardize_questions(mcq_qs, "mcq"))
        
        return questions

    def _generate_fallback_questions(self, user_type: str, 
                                     exam_structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fallback: generate all questions fresh when bank is empty.
        Still maintains proper section types.
        """
        logger.warning("⚠️ Using fallback question generation (bank empty)")
        
        try:
            context = self.content_service.get_context_for_questions(user_type)
            questions = []
            
            if user_type == "dev":
                sections = exam_structure.get("sections", {})
                
                # Generate each section separately to ensure proper typing
                apt_count = sections.get("aptitude", {}).get("question_count", 9)
                theory_count = sections.get("theory", {}).get("question_count", 9)
                coding_count = sections.get("coding", {}).get("question_count", 5)
                
                logger.info(f"  Generating: {apt_count} aptitude, {theory_count} theory, {coding_count} coding")
                
                # Aptitude
                if apt_count > 0:
                    apt_qs = self.ai_service.generate_questions_for_bank("dev", "aptitude", context, apt_count)
                    questions.extend(self._standardize_questions(apt_qs, "aptitude"))
                
                # Theory
                if theory_count > 0:
                    theory_qs = self.ai_service.generate_questions_for_bank("dev", "theory", context, theory_count)
                    questions.extend(self._standardize_questions(theory_qs, "theory"))
                
                # Coding
                if coding_count > 0:
                    coding_qs = self.ai_service.generate_questions_for_bank("dev", "coding", context, coding_count)
                    questions.extend(self._standardize_questions(coding_qs, "coding"))
            else:
                # Non-developer: MCQ only
                mcq_count = exam_structure.get("total_questions", 30)
                mcq_qs = self.ai_service.generate_questions_for_bank("non_dev", "mcq", context, mcq_count)
                questions.extend(self._standardize_questions(mcq_qs, "mcq"))
            
            # Re-number
            for i, q in enumerate(questions, 1):
                q["question_number"] = i
            
            return questions
            
        except Exception as e:
            logger.error(f"Fallback generation failed: {e}")
            raise

    def _create_test_response(self, test_id: str, test_data: Dict[str, Any],
                              current_question: Dict[str, Any], time_limit: int,
                              exam_structure: Dict[str, Any]):
        """Create test start response with section info"""
        
        # Get section info
        questions = test_data.get("questions", [])
        section_info = self._get_section_info(questions)
        current_section = self._get_current_section(1, section_info)
        
        # Get question type from the actual question data
        q_type = "aptitude"  # First question is always aptitude for dev
        if questions:
            q_type = questions[0].get("question_type", "aptitude")
        
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
            question_type=q_type,  # Explicitly set from questions list
            title=questions[0].get("title", "") if questions else "",
            options=current_question.get("options"),
            time_limit=time_limit,
            exam_structure=exam_structure,
            # Section navigation info
            current_section=current_section,
            section_info=section_info,
            section_progress=self._get_section_progress(1, section_info)
        )
    
    def _get_section_info(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get section breakdown from questions.
        Returns start/end indices for each section.
        """
        sections = {
            "aptitude": {"start": None, "end": None, "count": 0, "questions": []},
            "theory": {"start": None, "end": None, "count": 0, "questions": []},
            "coding": {"start": None, "end": None, "count": 0, "questions": []}
        }
        
        for i, q in enumerate(questions, 1):
            q_type = q.get("question_type", "theory")
            
            if q_type in sections:
                if sections[q_type]["start"] is None:
                    sections[q_type]["start"] = i
                sections[q_type]["end"] = i
                sections[q_type]["count"] += 1
                sections[q_type]["questions"].append(i)
        
        # Build section order
        section_order = []
        for sec_name in ["aptitude", "theory", "coding"]:
            if sections[sec_name]["count"] > 0:
                section_order.append({
                    "name": sec_name,
                    "display_name": sec_name.upper(),
                    "start": sections[sec_name]["start"],
                    "end": sections[sec_name]["end"],
                    "count": sections[sec_name]["count"],
                    "time_per_question": self._get_question_time_limit(sec_name)
                })
        
        return {
            "sections": section_order,
            "total_sections": len(section_order),
            "breakdown": {k: v["count"] for k, v in sections.items() if v["count"] > 0}
        }
    
    def _get_current_section(self, question_number: int, 
                             section_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get current section based on question number"""
        for i, section in enumerate(section_info.get("sections", [])):
            if section["start"] <= question_number <= section["end"]:
                return {
                    "index": i,
                    "name": section["name"],
                    "display_name": section["display_name"],
                    "start": section["start"],
                    "end": section["end"],
                    "count": section["count"],
                    "is_first_section": i == 0,
                    "is_last_section": i == len(section_info["sections"]) - 1
                }
        
        # Default to last section
        sections = section_info.get("sections", [])
        if sections:
            last = sections[-1]
            return {
                "index": len(sections) - 1,
                "name": last["name"],
                "display_name": last["display_name"],
                "start": last["start"],
                "end": last["end"],
                "count": last["count"],
                "is_first_section": False,
                "is_last_section": True
            }
        
        return {"name": "unknown", "index": 0}
    
    def _get_section_progress(self, question_number: int, 
                              section_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get progress within current section"""
        current = self._get_current_section(question_number, section_info)
        
        questions_in_section = question_number - current.get("start", 1) + 1
        total_in_section = current.get("count", 1)
        
        return {
            "current_in_section": questions_in_section,
            "total_in_section": total_in_section,
            "section_percentage": round(questions_in_section / total_in_section * 100, 1),
            "is_section_complete": questions_in_section >= total_in_section,
            "is_last_question_in_section": questions_in_section == total_in_section
        }

    # ================================================================
    # SUBMIT ANSWER
    # ================================================================

    async def submit_answer(self, test_id: str, question_number: int, answer: str):
        """Submit an answer and get next question or final results"""
        logger.info(f"📝 Submitting answer: {test_id} Q{question_number}")

        try:
            test_data = memory_manager.get_test(test_id)
            if not test_data:
                raise ValueError("Test not found or expired")

            self._validate_submission(test_id, question_number, answer, test_data)

            # Process answer
            processed_answer = self._process_answer(
                answer, test_data["user_type"], test_id, question_number
            )

            # Submit to memory
            success = memory_manager.submit_answer(test_id, question_number, processed_answer)
            if not success:
                raise Exception("Failed to submit answer")

            # Check if test is complete
            if memory_manager.is_test_complete(test_id):
                logger.info(f"🏁 Test completed: {test_id}")
                return await self._complete_test(test_id, test_data)

            # Get next question
            next_question = memory_manager.get_current_question(test_id)
            if not next_question:
                raise Exception("Failed to get next question")

            # Format next question
            next_question["question_html"] = markdown.markdown(
                next_question["question_html"],
                extensions=['codehilite', 'fenced_code']
            )

            # Get time limit for next question
            questions = test_data.get("questions", [])
            next_q_num = next_question["question_number"]
            next_q_type = "theory"
            if 1 <= next_q_num <= len(questions):
                next_q_type = questions[next_q_num - 1].get("question_type", "theory")
            
            time_limit = self._get_question_time_limit(next_q_type)

            response = self._create_next_question_response(next_question, time_limit, test_data)

            logger.info(f"➡️ Next question ready: Q{next_question['question_number']} ({next_q_type})")
            return response

        except Exception as e:
            logger.error(f"❌ Answer submission failed: {e}")
            raise

    def _validate_submission(self, test_id: str, question_number: int, 
                            answer: str, test_data: Dict[str, Any]):
        """Validate answer submission"""
        if not ValidationUtils.validate_test_id(test_id):
            raise ValueError("Invalid test ID format")

        if not ValidationUtils.validate_question_number(question_number, test_data["total_questions"]):
            raise ValueError("Invalid question number")

        if not ValidationUtils.validate_answer(answer, test_data["user_type"]):
            raise ValueError("Invalid answer format")

        if question_number != test_data["current_question"]:
            raise ValueError(f"Question number mismatch. Expected {test_data['current_question']}")

    def _process_answer(self, answer: str, user_type: str, 
                       test_id: str, question_number: int) -> str:
        """Process and optionally convert answer"""
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
            except Exception:
                pass

        return ValidationUtils.sanitize_input(answer)

    def _create_next_question_response(self, next_question: Dict[str, Any], 
                                       time_limit: int,
                                       test_data: Dict[str, Any] = None) -> Any:
        """Create response for next question with section info"""
        
        class NextQuestionResponse:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

        class SubmitResponse:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        # Get section info if test_data available
        section_info = {}
        current_section = {}
        section_progress = {}
        section_completed = None
        next_section = None
        q_type = next_question.get("type", "theory")
        title = ""
        
        if test_data:
            questions = test_data.get("questions", [])
            section_info = self._get_section_info(questions)
            q_num = next_question["question_number"]
            current_section = self._get_current_section(q_num, section_info)
            section_progress = self._get_section_progress(q_num, section_info)
            
            # Get actual question_type from questions list
            if 1 <= q_num <= len(questions):
                q_type = questions[q_num - 1].get("question_type", "theory")
                title = questions[q_num - 1].get("title", "")
            
            # Check if previous question was last in its section
            prev_q_num = q_num - 1
            if prev_q_num > 0:
                prev_section = self._get_current_section(prev_q_num, section_info)
                if prev_section["name"] != current_section["name"]:
                    section_completed = prev_section["display_name"]
                    next_section = current_section["display_name"]

        next_q = NextQuestionResponse(
            question_number=next_question["question_number"],
            total_questions=next_question["total_questions"],
            question_html=next_question["question_html"],
            question_type=q_type,  # From actual questions list
            title=title,
            options=next_question.get("options"),
            time_limit=time_limit,
            # Section-specific info
            section_question_number=section_progress.get("current_in_section", 1),
            section_total_questions=section_progress.get("total_in_section", 1)
        )

        return SubmitResponse(
            test_completed=False,
            next_question=next_q,
            # Section navigation info
            current_section=current_section,
            section_info=section_info,
            section_progress=section_progress,
            section_just_completed=section_completed,
            next_section_starting=next_section
        )

    # ================================================================
    # COMPLETE TEST
    # ================================================================

    async def _complete_test(self, test_id: str, test_data: Dict[str, Any]):
        """Complete test and evaluate answers"""
        logger.info(f"🎯 Completing test: {test_id}")

        answers = memory_manager.get_test_answers(test_id)
        if not answers:
            raise Exception("No answers found")

        # Organize answers by section for developer tests
        if test_data["user_type"] == "dev":
            evaluation_result = await self._evaluate_developer_test(test_data, answers)
        else:
            evaluation_result = await self._evaluate_non_dev_test(test_data, answers)

        # Save results
        await self._save_test_results(test_id, test_data, evaluation_result, answers)

        # Cleanup
        memory_manager.cleanup_test(test_id)

        return self._create_completion_response(evaluation_result, test_data["total_questions"])

    async def _evaluate_developer_test(self, test_data: Dict[str, Any],
                                       answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate developer test by sections: Aptitude → Theory → Coding
        Each section is evaluated separately with specialized prompts.
        """
        logger.info("📊 Evaluating developer test by sections")
        
        questions = test_data.get("questions", [])
        
        # Group answers by question type (maintain order)
        sections = {
            "aptitude": [],
            "theory": [],
            "coding": []
        }
        
        for i, answer_data in enumerate(answers):
            # Get question type from the original question
            q_type = "theory"  # default
            if i < len(questions):
                q_type = questions[i].get("question_type", "theory").lower()
                
                # Normalize type
                if "aptitude" in q_type or "logical" in q_type:
                    q_type = "aptitude"
                elif "coding" in q_type or "code" in q_type:
                    q_type = "coding"
                else:
                    q_type = "theory"
            
            qa_pair = {
                "question": answer_data["question"],
                "answer": answer_data["answer"],
                "question_type": q_type,
                "options": answer_data.get("options", [])
            }
            
            sections[q_type].append(qa_pair)
        
        # Log section breakdown
        for sec, items in sections.items():
            if items:
                logger.info(f"  📋 {sec.upper()}: {len(items)} questions")
        
        # Evaluate by section (Aptitude → Theory → Coding order)
        return self.ai_service.evaluate_by_section("dev", sections)

    async def _evaluate_non_dev_test(self, test_data: Dict[str, Any],
                                     answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate non-developer test"""
        logger.info("📊 Evaluating non-developer test")
        
        qa_pairs = []
        for answer_data in answers:
            qa_pairs.append({
                "question": answer_data["question"],
                "answer": answer_data["answer"],
                "question_type": "mcq",
                "options": answer_data.get("options", [])
            })
        
        return self.ai_service.evaluate_test_batch("non_dev", qa_pairs)

    def _create_completion_response(self, evaluation_result: Dict[str, Any], 
                                   total_questions: int):
        """Create test completion response with section breakdown"""
        
        section_scores = evaluation_result.get("section_scores", {})
        
        # Build section results for frontend
        section_results = []
        for sec_name in ["aptitude", "theory", "coding"]:
            if sec_name in section_scores:
                sec = section_scores[sec_name]
                section_results.append({
                    "name": sec_name,
                    "display_name": sec_name.upper(),
                    "correct": sec["correct"],
                    "total": sec["total"],
                    "percentage": sec["percentage"],
                    "status": "pass" if sec["percentage"] >= 50 else "fail"
                })
        
        class CompletionResponse:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

        return CompletionResponse(
            test_completed=True,
            score=evaluation_result["total_correct"],
            total_questions=total_questions,
            score_percentage=round(evaluation_result["total_correct"] / total_questions * 100, 1),
            # Section breakdown for frontend
            section_scores=section_scores,
            section_results=section_results,
            # Detailed report
            analytics=evaluation_result["evaluation_report"],
            # Summary for quick display
            summary={
                "total_score": f"{evaluation_result['total_correct']}/{total_questions}",
                "percentage": round(evaluation_result["total_correct"] / total_questions * 100, 1),
                "status": "pass" if evaluation_result["total_correct"] / total_questions >= 0.5 else "fail",
                "sections_passed": sum(1 for s in section_results if s["status"] == "pass"),
                "total_sections": len(section_results)
            }
        )

    async def _save_test_results(self, test_id: str, test_data: Dict[str, Any],
                                 evaluation_result: Dict[str, Any], 
                                 answers: List[Dict[str, Any]]):
        """Save test results to database"""
        # Add evaluation data to answers
        for i, answer in enumerate(answers):
            if i < len(evaluation_result.get("scores", [])):
                answer["correct"] = bool(evaluation_result["scores"][i])
            if i < len(evaluation_result.get("feedbacks", [])):
                answer["feedback"] = evaluation_result["feedbacks"][i]

        save_data = {
            "user_type": test_data["user_type"],
            "total_questions": test_data["total_questions"],
            "answers": answers,
            "section_scores": evaluation_result.get("section_scores", {})
        }

        self.db_manager.save_test_results(test_id, save_data, evaluation_result)
        logger.info(f"💾 Results saved: {test_id}")

    # ================================================================
    # SECTION NAVIGATION (NEW)
    # ================================================================
    
    async def get_test_status(self, test_id: str) -> Dict[str, Any]:
        """
        Get current test status including section progress.
        Useful for frontend to show progress bars, section navigation.
        """
        test_data = memory_manager.get_test(test_id)
        if not test_data:
            raise ValueError("Test not found or expired")
        
        questions = test_data.get("questions", [])
        section_info = self._get_section_info(questions)
        current_q = test_data.get("current_question", 1)
        current_section = self._get_current_section(current_q, section_info)
        section_progress = self._get_section_progress(current_q, section_info)
        
        # Get answered questions count per section
        answers = memory_manager.get_test_answers(test_id)
        answered_by_section = {"aptitude": 0, "theory": 0, "coding": 0}
        
        for i, ans in enumerate(answers):
            if i < len(questions):
                q_type = questions[i].get("question_type", "theory")
                if q_type in answered_by_section:
                    answered_by_section[q_type] += 1
        
        return {
            "test_id": test_id,
            "user_type": test_data["user_type"],
            "current_question": current_q,
            "total_questions": test_data["total_questions"],
            "overall_progress": round((current_q - 1) / test_data["total_questions"] * 100, 1),
            "current_section": current_section,
            "section_info": section_info,
            "section_progress": section_progress,
            "answered_by_section": answered_by_section,
            "is_complete": memory_manager.is_test_complete(test_id),
            "time_elapsed": time.time() - test_data.get("started_at", time.time())
        }
    
    async def get_section_questions(self, test_id: str, section_name: str) -> Dict[str, Any]:
        """
        Get all questions for a specific section.
        Useful for section review or navigation.
        """
        test_data = memory_manager.get_test(test_id)
        if not test_data:
            raise ValueError("Test not found or expired")
        
        questions = test_data.get("questions", [])
        answers = memory_manager.get_test_answers(test_id)
        
        section_questions = []
        for i, q in enumerate(questions):
            if q.get("question_type") == section_name:
                q_num = i + 1
                is_answered = q_num <= len(answers)
                
                section_questions.append({
                    "question_number": q_num,
                    "title": q.get("title", f"Question {q_num}"),
                    "difficulty": q.get("difficulty", "Medium"),
                    "is_answered": is_answered,
                    "time_limit": q.get("time_limit", 120)
                })
        
        return {
            "section_name": section_name,
            "questions": section_questions,
            "total": len(section_questions),
            "answered": sum(1 for q in section_questions if q["is_answered"])
        }
    
    async def navigate_to_section(self, test_id: str, section_name: str) -> Dict[str, Any]:
        """
        Navigate to a specific section (if allowed).
        Returns the first question of that section.
        
        Note: User can only navigate to sections they haven't completed yet,
        or review completed sections (based on your requirements).
        """
        test_data = memory_manager.get_test(test_id)
        if not test_data:
            raise ValueError("Test not found or expired")
        
        questions = test_data.get("questions", [])
        section_info = self._get_section_info(questions)
        
        # Find the section
        target_section = None
        for section in section_info.get("sections", []):
            if section["name"] == section_name:
                target_section = section
                break
        
        if not target_section:
            raise ValueError(f"Section '{section_name}' not found")
        
        # Get first question of section
        first_q_num = target_section["start"]
        
        # Update current question in test
        test_data["current_question"] = first_q_num
        
        # Get the question
        current_question = memory_manager.get_current_question(test_id)
        if not current_question:
            raise Exception("Failed to get section question")
        
        # Format response
        current_question["question_html"] = markdown.markdown(
            current_question["question_html"],
            extensions=['codehilite', 'fenced_code']
        )
        
        time_limit = self._get_question_time_limit(section_name)
        current_section = self._get_current_section(first_q_num, section_info)
        section_progress = self._get_section_progress(first_q_num, section_info)
        
        return {
            "success": True,
            "section_name": section_name,
            "question_number": first_q_num,
            "total_questions": test_data["total_questions"],
            "question_html": current_question["question_html"],
            "question_type": current_question.get("type", section_name),
            "options": current_question.get("options"),
            "time_limit": time_limit,
            "current_section": current_section,
            "section_progress": section_progress
        }

    # ================================================================
    # HEALTH CHECK & UTILITIES
    # ================================================================

    def health_check(self) -> Dict[str, Any]:
        """Check test service health"""
        try:
            bank_stats = self.db_manager.get_question_bank_stats()
            memory_stats = memory_manager.get_memory_stats()
            
            return {
                "status": "healthy",
                "active_tests": memory_stats.get("active_tests", 0),
                "question_bank": bank_stats,
                "exam_structure": {
                    "dev": config.get_exam_structure("dev"),
                    "non_dev": config.get_exam_structure("non_dev")
                }
            }
        except Exception as e:
            return {
                "status": "degraded",
                "error": str(e)
            }

    def get_exam_info(self, user_type: str) -> Dict[str, Any]:
        """Get exam information for frontend"""
        return config.get_exam_structure(user_type)

    async def refill_question_bank(self, user_type: str = None):
        """Manually trigger question bank refill"""
        logger.info("🔄 Manual bank refill triggered")
        
        types_to_check = [user_type] if user_type else ["dev", "non_dev"]
        
        for ut in types_to_check:
            needs = self.db_manager.check_bank_needs_refill(ut)
            if needs:
                self._populate_question_bank(ut, needs)
        
        return self.db_manager.get_question_bank_stats()


# ================================================================
# SINGLETON
# ================================================================

_test_service = None

def get_test_service() -> TestService:
    """Get test service singleton"""
    global _test_service
    if _test_service is None:
        _test_service = TestService()
    return _test_service