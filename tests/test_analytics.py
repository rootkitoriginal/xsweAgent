"""
Tests for the Analytics Engine and Strategies.
"""

import pytest
from datetime import datetime, timedelta

from src.analytics.engine import (
    AnalyticsEngine,
    AnalyticsConfiguration,
    create_analytics_engine,
)
from src.analytics.strategies import (
    ProductivityAnalysisStrategy,
    VelocityAnalysisStrategy,
)
from src.github_monitor.models import Issue, IssueState


@pytest.fixture
def sample_issues():
    """Fixture for a list of sample issues."""
    now = datetime.now()
    return [
        Issue(
            id=1,
            number=1,
            title="Open Issue 1",
            state=IssueState.OPEN,
            created_at=now - timedelta(days=10),
        ),
        Issue(
            id=2,
            number=2,
            title="Closed Issue 1",
            state=IssueState.CLOSED,
            created_at=now - timedelta(days=20),
            closed_at=now - timedelta(days=5),
        ),
        Issue(
            id=3,
            number=3,
            title="Open Issue 2",
            state=IssueState.OPEN,
            created_at=now - timedelta(days=30),
        ),
        Issue(
            id=4,
            number=4,
            title="Closed Issue 2",
            state=IssueState.CLOSED,
            created_at=now - timedelta(days=40),
            closed_at=now - timedelta(days=15),
        ),
        Issue(
            id=5,
            number=5,
            title="Very old closed",
            state=IssueState.CLOSED,
            created_at=now - timedelta(days=100),
            closed_at=now - timedelta(days=95),
        ),
    ]


@pytest.mark.asyncio
async def test_productivity_strategy(sample_issues):
    """Test the ProductivityAnalysisStrategy."""
    strategy = ProductivityAnalysisStrategy()
    engine = await create_analytics_engine()  # To get context
    context = engine._create_context(
        sample_issues, "test/repo", AnalyticsConfiguration()
    )

    result = await strategy.analyze(sample_issues, context)

    assert result.analysis_type.value == "productivity"
    assert result.metrics["total_issues"] == 5
    assert result.metrics["open_issues"] == 2
    assert result.metrics["closed_issues"] == 3
    assert "avg_resolution_time_days" in result.metrics


@pytest.mark.asyncio
async def test_velocity_strategy(sample_issues):
    """Test the VelocityAnalysisStrategy."""
    strategy = VelocityAnalysisStrategy()
    engine = await create_analytics_engine()
    config = AnalyticsConfiguration(velocity_calculation_period=10)
    context = engine._create_context(sample_issues, "test/repo", config)

    # Filter issues to a relevant window for velocity
    issues_in_window = [
        i
        for i in sample_issues
        if i.closed_at and i.closed_at > datetime.now() - timedelta(days=30)
    ]

    result = await strategy.analyze(issues_in_window, context)

    assert result.analysis_type.value == "velocity"
    assert "average_velocity" in result.metrics
    assert "velocity_per_period" in result.details


@pytest.mark.asyncio
async def test_analytics_engine_full_run(sample_issues):
    """Test a full run of the AnalyticsEngine."""
    engine = await create_analytics_engine()

    results = await engine.analyze(sample_issues, "test/repo")

    assert "productivity" in results
    assert "velocity" in results
    assert "burndown" in results
    assert "quality" in results

    assert results["productivity"].score is not None
    assert results["velocity"].metrics["average_velocity"] is not None


@pytest.mark.asyncio
async def test_engine_insufficient_data(sample_issues):
    """Test that the engine handles insufficient data."""
    engine = await create_analytics_engine()

    # Use only a few issues
    small_issue_list = sample_issues[:2]

    results = await engine.analyze(small_issue_list, "test/repo")

    # Default minimum is 5, so this should be empty
    assert not results
