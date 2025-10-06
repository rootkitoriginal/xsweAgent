"""
Performance tests for analytics engine.

Tests performance benchmarks and scalability of analytics operations.
"""
import pytest
import time
from datetime import datetime

from src.analytics.engine import create_analytics_engine
from tests.utils.test_data_builder import create_sample_issues
from tests.utils.assertions import PerformanceAssertions


@pytest.mark.performance
@pytest.mark.slow
class TestAnalyticsPerformance:
    """Performance benchmarks for analytics engine."""
    
    @pytest.mark.asyncio
    async def test_small_dataset_performance(self):
        """Test analytics performance with small dataset (10 issues)."""
        issues = create_sample_issues(total=10, open_ratio=0.6)
        
        engine = await create_analytics_engine()
        
        start_time = time.time()
        results = await engine.analyze(issues, "test/repo")
        duration = time.time() - start_time
        
        # Should complete in less than 1 second for small dataset
        PerformanceAssertions.assert_execution_time(
            duration, 1.0, "Small dataset analytics"
        )
        
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_medium_dataset_performance(self):
        """Test analytics performance with medium dataset (100 issues)."""
        issues = create_sample_issues(total=100, open_ratio=0.5)
        
        engine = await create_analytics_engine()
        
        start_time = time.time()
        results = await engine.analyze(issues, "test/repo")
        duration = time.time() - start_time
        
        # Should complete in less than 3 seconds for medium dataset
        PerformanceAssertions.assert_execution_time(
            duration, 3.0, "Medium dataset analytics"
        )
        
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_large_dataset_performance(self):
        """Test analytics performance with large dataset (1000 issues)."""
        issues = create_sample_issues(total=1000, open_ratio=0.4)
        
        engine = await create_analytics_engine()
        
        start_time = time.time()
        results = await engine.analyze(issues, "test/repo")
        duration = time.time() - start_time
        
        # Should complete in less than 10 seconds for large dataset
        PerformanceAssertions.assert_execution_time(
            duration, 10.0, "Large dataset analytics"
        )
        
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_repeated_analysis_performance(self):
        """Test performance of repeated analysis runs."""
        issues = create_sample_issues(total=50, open_ratio=0.6)
        engine = await create_analytics_engine()
        
        durations = []
        
        # Run analysis 10 times
        for i in range(10):
            start_time = time.time()
            results = await engine.analyze(issues, f"test/repo-{i}")
            duration = time.time() - start_time
            durations.append(duration)
        
        # Average time should be reasonable
        avg_duration = sum(durations) / len(durations)
        
        PerformanceAssertions.assert_execution_time(
            avg_duration, 2.0, "Average repeated analysis"
        )
        
        # Verify consistency (no extreme outliers)
        max_duration = max(durations)
        min_duration = min(durations)
        
        # Max should not be more than 3x min (indicates consistent performance)
        assert max_duration <= min_duration * 3, \
            f"Inconsistent performance: min={min_duration:.3f}s, max={max_duration:.3f}s"
    
    @pytest.mark.asyncio
    async def test_concurrent_analysis_performance(self):
        """Test performance under concurrent analysis requests."""
        import asyncio
        
        async def analyze_dataset(repo_name: str):
            issues = create_sample_issues(total=50, open_ratio=0.5)
            engine = await create_analytics_engine()
            return await engine.analyze(issues, repo_name)
        
        # Run 5 concurrent analyses
        start_time = time.time()
        
        tasks = [
            analyze_dataset(f"test/repo-{i}")
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time
        
        # Should complete in less than 5 seconds for 5 concurrent runs
        PerformanceAssertions.assert_execution_time(
            duration, 5.0, "Concurrent analysis (5 repos)"
        )
        
        # All should succeed
        assert len(results) == 5
        assert all(len(r) > 0 for r in results if r)
    
    @pytest.mark.asyncio
    async def test_strategy_execution_time(self):
        """Test individual strategy execution times."""
        from src.analytics.strategies import (
            ProductivityAnalysisStrategy,
            VelocityAnalysisStrategy,
            BurndownAnalysisStrategy,
            QualityAnalysisStrategy
        )
        from src.analytics.engine import AnalyticsConfiguration
        
        issues = create_sample_issues(total=100, open_ratio=0.5)
        engine = await create_analytics_engine()
        config = AnalyticsConfiguration()
        context = engine._create_context(issues, "test/repo", config)
        
        strategies = [
            ("Productivity", ProductivityAnalysisStrategy()),
            ("Velocity", VelocityAnalysisStrategy()),
            ("Burndown", BurndownAnalysisStrategy()),
            ("Quality", QualityAnalysisStrategy())
        ]
        
        for name, strategy in strategies:
            start_time = time.time()
            result = await strategy.analyze(issues, context)
            duration = time.time() - start_time
            
            # Each strategy should complete in less than 2 seconds
            PerformanceAssertions.assert_execution_time(
                duration, 2.0, f"{name} strategy"
            )
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_memory_efficiency(self):
        """Test memory usage during analytics processing."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Measure initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process large dataset
        issues = create_sample_issues(total=1000, open_ratio=0.5)
        engine = await create_analytics_engine()
        results = await engine.analyze(issues, "test/repo")
        
        # Measure final memory
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = final_memory - initial_memory
        
        # Should not use excessive memory (less than 100MB increase)
        PerformanceAssertions.assert_memory_usage(
            memory_used, 100.0, "Analytics processing"
        )
        
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_cache_performance_impact(self):
        """Test performance improvement from caching."""
        issues = create_sample_issues(total=100, open_ratio=0.5)
        engine = await create_analytics_engine()
        
        # First run (no cache)
        start_time = time.time()
        results1 = await engine.analyze(issues, "test/repo")
        first_run_duration = time.time() - start_time
        
        # Clear and run again to measure consistency
        engine.clear_cache()  # Not an async method, no await needed
        
        start_time = time.time()
        results2 = await engine.analyze(issues, "test/repo")
        second_run_duration = time.time() - start_time
        
        # Both should complete in reasonable time
        PerformanceAssertions.assert_execution_time(
            first_run_duration, 3.0, "First analysis run"
        )
        PerformanceAssertions.assert_execution_time(
            second_run_duration, 3.0, "Second analysis run"
        )
        
        # Results should be consistent
        assert len(results1) == len(results2)
    
    @pytest.mark.asyncio
    async def test_scalability_linear_growth(self):
        """Test that processing time grows linearly with dataset size."""
        dataset_sizes = [50, 100, 200]
        durations = []
        
        engine = await create_analytics_engine()
        
        for size in dataset_sizes:
            issues = create_sample_issues(total=size, open_ratio=0.5)
            
            start_time = time.time()
            await engine.analyze(issues, f"test/repo-{size}")
            duration = time.time() - start_time
            
            durations.append(duration)
        
        # Check that growth is roughly linear (not exponential)
        # Time for 200 issues should be less than 5x time for 50 issues
        ratio = durations[2] / durations[0] if durations[0] > 0 else 0
        
        assert ratio < 5.0, \
            f"Non-linear scaling detected: 200 issues took {ratio:.2f}x " \
            f"longer than 50 issues"
