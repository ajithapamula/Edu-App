# weekend_mocktest/services/test_service.py
"""
Mock Test Service - UPDATED with AI Explanations in Evaluation

UPDATES:
- Saves section_details with AI explanations
- Proper answer comparison
- Stores detailed question-by-question results
"""

import logging
import markdown
import time
import hashlib
import uuid
from typing import Dict, Any, List, Optional

from ..core.config import config
from ..core.database import get_db_manager
from ..core.ai_services import get_ai_service
from ..core.content_service import get_content_service
from ..core.utils import memory_manager, ValidationUtils

logger = logging.getLogger(__name__)


class TestService:
    """Test service with AI explanations in evaluation"""

    PROGRAMMING_KEYWORDS = [
        'write a program', 'write a function', 'write code', 'write python',
        'implement a function', 'create a function', 'code to',
        'python program', 'python code', 'python function',
        'in python', 'using python', 'java program',
        'def ', 'import ', 'from ', 'class ', 'return ',
        'print(', 'input(', 'len(', 'range(',
        '__init__', '__name__', '__main__', 'self.',
        'try:', 'except:', 'finally:', 'lambda',
        'for i in range', '>>>', '```python',
        '.py', 'pip install', 'pip ', 'npm ',
        'pandas', 'numpy', 'tensorflow', 'pytorch', 'sklearn',
        'django', 'flask', 'react', 'angular', 'vue'
    ]
    
    SAP_WHITELIST = [
        'sap', 'erp', 'enterprise', 'procurement', 'sales', 'distribution',
        'finance', 'accounting', 'hr', 'human resources', 'production',
        'material', 'vendor', 'customer', 'invoice', 'payment', 'billing',
        'purchase order', 'sales order', 'master data', 'transaction',
        'mm', 'sd', 'fico', 'pp', 'wm', 'qm', 'pm',
        'general ledger', 'cost center', 'profit center',
        'business process', 'organizational'
    ]

    def __init__(self):
        self.db_manager = get_db_manager()
        self.ai_service = get_ai_service()
        self.content_service = get_content_service()
        logger.info("🚀 Test Service initialized with AI Explanations support")

    def _is_programming_question(self, question_data: Dict) -> bool:
        """Check if question contains programming content"""
        text_parts = [
            str(question_data.get("question", "")),
            str(question_data.get("title", "")),
        ]
        
        options = question_data.get("options", [])
        if isinstance(options, list):
            text_parts.extend([str(opt) for opt in options])
        elif isinstance(options, dict):
            text_parts.extend([str(v) for v in options.values()])
        
        combined = " ".join(text_parts).lower()
        
        for sap_term in self.SAP_WHITELIST:
            if sap_term in combined:
                return False
        
        for keyword in self.PROGRAMMING_KEYWORDS:
            if keyword.lower() in combined:
                return True
        
        return False

    def _filter_programming_questions(self, questions: List[Dict], user_type: str) -> List[Dict]:
        """Filter out programming questions for non-dev users"""
        if user_type == "dev":
            return questions
        
        filtered = []
        removed = 0
        
        for q in questions:
            if q.get("question_type") == "coding":
                removed += 1
                continue
            
            if self._is_programming_question(q):
                removed += 1
            else:
                filtered.append(q)
        
        if removed > 0:
            logger.info(f"✅ Filtered out {removed} programming questions for non-dev")
        
        return filtered

    async def start_test(self, user_type: str, student_id: int = None):
        """Start test with NO question repetition"""
        
        logger.info("")
        logger.info("=" * 70)
        if user_type == "dev":
            logger.info("🟢🟢🟢 STARTING DEVELOPER TEST 🟢🟢🟢")
        else:
            logger.info("🟠🟠🟠 STARTING NON-DEVELOPER TEST 🟠🟠🟠")
        logger.info("=" * 70)

        if not ValidationUtils.validate_user_type(user_type):
            raise ValueError("Invalid user type. Use 'dev' or 'non_dev'")

        try:
            if student_id is None:
                student_info = self.db_manager._get_student_info()
                student_id = student_info["student_id"]
            
            exam_structure = config.get_exam_structure(user_type)
            questions = self._generate_questions_no_repeat(user_type, exam_structure, student_id)
            
            if not questions:
                raise Exception("Failed to generate questions")
            
            if user_type == "non_dev":
                questions = self._filter_programming_questions(questions, user_type)
            
            test_id = memory_manager.create_test(user_type, questions, student_id)
            test_data = memory_manager.get_test(test_id)
            test_data["student_id"] = student_id
            test_data["exam_structure"] = exam_structure
            
            question_ids = [q.get("question_id") for q in questions if q.get("question_id")]
            if question_ids:
                self.db_manager.mark_questions_as_seen(student_id, question_ids)
                self.db_manager.increment_question_usage(question_ids)
            
            current_question = memory_manager.get_current_question(test_id)
            current_question["question_html"] = markdown.markdown(
                current_question["question_html"],
                extensions=['fenced_code']
            )
            
            first_q = questions[0]
            time_limit = self._get_time_limit(first_q.get("question_type", "aptitude"), user_type)
            
            response = self._create_start_response(test_id, test_data, current_question, time_limit, exam_structure, user_type)
            
            logger.info(f"✅ Test started: {test_id} ({len(questions)} questions)")
            return response

        except Exception as e:
            logger.error(f"❌ Test start failed: {e}")
            raise

    def _generate_questions_no_repeat(self, user_type: str, exam_structure: Dict, student_id: int) -> List[Dict]:
        """Generate questions with NO REPETITION for this student"""
        questions = []
        sections = exam_structure.get("sections", {})
        
        context = self.content_service.get_context_for_questions(user_type)
        
        if user_type == "dev":
            section_config = [
                ("aptitude", sections.get("aptitude", {}).get("question_count", 10), True),
                ("mcq", sections.get("mcq", {}).get("question_count", 10), True),
                ("coding", sections.get("coding", {}).get("question_count", 5), False)
            ]
        else:
            section_config = [
                ("aptitude", sections.get("aptitude", {}).get("question_count", 10), True),
                ("mcq", sections.get("mcq", {}).get("question_count", 20), True)
            ]
        
        for q_type, count, is_mcq in section_config:
            if user_type == "non_dev" and q_type == "coding":
                continue
            
            section_qs = self._get_section_questions_no_repeat(
                student_id=student_id,
                user_type=user_type,
                question_type=q_type,
                count=count,
                is_mcq=is_mcq,
                context="" if q_type == "aptitude" else context
            )
            
            if user_type == "non_dev":
                section_qs = self._filter_programming_questions(section_qs, user_type)
            
            questions.extend(section_qs)
        
        for i, q in enumerate(questions, 1):
            q["question_number"] = i
        
        return questions

    def _get_section_questions_no_repeat(self, student_id: int, user_type: str, 
                                          question_type: str, count: int, 
                                          is_mcq: bool, context: str) -> List[Dict]:
        """Get section questions, ensuring no repetition"""
        
        if user_type == "non_dev" and question_type == "coding":
            return []
        
        unseen = self.db_manager.get_unseen_questions(student_id, user_type, question_type, count * 2)
        
        if user_type == "non_dev" and unseen:
            unseen = [q for q in unseen if not self._is_programming_question(q)]
        
        if len(unseen) < count:
            shortfall = count - len(unseen)
            generate_count = shortfall + 10
            
            new_qs = self.ai_service.generate_questions_for_bank(
                user_type, question_type, context, generate_count
            )
            
            if user_type == "non_dev" and new_qs:
                new_qs = [q for q in new_qs if not self._is_programming_question(q)]
            
            if new_qs:
                for q in new_qs:
                    q["question_id"] = str(uuid.uuid4())
                    q["question_hash"] = hashlib.md5(q.get("question", "").encode()).hexdigest()
                
                self.db_manager.add_questions_to_bank(new_qs, user_type)
                unseen = self.db_manager.get_unseen_questions(student_id, user_type, question_type, count * 2)
                
                if user_type == "non_dev":
                    unseen = [q for q in unseen if not self._is_programming_question(q)]
        
        return self._format_questions(unseen[:count], question_type, is_mcq)

    def _format_questions(self, questions: List[Dict], q_type: str, is_mcq: bool) -> List[Dict]:
        """Format questions for test"""
        formatted = []
        
        for q in questions:
            fq = {
                "question_id": q.get("question_id", str(uuid.uuid4())),
                "question_number": 0,
                "title": q.get("title", "Question"),
                "difficulty": q.get("difficulty", "Medium"),
                "question_type": q_type,
                "question": q.get("question", ""),
                "options": q.get("options") if is_mcq else None,
                "correct_answer": q.get("correct_answer"),
                "correct_option_text": q.get("correct_option_text"),
                "is_mcq": is_mcq
            }
            if is_mcq and (not fq["options"] or len(fq["options"]) < 4):
                fq["options"] = ["Option A", "Option B", "Option C", "Option D"]
            formatted.append(fq)
        
        return formatted

    async def submit_answer(self, test_id: str, question_number: int, answer: str):
        """Submit answer"""
        logger.info(f"📝 Submit: {test_id} Q{question_number}")

        try:
            if self.db_manager.is_test_terminated(test_id):
                reason = self.db_manager.get_termination_reason(test_id)
                raise ValueError(f"Test terminated: {reason}")
            
            test_data = memory_manager.get_test(test_id)
            if not test_data:
                raise ValueError("Test not found")

            user_type = test_data.get("user_type", "dev")
            
            processed = self._process_answer(answer, test_id, question_number)
            memory_manager.submit_answer(test_id, question_number, processed)

            if memory_manager.is_test_complete(test_id):
                return await self._complete_test(test_id, test_data)

            next_q = memory_manager.get_current_question(test_id)
            next_q["question_html"] = markdown.markdown(
                next_q["question_html"], extensions=['fenced_code']
            )

            questions = test_data.get("questions", [])
            q_num = next_q["question_number"]
            q_data = questions[q_num - 1] if q_num <= len(questions) else {}
            
            time_limit = self._get_time_limit(q_data.get("question_type", "mcq"), user_type)
            
            return self._create_next_response(next_q, time_limit, test_data)

        except Exception as e:
            logger.error(f"❌ Submit failed: {e}")
            raise

    def _process_answer(self, answer: str, test_id: str, q_num: int) -> str:
        """Process answer - convert index to text if needed"""
        if answer.isdigit():
            try:
                test_data = memory_manager.get_test(test_id)
                questions = test_data["questions"]
                if q_num <= len(questions):
                    q = questions[q_num - 1]
                    options = q.get("options", [])
                    idx = int(answer)
                    if 0 <= idx < len(options):
                        return options[idx]
            except:
                pass
        return answer.strip()

    def add_warning(self, test_id: str, student_id: int, warning_type: str, 
                    details: Dict = None) -> Dict[str, Any]:
        """Add a proctoring warning"""
        result = self.db_manager.add_warning(test_id, student_id, warning_type, details)
        
        if result.get("should_terminate"):
            logger.warning(f"🚫 Auto-terminating test {test_id} after 3 warnings")
        
        return result

    def get_warning_status(self, test_id: str) -> Dict[str, Any]:
        """Get current warning status for a test"""
        warnings = self.db_manager.get_warnings(test_id)
        return {
            "test_id": test_id,
            "warning_count": warnings.get("warning_count", 0),
            "max_warnings": 3,
            "warnings_remaining": max(0, 3 - warnings.get("warning_count", 0)),
            "is_terminated": warnings.get("terminated", False),
            "termination_reason": warnings.get("termination_reason"),
            "warnings": warnings.get("warnings", [])
        }

    # ════════════════════════════════════════════════════════════
    # COMPLETE TEST WITH AI EXPLANATIONS
    # ════════════════════════════════════════════════════════════

    async def _complete_test(self, test_id: str, test_data: Dict):
        """Complete test and evaluate with AI explanations"""
        logger.info(f"🎯 Completing: {test_id}")

        answers = memory_manager.get_test_answers(test_id)
        user_type = test_data.get("user_type", "dev")
        questions = test_data.get("questions", [])
        
        logger.info(f"📊 Evaluating {len(answers)} answers for {user_type} test with AI explanations")
        
        # Build sections for evaluation
        if user_type == "non_dev":
            sections = {"aptitude": [], "mcq": []}
        else:
            sections = {"aptitude": [], "mcq": [], "coding": []}
        
        for i, ans_data in enumerate(answers):
            q = questions[i] if i < len(questions) else {}
            q_type = q.get("question_type", "mcq")
            
            if user_type == "non_dev" and q_type not in ["aptitude", "mcq"]:
                q_type = "mcq"
            
            qa_entry = {
                "question": q.get("question", ans_data.get("question", "")),
                "answer": ans_data.get("answer", ""),
                "question_type": q_type,
                "options": q.get("options", []),
                "correct_answer": q.get("correct_answer"),
                "correct_option_text": q.get("correct_option_text")
            }
            
            if q_type in sections:
                sections[q_type].append(qa_entry)
        
        # Evaluate with AI explanations
        logger.info(f"🤖 Generating AI explanations for evaluation...")
        eval_result = self.ai_service.evaluate_by_section(user_type, sections)
        
        logger.info(f"✅ Evaluation complete: {eval_result.get('total_correct', 0)}/{len(answers)} correct")
        
        # Save results with section_details
        await self._save_results(test_id, test_data, eval_result, answers)
        memory_manager.cleanup_test(test_id)
        
        return self._create_complete_response(eval_result, test_data["total_questions"], user_type, test_id)

    def _create_complete_response(self, eval_result: Dict, total_q: int, user_type: str, test_id: str):
        """Create completion response"""
        correct = eval_result.get("total_correct", 0)
        pct = round((correct / total_q) * 100, 1) if total_q else 0

        if pct >= 80:
            status, msg = "Excellent", "Excellent performance!"
        elif pct >= 50:
            status, msg = "Good", "Good attempt, room for improvement."
        else:
            status, msg = "Needs Improvement", "Please practice more."

        warnings = self.db_manager.get_warnings(test_id)

        class Response:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

        return Response(
            test_completed=True,
            score=correct,
            total_questions=total_q,
            score_percentage=pct,
            analytics=eval_result.get("evaluation_report", ""),
            section_scores=eval_result.get("section_scores", {}),
            section_details=eval_result.get("section_details", {}),  # NEW: Include section_details
            warning_count=warnings.get("warning_count", 0),
            terminated_by_warnings=warnings.get("terminated", False),
            summary={"status": status, "percentage": pct, "final_message": msg}
        )

    async def _save_results(self, test_id: str, test_data: Dict, eval_result: Dict, answers: List):
        """Save test results to MongoDB with section_details and AI explanations"""
        questions = test_data.get("questions", [])
        scores = eval_result.get("scores", [])
        feedbacks = eval_result.get("feedbacks", [])
        section_details = eval_result.get("section_details", {})

        # Build conversation_pairs for backward compatibility
        conversation_pairs = []
        for idx, ans in enumerate(answers):
            q = questions[idx] if idx < len(questions) else {}
            is_correct = bool(scores[idx]) if idx < len(scores) else False
            correct_ans = q.get("correct_option_text") or q.get("correct_answer", "N/A")
            
            fb = feedbacks[idx] if idx < len(feedbacks) else ""

            conversation_pairs.append({
                "question_number": idx + 1,
                "question_id": q.get("question_id"),
                "question": q.get("question"),
                "question_type": q.get("question_type"),
                "answer": ans.get("answer"),
                "correct": is_correct,
                "correct_answer": correct_ans,
                "feedback": fb,  # AI explanation
                "options": q.get("options", [])
            })

        total_correct = eval_result.get("total_correct", 0)
        total_q = test_data.get("total_questions", len(questions))
        pct = round((total_correct / total_q) * 100, 1) if total_q else 0

        if pct >= 80:
            final_msg = "Excellent performance!"
        elif pct >= 50:
            final_msg = "Good attempt, room for improvement."
        else:
            final_msg = "Needs Improvement. Please practice more."

        warnings_data = self.db_manager.get_warnings(test_id)

        doc = {
            "test_id": test_id,
            "user_type": test_data.get("user_type"),
            "Student_ID": test_data.get("student_id"),
            "score": total_correct,
            "total_questions": total_q,
            "score_percentage": pct,
            "final_message": final_msg,
            
            # Section scores (summary)
            "section_scores": eval_result.get("section_scores", {}),
            
            # NEW: Section details with AI explanations
            "section_details": section_details,
            
            # Detailed evaluation report
            "evaluation_report": eval_result.get("evaluation_report", ""),
            
            # Raw scores and feedbacks
            "scores": scores,
            "feedbacks": feedbacks,
            
            # Backward compatible conversation_pairs
            "conversation_pairs": conversation_pairs,
            
            "test_completed": True,
            "timestamp": time.time(),
            
            # Warning audit trail
            "warning_count": warnings_data.get("warning_count", 0),
            "warnings": warnings_data.get("warnings", []),
            "terminated_by_warnings": warnings_data.get("terminated", False),
            "termination_reason": warnings_data.get("termination_reason")
        }

        self.db_manager.test_results_collection.update_one(
            {"test_id": test_id},
            {"$set": doc},
            upsert=True
        )

        logger.info(f"💾 Saved with AI explanations: {test_id} | {total_correct}/{total_q} ({pct}%)")

    async def force_complete_test(self, test_id: str, reason: str, warnings: int = 0):
        """Force complete test due to warnings"""
        logger.warning(f"🚨 Force complete: {test_id} - {reason}")
        
        try:
            test_data = memory_manager.get_test(test_id)
            if not test_data:
                return {"status": "not_found"}
            
            answers = memory_manager.get_test_answers(test_id) or []
            user_type = test_data.get("user_type", "dev")
            questions = test_data.get("questions", [])
            
            if user_type == "non_dev":
                sections = {"aptitude": [], "mcq": []}
            else:
                sections = {"aptitude": [], "mcq": [], "coding": []}
            
            for i, ans in enumerate(answers):
                q = questions[i] if i < len(questions) else {}
                qt = q.get("question_type", "mcq")
                if user_type == "non_dev" and qt not in ["aptitude", "mcq"]:
                    qt = "mcq"
                if qt in sections:
                    sections[qt].append({
                        "question": q.get("question", ans.get("question", "")),
                        "answer": ans.get("answer", ""),
                        "question_type": qt,
                        "options": q.get("options", []),
                        "correct_answer": q.get("correct_answer"),
                        "correct_option_text": q.get("correct_option_text")
                    })
            
            eval_result = self.ai_service.evaluate_by_section(user_type, sections)
            eval_result["terminated"] = True
            eval_result["termination_reason"] = reason
            
            await self._save_results(test_id, test_data, eval_result, answers)
            memory_manager.cleanup_test(test_id)
            
            return {"status": "terminated", "reason": reason}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _get_time_limit(self, q_type: str, user_type: str) -> int:
        """Get time limit in seconds"""
        if user_type == "non_dev":
            return {"aptitude": 60, "mcq": 60}.get(q_type, 60)
        return {"aptitude": 60, "mcq": 60, "coding": 600}.get(q_type, 60)

    def _create_start_response(self, test_id: str, test_data: Dict, current_q: Dict, 
                                time_limit: int, exam_structure: Dict, user_type: str):
        """Create test start response"""
        questions = test_data.get("questions", [])
        section_info = self._get_section_info(questions, user_type)
        current_section = self._get_current_section(1, section_info)
        first_q = questions[0] if questions else {}

        class Response:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

        return Response(
            test_id=test_id,
            user_type=user_type,
            question_number=current_q["question_number"],
            total_questions=current_q["total_questions"],
            question_html=current_q["question_html"],
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

    def _create_next_response(self, next_q: Dict, time_limit: int, test_data: Dict):
        """Create next question response"""
        user_type = test_data.get("user_type", "dev")
        questions = test_data.get("questions", [])
        section_info = self._get_section_info(questions, user_type)
        q_num = next_q["question_number"]
        curr_sec = self._get_current_section(q_num, section_info)
        sec_progress = self._get_section_progress(q_num, section_info)
        
        q = questions[q_num - 1] if q_num <= len(questions) else {}
        
        prev_sec = self._get_current_section(q_num - 1, section_info) if q_num > 1 else curr_sec
        sec_completed = prev_sec["display_name"] if prev_sec["name"] != curr_sec["name"] else None

        class Response:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

        return Response(
            test_completed=False,
            next_question=Response(
                question_number=next_q["question_number"],
                total_questions=next_q["total_questions"],
                question_html=next_q["question_html"],
                question_type=q.get("question_type", "mcq"),
                title=q.get("title", ""),
                options=q.get("options"),
                is_mcq=q.get("is_mcq", True),
                time_limit=time_limit
            ),
            current_section=curr_sec,
            section_info=section_info,
            section_progress=sec_progress,
            section_just_completed=sec_completed,
            next_section_starting=curr_sec["display_name"] if sec_completed else None
        )

    def _get_section_info(self, questions: List[Dict], user_type: str) -> Dict:
        """Get section breakdown"""
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
            qt = q.get("question_type", "mcq")
            if qt in sections:
                if sections[qt]["start"] is None:
                    sections[qt]["start"] = i
                sections[qt]["end"] = i
                sections[qt]["count"] += 1
        
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

    def _get_current_section(self, q_num: int, section_info: Dict) -> Dict:
        """Get current section"""
        for i, sec in enumerate(section_info.get("sections", [])):
            if sec["start"] <= q_num <= sec["end"]:
                return {"index": i, "name": sec["name"], "display_name": sec["display_name"],
                       "start": sec["start"], "end": sec["end"], "count": sec["count"]}
        return {"name": "unknown", "index": 0}

    def _get_section_progress(self, q_num: int, section_info: Dict) -> Dict:
        """Get progress in section"""
        curr = self._get_current_section(q_num, section_info)
        in_sec = q_num - curr.get("start", 1) + 1
        total = curr.get("count", 1)
        return {"current_in_section": in_sec, "total_in_section": total,
                "is_last_question_in_section": in_sec >= total}

    def _get_question_time_limit(self, q_type: str, user_type: str) -> int:
        """Alias for _get_time_limit"""
        return self._get_time_limit(q_type, user_type)

    async def get_test_results(self, test_id: str) -> Optional[Dict]:
        """Get test results from MongoDB"""
        doc = self.db_manager.test_results_collection.find_one(
            {"test_id": test_id}, {"_id": 0}
        )
        if doc:
            return {
                "test_id": doc.get("test_id"),
                "score": doc.get("score", 0),
                "total_questions": doc.get("total_questions", 0),
                "score_percentage": doc.get("score_percentage", 0),
                "analytics": doc.get("evaluation_report", ""),
                "section_scores": doc.get("section_scores", {}),
                "section_details": doc.get("section_details", {}),
                "timestamp": doc.get("timestamp", 0),
                "warning_count": doc.get("warning_count", 0),
                "terminated_by_warnings": doc.get("terminated_by_warnings", False)
            }
        return None

    async def get_all_tests(self) -> List[Dict]:
        """Get all test results"""
        cursor = self.db_manager.test_results_collection.find(
            {}, {"_id": 0}
        ).sort("timestamp", -1).limit(100)
        return list(cursor)

    async def get_students(self) -> List[Dict]:
        """Get unique students"""
        pipeline = [
            {"$group": {"_id": "$Student_ID"}},
            {"$project": {"Student_ID": "$_id", "_id": 0}}
        ]
        return list(self.db_manager.test_results_collection.aggregate(pipeline))

    async def get_student_tests(self, student_id: str) -> List[Dict]:
        """Get tests for a student"""
        cursor = self.db_manager.test_results_collection.find(
            {"Student_ID": int(student_id)}, {"_id": 0}
        ).sort("timestamp", -1)
        return list(cursor)

    def cleanup_expired_tests(self) -> Dict:
        """Cleanup expired tests"""
        memory_manager.cleanup_expired_data()
        return {"message": "Cleanup complete", "active_tests": len(memory_manager.tests)}

    def health_check(self) -> Dict:
        """Health check"""
        return {"status": "healthy"}


# Singleton
_test_service = None

def get_test_service() -> TestService:
    global _test_service
    if _test_service is None:
        _test_service = TestService()
    return _test_service