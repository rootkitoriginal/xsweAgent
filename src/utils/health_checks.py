"""
Health check utilities for monitoring service availability.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    name: str
    status: HealthStatus
    message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    response_time_ms: Optional[float] = None


class HealthCheck:
    """
    Health check for monitoring service availability.

    Performs periodic checks and tracks service health over time.
    """

    def __init__(
        self,
        name: str,
        check_func: Callable,
        interval: float = 60.0,
        timeout: float = 10.0,
    ):
        """
        Initialize health check.

        Args:
            name: Name of the service to check
            check_func: Async function that performs the health check
            interval: Seconds between checks
            timeout: Timeout for each check
        """
        self.name = name
        self.check_func = check_func
        self.interval = interval
        self.timeout = timeout
        self.last_result: Optional[HealthCheckResult] = None
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

    async def perform_check(self) -> HealthCheckResult:
        """Perform a single health check."""
        start_time = time.time()
        try:
            await asyncio.wait_for(self.check_func(), timeout=self.timeout)
            response_time = (time.time() - start_time) * 1000

            result = HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                message="Service is healthy",
                response_time_ms=response_time,
            )
        except asyncio.TimeoutError:
            result = HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timed out after {self.timeout}s",
            )
        except Exception as e:
            result = HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                details={"error": str(e)},
            )

        self.last_result = result
        return result

    async def start_monitoring(self):
        """Start continuous health monitoring."""
        if self.is_running:
            logger.warning(f"Health check {self.name} is already running")
            return

        self.is_running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Started health monitoring for {self.name}")

    async def stop_monitoring(self):
        """Stop continuous health monitoring."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"Stopped health monitoring for {self.name}")

    async def _monitor_loop(self):
        """Continuous monitoring loop."""
        while self.is_running:
            try:
                await self.perform_check()
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check monitoring loop: {e}")
                await asyncio.sleep(self.interval)

    def get_status(self) -> Optional[HealthCheckResult]:
        """Get the last health check result."""
        return self.last_result

    def is_healthy(self) -> bool:
        """Check if service is currently healthy."""
        return (
            self.last_result is not None
            and self.last_result.status == HealthStatus.HEALTHY
        )


class HealthCheckRegistry:
    """Registry for managing multiple health checks."""

    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}

    def register(self, health_check: HealthCheck):
        """Register a health check."""
        self.checks[health_check.name] = health_check
        logger.info(f"Registered health check: {health_check.name}")

    def unregister(self, name: str):
        """Unregister a health check."""
        if name in self.checks:
            del self.checks[name]
            logger.info(f"Unregistered health check: {name}")

    async def start_all(self):
        """Start all registered health checks."""
        for check in self.checks.values():
            await check.start_monitoring()

    async def stop_all(self):
        """Stop all registered health checks."""
        for check in self.checks.values():
            await check.stop_monitoring()

    async def check_all(self) -> Dict[str, HealthCheckResult]:
        """Perform all health checks once."""
        results = {}
        for name, check in self.checks.items():
            results[name] = await check.perform_check()
        return results

    def get_overall_status(self) -> HealthStatus:
        """Get overall health status across all services."""
        if not self.checks:
            return HealthStatus.HEALTHY

        unhealthy_count = sum(
            1
            for check in self.checks.values()
            if check.last_result
            and check.last_result.status == HealthStatus.UNHEALTHY
        )
        degraded_count = sum(
            1
            for check in self.checks.values()
            if check.last_result and check.last_result.status == HealthStatus.DEGRADED
        )

        if unhealthy_count > 0:
            return HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY


# Global health check registry
_health_registry = HealthCheckRegistry()


def get_health_registry() -> HealthCheckRegistry:
    """Get the global health check registry."""
    return _health_registry
