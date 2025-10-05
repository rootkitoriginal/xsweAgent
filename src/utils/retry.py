"""
Retry logic with exponential backoff for resilient API calls.
"""

import asyncio
import logging
import random
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional, Type, Union

from .exceptions import RetryExhaustedError

logger = logging.getLogger(__name__)


class BackoffStrategy(Enum):
    """Backoff strategies for retry logic."""

    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    EXPONENTIAL_JITTER = "exponential_jitter"


@dataclass
class RetryPolicy:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL_JITTER
    retryable_exceptions: tuple = (Exception,)

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt number."""
        if self.backoff_strategy == BackoffStrategy.LINEAR:
            delay = self.base_delay * attempt
        elif self.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            delay = self.base_delay * (2 ** (attempt - 1))
        else:  # EXPONENTIAL_JITTER
            delay = self.base_delay * (2 ** (attempt - 1))
            # Add jitter: random value between 0 and calculated delay
            delay = delay * (0.5 + random.random() * 0.5)

        return min(delay, self.max_delay)


class RetryPolicies:
    """Pre-configured retry policies for common scenarios."""

    # AI API calls - moderate retries with jitter
    GEMINI_API = RetryPolicy(
        max_attempts=3,
        base_delay=2.0,
        max_delay=30.0,
        backoff_strategy=BackoffStrategy.EXPONENTIAL_JITTER,
    )

    # GitHub API - more aggressive for rate limits
    GITHUB_API = RetryPolicy(
        max_attempts=5,
        base_delay=1.0,
        max_delay=60.0,
        backoff_strategy=BackoffStrategy.EXPONENTIAL_JITTER,
    )

    # Quick operations - fast failure
    FAST_FAIL = RetryPolicy(
        max_attempts=2,
        base_delay=0.5,
        max_delay=2.0,
        backoff_strategy=BackoffStrategy.LINEAR,
    )

    # Critical operations - aggressive retry
    CRITICAL = RetryPolicy(
        max_attempts=10,
        base_delay=1.0,
        max_delay=120.0,
        backoff_strategy=BackoffStrategy.EXPONENTIAL_JITTER,
    )


def retry(
    policy: Union[RetryPolicy, None] = None,
    max_attempts: Optional[int] = None,
    base_delay: Optional[float] = None,
):
    """
    Decorator to add retry logic to async functions.

    Args:
        policy: RetryPolicy to use. If None, uses default policy.
        max_attempts: Override max attempts from policy.
        base_delay: Override base delay from policy.

    Example:
        @retry(RetryPolicies.GEMINI_API)
        async def call_api():
            # API call logic
            pass
    """
    if policy is None:
        policy = RetryPolicy()

    # Allow overriding specific parameters
    if max_attempts is not None:
        policy.max_attempts = max_attempts
    if base_delay is not None:
        policy.base_delay = base_delay

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(1, policy.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except policy.retryable_exceptions as e:
                    last_exception = e
                    if attempt >= policy.max_attempts:
                        logger.error(
                            f"Retry exhausted for {func.__name__} after {attempt} attempts: {e}"
                        )
                        raise RetryExhaustedError(
                            f"Failed after {attempt} attempts: {str(e)}"
                        ) from e

                    delay = policy.calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt}/{policy.max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)

            # Should never reach here, but just in case
            if last_exception:
                raise RetryExhaustedError(
                    f"Unexpected retry exhaustion for {func.__name__}"
                ) from last_exception

        return wrapper

    return decorator
