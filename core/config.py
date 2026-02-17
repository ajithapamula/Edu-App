"""
Unified Configuration Module
============================

Merged from:
- daily_standup/core/config.py
- weekend_mocktest/core/config.py
- weekly_interview/core/config.py

Supports:
- MySQL & MongoDB configs
- Daily Standup, Mock Test, Weekly Interview
- TTS (fixed + dynamic)
- AI Model settings
- WebSocket, session, test, and interview configs
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")


class Config:
    """Central configuration class for all sub-apps"""

    # =========================================================================
    # PATHS
    # =========================================================================
    CURRENT_DIR = Path(__file__).resolve().parent.parent
    AUDIO_DIR = CURRENT_DIR / "audio"
    TEMP_DIR = CURRENT_DIR / "temp"
    REPORTS_DIR = CURRENT_DIR / "reports"

    MAX_REDIRECTS_OFFTOPIC = 3
    REDIRECT_MAX_WORDS = 18
    MAX_VULGAR_STRIKES = 2
    BOUNDARY_TONE = "calm, brief, professional"

    SAFETY_SYSTEM_PREAMBLE = """
    You are a professional standup facilitator.
    Stay strictly on project/work topics.
    If the user goes off-topic: give a brief redirect (≤ 18 words) and ask one on-topic question.
    If the user uses vulgar/abusive language: do NOT repeat it; issue a short warning and restate the topic.
    After two warnings, end politely. Never generate sexual or hateful content. Tone: calm, brief, professional.
    """.strip()

    MAX_REDIRECTS_OFFTOPIC = 3
    MAX_VULGAR_STRIKES = 2
    REDIRECT_MAX_WORDS = 18
    # =========================================================================
    # MYSQL CONFIG (shared across apps)
    # =========================================================================
    MYSQL_HOST = os.getenv("MYSQL_HOST", "192.168.48.201")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "SuperDB")
    MYSQL_USER = os.getenv("MYSQL_USER", "sa")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "Welcome@123")

    @property
    def mysql_connection_config(self) -> dict:
        return {
            "host": self.MYSQL_HOST,
            "port": self.MYSQL_PORT,
            "database": self.MYSQL_DATABASE,
            "user": self.MYSQL_USER,
            "password": self.MYSQL_PASSWORD,
        }

    # =========================================================================
    # MONGODB CONFIG
    # =========================================================================
    # daily_standup + weekly_interview style
    MONGODB_HOST = os.getenv("MONGODB_HOST", "192.168.48.201")
    MONGODB_PORT = int(os.getenv("MONGODB_PORT", "27017"))
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "ml_notes")
    MONGODB_USERNAME = os.getenv("MONGODB_USERNAME", "connectly")
    MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD", "LT@connect25")
    MONGODB_AUTH_SOURCE = os.getenv("MONGODB_AUTH_SOURCE", "admin")

    # weekend_mocktest style
    MONGO_USER = os.getenv("MONGO_USER", MONGODB_USERNAME)
    MONGO_PASS = os.getenv("MONGO_PASS", MONGODB_PASSWORD)
    MONGO_HOST = os.getenv("MONGO_HOST", f"{MONGODB_HOST}:{MONGODB_PORT}")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", MONGODB_DATABASE)
    MONGO_AUTH_SOURCE = os.getenv("MONGO_AUTH_SOURCE", MONGODB_AUTH_SOURCE)

    @property
    def MONGO_CONNECTION_STRING(self) -> str:
        from urllib.parse import quote_plus
        encoded_pass = quote_plus(self.MONGO_PASS)
        return (
            f"mongodb://{self.MONGO_USER}:{encoded_pass}"
            f"@{self.MONGO_HOST}/ml_notes"
            f"?authSource=admin"
            f"&maxPoolSize={self.MONGO_MAX_POOL_SIZE}"
            f"&serverSelectionTimeoutMS={self.MONGO_SERVER_SELECTION_TIMEOUT}"
        )

    @property
    def mongodb_connection_string(self) -> str:
        """Alias for consistency with weekly_interview"""
        return self.MONGO_CONNECTION_STRING

    # in core/config.py (near other conversation settings)
    GREETING_LLM_ENABLED = os.getenv("GREETING_LLM_ENABLED", "true").lower() == "true"
    GREETING_LLM_TIMEOUT_MS = int(os.getenv("GREETING_LLM_TIMEOUT_MS", "1500"))
    GREETING_GROQ_FALLBACK = os.getenv("GREETING_GROQ_FALLBACK", "true").lower() == "true"

    # config.py
    MIN_STT_SEGMENT_MS = int(os.getenv("MIN_STT_SEGMENT_MS", "700"))
    MAX_STT_LATENCY_MS = int(os.getenv("MAX_STT_LATENCY_MS", "1600"))
    MIN_STT_SEGMENT_BYTES = int(os.getenv("MIN_STT_SEGMENT_BYTES", "8192"))
    CLIENT_SILENCE_THRESHOLD_MS = int(os.getenv("CLIENT_SILENCE_THRESHOLD_MS", "4000"))
    CLIENT_SILENCE_GRACE_MS = int(os.getenv("CLIENT_SILENCE_GRACE_MS", "250"))
    FILLER_IGNORE_MAX_TOKENS = int(os.getenv("FILLER_IGNORE_MAX_TOKENS", "2"))

    # =========================================================================
    # ADD THESE LINES TO YOUR config.py (after the CORS SETTINGS section)
    # =========================================================================

    # =========================================================================
    # AWS S3 CONFIG (for PDF storage)
    # =========================================================================
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
    AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME", "imeetpro-225220763325")
    AWS_S3_INTERVIEW_PREFIX = os.getenv("AWS_S3_INTERVIEW_PREFIX", "weekly-interviews")

    # =========================================================================
    # COLLECTION NAMES
    # =========================================================================
    SUMMARIES_COLLECTION = os.getenv("SUMMARIES_COLLECTION", "summaries")
    RESULTS_COLLECTION = os.getenv("RESULTS_COLLECTION", "daily_standup_results")
    TEST_RESULTS_COLLECTION = os.getenv("TEST_RESULTS_COLLECTION", "mock_test_results")
    INTERVIEW_RESULTS_COLLECTION = os.getenv(
        "INTERVIEW_RESULTS_COLLECTION", "interview_results"
    )

    # =========================================================================
    # DAILY STANDUP SETTINGS (UNCHANGED)
    # =========================================================================
    GREETING_EXCHANGES = int(os.getenv("GREETING_EXCHANGES", "2"))
    SUMMARY_CHUNKS = int(os.getenv("SUMMARY_CHUNKS", "8"))
    TOTAL_QUESTIONS = int(os.getenv("TOTAL_QUESTIONS", "20"))
    MIN_QUESTIONS_PER_CONCEPT = int(os.getenv("MIN_QUESTIONS_PER_CONCEPT", "1"))
    MAX_QUESTIONS_PER_CONCEPT = int(os.getenv("MAX_QUESTIONS_PER_CONCEPT", "4"))
    ESTIMATED_SECONDS_PER_QUESTION = int(
        os.getenv("ESTIMATED_SECONDS_PER_QUESTION", "180")
    )
    BASE_QUESTIONS_PER_CHUNK = int(os.getenv("BASE_QUESTIONS_PER_CHUNK", "3"))
    SILENCE_CHUNKS_THRESHOLD = 1
    SILENCE_GRACE_AFTER_GREETING_SECONDS = 4

    # =========================================================================
    # WEEKEND MOCKTEST SETTINGS (UNCHANGED)
    # =========================================================================
    QUESTIONS_PER_TEST = int(os.getenv("QUESTIONS_PER_TEST", "10"))
    DEV_TIME_LIMIT = int(os.getenv("DEV_TIME_LIMIT", "300"))
    NON_DEV_TIME_LIMIT = int(os.getenv("NON_DEV_TIME_LIMIT", "120"))
    QUESTION_CACHE_DURATION_HOURS = int(
        os.getenv("QUESTION_CACHE_DURATION_HOURS", "6")
    )
    TEST_SESSION_TIMEOUT = int(os.getenv("TEST_SESSION_TIMEOUT", "3600"))

    # =========================================================================
    # WEEKLY INTERVIEW SETTINGS (UPDATED - Time-based rounds)
    # =========================================================================
    RECENT_SUMMARIES_DAYS = int(os.getenv("RECENT_SUMMARIES_DAYS", "7"))
    SUMMARIES_LIMIT = int(os.getenv("SUMMARIES_LIMIT", "10"))
    CONTENT_SLICE_FRACTION = float(os.getenv("CONTENT_SLICE_FRACTION", "0.4"))
    MIN_CONTENT_LENGTH = int(os.getenv("MIN_CONTENT_LENGTH", "200"))

    MIN_INTERVIEW_FRAGMENTS = int(os.getenv("MIN_INTERVIEW_FRAGMENTS", "6"))
    MAX_INTERVIEW_FRAGMENTS = int(os.getenv("MAX_INTERVIEW_FRAGMENTS", "12"))
    FRAGMENT_MIN_LENGTH = int(os.getenv("FRAGMENT_MIN_LENGTH", "100"))

    # Total interview duration: 45 minutes
    INTERVIEW_DURATION_MINUTES = int(os.getenv("INTERVIEW_DURATION_MINUTES", "45"))
    
    # Time-based round durations (in seconds)
    COMMUNICATION_ROUND_DURATION = int(os.getenv("COMMUNICATION_ROUND_DURATION", "600"))  # 10 minutes
    TECHNICAL_ROUND_DURATION = int(os.getenv("TECHNICAL_ROUND_DURATION", "1200"))  # 20 minutes
    HR_ROUND_DURATION = int(os.getenv("HR_ROUND_DURATION", "900"))  # 15 minutes
    
    # Round time configuration dictionary
    ROUND_DURATIONS = {
        "communication": COMMUNICATION_ROUND_DURATION,
        "technical": TECHNICAL_ROUND_DURATION,
        "hr": HR_ROUND_DURATION,
    }
    
    # Minimum questions per round (ensure at least some questions even if time is short)
    MIN_QUESTIONS_PER_ROUND = int(os.getenv("MIN_QUESTIONS_PER_ROUND", "3"))
    MAX_QUESTIONS_PER_ROUND = int(os.getenv("MAX_QUESTIONS_PER_ROUND", "10"))
    MAX_QUESTIONS_PER_CONCEPT_WI = int(os.getenv("MAX_QUESTIONS_PER_CONCEPT_WI", "3"))

    # Round order: Communication -> Technical -> HR (no greeting round)
    ROUND_NAMES = ["communication", "technical", "hr"]
    TOTAL_ROUNDS = len(ROUND_NAMES)
    
    # Silence handling for weekly interview
    WI_SILENCE_PROMPT_THRESHOLD_SECONDS = int(os.getenv("WI_SILENCE_PROMPT_THRESHOLD_SECONDS", "10"))
    WI_MAX_SILENCE_PROMPTS = int(os.getenv("WI_MAX_SILENCE_PROMPTS", "2"))
    
    # Adaptive difficulty settings for technical round
    WI_DIFFICULTY_INCREASE_THRESHOLD = float(os.getenv("WI_DIFFICULTY_INCREASE_THRESHOLD", "0.7"))
    WI_DIFFICULTY_DECREASE_THRESHOLD = float(os.getenv("WI_DIFFICULTY_DECREASE_THRESHOLD", "0.4"))
    
    # Response quality thresholds
    WI_STRONG_ANSWER_MIN_WORDS = int(os.getenv("WI_STRONG_ANSWER_MIN_WORDS", "30"))
    WI_WEAK_ANSWER_MAX_WORDS = int(os.getenv("WI_WEAK_ANSWER_MAX_WORDS", "10"))

    # =========================================================================
    # TTS CONFIG (merged)
    # =========================================================================
    REF_AUDIO_DIR = (Path(__file__).resolve().parent.parent / "core/ref_audios")
    TTS_STREAM_ENCODING = os.getenv("TTS_STREAM_ENCODING", "wav")

    # daily_standup fixed style
    TTS_VOICE = os.getenv("TTS_VOICE", "en-IN-PrabhatNeural")
    TTS_RATE = os.getenv("TTS_RATE", "+25%")
    TTS_CHUNK_SIZE = int(os.getenv("TTS_CHUNK_SIZE", "30"))
    TTS_OVERLAP = int(os.getenv("TTS_OVERLAP", "3"))

    # weekly_interview dynamic style
    TTS_VOICE_PREFERENCE = os.getenv("TTS_VOICE_PREFERENCE", TTS_VOICE)
    TTS_SPEED = os.getenv("TTS_SPEED", "+25%")
    TTS_VOICE_SELECTION_STRATEGY = os.getenv(
        "TTS_VOICE_SELECTION_STRATEGY", "dynamic_preference"
    )
    TTS_FALLBACK_ENABLED = os.getenv("TTS_FALLBACK_ENABLED", "true").lower() == "true"

    TTS_VOICE_PREFERENCES = [
        TTS_VOICE_PREFERENCE,
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
        """Ordered voice preferences (user-preferred first)."""
        prefs = [self.TTS_VOICE_PREFERENCE]
        prefs.extend(
            [voice for voice in self.TTS_VOICE_PREFERENCES if voice != self.TTS_VOICE_PREFERENCE]
        )
        return prefs

    # =========================================================================
    # AI MODEL CONFIG
    # =========================================================================
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "300"))

    GROQ_TRANSCRIPTION_MODEL = os.getenv("GROQ_TRANSCRIPTION_MODEL", "whisper-large-v3-turbo")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    GROQ_TIMEOUT = int(os.getenv("GROQ_TIMEOUT", "60"))
    GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.1"))
    GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "3000"))

    # =========================================================================
    # WEBSOCKET / SESSION CONFIG
    # =========================================================================
    WEBSOCKET_TIMEOUT = float(os.getenv("WEBSOCKET_TIMEOUT", "300.0"))
    MAX_MESSAGE_SIZE = int(os.getenv("MAX_MESSAGE_SIZE", "16777216"))
    SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))
    MAX_ACTIVE_SESSIONS = int(os.getenv("MAX_ACTIVE_SESSIONS", "100"))

    # Hard/soft cutoff (45 minutes for full interview)
    SESSION_MAX_SECONDS = int(os.getenv("SESSION_MAX_SECONDS", "2700"))
    SESSION_SOFT_CUTOFF_SECONDS = int(os.getenv("SESSION_SOFT_CUTOFF_SECONDS", "10"))
    FINAL_ANSWER_GRACE_SECONDS = int(os.getenv("FINAL_ANSWER_GRACE_SECONDS", "0"))

    # =========================================================================
    # PERFORMANCE
    # =========================================================================
    THREAD_POOL_MAX_WORKERS = int(os.getenv("THREAD_POOL_MAX_WORKERS", "4"))
    MONGO_MAX_POOL_SIZE = int(os.getenv("MONGO_MAX_POOL_SIZE", "50"))
    MONGO_SERVER_SELECTION_TIMEOUT = int(
        os.getenv("MONGO_SERVER_SELECTION_TIMEOUT", "5000")
    )

    # =========================================================================
    # CONVERSATION
    # =========================================================================
    CONVERSATION_WINDOW_SIZE = int(os.getenv("CONVERSATION_WINDOW_SIZE", "3"))
    MAX_RECORDING_DURATION = float(os.getenv("MAX_RECORDING_DURATION", "60"))
    SILENCE_THRESHOLD = int(os.getenv("SILENCE_THRESHOLD", "400"))

    # =========================================================================
    # APP METADATA
    # =========================================================================
    APP_TITLE = "Unified Edu-App AI System"
    APP_VERSION = "2.0.0"
    APP_DESCRIPTION = "Unified AI-powered daily standup, mock test, and interview system"

    # =============================================================================
    # CORS SETTINGS
    # =============================================================================
    CORS_ALLOW_ORIGINS = ["*"]
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_METHODS = ["*"]
    CORS_ALLOW_HEADERS = ["*"]

    # =========================================================================
    # EVALUATION CONFIG (UPDATED for new weekly interview criteria)
    # =========================================================================
    EVALUATION_CRITERIA = {
        # Weekly Interview weights (5 criteria)
        "communication_weight": 0.25,
        "technical_weight": 0.30,
        "leadership_weight": 0.15,
        "behaviour_weight": 0.15,
        "confidence_weight": 0.15,
    }

    # =========================================================================
    # VALIDATION
    # =========================================================================
    def validate(self) -> dict:
        """Configuration validation"""
        issues = []

        if not os.getenv("GROQ_API_KEY"):
            issues.append("GROQ_API_KEY is required")
        if not os.getenv("OPENAI_API_KEY"):
            issues.append("OPENAI_API_KEY is required")

        if self.QUESTIONS_PER_TEST < 1 or self.QUESTIONS_PER_TEST > 20:
            issues.append("QUESTIONS_PER_TEST must be between 1 and 20")

        if not (0.1 <= self.CONTENT_SLICE_FRACTION <= 1.0):
            issues.append("CONTENT_SLICE_FRACTION must be between 0.1 and 1.0")
        
        # Validate round durations
        total_round_time = sum(self.ROUND_DURATIONS.values())
        if total_round_time != self.INTERVIEW_DURATION_MINUTES * 60:
            issues.append(f"Round durations ({total_round_time}s) don't match total interview time ({self.INTERVIEW_DURATION_MINUTES * 60}s)")

        return {"valid": len(issues) == 0, "issues": issues}


# Global config
config = Config()

# Validate immediately
validation = config.validate()
if not validation["valid"]:
    raise ValueError(f"Configuration invalid: {validation['issues']}")

# Ensure required dirs exist
for directory in [config.AUDIO_DIR, config.TEMP_DIR, config.REPORTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

QUESTION_TIMEOUT_SECONDS = 15
DEFAULT_ANSWER_TEXT = "I need more time to think about this."
AUTO_ADVANCE_ENABLED = True
MIN_AUDIO_SIZE_BYTES = 50
MAX_CLARIFICATION_ATTEMPTS = 3