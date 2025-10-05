"""
Circuit Breaker pattern implementation for preventing cascading failures.

This module provides circuit breaker functionality to prevent cascading
failures when external services become unavailable. It monitors failure
rates and automatically trips to prevent further calls.
"""

import asyncio
import functools
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    Type,
    TypeVar,
    Union,
)

from .exceptions import CircuitBreakerException

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class CircuitState(Enum):
    """Circuit breaker states."""
    
    CLOSED = "closed"      # Normal operation - requests pass through
    OPEN = "open"          # Circuit is open - requests fail fast
    HALF_OPEN = "half_open"  # Testing - limited requests allowed


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    
    # Failure threshold
    failure_threshold: int = 5
    failure_rate_threshold: float = 0.5  # 50% failure rate
    minimum_requests: int = 10  # Minimum requests before rate calculation
    
    # Timing
    recovery_timeout: int = 60  # Seconds before moving to half-open
    request_timeout: float = 30.0  # Default request timeout
    
    # Half-open state behavior
    half_open_max_calls: int = 3  # Max calls allowed in half-open state
    
    # Exception handling
    expected_exceptions: tuple = (Exception,)
    ignored_exceptions: tuple = ()  # Exceptions that don't count as failures
    
    # Monitoring
    sliding_window_size: int = 100  # Number of recent calls to track
    
    def __post_init__(self):
        """Validate configuration."""
        if self.failure_threshold <= 0:
            raise ValueError("failure_threshold must be > 0")
        if not 0 < self.failure_rate_threshold <= 1:
            raise ValueError("failure_rate_threshold must be between 0 and 1")
        if self.minimum_requests <= 0:
            raise ValueError("minimum_requests must be > 0")
        if self.recovery_timeout <= 0:
            raise ValueError("recovery_timeout must be > 0")


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker monitoring."""
    
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    total_requests: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state_changed_time: float = field(default_factory=time.time)
    half_open_calls: int = 0
    
    @property
    def failure_rate(self) -> float:
        """Calculate current failure rate."""
        if self.total_requests == 0:
            return 0.0
        return self.failure_count / self.total_requests
    
    @property
    def success_rate(self) -> float:
        """Calculate current success rate."""
        return 1.0 - self.failure_rate
    
    def reset_counts(self):
        """Reset failure/success counts (used when window slides)."""
        self.failure_count = 0
        self.success_count = 0
        self.total_requests = 0


class CircuitBreaker:
    """
    Circuit breaker implementation with sliding window failure tracking.
    
    The circuit breaker monitors the failure rate of operations and can be in
    one of three states:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Circuit is tripped, requests fail fast
    - HALF_OPEN: Testing recovery, limited requests allowed
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.stats = CircuitBreakerStats()
        self._lock = Lock()
        self._recent_calls = []  # Sliding window of recent call results
        
    def _should_trip(self) -> bool:
        """Determine if circuit should trip to OPEN state."""
        with self._lock:
            # Need minimum number of requests
            if self.stats.total_requests < self.config.minimum_requests:
                return False
            
            # Check if failure count exceeds threshold
            if self.stats.failure_count >= self.config.failure_threshold:
                return True
            
            # Check if failure rate exceeds threshold
            if self.stats.failure_rate >= self.config.failure_rate_threshold:
                return True
                
            return False
    
    def _should_attempt_reset(self) -> bool:
        """Determine if circuit should move from OPEN to HALF_OPEN."""
        if self.stats.state != CircuitState.OPEN:
            return False
            
        # Check if recovery timeout has elapsed
        time_since_trip = time.time() - self.stats.state_changed_time
        return time_since_trip >= self.config.recovery_timeout
    
    def _record_success(self):
        """Record a successful operation."""
        with self._lock:
            self.stats.success_count += 1
            self.stats.total_requests += 1
            self.stats.last_success_time = time.time()
            
            # Add to sliding window
            self._recent_calls.append(True)
            if len(self._recent_calls) > self.config.sliding_window_size:
                # Remove oldest call and adjust counts if needed
                oldest = self._recent_calls.pop(0)
                if not oldest:  # Was a failure
                    self.stats.failure_count = max(0, self.stats.failure_count - 1)
                else:  # Was a success
                    self.stats.success_count = max(0, self.stats.success_count - 1)
                self.stats.total_requests = max(0, self.stats.total_requests - 1)
    
    def _record_failure(self, exception: Exception):
        """Record a failed operation."""
        # Don't record ignored exceptions as failures
        if isinstance(exception, self.config.ignored_exceptions):
            return
            
        with self._lock:
            self.stats.failure_count += 1
            self.stats.total_requests += 1
            self.stats.last_failure_time = time.time()
            
            # Add to sliding window
            self._recent_calls.append(False)
            if len(self._recent_calls) > self.config.sliding_window_size:
                # Remove oldest call and adjust counts if needed
                oldest = self._recent_calls.pop(0)
                if not oldest:  # Was a failure
                    self.stats.failure_count = max(0, self.stats.failure_count - 1)
                else:  # Was a success
                    self.stats.success_count = max(0, self.stats.success_count - 1)
                self.stats.total_requests = max(0, self.stats.total_requests - 1)
    
    def _change_state(self, new_state: CircuitState):
        """Change circuit breaker state."""
        with self._lock:
            old_state = self.stats.state
            self.stats.state = new_state
            self.stats.state_changed_time = time.time()
            
            if new_state == CircuitState.HALF_OPEN:
                self.stats.half_open_calls = 0
            
            logger.info(
                f"Circuit breaker '{self.name}' state changed: {old_state.value} -> {new_state.value}",
                extra={
                    "circuit_name": self.name,
                    "old_state": old_state.value,
                    "new_state": new_state.value,
                    "failure_count": self.stats.failure_count,
                    "failure_rate": self.stats.failure_rate,
                }
            )
    
    def can_execute(self) -> bool:
        """Check if a request can be executed."""
        with self._lock:
            if self.stats.state == CircuitState.CLOSED:
                return True
            
            if self.stats.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._change_state(CircuitState.HALF_OPEN)
                    return True
                return False
            
            if self.stats.state == CircuitState.HALF_OPEN:
                return self.stats.half_open_calls < self.config.half_open_max_calls
        
        return False
    
    def execute_request(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a request through the circuit breaker."""
        if not self.can_execute():
            raise CircuitBreakerException(
                f"Circuit breaker '{self.name}' is OPEN",
                circuit_name=self.name,
                state=self.stats.state.value,
                failure_count=self.stats.failure_count,
            )
        
        # Track half-open calls
        if self.stats.state == CircuitState.HALF_OPEN:
            with self._lock:
                self.stats.half_open_calls += 1
        
        try:
            result = func(*args, **kwargs)
            self._record_success()
            
            # Handle state transitions on success
            if self.stats.state == CircuitState.HALF_OPEN:
                # If we've had enough successful calls in half-open, close the circuit
                if self.stats.half_open_calls >= self.config.half_open_max_calls:
                    self._change_state(CircuitState.CLOSED)
            
            return result
            
        except Exception as e:
            self._record_failure(e)
            
            # Handle state transitions on failure
            if self.stats.state == CircuitState.HALF_OPEN:
                # Any failure in half-open immediately opens the circuit
                self._change_state(CircuitState.OPEN)
            elif self.stats.state == CircuitState.CLOSED:
                # Check if we should trip the circuit
                if self._should_trip():
                    self._change_state(CircuitState.OPEN)
            
            raise
    
    async def execute_async_request(self, func: Callable, *args, **kwargs) -> Any:
        """Execute an async request through the circuit breaker."""
        if not self.can_execute():
            raise CircuitBreakerException(
                f"Circuit breaker '{self.name}' is OPEN",
                circuit_name=self.name,
                state=self.stats.state.value,
                failure_count=self.stats.failure_count,
            )
        
        # Track half-open calls
        if self.stats.state == CircuitState.HALF_OPEN:
            with self._lock:
                self.stats.half_open_calls += 1
        
        try:
            result = await func(*args, **kwargs)
            self._record_success()
            
            # Handle state transitions on success
            if self.stats.state == CircuitState.HALF_OPEN:
                if self.stats.half_open_calls >= self.config.half_open_max_calls:
                    self._change_state(CircuitState.CLOSED)
            
            return result
            
        except Exception as e:
            self._record_failure(e)
            
            # Handle state transitions on failure
            if self.stats.state == CircuitState.HALF_OPEN:
                self._change_state(CircuitState.OPEN)
            elif self.stats.state == CircuitState.CLOSED:
                if self._should_trip():
                    self._change_state(CircuitState.OPEN)
            
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current circuit breaker statistics."""
        with self._lock:
            return {
                "name": self.name,
                "state": self.stats.state.value,
                "failure_count": self.stats.failure_count,
                "success_count": self.stats.success_count,
                "total_requests": self.stats.total_requests,
                "failure_rate": self.stats.failure_rate,
                "success_rate": self.stats.success_rate,
                "last_failure_time": self.stats.last_failure_time,
                "last_success_time": self.stats.last_success_time,
                "state_changed_time": self.stats.state_changed_time,
                "half_open_calls": self.stats.half_open_calls,
            }
    
    def reset(self):
        """Reset circuit breaker to initial state."""
        with self._lock:
            self.stats = CircuitBreakerStats()
            self._recent_calls = []
            logger.info(f"Circuit breaker '{self.name}' has been reset")


# Global registry of circuit breakers
_circuit_breakers: Dict[str, CircuitBreaker] = {}
_registry_lock = Lock()


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get or create a circuit breaker by name."""
    with _registry_lock:
        if name not in _circuit_breakers:
            if config is None:
                config = CircuitBreakerConfig()
            _circuit_breakers[name] = CircuitBreaker(name, config)
        return _circuit_breakers[name]


def circuit_breaker(
    name: Optional[str] = None,
    config: Optional[CircuitBreakerConfig] = None,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    **kwargs
) -> Callable[[F], F]:
    """
    Decorator for adding circuit breaker protection to functions.
    
    Args:
        name: Circuit breaker name (defaults to function name)
        config: Circuit breaker configuration
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds before attempting recovery
        **kwargs: Additional configuration parameters
        
    Returns:
        Decorated function with circuit breaker protection
        
    Examples:
        @circuit_breaker(name="github_api", failure_threshold=3)
        async def github_api_call():
            pass
            
        @circuit_breaker(config=CircuitBreakerConfig(failure_threshold=10))
        def database_operation():
            pass
    """
    
    def decorator(func: F) -> F:
        circuit_name = name or func.__name__
        
        # Build configuration
        if config:
            cb_config = config
        else:
            cb_config = CircuitBreakerConfig(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                **kwargs
            )
        
        # Get or create circuit breaker
        cb = get_circuit_breaker(circuit_name, cb_config)
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await cb.execute_async_request(func, *args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                return cb.execute_request(func, *args, **kwargs)
            return sync_wrapper
    
    return decorator


# Predefined circuit breaker configurations
class CircuitBreakerPolicies:
    """Predefined circuit breaker policies for common use cases."""
    
    @staticmethod
    def github_api() -> CircuitBreakerConfig:
        """Circuit breaker policy for GitHub API."""
        return CircuitBreakerConfig(
            failure_threshold=5,
            failure_rate_threshold=0.6,
            minimum_requests=10,
            recovery_timeout=120,  # 2 minutes
            request_timeout=30.0,
            half_open_max_calls=3,
        )
    
    @staticmethod
    def gemini_api() -> CircuitBreakerConfig:
        """Circuit breaker policy for Gemini AI API."""
        return CircuitBreakerConfig(
            failure_threshold=3,
            failure_rate_threshold=0.5,
            minimum_requests=5,
            recovery_timeout=60,  # 1 minute
            request_timeout=60.0,  # AI calls can be slower
            half_open_max_calls=2,
        )
    
    @staticmethod
    def database() -> CircuitBreakerConfig:
        """Circuit breaker policy for database operations."""
        return CircuitBreakerConfig(
            failure_threshold=10,
            failure_rate_threshold=0.7,
            minimum_requests=20,
            recovery_timeout=30,  # 30 seconds
            request_timeout=10.0,
            half_open_max_calls=5,
        )
    
    @staticmethod
    def external_service() -> CircuitBreakerConfig:
        """Generic circuit breaker policy for external services."""
        return CircuitBreakerConfig(
            failure_threshold=5,
            failure_rate_threshold=0.5,
            minimum_requests=10,
            recovery_timeout=60,
            request_timeout=30.0,
            half_open_max_calls=3,
        )


def get_all_circuit_breakers() -> Dict[str, Dict[str, Any]]:
    """Get statistics for all registered circuit breakers."""
    with _registry_lock:
        return {name: cb.get_stats() for name, cb in _circuit_breakers.items()}


def reset_all_circuit_breakers():
    """Reset all registered circuit breakers."""
    with _registry_lock:
        for cb in _circuit_breakers.values():
            cb.reset()
        logger.info("All circuit breakers have been reset")