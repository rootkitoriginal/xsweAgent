"""
Tests for CachedGitHubRepository caching functionality.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import using proper package structure
from src.github_monitor.repository import (AwaitableList,
                                           CachedGitHubRepository,
                                           SearchCriteria)


@pytest.fixture
def cached_repo():
    """Fixture for CachedGitHubRepository with test configuration."""
    return CachedGitHubRepository(
        repo_name="test/repo",
        api_token="fake_token",
        default_ttl=5,  # 5 seconds for faster tests
    )


@pytest.fixture
def mock_github_issues():
    """Fixture for mock GitHub issues."""
    issue1 = MagicMock()
    issue1.number = 1
    issue1.title = "Test Issue 1"
    issue1.state = "open"
    issue1.created_at = "2023-01-01T12:00:00Z"
    issue1.updated_at = "2023-01-02T12:00:00Z"
    issue1.closed_at = None
    issue1.user.login = "testuser"

    issue2 = MagicMock()
    issue2.number = 2
    issue2.title = "Test Issue 2"
    issue2.state = "closed"
    issue2.created_at = "2023-01-03T12:00:00Z"
    issue2.updated_at = "2023-01-04T12:00:00Z"
    issue2.closed_at = "2023-01-05T12:00:00Z"
    issue2.user.login = "testuser"

    return [issue1, issue2]


class TestCachedGitHubRepository:
    """Test suite for CachedGitHubRepository caching functionality."""

    def test_initialization(self, cached_repo):
        """Test that CachedGitHubRepository initializes correctly."""
        assert cached_repo._cache == {}
        assert cached_repo._cache_hits == 0
        assert cached_repo._cache_misses == 0
        assert "issues" in cached_repo._ttl_config
        assert "issue" in cached_repo._ttl_config
        assert "repository_info" in cached_repo._ttl_config
        assert "timeline" in cached_repo._ttl_config

    def test_cache_key_generation(self, cached_repo):
        """Test cache key generation with various parameters."""
        # Simple key
        key1 = cached_repo._generate_cache_key("issues")
        assert key1 == "issues"

        # Key with args
        key2 = cached_repo._generate_cache_key("issue", 123)
        assert key2 == "issue:123"

        # Key with kwargs
        key3 = cached_repo._generate_cache_key("issues", state="open", labels="bug")
        assert "state=open" in key3
        assert "labels=bug" in key3

    @patch("github.Github")
    def test_get_issues_cache_miss(self, MockGithub, cached_repo, mock_github_issues):
        """Test get_issues on cache miss."""
        mock_github_repo = MagicMock()
        mock_github_repo.get_issues.return_value = mock_github_issues

        mock_instance = MockGithub.return_value
        mock_instance.get_repo.return_value = mock_github_repo

        # First call should be a cache miss
        issues = cached_repo.get_issues()

        assert len(issues) == 2
        assert cached_repo._cache_misses == 1
        assert cached_repo._cache_hits == 0
        assert len(cached_repo._cache) == 1

    @patch("github.Github")
    def test_get_issues_cache_hit(self, MockGithub, cached_repo, mock_github_issues):
        """Test get_issues on cache hit."""
        mock_github_repo = MagicMock()
        mock_github_repo.get_issues.return_value = mock_github_issues

        mock_instance = MockGithub.return_value
        mock_instance.get_repo.return_value = mock_github_repo

        # First call - cache miss
        issues1 = cached_repo.get_issues()
        assert cached_repo._cache_misses == 1
        assert cached_repo._cache_hits == 0

        # Second call - cache hit
        issues2 = cached_repo.get_issues()
        assert cached_repo._cache_misses == 1
        assert cached_repo._cache_hits == 1

        # Results should be identical
        assert len(issues1) == len(issues2)

    @patch("github.Github")
    def test_get_issues_with_different_criteria(
        self, MockGithub, cached_repo, mock_github_issues
    ):
        """Test that different search criteria produce different cache keys."""
        mock_github_repo = MagicMock()
        mock_github_repo.get_issues.return_value = mock_github_issues

        mock_instance = MockGithub.return_value
        mock_instance.get_repo.return_value = mock_github_repo

        # Call with different criteria
        criteria1 = SearchCriteria(state="open")
        issues1 = cached_repo.get_issues(criteria1)

        criteria2 = SearchCriteria(state="closed")
        issues2 = cached_repo.get_issues(criteria2)

        # Should have 2 cache entries (different keys)
        assert len(cached_repo._cache) == 2
        assert cached_repo._cache_misses == 2
        assert cached_repo._cache_hits == 0

    def test_cache_expiration(self, cached_repo):
        """Test that cache expires after TTL."""
        # Manually add data to cache with old timestamp
        old_time = datetime.now() - timedelta(seconds=10)
        cache_key = "test:key"
        cached_repo._cache[cache_key] = ("test_data", old_time)

        # Check if cache is valid (TTL is 5 seconds, data is 10 seconds old)
        is_valid = cached_repo._is_cache_valid(
            cache_key, cached_repo._ttl_config["issues"]
        )
        assert is_valid is False

    def test_cache_not_expired(self, cached_repo):
        """Test that cache is valid within TTL."""
        # Add fresh data to cache
        cache_key = "test:key"
        cached_repo._cache[cache_key] = ("test_data", datetime.now())

        # Check if cache is valid
        is_valid = cached_repo._is_cache_valid(
            cache_key, cached_repo._ttl_config["issues"]
        )
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_get_issue_caching(self, cached_repo):
        """Test get_issue method caching."""
        with patch.object(
            cached_repo.__class__.__bases__[0], "get_issue", new_callable=AsyncMock
        ) as mock_get_issue:
            mock_get_issue.return_value = {"number": 123, "title": "Test Issue"}

            # First call - cache miss
            issue1 = await cached_repo.get_issue(123)
            assert cached_repo._cache_misses == 1
            assert mock_get_issue.call_count == 1

            # Second call - cache hit
            issue2 = await cached_repo.get_issue(123)
            assert cached_repo._cache_hits == 1
            assert mock_get_issue.call_count == 1  # Should not call parent again

            assert issue1 == issue2

    @pytest.mark.asyncio
    async def test_get_repository_info_caching(self, cached_repo):
        """Test get_repository_info method caching."""
        with patch.object(
            cached_repo.__class__.__bases__[0],
            "get_repository_info",
            new_callable=AsyncMock,
        ) as mock_get_repo:
            mock_get_repo.return_value = {"name": "test/repo", "stars": 100}

            # First call - cache miss
            info1 = await cached_repo.get_repository_info()
            assert cached_repo._cache_misses == 1
            assert mock_get_repo.call_count == 1

            # Second call - cache hit
            info2 = await cached_repo.get_repository_info()
            assert cached_repo._cache_hits == 1
            assert mock_get_repo.call_count == 1

            assert info1 == info2

    @pytest.mark.asyncio
    async def test_get_issue_timeline_caching(self, cached_repo):
        """Test get_issue_timeline method caching."""
        with patch.object(
            cached_repo.__class__.__bases__[0],
            "get_issue_timeline",
            new_callable=AsyncMock,
        ) as mock_get_timeline:
            mock_get_timeline.return_value = [
                {"event": "commented", "time": "2023-01-01"}
            ]

            # First call - cache miss
            timeline1 = await cached_repo.get_issue_timeline(123)
            assert cached_repo._cache_misses == 1
            assert mock_get_timeline.call_count == 1

            # Second call - cache hit
            timeline2 = await cached_repo.get_issue_timeline(123)
            assert cached_repo._cache_hits == 1
            assert mock_get_timeline.call_count == 1

            assert timeline1 == timeline2

    def test_clear_cache(self, cached_repo):
        """Test clear_cache method."""
        # Add some data to cache
        cached_repo._cache["key1"] = ("data1", datetime.now())
        cached_repo._cache["key2"] = ("data2", datetime.now())
        cached_repo._cache_hits = 5
        cached_repo._cache_misses = 3

        # Clear cache
        cached_repo.clear_cache()

        assert len(cached_repo._cache) == 0
        assert cached_repo._cache_hits == 0
        assert cached_repo._cache_misses == 0

    def test_invalidate_cache_all(self, cached_repo):
        """Test invalidate_cache without pattern (clear all)."""
        # Add some data to cache
        cached_repo._cache["issues:open"] = ("data1", datetime.now())
        cached_repo._cache["issue:123"] = ("data2", datetime.now())
        cached_repo._cache["timeline:456"] = ("data3", datetime.now())

        # Invalidate all
        count = cached_repo.invalidate_cache()

        assert count == 3
        assert len(cached_repo._cache) == 0

    def test_invalidate_cache_pattern(self, cached_repo):
        """Test invalidate_cache with pattern."""
        # Add some data to cache
        cached_repo._cache["issues:open"] = ("data1", datetime.now())
        cached_repo._cache["issues:closed"] = ("data2", datetime.now())
        cached_repo._cache["issue:123"] = ("data3", datetime.now())
        cached_repo._cache["timeline:456"] = ("data4", datetime.now())

        # Invalidate only 'issues:' entries
        count = cached_repo.invalidate_cache("issues:")

        assert count == 2
        assert len(cached_repo._cache) == 2
        assert "issue:123" in cached_repo._cache
        assert "timeline:456" in cached_repo._cache

    def test_get_cache_stats(self, cached_repo):
        """Test get_cache_stats method."""
        # Add some data and simulate hits/misses
        cached_repo._cache["key1"] = ("data1", datetime.now())
        cached_repo._cache["key2"] = ("data2", datetime.now())
        cached_repo._cache_hits = 8
        cached_repo._cache_misses = 2

        stats = cached_repo.get_cache_stats()

        assert stats["total_entries"] == 2
        assert stats["cache_hits"] == 8
        assert stats["cache_misses"] == 2
        assert stats["hit_rate_percent"] == 80.0
        assert "ttl_config" in stats

    def test_get_cache_stats_no_requests(self, cached_repo):
        """Test get_cache_stats with no requests."""
        stats = cached_repo.get_cache_stats()

        assert stats["total_entries"] == 0
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["hit_rate_percent"] == 0.0

    def test_custom_ttl_configuration(self):
        """Test custom TTL configuration."""
        repo = CachedGitHubRepository(
            repo_name="test/repo", api_token="fake_token", default_ttl=10
        )

        # Check default TTLs based on custom default
        assert repo._ttl_config["issues"] == 10
        assert repo._ttl_config["issue"] == 10
        assert repo._ttl_config["repository_info"] == 60  # 6x default
        assert repo._ttl_config["timeline"] == 20  # 2x default

    @patch("github.Github")
    def test_repository_info_longer_ttl(self, MockGithub):
        """Test that repository_info has longer TTL than other methods."""
        repo = CachedGitHubRepository(
            repo_name="test/repo", api_token="fake_token", default_ttl=5
        )

        # Repository info should have longer TTL
        assert repo._ttl_config["repository_info"] > repo._ttl_config["issues"]
        assert repo._ttl_config["repository_info"] > repo._ttl_config["issue"]
        assert repo._ttl_config["repository_info"] > repo._ttl_config["timeline"]
