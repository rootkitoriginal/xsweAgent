"""
Custom exceptions for xSwE Agent.
Provides structured error handling across the application.
"""


class XSWEBaseException(Exception):
    """Base exception for all xSwE Agent errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class RetryExhaustedError(XSWEBaseException):
    """Raised when retry attempts are exhausted."""

    pass


class CircuitBreakerError(XSWEBaseException):
    """Raised when circuit breaker is open."""

    pass


class ChartGenerationError(XSWEBaseException):
    """Raised when chart generation fails."""

    pass


class APIError(XSWEBaseException):
    """Raised when external API calls fail."""

    pass


class ConfigurationError(XSWEBaseException):
    """Raised when configuration is invalid."""

    pass
