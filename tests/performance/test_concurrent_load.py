"""
Concurrent load and stress tests.

Tests system behavior under concurrent operations and high load.
"""
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

from src.analytics.engine import create_analytics_engine
from src.github_monitor.service import GitHubIssuesService
from tests.utils.test_data_builder import create_sample_issues
from tests.utils.assertions import PerformanceAssertions


@pytest.mark.performance
@pytest.mark.slow
class TestConcurrentLoad:
    """Stress tests for concurrent operations."""
    
    @pytest.mark.asyncio
    async def test_concurrent_analytics_requests(self):
        """Test handling multiple concurrent analytics requests."""
        
        async def run_analysis(repo_id: int):
            issues = create_sample_issues(total=50, open_ratio=0.6)
            engine = await create_analytics_engine()
            return await engine.analyze(issues, f"repo-{repo_id}")
        
        # Run 10 concurrent analyses
        start_time = time.time()
        
        tasks = [run_analysis(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        duration = time.time() - start_time
        
        # Should handle 10 concurrent requests efficiently
        PerformanceAssertions.assert_execution_time(
            duration, 10.0, "10 concurrent analytics requests"
        )
        
        # All should succeed
        assert len(results) == 10
        assert all(isinstance(r, dict) for r in results)
    
    @pytest.mark.asyncio
    async def test_high_concurrency_analytics(self):
        """Test system under high concurrency (50 requests)."""
        
        async def quick_analysis(repo_id: int):
            issues = create_sample_issues(total=20, open_ratio=0.5)
            engine = await create_analytics_engine()
            return await engine.analyze(issues, f"repo-{repo_id}")
        
        start_time = time.time()
        
        # Run 50 concurrent analyses
        tasks = [quick_analysis(i) for i in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        duration = time.time() - start_time
        
        # Should complete in reasonable time even under high load
        PerformanceAssertions.assert_execution_time(
            duration, 30.0, "50 concurrent analytics requests"
        )
        
        # Most should succeed (allow some failures under stress)
        successful = sum(1 for r in results if isinstance(r, dict))
        assert successful >= 45, f"Only {successful}/50 requests succeeded"
    
    @pytest.mark.asyncio
    async def test_concurrent_mixed_operations(self):
        """Test mixed concurrent operations (read, analyze, generate)."""
        from src.charts.factory import ChartFactory, ChartType
        
        async def analytics_task(i):
            issues = create_sample_issues(total=30, open_ratio=0.6)
            engine = await create_analytics_engine()
            return await engine.analyze(issues, f"repo-{i}")
        
        def chart_task(i):
            data = {"labels": ["A", "B"], "values": [10, 20]}
            chart = ChartFactory.create_chart(
                chart_type=ChartType.BAR,
                data=data,
                title=f"Chart {i}"
            )
            return chart.generate()
        
        start_time = time.time()
        
        # Mix of async analytics and sync chart generation
        analytics_tasks = [analytics_task(i) for i in range(5)]
        
        # Run analytics
        analytics_results = await asyncio.gather(*analytics_tasks)
        
        # Run chart generation in thread pool
        with ThreadPoolExecutor(max_workers=5) as executor:
            chart_futures = [executor.submit(chart_task, i) for i in range(5)]
            chart_results = [f.result() for f in chart_futures]
        
        duration = time.time() - start_time
        
        PerformanceAssertions.assert_execution_time(
            duration, 15.0, "Mixed concurrent operations"
        )
        
        assert len(analytics_results) == 5
        assert len(chart_results) == 5
    
    @pytest.mark.asyncio
    async def test_burst_traffic_handling(self):
        """Test handling burst traffic patterns."""
        
        async def burst_request(burst_id: int, request_id: int):
            issues = create_sample_issues(total=25, open_ratio=0.5)
            engine = await create_analytics_engine()
            return await engine.analyze(issues, f"burst-{burst_id}-req-{request_id}")
        
        # Simulate 3 bursts of 10 requests each
        all_durations = []
        
        for burst in range(3):
            start_time = time.time()
            
            tasks = [burst_request(burst, i) for i in range(10)]
            results = await asyncio.gather(*tasks)
            
            duration = time.time() - start_time
            all_durations.append(duration)
            
            assert len(results) == 10
            
            # Brief pause between bursts
            await asyncio.sleep(0.5)
        
        # Each burst should complete in reasonable time
        for i, duration in enumerate(all_durations):
            PerformanceAssertions.assert_execution_time(
                duration, 8.0, f"Burst {i+1}"
            )
    
    @pytest.mark.asyncio
    async def test_sustained_load(self):
        """Test system under sustained load over time."""
        
        async def continuous_analysis(duration_seconds: int):
            """Run analyses continuously for specified duration."""
            end_time = time.time() + duration_seconds
            count = 0
            
            while time.time() < end_time:
                issues = create_sample_issues(total=20, open_ratio=0.5)
                engine = await create_analytics_engine()
                await engine.analyze(issues, f"sustained-{count}")
                count += 1
                await asyncio.sleep(0.1)  # Small delay between requests
            
            return count
        
        # Run sustained load for 5 seconds
        start_time = time.time()
        requests_completed = await continuous_analysis(5)
        duration = time.time() - start_time
        
        # Should complete close to target duration
        assert 4.5 <= duration <= 6.0, f"Duration {duration}s not in expected range"
        
        # Should handle reasonable number of requests
        assert requests_completed > 0
        
        # Calculate throughput
        throughput = requests_completed / duration
        assert throughput > 1, f"Low throughput: {throughput:.2f} req/s"
    
    @pytest.mark.asyncio
    async def test_resource_cleanup_under_load(self):
        """Test that resources are properly cleaned up under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_connections = len(process.connections())
        initial_threads = process.num_threads()
        
        async def analysis_with_cleanup(i):
            issues = create_sample_issues(total=30, open_ratio=0.5)
            engine = await create_analytics_engine()
            result = await engine.analyze(issues, f"cleanup-{i}")
            await engine.clear_cache()
            return result
        
        # Run 20 analyses
        tasks = [analysis_with_cleanup(i) for i in range(20)]
        await asyncio.gather(*tasks)
        
        # Check resource usage
        final_connections = len(process.connections())
        final_threads = process.num_threads()
        
        # Connections and threads should not grow excessively
        connection_growth = final_connections - initial_connections
        thread_growth = final_threads - initial_threads
        
        assert connection_growth < 100, f"Too many connections: +{connection_growth}"
        assert thread_growth < 50, f"Too many threads: +{thread_growth}"
    
    @pytest.mark.asyncio
    async def test_error_rate_under_load(self):
        """Test error rate remains acceptable under high load."""
        
        async def potentially_failing_analysis(i):
            try:
                issues = create_sample_issues(total=30, open_ratio=0.5)
                engine = await create_analytics_engine()
                return await engine.analyze(issues, f"error-test-{i}")
            except Exception as e:
                return {"error": str(e)}
        
        # Run 30 concurrent requests
        tasks = [potentially_failing_analysis(i) for i in range(30)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successes and failures
        successes = sum(1 for r in results if isinstance(r, dict) and "error" not in r)
        failures = len(results) - successes
        
        # Error rate should be less than 10%
        error_rate = failures / len(results)
        assert error_rate < 0.10, f"High error rate: {error_rate*100:.1f}%"
    
    @pytest.mark.asyncio
    async def test_timeout_handling_under_load(self):
        """Test that timeouts are properly handled under load."""
        
        async def timed_analysis(i, timeout_seconds):
            try:
                issues = create_sample_issues(total=50, open_ratio=0.5)
                engine = await create_analytics_engine()
                
                # Use asyncio.wait_for to enforce timeout
                result = await asyncio.wait_for(
                    engine.analyze(issues, f"timeout-{i}"),
                    timeout=timeout_seconds
                )
                return {"status": "success", "result": result}
            except asyncio.TimeoutError:
                return {"status": "timeout"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        # Run with tight timeout to potentially trigger timeouts
        tasks = [timed_analysis(i, 2.0) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All should complete (either success or timeout, no crashes)
        assert len(results) == 10
        assert all("status" in r for r in results)
        
        # Most should succeed
        successes = sum(1 for r in results if r["status"] == "success")
        assert successes >= 7, f"Only {successes}/10 completed within timeout"
    
    @pytest.mark.asyncio
    async def test_memory_stability_under_load(self):
        """Test memory remains stable under prolonged load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        memory_samples = []
        
        async def analysis_round():
            """Run a round of analyses and measure memory."""
            tasks = [
                self._single_analysis(i)
                for i in range(10)
            ]
            await asyncio.gather(*tasks)
            
            # Sample memory
            memory_mb = process.memory_info().rss / 1024 / 1024
            memory_samples.append(memory_mb)
        
        # Run 5 rounds
        for _ in range(5):
            await analysis_round()
            await asyncio.sleep(0.5)
        
        # Memory should not grow significantly
        if len(memory_samples) >= 2:
            memory_growth = memory_samples[-1] - memory_samples[0]
            
            # Allow some growth, but not excessive (< 50MB)
            assert memory_growth < 50, \
                f"Excessive memory growth: {memory_growth:.1f}MB"
    
    async def _single_analysis(self, i):
        """Helper for running single analysis."""
        issues = create_sample_issues(total=25, open_ratio=0.5)
        engine = await create_analytics_engine()
        return await engine.analyze(issues, f"load-{i}")
