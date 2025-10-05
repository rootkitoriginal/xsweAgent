"""
Metrics collection and monitoring utilities.
Provides decorators and utilities for tracking performance metrics.
"""

import functools
import logging
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Centralized metrics collection for performance monitoring.
    
    Example:
        metrics = MetricsCollector()
        metrics.record_execution_time("chart_generation", 125.5)
        metrics.increment_counter("charts_generated")
        stats = metrics.get_stats("chart_generation")
    """

    def __init__(self):
        self._execution_times: Dict[str, list] = {}
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}

    def record_execution_time(self, operation: str, duration_ms: float):
        """Record execution time for an operation."""
        if operation not in self._execution_times:
            self._execution_times[operation] = []
        self._execution_times[operation].append(duration_ms)
        logger.debug(f"Recorded execution time for {operation}: {duration_ms}ms")

    def increment_counter(self, counter: str, value: int = 1):
        """Increment a counter."""
        self._counters[counter] = self._counters.get(counter, 0) + value
        logger.debug(f"Incremented counter {counter} to {self._counters[counter]}")

    def set_gauge(self, gauge: str, value: float):
        """Set a gauge value."""
        self._gauges[gauge] = value
        logger.debug(f"Set gauge {gauge} to {value}")

    def get_stats(self, operation: str) -> Dict[str, Any]:
        """Get statistics for an operation."""
        times = self._execution_times.get(operation, [])
        if not times:
            return {"operation": operation, "count": 0}

        return {
            "operation": operation,
            "count": len(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "avg_ms": sum(times) / len(times),
            "total_ms": sum(times),
        }

    def get_counter(self, counter: str) -> int:
        """Get counter value."""
        return self._counters.get(counter, 0)

    def get_gauge(self, gauge: str) -> Optional[float]:
        """Get gauge value."""
        return self._gauges.get(gauge)

    def get_all_stats(self) -> Dict[str, Any]:
        """Get all metrics statistics."""
        return {
            "execution_times": {
                op: self.get_stats(op) for op in self._execution_times.keys()
            },
            "counters": self._counters.copy(),
            "gauges": self._gauges.copy(),
            "timestamp": datetime.now().isoformat(),
        }

    def reset(self):
        """Reset all metrics."""
        self._execution_times.clear()
        self._counters.clear()
        self._gauges.clear()
        logger.info("Metrics reset")


# Global metrics collector instance
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return _metrics_collector


def track_execution_time(operation_name: str):
    """
    Decorator to track execution time of a function.

    Args:
        operation_name: Name of the operation being tracked

    Example:
        @track_execution_time('chart_generation')
        def generate_chart():
            # ... chart generation code
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                _metrics_collector.record_execution_time(operation_name, duration_ms)
                logger.debug(f"{operation_name} took {duration_ms:.2f}ms")

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                _metrics_collector.record_execution_time(operation_name, duration_ms)
                logger.debug(f"{operation_name} took {duration_ms:.2f}ms")

        # Return appropriate wrapper
        import asyncio
        import inspect

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


@contextmanager
def measure_time(operation_name: str):
    """
    Context manager to measure execution time.

    Example:
        with measure_time('data_processing'):
            # ... processing code
            pass
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        _metrics_collector.record_execution_time(operation_name, duration_ms)
        logger.debug(f"{operation_name} took {duration_ms:.2f}ms")
