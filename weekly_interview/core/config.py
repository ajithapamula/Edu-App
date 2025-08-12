# weekly_interview/core/config.py
"""
Enhanced Configuration - NO HARDCODED TTS VOICE, DYNAMIC SELECTION
Optimized for 7-day summary processing and fragment-based questioning
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

class Config:
    """Enhanced configuration class for Interview System - DYNAMIC TTS VOICE"""
    
    # =============================================================================
    # PATHS AND DIRECTORIES
    # =============================================================================
    CURRENT_DIR = Path(__file__).resolve().parent.parent  # weekly_interview directory
    AUDIO_DIR = CURRENT_DIR / "audio"
    TEMP_DIR = CURRENT_DIR / "temp"
    REPORTS_DIR = CURRENT_DIR / "reports"
    
    # =============================================================================
    # DATABASE CONFIGURATION - SAME AS DAILY STANDUP
    # =============================================================================
    MYSQL_HOST = os.getenv("MYSQL_HOST", "192.168.48.201")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "SuperDB")
    MYSQL_USER = os.getenv("MYSQL_USER", "sa")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "Welcome@123")
    
    MONGODB_HOST = os.getenv("MONGODB_HOST", "192.168.48.201")
    MONGODB_PORT = int(os.getenv("MONGODB_PORT", "27017"))
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "ml_notes")
    MONGODB_USERNAME = os.getenv("MONGODB_USERNAME", "connectly")
    MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD", "LT@connect25")
    MONGODB_AUTH_SOURCE = os.getenv("MONGODB_AUTH_SOURCE", "admin")
    
    # =============================================================================
    # COLLECTION NAMES
    # =============================================================================
    SUMMARIES_COLLECTION = os.getenv("SUMMARIES_COLLECTION", "summaries")
    INTERVIEW_RESULTS_COLLECTION = os.getenv("INTERVIEW_RESULTS_COLLECTION", "interview_results")
    
    # =============================================================================
    # ENHANCED 7-DAY CONTENT PROCESSING CONFIGURATION
    # =============================================================================
    RECENT_SUMMARIES_DAYS = int(os.getenv("RECENT_SUMMARIES_DAYS", "7"))  # 7-day window
    SUMMARIES_LIMIT = int(os.getenv("SUMMARIES_LIMIT", "10"))  # Max summaries to process
    CONTENT_SLICE_FRACTION = float(os.getenv("CONTENT_SLICE_FRACTION", "0.4"))  # 40% slice per summary
    MIN_CONTENT_LENGTH = int(os.getenv("MIN_CONTENT_LENGTH", "200"))  # Minimum content length
    
    # Enhanced fragment configuration for interviews
    MIN_INTERVIEW_FRAGMENTS = int(os.getenv("MIN_INTERVIEW_FRAGMENTS", "6"))  # Minimum fragments
    MAX_INTERVIEW_FRAGMENTS = int(os.getenv("MAX_INTERVIEW_FRAGMENTS", "12"))  # Maximum fragments
    FRAGMENT_MIN_LENGTH = int(os.getenv("FRAGMENT_MIN_LENGTH", "100"))  # Min chars per fragment
    
    # =============================================================================
    # INTERVIEW CONFIGURATION - ROUNDS BASED
    # =============================================================================
    INTERVIEW_DURATION_MINUTES = int(os.getenv("INTERVIEW_DURATION_MINUTES", "45"))  # Total duration
    QUESTIONS_PER_ROUND = int(os.getenv("QUESTIONS_PER_ROUND", "6"))  # Questions per round
    MIN_QUESTIONS_PER_ROUND = int(os.getenv("MIN_QUESTIONS_PER_ROUND", "4"))
    MAX_QUESTIONS_PER_ROUND = int(os.getenv("MAX_QUESTIONS_PER_ROUND", "8"))
    
    # Interview rounds (keep existing structure)
    ROUND_NAMES = ["greeting", "technical", "communication", "hr"]
    TOTAL_ROUNDS = len(ROUND_NAMES)
    
    # Fragment-based questioning (adapted from daily_standup)
    MIN_QUESTIONS_PER_CONCEPT = int(os.getenv("MIN_QUESTIONS_PER_CONCEPT", "1"))
    MAX_QUESTIONS_PER_CONCEPT = int(os.getenv("MAX_QUESTIONS_PER_CONCEPT", "3"))
    
    # =============================================================================
    # DYNAMIC TTS CONFIGURATION - NO HARDCODED VOICE
    # =============================================================================
    # TTS Voice preference (will be dynamically selected if not available)
    TTS_VOICE_PREFERENCE = os.getenv("TTS_VOICE", "en-US-JennyNeural")  # Preferred voice
    TTS_SPEED = os.getenv("TTS_SPEED", "+25%")  # Same as daily_standup
    TTS_CHUNK_SIZE = int(os.getenv("TTS_CHUNK_SIZE", "30"))  # Same chunking
    
    # Dynamic TTS voice selection strategy
    TTS_VOICE_SELECTION_STRATEGY = "dynamic_preference"  # Options: dynamic_preference, first_available, random
    TTS_FALLBACK_ENABLED = True  # Enable voice fallback if preferred not available
    
    @property
    def TTS_VOICE(self):
        """Dynamic TTS voice property - will be determined at runtime"""
        return self.TTS_VOICE_PREFERENCE
    
    # Audio processing settings
    MAX_RECORDING_DURATION = int(os.getenv("MAX_RECORDING_DURATION", "25"))  # Same as daily_standup
    SILENCE_THRESHOLD = int(os.getenv("SILENCE_THRESHOLD", "400"))  # Same threshold
    
    # =============================================================================
    # AI MODEL CONFIGURATION - SAME AS DAILY STANDUP
    # =============================================================================
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))  # Same as daily_standup
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "300"))  # Same as daily_standup
    
    GROQ_MODEL = "distil-whisper-large-v3-en" # Same as daily_standup
    GROQ_TIMEOUT = int(os.getenv("GROQ_TIMEOUT", "30"))
    
    # =============================================================================
    # WEBSOCKET CONFIGURATION - SAME AS DAILY STANDUP
    # =============================================================================
    WEBSOCKET_TIMEOUT = float(os.getenv("WEBSOCKET_TIMEOUT", "300.0"))  # Same timeout
    MAX_MESSAGE_SIZE = int(os.getenv("MAX_MESSAGE_SIZE", "16777216"))  # 16MB
    
    # =============================================================================
    # SESSION MANAGEMENT - SIMPLIFIED LIKE DAILY STANDUP
    # =============================================================================
    SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
    MAX_ACTIVE_SESSIONS = int(os.getenv("MAX_ACTIVE_SESSIONS", "100"))
    
    # =============================================================================
    # PERFORMANCE SETTINGS - SAME AS DAILY STANDUP
    # =============================================================================
    THREAD_POOL_MAX_WORKERS = int(os.getenv("THREAD_POOL_MAX_WORKERS", "4"))  # Same as daily_standup
    MONGO_MAX_POOL_SIZE = int(os.getenv("MONGO_MAX_POOL_SIZE", "50"))
    MONGO_SERVER_SELECTION_TIMEOUT = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT", "5000"))
    
    # =============================================================================
    # CONVERSATION SETTINGS - DAILY STANDUP STYLE
    # =============================================================================
    CONVERSATION_WINDOW_SIZE = int(os.getenv("CONVERSATION_WINDOW_SIZE", "3"))  # Same as daily_standup
    
    # =============================================================================
    # CORS SETTINGS - SAME AS DAILY STANDUP
    # =============================================================================
    CORS_ALLOW_ORIGINS = ["*"]
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_METHODS = ["*"]
    CORS_ALLOW_HEADERS = ["*"]
    
    # =============================================================================
    # APPLICATION SETTINGS
    # =============================================================================
    APP_TITLE = "Enhanced Mock Interview System"
    APP_VERSION = "3.0.0"
    APP_DESCRIPTION = "AI-powered interview system with 7-day content processing and real-time streaming"
    
    # =============================================================================
    # EVALUATION CONFIGURATION
    # =============================================================================
    EVALUATION_CRITERIA = {
        "technical_weight": 0.35,      # 35% Technical Assessment
        "communication_weight": 0.30,  # 30% Communication Skills  
        "behavioral_weight": 0.25,     # 25% Behavioral/HR
        "overall_presentation": 0.10   # 10% Overall Presentation
    }
    
    # =============================================================================
    # DYNAMIC TTS VOICE PREFERENCES (NO HARDCODED FALLBACKS)
    # =============================================================================
    TTS_VOICE_PREFERENCES = [
        # User preference first
        "TTS_VOICE_PREFERENCE",  # Will be replaced with actual preference
        # High-quality English voices in preference order
        "en-US-JennyNeural",
        "en-US-AriaNeural", 
        "en-US-GuyNeural",
        "en-US-SaraNeural",
        "en-GB-SoniaNeural",
        "en-AU-NatashaNeural",
        "en-IN-NeerjaNeural",
        "en-IN-PrabhatNeural",
    ]
    
    def get_dynamic_tts_preferences(self):
        """Get dynamic TTS voice preferences with user preference first"""
        preferences = [self.TTS_VOICE_PREFERENCE]
        preferences.extend([voice for voice in self.TTS_VOICE_PREFERENCES[1:] if voice != self.TTS_VOICE_PREFERENCE])
        return preferences
    
    # =============================================================================
    # REQUIRED API KEYS VALIDATION - SAME AS DAILY STANDUP
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
    
    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    @property
    def mysql_connection_config(self) -> dict:
        """Get MySQL connection configuration"""
        return {
            'host': self.MYSQL_HOST,
            'port': self.MYSQL_PORT,
            'database': self.MYSQL_DATABASE,
            'user': self.MYSQL_USER,
            'password': self.MYSQL_PASSWORD
        }
    
    @property
    def mongodb_connection_string(self) -> str:
        """Get MongoDB connection string"""
        from urllib.parse import quote_plus
        username = quote_plus(self.MONGODB_USERNAME)
        password = quote_plus(self.MONGODB_PASSWORD)
        return f"mongodb://{username}:{password}@{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_AUTH_SOURCE}"
    
    def get_round_config(self, round_name: str) -> dict:
        """Get configuration for specific interview round"""
        round_configs = {
            "greeting": {
                "duration_minutes": 3,
                "max_questions": 2,
                "focus": "introduction_and_rapport"
            },
            "technical": {
                "duration_minutes": 20,
                "max_questions": self.QUESTIONS_PER_ROUND,
                "focus": "technical_skills_assessment"
            },
            "communication": {
                "duration_minutes": 12,
                "max_questions": self.QUESTIONS_PER_ROUND,
                "focus": "communication_and_presentation"
            },
            "hr": {
                "duration_minutes": 10,
                "max_questions": self.QUESTIONS_PER_ROUND,
                "focus": "behavioral_and_cultural_fit"
            }
        }
        return round_configs.get(round_name, {})

# Global config instance
config = Config()

# Validate required environment variables on import
config.validate_required_env_vars()

# Ensure directories exist
for directory in [config.AUDIO_DIR, config.TEMP_DIR, config.REPORTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)