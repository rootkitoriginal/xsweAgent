"""
MCP Server - Main Application
Initializes the FastAPI application, middleware, and routers.
"""

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..config import get_config
from ..config.logging_config import setup_logging
from .routers import github, analytics, charts
from .services.lifespan import lifespan

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Get application settings
settings = get_config()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="A comprehensive monitoring and analytics server for GitHub repositories.",
    version="1.0.0",
    lifespan=lifespan,
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(",") if settings.cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log incoming requests."""
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

# --- Routers ---
app.include_router(github.router, prefix="/api/v1/github", tags=["GitHub"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(charts.router, prefix="/api/v1/charts", tags=["Charts"])


# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def read_root():
    """Root endpoint providing basic application info."""
    return {
        "application": settings.app_name,
        "version": app.version,
        "message": "Welcome to the xSweAgent MCP Server!",
        "documentation": "/docs"
    }


# --- Health Endpoint ---
@app.get("/health", tags=["Health"])
async def read_health():
    """Simple health check endpoint used by monitoring/probes."""
    # Basic liveness check. We can expand this to check DB/Redis later.
    return {"status": "ok", "application": settings.app_name}

# --- Exception Handler ---
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handles unexpected errors."""
    logger.error(f"Unhandled exception for {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."}
    )
