"""
Analytics Engine - Main analytics module.
Provides comprehensive data analysis capabilities for GitHub issues.
"""

from .strategies import (
    AnalysisStrategy,
    AnalysisResult,
    AnalysisType,
    ProductivityAnalysisStrategy,
    VelocityAnalysisStrategy,
    BurndownAnalysisStrategy,
    QualityAnalysisStrategy,
    AnalyticsEngine,
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
