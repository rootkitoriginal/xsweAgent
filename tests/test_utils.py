"""
Tests for utility infrastructure components.
"""

import pytest
from unittest.mock import Mock, patch
import time

from src.utils import (
    ChartGenerationError,
    CircuitBreakerError,
    HealthCheck,
    HealthStatus,
    MetricsCollector,
    RetryExhaustedError,
    RetryPolicies,
    XSWEBaseException,
    circuit_breaker,
    retry,
    track_execution_time,
)


class TestExceptions:
    """Test custom exceptions."""

    def test_base_exception(self):
        """Test base exception with details."""
        exc = XSWEBaseException("Test error", details={"key": "value"})
        assert exc.message == "Test error"
        assert exc.details == {"key": "value"}

    def test_chart_generation_error(self):
        """Test chart generation error."""
        exc = ChartGenerationError("Chart failed", details={"chart_type": "bar"})
        assert "Chart failed" in str(exc)
        assert exc.details["chart_type"] == "bar"


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

        @circuit_breaker(failure_threshold=3, timeout=60)
        def working_function():
            return "success"

        result = working_function()
        assert result == "success"

    def test_circuit_breaker_opens(self):
        """Test circuit breaker opens after failures."""
        call_count = 0

        @circuit_breaker(failure_threshold=2, timeout=1)
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
        health = HealthCheck()

        def check_service():
            return True

        health.register("test_service", check_service)
        result = health.check("test_service")

        assert result.name == "test_service"
        assert result.status == HealthStatus.HEALTHY

    def test_check_all(self):
        """Test checking all registered services."""
        health = HealthCheck()

        health.register("service1", lambda: True)
        health.register("service2", lambda: True)
        health.register("service3", lambda: False)

        results = health.check_all()

        assert len(results) == 3
        assert results["service1"].status == HealthStatus.HEALTHY
        assert results["service2"].status == HealthStatus.HEALTHY
        assert results["service3"].status == HealthStatus.UNHEALTHY

    def test_overall_status(self):
        """Test overall health status calculation."""
        health = HealthCheck()

        health.register("service1", lambda: True)
        health.register("service2", lambda: True)

        health.check_all()
        assert health.get_overall_status() == HealthStatus.HEALTHY

    def test_health_check_failure(self):
        """Test health check with exception."""
        health = HealthCheck()

        def failing_check():
            raise RuntimeError("Service down")

        health.register("failing_service", failing_check)
        result = health.check("failing_service")

        assert result.status == HealthStatus.UNHEALTHY
        assert "Service down" in result.message


class TestMetrics:
    """Test metrics collection."""

    def test_record_execution_time(self):
        """Test recording execution times."""
        metrics = MetricsCollector()
        
        metrics.record_execution_time("operation1", 100.5)
        metrics.record_execution_time("operation1", 150.2)

        stats = metrics.get_stats("operation1")
        assert stats["count"] == 2
        assert stats["min_ms"] == 100.5
        assert stats["max_ms"] == 150.2
        assert stats["avg_ms"] == pytest.approx(125.35)

    def test_increment_counter(self):
        """Test counter increments."""
        metrics = MetricsCollector()
        
        metrics.increment_counter("charts_generated")
        metrics.increment_counter("charts_generated", 5)

        assert metrics.get_counter("charts_generated") == 6

    def test_set_gauge(self):
        """Test gauge values."""
        metrics = MetricsCollector()
        
        metrics.set_gauge("memory_usage", 75.5)
        assert metrics.get_gauge("memory_usage") == 75.5

    def test_track_execution_time_decorator(self):
        """Test execution time tracking decorator."""
        metrics = MetricsCollector()

        @track_execution_time("test_operation")
        def slow_function():
            time.sleep(0.01)
            return "done"

        result = slow_function()
        assert result == "done"
        
        # Check that execution time was recorded
        from src.utils.metrics import get_metrics_collector
        global_metrics = get_metrics_collector()
        stats = global_metrics.get_stats("test_operation")
        assert stats["count"] >= 1
        assert stats["min_ms"] > 0

    def test_reset_metrics(self):
        """Test resetting all metrics."""
        metrics = MetricsCollector()
        
        metrics.record_execution_time("op1", 100)
        metrics.increment_counter("counter1")
        metrics.set_gauge("gauge1", 50)

        metrics.reset()

        assert metrics.get_counter("counter1") == 0
        assert metrics.get_gauge("gauge1") is None
        assert metrics.get_stats("op1")["count"] == 0
