# weekly_interview/__init__.py
"""
Enhanced Mock Interview System
AI-powered interview system with real-time WebSocket communication and comprehensive evaluation
"""

from .main import app
from .core.config import config

__version__ = "3.0.0"
__title__ = "Enhanced Mock Interview System"
__description__ = "AI-powered interview system with real-time WebSocket communication"

# Export main components
__all__ = [
    "app",
    "config"
]