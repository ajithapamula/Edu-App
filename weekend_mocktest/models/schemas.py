# weekend_mocktest/models/schemas.py
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
import uuid

class StartTestRequest(BaseModel):
    """Request model for starting a test"""
    user_type: str = Field(..., description="User type: 'dev' or 'non_dev'")
    
    @validator('user_type')
    def validate_user_type(cls, v):
        if v not in ['dev', 'non_dev']:
            raise ValueError("user_type must be 'dev' or 'non_dev'")
        return v

class SubmitAnswerRequest(BaseModel):
    """Request model for submitting an answer"""
    test_id: str = Field(..., description="Test ID")
    question_number: int = Field(..., ge=1, description="Question number (1-based)")
    answer: str = Field(..., min_length=1, description="Answer text or option index")
    
    @validator('test_id')
    def validate_test_id(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError("Invalid test_id format")
        return v
    
    @validator('answer')
    def validate_answer(cls, v):
        if not v or not v.strip():
            raise ValueError("Answer cannot be empty")
        return v.strip()

class NextQuestionResponse(BaseModel):
    """Response model for next question"""
    question_number: int = Field(..., description="Current question number")
    total_questions: int = Field(..., description="Total questions in test")
    question_html: str = Field(..., description="Question content in HTML")
    options: Optional[List[str]] = Field(None, description="Options for MCQ (non_dev only)")
    time_limit: int = Field(..., description="Time limit in seconds")

class TestResponse(BaseModel):
    """Response model for test start"""
    test_id: str = Field(..., description="Unique test identifier")
    user_type: str = Field(..., description="User type for the test")
    question_number: int = Field(..., description="Current question number")
    total_questions: int = Field(..., description="Total questions in test")
    question_html: str = Field(..., description="Question content in HTML")
    options: Optional[List[str]] = Field(None, description="Options for MCQ")
    time_limit: int = Field(..., description="Time limit per question in seconds")

class SubmitAnswerResponse(BaseModel):
    """Response model for answer submission"""
    test_completed: bool = Field(..., description="Whether the test is completed")
    next_question: Optional[NextQuestionResponse] = Field(None, description="Next question data")
    score: Optional[int] = Field(None, description="Final score (if completed)")
    total_questions: Optional[int] = Field(None, description="Total questions (if completed)")
    analytics: Optional[str] = Field(None, description="Evaluation analytics (if completed)")

class TestResultsResponse(BaseModel):
    """Response model for test results"""
    test_id: str = Field(..., description="Test identifier")
    score: int = Field(..., description="Total correct answers")
    total_questions: int = Field(..., description="Total questions in test")
    score_percentage: float = Field(..., description="Score as percentage")
    analytics: str = Field(..., description="Detailed evaluation report")
    timestamp: float = Field(..., description="Completion timestamp")
    pdf_available: bool = Field(True, description="Whether PDF download is available")

class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Status message")
    timestamp: float = Field(..., description="Health check timestamp")
    active_tests: int = Field(..., description="Number of active tests")

class ErrorResponse(BaseModel):
    """Response model for errors"""
    error: str = Field(..., description="Error message")
    component: Optional[str] = Field(None, description="Component that failed")
    suggested_action: Optional[str] = Field(None, description="Suggested action")
    timestamp: float = Field(..., description="Error timestamp")

class StudentResponse(BaseModel):
    """Response model for student data"""
    Student_ID: int = Field(..., description="Student ID")
    name: str = Field(..., description="Student name")

class StudentsListResponse(BaseModel):
    """Response model for students list"""
    count: int = Field(..., description="Number of students")
    students: List[StudentResponse] = Field(..., description="List of students")

class TestSummaryResponse(BaseModel):
    """Response model for test summary"""
    test_id: str = Field(..., description="Test identifier")
    name: str = Field(..., description="Student name")
    score: int = Field(..., description="Score achieved")
    total_questions: int = Field(..., description="Total questions")
    score_percentage: float = Field(..., description="Score percentage")
    timestamp: float = Field(..., description="Test timestamp")
    user_type: str = Field(..., description="Test user type")

class TestsListResponse(BaseModel):
    """Response model for tests list"""
    count: int = Field(..., description="Number of tests")
    results: List[TestSummaryResponse] = Field(..., description="List of test results")
    timestamp: float = Field(..., description="Response timestamp")

class SystemStatusResponse(BaseModel):
    """Response model for system status"""
    api_status: str = Field(..., description="API status")
    timestamp: float = Field(..., description="Status check timestamp")
    active_tests: int = Field(..., description="Active tests count")
    groq_available: bool = Field(..., description="Groq AI service availability")
    mongodb_available: bool = Field(..., description="MongoDB availability")
    version: str = Field(..., description="API version")

class CleanupResponse(BaseModel):
    """Response model for cleanup operations"""
    message: str = Field(..., description="Cleanup result message")
    tests_cleaned: int = Field(..., description="Number of tests cleaned")
    active_tests: int = Field(..., description="Remaining active tests")
    timestamp: float = Field(..., description="Cleanup timestamp")

class ValidationResponse(BaseModel):
    """Response model for validation operations"""
    valid: bool = Field(..., description="Whether validation passed")
    issues: List[str] = Field(..., description="List of validation issues")
    config_loaded: bool = Field(..., description="Whether config loaded successfully")

# Internal models for data processing
class QuestionData(BaseModel):
    """Internal model for question data"""
    question_number: int = Field(..., description="Question number")
    title: str = Field("", description="Question title")
    difficulty: str = Field("Medium", description="Question difficulty")
    type: str = Field("General", description="Question type")
    question: str = Field(..., description="Question content")
    options: Optional[List[str]] = Field(None, description="MCQ options")

class AnswerData(BaseModel):
    """Internal model for answer data"""
    question_number: int = Field(..., description="Question number")
    question: str = Field(..., description="Question content")
    answer: str = Field(..., description="User answer")
    options: List[str] = Field(default_factory=list, description="Available options")
    correct: Optional[bool] = Field(None, description="Whether answer is correct")
    feedback: Optional[str] = Field(None, description="Feedback for answer")
    submitted_at: float = Field(..., description="Submission timestamp")

class EvaluationResult(BaseModel):
    """Internal model for evaluation results"""
    total_correct: int = Field(..., description="Number of correct answers")
    scores: List[int] = Field(..., description="Scores for each question (0 or 1)")
    feedbacks: List[str] = Field(..., description="Feedback for each question")
    evaluation_report: str = Field(..., description="Complete evaluation report")

class TestData(BaseModel):
    """Internal model for test data"""
    user_type: str = Field(..., description="Test user type")
    total_questions: int = Field(..., description="Total questions")
    current_question: int = Field(1, description="Current question number")
    questions: List[QuestionData] = Field(..., description="All test questions")
    created_at: float = Field(..., description="Test creation timestamp")
    started_at: float = Field(..., description="Test start timestamp")

class CacheData(BaseModel):
    """Internal model for cached data"""
    questions: List[QuestionData] = Field(..., description="Cached questions")
    created_at: float = Field(..., description="Cache creation timestamp")

class DatabaseDocument(BaseModel):
    """Internal model for database documents"""
    test_id: str = Field(..., description="Test identifier")
    timestamp: float = Field(..., description="Document timestamp")
    Student_ID: int = Field(..., description="Student ID")
    name: str = Field(..., description="Student name")
    session_id: str = Field(..., description="Session ID")
    user_type: str = Field(..., description="User type")
    score: int = Field(..., description="Test score")
    total_questions: int = Field(..., description="Total questions")
    score_percentage: float = Field(..., description="Score percentage")
    evaluation_report: str = Field(..., description="Evaluation report")
    conversation_pairs: List[Dict[str, Any]] = Field(..., description="Q&A pairs")
    test_completed: bool = Field(True, description="Test completion status")

# Configuration models
class DatabaseConfig(BaseModel):
    """Configuration model for database settings"""
    mongo_connection_string: str = Field(..., description="MongoDB connection string")
    sql_connection_string: str = Field(..., description="SQL Server connection string")
    summaries_collection: str = Field(..., description="Summaries collection name")
    results_collection: str = Field(..., description="Results collection name")

class AIConfig(BaseModel):
    """Configuration model for AI settings"""
    model_name: str = Field(..., description="LLM model name")
    timeout: int = Field(..., description="Request timeout")
    temperature: float = Field(..., description="Generation temperature")
    max_tokens: int = Field(..., description="Maximum tokens")
    top_p: float = Field(..., description="Top-p sampling parameter")

class ContentConfig(BaseModel):
    """Configuration model for content settings"""
    summaries_count: int = Field(..., description="Number of summaries to fetch")
    slice_fraction: float = Field(..., description="Fraction of content to slice")
    questions_per_test: int = Field(..., description="Questions per test")
    cache_duration_hours: int = Field(..., description="Cache duration in hours")