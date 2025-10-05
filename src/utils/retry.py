"""
Retry and Circuit Breaker utilities.
Provides decorators for handling transient failures and service protection.
"""

import functools
import logging
import time
from typing import Any, Callable, Optional, Type, Union

from tenacity import (
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    retry as tenacity_retry,
)

from .exceptions import CircuitBreakerError, RetryExhaustedError

logger = logging.getLogger(__name__)


class RetryPolicies:
    """Pre-configured retry policies for common scenarios."""

    # Default policy: 3 attempts with exponential backoff
    DEFAULT = {
        "stop": stop_after_attempt(3),
        "wait": wait_exponential(multiplier=1, min=1, max=10),
        "reraise": True,
    }

    # Aggressive policy: 5 attempts with longer waits
    AGGRESSIVE = {
        "stop": stop_after_attempt(5),
        "wait": wait_exponential(multiplier=2, min=2, max=30),
        "reraise": True,
    }

    # Quick policy: 2 attempts with minimal wait
    QUICK = {
        "stop": stop_after_attempt(2),
        "wait": wait_exponential(multiplier=1, min=1, max=5),
        "reraise": True,
    }

    # API policy: optimized for external API calls
    API = {
        "stop": stop_after_attempt(3),
        "wait": wait_exponential(multiplier=2, min=2, max=20),
        "reraise": True,
    }


def retry(
    policy: dict = None,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None,
):
    """
    Retry decorator with configurable policy.

    Args:
        policy: Retry policy configuration (uses DEFAULT if not provided)
        exceptions: Tuple of exception types to retry on
        on_retry: Optional callback function called on each retry

    Example:
        @retry(RetryPolicies.DEFAULT)
        async def fetch_data():
            return await api_call()
    """
    if policy is None:
        policy = RetryPolicies.DEFAULT

    def decorator(func):
        @functools.wraps(func)
        @tenacity_retry(
            retry=retry_if_exception_type(exceptions),
            **policy,
        )
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                if on_retry:
                    on_retry(e)
                logger.warning(
                    f"Retrying {func.__name__} due to {type(e).__name__}: {str(e)}"
                )
                raise

        @functools.wraps(func)
        @tenacity_retry(
            retry=retry_if_exception_type(exceptions),
            **policy,
        )
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if on_retry:
                    on_retry(e)
                logger.warning(
                    f"Retrying {func.__name__} due to {type(e).__name__}: {str(e)}"
                )
                raise

        # Return appropriate wrapper based on function type
        import asyncio
        import inspect

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class CircuitBreaker:
    """
    Circuit breaker implementation for service protection.

    Prevents cascading failures by temporarily blocking calls to failing services.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: Type[Exception] = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if time.time() - self.last_failure_time >= self.timeout:
                self.state = "half-open"
                logger.info(f"Circuit breaker for {func.__name__} entering half-open state")
            else:
                raise CircuitBreakerError(
                    f"Circuit breaker is open for {func.__name__}",
                    details={"failure_count": self.failure_count},
                )

        try:
            result = func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
                logger.info(f"Circuit breaker for {func.__name__} closed")
            return result
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.error(
                    f"Circuit breaker opened for {func.__name__} "
                    f"after {self.failure_count} failures"
                )

            raise


def circuit_breaker(
    failure_threshold: int = 5,
    timeout: int = 60,
    expected_exception: Type[Exception] = Exception,
):
    """
    Circuit breaker decorator.

    Args:
        failure_threshold: Number of failures before opening circuit
        timeout: Seconds to wait before attempting to close circuit
        expected_exception: Exception type that triggers the circuit breaker

    Example:
        @circuit_breaker(failure_threshold=3, timeout=30)
        def external_api_call():
            return requests.get(url)
    """
    breaker = CircuitBreaker(failure_threshold, timeout, expected_exception)

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)

        return wrapper

    return decorator
