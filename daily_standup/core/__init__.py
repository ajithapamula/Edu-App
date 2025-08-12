"""
Core module for Daily Standup system
Exports all essential components for clean imports
"""

from .config import config
from .database import DatabaseManager
from .ai_services import (
    SharedClientManager,
    SessionData,
    SessionStage,
    SummaryManager,
    OptimizedAudioProcessor,
    OptimizedConversationManager,
    shared_clients
)
from .tts_processor import UltraFastTTSProcessor
from .prompts import prompts

__all__ = [
    'config',
    'DatabaseManager', 
    'SharedClientManager',
    'SessionData',
    'SessionStage',
    'SummaryManager',
    'OptimizedAudioProcessor',
    'UltraFastTTSProcessor',
    'OptimizedConversationManager',
    'shared_clients',
    'prompts'
]