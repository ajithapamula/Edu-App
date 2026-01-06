# weekend_mocktest/core/config.py
import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Central configuration for the Weekend Mock Test system.
    
    Supports:
    - Weekly AI-based exams (1 hour)
    - Developer & Non-developer tracks
    - Question Bank for large-scale non-repetition
    - MongoDB summaries
    - Groq LLM evaluation
    """

    # ============================================================
    # API CONFIGURATION
    # ============================================================
    API_TITLE = "Mock Test API"
    API_DESCRIPTION = "AI-powered weekly mock testing system with question bank"
    API_VERSION = "7.0.0-question-bank"

    # ============================================================
    # MONGODB CONFIGURATION (PRIMARY DATA SOURCE)
    # ============================================================
    MONGO_USER = os.getenv("MONGO_USER", "connectly")
    MONGO_PASS = os.getenv("MONGO_PASS", "LT@connect25")
    MONGO_HOST = os.getenv("MONGO_HOST", "192.168.48.201:27017")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "test")
    MONGO_AUTH_SOURCE = os.getenv("MONGO_AUTH_SOURCE", "admin")

    @property
    def MONGO_CONNECTION_STRING(self) -> str:
        encoded_pass = quote_plus(self.MONGO_PASS)
        return f"mongodb://{self.MONGO_USER}:{encoded_pass}@{self.MONGO_HOST}/{self.MONGO_AUTH_SOURCE}"

    # MongoDB collections
    SUMMARIES_COLLECTION = "summaries"
    TEST_RESULTS_COLLECTION = "mock_test_results"
    QUESTION_BANK_COLLECTION = "question_bank"
    STUDENT_QUESTION_HISTORY_COLLECTION = "student_question_history"

    # ============================================================
    # MYSQL CONFIGURATION (STUDENT METADATA)
    # ============================================================
    DB_CONFIG = {
        "HOST": os.getenv("MYSQL_HOST", "192.168.48.201"),
        "PORT": int(os.getenv("MYSQL_PORT", "3306")),
        "DATABASE": os.getenv("MYSQL_DATABASE", "SuperDB"),
        "USER": os.getenv("MYSQL_USER", "sa"),
        "PASSWORD": os.getenv("MYSQL_PASSWORD", "Welcome@123"),
    }

    # ============================================================
    # WEEKLY CONTENT SETTINGS
    # ============================================================
    WEEKLY_CONTEXT_DAYS = int(os.getenv("WEEKLY_CONTEXT_DAYS", "7"))
    RECENT_SUMMARIES_COUNT = int(os.getenv("RECENT_SUMMARIES_COUNT", "10"))
    SUMMARY_SLICE_FRACTION = float(os.getenv("SUMMARY_SLICE_FRACTION", "1.0"))

    # ============================================================
    # DEVELOPER EXAM STRUCTURE
    # 10 Aptitude + 10 MCQ + 5 Coding = 25 questions
    # Total time: ~62 minutes (1 hour 2 minutes)
    # ============================================================
    EXAM_TOTAL_MINUTES = int(os.getenv("EXAM_TOTAL_MINUTES", "62"))

    # ---- Fixed question counts ----
    DEV_APTITUDE_COUNT_FIXED = int(os.getenv("DEV_APTITUDE_COUNT", "10"))   # 10 aptitude
    DEV_MCQ_COUNT_FIXED = int(os.getenv("DEV_MCQ_COUNT", "10"))             # 10 MCQ (changed from theory)
    DEV_CODING_COUNT_FIXED = int(os.getenv("DEV_CODING_COUNT", "5"))        # 5 coding

    # ---- Time per question (in minutes) ----
    APTITUDE_TIME_PER_Q = int(os.getenv("APTITUDE_TIME_PER_Q", "2"))      # 2 min per aptitude
    MCQ_TIME_PER_Q = int(os.getenv("MCQ_TIME_PER_Q", "2"))                # 2 min per MCQ (changed from theory)
    CODING_TIME_PER_Q = int(os.getenv("CODING_TIME_PER_Q", "4"))          # 4 min per coding

    # ============================================================
    # NON-DEVELOPER EXAM STRUCTURE
    # 10 Aptitude (10 min) + 20 MCQ (35 min) = 30 questions, 45 minutes
    # ============================================================
    NON_DEV_APTITUDE_COUNT = int(os.getenv("NON_DEV_APTITUDE_COUNT", "10"))
    NON_DEV_MCQ_COUNT = int(os.getenv("NON_DEV_MCQ_COUNT", "20"))
    NON_DEV_APTITUDE_TIME_PER_Q = int(os.getenv("NON_DEV_APTITUDE_TIME_PER_Q", "1"))
    NON_DEV_MCQ_TIME_PER_Q = int(os.getenv("NON_DEV_MCQ_TIME_PER_Q", "1"))
    NON_DEV_TOTAL_QUESTIONS = int(os.getenv("NON_DEV_TOTAL_QUESTIONS", "30"))
    NON_DEV_TOTAL_MINUTES = int(os.getenv("NON_DEV_TOTAL_MINUTES", "45"))

    # ---- Percentage (kept for backward compatibility) ----
    DEV_APTITUDE_PERCENT = int(os.getenv("DEV_APTITUDE_PERCENT", "40"))
    DEV_MCQ_PERCENT = int(os.getenv("DEV_MCQ_PERCENT", "40"))             # Changed from theory
    DEV_CODING_PERCENT = int(os.getenv("DEV_CODING_PERCENT", "20"))

    # ============================================================
    # QUESTION COUNTS (FIXED VALUES)
    # ============================================================
    @property
    def DEV_APTITUDE_MINUTES(self) -> int:
        """Minutes allocated for aptitude section"""
        return self.DEV_APTITUDE_COUNT_FIXED * self.APTITUDE_TIME_PER_Q
    
    @property
    def DEV_MCQ_MINUTES(self) -> int:
        """Minutes allocated for MCQ section"""
        return self.DEV_MCQ_COUNT_FIXED * self.MCQ_TIME_PER_Q
    
    @property
    def DEV_CODING_MINUTES(self) -> int:
        """Minutes allocated for coding section"""
        return self.DEV_CODING_COUNT_FIXED * self.CODING_TIME_PER_Q
    
    @property
    def DEV_APTITUDE_COUNT(self) -> int:
        """Number of aptitude questions - FIXED at 10"""
        return self.DEV_APTITUDE_COUNT_FIXED
    
    @property
    def DEV_MCQ_COUNT(self) -> int:
        """Number of MCQ questions - FIXED at 10"""
        return self.DEV_MCQ_COUNT_FIXED
    
    @property
    def DEV_CODING_COUNT(self) -> int:
        """Number of coding questions - FIXED at 5"""
        return self.DEV_CODING_COUNT_FIXED
    
    @property
    def DEV_TOTAL_QUESTIONS(self) -> int:
        """Total developer questions: 10 + 10 + 5 = 25"""
        return self.DEV_APTITUDE_COUNT + self.DEV_MCQ_COUNT + self.DEV_CODING_COUNT

    # ============================================================
    # QUESTION BANK SETTINGS (LARGE SCALE)
    # ============================================================
    MIN_BANK_APTITUDE = int(os.getenv("MIN_BANK_APTITUDE", "100"))
    MIN_BANK_MCQ = int(os.getenv("MIN_BANK_MCQ", "100"))                  # Changed from MIN_BANK_THEORY
    MIN_BANK_CODING = int(os.getenv("MIN_BANK_CODING", "50"))
    MIN_BANK_NON_DEV = int(os.getenv("MIN_BANK_NON_DEV", "150"))

    BATCH_SIZE_APTITUDE = int(os.getenv("BATCH_SIZE_APTITUDE", "20"))
    BATCH_SIZE_MCQ = int(os.getenv("BATCH_SIZE_MCQ", "20"))              # Changed from BATCH_SIZE_THEORY
    BATCH_SIZE_CODING = int(os.getenv("BATCH_SIZE_CODING", "10"))
    BATCH_SIZE_NON_DEV = int(os.getenv("BATCH_SIZE_NON_DEV", "30"))

    QUESTION_EXPIRY_DAYS = int(os.getenv("QUESTION_EXPIRY_DAYS", "30"))
    QUESTION_MAX_USAGE = int(os.getenv("QUESTION_MAX_USAGE", "500"))

    # ============================================================
    # LEGACY SETTINGS (BACKWARD COMPATIBILITY)
    # ============================================================
    QUESTIONS_PER_TEST = int(os.getenv("QUESTIONS_PER_TEST", "10"))
    DEV_TIME_LIMIT = int(os.getenv("DEV_TIME_LIMIT", "300"))
    NON_DEV_TIME_LIMIT = int(os.getenv("NON_DEV_TIME_LIMIT", "60"))
    TEST_SESSION_TIMEOUT = int(os.getenv("TEST_SESSION_TIMEOUT", "3600"))
    QUESTION_CACHE_DURATION_HOURS = int(os.getenv("QUESTION_CACHE_DURATION_HOURS", "6"))

    # ============================================================
    # GROQ AI CONFIGURATION
    # ============================================================
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_MCQ_MODEL = os.getenv("GROQ_MCQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_TIMEOUT = int(os.getenv("GROQ_TIMEOUT", "90"))
    GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.2"))
    GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "6000"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY = int(os.getenv("RETRY_DELAY", "2"))

    # ============================================================
    # EVALUATION SETTINGS
    # ============================================================
    EVALUATION_TEMPERATURE = float(os.getenv("EVALUATION_TEMPERATURE", "0.3"))
    EVALUATION_MAX_TOKENS = int(os.getenv("EVALUATION_MAX_TOKENS", "8000"))

    # ============================================================
    # VALIDATION
    # ============================================================
    def validate(self) -> dict:
        issues = []

        if not self.GROQ_API_KEY:
            issues.append("GROQ_API_KEY is required")

        if not self.MONGO_USER or not self.MONGO_PASS:
            issues.append("MongoDB credentials missing")

        if self.EXAM_TOTAL_MINUTES <= 0:
            issues.append("EXAM_TOTAL_MINUTES must be > 0")

        if (self.DEV_APTITUDE_PERCENT + self.DEV_MCQ_PERCENT + self.DEV_CODING_PERCENT) != 100:
            issues.append("DEV exam percentages must total 100")

        if not (0.1 <= self.SUMMARY_SLICE_FRACTION <= 1.0):
            issues.append("SUMMARY_SLICE_FRACTION must be between 0.1 and 1.0")

        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

    def get_exam_structure(self, user_type: str = "dev") -> dict:
        """Get exam structure summary for given user type"""
        if user_type == "dev":
            return {
                "total_time_minutes": self.EXAM_TOTAL_MINUTES,
                "sections": {
                    "aptitude": {
                        "percentage": self.DEV_APTITUDE_PERCENT,
                        "minutes": self.DEV_APTITUDE_MINUTES,
                        "question_count": self.DEV_APTITUDE_COUNT,
                        "time_per_question_sec": self.APTITUDE_TIME_PER_Q * 60
                    },
                    "mcq": {  # Changed from "theory"
                        "percentage": self.DEV_MCQ_PERCENT,
                        "minutes": self.DEV_MCQ_MINUTES,
                        "question_count": self.DEV_MCQ_COUNT,
                        "time_per_question_sec": self.MCQ_TIME_PER_Q * 60
                    },
                    "coding": {
                        "percentage": self.DEV_CODING_PERCENT,
                        "minutes": self.DEV_CODING_MINUTES,
                        "question_count": self.DEV_CODING_COUNT,
                        "time_per_question_sec": self.CODING_TIME_PER_Q * 60
                    }
                },
                "total_questions": self.DEV_TOTAL_QUESTIONS
            }
        else:
            # Non-developer: Aptitude (10) + MCQ (20) = 30 questions, 45 minutes
            return {
                "total_time_minutes": self.NON_DEV_TOTAL_MINUTES,
                "sections": {
                    "aptitude": {
                        "percentage": 33,
                        "minutes": self.NON_DEV_APTITUDE_COUNT * self.NON_DEV_APTITUDE_TIME_PER_Q,
                        "question_count": self.NON_DEV_APTITUDE_COUNT,
                        "time_per_question_sec": self.NON_DEV_APTITUDE_TIME_PER_Q * 60
                    },
                    "mcq": {
                        "percentage": 67,
                        "minutes": self.NON_DEV_TOTAL_MINUTES - (self.NON_DEV_APTITUDE_COUNT * self.NON_DEV_APTITUDE_TIME_PER_Q),
                        "question_count": self.NON_DEV_MCQ_COUNT,
                        "time_per_question_sec": self.NON_DEV_MCQ_TIME_PER_Q * 60
                    }
                },
                "total_questions": self.NON_DEV_TOTAL_QUESTIONS
            }

# ============================================================
# GLOBAL CONFIG INSTANCE
# ============================================================
config = Config()

# Validate on import (fail fast)
_validation = config.validate()
if not _validation["valid"]:
    raise ValueError(f"Configuration invalid: {_validation['issues']}")

# Log exam structure on startup
import logging
logger = logging.getLogger(__name__)
logger.info(f"📊 Developer Exam: {config.DEV_APTITUDE_COUNT} aptitude + {config.DEV_MCQ_COUNT} mcq + {config.DEV_CODING_COUNT} coding = {config.DEV_TOTAL_QUESTIONS} questions in {config.EXAM_TOTAL_MINUTES} min")
logger.info(f"📊 Non-Dev Exam: {config.NON_DEV_APTITUDE_COUNT} aptitude + {config.NON_DEV_MCQ_COUNT} MCQ = {config.NON_DEV_TOTAL_QUESTIONS} questions in {config.NON_DEV_TOTAL_MINUTES} min")