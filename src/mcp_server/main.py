"""
MCP Server - Main Application
Initializes the FastAPI application, middleware, and routers.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..config import get_config
from ..config.logging_config import get_logger, setup_logging
from .routers import ai, analytics, charts, github, health, metrics, resources, tools
from .services.lifespan import lifespan
from .services.middleware import (
    ErrorHandlingMiddleware,
    PerformanceMonitoringMiddleware,
    RequestCorrelationMiddleware,
    RequestLoggingMiddleware,
)

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Get application settings
settings = get_config()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="A comprehensive MCP server with monitoring, analytics, and AI capabilities for GitHub repositories.",
    version="1.0.0",
    lifespan=lifespan,
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- Middleware (order matters - first added is outermost) ---

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(",") if settings.cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handling middleware
app.add_middleware(ErrorHandlingMiddleware)

# Performance monitoring middleware
app.add_middleware(PerformanceMonitoringMiddleware)

# Request correlation middleware
app.add_middleware(RequestCorrelationMiddleware)

# Request logging middleware
app.add_middleware(RequestLoggingMiddleware)


# --- Routers ---

# Core functionality routers
app.include_router(github.router, prefix="/api/v1/github", tags=["GitHub"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(charts.router, prefix="/api/v1/charts", tags=["Charts"])

# New AI and monitoring routers
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI"])
app.include_router(health.router, prefix="/api/v1/health", tags=["Health"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["Metrics"])

# MCP protocol routers
app.include_router(tools.router, prefix="/api/v1/mcp/tools", tags=["MCP Tools"])
app.include_router(resources.router, prefix="/api/v1/mcp/resources", tags=["MCP Resources"])


# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def read_root():
    """Root endpoint providing basic application info."""
    return {
        "application": settings.app_name,
        "version": app.version,
        "message": "Welcome to the xSweAgent MCP Server!",
        "documentation": "/docs",
        "api_endpoints": {
            "github": "/api/v1/github",
            "analytics": "/api/v1/analytics",
            "charts": "/api/v1/charts",
            "ai": "/api/v1/ai",
            "health": "/api/v1/health",
            "metrics": "/api/v1/metrics",
            "mcp_tools": "/api/v1/mcp/tools",
            "mcp_resources": "/api/v1/mcp/resources",
        },
    }


# --- Health Endpoint (basic liveness) ---
@app.get("/health", tags=["Health"])
async def read_health():
    """Simple health check endpoint used by monitoring/probes."""
    return {
        "status": "ok",
        "application": settings.app_name,
        "version": app.version,
    }


# --- Exception Handler ---
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handles unexpected errors."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    logger.error(
        f"Unhandled exception for {request.method} {request.url}",
        correlation_id=correlation_id,
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred.",
            "correlation_id": correlation_id,
        },
    )
