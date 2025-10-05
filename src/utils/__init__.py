"""
Utils Module
Infrastructure components for retry logic, circuit breakers, health checks, and metrics.
"""

from .circuit_breaker import CircuitBreaker, CircuitBreakerPolicies
from .exceptions import (
    ChartGenerationError,
    CircuitBreakerError,
    HealthCheckError,
    RateLimitError,
    RetryExhaustedError,
    XSWEAgentError,
)
from .health_checks import (
    HealthCheck,
    HealthCheckRegistry,
    HealthCheckResult,
    HealthStatus,
    get_health_check_registry,
)
from .metrics import MetricsCollector, get_metrics_collector, track_api_calls
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
    "HealthCheckResult",
    "HealthStatus",
    "get_health_check_registry",
    # Metrics
    "MetricsCollector",
    "get_metrics_collector",
    "track_api_calls",
    # Exceptions
    "XSWEAgentError",
    "RetryExhaustedError",
    "CircuitBreakerError",
    "HealthCheckError",
    "RateLimitError",
    "ChartGenerationError",
]
