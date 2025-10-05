"""
Tests for infrastructure utilities (retry, circuit breaker, metrics, health checks).
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.utils import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitBreakerPolicies,
    CircuitState,
    HealthCheck,
    HealthStatus,
    MetricsTracker,
    RetryExhaustedError,
    RetryPolicies,
    retry,
    track_api_calls,
)
from src.utils.circuit_breaker import CircuitBreakerConfig


# ========== Retry Tests ==========


@pytest.mark.asyncio
async def test_retry_success():
    """Test successful execution with retry decorator."""
    call_count = 0

    @retry(RetryPolicies.FAST_FAIL)
    async def successful_function():
        nonlocal call_count
        call_count += 1
        return "success"

    result = await successful_function()
    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_with_failures_then_success():
    """Test retry logic with initial failures then success."""
    call_count = 0

    @retry(RetryPolicies.FAST_FAIL)
    async def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Temporary error")
        return "success"

    result = await flaky_function()
    assert result == "success"
    assert call_count == 2


@pytest.mark.asyncio
async def test_retry_exhausted():
    """Test that retry exhausts after max attempts."""

    @retry(RetryPolicies.FAST_FAIL)
    async def always_fails():
        raise ValueError("Always fails")

    with pytest.raises(RetryExhaustedError):
        await always_fails()


# ========== Circuit Breaker Tests ==========


@pytest.mark.asyncio
async def test_circuit_breaker_closed_state():
    """Test circuit breaker in closed (normal) state."""
    config = CircuitBreakerConfig(failure_threshold=3)
    breaker = CircuitBreaker(config)

    async def successful_func():
        return "success"

    result = await breaker.call(successful_func)
    assert result == "success"
    assert breaker.get_state() == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures():
    """Test circuit breaker opens after threshold failures."""
    config = CircuitBreakerConfig(failure_threshold=3, timeout=0.1)
    breaker = CircuitBreaker(config)

    async def failing_func():
        raise ValueError("Failure")

    # Trigger failures to open circuit
    for _ in range(3):
        try:
            await breaker.call(failing_func)
        except ValueError:
            pass

    assert breaker.get_state() == CircuitState.OPEN

    # Next call should raise circuit breaker error
    with pytest.raises(CircuitBreakerOpenError):
        await breaker.call(failing_func)


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_recovery():
    """Test circuit breaker recovery through half-open state."""
    config = CircuitBreakerConfig(
        failure_threshold=2, success_threshold=1, timeout=0.1
    )
    breaker = CircuitBreaker(config)

    async def failing_func():
        raise ValueError("Failure")

    async def success_func():
        return "success"

    # Open the circuit
    for _ in range(2):
        try:
            await breaker.call(failing_func)
        except ValueError:
            pass

    assert breaker.get_state() == CircuitState.OPEN

    # Wait for timeout
    await asyncio.sleep(0.15)

    # Should be half-open now, success should close it
    result = await breaker.call(success_func)
    assert result == "success"
    assert breaker.get_state() == CircuitState.CLOSED


# ========== Metrics Tests ==========


def test_metrics_tracker_records_call():
    """Test metrics tracker records API calls."""
    tracker = MetricsTracker()

    tracker.record_call("test_operation", duration_ms=100.0, success=True)

    metrics = tracker.get_metrics("test_operation")
    assert metrics is not None
    assert metrics.total_calls == 1
    assert metrics.successful_calls == 1
    assert metrics.failed_calls == 0
    assert metrics.avg_duration_ms == 100.0


def test_metrics_tracker_aggregates_multiple_calls():
    """Test metrics tracker aggregates multiple calls."""
    tracker = MetricsTracker()

    tracker.record_call("test_op", duration_ms=100.0, success=True)
    tracker.record_call("test_op", duration_ms=200.0, success=True)
    tracker.record_call("test_op", duration_ms=150.0, success=False)

    metrics = tracker.get_metrics("test_op")
    assert metrics.total_calls == 3
    assert metrics.successful_calls == 2
    assert metrics.failed_calls == 1
    assert metrics.avg_duration_ms == 150.0
    assert metrics.min_duration_ms == 100.0
    assert metrics.max_duration_ms == 200.0


@pytest.mark.asyncio
async def test_track_api_calls_decorator():
    """Test track_api_calls decorator records metrics."""
    from src.utils.metrics import get_metrics_tracker

    tracker = get_metrics_tracker()
    tracker.clear_metrics()

    @track_api_calls("test_decorated")
    async def decorated_function():
        await asyncio.sleep(0.01)
        return "result"

    result = await decorated_function()
    assert result == "result"

    metrics = tracker.get_metrics("test_decorated")
    assert metrics is not None
    assert metrics.total_calls == 1
    assert metrics.successful_calls == 1


# ========== Health Check Tests ==========


@pytest.mark.asyncio
async def test_health_check_healthy():
    """Test health check reports healthy status."""

    async def healthy_check():
        return True

    health_check = HealthCheck("test_service", healthy_check)
    result = await health_check.perform_check()

    assert result.status == HealthStatus.HEALTHY
    assert result.name == "test_service"
    assert health_check.is_healthy()


@pytest.mark.asyncio
async def test_health_check_unhealthy():
    """Test health check reports unhealthy status."""

    async def unhealthy_check():
        raise Exception("Service down")

    health_check = HealthCheck("test_service", unhealthy_check)
    result = await health_check.perform_check()

    assert result.status == HealthStatus.UNHEALTHY
    assert not health_check.is_healthy()


@pytest.mark.asyncio
async def test_health_check_timeout():
    """Test health check handles timeout."""

    async def slow_check():
        await asyncio.sleep(1.0)
        return True

    health_check = HealthCheck("test_service", slow_check, timeout=0.1)
    result = await health_check.perform_check()

    assert result.status == HealthStatus.UNHEALTHY
    assert "timed out" in result.message.lower()


@pytest.mark.asyncio
async def test_health_check_monitoring_loop():
    """Test continuous health monitoring."""

    check_count = 0

    async def check_func():
        nonlocal check_count
        check_count += 1
        return True

    health_check = HealthCheck("test_service", check_func, interval=0.1)

    # Start monitoring
    await health_check.start_monitoring()
    await asyncio.sleep(0.35)  # Should perform ~3 checks
    await health_check.stop_monitoring()

    assert check_count >= 2  # At least 2 checks should have run
