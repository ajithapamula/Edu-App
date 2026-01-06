# weekend_mocktest/services/test_service.py
# FIXED: Dev=3 sections (apt+mcq+coding), NonDev=2 sections (apt+mcq), No repetition
import logging
import markdown
from typing import Dict, Any, List
from ..core.config import config
from ..core.database import get_db_manager
from ..core.ai_services import get_ai_service
from ..core.content_service import get_content_service
from ..core.utils import memory_manager, ValidationUtils

logger = logging.getLogger(__name__)


class TestService:
    """
    Test service for large scale deployment.
    
    Developer: Aptitude (10) + MCQ (10) + Coding (5) = 25 questions, 3 section evaluation
    Non-Developer: Aptitude (10) + MCQ (20) = 30 questions, 2 section evaluation
    
    Features:
    - Auto collection routing (dev→Developer, non_dev→Non-Developer)
    - No question repetition for same user
    - Question bank for large scale
    """

    def __init__(self):
        self.db_manager = get_db_manager()
        self.ai_service = get_ai_service()
        self.content_service = get_content_service()
        self._ensure_question_bank_ready()
        logger.info("🚀 Test service initialized")

    def _ensure_question_bank_ready(self):
        """Ensure question bank has enough questions"""
        try:
            for user_type in ["dev", "non_dev"]:
                needs = self.db_manager.check_bank_needs_refill(user_type)
                if needs:
                    logger.info(f"📦 Refilling question bank for {user_type}: {needs}")
                    self._populate_question_bank(user_type, needs)
        except Exception as e:
            logger.warning(f"⚠️ Bank check failed: {e}")

    def _populate_question_bank(self, user_type: str, needs: Dict[str, int]):
        """Populate question bank with new questions"""
        try:
            # Get context from correct collection (auto-routed)
            context = self.content_service.get_context_for_questions(user_type)
            
            for question_type, count in needs.items():
                if count <= 0:
                    continue
                    
                questions = self.ai_service.generate_questions_for_bank(
                    user_type, question_type, context, count
                )
                if questions:
                    self.db_manager.add_questions_to_bank(questions, user_type)
                    
            self.db_manager.retire_overused_questions()
        except Exception as e:
            logger.error(f"❌ Bank population failed: {e}")

    async def start_test(self, user_type: str, student_id: int = None):
        """
        Start a new test.
        
        user_type='dev' → Developer collection → 3 sections
        user_type='non_dev' → Non-Developer collection → 2 sections
        """
        logger.info(f"🎯 Starting {user_type} test")

        if not ValidationUtils.validate_user_type(user_type):
            raise ValueError("Invalid user type. Use 'dev' or 'non_dev'")

        try:
            if student_id is None:
                student_info = self.db_manager._get_student_info()
                student_id = student_info["student_id"]
            
            exam_structure = config.get_exam_structure(user_type)
            logger.info(f"📋 Exam structure: {exam_structure}")
            
            # Generate questions (auto-routes to correct collection)
            questions = self._get_questions_for_test(user_type, student_id, exam_structure)
            
            if not questions:
                raise Exception("Failed to generate questions")
            
            # Mark questions as seen (prevents repetition)
            question_ids = [q.get("question_id") for q in questions if q.get("question_id")]
            if question_ids:
                self.db_manager.mark_questions_as_seen(student_id, question_ids)
            
            # Create test session
            test_id = memory_manager.create_test(user_type, questions)
            test_data = memory_manager.get_test(test_id)
            test_data["student_id"] = student_id
            test_data["exam_structure"] = exam_structure
            
            current_question = memory_manager.get_current_question(test_id)
            current_question["question_html"] = markdown.markdown(
                current_question["question_html"],
                extensions=['codehilite', 'fenced_code']
            )
            
            first_q = questions[0]
            time_limit = self._get_question_time_limit(first_q.get("question_type", "aptitude"), user_type)
            
            response = self._create_test_response(test_id, test_data, current_question, time_limit, exam_structure, user_type)
            
            logger.info(f"✅ Test started: {test_id} ({len(questions)} questions)")
            return response

        except Exception as e:
            logger.error(f"❌ Test start failed: {e}")
            raise

    def _get_questions_for_test(self, user_type: str, student_id: int,
                                exam_structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate questions based on user type.
        
        DEVELOPER (user_type='dev'):
          - Aptitude: 10 questions (general)
          - MCQ: 10 questions (from Developer collection)
          - Coding: 5 questions (from Developer collection)
          = 25 total
        
        NON-DEVELOPER (user_type='non_dev'):
          - Aptitude: 10 questions (general)
          - MCQ: 20 questions (from Non-Developer collection)
          - NO CODING!
          = 30 total
        """
        questions = []
        sections = exam_structure.get("sections", {})
        
        try:
            # Get context from correct collection (AUTO ROUTED)
            logger.info(f"📚 Getting content for {user_type} (auto-routed to correct collection)")
            context = self.content_service.get_context_for_questions(user_type)
            
            if user_type == "dev":
                # ============================================
                # DEVELOPER: 3 SECTIONS (Aptitude + MCQ + Coding)
                # ============================================
                logger.info("🔧 DEVELOPER TEST: 3 sections")
                
                # 1. Aptitude (general, no context needed)
                apt_count = sections.get("aptitude", {}).get("question_count", 10)
                apt_qs = self.ai_service.generate_questions_for_bank("dev", "aptitude", "", apt_count)
                questions.extend(self._standardize_questions(apt_qs, "aptitude", is_mcq=True))
                logger.info(f"  ✓ Aptitude: {len(apt_qs)} questions")
                
                # 2. MCQ (from Developer collection)
                mcq_count = sections.get("mcq", {}).get("question_count", 10)
                mcq_qs = self.ai_service.generate_questions_for_bank("dev", "mcq", context, mcq_count)
                questions.extend(self._standardize_questions(mcq_qs, "mcq", is_mcq=True))
                logger.info(f"  ✓ MCQ: {len(mcq_qs)} questions")
                
                # 3. Coding (from Developer collection)
                code_count = sections.get("coding", {}).get("question_count", 5)
                code_qs = self.ai_service.generate_questions_for_bank("dev", "coding", context, code_count)
                questions.extend(self._standardize_questions(code_qs, "coding", is_mcq=False))
                logger.info(f"  ✓ Coding: {len(code_qs)} questions")
                
            else:
                # ============================================
                # NON-DEVELOPER: 2 SECTIONS ONLY (Aptitude + MCQ)
                # NO CODING!
                # ============================================
                logger.info("📊 NON-DEVELOPER TEST: 2 sections only (NO CODING)")
                
                # 1. Aptitude (general)
                apt_count = sections.get("aptitude", {}).get("question_count", 10)
                apt_qs = self.ai_service.generate_questions_for_bank("non_dev", "aptitude", "", apt_count)
                questions.extend(self._standardize_questions(apt_qs, "aptitude", is_mcq=True))
                logger.info(f"  ✓ Aptitude: {len(apt_qs)} questions")
                
                # 2. MCQ (from Non-Developer collection)
                mcq_count = sections.get("mcq", {}).get("question_count", 20)
                mcq_qs = self.ai_service.generate_questions_for_bank("non_dev", "mcq", context, mcq_count)
                questions.extend(self._standardize_questions(mcq_qs, "mcq", is_mcq=True))
                logger.info(f"  ✓ MCQ: {len(mcq_qs)} questions")
                
                # NO CODING FOR NON-DEVELOPER!
            
            # Re-number questions
            for i, q in enumerate(questions, 1):
                q["question_number"] = i
            
            # Log final breakdown
            breakdown = {}
            for q in questions:
                qt = q.get("question_type", "unknown")
                breakdown[qt] = breakdown.get(qt, 0) + 1
            logger.info(f"📝 Final: {breakdown}, Total: {len(questions)}")
            
            return questions
            
        except Exception as e:
            logger.error(f"❌ Question generation failed: {e}")
            raise

    def _standardize_questions(self, questions: List[Dict[str, Any]], 
                               question_type: str, is_mcq: bool) -> List[Dict[str, Any]]:
        """Standardize questions format"""
        standardized = []
        for q in questions:
            std_q = {
                "question_id": q.get("question_id", ""),
                "question_number": 0,
                "title": q.get("title", "Question"),
                "difficulty": q.get("difficulty", "Medium"),
                "question_type": question_type,
                "question": q.get("question", ""),
                "options": q.get("options") if is_mcq else None,
                "correct_answer": q.get("correct_answer"),
                "correct_option_text": q.get("correct_option_text"),
                "is_mcq": is_mcq
            }
            if is_mcq and (not std_q["options"] or len(std_q["options"]) < 3):
                std_q["options"] = ["Option A", "Option B", "Option C", "Option D"]
            standardized.append(std_q)
        return standardized

    def _get_question_time_limit(self, question_type: str, user_type: str) -> int:
        """Get time limit in seconds"""
        if user_type == "non_dev":
            return {"aptitude": 60, "mcq": 60}.get(question_type, 60)
        else:
            return {"aptitude": 90, "mcq": 90, "coding": 240}.get(question_type, 90)

    def _create_test_response(self, test_id: str, test_data: Dict[str, Any],
                              current_question: Dict[str, Any], time_limit: int,
                              exam_structure: Dict[str, Any], user_type: str):
        """Create test start response"""
        questions = test_data.get("questions", [])
        section_info = self._get_section_info(questions, user_type)
        current_section = self._get_current_section(1, section_info)
        
        first_q = questions[0] if questions else {}
        
        class TestResponse:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

        return TestResponse(
            test_id=test_id,
            user_type=user_type,
            question_number=current_question["question_number"],
            total_questions=current_question["total_questions"],
            question_html=current_question["question_html"],
            question_type=first_q.get("question_type", "aptitude"),
            title=first_q.get("title", ""),
            options=first_q.get("options"),
            is_mcq=first_q.get("is_mcq", True),
            time_limit=time_limit,
            exam_structure=exam_structure,
            current_section=current_section,
            section_info=section_info,
            section_progress=self._get_section_progress(1, section_info)
        )
    
    def _get_section_info(self, questions: List[Dict[str, Any]], user_type: str) -> Dict[str, Any]:
        """Get section breakdown - 2 sections for non_dev, 3 for dev"""
        if user_type == "non_dev":
            sections = {"aptitude": {"start": None, "end": None, "count": 0},
                       "mcq": {"start": None, "end": None, "count": 0}}
            section_order = ["aptitude", "mcq"]
        else:
            sections = {"aptitude": {"start": None, "end": None, "count": 0},
                       "mcq": {"start": None, "end": None, "count": 0},
                       "coding": {"start": None, "end": None, "count": 0}}
            section_order = ["aptitude", "mcq", "coding"]
        
        for i, q in enumerate(questions, 1):
            q_type = q.get("question_type", "mcq")
            if q_type in sections:
                if sections[q_type]["start"] is None:
                    sections[q_type]["start"] = i
                sections[q_type]["end"] = i
                sections[q_type]["count"] += 1
        
        section_list = []
        for name in section_order:
            if sections[name]["count"] > 0:
                section_list.append({
                    "name": name,
                    "display_name": name.upper(),
                    "start": sections[name]["start"],
                    "end": sections[name]["end"],
                    "count": sections[name]["count"]
                })
        
        return {"sections": section_list, "total_sections": len(section_list)}
    
    def _get_current_section(self, question_number: int, section_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get current section based on question number"""
        for i, section in enumerate(section_info.get("sections", [])):
            if section["start"] <= question_number <= section["end"]:
                return {"index": i, "name": section["name"], "display_name": section["display_name"],
                       "start": section["start"], "end": section["end"], "count": section["count"]}
        return {"name": "unknown", "index": 0}
    
    def _get_section_progress(self, question_number: int, section_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get progress within section"""
        current = self._get_current_section(question_number, section_info)
        in_section = question_number - current.get("start", 1) + 1
        total = current.get("count", 1)
        return {"current_in_section": in_section, "total_in_section": total,
                "is_last_question_in_section": in_section >= total}

    async def submit_answer(self, test_id: str, question_number: int, answer: str):
        """Submit answer and get next question"""
        logger.info(f"📝 Submitting: {test_id} Q{question_number}")

        try:
            test_data = memory_manager.get_test(test_id)
            if not test_data:
                raise ValueError("Test not found")

            user_type = test_data.get("user_type", "dev")
            
            # Process answer
            processed_answer = self._process_answer(answer, test_id, question_number)
            memory_manager.submit_answer(test_id, question_number, processed_answer)

            # Check if test complete
            if memory_manager.is_test_complete(test_id):
                logger.info(f"🏁 Test completed: {test_id}")
                return await self._complete_test(test_id, test_data)

            # Get next question
            next_question = memory_manager.get_current_question(test_id)
            next_question["question_html"] = markdown.markdown(
                next_question["question_html"],
                extensions=['codehilite', 'fenced_code']
            )

            questions = test_data.get("questions", [])
            next_q_num = next_question["question_number"]
            next_q = questions[next_q_num - 1] if next_q_num <= len(questions) else {}
            
            time_limit = self._get_question_time_limit(next_q.get("question_type", "mcq"), user_type)
            
            return self._create_next_question_response(next_question, time_limit, test_data)

        except Exception as e:
            logger.error(f"❌ Submit failed: {e}")
            raise

    def _process_answer(self, answer: str, test_id: str, question_number: int) -> str:
        """Process answer - convert option index to text if MCQ"""
        if answer.isdigit():
            try:
                test_data = memory_manager.get_test(test_id)
                questions = test_data["questions"]
                if question_number <= len(questions):
                    question = questions[question_number - 1]
                    options = question.get("options", [])
                    idx = int(answer)
                    if 0 <= idx < len(options):
                        return options[idx]
            except:
                pass
        return answer.strip()

    def _create_next_question_response(self, next_question: Dict[str, Any], 
                                       time_limit: int, test_data: Dict[str, Any]):
        """Create next question response"""
        user_type = test_data.get("user_type", "dev")
        questions = test_data.get("questions", [])
        section_info = self._get_section_info(questions, user_type)
        q_num = next_question["question_number"]
        current_section = self._get_current_section(q_num, section_info)
        section_progress = self._get_section_progress(q_num, section_info)
        
        q = questions[q_num - 1] if q_num <= len(questions) else {}
        
        # Check for section change
        prev_section = self._get_current_section(q_num - 1, section_info) if q_num > 1 else current_section
        section_completed = prev_section["display_name"] if prev_section["name"] != current_section["name"] else None
        
        class Response:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

        return Response(
            test_completed=False,
            next_question=Response(
                question_number=next_question["question_number"],
                total_questions=next_question["total_questions"],
                question_html=next_question["question_html"],
                question_type=q.get("question_type", "mcq"),
                title=q.get("title", ""),
                options=q.get("options"),
                is_mcq=q.get("is_mcq", True),
                time_limit=time_limit
            ),
            current_section=current_section,
            section_info=section_info,
            section_progress=section_progress,
            section_just_completed=section_completed,
            next_section_starting=current_section["display_name"] if section_completed else None
        )

    async def _complete_test(self, test_id: str, test_data: Dict[str, Any]):
        """Complete test and evaluate by sections"""
        logger.info(f"🎯 Completing test: {test_id}")

        answers = memory_manager.get_test_answers(test_id)
        user_type = test_data.get("user_type", "dev")
        
        # Evaluate based on user type
        if user_type == "dev":
            # DEVELOPER: 3 sections (Aptitude, MCQ, Coding)
            evaluation_result = await self._evaluate_developer_test(test_data, answers)
        else:
            # NON-DEVELOPER: 2 sections only (Aptitude, MCQ)
            evaluation_result = await self._evaluate_non_dev_test(test_data, answers)

        await self._save_test_results(test_id, test_data, evaluation_result, answers)
        memory_manager.cleanup_test(test_id)

        return self._create_completion_response(evaluation_result, test_data["total_questions"], user_type)

    async def _evaluate_developer_test(self, test_data: Dict[str, Any],
                                       answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        DEVELOPER EVALUATION: 3 SECTIONS
        - Aptitude
        - MCQ
        - Coding
        """
        logger.info("📊 Evaluating DEVELOPER test (3 sections: Aptitude, MCQ, Coding)")
        
        questions = test_data.get("questions", [])
        sections = {"aptitude": [], "mcq": [], "coding": []}
        
        for i, answer_data in enumerate(answers):
            q_type = questions[i].get("question_type", "mcq") if i < len(questions) else "mcq"
            sections[q_type].append({
                "question": answer_data["question"],
                "answer": answer_data["answer"],
                "question_type": q_type,
                "options": answer_data.get("options", []),
                "correct_answer": questions[i].get("correct_answer") if i < len(questions) else None,
                "correct_option_text": questions[i].get("correct_option_text") if i < len(questions) else None
            })
        
        return self.ai_service.evaluate_by_section("dev", sections)

    async def _evaluate_non_dev_test(self, test_data: Dict[str, Any],
                                     answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        NON-DEVELOPER EVALUATION: 2 SECTIONS ONLY
        - Aptitude
        - MCQ
        - NO CODING!
        """
        logger.info("📊 Evaluating NON-DEVELOPER test (2 sections: Aptitude, MCQ)")
        
        questions = test_data.get("questions", [])
        
        # ONLY 2 sections for non-dev
        sections = {"aptitude": [], "mcq": []}
        
        for i, answer_data in enumerate(answers):
            q_type = questions[i].get("question_type", "mcq") if i < len(questions) else "mcq"
            # Force any non-aptitude to mcq for non-dev
            if q_type not in ["aptitude", "mcq"]:
                q_type = "mcq"
            
            sections[q_type].append({
                "question": answer_data["question"],
                "answer": answer_data["answer"],
                "question_type": q_type,
                "options": answer_data.get("options", []),
                "correct_answer": questions[i].get("correct_answer") if i < len(questions) else None,
                "correct_option_text": questions[i].get("correct_option_text") if i < len(questions) else None
            })
        
        logger.info(f"  Aptitude: {len(sections['aptitude'])} questions")
        logger.info(f"  MCQ: {len(sections['mcq'])} questions")
        
        return self.ai_service.evaluate_by_section("non_dev", sections)

    def _create_completion_response(self, evaluation_result: Dict[str, Any], 
                                    total_questions: int, user_type: str):
        """Create completion response with section scores"""
        section_scores = evaluation_result.get("section_scores", {})
        
        # Order based on user type
        if user_type == "non_dev":
            section_order = ["aptitude", "mcq"]  # 2 sections only
        else:
            section_order = ["aptitude", "mcq", "coding"]  # 3 sections
        
        section_results = []
        for sec_name in section_order:
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
        
        class Response:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

        total_correct = evaluation_result.get("total_correct", 0)
        return Response(
            test_completed=True,
            score=total_correct,
            total_questions=total_questions,
            score_percentage=round(total_correct / total_questions * 100, 1) if total_questions > 0 else 0,
            section_scores=section_scores,
            section_results=section_results,
            analytics=evaluation_result.get("evaluation_report", ""),
            summary={
                "total_score": f"{total_correct}/{total_questions}",
                "percentage": round(total_correct / total_questions * 100, 1) if total_questions > 0 else 0,
                "status": "pass" if total_correct / total_questions >= 0.5 else "fail",
                "sections_passed": sum(1 for s in section_results if s["status"] == "pass"),
                "total_sections": len(section_results)
            }
        )

    async def _save_test_results(self, test_id: str, test_data: Dict[str, Any],
                                 evaluation_result: Dict[str, Any], answers: List[Dict[str, Any]]):
        """Save results"""
        for i, answer in enumerate(answers):
            if i < len(evaluation_result.get("scores", [])):
                answer["correct"] = bool(evaluation_result["scores"][i])
            if i < len(evaluation_result.get("feedbacks", [])):
                answer["feedback"] = evaluation_result["feedbacks"][i]

        save_data = {
            "user_type": test_data["user_type"],
            "student_id": test_data.get("student_id"),
            "total_questions": test_data["total_questions"],
            "answers": answers,
            "section_scores": evaluation_result.get("section_scores", {})
        }

        self.db_manager.save_test_results(test_id, save_data, evaluation_result)

    async def force_complete_test(self, test_id: str, termination_reason: str, warnings: int = 0):
        """Force complete test due to proctoring violation"""
        logger.warning(f"🚨 Force completing: {test_id} - {termination_reason}")
        
        try:
            test_data = memory_manager.get_test(test_id)
            if not test_data:
                return {"status": "not_found"}
            
            user_type = test_data.get("user_type", "dev")
            answers = memory_manager.get_test_answers(test_id) or []
            
            if user_type == "dev":
                evaluation_result = await self._evaluate_developer_test(test_data, answers)
            else:
                evaluation_result = await self._evaluate_non_dev_test(test_data, answers)
            
            evaluation_result["terminated"] = True
            evaluation_result["termination_reason"] = termination_reason
            
            await self._save_test_results(test_id, test_data, evaluation_result, answers)
            memory_manager.cleanup_test(test_id)
            
            return {"status": "terminated", "reason": termination_reason}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def health_check(self) -> Dict[str, Any]:
        """Health check"""
        return {
            "status": "healthy",
            "question_bank": self.db_manager.get_question_bank_stats(),
            "collections": self.content_service.get_collection_stats()
        }


_test_service = None

def get_test_service() -> TestService:
    global _test_service
    if _test_service is None:
        _test_service = TestService()
    return _test_service