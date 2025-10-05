"""
Analytics Engine - Main analytics module.
Provides comprehensive data analysis capabilities for GitHub issues.
"""

from .strategies import (
    AnalysisResult,
    AnalysisStrategy,
    AnalysisType,
    AnalyticsEngine,
    BurndownAnalysisStrategy,
    ProductivityAnalysisStrategy,
    QualityAnalysisStrategy,
    VelocityAnalysisStrategy,
)

__all__ = [
    "AnalysisStrategy",
    "AnalysisResult",
    "AnalysisType",
    "ProductivityAnalysisStrategy",
    "VelocityAnalysisStrategy",
    "BurndownAnalysisStrategy",
    "QualityAnalysisStrategy",
    "AnalyticsEngine",
]
