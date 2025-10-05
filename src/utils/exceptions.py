"""
Custom exceptions for xSwE Agent infrastructure.
"""


class XSWEAgentError(Exception):
    """Base exception for all xSwE Agent errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# Alias for backwards compatibility
XSWEBaseException = XSWEAgentError


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


class ChartGenerationError(XSWEAgentError):
    """Raised when chart generation fails."""

    pass


# Legacy aliases for backward compatibility
CircuitBreakerException = CircuitBreakerError
HealthCheckException = HealthCheckError
RetryException = RetryExhaustedError
