# weekend_mocktest/api/routes.py
"""
API Routes - PRODUCTION VERSION

Includes:
- Test routes (start, submit, results, pdf)
- Warning routes (add, status, history)
- Section-wise evaluation with AI explanations
"""

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
    return {"service": "Mock Test API", "version": "8.0.0", "status": "operational"}


@router.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": DateTimeUtils.get_current_timestamp()}


# ================================================================
# TEST ROUTES
# ================================================================

@router.post("/api/test/start")
async def start_test(request_data: dict):
    """Start test - Frontend compatible with ALL fields from test_service"""
    try:
        # LOG WHAT FRONTEND SENDS
        logger.info(f"📥 RECEIVED FROM FRONTEND: {request_data}")
        
        user_type = request_data.get("user_type", "dev")
        student_id = request_data.get("student_id")
        
        # Normalize user_type
        original_user_type = user_type
        if user_type in ["developer", "dev"]:
            user_type = "dev"
        elif user_type in ["non-developer", "non_dev", "nondev", "non-dev"]:
            user_type = "non_dev"
        else:
            logger.warning(f"⚠️ Unknown user_type '{user_type}', defaulting to 'dev'")
            user_type = "dev"
        
        logger.info(f"🎯 Starting test: original_type='{original_user_type}' → normalized='{user_type}', student_id={student_id}")
        test_response = await test_service.start_test(user_type, student_id)
        
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
        }
        
        logger.info(f"✅ Test started: {test_response.test_id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Test start failed: {e}")
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
        
        logger.info(f"📝 Submitting answer for test {test_id[:8]}, question {question_number}")
        response = await test_service.submit_answer(test_id, question_number, answer)
        
        if response.test_completed:
            # Serialize all evaluation data
            section_scores = _serialize_object(getattr(response, 'section_scores', {}))
            section_results = _serialize_object(getattr(response, 'section_results', []))
            section_details = _serialize_object(getattr(response, 'section_details', {}))
            summary = _serialize_object(getattr(response, 'summary', {}))
            recommendations = getattr(response, 'recommendations', [])
            
            logger.info(f"✅ Test completed: {response.score}/{response.total_questions}")
            
            return {
                "testCompleted": True,
                "testId": test_id,
                "score": response.score,
                "totalQuestions": response.total_questions,
                "scorePercentage": getattr(response, 'score_percentage', 0),
                "analytics": getattr(response, 'analytics', ''),
                
                # Section-wise scores (summary)
                "sectionScores": section_scores,
                
                # Section-wise detailed results with AI explanations
                # Format: { "aptitude": [...], "mcq": [...], "coding": [...] }
                # Each item: { question, userAnswer, correctAnswer, isCorrect, explanation }
                "sectionDetails": section_details,
                
                "sectionResults": section_results,
                "summary": summary,
                "recommendations": recommendations,
                "warningCount": getattr(response, 'warning_count', 0),
                "terminatedByWarnings": getattr(response, 'terminated_by_warnings', False),
                "pdfAvailable": True,
                
                # snake_case compatibility
                "test_completed": True,
                "test_id": test_id,
                "total_questions": response.total_questions,
                "score_percentage": getattr(response, 'score_percentage', 0),
                "section_scores": section_scores,
                "section_details": section_details,
                "section_results": section_results,
                "warning_count": getattr(response, 'warning_count', 0),
                "terminated_by_warnings": getattr(response, 'terminated_by_warnings', False),
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
                
                # snake_case compatibility
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
            }
        
    except Exception as e:
        logger.error(f"❌ Answer submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/test/results/{test_id}")
async def get_test_results(test_id: str):
    """
    Get detailed test results with section-wise breakdown.
    
    Returns:
    - Overall score and percentage
    - sectionScores: { aptitude: {correct, total, percentage}, mcq: {...}, coding: {...} }
    - sectionDetails: Per-question breakdown with AI explanations
      {
        "aptitude": [
          {
            "questionNumber": 1,
            "question": "What is 25% of 200?",
            "userAnswer": "50",
            "correctAnswer": "50",
            "isCorrect": true,
            "explanation": "Correct! 25% of 200 = 0.25 × 200 = 50"
          },
          ...
        ],
        "mcq": [...],
        "coding": [...]
      }
    """
    try:
        results = await test_service.get_test_results(test_id)
        if not results:
            raise HTTPException(status_code=404, detail="Test results not found")
        
        section_scores = results.get("section_scores", {})
        section_details = results.get("section_details", {})
        recommendations = results.get("recommendations", [])
        
        return {
            # Test identification
            "testId": test_id,
            "test_id": test_id,
            "studentId": results.get("student_id"),
            "student_id": results.get("student_id"),
            "userType": results.get("user_type", "dev"),
            "user_type": results.get("user_type", "dev"),
            
            # Overall scores
            "score": results["score"],
            "totalQuestions": results["total_questions"],
            "total_questions": results["total_questions"],
            "scorePercentage": results.get("score_percentage", 0),
            "score_percentage": results.get("score_percentage", 0),
            
            # Section-wise scores (summary)
            "sectionScores": section_scores,
            "section_scores": section_scores,
            
            # Section-wise detailed results with AI explanations
            "sectionDetails": section_details,
            "section_details": section_details,
            
            # Evaluation report and recommendations
            "analytics": results.get("analytics", ""),
            "evaluationReport": results.get("evaluation_report", ""),
            "evaluation_report": results.get("evaluation_report", ""),
            "recommendations": recommendations,
            
            # Proctoring info
            "warningCount": results.get("warning_count", 0),
            "warning_count": results.get("warning_count", 0),
            "terminatedByWarnings": results.get("terminated_by_warnings", False),
            "terminated_by_warnings": results.get("terminated_by_warnings", False),
            
            # PDF and timestamp
            "pdfAvailable": True,
            "pdfPath": results.get("pdf_path", ""),
            "pdf_path": results.get("pdf_path", ""),
            "timestamp": results.get("timestamp"),
            "completedAt": results.get("completed_at") or results.get("timestamp"),
            "completed_at": results.get("completed_at") or results.get("timestamp"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/test/pdf/{test_id}")
async def download_pdf(test_id: str):
    """Download PDF report with section-wise breakdown and AI explanations"""
    try:
        pdf_bytes = await pdf_service.generate_test_results_pdf(test_id)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=test_results_{test_id[:8]}.pdf"}
        )
    except Exception as e:
        logger.error(f"❌ PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/test/regenerate-pdf/{test_id}")
async def regenerate_pdf(test_id: str):
    """Regenerate PDF report for a test"""
    try:
        results = await test_service.get_test_results(test_id)
        if not results:
            raise HTTPException(status_code=404, detail="Test results not found")
        
        logger.info(f"🔄 Regenerating PDF for test {test_id[:8]}...")
        
        pdf_bytes = await pdf_service.generate_test_results_pdf(test_id)
        
        return {
            "success": True,
            "message": "PDF regenerated successfully",
            "testId": test_id,
            "test_id": test_id,
            "pdfAvailable": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Regenerate PDF failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/test/force-complete")
async def force_complete_test(request_data: dict):
    """Force complete test (proctoring termination or manual submit)"""
    try:
        test_id = request_data.get("test_id")
        termination_reason = request_data.get("termination_reason", "Proctoring violation")
        warnings = request_data.get("warnings", 0)
        
        if not test_id:
            raise ValueError("test_id is required")
        
        logger.warning(f"🚨 Force completing test {test_id[:8]}: {termination_reason}")
        
        result = await test_service.force_complete_test(test_id, termination_reason, warnings)
        
        return {
            "success": result.get("status") != "error",
            "status": result.get("status"),
            "reason": result.get("reason"),
            "testId": test_id,
            "test_id": test_id,
            "score": result.get("score", 0),
            "totalQuestions": result.get("total_questions", 0),
            "total_questions": result.get("total_questions", 0),
            "sectionScores": result.get("section_scores", {}),
            "section_scores": result.get("section_scores", {}),
            "sectionDetails": result.get("section_details", {}),
            "section_details": result.get("section_details", {}),
        }
    except Exception as e:
        logger.error(f"❌ Force complete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ================================================================
# WARNING ROUTES (Proctoring - 3 warnings = termination)
# ================================================================

@router.post("/api/warnings/add")
async def add_warning(request_data: dict):
    """
    Add a proctoring warning.
    
    Warning types:
    - multiple_faces: Multiple faces detected in camera
    - object_detected: Objects like phone/book detected
    - tab_switch: Tab or window switching detected
    - face_turning: Face turned away from screen
    - face_not_visible: Face not detected in camera
    - screenshot: Screenshot attempt detected
    
    After 3 warnings, test is automatically terminated.
    """
    try:
        test_id = request_data.get("test_id")
        student_id = request_data.get("student_id")
        warning_type = request_data.get("warning_type")
        details = request_data.get("details", {})
        
        if not test_id:
            raise ValueError("test_id is required")
        if not warning_type:
            raise ValueError("warning_type is required")
        
        # Validate warning type
        valid_types = ["multiple_faces", "object_detected", "tab_switch", 
                       "face_turning", "face_not_visible", "screenshot"]
        if warning_type not in valid_types:
            raise ValueError(f"Invalid warning_type. Must be one of: {valid_types}")
        
        result = test_service.add_warning(test_id, student_id, warning_type, details)
        
        # If should terminate, force complete
        if result.get("should_terminate"):
            logger.warning(f"🚨 Max warnings reached for test {test_id[:8]}, terminating...")
            await test_service.force_complete_test(
                test_id, 
                f"Maximum warnings exceeded ({result['warning_count']} warnings)",
                result['warning_count']
            )
        
        return {
            "success": True,
            "testId": test_id,
            "warningCount": result.get("warning_count", 0),
            "maxWarnings": result.get("max_warnings", 3),
            "warningsRemaining": result.get("warnings_remaining", 0),
            "shouldTerminate": result.get("should_terminate", False),
            "warningType": warning_type,
            "message": result.get("message", "Warning recorded"),
            
            # snake_case compatibility
            "test_id": test_id,
            "warning_count": result.get("warning_count", 0),
            "max_warnings": result.get("max_warnings", 3),
            "warnings_remaining": result.get("warnings_remaining", 0),
            "should_terminate": result.get("should_terminate", False),
            "warning_type": warning_type,
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Failed to add warning: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/warnings/{test_id}")
async def get_warnings(test_id: str):
    """Get all warnings for a test with full audit trail"""
    try:
        result = test_service.get_warning_status(test_id)
        return {
            "testId": test_id,
            "warningCount": result.get("warning_count", 0),
            "maxWarnings": result.get("max_warnings", 3),
            "warningsRemaining": result.get("warnings_remaining", 0),
            "isTerminated": result.get("is_terminated", False),
            "terminationReason": result.get("termination_reason"),
            "warnings": result.get("warnings", []),
            
            # snake_case compatibility
            "test_id": test_id,
            "warning_count": result.get("warning_count", 0),
            "is_terminated": result.get("is_terminated", False),
            "termination_reason": result.get("termination_reason"),
        }
    except Exception as e:
        logger.error(f"❌ Get warnings failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/warnings/{test_id}/status")
async def get_warning_status(test_id: str):
    """
    Check if test can continue or is terminated.
    Frontend should call this before each action.
    """
    try:
        result = test_service.get_warning_status(test_id)
        return {
            "testId": test_id,
            "canContinue": not result.get("is_terminated", False),
            "isTerminated": result.get("is_terminated", False),
            "terminationReason": result.get("termination_reason"),
            "warningCount": result.get("warning_count", 0),
            "maxWarnings": 3,
            "warningsRemaining": result.get("warnings_remaining", 0),
        }
    except Exception as e:
        logger.error(f"❌ Get warning status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/warnings/types")
async def get_warning_types():
    """Get list of valid warning types for proctoring"""
    return {
        "warning_types": [
            {"type": "multiple_faces", "description": "Multiple faces detected in camera"},
            {"type": "object_detected", "description": "Objects like phone/book detected"},
            {"type": "tab_switch", "description": "Tab or window switching detected"},
            {"type": "face_turning", "description": "Face turned away from screen"},
            {"type": "face_not_visible", "description": "Face not detected in camera"},
            {"type": "screenshot", "description": "Screenshot attempt detected"},
        ],
        "max_warnings": 3,
        "note": "After 3 warnings, test is automatically terminated"
    }


# ================================================================
# STUDENT HISTORY & DASHBOARD ENDPOINTS
# ================================================================

@router.get("/api/student/{student_id}/history")
async def get_student_history(student_id: str):
    """
    Get test history for a student (for dashboard).
    
    Returns all past tests with scores, section breakdown, and PDF availability.
    """
    try:
        history = await test_service.get_student_tests(student_id)
        
        # Format for dashboard
        formatted = []
        for test in history:
            formatted.append({
                "testId": test.get("test_id"),
                "test_id": test.get("test_id"),
                "userType": test.get("user_type", "dev"),
                "user_type": test.get("user_type", "dev"),
                "score": test.get("score", 0),
                "totalQuestions": test.get("total_questions", 0),
                "total_questions": test.get("total_questions", 0),
                "scorePercentage": test.get("score_percentage", 0),
                "score_percentage": test.get("score_percentage", 0),
                "sectionScores": test.get("section_scores", {}),
                "section_scores": test.get("section_scores", {}),
                "pdfAvailable": True,
                "pdfPath": test.get("pdf_path"),
                "pdf_path": test.get("pdf_path"),
                "completedAt": test.get("completed_at") or test.get("timestamp"),
                "completed_at": test.get("completed_at") or test.get("timestamp"),
                "terminatedByWarnings": test.get("terminated_by_warnings", False),
                "terminated_by_warnings": test.get("terminated_by_warnings", False),
            })
        
        return {
            "studentId": student_id,
            "student_id": student_id,
            "count": len(formatted),
            "history": formatted
        }
        
    except Exception as e:
        logger.error(f"❌ Get student history failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/student/{student_id}/dashboard")
async def get_student_dashboard(student_id: str):
    """
    Get comprehensive dashboard data for a student.
    
    Includes:
    - Recent tests
    - Performance trends
    - Section-wise analysis across all tests
    """
    try:
        history = await test_service.get_student_tests(student_id)
        
        if not history:
            return {
                "studentId": student_id,
                "totalTests": 0,
                "recentTests": [],
                "performanceTrend": [],
                "sectionAnalysis": {},
                "averageScore": 0
            }
        
        # Calculate statistics
        total_score = sum(t.get("score", 0) for t in history)
        total_questions = sum(t.get("total_questions", 0) for t in history)
        avg_percentage = round((total_score / total_questions) * 100, 1) if total_questions > 0 else 0
        
        # Section analysis across all tests
        section_totals = {}
        for test in history:
            for section, data in test.get("section_scores", {}).items():
                if section not in section_totals:
                    section_totals[section] = {"correct": 0, "total": 0}
                section_totals[section]["correct"] += data.get("correct", 0)
                section_totals[section]["total"] += data.get("total", 0)
        
        section_analysis = {}
        for section, data in section_totals.items():
            section_analysis[section] = {
                "correct": data["correct"],
                "total": data["total"],
                "percentage": round((data["correct"] / data["total"]) * 100, 1) if data["total"] > 0 else 0
            }
        
        # Performance trend (last 10 tests)
        trend = []
        for test in history[-10:]:
            trend.append({
                "testId": test.get("test_id"),
                "percentage": test.get("score_percentage", 0),
                "date": test.get("completed_at") or test.get("timestamp")
            })
        
        return {
            "studentId": student_id,
            "student_id": student_id,
            "totalTests": len(history),
            "total_tests": len(history),
            "averageScore": avg_percentage,
            "average_score": avg_percentage,
            "recentTests": history[-5:],
            "recent_tests": history[-5:],
            "performanceTrend": trend,
            "performance_trend": trend,
            "sectionAnalysis": section_analysis,
            "section_analysis": section_analysis,
        }
        
    except Exception as e:
        logger.error(f"❌ Get student dashboard failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ================================================================
# QUESTION NAVIGATION ROUTES
# ================================================================

@router.get("/api/test/{test_id}/question/{question_number}")
async def get_specific_question(test_id: str, question_number: int):
    """Get specific question by number (for navigation)"""
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
            
            # snake_case compatibility
            "question_number": question_number,
            "total_questions": total_questions,
            "question_type": question_type,
            "is_mcq": is_mcq,
            "time_limit": time_limit,
            "saved_answer": saved_answer,
            "section_info": section_info,
            "current_section": current_section,
            "section_progress": section_progress,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get question failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/test/{test_id}/status")
async def get_test_status(test_id: str):
    """Get current test status and progress"""
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
        
        # Get warning status
        warning_status = test_service.get_warning_status(test_id)
        
        return {
            "testId": test_id,
            "userType": user_type,
            "totalQuestions": test_data.get("total_questions", 25),
            "currentQuestion": current_q,
            "answeredCount": len(answers) if answers else 0,
            "sectionInfo": section_info,
            "currentSection": current_section,
            "sectionProgress": section_progress,
            "isComplete": current_q > test_data.get("total_questions", 25),
            "warningCount": warning_status.get("warning_count", 0),
            "isTerminated": warning_status.get("is_terminated", False),
            
            # snake_case compatibility
            "test_id": test_id,
            "user_type": user_type,
            "total_questions": test_data.get("total_questions", 25),
            "current_question": current_q,
            "answered_count": len(answers) if answers else 0,
            "section_info": section_info,
            "current_section": current_section,
            "section_progress": section_progress,
            "is_complete": current_q > test_data.get("total_questions", 25),
            "warning_count": warning_status.get("warning_count", 0),
            "is_terminated": warning_status.get("is_terminated", False),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get test status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ================================================================
# ADMIN ROUTES
# ================================================================

@router.get("/api/tests")
async def get_all_tests():
    """Get all tests (admin)"""
    try:
        results = await test_service.get_all_tests()
        return {
            "count": len(results),
            "results": results,
            "timestamp": DateTimeUtils.get_current_timestamp()
        }
    except Exception as e:
        logger.error(f"❌ Get all tests failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/students")
async def get_students():
    """Get all students who have taken tests"""
    try:
        students = await test_service.get_students()
        return {"count": len(students), "students": students}
    except Exception as e:
        logger.error(f"❌ Get students failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/students/{student_id}/tests")
async def get_student_tests(student_id: str):
    """Get all tests for a specific student"""
    try:
        tests = await test_service.get_student_tests(student_id)
        return {
            "studentId": student_id,
            "student_id": student_id,
            "count": len(tests),
            "tests": tests
        }
    except Exception as e:
        logger.error(f"❌ Get student tests failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/cleanup")
async def cleanup_resources():
    """Cleanup expired tests and resources"""
    try:
        result = test_service.cleanup_expired_tests()
        return result
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/exam-info")
async def get_exam_info():
    """Get exam structure information for both tracks"""
    return {
        "developer": {
            "sections": [
                {"name": "aptitude", "questions": 10, "time_per_question": 90},
                {"name": "mcq", "questions": 10, "time_per_question": 90},
                {"name": "coding", "questions": 5, "time_per_question": 300}
            ],
            "total_questions": 25,
            "total_time_minutes": 62
        },
        "non_developer": {
            "sections": [
                {"name": "aptitude", "questions": 10, "time_per_question": 60},
                {"name": "mcq", "questions": 20, "time_per_question": 75}
            ],
            "total_questions": 30,
            "total_time_minutes": 45
        }
    }