"""
Logging configuration and setup for xSwE Agent.
Provides structured logging with multiple output formats and levels.
"""

import structlog
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

import structlog
from loguru import logger

# Prefer importing the package-level compatibility helper which exposes
# get_config for legacy callers and get_settings for newer code.
from . import get_config


class LoggerSetup:
    """Centralized logging setup and configuration."""

    def __init__(self):
        try:
            self.config = get_config()
        except Exception:
            # During unit tests we may intentionally trigger
            # ValidationError when instantiating config classes. To avoid
            # crashing imports, fall back to a minimal config object that
            # provides the attributes used by the logger setup.
            from types import SimpleNamespace

            fallback_logging = SimpleNamespace(level="INFO", format="simple", file=None)
            fallback = SimpleNamespace(debug=False, logging=fallback_logging)
            self.config = fallback

        # Proceed to initialize logging subsystems; they will use the
        # fallback config when real settings are not yet available.
        self._setup_structlog()
        self._setup_loguru()

    def _setup_structlog(self):
        """Configure structlog for structured logging."""
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                (
                    structlog.dev.ConsoleRenderer()
                    if self.config.debug
                    else structlog.processors.JSONRenderer()
                ),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, self.config.logging.level)
            ),
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )

    def _setup_loguru(self):
        """Configure loguru for enhanced logging features."""
        # Remove default logger
        logger.remove()

        # Console logger
        logger.add(
            sys.stderr,
            format=self._get_log_format(),
            level=self.config.logging.level,
            colorize=True,
            backtrace=True,
            diagnose=self.config.debug,
        )

        # File logger (if configured)
        if self.config.logging.file:
            log_path = Path(self.config.logging.file)
            log_path.parent.mkdir(exist_ok=True)
            try:
                logger.add(
                    log_path,
                    format=self._get_log_format(for_file=True),
                    level=self.config.logging.level,
                    rotation="1 day",
                    retention="30 days",
                    compression="gz",
                    backtrace=True,
                    diagnose=self.config.debug,
                )
            except PermissionError:
                # If we cannot write to the file (readonly FS, permissions),
                # continue with console-only logging to avoid crashing the app.
                logger.warning(
                    f"Cannot write log file {log_path}; continuing with console logging only."
                )
            except Exception:
                # Generic fallback: don't let logging setup crash the application.
                logger.warning(
                    f"Failed to initialize file logger for {log_path}; continuing with console logging."
                )

    def _get_log_format(self, for_file: bool = False) -> str:
        """Get appropriate log format based on configuration."""
        if self.config.logging.format == "json":
            return "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}"
        elif self.config.logging.format == "simple":
            return "{time:HH:mm:ss} | {level} | {message}"
        else:  # structured
            if for_file:
                return "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}"
            else:
                return "<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>"


class XSWELogger:
    """Enhanced logger with context management for xSwE Agent."""

    def __init__(self, name: str):
        self.name = name
        self.logger = logger.bind(component=name)
        self.struct_logger = structlog.get_logger(name)

    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message with context."""
        self.logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message with context."""
        self.logger.critical(message, **kwargs)

    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, **kwargs)

    def bind(self, **kwargs) -> "XSWELogger":
        """Create new logger with bound context."""
        new_logger = XSWELogger(self.name)
        new_logger.logger = self.logger.bind(**kwargs)
        new_logger.struct_logger = self.struct_logger.bind(**kwargs)
        return new_logger

    def with_context(self, **kwargs) -> "XSWELogger":
        """Add context to logger (alias for bind)."""
        return self.bind(**kwargs)


class PerformanceLogger:
    """Logger for performance monitoring and metrics."""

    def __init__(self):
        self.logger = XSWELogger("performance")

    def log_api_call(
        self,
        api_name: str,
        endpoint: str,
        duration_ms: float,
        status_code: Optional[int] = None,
        **kwargs,
    ):
        """Log API call performance metrics."""
        self.logger.info(
            "API call completed",
            api_name=api_name,
            endpoint=endpoint,
            duration_ms=duration_ms,
            status_code=status_code,
            **kwargs,
        )

    def log_function_timing(self, function_name: str, duration_ms: float, **kwargs):
        """Log function execution timing."""
        self.logger.info(
            "Function execution completed",
            function=function_name,
            duration_ms=duration_ms,
            **kwargs,
        )

    def log_chart_generation(
        self, chart_type: str, data_points: int, duration_ms: float, **kwargs
    ):
        """Log chart generation performance."""
        self.logger.info(
            "Chart generation completed",
            chart_type=chart_type,
            data_points=data_points,
            duration_ms=duration_ms,
            **kwargs,
        )


class SecurityLogger:
    """Logger for security-related events."""

    def __init__(self):
        self.logger = XSWELogger("security")

    def log_authentication_attempt(
        self,
        user_id: Optional[str] = None,
        success: bool = True,
        ip_address: Optional[str] = None,
        **kwargs,
    ):
        """Log authentication attempts."""
        self.logger.info(
            "Authentication attempt",
            user_id=user_id,
            success=success,
            ip_address=ip_address,
            **kwargs,
        )

    def log_api_access(
        self,
        endpoint: str,
        method: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        **kwargs,
    ):
        """Log API access events."""
        self.logger.info(
            "API access",
            endpoint=endpoint,
            method=method,
            user_id=user_id,
            ip_address=ip_address,
            **kwargs,
        )

    def log_rate_limit_exceeded(
        self, api_name: str, user_id: Optional[str] = None, **kwargs
    ):
        """Log rate limiting events."""
        self.logger.warning(
            "Rate limit exceeded", api_name=api_name, user_id=user_id, **kwargs
        )


def get_logger(name: str) -> XSWELogger:
    """Get a logger instance for the specified component."""
    return XSWELogger(name)


def get_performance_logger() -> PerformanceLogger:
    """Get the performance logger instance."""
    return PerformanceLogger()


def get_security_logger() -> SecurityLogger:
    """Get the security logger instance."""
    return SecurityLogger()


# Initialize logging on module import
_logger_setup = LoggerSetup()


def setup_logging() -> LoggerSetup:
    """Ensure logging is configured and return the LoggerSetup instance.

    This is a small compatibility helper for modules that import
    ``setup_logging`` from this package during application bootstrap.
    """
    global _logger_setup
    if _logger_setup is None:
        _logger_setup = LoggerSetup()
    return _logger_setup
