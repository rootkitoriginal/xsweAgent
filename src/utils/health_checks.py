"""
Health check system for monitoring component availability.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

from .exceptions import HealthCheckError

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    component: str
    status: HealthStatus
    message: str = ""
    details: Dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0.0


class HealthCheck:
    """
    Health check for a system component.

    Example:
        async def check_database():
            await db.ping()
            return HealthCheckResult(
                component="database",
                status=HealthStatus.HEALTHY,
                message="Database connection OK"
            )

        health_check = HealthCheck("database", check_database)
        result = await health_check.execute()
    """

    def __init__(
        self,
        name: str,
        check_func: Callable,
        timeout: float = 5.0,
        critical: bool = True,
    ):
        self.name = name
        self.check_func = check_func
        self.timeout = timeout
        self.critical = critical

    async def execute(self) -> HealthCheckResult:
        """Execute the health check."""
        start_time = time.time()

        try:
            if asyncio.iscoroutinefunction(self.check_func):
                result = await asyncio.wait_for(
                    self.check_func(), timeout=self.timeout
                )
            else:
                result = self.check_func()

            if isinstance(result, HealthCheckResult):
                result.duration_ms = (time.time() - start_time) * 1000
                return result
            else:
                # If check returns True/None, consider it healthy
                return HealthCheckResult(
                    component=self.name,
                    status=HealthStatus.HEALTHY,
                    message=f"{self.name} is healthy",
                    duration_ms=(time.time() - start_time) * 1000,
                )

        except asyncio.TimeoutError:
            logger.error(f"Health check timeout for {self.name}")
            return HealthCheckResult(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timed out after {self.timeout}s",
                duration_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            return HealthCheckResult(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
            )


class HealthCheckRegistry:
    """
    Registry for managing multiple health checks.

    Example:
        registry = HealthCheckRegistry()
        registry.register(HealthCheck("db", check_db))
        registry.register(HealthCheck("cache", check_cache))

        results = await registry.check_all()
    """

    def __init__(self):
        self._checks: Dict[str, HealthCheck] = {}

    def register(self, check: HealthCheck):
        """Register a health check."""
        self._checks[check.name] = check
        logger.info(f"Registered health check: {check.name}")

    def unregister(self, name: str):
        """Unregister a health check."""
        if name in self._checks:
            del self._checks[name]
            logger.info(f"Unregistered health check: {name}")

    async def check(self, name: str) -> HealthCheckResult:
        """Execute a specific health check."""
        if name not in self._checks:
            raise HealthCheckError(f"Health check not found: {name}")

        return await self._checks[name].execute()

    async def check_all(self) -> Dict[str, HealthCheckResult]:
        """Execute all registered health checks."""
        results = {}

        for name, check in self._checks.items():
            results[name] = await check.execute()

        return results

    async def get_overall_status(self) -> HealthStatus:
        """Get overall system health status."""
        results = await self.check_all()

        if not results:
            return HealthStatus.HEALTHY

        # Check critical components
        has_critical_failure = False
        has_degraded = False

        for name, result in results.items():
            check = self._checks[name]

            if result.status == HealthStatus.UNHEALTHY and check.critical:
                has_critical_failure = True
            elif result.status in (HealthStatus.UNHEALTHY, HealthStatus.DEGRADED):
                has_degraded = True

        if has_critical_failure:
            return HealthStatus.UNHEALTHY
        elif has_degraded:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    def list_checks(self) -> List[str]:
        """List all registered health checks."""
        return list(self._checks.keys())


# Global registry instance
_registry = HealthCheckRegistry()


def get_health_check_registry() -> HealthCheckRegistry:
    """Get the global health check registry."""
    return _registry
