"""
Utils Module
Infrastructure components for retry logic, circuit breakers, health checks, and metrics.
"""

from .circuit_breaker import CircuitBreaker, CircuitBreakerPolicies
from .exceptions import (
    CircuitBreakerError,
    HealthCheckError,
    RateLimitError,
    RetryExhaustedError,
    XSWEAgentError,
)
from .health_checks import HealthCheck, HealthCheckRegistry, HealthStatus
from .metrics import MetricsCollector, track_api_calls
from .retry import BackoffStrategy, RetryPolicies, RetryPolicy, retry

__all__ = [
    # Retry
    "retry",
    "RetryPolicy",
    "RetryPolicies",
    "BackoffStrategy",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerPolicies",
    # Health Checks
    "HealthCheck",
    "HealthCheckRegistry",
    "HealthStatus",
    # Metrics
    "MetricsCollector",
    "track_api_calls",
    # Exceptions
    "XSWEAgentError",
    "RetryExhaustedError",
    "CircuitBreakerError",
    "HealthCheckError",
    "RateLimitError",
]
