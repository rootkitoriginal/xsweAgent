"""
Circuit breaker pattern implementation for fault tolerance.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Callable, Optional

from .exceptions import CircuitBreakerError

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerPolicy:
    """Configuration for circuit breaker behavior."""

    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes to close from half-open
    timeout: float = 60.0  # Seconds before trying again (half-open)
    exceptions: tuple = (Exception,)


class CircuitBreakerPolicies:
    """Pre-configured circuit breaker policies."""

    # Standard policy for most services
    STANDARD = CircuitBreakerPolicy(
        failure_threshold=5,
        success_threshold=2,
        timeout=60.0,
    )

    # Aggressive policy for critical services
    AGGRESSIVE = CircuitBreakerPolicy(
        failure_threshold=3,
        success_threshold=3,
        timeout=120.0,
    )

    # Lenient policy for non-critical services
    LENIENT = CircuitBreakerPolicy(
        failure_threshold=10,
        success_threshold=2,
        timeout=30.0,
    )

    # MCP tools policy
    MCP_TOOLS = CircuitBreakerPolicy(
        failure_threshold=5,
        success_threshold=2,
        timeout=60.0,
    )

    # External API policy
    EXTERNAL_API = CircuitBreakerPolicy(
        failure_threshold=4,
        success_threshold=2,
        timeout=90.0,
    )


@dataclass
class CircuitBreakerState:
    """Runtime state for a circuit breaker."""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_state_change: float = field(default_factory=time.time)


class CircuitBreaker:
    """
    Circuit breaker implementation for protecting against cascading failures.

    Example:
        breaker = CircuitBreaker(CircuitBreakerPolicies.STANDARD)

        @breaker
        async def call_external_api():
            return await api.fetch()
    """

    def __init__(self, policy: CircuitBreakerPolicy):
        self.policy = policy
        self.state = CircuitBreakerState()
        self._lock = asyncio.Lock()

    def __call__(self, func: Callable):
        """Use circuit breaker as a decorator."""

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            await self._check_state()

            try:
                result = await func(*args, **kwargs)
                await self._on_success()
                return result
            except self.policy.exceptions as e:
                await self._on_failure()
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, use blocking check
            self._check_state_sync()

            try:
                result = func(*args, **kwargs)
                self._on_success_sync()
                return result
            except self.policy.exceptions as e:
                self._on_failure_sync()
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    async def _check_state(self):
        """Check if request should be allowed."""
        async with self._lock:
            if self.state.state == CircuitState.OPEN:
                # Check if timeout has elapsed
                if (
                    self.state.last_failure_time
                    and time.time() - self.state.last_failure_time >= self.policy.timeout
                ):
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                    self.state.state = CircuitState.HALF_OPEN
                    self.state.success_count = 0
                    self.state.last_state_change = time.time()
                else:
                    raise CircuitBreakerError("Circuit breaker is OPEN")

    def _check_state_sync(self):
        """Synchronous version of state check."""
        if self.state.state == CircuitState.OPEN:
            if (
                self.state.last_failure_time
                and time.time() - self.state.last_failure_time >= self.policy.timeout
            ):
                logger.info("Circuit breaker transitioning to HALF_OPEN")
                self.state.state = CircuitState.HALF_OPEN
                self.state.success_count = 0
                self.state.last_state_change = time.time()
            else:
                raise CircuitBreakerError("Circuit breaker is OPEN")

    async def _on_success(self):
        """Handle successful call."""
        async with self._lock:
            if self.state.state == CircuitState.HALF_OPEN:
                self.state.success_count += 1
                if self.state.success_count >= self.policy.success_threshold:
                    logger.info("Circuit breaker transitioning to CLOSED")
                    self.state.state = CircuitState.CLOSED
                    self.state.failure_count = 0
                    self.state.last_state_change = time.time()
            elif self.state.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.state.failure_count = 0

    def _on_success_sync(self):
        """Synchronous version of success handler."""
        if self.state.state == CircuitState.HALF_OPEN:
            self.state.success_count += 1
            if self.state.success_count >= self.policy.success_threshold:
                logger.info("Circuit breaker transitioning to CLOSED")
                self.state.state = CircuitState.CLOSED
                self.state.failure_count = 0
                self.state.last_state_change = time.time()
        elif self.state.state == CircuitState.CLOSED:
            self.state.failure_count = 0

    async def _on_failure(self):
        """Handle failed call."""
        async with self._lock:
            self.state.failure_count += 1
            self.state.last_failure_time = time.time()

            if self.state.state == CircuitState.HALF_OPEN:
                logger.warning("Circuit breaker transitioning to OPEN (failed during HALF_OPEN)")
                self.state.state = CircuitState.OPEN
                self.state.last_state_change = time.time()
            elif (
                self.state.state == CircuitState.CLOSED
                and self.state.failure_count >= self.policy.failure_threshold
            ):
                logger.warning(
                    f"Circuit breaker transitioning to OPEN "
                    f"(threshold {self.policy.failure_threshold} reached)"
                )
                self.state.state = CircuitState.OPEN
                self.state.last_state_change = time.time()

    def _on_failure_sync(self):
        """Synchronous version of failure handler."""
        self.state.failure_count += 1
        self.state.last_failure_time = time.time()

        if self.state.state == CircuitState.HALF_OPEN:
            logger.warning("Circuit breaker transitioning to OPEN (failed during HALF_OPEN)")
            self.state.state = CircuitState.OPEN
            self.state.last_state_change = time.time()
        elif (
            self.state.state == CircuitState.CLOSED
            and self.state.failure_count >= self.policy.failure_threshold
        ):
            logger.warning(
                f"Circuit breaker transitioning to OPEN "
                f"(threshold {self.policy.failure_threshold} reached)"
            )
            self.state.state = CircuitState.OPEN
            self.state.last_state_change = time.time()

    def get_state(self) -> dict:
        """Get current circuit breaker state."""
        return {
            "state": self.state.state.value,
            "failure_count": self.state.failure_count,
            "success_count": self.state.success_count,
            "last_state_change": self.state.last_state_change,
        }


def circuit_breaker(policy: CircuitBreakerPolicy):
    """
    Decorator factory for circuit breaker.

    Example:
        @circuit_breaker(CircuitBreakerPolicies.STANDARD)
        async def external_call():
            return await api.fetch()
    """
    breaker = CircuitBreaker(policy)
    return breaker
