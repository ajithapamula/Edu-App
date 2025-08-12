"""
Configuration module for Daily Standup application
Handles all configuration values from environment variables
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from parent directory
load_dotenv(Path(__file__).parent.parent / '.env')

class Config:
    """Central configuration class"""
    
    # =============================================================================
    # PATHS AND DIRECTORIES
    # =============================================================================
    CURRENT_DIR = Path(__file__).resolve().parent.parent  # daily_standup directory
    AUDIO_DIR = CURRENT_DIR / "audio"
    TEMP_DIR = CURRENT_DIR / "temp"
    REPORTS_DIR = CURRENT_DIR / "reports"
    
    # =============================================================================
    # DATABASE CONFIGURATION - MYSQL (from your check_sql.py)
    # =============================================================================
    MYSQL_HOST = os.getenv("MYSQL_HOST", "192.168.48.201")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "SuperDB")
    MYSQL_USER = os.getenv("MYSQL_USER", "sa")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "Welcome@123")
    
    # =============================================================================
    # DATABASE CONFIGURATION - MONGODB (from your check_mongo.py)
    # =============================================================================
    MONGODB_HOST = os.getenv("MONGODB_HOST", "192.168.48.201")
    MONGODB_PORT = int(os.getenv("MONGODB_PORT", "27017"))
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "ml_notes")
    MONGODB_USERNAME = os.getenv("MONGODB_USERNAME", "connectly")
    MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD", "LT@connect25")
    MONGODB_AUTH_SOURCE = os.getenv("MONGODB_AUTH_SOURCE", "admin")
    
    # =============================================================================
    # DATABASE COLLECTION NAMES
    # =============================================================================
    SUMMARIES_COLLECTION = os.getenv("SUMMARIES_COLLECTION", "summaries")  # From your check_mongo.py
    RESULTS_COLLECTION = os.getenv("RESULTS_COLLECTION", "daily_standup_results")
    
    # =============================================================================
    # TTS CONFIGURATION
    # =============================================================================
    TTS_VOICE = "en-IN-PrabhatNeural"
    TTS_RATE = "+25%"
    TTS_CHUNK_SIZE = 30
    TTS_OVERLAP = 3
    
    # =============================================================================
    # CONVERSATION FLOW CONFIGURATION
    # =============================================================================
    GREETING_EXCHANGES = 2  # Number of greeting exchanges before technical questions
    SUMMARY_CHUNKS = 8  # Default number of summary chunks to create
    
    # =============================================================================
    # DYNAMIC QUESTIONING CONFIGURATION
    # =============================================================================
    TOTAL_QUESTIONS = 20  # Baseline hint for ratio calculation
    MIN_QUESTIONS_PER_CONCEPT = 1  # Minimum questions per concept
    MAX_QUESTIONS_PER_CONCEPT = 4  # Maximum questions per concept for balance
    ESTIMATED_SECONDS_PER_QUESTION = 180  # 3 minutes, for UI timer estimation
    BASE_QUESTIONS_PER_CHUNK = 3  # Base questions per summary chunk
    
    # =============================================================================
    # CONVERSATION SETTINGS
    # =============================================================================
    CONVERSATION_WINDOW_SIZE = 3  # Conversation history window per concept
    MAX_RECORDING_TIME = 25.0
    SILENCE_THRESHOLD = 400
    
    # =============================================================================
    # AI MODEL CONFIGURATION
    # =============================================================================
    OPENAI_MODEL = "gpt-4.1-mini"
    OPENAI_TEMPERATURE = 0.1
    OPENAI_MAX_TOKENS = 300
    GROQ_TRANSCRIPTION_MODEL = "distil-whisper-large-v3-en"
    
    # =============================================================================
    # APPLICATION SETTINGS
    # =============================================================================
    APP_TITLE = "Ultra-Fast Daily Standup System"
    APP_VERSION = "2.0.0"
    WEBSOCKET_TIMEOUT = 300.0
    
    # =============================================================================
    # PERFORMANCE SETTINGS
    # =============================================================================
    THREAD_POOL_MAX_WORKERS = 4
    MONGO_MAX_POOL_SIZE = 50
    MONGO_SERVER_SELECTION_TIMEOUT = 5000
    
    # =============================================================================
    # CORS SETTINGS
    # =============================================================================
    CORS_ALLOW_ORIGINS = ["*"]
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_METHODS = ["*"]
    CORS_ALLOW_HEADERS = ["*"]
    
    # =============================================================================
    # REQUIRED API KEYS VALIDATION
    # =============================================================================
    @staticmethod
    def validate_required_env_vars():
        """Validate that all required environment variables are set"""
        required_vars = [
            "GROQ_API_KEY",
            "OPENAI_API_KEY"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise Exception(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True

# Global config instance
config = Config()

# Validate required environment variables on import
config.validate_required_env_vars()

# Ensure directories exist
for directory in [config.AUDIO_DIR, config.TEMP_DIR, config.REPORTS_DIR]:
    directory.mkdir(exist_ok=True)