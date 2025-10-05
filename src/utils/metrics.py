"""
Metrics tracking and monitoring utilities.
"""

import logging
import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class APICallMetrics:
    """Metrics for a single API call."""

    operation: str
    start_time: float
    end_time: float
    duration_ms: float
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedMetrics:
    """Aggregated metrics for an operation."""

    operation: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_duration_ms: float = 0.0
    avg_duration_ms: float = 0.0
    min_duration_ms: Optional[float] = None
    max_duration_ms: Optional[float] = None

    def add_call(self, metrics: APICallMetrics):
        """Add a call to aggregated metrics."""
        self.total_calls += 1
        if metrics.success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1

        self.total_duration_ms += metrics.duration_ms

        if self.min_duration_ms is None or metrics.duration_ms < self.min_duration_ms:
            self.min_duration_ms = metrics.duration_ms
        if self.max_duration_ms is None or metrics.duration_ms > self.max_duration_ms:
            self.max_duration_ms = metrics.duration_ms

        self.avg_duration_ms = self.total_duration_ms / self.total_calls

    def get_success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_calls == 0:
            return 0.0
        return (self.successful_calls / self.total_calls) * 100


class MetricsTracker:
    """
    Tracks metrics for API calls and operations.

    Provides aggregated statistics and performance monitoring.
    """

    def __init__(self):
        self.metrics: Dict[str, List[APICallMetrics]] = {}
        self.aggregated: Dict[str, AggregatedMetrics] = {}

    def record_call(
        self, operation: str, duration_ms: float, success: bool, **metadata
    ):
        """Record a single API call."""
        now = time.time()
        metrics = APICallMetrics(
            operation=operation,
            start_time=now - (duration_ms / 1000),
            end_time=now,
            duration_ms=duration_ms,
            success=success,
            metadata=metadata,
        )

        # Store individual metric
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(metrics)

        # Update aggregated metrics
        if operation not in self.aggregated:
            self.aggregated[operation] = AggregatedMetrics(operation=operation)
        self.aggregated[operation].add_call(metrics)

        # Log if slow or failed
        if not success or duration_ms > 5000:
            level = logging.WARNING if not success else logging.INFO
            logger.log(
                level,
                f"API call {operation}: duration={duration_ms:.2f}ms, success={success}",
            )

    def get_metrics(self, operation: str) -> Optional[AggregatedMetrics]:
        """Get aggregated metrics for an operation."""
        return self.aggregated.get(operation)

    def get_all_metrics(self) -> Dict[str, AggregatedMetrics]:
        """Get all aggregated metrics."""
        return self.aggregated.copy()

    def get_recent_calls(
        self, operation: str, limit: int = 10
    ) -> List[APICallMetrics]:
        """Get recent calls for an operation."""
        if operation not in self.metrics:
            return []
        return self.metrics[operation][-limit:]

    def clear_metrics(self, operation: Optional[str] = None):
        """Clear metrics for an operation or all operations."""
        if operation:
            self.metrics.pop(operation, None)
            self.aggregated.pop(operation, None)
        else:
            self.metrics.clear()
            self.aggregated.clear()


# Global metrics tracker
_metrics_tracker = MetricsTracker()


def get_metrics_tracker() -> MetricsTracker:
    """Get the global metrics tracker."""
    return _metrics_tracker


def track_api_calls(operation: str) -> Callable:
    """
    Decorator to track API call metrics.

    Args:
        operation: Name of the operation to track

    Example:
        @track_api_calls('gemini_analysis')
        async def analyze_code(code: str):
            # Analysis logic
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            success = False
            error = None

            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error = str(e)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                _metrics_tracker.record_call(
                    operation=operation,
                    duration_ms=duration_ms,
                    success=success,
                    error=error,
                )

        return wrapper

    return decorator
