"""
MCP Server - Caching
Response caching strategies for improved performance.
"""

import hashlib
import json
import time
from typing import Any, Dict, Optional

from ...config.logging_config import get_logger

logger = get_logger(__name__)


class CacheEntry:
    """Cache entry with expiration."""

    def __init__(self, value: Any, ttl: float):
        self.value = value
        self.expiry = time.time() + ttl
        self.created_at = time.time()

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() > self.expiry


class ResponseCache:
    """
    Simple in-memory cache for API responses.

    Example:
        cache = ResponseCache(default_ttl=300)
        cache.set("key", data)
        result = cache.get("key")
    """

    def __init__(self, default_ttl: float = 300):
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            self._misses += 1
            return None

        entry = self._cache[key]

        if entry.is_expired():
            del self._cache[key]
            self._misses += 1
            return None

        self._hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if not provided)
        """
        ttl = ttl or self.default_ttl
        self._cache[key] = CacheEntry(value, ttl)

    def delete(self, key: str):
        """Delete entry from cache."""
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> Dict:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = (
            (self._hits / total_requests * 100) if total_requests > 0 else 0
        )

        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2),
        }

    def cleanup_expired(self):
        """Remove expired entries."""
        expired_keys = [
            key for key, entry in self._cache.items() if entry.is_expired()
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")


def generate_cache_key(endpoint: str, params: Dict[str, Any]) -> str:
    """
    Generate a cache key from endpoint and parameters.

    Args:
        endpoint: API endpoint
        params: Request parameters

    Returns:
        Cache key hash
    """
    # Sort params for consistent key generation
    sorted_params = json.dumps(params, sort_keys=True)
    key_str = f"{endpoint}:{sorted_params}"

    # Generate hash
    return hashlib.md5(key_str.encode()).hexdigest()


# Global cache instance
_cache = ResponseCache(default_ttl=300)


def get_response_cache() -> ResponseCache:
    """Get the global response cache instance."""
    return _cache
