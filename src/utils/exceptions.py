"""
Custom exceptions for xSwE Agent.
Provides a hierarchy of exceptions for better error handling.
"""


class XSWEException(Exception):
    """Base exception for all xSwE Agent errors."""

    pass


class GitHubAPIException(XSWEException):
    """Exception raised for GitHub API errors."""

    pass


class RateLimitException(GitHubAPIException):
    """Exception raised when GitHub API rate limit is exceeded."""

    pass


class AnalyticsException(XSWEException):
    """Exception raised during analytics processing."""

    pass


class GeminiException(XSWEException):
    """Exception raised for Gemini API errors."""

    pass


class ConfigurationException(XSWEException):
    """Exception raised for configuration errors."""

    pass


class CircuitBreakerException(XSWEException):
    """Exception raised when circuit breaker is open."""

    pass
