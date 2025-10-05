"""
Enhanced logging configuration and setup for xSwE Agent.
Provides structured logging with correlation IDs, request tracking,
and comprehensive error context for robust monitoring and debugging.
"""

import asyncio
import json
import logging
import sys
import traceback
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from threading import local
from typing import Any, Dict, Optional, Union

import structlog
from loguru import logger

# Prefer importing the package-level compatibility helper which exposes
# get_config for legacy callers and get_settings for newer code.
from . import get_config

# Context variables for correlation tracking
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id: ContextVar[Optional[str]] = ContextVar('user_id', default=None)

# Thread-local storage for sync contexts
_thread_local = local()


class CorrelatedFormatter(logging.Formatter):
    """Custom formatter that includes correlation context."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Add correlation context to record
        record.correlation_id = get_correlation_id()
        record.request_id = get_request_id()
        record.user_id = get_user_id()
        
        # Add performance context if available
        if hasattr(record, 'duration'):
            record.performance = {'duration': record.duration}
        
        return super().format(record)


class StructuredJsonFormatter(logging.Formatter):
    """JSON formatter with structured fields for production logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add correlation context
        if correlation_id := get_correlation_id():
            log_entry['correlation_id'] = correlation_id
        if request_id := get_request_id():
            log_entry['request_id'] = request_id
        if user_id := get_user_id():
            log_entry['user_id'] = user_id
        
        # Add exception information
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info),
            }
        
        # Add extra fields from the record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info', 'correlation_id', 'request_id',
                          'user_id']:
                if not key.startswith('_'):
                    log_entry['extra'] = log_entry.get('extra', {})
                    log_entry['extra'][key] = value
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)


class EnhancedLoggerSetup:
    """Enhanced centralized logging setup with correlation and structured output."""

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

        # Setup enhanced logging
        self._setup_python_logging()
        self._setup_structlog()
        self._setup_loguru()
        
    def _setup_python_logging(self):
        """Configure Python standard logging with enhanced formatters."""
        # Clear any existing handlers
        root = logging.getLogger()
        root.handlers.clear()
        
        # Set log level
        log_level = getattr(logging, getattr(self.config.logging, 'level', 'INFO').upper())
        root.setLevel(log_level)
        
        # Console handler with appropriate formatter
        console_handler = logging.StreamHandler(sys.stdout)
        
        # Choose formatter based on environment
        if getattr(self.config, 'debug', False) or getattr(self.config.logging, 'format', 'simple') == 'simple':
            # Development/debug mode - human readable
            formatter = CorrelatedFormatter(
                '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | '
                '[%(correlation_id)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            # Production mode - structured JSON
            formatter = StructuredJsonFormatter()
        
        console_handler.setFormatter(formatter)
        root.addHandler(console_handler)
        
        # File handler if configured
        if hasattr(self.config.logging, 'file') and self.config.logging.file:
            file_handler = logging.FileHandler(self.config.logging.file)
            file_handler.setFormatter(StructuredJsonFormatter())  # Always JSON for files
            root.addHandler(file_handler)


# Legacy class for backward compatibility
class LoggerSetup(EnhancedLoggerSetup):
    """Legacy logger setup - redirects to enhanced version."""
    pass

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


# Correlation ID utilities
def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())


def set_correlation_id(correlation_id_value: str) -> None:
    """Set the correlation ID for the current context."""
    correlation_id.set(correlation_id_value)
    
    # Also set in thread local for sync contexts
    _thread_local.correlation_id = correlation_id_value


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID."""
    try:
        # Try context var first (works in async)
        return correlation_id.get()
    except LookupError:
        # Fall back to thread local (sync contexts)
        return getattr(_thread_local, 'correlation_id', None)


def set_request_id(request_id_value: str) -> None:
    """Set the request ID for the current context."""
    request_id.set(request_id_value)
    _thread_local.request_id = request_id_value


def get_request_id() -> Optional[str]:
    """Get the current request ID."""
    try:
        return request_id.get()
    except LookupError:
        return getattr(_thread_local, 'request_id', None)


def set_user_id(user_id_value: str) -> None:
    """Set the user ID for the current context."""
    user_id.set(user_id_value)
    _thread_local.user_id = user_id_value


def get_user_id() -> Optional[str]:
    """Get the current user ID."""
    try:
        return user_id.get()
    except LookupError:
        return getattr(_thread_local, 'user_id', None)


@contextmanager
def correlation_context(correlation_id_value: Optional[str] = None, 
                       request_id_value: Optional[str] = None,
                       user_id_value: Optional[str] = None):
    """Context manager for setting correlation context."""
    # Generate correlation ID if not provided
    if correlation_id_value is None:
        correlation_id_value = generate_correlation_id()
    
    # Save previous values
    old_correlation = get_correlation_id()
    old_request = get_request_id()
    old_user = get_user_id()
    
    try:
        # Set new values
        set_correlation_id(correlation_id_value)
        if request_id_value:
            set_request_id(request_id_value)
        if user_id_value:
            set_user_id(user_id_value)
        
        yield {
            'correlation_id': correlation_id_value,
            'request_id': request_id_value,
            'user_id': user_id_value,
        }
    finally:
        # Restore previous values
        if old_correlation:
            set_correlation_id(old_correlation)
        if old_request:
            set_request_id(old_request)
        if old_user:
            set_user_id(old_user)


def with_correlation(correlation_id_value: Optional[str] = None):
    """Decorator for adding correlation context to functions."""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                with correlation_context(correlation_id_value):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                with correlation_context(correlation_id_value):
                    return func(*args, **kwargs)
            return sync_wrapper
    return decorator


# Initialize enhanced logging on module import
_logger_setup = EnhancedLoggerSetup()


def setup_logging() -> EnhancedLoggerSetup:
    """Ensure logging is configured and return the LoggerSetup instance.

    This is a small compatibility helper for modules that import
    ``setup_logging`` from this package during application bootstrap.
    """
    global _logger_setup
    if _logger_setup is None:
        _logger_setup = EnhancedLoggerSetup()
    return _logger_setup


def with_correlation(func):
    """
    Decorator to add correlation ID to log context.
    
    Example:
        @with_correlation
        async def process_request():
            logger.info("Processing request")  # Will include correlation_id
    """
    import functools
    import uuid
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        correlation_id = str(uuid.uuid4())
        bound_logger = logger.bind(correlation_id=correlation_id)
        
        # Store in context for nested calls
        import contextvars
        _correlation_id = contextvars.ContextVar('correlation_id', default=None)
        token = _correlation_id.set(correlation_id)
        
        try:
            return await func(*args, **kwargs)
        finally:
            _correlation_id.reset(token)
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        correlation_id = str(uuid.uuid4())
        bound_logger = logger.bind(correlation_id=correlation_id)
        
        import contextvars
        _correlation_id = contextvars.ContextVar('correlation_id', default=None)
        token = _correlation_id.set(correlation_id)
        
        try:
            return func(*args, **kwargs)
        finally:
            _correlation_id.reset(token)
    
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
