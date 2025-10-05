"""
Example usage of CachedGitHubRepository with caching capabilities.

This example demonstrates:
- Basic caching functionality
- Cache statistics monitoring
- Selective cache invalidation
- Performance comparison
"""

import asyncio
import time

from src.github_monitor.repository import (CachedGitHubRepository,
                                           SearchCriteria)


def example_basic_caching():
    """Demonstrate basic caching functionality."""
    print("\n" + "=" * 70)
    print("Example 1: Basic Caching")
    print("=" * 70)

    # Create a cached repository with 5-minute default TTL
    repo = CachedGitHubRepository(
        repo_name="octocat/Hello-World",
        token="your_github_token_here",  # Replace with your token
        default_ttl=300,  # 5 minutes
    )

    print("\nConfiguration:")
    print(f"  - Default TTL: 300s (5 minutes)")
    print(f"  - Repository Info TTL: 1800s (30 minutes)")

    print("\nNote: This is a demonstration. Replace token with real GitHub token")
    print("      to see actual API calls and caching in action.")


def example_cache_statistics():
    """Demonstrate cache statistics tracking."""
    print("\n" + "=" * 70)
    print("Example 2: Cache Statistics")
    print("=" * 70)

    repo = CachedGitHubRepository(
        repo_name="octocat/Hello-World", token="your_github_token_here", default_ttl=300
    )

    print("\nCache statistics structure:")
    stats = repo.get_cache_stats()
    print(f"  - total_entries: {stats['total_entries']}")
    print(f"  - cache_hits: {stats['cache_hits']}")
    print(f"  - cache_misses: {stats['cache_misses']}")
    print(f"  - hit_rate_percent: {stats['hit_rate_percent']}")
    print(f"  - ttl_config: {stats['ttl_config']}")


def example_cache_management():
    """Demonstrate cache management operations."""
    print("\n" + "=" * 70)
    print("Example 3: Cache Management")
    print("=" * 70)

    repo = CachedGitHubRepository(
        repo_name="octocat/Hello-World", token="your_github_token_here", default_ttl=300
    )

    print("\nAvailable cache management methods:")
    print("  1. clear_cache() - Clear all cache and reset stats")
    print("  2. invalidate_cache(pattern) - Selectively invalidate entries")
    print("  3. get_cache_stats() - Get cache performance metrics")

    print("\nExample invalidation patterns:")
    print("  - invalidate_cache('issues:') - All issues queries")
    print("  - invalidate_cache('issue:123') - Specific issue")
    print("  - invalidate_cache('timeline:') - All timelines")
    print("  - invalidate_cache() - Clear all (same as clear_cache)")


def example_ttl_configuration():
    """Demonstrate TTL configuration options."""
    print("\n" + "=" * 70)
    print("Example 4: TTL Configuration")
    print("=" * 70)

    # Different TTL strategies
    print("\nStrategy 1: Active Repository (1 minute base)")
    active = CachedGitHubRepository(repo_name="active/repo", default_ttl=60)
    print(f"  Issues: {active._ttl_config['issues']}s")
    print(f"  Repository Info: {active._ttl_config['repository_info']}s")

    print("\nStrategy 2: Stable Repository (30 minute base)")
    stable = CachedGitHubRepository(repo_name="stable/repo", default_ttl=1800)
    print(f"  Issues: {stable._ttl_config['issues']}s")
    print(f"  Repository Info: {stable._ttl_config['repository_info']}s")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("CachedGitHubRepository Examples")
    print("=" * 70)

    example_basic_caching()
    example_cache_statistics()
    example_cache_management()
    example_ttl_configuration()

    print("\n" + "=" * 70)
    print("Examples completed!")
    print("\nFor full working examples with real API calls,")
    print("replace 'your_github_token_here' with an actual GitHub token.")
    print("=" * 70)
