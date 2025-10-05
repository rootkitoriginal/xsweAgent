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
from .health_checks import HealthChecker, HealthStatus
from .metrics import MetricsCollector, Counter, Histogram, Gauge
from .exceptions import (
    XSWEException,
    APIException,
    RetryException,
    CircuitBreakerException,
    HealthCheckException,
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