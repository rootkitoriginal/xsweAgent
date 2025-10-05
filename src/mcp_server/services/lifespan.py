"""
MCP Server - Lifespan Management
Handles application startup and shutdown events.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.analytics.engine import create_analytics_engine
from src.config import get_config
from src.github_monitor.service import GitHubIssuesService

from .monitoring import register_health_checks, run_periodic_health_checks

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Initializes and cleans up resources.
    """
    logger.info("Application starting up...")

    # --- Initialize services ---
    settings = get_config()

    # GitHub service
    github_service = GitHubIssuesService()

    # Analytics engine
    analytics_engine = await create_analytics_engine()

    # Gemini client (optional)
    gemini_client = None
    try:
        if hasattr(settings, "gemini") and settings.gemini.api_key:
            from src.gemini_integration import GeminiClient

            gemini_client = GeminiClient(api_key=settings.gemini.api_key)
            logger.info("Gemini AI client initialized")
    except Exception as e:
        logger.warning(f"Gemini AI client not available: {e}")

    # Store services in app state
    app.state.github_service = github_service
    app.state.analytics_engine = analytics_engine
    app.state.gemini_client = gemini_client

    # Register health checks
    register_health_checks()
    logger.info("Health checks registered")

    # Start periodic health check task
    health_check_task = asyncio.create_task(run_periodic_health_checks(interval=300))

    logger.info("Services initialized and attached to app state.")

    yield

    # --- Cleanup on shutdown ---
    logger.info("Application shutting down...")

    # Cancel periodic health checks
    health_check_task.cancel()
    try:
        await health_check_task
    except asyncio.CancelledError:
        pass

    # Clear any resources if necessary
    if hasattr(app.state, "analytics_engine"):
        app.state.analytics_engine.clear_cache()
        logger.info("Analytics cache cleared.")

    # Clear response cache
    from .caching import get_response_cache

    cache = get_response_cache()
    cache.clear()
    logger.info("Response cache cleared.")

    logger.info("Shutdown complete.")
