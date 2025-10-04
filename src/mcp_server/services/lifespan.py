"""
MCP Server - Lifespan Management
Handles application startup and shutdown events.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.github_monitor.service import GitHubIssuesService
from src.analytics.engine import create_analytics_engine
from src.config import get_config

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

    # GitHub service - let the service create its repository from configured settings
    # or provide a repository instance via the factory if explicit control is needed.
    github_service = GitHubIssuesService()

    # Analytics engine
    analytics_engine = await create_analytics_engine()

    # Store services in app state for access in routers
    app.state.github_service = github_service
    app.state.analytics_engine = analytics_engine

    logger.info("Services initialized and attached to app state.")

    yield

    # --- Cleanup on shutdown ---
    logger.info("Application shutting down...")

    # Clear any resources if necessary
    if hasattr(app.state, "analytics_engine"):
        app.state.analytics_engine.clear_cache()
        logger.info("Analytics cache cleared.")

    logger.info("Shutdown complete.")
