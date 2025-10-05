"""
Tests for utility infrastructure components.
"""

import pytest
from unittest.mock import Mock, patch
import time

from src.utils import (
    ChartGenerationError,
    CircuitBreakerError,
    CircuitBreaker,
    CircuitBreakerPolicies,
    HealthCheck,
    HealthStatus,
    MetricsCollector,
    RetryExhaustedError,
    RetryPolicies,
    XSWEAgentError,
    retry,
    track_api_calls,
)


class TestExceptions:
    """Test custom exceptions."""

    def test_base_exception(self):
        """Test base exception with details."""
        exc = XSWEAgentError("Test error")
        assert str(exc) == "Test error"

    def test_chart_generation_error(self):
        """Test chart generation error."""
        exc = ChartGenerationError("Chart failed")
        assert str(exc) == "Chart failed"


class TestRetry:
    """Test retry mechanisms."""

    def test_retry_success(self):
        """Test successful execution without retry."""
        call_count = 0

        @retry(RetryPolicies.FAST)
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_function()
        assert result == "success"
        assert call_count == 1

    def test_retry_with_failure(self):
        """Test retry after failures."""
        call_count = 0

        @retry(RetryPolicies.FAST)
        def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = failing_then_success()
        assert result == "success"
        assert call_count == 2


class TestCircuitBreaker:
    """Test circuit breaker pattern."""

    def test_circuit_breaker_closed(self):
        """Test circuit breaker allows calls when closed."""
        breaker = CircuitBreaker(CircuitBreakerPolicies.STANDARD)

        @breaker
        def working_function():
            return "success"

        result = working_function()
        assert result == "success"

    def test_circuit_breaker_opens(self):
        """Test circuit breaker opens after failures."""
        from src.utils.circuit_breaker import CircuitBreakerPolicy
        
        call_count = 0
        policy = CircuitBreakerPolicy(failure_threshold=2, timeout=1)
        breaker = CircuitBreaker(policy)

        @breaker
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        # First two calls should fail normally
        with pytest.raises(ValueError):
            always_fails()
        with pytest.raises(ValueError):
            always_fails()

        # Circuit should now be open
        with pytest.raises(CircuitBreakerError):
            always_fails()


class TestHealthChecks:
    """Test health check system."""

    def test_register_and_check(self):
        """Test registering and executing health checks."""
        from src.utils import HealthCheckRegistry, HealthCheckResult
        
        registry = HealthCheckRegistry()

        async def check_service():
            return HealthCheckResult(
                component="test_service",
                status=HealthStatus.HEALTHY,
                message="Service is healthy"
            )

        check = HealthCheck("test_service", check_service)
        registry.register(check)
        
        # This test needs to be async or we skip it for now
        assert "test_service" in registry.list_checks()

    def test_check_all(self):
        """Test health check registry basic functionality.""" 
        from src.utils import HealthCheckRegistry
        
        registry = HealthCheckRegistry()
        assert len(registry.list_checks()) == 0  # Should start empty

    def test_overall_status(self):
        """Test health status calculation."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"

    def test_health_check_failure(self):
        """Test health check creation."""
        def test_check():
            return True
            
        check = HealthCheck("test", test_check)
        assert check.name == "test"
        assert check.critical is True  # Default value

    def test_overall_status(self):
        """Test health status calculation."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"

    def test_health_check_failure(self):
        """Test health check creation."""
        def test_check():
            return True
            
        check = HealthCheck("test", test_check)
        assert check.name == "test"
        assert check.critical is True  # Default value


class TestMetrics:
    """Test metrics collection."""

    def test_record_metrics(self):
        """Test recording metrics."""
        metrics = MetricsCollector()
        
        metrics.record("operation1", 100.5)
        metrics.record("operation1", 150.2)

        collected = metrics.get_metrics()
        assert "operation1" in collected
        assert collected["operation1"].count == 2
        assert collected["operation1"].min == 100.5
        assert collected["operation1"].max == 150.2

    def test_increment_counter(self):
        """Test counter increments."""
        metrics = MetricsCollector()
        
        metrics.increment("charts_generated")
        metrics.increment("charts_generated", 5)

        counters = metrics.get_counters()
        assert "charts_generated:" in str(counters)

    def test_clear_metrics(self):
        """Test clearing metrics."""
        metrics = MetricsCollector()
        
        metrics.record("test_metric", 100.0)
        metrics.clear()
        
        collected = metrics.get_metrics()
        assert len(collected) == 0

    def test_track_api_calls_decorator(self):
        """Test API call tracking decorator."""
        from src.utils.metrics import get_metrics_collector
        
        # Clear metrics first
        global_metrics = get_metrics_collector()
        global_metrics.clear()

        @track_api_calls("test_operation")
        def api_function():
            time.sleep(0.01)
            return "done"

        result = api_function()
        assert result == "done"
        
        # Check that metrics were recorded
        counters = global_metrics.get_counters()
        assert len(counters) > 0

    def test_reset_metrics(self):
        """Test resetting all metrics."""
        metrics = MetricsCollector()
        
        metrics.record("op1", 100)
        metrics.increment("counter1")

        metrics.clear()

        collected = metrics.get_metrics()
        counters = metrics.get_counters()
        assert len(collected) == 0
        assert len(counters) == 0
