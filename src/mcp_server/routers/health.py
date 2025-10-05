"""
MCP Server - Health Router
Handles system health monitoring endpoints.
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, Request

from ...config.logging_config import get_logger
from ...utils import HealthStatus, get_health_check_registry

logger = get_logger(__name__)
router = APIRouter()


@router.get("/status")
async def get_health_status():
    """
    Get overall system health status.

    Returns:
        Overall health status and component summary
    """
    registry = get_health_check_registry()

    try:
        system_health = await registry.get_system_health()
        
        # get_system_health already returns everything we need
        return {
            "status": system_health["status"],
            "components": system_health["summary"]["total_checks"],
            "summary": {
                "healthy": system_health["summary"]["healthy"],
                "degraded": system_health["summary"]["degraded"],
                "unhealthy": system_health["summary"]["unhealthy"]
            },
            "timestamp": system_health["timestamp"],
        }
    except Exception as e:
        logger.error(f"Failed to get health status: {e}", exc_info=True)
        return {
            "status": HealthStatus.UNHEALTHY.value,
            "error": str(e),
        }


@router.get("/components")
async def get_component_health():
    """
    Get detailed health status for all components.

    Returns:
        Detailed health information for each component
    """
    registry = get_health_check_registry()

    try:
        results = await registry.check_all()

        components = {}
        for name, result in results.items():
            components[name] = {
                "status": result.status.value,
                "message": result.message,
                "duration_ms": result.duration * 1000,
                "timestamp": result.timestamp,
                "details": result.details,
            }

        return {
            "components": components,
            "total": len(components),
        }
    except Exception as e:
        logger.error(f"Failed to get component health: {e}", exc_info=True)
        return {
            "error": str(e),
            "components": {},
        }


@router.get("/components/{component}")
async def get_specific_component_health(component: str):
    """
    Get health status for a specific component.

    Args:
        component: Name of the component to check

    Returns:
        Health status for the specified component
    """
    registry = get_health_check_registry()

    try:
        result = await registry.check(component)

        return {
            "component": component,
            "status": result.status.value,
            "message": result.message,
            "duration_ms": result.duration * 1000,
            "timestamp": result.timestamp,
            "details": result.details,
        }
    except Exception as e:
        logger.error(
            f"Failed to get health for component {component}: {e}", exc_info=True
        )
        return {
            "component": component,
            "status": HealthStatus.UNHEALTHY.value,
            "error": str(e),
        }


@router.get("/metrics")
async def get_health_metrics():
    """
    Get aggregated health metrics.

    Returns:
        Aggregated health metrics across all components
    """
    registry = get_health_check_registry()

    try:
        results = await registry.check_all()

        if not results:
            return {
                "total_checks": 0,
                "avg_duration_ms": 0,
                "status_distribution": {},
            }

        total_duration = sum(r.duration * 1000 for r in results.values())
        avg_duration = total_duration / len(results)

        status_distribution = {
            "healthy": sum(
                1 for r in results.values() if r.status == HealthStatus.HEALTHY
            ),
            "degraded": sum(
                1 for r in results.values() if r.status == HealthStatus.DEGRADED
            ),
            "unhealthy": sum(
                1 for r in results.values() if r.status == HealthStatus.UNHEALTHY
            ),
        }

        return {
            "total_checks": len(results),
            "avg_duration_ms": round(avg_duration, 2),
            "min_duration_ms": round(
                min(r.duration * 1000 for r in results.values()), 2
            ),
            "max_duration_ms": round(
                max(r.duration * 1000 for r in results.values()), 2
            ),
            "status_distribution": status_distribution,
        }
    except Exception as e:
        logger.error(f"Failed to get health metrics: {e}", exc_info=True)
        return {
            "error": str(e),
        }


@router.post("/check")
async def trigger_health_check():
    """
    Manually trigger a comprehensive health check.

    Returns:
        Results of the triggered health check
    """
    registry = get_health_check_registry()

    try:
        results = await registry.check_all()
        overall_status = await registry.get_system_health()

        return {
            "status": overall_status.value,
            "checks_performed": len(results),
            "results": {
                name: {
                    "status": result.status.value,
                    "message": result.message,
                    "duration_ms": result.duration * 1000,
                }
                for name, result in results.items()
            },
        }
    except Exception as e:
        logger.error(f"Health check trigger failed: {e}", exc_info=True)
        return {
            "status": HealthStatus.UNHEALTHY.value,
            "error": str(e),
        }


@router.get("/list")
async def list_health_checks():
    """
    List all registered health checks.

    Returns:
        List of registered health check names
    """
    registry = get_health_check_registry()
    checks = registry.list_checks()

    return {
        "checks": checks,
        "total": len(checks),
    }
