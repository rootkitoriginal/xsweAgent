"""
Gemini Integration Module
Connects to Google's Gemini AI for code analysis and insights.
"""

from .client import GeminiClient
from .analyzer import CodeAnalyzer
from .models import AnalysisResult, CodeReport

__all__ = ["GeminiClient", "CodeAnalyzer", "AnalysisResult", "CodeReport"]
