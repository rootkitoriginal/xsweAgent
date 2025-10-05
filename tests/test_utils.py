"""
Tests for infrastructure utilities (retry, circuit breaker, metrics, health checks).
"""

import asyncio
from datetime import datetime

import pytest

from src.utils import (
    AnalyticsException,
    CircuitBreakerException,
    CircuitBreakerPolicies,
    RetryPolicies,
    circuit_breaker,
    get_circuit_breaker,
    get_health_registry,
    get_metrics_collector,
    register_health_check,
    retry_with_policy,
    track_api_calls,
)


# Retry Tests
@pytest.mark.asyncio
async def test_retry_policy_success():
    """Test retry succeeds on first attempt."""
    call_count = 0

    @retry_with_policy(RetryPolicies.ANALYTICS)
    async def successful_function():
        nonlocal call_count
        call_count += 1
        return "success"

    result = await successful_function()
    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_policy_eventual_success():
    """Test retry succeeds after failures."""
    call_count = 0

    @retry_with_policy(RetryPolicies.ANALYTICS)
    async def eventually_successful():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise Exception("Temporary failure")
        return "success"

    result = await eventually_successful()
    assert result == "success"
    assert call_count == 2


@pytest.mark.asyncio
async def test_retry_policy_max_attempts():
    """Test retry gives up after max attempts."""
    call_count = 0

    @retry_with_policy(RetryPolicies.ANALYTICS)
    async def always_fails():
        nonlocal call_count
        call_count += 1
        raise Exception("Persistent failure")

    with pytest.raises(Exception, match="Persistent failure"):
        await always_fails()

    assert call_count == RetryPolicies.ANALYTICS.max_attempts


# Circuit Breaker Tests
@pytest.mark.asyncio
async def test_circuit_breaker_normal_operation():
    """Test circuit breaker allows calls when closed."""
    call_count = 0

    @circuit_breaker(name="test_cb_normal", policy=CircuitBreakerPolicies.DEFAULT)
    async def normal_function():
        nonlocal call_count
        call_count += 1
        return "success"

    result = await normal_function()
    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_circuit_breaker_opens_on_failures():
    """Test circuit breaker opens after threshold failures."""
    call_count = 0
    policy = CircuitBreakerPolicies.DEFAULT
    
    # Reset the circuit breaker
    breaker = get_circuit_breaker("test_cb_failures", policy)
    breaker.reset()

    @circuit_breaker(name="test_cb_failures", policy=policy)
    async def failing_function():
        nonlocal call_count
        call_count += 1
        raise Exception("Function failure")

    # Call until circuit opens
    for _ in range(policy.failure_threshold):
        try:
            await failing_function()
        except Exception:
            pass

    # Circuit should be open now
    with pytest.raises(CircuitBreakerException):
        await failing_function()

    # Verify we didn't make extra calls after circuit opened
    assert call_count == policy.failure_threshold


# Metrics Tests
def test_metrics_counter():
    """Test counter metrics."""
    collector = get_metrics_collector()
    collector.reset()

    collector.increment_counter("test_counter", 1.0)
    collector.increment_counter("test_counter", 2.0)

    assert collector.get_counter("test_counter") == 3.0


def test_metrics_gauge():
    """Test gauge metrics."""
    collector = get_metrics_collector()
    collector.reset()

    collector.set_gauge("test_gauge", 42.0)
    assert collector.get_gauge("test_gauge") == 42.0

    collector.set_gauge("test_gauge", 100.0)
    assert collector.get_gauge("test_gauge") == 100.0


def test_metrics_histogram():
    """Test histogram metrics."""
    collector = get_metrics_collector()
    collector.reset()

    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    for value in values:
        collector.observe_histogram("test_histogram", value)

    stats = collector.get_histogram_stats("test_histogram")
    assert stats["count"] == 5
    assert stats["sum"] == 15.0
    assert stats["min"] == 1.0
    assert stats["max"] == 5.0
    assert stats["avg"] == 3.0


@pytest.mark.asyncio
async def test_track_api_calls_decorator():
    """Test track_api_calls decorator."""
    collector = get_metrics_collector()
    collector.reset()

    @track_api_calls("test_api")
    async def test_function():
        await asyncio.sleep(0.01)
        return "success"

    result = await test_function()
    assert result == "success"

    # Check metrics were recorded
    assert collector.get_counter("test_api_calls_total", status="success") == 1.0


# Health Checks Tests
@pytest.mark.asyncio
async def test_health_check_registration():
    """Test health check registration."""
    registry = get_health_registry()

    async def check_healthy():
        return True

    register_health_check("test_check", check_healthy)
    checks = registry.get_registered_checks()
    assert "test_check" in checks


@pytest.mark.asyncio
async def test_health_check_execution():
    """Test health check execution."""
    registry = get_health_registry()

    async def check_always_healthy():
        return True

    register_health_check("test_check_exec", check_always_healthy)
    results = await registry.check_all()

    assert "test_check_exec" in results
    assert results["test_check_exec"].status.value == "healthy"


@pytest.mark.asyncio
async def test_health_check_failure():
    """Test health check failure detection."""
    registry = get_health_registry()

    async def check_unhealthy():
        return False

    register_health_check("test_check_fail", check_unhealthy)
    results = await registry.check_all()

    assert "test_check_fail" in results
    assert results["test_check_fail"].status.value == "unhealthy"


# Integration Tests
@pytest.mark.asyncio
async def test_retry_with_metrics():
    """Test retry mechanism with metrics tracking."""
    collector = get_metrics_collector()
    collector.reset()
    call_count = 0

    @retry_with_policy(RetryPolicies.ANALYTICS)
    @track_api_calls("test_retry_metrics")
    async def function_with_retry():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise Exception("Temporary failure")
        return "success"

    result = await function_with_retry()
    assert result == "success"
    assert call_count == 2

    # Verify metrics were recorded for successful call
    assert collector.get_counter("test_retry_metrics_calls_total", status="success") == 1.0


@pytest.mark.asyncio
async def test_circuit_breaker_with_metrics():
    """Test circuit breaker with metrics tracking."""
    collector = get_metrics_collector()
    collector.reset()
    
    # Reset the circuit breaker
    breaker = get_circuit_breaker("test_cb_metrics", CircuitBreakerPolicies.DEFAULT)
    breaker.reset()

    @circuit_breaker(name="test_cb_metrics", policy=CircuitBreakerPolicies.DEFAULT)
    @track_api_calls("test_cb_api")
    async def function_with_cb():
        return "success"

    result = await function_with_cb()
    assert result == "success"

    # Verify metrics
    assert collector.get_counter("test_cb_api_calls_total", status="success") == 1.0
