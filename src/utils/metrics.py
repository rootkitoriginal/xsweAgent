"""
Metrics collection system with Prometheus compatibility.

This module provides comprehensive metrics collection for monitoring
system performance, API calls, and business metrics.
"""

import time
import threading
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics supported."""
    
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricLabels:
    """Labels for metric categorization."""
    
    labels: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        # Ensure all label values are strings
        self.labels = {k: str(v) for k, v in self.labels.items()}
    
    def __hash__(self):
        return hash(tuple(sorted(self.labels.items())))
    
    def __eq__(self, other):
        return isinstance(other, MetricLabels) and self.labels == other.labels
    
    def to_prometheus_format(self) -> str:
        """Format labels for Prometheus exposition format."""
        if not self.labels:
            return ""
        
        formatted_labels = []
        for key, value in sorted(self.labels.items()):
            # Escape quotes in values
            escaped_value = value.replace('"', '\\"')
            formatted_labels.append(f'{key}="{escaped_value}"')
        
        return "{" + ",".join(formatted_labels) + "}"


class BaseMetric(ABC):
    """Base class for all metrics."""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        labels: Optional[Dict[str, str]] = None,
    ):
        self.name = name
        self.description = description
        self.default_labels = MetricLabels(labels or {})
        self.created_at = datetime.utcnow()
        self._lock = threading.Lock()
    
    @abstractmethod
    def get_value(self, labels: Optional[MetricLabels] = None) -> Union[float, Dict[str, float]]:
        """Get the current metric value."""
        pass
    
    @abstractmethod
    def to_prometheus_format(self) -> List[str]:
        """Format metric for Prometheus exposition format."""
        pass
    
    def _get_full_labels(self, labels: Optional[MetricLabels] = None) -> MetricLabels:
        """Combine default labels with provided labels."""
        if labels is None:
            return self.default_labels
        
        combined = self.default_labels.labels.copy()
        combined.update(labels.labels)
        return MetricLabels(combined)


class Counter(BaseMetric):
    """Counter metric that only increases."""
    
    def __init__(self, name: str, description: str = "", labels: Optional[Dict[str, str]] = None):
        super().__init__(name, description, labels)
        self._values: Dict[MetricLabels, float] = defaultdict(float)
    
    def inc(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment the counter."""
        if value < 0:
            raise ValueError("Counter can only be incremented by non-negative values")
        
        metric_labels = self._get_full_labels(MetricLabels(labels) if labels else None)
        
        with self._lock:
            self._values[metric_labels] += value
    
    def get_value(self, labels: Optional[MetricLabels] = None) -> float:
        """Get counter value for specific labels."""
        metric_labels = self._get_full_labels(labels)
        
        with self._lock:
            return self._values.get(metric_labels, 0.0)
    
    def get_all_values(self) -> Dict[MetricLabels, float]:
        """Get all counter values."""
        with self._lock:
            return dict(self._values)
    
    def to_prometheus_format(self) -> List[str]:
        """Format counter for Prometheus."""
        lines = []
        
        if self.description:
            lines.append(f"# HELP {self.name} {self.description}")
        lines.append(f"# TYPE {self.name} counter")
        
        with self._lock:
            for labels, value in self._values.items():
                label_str = labels.to_prometheus_format()
                lines.append(f"{self.name}{label_str} {value}")
        
        return lines


class Gauge(BaseMetric):
    """Gauge metric that can go up and down."""
    
    def __init__(self, name: str, description: str = "", labels: Optional[Dict[str, str]] = None):
        super().__init__(name, description, labels)
        self._values: Dict[MetricLabels, float] = defaultdict(float)
    
    def set(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Set the gauge value."""
        metric_labels = self._get_full_labels(MetricLabels(labels) if labels else None)
        
        with self._lock:
            self._values[metric_labels] = value
    
    def inc(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment the gauge value."""
        metric_labels = self._get_full_labels(MetricLabels(labels) if labels else None)
        
        with self._lock:
            self._values[metric_labels] += value
    
    def dec(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Decrement the gauge value."""
        self.inc(-value, labels)
    
    def get_value(self, labels: Optional[MetricLabels] = None) -> float:
        """Get gauge value for specific labels."""
        metric_labels = self._get_full_labels(labels)
        
        with self._lock:
            return self._values.get(metric_labels, 0.0)
    
    def get_all_values(self) -> Dict[MetricLabels, float]:
        """Get all gauge values."""
        with self._lock:
            return dict(self._values)
    
    def to_prometheus_format(self) -> List[str]:
        """Format gauge for Prometheus."""
        lines = []
        
        if self.description:
            lines.append(f"# HELP {self.name} {self.description}")
        lines.append(f"# TYPE {self.name} gauge")
        
        with self._lock:
            for labels, value in self._values.items():
                label_str = labels.to_prometheus_format()
                lines.append(f"{self.name}{label_str} {value}")
        
        return lines


@dataclass
class HistogramBucket:
    """Histogram bucket for tracking value distribution."""
    
    le: float  # Upper bound (less than or equal)
    count: int = 0


class Histogram(BaseMetric):
    """Histogram metric for tracking value distributions."""
    
    DEFAULT_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float("inf")]
    
    def __init__(
        self,
        name: str,
        description: str = "",
        buckets: Optional[List[float]] = None,
        labels: Optional[Dict[str, str]] = None,
    ):
        super().__init__(name, description, labels)
        self.buckets = sorted(buckets or self.DEFAULT_BUCKETS)
        if self.buckets[-1] != float("inf"):
            self.buckets.append(float("inf"))
        
        self._buckets: Dict[MetricLabels, List[int]] = defaultdict(lambda: [0] * len(self.buckets))
        self._counts: Dict[MetricLabels, int] = defaultdict(int)
        self._sums: Dict[MetricLabels, float] = defaultdict(float)
    
    def observe(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Observe a value and update histogram buckets."""
        metric_labels = self._get_full_labels(MetricLabels(labels) if labels else None)
        
        with self._lock:
            # Update buckets
            for i, bucket_le in enumerate(self.buckets):
                if value <= bucket_le:
                    self._buckets[metric_labels][i] += 1
            
            # Update count and sum
            self._counts[metric_labels] += 1
            self._sums[metric_labels] += value
    
    def get_value(self, labels: Optional[MetricLabels] = None) -> Dict[str, Union[float, List[int]]]:
        """Get histogram statistics."""
        metric_labels = self._get_full_labels(labels)
        
        with self._lock:
            return {
                "count": self._counts.get(metric_labels, 0),
                "sum": self._sums.get(metric_labels, 0.0),
                "buckets": self._buckets.get(metric_labels, [0] * len(self.buckets)).copy(),
            }
    
    def to_prometheus_format(self) -> List[str]:
        """Format histogram for Prometheus."""
        lines = []
        
        if self.description:
            lines.append(f"# HELP {self.name} {self.description}")
        lines.append(f"# TYPE {self.name} histogram")
        
        with self._lock:
            for labels in set(self._counts.keys()) | set(self._buckets.keys()) | set(self._sums.keys()):
                label_str = labels.to_prometheus_format()
                
                # Bucket counts
                for i, bucket_le in enumerate(self.buckets):
                    bucket_count = self._buckets[labels][i] if i < len(self._buckets[labels]) else 0
                    le_label = f'le="{bucket_le}"'
                    
                    if label_str:
                        bucket_labels = f'{label_str[:-1]},{le_label}}}'
                    else:
                        bucket_labels = f'{{{le_label}}}'
                    
                    lines.append(f"{self.name}_bucket{bucket_labels} {bucket_count}")
                
                # Count and sum
                lines.append(f"{self.name}_count{label_str} {self._counts[labels]}")
                lines.append(f"{self.name}_sum{label_str} {self._sums[labels]}")
        
        return lines


class MetricsCollector:
    """Central metrics collector and registry."""
    
    def __init__(self):
        self._metrics: Dict[str, BaseMetric] = {}
        self._lock = threading.Lock()
        
        # Default system metrics
        self._setup_default_metrics()
    
    def _setup_default_metrics(self):
        """Set up default system metrics."""
        # API call metrics
        self.api_requests_total = self.counter(
            "api_requests_total",
            "Total number of API requests",
        )
        
        self.api_request_duration_seconds = self.histogram(
            "api_request_duration_seconds",
            "API request duration in seconds",
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, float("inf")],
        )
        
        self.api_errors_total = self.counter(
            "api_errors_total",
            "Total number of API errors",
        )
        
        # Health check metrics
        self.health_check_duration_seconds = self.histogram(
            "health_check_duration_seconds",
            "Health check duration in seconds",
        )
        
        self.health_check_status = self.gauge(
            "health_check_status",
            "Health check status (1=healthy, 0.5=degraded, 0=unhealthy)",
        )
        
        # Circuit breaker metrics
        self.circuit_breaker_state = self.gauge(
            "circuit_breaker_state",
            "Circuit breaker state (0=closed, 1=open, 0.5=half-open)",
        )
        
        self.circuit_breaker_failures_total = self.counter(
            "circuit_breaker_failures_total",
            "Total circuit breaker failures",
        )
        
        # Retry metrics
        self.retry_attempts_total = self.counter(
            "retry_attempts_total",
            "Total retry attempts",
        )
        
        # System metrics
        self.memory_usage_bytes = self.gauge(
            "memory_usage_bytes",
            "Current memory usage in bytes",
        )
        
        self.active_connections = self.gauge(
            "active_connections",
            "Number of active connections",
        )
    
    def counter(
        self,
        name: str,
        description: str = "",
        labels: Optional[Dict[str, str]] = None,
    ) -> Counter:
        """Create or get a counter metric."""
        return self._get_or_create_metric(name, Counter, description, labels)
    
    def gauge(
        self,
        name: str,
        description: str = "",
        labels: Optional[Dict[str, str]] = None,
    ) -> Gauge:
        """Create or get a gauge metric."""
        return self._get_or_create_metric(name, Gauge, description, labels)
    
    def histogram(
        self,
        name: str,
        description: str = "",
        buckets: Optional[List[float]] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> Histogram:
        """Create or get a histogram metric."""
        with self._lock:
            if name in self._metrics:
                metric = self._metrics[name]
                if not isinstance(metric, Histogram):
                    raise ValueError(f"Metric {name} already exists with different type")
                return metric
            
            metric = Histogram(name, description, buckets, labels)
            self._metrics[name] = metric
            return metric
    
    def _get_or_create_metric(
        self,
        name: str,
        metric_class: type,
        description: str,
        labels: Optional[Dict[str, str]],
    ) -> BaseMetric:
        """Get existing metric or create new one."""
        with self._lock:
            if name in self._metrics:
                metric = self._metrics[name]
                if not isinstance(metric, metric_class):
                    raise ValueError(f"Metric {name} already exists with different type")
                return metric
            
            metric = metric_class(name, description, labels)
            self._metrics[name] = metric
            return metric
    
    def get_metric(self, name: str) -> Optional[BaseMetric]:
        """Get a metric by name."""
        with self._lock:
            return self._metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, BaseMetric]:
        """Get all registered metrics."""
        with self._lock:
            return dict(self._metrics)
    
    def collect(self) -> str:
        """Collect all metrics in Prometheus exposition format."""
        lines = []
        
        with self._lock:
            for metric in self._metrics.values():
                lines.extend(metric.to_prometheus_format())
                lines.append("")  # Empty line between metrics
        
        return "\n".join(lines)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collector statistics."""
        with self._lock:
            return {
                "registered_metrics": len(self._metrics),
                "metrics_by_type": {
                    "counter": sum(1 for m in self._metrics.values() if isinstance(m, Counter)),
                    "gauge": sum(1 for m in self._metrics.values() if isinstance(m, Gauge)),
                    "histogram": sum(1 for m in self._metrics.values() if isinstance(m, Histogram)),
                },
                "metric_names": list(self._metrics.keys()),
            }


# Global metrics collector instance
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return _metrics_collector


# Decorators for automatic metrics collection
def track_api_calls(api_name: str, endpoint: Optional[str] = None):
    """Decorator to automatically track API call metrics."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            labels = {"api": api_name}
            if endpoint:
                labels["endpoint"] = endpoint
            
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # Record success
                collector.api_requests_total.inc(labels={**labels, "status": "success"})
                return result
                
            except Exception as e:
                # Record error
                collector.api_requests_total.inc(labels={**labels, "status": "error"})
                collector.api_errors_total.inc(labels={**labels, "error_type": type(e).__name__})
                raise
                
            finally:
                # Record duration
                duration = time.time() - start_time
                collector.api_request_duration_seconds.observe(duration, labels)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            labels = {"api": api_name}
            if endpoint:
                labels["endpoint"] = endpoint
            
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # Record success
                collector.api_requests_total.inc(labels={**labels, "status": "success"})
                return result
                
            except Exception as e:
                # Record error
                collector.api_requests_total.inc(labels={**labels, "status": "error"})
                collector.api_errors_total.inc(labels={**labels, "error_type": type(e).__name__})
                raise
                
            finally:
                # Record duration
                duration = time.time() - start_time
                collector.api_request_duration_seconds.observe(duration, labels)
        
        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def track_execution_time(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """Decorator to track function execution time."""
    
    def decorator(func: Callable) -> Callable:
        collector = get_metrics_collector()
        histogram = collector.histogram(
            metric_name,
            f"Execution time for {func.__name__} in seconds",
        )
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.time() - start_time
                histogram.observe(duration, labels)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start_time
                histogram.observe(duration, labels)
        
        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator