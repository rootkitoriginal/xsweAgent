"""
Custom exception classes for xSwE Agent infrastructure.
"""


class XSWEAgentError(Exception):
    """Base exception for xSwE Agent errors."""

    pass


class AIServiceError(XSWEAgentError):
    """Base exception for AI service errors."""

    pass


class RateLimitError(AIServiceError):
    """Raised when API rate limit is exceeded."""

    pass


class RetryExhaustedError(AIServiceError):
    """Raised when all retry attempts are exhausted."""

    pass


class CircuitBreakerOpenError(AIServiceError):
    """Raised when circuit breaker is open."""

    pass


class ValidationError(XSWEAgentError):
    """Raised when input/output validation fails."""

    pass


class SafetyError(XSWEAgentError):
    """Raised when safety checks fail."""

    pass
