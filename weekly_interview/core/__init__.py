# weekly_interview/core/__init__.py
"""
Core module for Enhanced Mock Interview System
Exports all essential components for clean imports
"""

from .config import config
from .database import DatabaseManager
from .content_service import ContentService
from .ai_services import (
    shared_clients,
    SharedClientManager,
    InterviewSession,
    InterviewStage,
    ConversationExchange,
    OptimizedAudioProcessor,
    OptimizedConversationManager
)

__all__ = [
    'config',
    'DatabaseManager',
    'ContentService',
    'shared_clients',
    'SharedClientManager',
    'InterviewSession',
    'InterviewStage',
    'ConversationExchange',
    'OptimizedAudioProcessor',
    'OptimizedConversationManager'
]