"""
Health check utilities for monitoring service health.
Provides components for tracking and reporting system health status.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ServiceHealth:
    """Health information for a service or component."""

    name: str
    status: HealthStatus
    message: str = ""
    last_check: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "last_check": self.last_check.isoformat(),
            "metadata": self.metadata,
        }


class HealthCheck:
    """
    Health check manager for monitoring multiple services.

    Example:
        health = HealthCheck()
        health.register("database", lambda: check_db_connection())
        health.register("cache", lambda: check_redis())
        status = health.check_all()
    """

    def __init__(self):
        self._checks: Dict[str, Callable[[], bool]] = {}
        self._results: Dict[str, ServiceHealth] = {}

    def register(self, name: str, check_func: Callable[[], bool]):
        """
        Register a health check function.

        Args:
            name: Service name
            check_func: Function that returns True if healthy, False otherwise
        """
        self._checks[name] = check_func
        logger.debug(f"Registered health check for {name}")

    def check(self, name: str) -> ServiceHealth:
        """
        Execute health check for a specific service.

        Args:
            name: Service name

        Returns:
            ServiceHealth object with check results
        """
        if name not in self._checks:
            return ServiceHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"No health check registered for {name}",
            )

        try:
            is_healthy = self._checks[name]()
            status = HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY
            message = "Service is operational" if is_healthy else "Service check failed"

            result = ServiceHealth(
                name=name,
                status=status,
                message=message,
                last_check=datetime.now(),
            )
            self._results[name] = result
            return result

        except Exception as e:
            logger.error(f"Health check failed for {name}: {e}")
            result = ServiceHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check error: {str(e)}",
                last_check=datetime.now(),
            )
            self._results[name] = result
            return result

    def check_all(self) -> Dict[str, ServiceHealth]:
        """
        Execute all registered health checks.

        Returns:
            Dictionary of service names to health status
        """
        results = {}
        for name in self._checks.keys():
            results[name] = self.check(name)
        return results

    def get_overall_status(self) -> HealthStatus:
        """
        Get overall system health status.

        Returns:
            HEALTHY if all services healthy, UNHEALTHY if any unhealthy,
            DEGRADED if some are unhealthy but system is operational
        """
        if not self._results:
            self.check_all()

        statuses = [result.status for result in self._results.values()]

        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            # Consider system degraded if less than half are unhealthy
            unhealthy_count = sum(1 for s in statuses if s == HealthStatus.UNHEALTHY)
            if unhealthy_count < len(statuses) / 2:
                return HealthStatus.DEGRADED
            return HealthStatus.UNHEALTHY
        else:
            return HealthStatus.DEGRADED

    def get_summary(self) -> Dict[str, Any]:
        """
        Get health check summary.

        Returns:
            Dictionary with overall status and individual service results
        """
        return {
            "overall_status": self.get_overall_status().value,
            "services": {
                name: result.to_dict() for name, result in self._results.items()
            },
            "timestamp": datetime.now().isoformat(),
        }
