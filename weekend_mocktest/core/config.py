# weekend_mocktest/core/config.py
import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Streamlined configuration for production-ready mock test system"""
    
    # ==================== API Configuration ====================
    API_TITLE = "Mock Test API"
    API_DESCRIPTION = "AI-powered mock testing system"
    API_VERSION = "6.0.0-production"
    
    # ==================== Database Configuration ====================
    # MongoDB (Primary database) - Updated with working credentials
    MONGO_USER = os.getenv("MONGO_USER", "connectly")
    MONGO_PASS = os.getenv("MONGO_PASS", "LT@connect25")
    MONGO_HOST = os.getenv("MONGO_HOST", "192.168.48.201:27017")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "ml_notes")  # Updated to correct DB
    MONGO_AUTH_SOURCE = os.getenv("MONGO_AUTH_SOURCE", "admin")  # Updated to admin
    
    @property
    def MONGO_CONNECTION_STRING(self) -> str:
        encoded_pass = quote_plus(self.MONGO_PASS)
        return f"mongodb://{self.MONGO_USER}:{encoded_pass}@{self.MONGO_HOST}/admin"
    
    # MySQL Server (Student data) - Updated with working credentials
    DB_CONFIG = {
        "HOST": os.getenv("MYSQL_HOST", "192.168.48.201"),
        "PORT": os.getenv("MYSQL_PORT", "3306"),
        "DATABASE": os.getenv("MYSQL_DATABASE", "SuperDB"),
        "USER": os.getenv("MYSQL_USER", "sa"),
        "PASSWORD": os.getenv("MYSQL_PASSWORD", "Welcome@123"),
    }
    
    # Collections - Updated with working collection names
    SUMMARIES_COLLECTION = "summaries"  # Updated to correct collection
    TEST_RESULTS_COLLECTION = "mock_test_results"
    
    # ==================== Content Processing ====================
    RECENT_SUMMARIES_COUNT = int(os.getenv("RECENT_SUMMARIES_COUNT", "10"))
    SUMMARY_SLICE_FRACTION = float(os.getenv("SUMMARY_SLICE_FRACTION", "0.4"))
    
    # ==================== Test Configuration ====================
    QUESTIONS_PER_TEST = int(os.getenv("QUESTIONS_PER_TEST", "10"))
    DEV_TIME_LIMIT = int(os.getenv("DEV_TIME_LIMIT", "300"))  # 5 minutes
    NON_DEV_TIME_LIMIT = int(os.getenv("NON_DEV_TIME_LIMIT", "120"))  # 2 minutes
    
    # Cache and session management
    QUESTION_CACHE_DURATION_HOURS = int(os.getenv("QUESTION_CACHE_DURATION_HOURS", "6"))
    TEST_SESSION_TIMEOUT = int(os.getenv("TEST_SESSION_TIMEOUT", "3600"))  # 1 hour
    
    # ==================== AI Service Configuration ====================
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_TIMEOUT = int(os.getenv("GROQ_TIMEOUT", "60"))
    GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.7"))
    GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "3000"))
    
    # Generation settings
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY = int(os.getenv("RETRY_DELAY", "2"))
    
    # ==================== Evaluation Configuration ====================
    EVALUATION_TEMPERATURE = float(os.getenv("EVALUATION_TEMPERATURE", "0.3"))
    EVALUATION_MAX_TOKENS = int(os.getenv("EVALUATION_MAX_TOKENS", "2000"))
    
    # ==================== Validation ====================
    def validate(self) -> dict:
        """Validate configuration"""
        issues = []
        
        if not self.GROQ_API_KEY:
            issues.append("GROQ_API_KEY is required")
        
        if not self.MONGO_USER or not self.MONGO_PASS:
            issues.append("MongoDB credentials are required")
        
        if self.QUESTIONS_PER_TEST < 1 or self.QUESTIONS_PER_TEST > 20:
            issues.append("QUESTIONS_PER_TEST must be between 1 and 20")
        
        if not (0.1 <= self.SUMMARY_SLICE_FRACTION <= 1.0):
            issues.append("SUMMARY_SLICE_FRACTION must be between 0.1 and 1.0")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

# Global configuration
config = Config()

# Validate on import
validation = config.validate()
if not validation["valid"]:
    raise ValueError(f"Configuration invalid: {validation['issues']}")