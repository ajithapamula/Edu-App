# weekend_mocktest/__init__.py
"""
Mock Test Module - Production Architecture
AI-powered mock testing system with real database integration
"""

__version__ = "6.0.0-production"
__author__ = "Mock Test Team"
__description__ = "Production mock testing system with AI-powered question generation"

# Import core components for compatibility
from .core.config import config
from .main import app

# Export for main app compatibility
__all__ = ["app", "config"]