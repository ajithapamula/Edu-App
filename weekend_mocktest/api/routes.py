# weekend_mocktest/api/routes.py
# FIXED: Now includes all fields needed by frontend (question_type, is_mcq, section_info, etc.)
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import io

from ..services.test_service import get_test_service
from ..services.pdf_service import get_pdf_service
from ..core.utils import DateTimeUtils

logger = logging.getLogger(__name__)

router = APIRouter()
test_service = get_test_service()
pdf_service = get_pdf_service()


def _serialize_object(obj):
    """Convert response object to dictionary recursively"""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return {k: _serialize_object(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize_object(item) for item in obj]
    if hasattr(obj, '__dict__'):
        return {k: _serialize_object(v) for k, v in obj.__dict__.items()}
    return obj


@router.get("/")
async def home():
    return {"service": "Mock Test API", "version": "7.0.0", "status": "operational"}


@router.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": DateTimeUtils.get_current_timestamp()}


@router.post("/api/test/start")
async def start_test(request_data: dict):
    """Start test - Frontend compatible with ALL fields from test_service"""
    try:
        user_type = request_data.get("user_type", "dev")
        if user_type in ["developer", "dev"]:
            user_type = "dev"
        elif user_type in ["non-developer", "non_dev"]:
            user_type = "non_dev"
        else:
            raise ValueError(f"Invalid user_type: {user_type}")
        
        logger.info(f"Starting test for user_type: {user_type}")
        test_response = await test_service.start_test(user_type)
        
        # Serialize all objects
        section_info = _serialize_object(getattr(test_response, 'section_info', None))
        current_section = _serialize_object(getattr(test_response, 'current_section', None))
        section_progress = _serialize_object(getattr(test_response, 'section_progress', None))
        exam_structure = _serialize_object(getattr(test_response, 'exam_structure', None))
        
        response = {
            # Primary fields (camelCase)
            "testId": test_response.test_id,
            "sessionId": f"session_{test_response.test_id[:8]}",
            "userType": user_type,
            "totalQuestions": test_response.total_questions,
            "timeLimit": test_response.time_limit,
            "duration": test_response.time_limit // 60,
            "questionNumber": test_response.question_number,
            "questionHtml": test_response.question_html,
            "questionType": getattr(test_response, 'question_type', 'aptitude'),
            "title": getattr(test_response, 'title', ''),
            "options": test_response.options,
            "isMcq": getattr(test_response, 'is_mcq', True),
            "sectionInfo": section_info,
            "currentSection": current_section,
            "sectionProgress": section_progress,
            "examStructure": exam_structure,
            
            # Backward compatibility (snake_case)
            "test_id": test_response.test_id,
            "session_id": f"session_{test_response.test_id[:8]}",
            "user_type": user_type,
            "total_questions": test_response.total_questions,
            "time_limit": test_response.time_limit,
            "question_number": test_response.question_number,
            "question_html": test_response.question_html,
            "question_type": getattr(test_response, 'question_type', 'aptitude'),
            "is_mcq": getattr(test_response, 'is_mcq', True),
            "section_info": section_info,
            "current_section": current_section,
            "section_progress": section_progress,
            "exam_structure": exam_structure,
            
            "raw": {
                "test_id": test_response.test_id,
                "user_type": user_type,
                "total_questions": test_response.total_questions,
                "time_limit": test_response.time_limit,
                "question_number": test_response.question_number,
                "question_html": test_response.question_html,
                "question_type": getattr(test_response, 'question_type', 'aptitude'),
                "title": getattr(test_response, 'title', ''),
                "options": test_response.options,
                "is_mcq": getattr(test_response, 'is_mcq', True),
                "section_info": section_info,
                "current_section": current_section,
                "section_progress": section_progress,
                "exam_structure": exam_structure
            }
        }
        
        logger.info(f"Test started: {test_response.test_id}")
        return response
        
    except Exception as e:
        logger.error(f"Test start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/test/submit")
async def submit_answer(request_data: dict):
    """Submit answer - Frontend compatible with ALL section tracking fields"""
    try:
        test_id = request_data.get("test_id")
        question_number = request_data.get("question_number")
        answer = request_data.get("answer", "")
        
        if not test_id:
            raise ValueError("test_id is required")
        if not question_number:
            raise ValueError("question_number is required")
        
        logger.info(f"Submitting answer for test {test_id}, question {question_number}")
        response = await test_service.submit_answer(test_id, question_number, answer)
        
        if response.test_completed:
            section_scores = _serialize_object(getattr(response, 'section_scores', {}))
            section_results = _serialize_object(getattr(response, 'section_results', []))
            summary = _serialize_object(getattr(response, 'summary', {}))
            
            return {
                "testCompleted": True,
                "score": response.score,
                "totalQuestions": response.total_questions,
                "scorePercentage": getattr(response, 'score_percentage', 0),
                "analytics": getattr(response, 'analytics', ''),
                "sectionScores": section_scores,
                "sectionResults": section_results,
                "summary": summary,
                "test_completed": True,
                "total_questions": response.total_questions,
                "section_scores": section_scores,
                "section_results": section_results
            }
        else:
            next_q = response.next_question
            section_info = _serialize_object(getattr(response, 'section_info', None))
            current_section = _serialize_object(getattr(response, 'current_section', None))
            section_progress = _serialize_object(getattr(response, 'section_progress', None))
            section_just_completed = getattr(response, 'section_just_completed', None)
            next_section_starting = getattr(response, 'next_section_starting', None)
            
            return {
                "testCompleted": False,
                "nextQuestion": {
                    "questionNumber": next_q.question_number,
                    "totalQuestions": next_q.total_questions,
                    "questionHtml": next_q.question_html,
                    "questionType": getattr(next_q, 'question_type', 'mcq'),
                    "title": getattr(next_q, 'title', ''),
                    "options": next_q.options,
                    "isMcq": getattr(next_q, 'is_mcq', True),
                    "timeLimit": next_q.time_limit
                },
                "sectionInfo": section_info,
                "currentSection": current_section,
                "sectionProgress": section_progress,
                "sectionJustCompleted": section_just_completed,
                "nextSectionStarting": next_section_starting,
                "test_completed": False,
                "next_question": {
                    "question_number": next_q.question_number,
                    "total_questions": next_q.total_questions,
                    "question_html": next_q.question_html,
                    "question_type": getattr(next_q, 'question_type', 'mcq'),
                    "title": getattr(next_q, 'title', ''),
                    "options": next_q.options,
                    "is_mcq": getattr(next_q, 'is_mcq', True),
                    "time_limit": next_q.time_limit
                },
                "section_info": section_info,
                "current_section": current_section,
                "section_progress": section_progress,
                "section_just_completed": section_just_completed,
                "next_section_starting": next_section_starting
            }
        
    except Exception as e:
        logger.error(f"Answer submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/test/results/{test_id}")
async def get_test_results(test_id: str):
    try:
        results = await test_service.get_test_results(test_id)
        if not results:
            raise HTTPException(status_code=404, detail="Test results not found")
        
        return {
            "testId": test_id,
            "score": results["score"],
            "totalQuestions": results["total_questions"],
            "scorePercentage": results.get("score_percentage", 0),
            "analytics": results["analytics"],
            "timestamp": results["timestamp"],
            "pdfAvailable": True,
            "sectionScores": results.get("section_scores", {}),
            "sectionResults": results.get("section_results", []),
            "test_id": test_id,
            "total_questions": results["total_questions"],
            "section_scores": results.get("section_scores", {}),
            "section_results": results.get("section_results", [])
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/test/pdf/{test_id}")
async def download_pdf(test_id: str):
    try:
        pdf_bytes = await pdf_service.generate_test_results_pdf(test_id)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=test_results_{test_id}.pdf"}
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/test/force-complete")
async def force_complete_test(request_data: dict):
    try:
        test_id = request_data.get("test_id")
        termination_reason = request_data.get("termination_reason", "Proctoring violation")
        warnings = request_data.get("warnings", 0)
        
        if not test_id:
            raise ValueError("test_id is required")
        
        result = await test_service.force_complete_test(test_id, termination_reason, warnings)
        return {"success": result.get("status") != "error", "status": result.get("status"), "reason": result.get("reason")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/test/{test_id}/question/{question_number}")
async def get_specific_question(test_id: str, question_number: int):
    try:
        from ..core.utils import memory_manager
        import markdown
        
        test_data = memory_manager.get_test(test_id)
        if not test_data:
            raise HTTPException(status_code=404, detail="Test not found")
        
        user_type = test_data.get("user_type", "dev")
        total_questions = test_data.get("total_questions", 25)
        
        if question_number < 1 or question_number > total_questions:
            raise HTTPException(status_code=400, detail=f"Question number must be between 1 and {total_questions}")
        
        questions = test_data.get("questions", [])
        if question_number > len(questions):
            raise HTTPException(status_code=404, detail="Question not found")
        
        question = questions[question_number - 1]
        question_type = question.get("question_type", "mcq")
        is_mcq = question.get("is_mcq", True)
        options = question.get("options")
        time_limit = test_service._get_question_time_limit(question_type, user_type)
        
        question_html = question.get("question", "")
        if question_html:
            question_html = markdown.markdown(question_html, extensions=['codehilite', 'fenced_code'])
        
        section_info = test_service._get_section_info(questions, user_type)
        current_section = test_service._get_current_section(question_number, section_info)
        section_progress = test_service._get_section_progress(question_number, section_info)
        
        answers = memory_manager.get_test_answers(test_id)
        saved_answer = ""
        if answers and question_number <= len(answers):
            saved_answer = answers[question_number - 1].get("answer", "")
        
        return {
            "success": True,
            "questionNumber": question_number,
            "totalQuestions": total_questions,
            "questionHtml": question_html,
            "questionType": question_type,
            "title": question.get("title", ""),
            "options": options,
            "isMcq": is_mcq,
            "timeLimit": time_limit,
            "savedAnswer": saved_answer,
            "sectionInfo": section_info,
            "currentSection": current_section,
            "sectionProgress": section_progress,
            "question_number": question_number,
            "question_type": question_type,
            "is_mcq": is_mcq,
            "time_limit": time_limit
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get question failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/test/{test_id}/navigate")
async def navigate_to_section(test_id: str, request_data: dict):
    try:
        section_name = request_data.get("section", "").lower()
        if section_name not in ["aptitude", "mcq", "coding"]:
            raise HTTPException(status_code=400, detail="Invalid section name")
        
        from ..core.utils import memory_manager
        test_data = memory_manager.get_test(test_id)
        if not test_data:
            raise HTTPException(status_code=404, detail="Test not found")
        
        questions = test_data.get("questions", [])
        user_type = test_data.get("user_type", "dev")
        section_info = test_service._get_section_info(questions, user_type)
        
        question_number = 1
        for section in section_info.get("sections", []):
            if section["name"] == section_name:
                question_number = section["start"]
                break
        
        return await get_specific_question(test_id, question_number)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/test/{test_id}/status")
async def get_test_status(test_id: str):
    try:
        from ..core.utils import memory_manager
        test_data = memory_manager.get_test(test_id)
        if not test_data:
            raise HTTPException(status_code=404, detail="Test not found")
        
        user_type = test_data.get("user_type", "dev")
        questions = test_data.get("questions", [])
        current_q = test_data.get("current_question", 1)
        
        section_info = test_service._get_section_info(questions, user_type)
        current_section = test_service._get_current_section(current_q, section_info)
        section_progress = test_service._get_section_progress(current_q, section_info)
        answers = memory_manager.get_test_answers(test_id)
        
        return {
            "testId": test_id,
            "userType": user_type,
            "totalQuestions": test_data.get("total_questions", 25),
            "currentQuestion": current_q,
            "answeredCount": len(answers) if answers else 0,
            "sectionInfo": section_info,
            "currentSection": current_section,
            "sectionProgress": section_progress,
            "isComplete": current_q > test_data.get("total_questions", 25)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/tests")
async def get_all_tests():
    try:
        results = await test_service.get_all_tests()
        return {"count": len(results), "results": results, "timestamp": DateTimeUtils.get_current_timestamp()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/students")
async def get_students():
    try:
        students = await test_service.get_students()
        return {"count": len(students), "students": students}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/students/{student_id}/tests")
async def get_student_tests(student_id: str):
    try:
        tests = await test_service.get_student_tests(student_id)
        return {"count": len(tests), "tests": tests}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/cleanup")
async def cleanup_resources():
    try:
        result = test_service.cleanup_expired_tests()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))