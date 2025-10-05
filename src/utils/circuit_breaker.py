"""
Circuit breaker pattern implementation for external API protection.
Prevents cascading failures by opening the circuit when errors exceed thresholds.
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

from ..config.logging_config import get_logger
from .exceptions import CircuitBreakerException

logger = get_logger("circuit_breaker")


class CircuitState(str, Enum):
    """States of a circuit breaker."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit broken, rejecting calls
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerPolicy:
    """Configuration for circuit breaker behavior."""

    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes to close from half-open
    timeout: float = 60.0  # Seconds before attempting recovery
    expected_exceptions: tuple = (Exception,)


class CircuitBreakerPolicies:
    """Predefined circuit breaker policies."""

    GITHUB_API = CircuitBreakerPolicy(
        failure_threshold=5,
        success_threshold=2,
        timeout=60.0,
    )

    GEMINI_API = CircuitBreakerPolicy(
        failure_threshold=3,
        success_threshold=2,
        timeout=30.0,
    )

    DEFAULT = CircuitBreakerPolicy(
        failure_threshold=5,
        success_threshold=2,
        timeout=60.0,
    )


@dataclass
class CircuitBreaker:
    """Circuit breaker implementation.

    Tracks failures and opens the circuit when threshold is exceeded.
    """

    name: str
    policy: CircuitBreakerPolicy
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection.

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerException: If circuit is open
        """
        async with self._lock:
            # Check if we should attempt recovery
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    logger.info(f"Circuit breaker {self.name}: Attempting recovery")
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise CircuitBreakerException(
                        f"Circuit breaker {self.name} is OPEN. "
                        f"Will retry after {self.policy.timeout}s"
                    )

        # Execute the function
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            await self._on_success()
            return result

        except self.policy.expected_exceptions as e:
            await self._on_failure(e)
            raise

    async def _on_success(self):
        """Handle successful execution."""
        async with self._lock:
            self.failure_count = 0

            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.policy.success_threshold:
                    logger.info(f"Circuit breaker {self.name}: Closing (recovered)")
                    self.state = CircuitState.CLOSED
                    self.success_count = 0

    async def _on_failure(self, exception: Exception):
        """Handle failed execution."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            logger.warning(
                f"Circuit breaker {self.name}: Failure {self.failure_count}/{self.policy.failure_threshold}",
                error=str(exception),
            )

            if self.state == CircuitState.HALF_OPEN:
                # Failed during recovery attempt
                logger.warning(f"Circuit breaker {self.name}: Recovery failed, reopening")
                self.state = CircuitState.OPEN
                self.success_count = 0

            elif self.failure_count >= self.policy.failure_threshold:
                logger.error(f"Circuit breaker {self.name}: Opening due to failures")
                self.state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.last_failure_time is None:
            return True

        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.policy.timeout

    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self.state

    def reset(self):
        """Manually reset the circuit breaker."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info(f"Circuit breaker {self.name}: Manually reset")


# Global circuit breaker registry
_circuit_breakers = {}


def get_circuit_breaker(
    name: str, policy: Optional[CircuitBreakerPolicy] = None
) -> CircuitBreaker:
    """Get or create a circuit breaker.

    Args:
        name: Unique name for the circuit breaker
        policy: Optional policy, uses DEFAULT if not provided

    Returns:
        CircuitBreaker instance
    """
    if name not in _circuit_breakers:
        policy = policy or CircuitBreakerPolicies.DEFAULT
        _circuit_breakers[name] = CircuitBreaker(name=name, policy=policy)
    return _circuit_breakers[name]


def circuit_breaker(
    name: Optional[str] = None,
    policy: Optional[CircuitBreakerPolicy] = None,
):
    """Decorator to protect functions with circuit breaker.

    Args:
        name: Optional name for circuit breaker, uses function name if not provided
        policy: Optional policy, uses DEFAULT if not provided

    Example:
        @circuit_breaker(name="github_api", policy=CircuitBreakerPolicies.GITHUB_API)
        async def fetch_issues():
            # API call
            pass
    """

    def decorator(func):
        breaker_name = name or func.__name__
        breaker = get_circuit_breaker(breaker_name, policy)

        async def async_wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)

        def sync_wrapper(*args, **kwargs):
            # For sync functions, we need to run in event loop
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(breaker.call(func, *args, **kwargs))

        if asyncio.iscoroutinefunction(func):
            async_wrapper.__name__ = func.__name__
            async_wrapper.__doc__ = func.__doc__
            return async_wrapper
        else:
            sync_wrapper.__name__ = func.__name__
            sync_wrapper.__doc__ = func.__doc__
            return sync_wrapper

    return decorator
