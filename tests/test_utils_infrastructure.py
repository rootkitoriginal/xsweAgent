"""
Tests for utils infrastructure components.
"""

import asyncio
import time

import pytest

from src.utils import (
    BackoffStrategy,
    BaseHealthCheck,
    CircuitBreaker,
    CircuitBreakerPolicies,
    HealthChecker,
    HealthCheckResult,
    HealthStatus,
    MetricsCollector,
    RetryPolicies,
    RetryPolicy,
    retry,
    track_api_calls,
)


class TestRetry:
    """Tests for retry functionality."""

    @pytest.mark.asyncio
    async def test_retry_success(self):
        """Test successful call with retry decorator."""
        call_count = 0

        @retry(policy=RetryPolicies.FAST)
        async def successful_call():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_call()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_eventual_success(self):
        """Test call that succeeds after retries."""
        call_count = 0

        @retry(policy=RetryPolicies.FAST)
        async def eventually_successful():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return "success"

        result = await eventually_successful()
        assert result == "success"
        assert call_count == 2

    def test_retry_policy_configuration(self):
        """Test retry policy configuration."""
        from src.utils.retry import RetryConfig
        
        config = RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            max_delay=30.0,
            backoff_strategy=BackoffStrategy.EXPONENTIAL,
        )
        
        policy = RetryPolicy(
            name="test_policy",
            config=config,
            description="Test retry policy"
        )

        assert policy.config.max_attempts == 5
        assert policy.config.base_delay == 2.0
        assert policy.config.max_delay == 30.0
        assert policy.config.backoff_strategy == BackoffStrategy.EXPONENTIAL


class TestCircuitBreaker:
    """Tests for circuit breaker functionality."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state."""
        breaker = CircuitBreaker("test_breaker", CircuitBreakerPolicies.external_service())

        async def successful_call():
            return "success"

        result = await breaker.execute_async_request(successful_call)
        assert result == "success"
        assert breaker.stats.failure_count == 0

    def test_circuit_breaker_state(self):
        """Test getting circuit breaker state."""
        breaker = CircuitBreaker("test_breaker_2", CircuitBreakerPolicies.external_service())
        stats = breaker.get_stats()

        assert "state" in stats
        assert "failure_count" in stats
        assert stats["failure_count"] == 0


class TestHealthChecks:
    """Tests for health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check."""
        
        class TestHealthCheck(BaseHealthCheck):
            async def _perform_check(self) -> HealthCheckResult:
                return HealthCheckResult(
                    component="test",
                    status=HealthStatus.HEALTHY,
                    message="All good",
                )

        check = TestHealthCheck("test")
        result = await check.check()

        assert result.component == "test"
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "All good"

    @pytest.mark.asyncio
    async def test_health_check_registry(self):
        """Test health check registry."""
        registry = HealthChecker()

        class TestHealthCheck(BaseHealthCheck):
            async def _perform_check(self) -> HealthCheckResult:
                return HealthCheckResult(
                    component="test_component",
                    status=HealthStatus.HEALTHY,
                    message="Health check passed",
                )

        check = TestHealthCheck("test_component")
        registry.register_check(check)

        assert "test_component" in registry.checks

        result = await registry.check_single("test_component")
        assert result.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_health_check_overall_status(self):
        """Test overall health status calculation."""
        registry = HealthChecker()

        class HealthyCheck(BaseHealthCheck):
            async def _perform_check(self) -> HealthCheckResult:
                return HealthCheckResult(
                    component="healthy",
                    status=HealthStatus.HEALTHY,
                    message="System is healthy",
                )

        class DegradedCheck(BaseHealthCheck):
            async def _perform_check(self) -> HealthCheckResult:
                return HealthCheckResult(
                    component="degraded",
                    status=HealthStatus.DEGRADED,
                    message="System is degraded",
                )

        registry.register_check(HealthyCheck("healthy"))
        registry.register_check(DegradedCheck("degraded"))

        health_status = await registry.get_system_health()
        # Should have both components checked
        assert "healthy" in health_status["components"]
        assert "degraded" in health_status["components"]
        assert health_status["summary"]["total_checks"] == 2


class TestMetrics:
    """Tests for metrics collection."""

    def test_metrics_collection(self):
        """Test basic metrics recording."""
        collector = MetricsCollector()

        # Create a gauge metric and set values
        test_gauge = collector.gauge("test_metric", "Test metric")
        test_gauge.set(100.0)
        test_gauge.set(200.0)
        test_gauge.set(150.0)

        metrics = collector.get_all_metrics()
        assert "test_metric" in metrics

        metric = metrics["test_metric"]
        assert metric.get_value() == 150.0  # Last set value for gauge

    def test_metrics_counters(self):
        """Test counter metrics."""
        collector = MetricsCollector()

        # Create a counter and increment it
        api_counter = collector.counter("api_calls", "API call counter", {"endpoint": "/test"})
        api_counter.inc()
        api_counter.inc()
        api_counter.inc()

        metrics = collector.get_all_metrics()
        assert "api_calls" in metrics
        counter_metric = metrics["api_calls"]
        assert counter_metric.get_value() == 3

    def test_metrics_stats(self):
        """Test metrics statistics."""
        collector = MetricsCollector()

        # Create different types of metrics
        collector.gauge("test_gauge", "Test gauge")
        collector.counter("test_counter", "Test counter")
        collector.histogram("test_histogram", "Test histogram")

        stats = collector.get_stats()
        assert stats["registered_metrics"] >= 3
        assert "counter" in stats["metrics_by_type"]
        assert "gauge" in stats["metrics_by_type"]
        assert "histogram" in stats["metrics_by_type"]

    @pytest.mark.asyncio
    async def test_track_api_calls_decorator(self):
        """Test API call tracking decorator."""
        from src.utils import get_metrics_collector

        collector = get_metrics_collector()

        @track_api_calls("test_endpoint")
        async def test_function():
            return "success"

        result = await test_function()
        assert result == "success"

        # Check that metrics were recorded
        metrics = collector.get_all_metrics()
        # Should have recorded API request metrics
        assert "api_requests_total" in metrics

    def test_prometheus_format(self):
        """Test Prometheus format export."""
        collector = MetricsCollector()

        # Create some metrics
        gauge = collector.gauge("test_gauge", "Test gauge metric")
        counter = collector.counter("test_counter", "Test counter metric")
        
        gauge.set(100.0)
        counter.inc(5)

        prometheus_text = collector.collect()

        assert isinstance(prometheus_text, str)
        assert "# HELP" in prometheus_text
        assert "# TYPE" in prometheus_text
