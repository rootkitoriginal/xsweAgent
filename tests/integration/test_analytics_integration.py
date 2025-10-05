"""
Integration tests for analytics pipeline.

Tests the complete analytics workflow from data ingestion to result generation.
"""
import pytest
from datetime import datetime, timedelta

from src.analytics.engine import create_analytics_engine, AnalyticsConfiguration
from src.analytics.strategies import (
    ProductivityAnalysisStrategy,
    VelocityAnalysisStrategy,
    BurndownAnalysisStrategy,
    QualityAnalysisStrategy
)
from tests.utils.test_data_builder import IssueListBuilder, create_sample_issues
from tests.utils.assertions import MetricsAssertions, AnalyticsAssertions


@pytest.mark.integration
class TestAnalyticsIntegration:
    """Integration tests for analytics pipeline."""
    
    @pytest.mark.asyncio
    async def test_full_analytics_pipeline(self):
        """Test complete analytics pipeline from issues to insights."""
        # Create realistic issue data
        issues = (IssueListBuilder()
                  .add_open_issues(7)
                  .add_closed_issues(13)
                  .build())
        
        # Run full analytics
        engine = await create_analytics_engine()
        results = await engine.analyze(issues, "test/repo")
        
        # Verify all analysis types are present
        assert "productivity" in results
        assert "velocity" in results
        assert "burndown" in results
        assert "quality" in results
        
        # Verify each result has required structure
        for analysis_type, result in results.items():
            AnalyticsAssertions.assert_analysis_result_structure(result.__dict__)
    
    @pytest.mark.asyncio
    async def test_productivity_analysis_integration(self):
        """Test productivity analysis with realistic data."""
        # Create issues with varied resolution times
        builder = IssueListBuilder()
        
        # Fast resolution issues (1-2 days)
        for i in range(5):
            builder.add_closed_issue(
                title=f"Fast Issue {i}",
                created_days_ago=i + 5,
                closed_days_ago=i + 3
            )
        
        # Medium resolution issues (5-7 days)
        for i in range(3):
            builder.add_closed_issue(
                title=f"Medium Issue {i}",
                created_days_ago=i + 15,
                closed_days_ago=i + 8
            )
        
        # Still open issues
        builder.add_open_issues(4)
        
        issues = builder.build()
        
        strategy = ProductivityAnalysisStrategy()
        engine = await create_analytics_engine()
        context = engine._create_context(issues, "test/repo", AnalyticsConfiguration())
        
        result = await strategy.analyze(issues, context)
        
        # Verify metrics
        assert "total_issues" in result.metrics
        assert "closed_issues" in result.metrics
        assert "avg_resolution_time_days" in result.metrics
        
        MetricsAssertions.assert_positive_metric(result.metrics, "total_issues")
        MetricsAssertions.assert_positive_metric(result.metrics, "closed_issues")
        
        # Average resolution time should be reasonable (not negative, not too large)
        avg_time = result.metrics.get("avg_resolution_time_days", 0)
        assert 0 <= avg_time <= 30, f"Average resolution time {avg_time} seems unrealistic"
    
    @pytest.mark.asyncio
    async def test_velocity_analysis_integration(self):
        """Test velocity analysis with time-based data."""
        # Create issues spread over time periods
        builder = IssueListBuilder()
        
        # Closed issues over several weeks
        for week in range(4):
            for issue_in_week in range(5):
                builder.add_closed_issue(
                    title=f"Week {week} Issue {issue_in_week}",
                    created_days_ago=(week * 7) + 14,
                    closed_days_ago=(week * 7) + issue_in_week
                )
        
        issues = builder.build()
        
        strategy = VelocityAnalysisStrategy()
        engine = await create_analytics_engine()
        context = engine._create_context(issues, "test/repo", AnalyticsConfiguration())
        
        # Filter to recent issues
        recent_issues = [
            i for i in issues
            if i.closed_at and i.closed_at > datetime.now() - timedelta(days=30)
        ]
        
        result = await strategy.analyze(recent_issues, context)
        
        # Verify velocity metrics
        assert "average_velocity" in result.metrics
        assert "velocity_per_period" in result.details
        
        MetricsAssertions.assert_positive_metric(result.metrics, "average_velocity")
    
    @pytest.mark.asyncio
    async def test_multi_strategy_coordination(self):
        """Test that multiple strategies work together correctly."""
        issues = create_sample_issues(total=20, open_ratio=0.4)
        
        # Run all strategies
        engine = await create_analytics_engine()
        
        productivity = ProductivityAnalysisStrategy()
        velocity = VelocityAnalysisStrategy()
        burndown = BurndownAnalysisStrategy()
        quality = QualityAnalysisStrategy()
        
        config = AnalyticsConfiguration()
        context = engine._create_context(issues, "test/repo", config)
        
        # Execute all strategies
        prod_result = await productivity.analyze(issues, context)
        vel_result = await velocity.analyze(issues, context)
        burn_result = await burndown.analyze(issues, context)
        qual_result = await quality.analyze(issues, context)
        
        # All should succeed and have metrics
        assert prod_result.metrics is not None
        assert vel_result.metrics is not None
        assert burn_result.metrics is not None
        assert qual_result.metrics is not None
        
        # Verify consistency across strategies
        total_from_prod = prod_result.metrics.get("total_issues", 0)
        assert total_from_prod == 20
    
    @pytest.mark.asyncio
    async def test_insufficient_data_handling(self):
        """Test analytics behavior with insufficient data."""
        # Create very small dataset
        issues = create_sample_issues(total=2, open_ratio=0.5)
        
        engine = await create_analytics_engine()
        
        # With default minimum of 5 issues, should return empty results
        results = await engine.analyze(issues, "test/repo")
        
        assert len(results) == 0 or all(
            len(r.metrics) == 0 for r in results.values()
        )
    
    @pytest.mark.asyncio
    async def test_custom_configuration(self):
        """Test analytics with custom configuration."""
        issues = create_sample_issues(total=15, open_ratio=0.6)
        
        # Create custom configuration
        config = AnalyticsConfiguration(
            minimum_issues_for_analysis=5,
            velocity_calculation_period=14,
            time_window_days=60
        )
        
        engine = await create_analytics_engine()
        results = await engine.analyze(issues, "test/repo", config)
        
        # Should have results with custom config
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_burndown_chart_data(self):
        """Test burndown analysis generates proper chart data."""
        builder = IssueListBuilder()
        
        # Create issues with varied completion times
        for i in range(10):
            builder.add_closed_issue(
                title=f"Task {i}",
                created_days_ago=20,
                closed_days_ago=20 - i * 2  # Progressive completion
            )
        
        builder.add_open_issues(5)  # Remaining work
        
        issues = builder.build()
        
        strategy = BurndownAnalysisStrategy()
        engine = await create_analytics_engine()
        context = engine._create_context(issues, "test/repo", AnalyticsConfiguration())
        
        result = await strategy.analyze(issues, context)
        
        # Should have burndown data points
        assert "remaining_issues" in result.metrics
        assert result.details is not None
    
    @pytest.mark.asyncio
    async def test_quality_metrics_calculation(self):
        """Test quality analysis metrics calculation."""
        builder = IssueListBuilder()
        
        # High quality: fast resolution, good completion rate
        for i in range(10):
            builder.add_closed_issue(
                title=f"Quality Issue {i}",
                created_days_ago=i + 10,
                closed_days_ago=i + 8  # 2-day resolution
            )
        
        builder.add_open_issues(2)
        
        issues = builder.build()
        
        strategy = QualityAnalysisStrategy()
        engine = await create_analytics_engine()
        context = engine._create_context(issues, "test/repo", AnalyticsConfiguration())
        
        result = await strategy.analyze(issues, context)
        
        # Should have quality score
        assert "quality_score" in result.metrics or result.score is not None
        
        if "quality_score" in result.metrics:
            quality_score = result.metrics["quality_score"]
            assert 0 <= quality_score <= 100
    
    @pytest.mark.asyncio
    async def test_edge_case_all_open_issues(self):
        """Test analytics with only open issues."""
        issues = (IssueListBuilder()
                  .add_open_issues(10)
                  .build())
        
        engine = await create_analytics_engine()
        results = await engine.analyze(issues, "test/repo")
        
        # Should handle gracefully
        if "productivity" in results:
            prod = results["productivity"]
            assert prod.metrics["open_issues"] == 10
            assert prod.metrics["closed_issues"] == 0
    
    @pytest.mark.asyncio
    async def test_edge_case_all_closed_issues(self):
        """Test analytics with only closed issues."""
        issues = (IssueListBuilder()
                  .add_closed_issues(10)
                  .build())
        
        engine = await create_analytics_engine()
        results = await engine.analyze(issues, "test/repo")
        
        # Should handle gracefully
        if "productivity" in results:
            prod = results["productivity"]
            assert prod.metrics["open_issues"] == 0
            assert prod.metrics["closed_issues"] == 10
    
    @pytest.mark.asyncio
    async def test_analytics_with_cache(self):
        """Test that analytics engine uses caching appropriately."""
        issues = create_sample_issues(total=15, open_ratio=0.6)
        
        engine = await create_analytics_engine()
        
        # First run
        results1 = await engine.analyze(issues, "test/repo")
        
        # Second run with same data (should potentially use cache)
        results2 = await engine.analyze(issues, "test/repo")
        
        # Results should be consistent
        if results1 and results2:
            assert len(results1) == len(results2)
