import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Central configuration for the Weekend Mock Test system.
    Supports:
    - Weekly AI-based exams
    - Developer & Non-developer tracks
    - MongoDB summaries
    - Groq LLM evaluation
    """

    # ============================================================
    # API CONFIGURATION
    # ============================================================
    API_TITLE = "Mock Test API"
    API_DESCRIPTION = "AI-powered weekly mock testing system"
    API_VERSION = "6.1.0-weekly-exam"

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
    # How many days of summaries to consider as "weekly"
    WEEKLY_CONTEXT_DAYS = int(os.getenv("WEEKLY_CONTEXT_DAYS", "7"))

    # How many summaries max to process
    RECENT_SUMMARIES_COUNT = int(os.getenv("RECENT_SUMMARIES_COUNT", "10"))

    # Slice fraction for long summaries
    SUMMARY_SLICE_FRACTION = float(os.getenv("SUMMARY_SLICE_FRACTION", "0.4"))

    # ============================================================
    # EXAM STRUCTURE (1 HOUR WEEKLY EXAM)
    # ============================================================
    EXAM_TOTAL_MINUTES = int(os.getenv("EXAM_TOTAL_MINUTES", "60"))

    # ---- Developer exam split (must total 100) ----
    DEV_APTITUDE_PERCENT = int(os.getenv("DEV_APTITUDE_PERCENT", "30"))
    DEV_THEORY_PERCENT   = int(os.getenv("DEV_THEORY_PERCENT", "30"))
    DEV_CODING_PERCENT   = int(os.getenv("DEV_CODING_PERCENT", "40"))

    # ---- Time per question (minutes) ----
    APTITUDE_Q_MIN = int(os.getenv("APTITUDE_Q_MIN", "2"))     # Logical / reasoning
    THEORY_Q_MIN   = int(os.getenv("THEORY_Q_MIN", "2"))       # Conceptual
    CODING_Q_MIN   = int(os.getenv("CODING_Q_MIN", "10"))      # Coding tasks

    # ============================================================
    # TEST RUNTIME LIMITS
    # ============================================================
    QUESTIONS_PER_TEST = int(os.getenv("QUESTIONS_PER_TEST", "10"))

    DEV_TIME_LIMIT = int(os.getenv("DEV_TIME_LIMIT", "300"))       # per question fallback
    NON_DEV_TIME_LIMIT = int(os.getenv("NON_DEV_TIME_LIMIT", "120"))

    TEST_SESSION_TIMEOUT = int(os.getenv("TEST_SESSION_TIMEOUT", "3600"))  # 1 hour
    QUESTION_CACHE_DURATION_HOURS = int(os.getenv("QUESTION_CACHE_DURATION_HOURS", "6"))

    # ============================================================
    # GROQ AI CONFIGURATION
    # ============================================================
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_TIMEOUT = int(os.getenv("GROQ_TIMEOUT", "60"))

    # Generation parameters
    GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.7"))
    GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "3000"))

    # Retry handling
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY = int(os.getenv("RETRY_DELAY", "2"))

    # ============================================================
    # EVALUATION SETTINGS
    # ============================================================
    EVALUATION_TEMPERATURE = float(os.getenv("EVALUATION_TEMPERATURE", "0.3"))
    EVALUATION_MAX_TOKENS = int(os.getenv("EVALUATION_MAX_TOKENS", "2000"))

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

        if (
            self.DEV_APTITUDE_PERCENT
            + self.DEV_THEORY_PERCENT
            + self.DEV_CODING_PERCENT
        ) != 100:
            issues.append("DEV exam percentages must total 100")

        if not (0.1 <= self.SUMMARY_SLICE_FRACTION <= 1.0):
            issues.append("SUMMARY_SLICE_FRACTION must be between 0.1 and 1.0")

        if self.QUESTIONS_PER_TEST < 1 or self.QUESTIONS_PER_TEST > 50:
            issues.append("QUESTIONS_PER_TEST must be between 1 and 50")

        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

# ============================================================
# GLOBAL CONFIG INSTANCE
# ============================================================
config = Config()

# Validate on import (fail fast)
_validation = config.validate()
if not _validation["valid"]:
    raise ValueError(f"Configuration invalid: {_validation['issues']}")
