"""
MCP Server - Rate Limiting
Intelligent rate limiting for API endpoints.
"""

import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Optional

from fastapi import HTTPException, Request, status

from ...config.logging_config import get_security_logger
from ...utils import RateLimitError

security_logger = get_security_logger()


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10


class RateLimiter:
    """
    Token bucket rate limiter with per-client tracking.

    Example:
        limiter = RateLimiter(RateLimitConfig(requests_per_minute=100))
        limiter.check_rate_limit(client_id)
    """

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._buckets: Dict[str, Dict] = defaultdict(
            lambda: {
                "tokens": config.burst_size,
                "last_update": time.time(),
                "minute_count": 0,
                "minute_start": time.time(),
                "hour_count": 0,
                "hour_start": time.time(),
            }
        )

    def check_rate_limit(self, client_id: str) -> bool:
        """
        Check if request is within rate limits.

        Args:
            client_id: Unique client identifier

        Returns:
            True if within limits

        Raises:
            RateLimitError: If rate limit exceeded
        """
        now = time.time()
        bucket = self._buckets[client_id]

        # Reset minute counter
        if now - bucket["minute_start"] >= 60:
            bucket["minute_count"] = 0
            bucket["minute_start"] = now

        # Reset hour counter
        if now - bucket["hour_start"] >= 3600:
            bucket["hour_count"] = 0
            bucket["hour_start"] = now

        # Check minute limit
        if bucket["minute_count"] >= self.config.requests_per_minute:
            security_logger.log_rate_limit_exceeded(
                api_name="mcp_server", user_id=client_id
            )
            raise RateLimitError(
                f"Rate limit exceeded: {self.config.requests_per_minute} requests per minute"
            )

        # Check hour limit
        if bucket["hour_count"] >= self.config.requests_per_hour:
            security_logger.log_rate_limit_exceeded(
                api_name="mcp_server", user_id=client_id
            )
            raise RateLimitError(
                f"Rate limit exceeded: {self.config.requests_per_hour} requests per hour"
            )

        # Refill tokens
        time_elapsed = now - bucket["last_update"]
        tokens_to_add = time_elapsed * (
            self.config.requests_per_minute / 60.0
        )  # tokens per second
        bucket["tokens"] = min(
            self.config.burst_size, bucket["tokens"] + tokens_to_add
        )
        bucket["last_update"] = now

        # Check if we have tokens
        if bucket["tokens"] < 1.0:
            security_logger.log_rate_limit_exceeded(
                api_name="mcp_server", user_id=client_id
            )
            raise RateLimitError("Rate limit exceeded: too many requests")

        # Consume token
        bucket["tokens"] -= 1.0
        bucket["minute_count"] += 1
        bucket["hour_count"] += 1

        return True

    def get_stats(self, client_id: str) -> Dict:
        """Get rate limit statistics for a client."""
        if client_id not in self._buckets:
            return {
                "tokens": self.config.burst_size,
                "minute_count": 0,
                "hour_count": 0,
            }

        bucket = self._buckets[client_id]
        return {
            "tokens": bucket["tokens"],
            "minute_count": bucket["minute_count"],
            "hour_count": bucket["hour_count"],
            "minute_limit": self.config.requests_per_minute,
            "hour_limit": self.config.requests_per_hour,
        }


# Global rate limiter instance
_rate_limiter = RateLimiter(
    RateLimitConfig(
        requests_per_minute=100,
        requests_per_hour=5000,
        burst_size=20,
    )
)


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter


async def rate_limit_dependency(request: Request) -> bool:
    """
    FastAPI dependency for rate limiting.

    Example:
        @app.get("/endpoint", dependencies=[Depends(rate_limit_dependency)])
        async def endpoint():
            return {"message": "success"}
    """
    limiter = get_rate_limiter()

    # Use IP address as client identifier
    client_id = request.client.host if request.client else "unknown"

    try:
        limiter.check_rate_limit(client_id)
        return True
    except RateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": str(limiter.config.requests_per_minute),
            },
        )
