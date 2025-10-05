"""
Gemini Integration Module
Enhanced AI integration with Google's Gemini 2.5 Flash for comprehensive analysis.
Provides code analysis, issue intelligence, trend prediction, sentiment analysis,
priority recommendations, and collaboration insights.
"""

from .analyzer import CodeAnalyzer, GeminiAnalyzer
from .client import GeminiClient
from .models import (
    AIAnalysisRequest,
    AIAnalysisResult,
    AIConfig,
    AnalysisResult,
    AnalysisStatus,
    AnalysisType,
    CodeReport,
    CodeSnippet,
    CollaborationInsights,
    IssueInsightResult,
    PriorityLevel,
    PriorityRecommendation,
    PromptTemplate,
    SafetyFilter,
    SentimentResult,
    SentimentType,
    Suggestion,
    TrendForecast,
)

__all__ = [
    # Client
    "GeminiClient",
    # Analyzers
    "GeminiAnalyzer",
    "CodeAnalyzer",
    # Core Models
    "AnalysisResult",
    "AnalysisStatus",
    "AnalysisType",
    "CodeReport",
    "CodeSnippet",
    "Suggestion",
    # Analysis Results
    "IssueInsightResult",
    "TrendForecast",
    "SentimentResult",
    "SentimentType",
    "PriorityRecommendation",
    "PriorityLevel",
    "CollaborationInsights",
    # Request/Response
    "AIAnalysisRequest",
    "AIAnalysisResult",
    # Configuration
    "AIConfig",
    "PromptTemplate",
    "SafetyFilter",
]
