"""
MCP Server - Middleware
Custom middleware for logging, correlation, and error handling.
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ...config.logging_config import get_logger, get_performance_logger

logger = get_logger(__name__)
perf_logger = get_performance_logger()


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation IDs to requests for tracing.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

        # Store in request state
        request.state.correlation_id = correlation_id

        # Add to logger context
        bound_logger = logger.bind(correlation_id=correlation_id)

        # Call next middleware/endpoint
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware to monitor and log request performance.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Call next middleware/endpoint
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log performance metrics
        perf_logger.log_api_call(
            api_name="mcp_server",
            endpoint=request.url.path,
            duration_ms=duration_ms,
            status_code=response.status_code,
            method=request.method,
        )

        # Add performance headers
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive error handling and logging.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Log the error with context
            correlation_id = getattr(request.state, "correlation_id", "unknown")
            logger.error(
                f"Unhandled error in request",
                correlation_id=correlation_id,
                path=request.url.path,
                method=request.method,
                error=str(e),
                exc_info=True,
            )

            # Return a generic error response
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=500,
                content={
                    "detail": "An internal server error occurred",
                    "correlation_id": correlation_id,
                },
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for detailed request/response logging.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Log request
        correlation_id = getattr(request.state, "correlation_id", "unknown")

        logger.info(
            "Incoming request",
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else "unknown",
        )

        # Call next middleware/endpoint
        response = await call_next(request)

        # Log response
        logger.info(
            "Outgoing response",
            correlation_id=correlation_id,
            status_code=response.status_code,
        )

        return response
