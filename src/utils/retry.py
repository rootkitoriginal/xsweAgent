"""
Retry logic with configurable backoff strategies.
"""

import asyncio
import logging
import random
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Callable, Optional, Type, Union

from .exceptions import RetryExhaustedError

logger = logging.getLogger(__name__)


class BackoffStrategy(Enum):
    """Backoff strategies for retry logic."""

    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    LINEAR_JITTER = "linear_jitter"
    EXPONENTIAL_JITTER = "exponential_jitter"


@dataclass
class RetryPolicy:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    exceptions: tuple = (Exception,)


class RetryPolicies:
    """Pre-configured retry policies for common scenarios."""

    # Fast retry for quick operations
    FAST = RetryPolicy(
        max_attempts=2,
        base_delay=0.5,
        max_delay=5.0,
        backoff_strategy=BackoffStrategy.LINEAR_JITTER,
    )

    # Standard retry for most operations
    STANDARD = RetryPolicy(
        max_attempts=3,
        base_delay=1.0,
        max_delay=30.0,
        backoff_strategy=BackoffStrategy.EXPONENTIAL_JITTER,
    )

    # Aggressive retry for critical operations
    AGGRESSIVE = RetryPolicy(
        max_attempts=5,
        base_delay=2.0,
        max_delay=60.0,
        backoff_strategy=BackoffStrategy.EXPONENTIAL_JITTER,
    )

    # MCP-specific retry policy
    MCP_TOOLS = RetryPolicy(
        max_attempts=2,
        base_delay=1.0,
        max_delay=10.0,
        backoff_strategy=BackoffStrategy.LINEAR_JITTER,
    )

    # GitHub API retry policy
    GITHUB_API = RetryPolicy(
        max_attempts=3,
        base_delay=2.0,
        max_delay=30.0,
        backoff_strategy=BackoffStrategy.EXPONENTIAL_JITTER,
    )

    # AI/Gemini API retry policy
    AI_API = RetryPolicy(
        max_attempts=3,
        base_delay=1.0,
        max_delay=20.0,
        backoff_strategy=BackoffStrategy.EXPONENTIAL_JITTER,
    )


def calculate_delay(
    attempt: int, policy: RetryPolicy, jitter: bool = False
) -> float:
    """Calculate delay for next retry attempt."""
    if policy.backoff_strategy in (
        BackoffStrategy.LINEAR,
        BackoffStrategy.LINEAR_JITTER,
    ):
        delay = policy.base_delay * attempt
    else:  # EXPONENTIAL
        delay = policy.base_delay * (2 ** (attempt - 1))

    delay = min(delay, policy.max_delay)

    if jitter or "jitter" in policy.backoff_strategy.value:
        # Add jitter: ±25% of the delay
        jitter_amount = delay * 0.25
        delay = delay + random.uniform(-jitter_amount, jitter_amount)
        delay = max(0, delay)  # Ensure non-negative

    return delay


def retry(
    policy: Union[RetryPolicy, Type[RetryPolicy]] = RetryPolicies.STANDARD
):
    """
    Decorator for retrying functions with configurable backoff.

    Args:
        policy: RetryPolicy instance or class defining retry behavior

    Example:
        @retry(RetryPolicies.STANDARD)
        async def fetch_data():
            return await api_call()
    """

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, policy.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except policy.exceptions as e:
                    last_exception = e
                    if attempt >= policy.max_attempts:
                        logger.error(
                            f"Retry exhausted for {func.__name__} after {attempt} attempts: {e}"
                        )
                        raise RetryExhaustedError(
                            f"Failed after {policy.max_attempts} attempts"
                        ) from e

                    delay = calculate_delay(attempt, policy)
                    logger.warning(
                        f"Attempt {attempt}/{policy.max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)

            if last_exception:
                raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, policy.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except policy.exceptions as e:
                    last_exception = e
                    if attempt >= policy.max_attempts:
                        logger.error(
                            f"Retry exhausted for {func.__name__} after {attempt} attempts: {e}"
                        )
                        raise RetryExhaustedError(
                            f"Failed after {policy.max_attempts} attempts"
                        ) from e

                    delay = calculate_delay(attempt, policy)
                    logger.warning(
                        f"Attempt {attempt}/{policy.max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    import time

                    time.sleep(delay)

            if last_exception:
                raise last_exception

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
