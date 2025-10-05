"""
Retry mechanism with configurable policies for xSwE Agent.
Uses tenacity library for robust retry handling.
"""

from dataclasses import dataclass
from typing import Callable, Optional, Type, Union

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_fixed,
)

from ..config.logging_config import get_logger
from .exceptions import GitHubAPIException, GeminiException, RateLimitException

logger = get_logger("retry")


@dataclass
class RetryPolicy:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    wait_strategy: str = "exponential"  # "exponential" or "fixed"
    wait_min: float = 1.0  # seconds
    wait_max: float = 60.0  # seconds
    multiplier: float = 2.0  # for exponential backoff
    exception_types: tuple = (Exception,)


class RetryPolicies:
    """Predefined retry policies for different use cases."""

    # GitHub API calls with exponential backoff
    GITHUB_API = RetryPolicy(
        max_attempts=5,
        wait_strategy="exponential",
        wait_min=2.0,
        wait_max=60.0,
        multiplier=2.0,
        exception_types=(GitHubAPIException,),
    )

    # Gemini API calls with shorter backoff
    GEMINI_API = RetryPolicy(
        max_attempts=3,
        wait_strategy="exponential",
        wait_min=1.0,
        wait_max=30.0,
        multiplier=2.0,
        exception_types=(GeminiException,),
    )

    # Analytics processing with fixed wait
    ANALYTICS = RetryPolicy(
        max_attempts=3,
        wait_strategy="fixed",
        wait_min=5.0,
        wait_max=5.0,
        multiplier=1.0,
        exception_types=(Exception,),
    )

    # Default policy for general operations
    DEFAULT = RetryPolicy(
        max_attempts=3,
        wait_strategy="exponential",
        wait_min=1.0,
        wait_max=10.0,
        multiplier=2.0,
        exception_types=(Exception,),
    )


def create_retry_decorator(policy: RetryPolicy):
    """Create a retry decorator from a retry policy.

    Args:
        policy: RetryPolicy configuration

    Returns:
        Configured tenacity retry decorator
    """
    # Choose wait strategy
    if policy.wait_strategy == "exponential":
        wait = wait_exponential(
            multiplier=policy.multiplier, min=policy.wait_min, max=policy.wait_max
        )
    else:  # fixed
        wait = wait_fixed(policy.wait_min)

    # Create the retry decorator
    return retry(
        stop=stop_after_attempt(policy.max_attempts),
        wait=wait,
        retry=retry_if_exception_type(policy.exception_types),
        before_sleep=lambda retry_state: logger.info(
            f"Retrying after error: {retry_state.outcome.exception()}, "
            f"attempt {retry_state.attempt_number}/{policy.max_attempts}"
        ),
        reraise=True,
    )


def retry_with_policy(
    policy: Union[RetryPolicy, str] = "DEFAULT",
) -> Callable:
    """Decorator to retry function calls with a specific policy.

    Args:
        policy: RetryPolicy instance or name of predefined policy

    Returns:
        Decorator function

    Example:
        @retry_with_policy(RetryPolicies.GITHUB_API)
        async def fetch_issues():
            # API call that may fail
            pass
    """
    # Handle string policy names
    if isinstance(policy, str):
        policy = getattr(RetryPolicies, policy, RetryPolicies.DEFAULT)

    return create_retry_decorator(policy)
