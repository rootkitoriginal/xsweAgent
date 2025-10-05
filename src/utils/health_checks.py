"""
Health check system for monitoring component availability and performance.

This module provides comprehensive health checking capabilities for all
system components including external APIs, database connections, and
system resources.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from .exceptions import HealthCheckException

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status values."""
    
    HEALTHY = "healthy"
    DEGRADED = "degraded"  
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""
    
    component: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration: float = 0.0  # Check duration in seconds
    error: Optional[Exception] = None
    
    def is_healthy(self) -> bool:
        """Check if the component is healthy."""
        return self.status == HealthStatus.HEALTHY
    
    def is_degraded(self) -> bool:
        """Check if the component is degraded but functional."""
        return self.status == HealthStatus.DEGRADED
    
    def is_unhealthy(self) -> bool:
        """Check if the component is unhealthy."""
        return self.status == HealthStatus.UNHEALTHY
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "component": self.component,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "duration": self.duration,
            "error": str(self.error) if self.error else None,
        }


@dataclass
class HealthCheckConfig:
    """Configuration for health checks."""
    
    timeout: float = 10.0  # Timeout in seconds
    interval: float = 30.0  # Check interval in seconds
    retries: int = 1  # Number of retries on failure
    retry_delay: float = 1.0  # Delay between retries
    critical: bool = False  # Whether failure affects overall system health
    enabled: bool = True  # Whether the check is enabled
    
    # Thresholds
    warning_threshold: Optional[float] = None  # Response time warning threshold
    critical_threshold: Optional[float] = None  # Response time critical threshold


class BaseHealthCheck(ABC):
    """Base class for all health checks."""
    
    def __init__(
        self,
        name: str,
        config: Optional[HealthCheckConfig] = None,
        description: str = "",
    ):
        self.name = name
        self.config = config or HealthCheckConfig()
        self.description = description
        self._last_result: Optional[HealthCheckResult] = None
        self._check_count = 0
        self._failure_count = 0
    
    @abstractmethod
    async def _perform_check(self) -> HealthCheckResult:
        """Perform the actual health check. Must be implemented by subclasses."""
        pass
    
    async def check(self) -> HealthCheckResult:
        """Execute the health check with retry logic and timing."""
        if not self.config.enabled:
            return HealthCheckResult(
                component=self.name,
                status=HealthStatus.UNKNOWN,
                message="Health check disabled",
            )
        
        start_time = time.time()
        last_error = None
        
        for attempt in range(self.config.retries + 1):
            try:
                result = await asyncio.wait_for(
                    self._perform_check(),
                    timeout=self.config.timeout
                )
                result.duration = time.time() - start_time
                
                # Apply thresholds to determine status
                if result.status == HealthStatus.HEALTHY:
                    result = self._apply_thresholds(result)
                
                self._last_result = result
                self._check_count += 1
                
                if not result.is_healthy():
                    self._failure_count += 1
                
                logger.debug(
                    f"Health check '{self.name}' completed: {result.status.value}",
                    extra={
                        "component": self.name,
                        "status": result.status.value,
                        "duration": result.duration,
                        "attempt": attempt + 1,
                    }
                )
                
                return result
                
            except asyncio.TimeoutError:
                last_error = TimeoutError(f"Health check timeout after {self.config.timeout}s")
            except Exception as e:
                last_error = e
                
            # Retry if not the last attempt
            if attempt < self.config.retries:
                logger.warning(
                    f"Health check '{self.name}' failed on attempt {attempt + 1}, retrying: {last_error}"
                )
                await asyncio.sleep(self.config.retry_delay)
        
        # All retries failed
        result = HealthCheckResult(
            component=self.name,
            status=HealthStatus.UNHEALTHY,
            message=f"Check failed after {self.config.retries + 1} attempts: {last_error}",
            duration=time.time() - start_time,
            error=last_error,
        )
        
        self._last_result = result
        self._check_count += 1
        self._failure_count += 1
        
        logger.error(
            f"Health check '{self.name}' failed: {last_error}",
            extra={
                "component": self.name,
                "error": str(last_error),
                "attempts": self.config.retries + 1,
            }
        )
        
        return result
    
    def _apply_thresholds(self, result: HealthCheckResult) -> HealthCheckResult:
        """Apply response time thresholds to determine status."""
        if self.config.critical_threshold and result.duration > self.config.critical_threshold:
            result.status = HealthStatus.UNHEALTHY
            result.message += f" (response time {result.duration:.2f}s exceeds critical threshold)"
        elif self.config.warning_threshold and result.duration > self.config.warning_threshold:
            result.status = HealthStatus.DEGRADED
            result.message += f" (response time {result.duration:.2f}s exceeds warning threshold)"
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get health check statistics."""
        failure_rate = self._failure_count / max(self._check_count, 1)
        
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.config.enabled,
            "critical": self.config.critical,
            "check_count": self._check_count,
            "failure_count": self._failure_count,
            "failure_rate": failure_rate,
            "last_result": self._last_result.to_dict() if self._last_result else None,
        }


class GitHubAPIHealthCheck(BaseHealthCheck):
    """Health check for GitHub API availability."""
    
    def __init__(
        self,
        api_token: Optional[str] = None,
        config: Optional[HealthCheckConfig] = None,
    ):
        super().__init__(
            name="github_api",
            config=config or HealthCheckConfig(timeout=10.0, critical=True),
            description="GitHub API connectivity and rate limit check",
        )
        self.api_token = api_token
    
    async def _perform_check(self) -> HealthCheckResult:
        """Check GitHub API health by calling the rate limit endpoint."""
        try:
            import aiohttp
            
            headers = {}
            if self.api_token:
                headers["Authorization"] = f"token {self.api_token}"
                headers["Accept"] = "application/vnd.github.v3+json"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.github.com/rate_limit",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Check rate limit status
                        core_limit = data.get("resources", {}).get("core", {})
                        remaining = core_limit.get("remaining", 0)
                        limit = core_limit.get("limit", 5000)
                        reset_time = core_limit.get("reset", 0)
                        
                        usage_percent = ((limit - remaining) / limit) * 100 if limit > 0 else 0
                        
                        # Determine status based on usage
                        if usage_percent >= 90:
                            status = HealthStatus.DEGRADED
                            message = f"GitHub API rate limit nearly exhausted ({remaining}/{limit})"
                        elif usage_percent >= 95:
                            status = HealthStatus.UNHEALTHY
                            message = f"GitHub API rate limit critical ({remaining}/{limit})"
                        else:
                            status = HealthStatus.HEALTHY
                            message = f"GitHub API available ({remaining}/{limit} requests remaining)"
                        
                        return HealthCheckResult(
                            component=self.name,
                            status=status,
                            message=message,
                            details={
                                "rate_limit": {
                                    "remaining": remaining,
                                    "limit": limit,
                                    "reset": reset_time,
                                    "usage_percent": round(usage_percent, 2),
                                }
                            },
                        )
                    
                    else:
                        return HealthCheckResult(
                            component=self.name,
                            status=HealthStatus.UNHEALTHY,
                            message=f"GitHub API returned status {response.status}",
                            details={"status_code": response.status},
                        )
                        
        except Exception as e:
            raise HealthCheckException(
                f"Failed to check GitHub API health: {str(e)}",
                component=self.name,
                status="unhealthy",
                details={"error": str(e)},
            )


class GeminiAPIHealthCheck(BaseHealthCheck):
    """Health check for Gemini AI API availability."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[HealthCheckConfig] = None,
    ):
        super().__init__(
            name="gemini_api",
            config=config or HealthCheckConfig(timeout=15.0, critical=False),
            description="Gemini AI API connectivity check",
        )
        self.api_key = api_key
    
    async def _perform_check(self) -> HealthCheckResult:
        """Check Gemini API health with a simple request."""
        try:
            # This is a placeholder - implement based on actual Gemini API
            if not self.api_key:
                return HealthCheckResult(
                    component=self.name,
                    status=HealthStatus.DEGRADED,
                    message="Gemini API key not configured",
                    details={"configured": False},
                )
            
            # Simple connectivity test (adjust based on actual Gemini API)
            import aiohttp
            
            # Use a lightweight endpoint for health checking
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            # This would need to be replaced with actual Gemini API endpoint
            test_payload = {
                "contents": [{"parts": [{"text": "ping"}]}],
                "generationConfig": {"maxOutputTokens": 1}
            }
            
            async with aiohttp.ClientSession() as session:
                # Placeholder URL - replace with actual Gemini health/test endpoint
                async with session.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
                    headers=headers,
                    json=test_payload,
                    params={"key": self.api_key}
                ) as response:
                    
                    if response.status == 200:
                        return HealthCheckResult(
                            component=self.name,
                            status=HealthStatus.HEALTHY,
                            message="Gemini API available and responding",
                            details={"configured": True},
                        )
                    elif response.status == 429:
                        return HealthCheckResult(
                            component=self.name,
                            status=HealthStatus.DEGRADED,
                            message="Gemini API rate limited",
                            details={"status_code": response.status},
                        )
                    else:
                        return HealthCheckResult(
                            component=self.name,
                            status=HealthStatus.UNHEALTHY,
                            message=f"Gemini API returned status {response.status}",
                            details={"status_code": response.status},
                        )
                        
        except Exception as e:
            raise HealthCheckException(
                f"Failed to check Gemini API health: {str(e)}",
                component=self.name,
                status="unhealthy",
                details={"error": str(e)},
            )


class DatabaseHealthCheck(BaseHealthCheck):
    """Health check for database connectivity."""
    
    def __init__(
        self,
        connection_string: Optional[str] = None,
        config: Optional[HealthCheckConfig] = None,
    ):
        super().__init__(
            name="database",
            config=config or HealthCheckConfig(timeout=5.0, critical=True),
            description="Database connectivity and performance check",
        )
        self.connection_string = connection_string
    
    async def _perform_check(self) -> HealthCheckResult:
        """Check database health with a simple query."""
        try:
            # This is a placeholder for database connectivity check
            # Implement based on your actual database setup
            
            if not self.connection_string:
                return HealthCheckResult(
                    component=self.name,
                    status=HealthStatus.DEGRADED,
                    message="Database connection not configured",
                    details={"configured": False},
                )
            
            # Simulate database check (replace with actual implementation)
            await asyncio.sleep(0.1)  # Simulate connection time
            
            return HealthCheckResult(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message="Database connection available",
                details={
                    "configured": True,
                    "connection_string": self.connection_string[:20] + "..." if len(self.connection_string) > 20 else self.connection_string,
                },
            )
            
        except Exception as e:
            raise HealthCheckException(
                f"Failed to check database health: {str(e)}",
                component=self.name,
                status="unhealthy",
                details={"error": str(e)},
            )


class MemoryHealthCheck(BaseHealthCheck):
    """Health check for memory usage."""
    
    def __init__(self, config: Optional[HealthCheckConfig] = None):
        super().__init__(
            name="memory",
            config=config or HealthCheckConfig(
                timeout=2.0,
                critical=False,
                warning_threshold=0.8,  # 80% memory usage
                critical_threshold=0.95,  # 95% memory usage
            ),
            description="System memory usage check",
        )
    
    async def _perform_check(self) -> HealthCheckResult:
        """Check system memory usage."""
        try:
            import psutil
            
            # Get memory information
            memory = psutil.virtual_memory()
            usage_percent = memory.percent / 100
            
            # Determine status based on usage
            if usage_percent >= 0.95:
                status = HealthStatus.UNHEALTHY
                message = f"Critical memory usage: {usage_percent:.1%}"
            elif usage_percent >= 0.8:
                status = HealthStatus.DEGRADED
                message = f"High memory usage: {usage_percent:.1%}"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage normal: {usage_percent:.1%}"
            
            return HealthCheckResult(
                component=self.name,
                status=status,
                message=message,
                details={
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "free": memory.free,
                    "percent": memory.percent,
                },
            )
            
        except ImportError:
            return HealthCheckResult(
                component=self.name,
                status=HealthStatus.UNKNOWN,
                message="psutil not available for memory monitoring",
                details={"psutil_available": False},
            )
        except Exception as e:
            raise HealthCheckException(
                f"Failed to check memory health: {str(e)}",
                component=self.name,
                status="unhealthy",
                details={"error": str(e)},
            )


class HealthChecker:
    """Main health checker that manages multiple health checks."""
    
    def __init__(self):
        self.checks: Dict[str, BaseHealthCheck] = {}
        self.last_full_check: Optional[datetime] = None
        
    def register_check(self, check: BaseHealthCheck):
        """Register a health check."""
        self.checks[check.name] = check
        logger.info(f"Registered health check: {check.name}")
    
    def unregister_check(self, name: str):
        """Unregister a health check."""
        if name in self.checks:
            del self.checks[name]
            logger.info(f"Unregistered health check: {name}")
    
    async def check_single(self, name: str) -> Optional[HealthCheckResult]:
        """Run a single health check by name."""
        check = self.checks.get(name)
        if not check:
            return None
        return await check.check()
    
    async def check_all(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks."""
        self.last_full_check = datetime.utcnow()
        
        results = {}
        
        # Run all checks concurrently
        tasks = {name: check.check() for name, check in self.checks.items()}
        
        if tasks:
            completed = await asyncio.gather(*tasks.values(), return_exceptions=True)
            
            for (name, _), result in zip(tasks.items(), completed):
                if isinstance(result, Exception):
                    results[name] = HealthCheckResult(
                        component=name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Health check failed: {str(result)}",
                        error=result,
                    )
                else:
                    results[name] = result
        
        return results
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health summary."""
        results = await self.check_all()
        
        # Calculate overall status
        overall_status = HealthStatus.HEALTHY
        critical_failures = []
        degraded_components = []
        
        for name, result in results.items():
            check = self.checks.get(name)
            
            if result.is_unhealthy():
                if check and check.config.critical:
                    critical_failures.append(name)
                    overall_status = HealthStatus.UNHEALTHY
                elif overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
            elif result.is_degraded():
                degraded_components.append(name)
                if overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
        
        # Determine overall message
        if overall_status == HealthStatus.HEALTHY:
            message = "All systems operational"
        elif overall_status == HealthStatus.DEGRADED:
            message = f"System degraded ({len(degraded_components)} components affected)"
        else:
            message = f"System unhealthy ({len(critical_failures)} critical failures)"
        
        return {
            "status": overall_status.value,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "components": {name: result.to_dict() for name, result in results.items()},
            "summary": {
                "total_checks": len(results),
                "healthy": sum(1 for r in results.values() if r.is_healthy()),
                "degraded": sum(1 for r in results.values() if r.is_degraded()),
                "unhealthy": sum(1 for r in results.values() if r.is_unhealthy()),
                "critical_failures": critical_failures,
                "degraded_components": degraded_components,
            },
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get health checker statistics."""
        return {
            "registered_checks": len(self.checks),
            "last_full_check": self.last_full_check.isoformat() if self.last_full_check else None,
            "checks": {name: check.get_stats() for name, check in self.checks.items()},
        }


# Global health checker instance
_health_checker = HealthChecker()


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance."""
    return _health_checker


def setup_default_health_checks(
    github_token: Optional[str] = None,
    gemini_api_key: Optional[str] = None,
    database_url: Optional[str] = None,
) -> HealthChecker:
    """Set up default health checks for common components."""
    checker = get_health_checker()
    
    # GitHub API health check
    if github_token:
        checker.register_check(GitHubAPIHealthCheck(api_token=github_token))
    
    # Gemini API health check
    if gemini_api_key:
        checker.register_check(GeminiAPIHealthCheck(api_key=gemini_api_key))
    
    # Database health check
    if database_url:
        checker.register_check(DatabaseHealthCheck(connection_string=database_url))
    
    # Memory health check (always available)
    checker.register_check(MemoryHealthCheck())
    
    return checker