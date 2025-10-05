"""
Metrics collection and tracking for monitoring.
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from functools import wraps
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """A single metric data point."""

    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Metric:
    """Aggregated metric with statistics."""

    name: str
    count: int = 0
    total: float = 0.0
    min: float = float("inf")
    max: float = float("-inf")
    avg: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    Collects and aggregates metrics for monitoring.

    Example:
        collector = MetricsCollector()
        collector.record("api_calls", 1, labels={"endpoint": "/api/v1/issues"})
        collector.record("response_time_ms", 150.5, labels={"endpoint": "/api/v1/issues"})

        metrics = collector.get_metrics()
    """

    def __init__(self):
        self._metrics: Dict[str, List[MetricPoint]] = defaultdict(list)
        self._counters: Dict[str, int] = defaultdict(int)

    def record(
        self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None
    ):
        """Record a metric value."""
        labels = labels or {}
        point = MetricPoint(name=name, value=value, labels=labels)
        self._metrics[name].append(point)

    def increment(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        labels = labels or {}
        key = f"{name}:{','.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
        self._counters[key] += value

    def get_metrics(self) -> Dict[str, Metric]:
        """Get aggregated metrics."""
        aggregated = {}

        for name, points in self._metrics.items():
            if not points:
                continue

            metric = Metric(name=name)
            metric.count = len(points)
            metric.total = sum(p.value for p in points)
            metric.min = min(p.value for p in points)
            metric.max = max(p.value for p in points)
            metric.avg = metric.total / metric.count if metric.count > 0 else 0.0

            aggregated[name] = metric

        return aggregated

    def get_counters(self) -> Dict[str, int]:
        """Get all counter values."""
        return dict(self._counters)

    def get_metric(self, name: str) -> Optional[Metric]:
        """Get a specific metric."""
        metrics = self.get_metrics()
        return metrics.get(name)

    def clear(self):
        """Clear all metrics."""
        self._metrics.clear()
        self._counters.clear()

    def get_prometheus_format(self) -> str:
        """
        Export metrics in Prometheus text format.

        Returns:
            String in Prometheus exposition format
        """
        lines = []

        # Export aggregated metrics
        metrics = self.get_metrics()
        for name, metric in metrics.items():
            # Add HELP and TYPE
            lines.append(f"# HELP {name} Metric for {name}")
            lines.append(f"# TYPE {name} gauge")

            # Add metric values
            lines.append(f"{name}_count {metric.count}")
            lines.append(f"{name}_total {metric.total}")
            lines.append(f"{name}_min {metric.min}")
            lines.append(f"{name}_max {metric.max}")
            lines.append(f"{name}_avg {metric.avg}")

        # Export counters
        for counter_key, value in self._counters.items():
            name = counter_key.split(":")[0]
            lines.append(f"# HELP {name} Counter for {name}")
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{counter_key.replace(':', '_')} {value}")

        return "\n".join(lines)


# Global metrics collector
_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector."""
    return _collector


def track_api_calls(endpoint: str):
    """
    Decorator to track API call metrics.

    Example:
        @track_api_calls('github_api')
        async def fetch_issues():
            return await github.get_issues()
    """

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            collector = get_metrics_collector()

            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                collector.increment(
                    f"{endpoint}_calls_total",
                    labels={"status": "success"},
                )
                collector.record(
                    f"{endpoint}_duration_ms",
                    duration_ms,
                    labels={"status": "success"},
                )

                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                collector.increment(
                    f"{endpoint}_calls_total",
                    labels={"status": "error"},
                )
                collector.record(
                    f"{endpoint}_duration_ms",
                    duration_ms,
                    labels={"status": "error"},
                )

                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            collector = get_metrics_collector()

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                collector.increment(
                    f"{endpoint}_calls_total",
                    labels={"status": "success"},
                )
                collector.record(
                    f"{endpoint}_duration_ms",
                    duration_ms,
                    labels={"status": "success"},
                )

                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                collector.increment(
                    f"{endpoint}_calls_total",
                    labels={"status": "error"},
                )
                collector.record(
                    f"{endpoint}_duration_ms",
                    duration_ms,
                    labels={"status": "error"},
                )

                raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
