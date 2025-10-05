"""
Custom exception classes for xSwE Agent infrastructure.

This module defines the exception hierarchy for robust error handling
across all components of the system.
"""

from typing import Optional, Any, Dict


class XSWEException(Exception):
    """Base exception for all xSwE Agent related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "context": self.context,
        }


class APIException(XSWEException):
    """Exception for external API related errors."""
    
    def __init__(
        self,
        message: str,
        api_name: str,
        status_code: Optional[int] = None,
        response_data: Optional[Any] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.api_name = api_name
        self.status_code = status_code
        self.response_data = response_data
        
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "api_name": self.api_name,
            "status_code": self.status_code,
            "response_data": self.response_data,
        })
        return data


class GitHubAPIException(APIException):
    """Specific exception for GitHub API errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, api_name="github", **kwargs)


class GeminiAPIException(APIException):
    """Specific exception for Gemini AI API errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, api_name="gemini", **kwargs)


class RetryException(XSWEException):
    """Exception raised when retry attempts are exhausted."""
    
    def __init__(
        self,
        message: str,
        attempts: int,
        last_exception: Optional[Exception] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.attempts = attempts
        self.last_exception = last_exception
        
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "attempts": self.attempts,
            "last_exception": str(self.last_exception) if self.last_exception else None,
            "last_exception_type": (
                self.last_exception.__class__.__name__ 
                if self.last_exception else None
            ),
        })
        return data


class CircuitBreakerException(XSWEException):
    """Exception raised when circuit breaker is open."""
    
    def __init__(
        self,
        message: str,
        circuit_name: str,
        state: str,
        failure_count: int,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.circuit_name = circuit_name
        self.state = state
        self.failure_count = failure_count
        
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "circuit_name": self.circuit_name,
            "state": self.state,
            "failure_count": self.failure_count,
        })
        return data


class HealthCheckException(XSWEException):
    """Exception for health check failures."""
    
    def __init__(
        self,
        message: str,
        component: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.component = component
        self.status = status
        self.details = details or {}
        
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "component": self.component,
            "status": self.status,
            "details": self.details,
        })
        return data


class ConfigurationException(XSWEException):
    """Exception for configuration related errors."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.config_key = config_key
        self.config_value = config_value
        
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "config_key": self.config_key,
            "config_value": self.config_value,
        })
        return data


class ValidationException(XSWEException):
    """Exception for data validation errors."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        constraint: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.field = field
        self.value = value
        self.constraint = constraint
        
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "field": self.field,
            "value": self.value,
            "constraint": self.constraint,
        })
        return data