"""
MCP Server - Metrics Router
Handles metrics collection and exposition endpoints.
"""

import logging

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, Response

from ...config.logging_config import get_logger
from ...utils import get_metrics_collector
from ...utils.metrics import Counter

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_class=PlainTextResponse)
async def get_metrics_prometheus():
    """
    Get metrics in Prometheus exposition format.

    Returns:
        Metrics in Prometheus text format
    """
    try:
        collector = get_metrics_collector()
        prometheus_text = collector.get_prometheus_format()

        return Response(
            content=prometheus_text,
            media_type="text/plain; version=0.0.4",
        )
    except Exception as e:
        logger.error(f"Failed to generate Prometheus metrics: {e}", exc_info=True)
        return Response(
            content=f"# Error generating metrics: {str(e)}\n",
            media_type="text/plain",
        )


@router.get("/summary")
async def get_metrics_summary():
    """
    Get human-readable metrics summary.

    Returns:
        JSON formatted metrics summary
    """
    try:
        collector = get_metrics_collector()
        metrics = collector.get_all_metrics()
        stats = collector.get_stats()

        metrics_data = {}
        for name, metric in metrics.items():
            if hasattr(metric, 'get_value'):
                value = metric.get_value()
                if isinstance(value, dict):
                    metrics_data[name] = value
                else:
                    metrics_data[name] = {"value": value}

        return {
            "metrics": metrics_data,
            "stats": stats,
            "total_metrics": len(metrics),
        }
    except Exception as e:
        logger.error(f"Failed to get metrics summary: {e}", exc_info=True)
        return {
            "error": str(e),
        }


@router.get("/performance")
async def get_performance_metrics():
    """
    Get performance-specific metrics.

    Returns:
        Performance metrics including API call times and throughput
    """
    try:
        collector = get_metrics_collector()
        metrics = collector.get_all_metrics()

        # Filter performance-related metrics
        performance_metrics = {}
        for name, metric in metrics.items():
            if "duration" in name or "time" in name or "latency" in name:
                if hasattr(metric, 'get_value'):
                    value = metric.get_value()
                    if isinstance(value, dict):
                        performance_metrics[name] = value
                    else:
                        performance_metrics[name] = {"value": value}

        # Get counter metrics  
        counter_metrics = {}
        for name, metric in metrics.items():
            if isinstance(metric, Counter):
                counter_metrics[name] = metric.get_value()
        
        api_calls = {
            k: v for k, v in counter_metrics.items() if "calls_total" in k
        }

        return {
            "performance_metrics": performance_metrics,
            "api_calls": api_calls,
        }
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}", exc_info=True)
        return {
            "error": str(e),
        }


@router.delete("/reset")
async def reset_metrics():
    """
    Reset all collected metrics.

    Returns:
        Confirmation of metrics reset
    """
    try:
        collector = get_metrics_collector()
        collector.clear()

        logger.info("Metrics reset successfully")

        return {
            "status": "success",
            "message": "All metrics have been reset",
        }
    except Exception as e:
        logger.error(f"Failed to reset metrics: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
        }


@router.get("/health")
async def get_metrics_health():
    """
    Get metrics system health.

    Returns:
        Health status of metrics collection system
    """
    try:
        collector = get_metrics_collector()
        metrics = collector.get_all_metrics()
        stats = collector.get_stats()

        return {
            "status": "healthy",
            "metrics_count": len(metrics),
            "counters_count": stats.get("metrics_by_type", {}).get("counter", 0),
            "collection_active": True,
            "stats": stats,
        }
    except Exception as e:
        logger.error(f"Metrics health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e),
        }
