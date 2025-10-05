"""
Metrics collection and tracking for xSwE Agent.
Provides simple in-memory metrics for monitoring.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from ..config.logging_config import get_logger

logger = get_logger("metrics")


@dataclass
class MetricPoint:
    """Single metric measurement."""

    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Collects and stores metrics for monitoring."""

    def __init__(self):
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._timers: Dict[str, List[MetricPoint]] = defaultdict(list)

    def increment_counter(self, name: str, value: float = 1.0, **labels):
        """Increment a counter metric.

        Args:
            name: Counter name
            value: Amount to increment (default 1.0)
            **labels: Additional labels for the metric
        """
        key = self._make_key(name, labels)
        self._counters[key] += value
        logger.debug(f"Counter {name} incremented", value=value, labels=labels)

    def set_gauge(self, name: str, value: float, **labels):
        """Set a gauge metric to a specific value.

        Args:
            name: Gauge name
            value: Value to set
            **labels: Additional labels for the metric
        """
        key = self._make_key(name, labels)
        self._gauges[key] = value
        logger.debug(f"Gauge {name} set", value=value, labels=labels)

    def observe_histogram(self, name: str, value: float, **labels):
        """Add an observation to a histogram.

        Args:
            name: Histogram name
            value: Value to observe
            **labels: Additional labels for the metric
        """
        key = self._make_key(name, labels)
        self._histograms[key].append(value)
        logger.debug(f"Histogram {name} observed", value=value, labels=labels)

    def record_timing(self, name: str, duration_ms: float, **labels):
        """Record a timing measurement.

        Args:
            name: Timer name
            duration_ms: Duration in milliseconds
            **labels: Additional labels for the metric
        """
        key = self._make_key(name, labels)
        self._timers[key].append(
            MetricPoint(timestamp=datetime.now(), value=duration_ms, labels=labels)
        )
        logger.debug(f"Timing {name} recorded", duration_ms=duration_ms, labels=labels)

    def get_counter(self, name: str, **labels) -> float:
        """Get current counter value."""
        key = self._make_key(name, labels)
        return self._counters.get(key, 0.0)

    def get_gauge(self, name: str, **labels) -> Optional[float]:
        """Get current gauge value."""
        key = self._make_key(name, labels)
        return self._gauges.get(key)

    def get_histogram_stats(self, name: str, **labels) -> Dict[str, float]:
        """Get statistics for a histogram.

        Returns:
            Dict with count, sum, min, max, avg
        """
        key = self._make_key(name, labels)
        values = self._histograms.get(key, [])

        if not values:
            return {"count": 0, "sum": 0, "min": 0, "max": 0, "avg": 0}

        return {
            "count": len(values),
            "sum": sum(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
        }

    def get_timer_stats(self, name: str, **labels) -> Dict[str, float]:
        """Get statistics for a timer.

        Returns:
            Dict with count, total_ms, min_ms, max_ms, avg_ms
        """
        key = self._make_key(name, labels)
        points = self._timers.get(key, [])

        if not points:
            return {"count": 0, "total_ms": 0, "min_ms": 0, "max_ms": 0, "avg_ms": 0}

        values = [p.value for p in points]
        return {
            "count": len(values),
            "total_ms": sum(values),
            "min_ms": min(values),
            "max_ms": max(values),
            "avg_ms": sum(values) / len(values),
        }

    def get_all_metrics(self) -> Dict[str, any]:
        """Get snapshot of all metrics."""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                name: self.get_histogram_stats(name.split(":")[0])
                for name in self._histograms.keys()
            },
            "timers": {
                name: self.get_timer_stats(name.split(":")[0])
                for name in self._timers.keys()
            },
            "timestamp": datetime.now().isoformat(),
        }

    def reset(self):
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._timers.clear()
        logger.info("Metrics reset")

    @staticmethod
    def _make_key(name: str, labels: Dict[str, str]) -> str:
        """Create a unique key from name and labels."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}:{label_str}"


# Global metrics collector instance
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return _metrics_collector


def track_api_calls(api_name: str):
    """Decorator to track API call metrics.

    Args:
        api_name: Name of the API being tracked

    Example:
        @track_api_calls('github')
        async def fetch_issues():
            # API call
            pass
    """

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                collector.increment_counter(
                    f"{api_name}_calls_total", status="success"
                )
                return result
            except Exception as e:
                collector.increment_counter(f"{api_name}_calls_total", status="error")
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                collector.record_timing(f"{api_name}_call_duration", duration_ms)

        def sync_wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                collector.increment_counter(
                    f"{api_name}_calls_total", status="success"
                )
                return result
            except Exception as e:
                collector.increment_counter(f"{api_name}_calls_total", status="error")
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                collector.record_timing(f"{api_name}_call_duration", duration_ms)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            async_wrapper.__name__ = func.__name__
            async_wrapper.__doc__ = func.__doc__
            return async_wrapper
        else:
            sync_wrapper.__name__ = func.__name__
            sync_wrapper.__doc__ = func.__doc__
            return sync_wrapper

    return decorator
