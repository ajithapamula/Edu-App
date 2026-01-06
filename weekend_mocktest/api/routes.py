# weekend_mocktest/api/routes.py
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

@router.get("/")
async def home():
    """Home endpoint"""
    return {
        "service": "Mock Test API",
        "version": "5.0.0",
        "status": "operational"
    }

@router.get("/api/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": DateTimeUtils.get_current_timestamp()
    }

# ==================== FRONTEND COMPATIBLE ENDPOINTS ====================

@router.post("/api/test/start")
async def start_test(request_data: dict):
    """Start test - Frontend compatible with standardized response"""
    try:
        # Handle both frontend formats
        user_type = request_data.get("user_type", "dev")
        
        # Convert frontend user types to backend format
        if user_type in ["developer", "dev"]:
            user_type = "dev"
        elif user_type in ["non-developer", "non_dev"]:
            user_type = "non_dev"
        else:
            raise ValueError(f"Invalid user_type: {user_type}")
        
        logger.info(f"Starting test for user_type: {user_type}")
        
        # Start test via service
        test_response = await test_service.start_test(user_type)
        
        # Create standardized response that matches frontend expectations
        response = {
            # Primary fields (what frontend expects)
            "testId": test_response.test_id,
            "sessionId": f"session_{test_response.test_id[:8]}",
            "userType": user_type,
            "totalQuestions": test_response.total_questions,
            "timeLimit": test_response.time_limit,
            "duration": test_response.time_limit // 60,  # Convert to minutes
            
            # Current question data
            "questionNumber": test_response.question_number,
            "questionHtml": test_response.question_html,
            "options": test_response.options,
            
            # Backward compatibility fields
            "test_id": test_response.test_id,
            "session_id": f"session_{test_response.test_id[:8]}",
            "user_type": user_type,
            "total_questions": test_response.total_questions,
            "time_limit": test_response.time_limit,
            "question_number": test_response.question_number,
            "question_html": test_response.question_html,
            
            # Raw data for debugging
            "raw": {
                "test_id": test_response.test_id,
                "session_id": f"session_{test_response.test_id[:8]}",
                "user_type": user_type,
                "total_questions": test_response.total_questions,
                "time_limit": test_response.time_limit,
                "question_number": test_response.question_number,
                "question_html": test_response.question_html,
                "options": test_response.options
            }
        }
        
        logger.info(f"Test started successfully: {test_response.test_id}")
        return response
        
    except Exception as e:
        logger.error(f"Test start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/test/submit")
async def submit_answer(request_data: dict):
    """Submit answer - Frontend compatible with proper response structure"""
    try:
        # Extract data with validation
        test_id = request_data.get("test_id")
        question_number = request_data.get("question_number")
        answer = request_data.get("answer", "")
        
        if not test_id:
            raise ValueError("test_id is required")
        if not question_number:
            raise ValueError("question_number is required")
        
        logger.info(f"Submitting answer for test {test_id}, question {question_number}")
        
        # Submit via service
        response = await test_service.submit_answer(test_id, question_number, answer)
        
        # Handle test completion
        if response.test_completed:
            return {
                # Primary fields
                "testCompleted": True,
                "score": response.score,
                "totalQuestions": response.total_questions,
                "analytics": response.analytics,
                
                # Backward compatibility
                "test_completed": True,
                "total_questions": response.total_questions
            }
        else:
            # Continue with next question
            next_q = response.next_question
            return {
                # Primary fields
                "testCompleted": False,
                "nextQuestion": {
                    "questionNumber": next_q.question_number,
                    "totalQuestions": next_q.total_questions,
                    "questionHtml": next_q.question_html,
                    "options": next_q.options,
                    "timeLimit": next_q.time_limit
                },
                
                # Backward compatibility
                "test_completed": False,
                "next_question": {
                    "question_number": next_q.question_number,
                    "total_questions": next_q.total_questions,
                    "question_html": next_q.question_html,
                    "options": next_q.options,
                    "time_limit": next_q.time_limit
                }
            }
        
    except Exception as e:
        logger.error(f"Answer submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/test/results/{test_id}")
async def get_test_results(test_id: str):
    """Get test results - Frontend compatible"""
    try:
        logger.info(f"Getting results for test: {test_id}")
        
        results = await test_service.get_test_results(test_id)
        
        if not results:
            raise HTTPException(status_code=404, detail="Test results not found")
        
        # Standardized response
        return {
            # Primary fields
            "testId": test_id,
            "score": results["score"],
            "totalQuestions": results["total_questions"],
            "scorePercentage": results.get("score_percentage", 0),
            "analytics": results["analytics"],
            "timestamp": results["timestamp"],
            "pdfAvailable": True,
            
            # Backward compatibility
            "test_id": test_id,
            "total_questions": results["total_questions"],
            "pdf_available": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/test/pdf/{test_id}")
async def download_pdf(test_id: str):
    """Download PDF - Frontend compatible"""
    try:
        logger.info(f"Generating PDF for test: {test_id}")
        
        pdf_bytes = await pdf_service.generate_test_results_pdf(test_id)
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=test_results_{test_id}.pdf"}
        )
        
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

# ==================== NAVIGATION ENDPOINTS ====================

@router.get("/api/test/{test_id}/question/{question_number}")
async def get_specific_question(test_id: str, question_number: int):
    """
    Get a specific question for navigation (Previous button, Go to Section).
    Used by frontend for:
    - Previous button navigation
    - Go to Aptitude/Theory/Coding section buttons
    """
    try:
        logger.info(f"📍 Getting question {question_number} for test {test_id}")
        
        # Get test data from memory
        from ..core.utils import memory_manager
        import markdown
        
        test_data = memory_manager.get_test(test_id)
        if not test_data:
            raise HTTPException(status_code=404, detail="Test not found or expired")
        
        # Validate question number
        total_questions = test_data.get("total_questions", 25)
        if question_number < 1 or question_number > total_questions:
            raise HTTPException(
                status_code=400, 
                detail=f"Question number must be between 1 and {total_questions}"
            )
        
        # Get questions list
        questions = test_data.get("questions", [])
        if question_number > len(questions):
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Get the specific question (0-indexed)
        question = questions[question_number - 1]
        
        # Determine section based on question number
        # Aptitude: Q1-10, Theory: Q11-20, Coding: Q21-25
        if question_number <= 10:
            question_type = "aptitude"
            section_question_number = question_number
            section_total = 10
            time_limit = 120  # 2 minutes
        elif question_number <= 20:
            question_type = "theory"
            section_question_number = question_number - 10
            section_total = 10
            time_limit = 120  # 2 minutes
        else:
            question_type = "coding"
            section_question_number = question_number - 20
            section_total = 5
            time_limit = 300  # 5 minutes
        
        # Override with actual question type if available
        actual_type = question.get("question_type", question_type)
        if actual_type:
            question_type = actual_type
            time_limit = test_service._get_question_time_limit(actual_type)
        
        # Format question HTML
        question_html = question.get("question", "")
        if question_html:
            question_html = markdown.markdown(
                question_html,
                extensions=['codehilite', 'fenced_code']
            )
        
        # Get saved answer if exists
        answers = memory_manager.get_test_answers(test_id)
        saved_answer = ""
        if answers and question_number <= len(answers):
            saved_answer = answers[question_number - 1].get("answer", "")
        
        # Build response
        response = {
            "success": True,
            
            # Primary fields (camelCase for frontend)
            "questionNumber": question_number,
            "totalQuestions": total_questions,
            "questionHtml": question_html,
            "questionType": question_type,
            "title": question.get("title", ""),
            "options": question.get("options"),
            "timeLimit": time_limit,
            "sectionQuestionNumber": section_question_number,
            "sectionTotalQuestions": section_total,
            "savedAnswer": saved_answer,
            
            # Backward compatibility (snake_case)
            "question_number": question_number,
            "total_questions": total_questions,
            "question_html": question_html,
            "question_type": question_type,
            "time_limit": time_limit,
            "section_question_number": section_question_number,
            "section_total_questions": section_total,
            "saved_answer": saved_answer
        }
        
        logger.info(f"✅ Returning Q{question_number} ({question_type}) for test {test_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get question failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/test/{test_id}/navigate")
async def navigate_to_section(test_id: str, request_data: dict):
    """
    Navigate to a specific section's first question.
    Used by "Go to Aptitude", "Go to Theory", "Go to Coding" buttons.
    """
    try:
        section_name = request_data.get("section", "").lower()
        
        if section_name not in ["aptitude", "theory", "coding"]:
            raise HTTPException(status_code=400, detail="Invalid section name")
        
        logger.info(f"🧭 Navigating to {section_name} section for test {test_id}")
        
        # Get first question number for section
        section_start = {
            "aptitude": 1,
            "theory": 11,
            "coding": 21
        }
        
        question_number = section_start.get(section_name, 1)
        
        # Use the get_specific_question logic
        return await get_specific_question(test_id, question_number)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Navigation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/test/{test_id}/status")
async def get_test_status(test_id: str):
    """
    Get current test status including progress and section info.
    """
    try:
        status = await test_service.get_test_status(test_id)
        return status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Get test status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ADMIN ENDPOINTS ====================

@router.get("/api/tests")
async def get_all_tests():
    """Get all test results"""
    try:
        results = await test_service.get_all_tests()
        return {
            "count": len(results),
            "results": results,
            "timestamp": DateTimeUtils.get_current_timestamp()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/students")
async def get_students():
    """Get students list"""
    try:
        students = await test_service.get_students()
        return {
            "count": len(students),
            "students": students
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/students/{student_id}/tests")
async def get_student_tests(student_id: str):
    """Get student tests"""
    try:
        tests = await test_service.get_student_tests(student_id)
        return {"count": len(tests), "tests": tests}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/cleanup")
async def cleanup_resources():
    """Cleanup expired tests"""
    try:
        result = test_service.cleanup_expired_tests()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))