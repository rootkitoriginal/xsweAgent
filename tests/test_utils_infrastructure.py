"""
Tests for utils infrastructure components.
"""

import asyncio
import time

import pytest

from src.utils import (
    BackoffStrategy,
    CircuitBreaker,
    CircuitBreakerPolicies,
    HealthCheck,
    HealthCheckRegistry,
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

        @retry(RetryPolicies.FAST)
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

        @retry(RetryPolicies.FAST)
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
        policy = RetryPolicy(
            max_attempts=5,
            base_delay=2.0,
            max_delay=30.0,
            backoff_strategy=BackoffStrategy.EXPONENTIAL,
        )

        assert policy.max_attempts == 5
        assert policy.base_delay == 2.0
        assert policy.max_delay == 30.0
        assert policy.backoff_strategy == BackoffStrategy.EXPONENTIAL


class TestCircuitBreaker:
    """Tests for circuit breaker functionality."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state."""
        breaker = CircuitBreaker(CircuitBreakerPolicies.STANDARD)

        @breaker
        async def successful_call():
            return "success"

        result = await successful_call()
        assert result == "success"
        assert breaker.state.failure_count == 0

    def test_circuit_breaker_state(self):
        """Test getting circuit breaker state."""
        breaker = CircuitBreaker(CircuitBreakerPolicies.STANDARD)
        state = breaker.get_state()

        assert "state" in state
        assert "failure_count" in state
        assert state["failure_count"] == 0


class TestHealthChecks:
    """Tests for health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check."""

        async def check_func():
            return HealthCheckResult(
                component="test",
                status=HealthStatus.HEALTHY,
                message="All good",
            )

        check = HealthCheck("test", check_func)
        result = await check.execute()

        assert result.component == "test"
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "All good"

    @pytest.mark.asyncio
    async def test_health_check_registry(self):
        """Test health check registry."""
        registry = HealthCheckRegistry()

        async def check_func():
            return HealthCheckResult(
                component="test",
                status=HealthStatus.HEALTHY,
            )

        check = HealthCheck("test_component", check_func)
        registry.register(check)

        assert "test_component" in registry.list_checks()

        result = await registry.check("test_component")
        assert result.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_health_check_overall_status(self):
        """Test overall health status calculation."""
        registry = HealthCheckRegistry()

        async def healthy_check():
            return HealthCheckResult(
                component="healthy",
                status=HealthStatus.HEALTHY,
            )

        async def degraded_check():
            return HealthCheckResult(
                component="degraded",
                status=HealthStatus.DEGRADED,
            )

        registry.register(HealthCheck("healthy", healthy_check))
        registry.register(HealthCheck("degraded", degraded_check, critical=False))

        overall = await registry.get_overall_status()
        # Should be degraded due to one degraded component
        assert overall == HealthStatus.DEGRADED


class TestMetrics:
    """Tests for metrics collection."""

    def test_metrics_collection(self):
        """Test basic metrics recording."""
        collector = MetricsCollector()

        collector.record("test_metric", 100.0)
        collector.record("test_metric", 200.0)
        collector.record("test_metric", 150.0)

        metrics = collector.get_metrics()
        assert "test_metric" in metrics

        metric = metrics["test_metric"]
        assert metric.count == 3
        assert metric.total == 450.0
        assert metric.avg == 150.0
        assert metric.min == 100.0
        assert metric.max == 200.0

    def test_metrics_counters(self):
        """Test counter metrics."""
        collector = MetricsCollector()

        collector.increment("api_calls", 1, labels={"endpoint": "/test"})
        collector.increment("api_calls", 1, labels={"endpoint": "/test"})
        collector.increment("api_calls", 1, labels={"endpoint": "/test"})

        counters = collector.get_counters()
        assert len(counters) > 0

    def test_metrics_clear(self):
        """Test clearing metrics."""
        collector = MetricsCollector()

        collector.record("test_metric", 100.0)
        collector.increment("counter", 1)

        collector.clear()

        metrics = collector.get_metrics()
        counters = collector.get_counters()

        assert len(metrics) == 0
        assert len(counters) == 0

    @pytest.mark.asyncio
    async def test_track_api_calls_decorator(self):
        """Test API call tracking decorator."""
        from src.utils import get_metrics_collector

        collector = get_metrics_collector()
        collector.clear()

        @track_api_calls("test_endpoint")
        async def test_function():
            return "success"

        result = await test_function()
        assert result == "success"

        # Check that metrics were recorded
        counters = collector.get_counters()
        # Should have recorded a call
        assert len(counters) > 0

    def test_prometheus_format(self):
        """Test Prometheus format export."""
        collector = MetricsCollector()
        collector.clear()

        collector.record("test_metric", 100.0)
        collector.increment("test_counter", 5)

        prometheus_text = collector.get_prometheus_format()

        assert isinstance(prometheus_text, str)
        assert "# HELP" in prometheus_text
        assert "# TYPE" in prometheus_text
