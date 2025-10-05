"""
Infrastructure utilities for xSwE Agent.
Provides retry, circuit breaker, metrics, and health check functionality.
"""

from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerPolicies,
    CircuitBreakerPolicy,
    CircuitState,
    circuit_breaker,
    get_circuit_breaker,
)
from .exceptions import (
    AnalyticsException,
    CircuitBreakerException,
    ConfigurationException,
    GeminiException,
    GitHubAPIException,
    RateLimitException,
    XSWEException,
)
from .health_checks import (
    CallableHealthCheck,
    HealthCheck,
    HealthCheckRegistry,
    HealthCheckResult,
    HealthStatus,
    get_health_registry,
    register_health_check,
)
from .metrics import (
    MetricPoint,
    MetricsCollector,
    get_metrics_collector,
    track_api_calls,
)
from .retry import (
    RetryPolicies,
    RetryPolicy,
    create_retry_decorator,
    retry_with_policy,
)

__all__ = [
    # Exceptions
    "XSWEException",
    "GitHubAPIException",
    "RateLimitException",
    "AnalyticsException",
    "GeminiException",
    "ConfigurationException",
    "CircuitBreakerException",
    # Retry
    "RetryPolicy",
    "RetryPolicies",
    "retry_with_policy",
    "create_retry_decorator",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerPolicy",
    "CircuitBreakerPolicies",
    "CircuitState",
    "circuit_breaker",
    "get_circuit_breaker",
    # Metrics
    "MetricsCollector",
    "MetricPoint",
    "get_metrics_collector",
    "track_api_calls",
    # Health Checks
    "HealthCheck",
    "CallableHealthCheck",
    "HealthCheckRegistry",
    "HealthCheckResult",
    "HealthStatus",
    "get_health_registry",
    "register_health_check",
]
