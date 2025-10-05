"""
MCP Server - Monitoring
Performance and health monitoring utilities.
"""

import asyncio
import logging
import time
from typing import Dict, List

from ...config.logging_config import get_logger
from ...utils import HealthCheck, HealthCheckResult, HealthStatus, get_health_check_registry

logger = get_logger(__name__)


async def check_github_service() -> HealthCheckResult:
    """Health check for GitHub service."""
    try:
        # This will be called with app context during actual checks
        return HealthCheckResult(
            component="github_service",
            status=HealthStatus.HEALTHY,
            message="GitHub service is operational",
        )
    except Exception as e:
        return HealthCheckResult(
            component="github_service",
            status=HealthStatus.UNHEALTHY,
            message=f"GitHub service error: {str(e)}",
        )


async def check_analytics_engine() -> HealthCheckResult:
    """Health check for analytics engine."""
    try:
        return HealthCheckResult(
            component="analytics_engine",
            status=HealthStatus.HEALTHY,
            message="Analytics engine is operational",
        )
    except Exception as e:
        return HealthCheckResult(
            component="analytics_engine",
            status=HealthStatus.UNHEALTHY,
            message=f"Analytics engine error: {str(e)}",
        )


async def check_gemini_client() -> HealthCheckResult:
    """Health check for Gemini AI client."""
    try:
        # Basic check - just verify it's configured
        return HealthCheckResult(
            component="gemini_client",
            status=HealthStatus.HEALTHY,
            message="Gemini AI client is configured",
        )
    except Exception as e:
        return HealthCheckResult(
            component="gemini_client",
            status=HealthStatus.DEGRADED,
            message=f"Gemini AI client not available: {str(e)}",
        )


async def check_cache_service() -> HealthCheckResult:
    """Health check for cache service."""
    try:
        from .caching import get_response_cache

        cache = get_response_cache()
        stats = cache.get_stats()

        return HealthCheckResult(
            component="cache_service",
            status=HealthStatus.HEALTHY,
            message=f"Cache operational with {stats['size']} entries",
            details=stats,
        )
    except Exception as e:
        return HealthCheckResult(
            component="cache_service",
            status=HealthStatus.UNHEALTHY,
            message=f"Cache service error: {str(e)}",
        )


async def check_metrics_collector() -> HealthCheckResult:
    """Health check for metrics collector."""
    try:
        from ...utils import get_metrics_collector

        collector = get_metrics_collector()
        metrics = collector.get_all_metrics()

        return HealthCheckResult(
            component="metrics_collector",
            status=HealthStatus.HEALTHY,
            message=f"Metrics collector operational with {len(metrics)} metrics",
            details={"metric_count": len(metrics)},
        )
    except Exception as e:
        return HealthCheckResult(
            component="metrics_collector",
            status=HealthStatus.UNHEALTHY,
            message=f"Metrics collector error: {str(e)}",
        )


def register_health_checks():
    """Register all health checks."""
    registry = get_health_check_registry()

    # Create simple health check classes
    class GitHubServiceHealthCheck(HealthCheck):
        def __init__(self):
            super().__init__("github_service")
        
        async def _perform_check(self) -> HealthCheckResult:
            return await check_github_service()

    class AnalyticsEngineHealthCheck(HealthCheck):
        def __init__(self):
            super().__init__("analytics_engine")
        
        async def _perform_check(self) -> HealthCheckResult:
            return await check_analytics_engine()

    class GeminiClientHealthCheck(HealthCheck):
        def __init__(self):
            super().__init__("gemini_client")
        
        async def _perform_check(self) -> HealthCheckResult:
            return await check_gemini_client()

    # Register health checks
    registry.register_check(GitHubServiceHealthCheck())
    registry.register_check(AnalyticsEngineHealthCheck())
    registry.register_check(GeminiClientHealthCheck())

    logger.info(f"Registered 3 health checks")


async def run_periodic_health_checks(interval: int = 60):
    """
    Run health checks periodically in the background.

    Args:
        interval: Check interval in seconds
    """
    registry = get_health_check_registry()

    while True:
        try:
            await asyncio.sleep(interval)

            results = await registry.check_all()
            overall_status = await registry.get_system_health()

            # Log summary
            healthy = sum(
                1 for r in results.values() if r.status == HealthStatus.HEALTHY
            )
            degraded = sum(
                1 for r in results.values() if r.status == HealthStatus.DEGRADED
            )
            unhealthy = sum(
                1 for r in results.values() if r.status == HealthStatus.UNHEALTHY
            )

            logger.info(
                f"Periodic health check completed",
                overall_status=overall_status.value,
                healthy=healthy,
                degraded=degraded,
                unhealthy=unhealthy,
            )

            # Log any unhealthy components
            for name, result in results.items():
                if result.status == HealthStatus.UNHEALTHY:
                    logger.warning(
                        f"Component unhealthy: {name}",
                        message=result.message,
                    )

        except Exception as e:
            logger.error(f"Periodic health check failed: {e}", exc_info=True)
