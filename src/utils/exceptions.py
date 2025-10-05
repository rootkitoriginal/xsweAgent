"""
Custom exceptions for xSwE Agent infrastructure.
"""


class XSWEAgentError(Exception):
    """Base exception for all xSwE Agent errors."""

    pass


class RetryExhaustedError(XSWEAgentError):
    """Raised when retry attempts are exhausted."""

    pass


class CircuitBreakerError(XSWEAgentError):
    """Raised when circuit breaker is open."""

    pass


class HealthCheckError(XSWEAgentError):
    """Raised when health check fails."""

    pass


class RateLimitError(XSWEAgentError):
    """Raised when rate limit is exceeded."""

    pass
