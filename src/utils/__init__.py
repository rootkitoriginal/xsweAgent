"""
Infrastructure utilities for error handling, retry logic, and monitoring.

This module provides robust infrastructure components for the xSwE Agent:
- Retry mechanisms with exponential backoff
- Circuit breaker patterns for external APIs
- Health checks for system components
- Metrics collection and monitoring
"""

from .retry import retry, RetryPolicy, RetryConfig
from .circuit_breaker import circuit_breaker, CircuitBreaker, CircuitState
from .health_checks import (
    HealthChecker, 
    HealthStatus, 
    HealthCheckResult,
    setup_default_health_checks,
    get_health_checker,
)
from .metrics import (
    MetricsCollector, 
    Counter, 
    Histogram, 
    Gauge,
    get_metrics_collector,
    track_api_calls,
    track_execution_time,
)
from .exceptions import (
    XSWEException,
    APIException,
    GitHubAPIException,
    GeminiAPIException,
    RetryException,
    CircuitBreakerException,
    HealthCheckException,
    ConfigurationException,
    ValidationException,
)

__all__ = [
    # Retry system
    "retry",
    "RetryPolicy", 
    "RetryConfig",
    # Circuit breaker
    "circuit_breaker",
    "CircuitBreaker",
    "CircuitState",
    # Health checks
    "HealthChecker",
    "HealthStatus",
    # Metrics
    "MetricsCollector",
    "Counter",
    "Histogram", 
    "Gauge",
    # Exceptions
    "XSWEException",
    "APIException",
    "RetryException",
    "CircuitBreakerException",
    "HealthCheckException",
]