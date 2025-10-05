"""
Health check system for monitoring service availability.
Provides health status for dependencies and internal components.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Optional

from ..config.logging_config import get_logger

logger = get_logger("health_checks")


class HealthStatus(str, Enum):
    """Health check status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    name: str
    status: HealthStatus
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


class HealthCheck:
    """Base class for health checks."""

    def __init__(self, name: str, timeout: float = 5.0):
        self.name = name
        self.timeout = timeout
        self.logger = get_logger(f"health_check.{name}")

    async def check(self) -> HealthCheckResult:
        """Perform the health check.

        Returns:
            HealthCheckResult with status
        """
        try:
            # Run with timeout
            result = await asyncio.wait_for(
                self._perform_check(), timeout=self.timeout
            )
            return result
        except asyncio.TimeoutError:
            self.logger.warning(f"Health check {self.name} timed out")
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check timed out after {self.timeout}s",
            )
        except Exception as e:
            self.logger.error(f"Health check {self.name} failed", error=str(e))
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {str(e)}",
            )

    async def _perform_check(self) -> HealthCheckResult:
        """Override this method to implement specific health check logic."""
        raise NotImplementedError


class CallableHealthCheck(HealthCheck):
    """Health check that wraps a callable function."""

    def __init__(
        self,
        name: str,
        check_func: Callable[[], bool],
        timeout: float = 5.0,
    ):
        super().__init__(name, timeout)
        self.check_func = check_func

    async def _perform_check(self) -> HealthCheckResult:
        """Execute the check function."""
        if asyncio.iscoroutinefunction(self.check_func):
            is_healthy = await self.check_func()
        else:
            is_healthy = self.check_func()

        if is_healthy:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                message="Check passed",
            )
        else:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message="Check failed",
            )


class HealthCheckRegistry:
    """Registry for managing multiple health checks."""

    def __init__(self):
        self._checks: Dict[str, HealthCheck] = {}

    def register(self, check: HealthCheck):
        """Register a health check.

        Args:
            check: HealthCheck instance to register
        """
        self._checks[check.name] = check
        logger.info(f"Registered health check: {check.name}")

    def unregister(self, name: str):
        """Unregister a health check.

        Args:
            name: Name of check to unregister
        """
        if name in self._checks:
            del self._checks[name]
            logger.info(f"Unregistered health check: {name}")

    async def check_all(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks.

        Returns:
            Dict mapping check name to result
        """
        results = {}

        if not self._checks:
            logger.warning("No health checks registered")
            return results

        # Run checks concurrently
        tasks = [check.check() for check in self._checks.values()]
        check_results = await asyncio.gather(*tasks, return_exceptions=True)

        for check_name, result in zip(self._checks.keys(), check_results):
            if isinstance(result, Exception):
                results[check_name] = HealthCheckResult(
                    name=check_name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check raised exception: {str(result)}",
                )
            else:
                results[check_name] = result

        return results

    async def get_overall_status(self) -> HealthStatus:
        """Get overall system health status.

        Returns:
            HEALTHY if all checks pass
            DEGRADED if some checks fail
            UNHEALTHY if critical checks fail
        """
        results = await self.check_all()

        if not results:
            return HealthStatus.UNKNOWN

        statuses = [r.status for r in results.values()]

        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.DEGRADED

    def get_registered_checks(self) -> List[str]:
        """Get list of registered check names."""
        return list(self._checks.keys())


# Global health check registry
_health_registry = HealthCheckRegistry()


def get_health_registry() -> HealthCheckRegistry:
    """Get the global health check registry."""
    return _health_registry


def register_health_check(
    name: str,
    check_func: Callable[[], bool],
    timeout: float = 5.0,
):
    """Register a health check function.

    Args:
        name: Name for the health check
        check_func: Function that returns True if healthy
        timeout: Timeout in seconds

    Example:
        async def check_github_api():
            # Check if GitHub API is accessible
            return True

        register_health_check("github_api", check_github_api)
    """
    check = CallableHealthCheck(name, check_func, timeout)
    _health_registry.register(check)
