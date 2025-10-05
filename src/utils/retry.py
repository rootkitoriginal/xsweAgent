"""
Retry mechanism with exponential backoff for robust API calls.

This module provides decorators and utilities for implementing retry logic
with configurable policies, exponential backoff, jitter, and comprehensive
error handling.
"""

import asyncio
import functools
import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from .exceptions import RetryException

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class BackoffStrategy(Enum):
    """Backoff strategies for retry delays."""
    
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"
    RANDOM = "random"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    backoff_factor: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.1
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
    exclude_exceptions: Tuple[Type[Exception], ...] = ()
    timeout_per_attempt: Optional[float] = None
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.base_delay < 0:
            raise ValueError("base_delay must be >= 0")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if self.backoff_factor <= 0:
            raise ValueError("backoff_factor must be > 0")
        if not 0 <= self.jitter_factor <= 1:
            raise ValueError("jitter_factor must be between 0 and 1")


@dataclass
class RetryPolicy:
    """Retry policy with predefined configurations."""
    
    name: str
    config: RetryConfig
    description: str = ""
    
    @classmethod
    def github_api(cls) -> "RetryPolicy":
        """Retry policy optimized for GitHub API calls."""
        return cls(
            name="github_api",
            description="GitHub API retry policy with rate limit handling",
            config=RetryConfig(
                max_attempts=5,
                base_delay=2.0,
                max_delay=120.0,
                backoff_strategy=BackoffStrategy.EXPONENTIAL,
                backoff_factor=2.0,
                jitter=True,
                exceptions=(
                    ConnectionError,
                    TimeoutError,
                    # Add specific HTTP exceptions as needed
                ),
                exclude_exceptions=(
                    # Don't retry on authentication errors
                    ValueError,  # Placeholder - replace with actual auth exceptions
                ),
            )
        )
    
    @classmethod
    def gemini_api(cls) -> "RetryPolicy":
        """Retry policy optimized for Gemini AI API calls."""
        return cls(
            name="gemini_api",
            description="Gemini AI API retry policy with quota handling",
            config=RetryConfig(
                max_attempts=4,
                base_delay=1.5,
                max_delay=60.0,
                backoff_strategy=BackoffStrategy.EXPONENTIAL,
                backoff_factor=2.5,
                jitter=True,
                exceptions=(
                    ConnectionError,
                    TimeoutError,
                ),
                exclude_exceptions=(
                    # Don't retry on API key or quota exceeded errors
                    ValueError,  # Placeholder
                ),
            )
        )
    
    @classmethod
    def database(cls) -> "RetryPolicy":
        """Retry policy for database operations."""
        return cls(
            name="database",
            description="Database operations retry policy",
            config=RetryConfig(
                max_attempts=3,
                base_delay=0.5,
                max_delay=10.0,
                backoff_strategy=BackoffStrategy.EXPONENTIAL,
                backoff_factor=2.0,
                jitter=True,
            )
        )
    
    @classmethod
    def fast_operations(cls) -> "RetryPolicy":
        """Retry policy for fast, low-latency operations."""
        return cls(
            name="fast_operations",
            description="Fast retry policy for low-latency operations",
            config=RetryConfig(
                max_attempts=2,
                base_delay=0.1,
                max_delay=2.0,
                backoff_strategy=BackoffStrategy.LINEAR,
                backoff_factor=1.5,
                jitter=False,
            )
        )


class RetryContext:
    """Context information for retry attempts."""
    
    def __init__(self, config: RetryConfig):
        self.config = config
        self.attempt = 0
        self.start_time = time.time()
        self.last_exception: Optional[Exception] = None
        self.delays: List[float] = []
        
    def calculate_delay(self) -> float:
        """Calculate delay for next retry attempt."""
        if self.config.backoff_strategy == BackoffStrategy.FIXED:
            delay = self.config.base_delay
        elif self.config.backoff_strategy == BackoffStrategy.LINEAR:
            delay = self.config.base_delay * self.attempt
        elif self.config.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (self.config.backoff_factor ** (self.attempt - 1))
        elif self.config.backoff_strategy == BackoffStrategy.RANDOM:
            delay = random.uniform(0, self.config.base_delay * self.attempt)
        else:
            delay = self.config.base_delay
            
        # Apply jitter if enabled
        if self.config.jitter and delay > 0:
            jitter_amount = delay * self.config.jitter_factor
            jitter = random.uniform(-jitter_amount, jitter_amount)
            delay = max(0, delay + jitter)
            
        # Cap at max_delay
        delay = min(delay, self.config.max_delay)
        
        self.delays.append(delay)
        return delay
    
    def should_retry(self, exception: Exception) -> bool:
        """Determine if we should retry based on exception and config."""
        # Check if we've exceeded max attempts
        if self.attempt >= self.config.max_attempts:
            return False
            
        # Check if exception should be excluded from retries
        if self.config.exclude_exceptions and isinstance(exception, self.config.exclude_exceptions):
            return False
            
        # Check if exception is in the retry list
        if self.config.exceptions and not isinstance(exception, self.config.exceptions):
            return False
            
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retry statistics."""
        return {
            "attempts": self.attempt,
            "total_time": time.time() - self.start_time,
            "delays": self.delays,
            "last_exception": str(self.last_exception) if self.last_exception else None,
            "success": self.last_exception is None,
        }


def retry(
    config: Optional[RetryConfig] = None,
    policy: Optional[RetryPolicy] = None,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    **kwargs,
) -> Callable[[F], F]:
    """
    Decorator for adding retry logic to functions and coroutines.
    
    Args:
        config: Retry configuration object
        policy: Predefined retry policy  
        max_attempts: Maximum number of retry attempts (if config not provided)
        base_delay: Base delay between retries (if config not provided)
        **kwargs: Additional configuration parameters
        
    Returns:
        Decorated function with retry logic
        
    Examples:
        @retry(max_attempts=5, base_delay=2.0)
        async def github_api_call():
            pass
            
        @retry(policy=RetryPolicy.gemini_api())
        async def gemini_call():
            pass
            
        @retry(RetryConfig(max_attempts=3, jitter=False))
        def sync_operation():
            pass
    """
    # Resolve configuration
    if policy:
        retry_config = policy.config
    elif config:
        retry_config = config
    else:
        # Build config from individual parameters
        retry_config = RetryConfig(
            max_attempts=max_attempts,
            base_delay=base_delay,
            **kwargs
        )
    
    def decorator(func: F) -> F:
        if asyncio.iscoroutinefunction(func):
            return _async_retry_wrapper(func, retry_config)
        else:
            return _sync_retry_wrapper(func, retry_config)
    
    return decorator


def _sync_retry_wrapper(func: Callable, config: RetryConfig) -> Callable:
    """Wrapper for synchronous functions."""
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        context = RetryContext(config)
        
        while True:
            context.attempt += 1
            
            try:
                # Apply timeout if configured
                if config.timeout_per_attempt:
                    # Note: This is a simple approach. For production,
                    # consider using signal.alarm or threading.Timer
                    start = time.time()
                    result = func(*args, **kwargs)
                    if time.time() - start > config.timeout_per_attempt:
                        raise TimeoutError(f"Function exceeded timeout of {config.timeout_per_attempt}s")
                else:
                    result = func(*args, **kwargs)
                    
                # Success - log and return
                if context.attempt > 1:
                    logger.info(
                        f"Function {func.__name__} succeeded on attempt {context.attempt}",
                        extra={"retry_stats": context.get_stats()}
                    )
                return result
                
            except Exception as e:
                context.last_exception = e
                
                if not context.should_retry(e):
                    logger.error(
                        f"Function {func.__name__} failed after {context.attempt} attempts",
                        extra={"retry_stats": context.get_stats()},
                        exc_info=True
                    )
                    raise RetryException(
                        f"Failed after {context.attempt} attempts: {str(e)}",
                        attempts=context.attempt,
                        last_exception=e,
                    )
                
                # Calculate delay and sleep
                delay = context.calculate_delay()
                logger.warning(
                    f"Function {func.__name__} failed on attempt {context.attempt}, "
                    f"retrying in {delay:.2f}s: {str(e)}"
                )
                time.sleep(delay)
    
    return wrapper


def _async_retry_wrapper(func: Callable, config: RetryConfig) -> Callable:
    """Wrapper for asynchronous functions."""
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        context = RetryContext(config)
        
        while True:
            context.attempt += 1
            
            try:
                # Apply timeout if configured
                if config.timeout_per_attempt:
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=config.timeout_per_attempt
                    )
                else:
                    result = await func(*args, **kwargs)
                    
                # Success - log and return
                if context.attempt > 1:
                    logger.info(
                        f"Async function {func.__name__} succeeded on attempt {context.attempt}",
                        extra={"retry_stats": context.get_stats()}
                    )
                return result
                
            except Exception as e:
                context.last_exception = e
                
                if not context.should_retry(e):
                    logger.error(
                        f"Async function {func.__name__} failed after {context.attempt} attempts",
                        extra={"retry_stats": context.get_stats()},
                        exc_info=True
                    )
                    raise RetryException(
                        f"Failed after {context.attempt} attempts: {str(e)}",
                        attempts=context.attempt,
                        last_exception=e,
                    )
                
                # Calculate delay and sleep
                delay = context.calculate_delay()
                logger.warning(
                    f"Async function {func.__name__} failed on attempt {context.attempt}, "
                    f"retrying in {delay:.2f}s: {str(e)}"
                )
                await asyncio.sleep(delay)
    
    return wrapper


# Convenience functions for common retry patterns
def retry_on_exception(exception_types: Tuple[Type[Exception], ...], **kwargs):
    """Retry only on specific exception types."""
    config = RetryConfig(exceptions=exception_types, **kwargs)
    return retry(config=config)


def retry_github_api(**kwargs):
    """Retry with GitHub API optimized settings."""
    return retry(policy=RetryPolicy.github_api())


def retry_gemini_api(**kwargs):
    """Retry with Gemini API optimized settings."""
    return retry(policy=RetryPolicy.gemini_api())


def retry_database(**kwargs):
    """Retry with database optimized settings."""
    return retry(policy=RetryPolicy.database())


# Predefined retry policies for convenience
class RetryPolicies:
    """Collection of predefined retry policies."""
    
    FAST = RetryPolicy.fast_operations()
    STANDARD = RetryPolicy.fast_operations()
    GITHUB_API = RetryPolicy.github_api()
    GEMINI_API = RetryPolicy.gemini_api()
    DATABASE = RetryPolicy.database()