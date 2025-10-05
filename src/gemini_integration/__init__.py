"""
Gemini Integration Module
Connects to Google's Gemini AI for code analysis and insights.
"""

from .analyzer import CodeAnalyzer
from .client import GeminiClient
from .models import AnalysisResult, CodeReport

__all__ = ["GeminiClient", "CodeAnalyzer", "AnalysisResult", "CodeReport"]
