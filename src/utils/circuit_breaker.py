"""
Circuit breaker pattern for protecting against cascading failures.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional

from .exceptions import CircuitBreakerOpenError

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failures detected, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""

    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes in half-open before closing
    timeout: float = 60.0  # Seconds before moving to half-open
    expected_exceptions: tuple = (Exception,)


class CircuitBreaker:
    """
    Circuit breaker for protecting services.

    Tracks failures and opens circuit to prevent cascading failures.
    """

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            await self._check_state()

            if self.state == CircuitState.OPEN:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN. Service unavailable. "
                    f"Will retry after {self.config.timeout}s"
                )

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except self.config.expected_exceptions as e:
            await self._on_failure()
            raise e

    async def _check_state(self):
        """Check and update circuit state based on conditions."""
        if self.state == CircuitState.OPEN:
            if (
                self.last_failure_time
                and time.time() - self.last_failure_time >= self.config.timeout
            ):
                logger.info("Circuit breaker moving to HALF_OPEN state")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0

    async def _on_success(self):
        """Handle successful execution."""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    logger.info("Circuit breaker moving to CLOSED state")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0

    async def _on_failure(self):
        """Handle failed execution."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if (
                self.state == CircuitState.CLOSED
                and self.failure_count >= self.config.failure_threshold
            ):
                logger.warning(
                    f"Circuit breaker opening after {self.failure_count} failures"
                )
                self.state = CircuitState.OPEN
            elif self.state == CircuitState.HALF_OPEN:
                logger.warning("Circuit breaker reopening after half-open failure")
                self.state = CircuitState.OPEN
                self.success_count = 0

    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self.state

    def reset(self):
        """Manually reset circuit breaker to closed state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info("Circuit breaker manually reset")


class CircuitBreakerPolicies:
    """Pre-configured circuit breaker policies."""

    # Gemini API - moderate protection
    GEMINI_API = CircuitBreakerConfig(
        failure_threshold=5, success_threshold=2, timeout=60.0
    )

    # GitHub API - more tolerant
    GITHUB_API = CircuitBreakerConfig(
        failure_threshold=10, success_threshold=3, timeout=30.0
    )

    # Critical services - aggressive protection
    CRITICAL = CircuitBreakerConfig(
        failure_threshold=3, success_threshold=2, timeout=120.0
    )


# Global circuit breakers registry
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str, config: Optional[CircuitBreakerConfig] = None
) -> CircuitBreaker:
    """Get or create a circuit breaker by name."""
    if name not in _circuit_breakers:
        if config is None:
            config = CircuitBreakerConfig()
        _circuit_breakers[name] = CircuitBreaker(config)
    return _circuit_breakers[name]


def circuit_breaker(
    config: CircuitBreakerConfig, name: Optional[str] = None
) -> Callable:
    """
    Decorator to add circuit breaker protection to async functions.

    Args:
        config: Circuit breaker configuration
        name: Optional name for the circuit breaker (defaults to function name)

    Example:
        @circuit_breaker(CircuitBreakerPolicies.GEMINI_API)
        async def call_gemini_api():
            # API call logic
            pass
    """

    def decorator(func: Callable) -> Callable:
        breaker_name = name or f"{func.__module__}.{func.__name__}"
        breaker = get_circuit_breaker(breaker_name, config)

        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            return await breaker.call(func, *args, **kwargs)

        return wrapper

    return decorator
