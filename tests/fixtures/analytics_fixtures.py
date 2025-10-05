"""
Fixtures for analytics testing.

Provides pre-configured analytics components for testing.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.analytics.engine import AnalyticsEngine, AnalyticsConfiguration
from src.analytics.strategies import (
    ProductivityAnalysisStrategy,
    VelocityAnalysisStrategy,
    BurndownAnalysisStrategy,
    QualityAnalysisStrategy
)
from tests.utils.test_data_builder import create_sample_issues


@pytest.fixture
def analytics_config():
    """Provide standard analytics configuration."""
    return AnalyticsConfiguration(
        minimum_issues=5,
        velocity_calculation_period=14,
        quality_weight=0.7
    )


@pytest.fixture
def analytics_config_strict():
    """Provide strict analytics configuration for testing edge cases."""
    return AnalyticsConfiguration(
        minimum_issues=10,
        velocity_calculation_period=7,
        quality_weight=0.9
    )


@pytest.fixture
async def analytics_engine():
    """Provide configured analytics engine."""
    from src.analytics.engine import create_analytics_engine
    engine = await create_analytics_engine()
    return engine


@pytest.fixture
def productivity_strategy():
    """Provide productivity analysis strategy."""
    return ProductivityAnalysisStrategy()


@pytest.fixture
def velocity_strategy():
    """Provide velocity analysis strategy."""
    return VelocityAnalysisStrategy()


@pytest.fixture
def burndown_strategy():
    """Provide burndown analysis strategy."""
    return BurndownAnalysisStrategy()


@pytest.fixture
def quality_strategy():
    """Provide quality analysis strategy."""
    return QualityAnalysisStrategy()


@pytest.fixture
def all_strategies():
    """Provide all analytics strategies."""
    return {
        "productivity": ProductivityAnalysisStrategy(),
        "velocity": VelocityAnalysisStrategy(),
        "burndown": BurndownAnalysisStrategy(),
        "quality": QualityAnalysisStrategy()
    }


@pytest.fixture
def sample_issues_small():
    """Provide small sample of issues (10 issues)."""
    return create_sample_issues(total=10, open_ratio=0.6)


@pytest.fixture
def sample_issues_medium():
    """Provide medium sample of issues (50 issues)."""
    return create_sample_issues(total=50, open_ratio=0.5)


@pytest.fixture
def sample_issues_large():
    """Provide large sample of issues (200 issues)."""
    return create_sample_issues(total=200, open_ratio=0.4)


@pytest.fixture
def sample_issues_all_open():
    """Provide issues that are all open."""
    return create_sample_issues(total=10, open_ratio=1.0)


@pytest.fixture
def sample_issues_all_closed():
    """Provide issues that are all closed."""
    return create_sample_issues(total=10, open_ratio=0.0)


@pytest.fixture
def mock_analytics_result():
    """Provide mock analytics result."""
    return {
        "productivity": {
            "analysis_type": "productivity",
            "timestamp": "2024-01-01T00:00:00Z",
            "metrics": {
                "total_issues": 50,
                "open_issues": 20,
                "closed_issues": 30,
                "avg_resolution_time_days": 3.5
            },
            "score": 85.0,
            "summary": "Good productivity metrics",
            "recommendations": ["Maintain current pace"],
            "details": {}
        },
        "velocity": {
            "analysis_type": "velocity",
            "timestamp": "2024-01-01T00:00:00Z",
            "metrics": {
                "average_velocity": 12.5,
                "velocity_trend": "increasing"
            },
            "score": 80.0,
            "summary": "Velocity is improving",
            "recommendations": ["Continue monitoring"],
            "details": {}
        }
    }


@pytest.fixture
def analytics_context(analytics_engine, sample_issues_medium, analytics_config):
    """Provide analytics context for strategy testing."""
    return analytics_engine._create_context(
        sample_issues_medium,
        "test/repo",
        analytics_config
    )
