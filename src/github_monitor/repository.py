"""
GitHub Repository implementation using Repository Pattern.
Handles all interactions with GitHub API.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass

import httpx
from github import Github
from github.Issue import Issue as PyGithubIssue
from github.Repository import Repository as PyGithubRepo
from github.GithubException import GithubException, RateLimitExceededException

from ..config import get_config
from ..config.logging_config import get_logger
from .models import Issue, Repository, IssueState, GitHubUser, Label, Milestone


@dataclass
class SearchCriteria:
    """Search criteria for GitHub issues."""

    state: Optional[IssueState] = None
    labels: Optional[List[str]] = None
    assignee: Optional[str] = None
    creator: Optional[str] = None
    milestone: Optional[str] = None
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    sort: str = "created"
    direction: str = "desc"
    per_page: int = 100


class GitHubRepositoryInterface(ABC):
    """Abstract interface for GitHub repository operations."""

    @abstractmethod
    async def get_issues(self, criteria: SearchCriteria) -> List[Issue]:
        """Get issues based on search criteria."""
        pass

    @abstractmethod
    async def get_issue(self, issue_number: int) -> Optional[Issue]:
        """Get a specific issue by number."""
        pass

    @abstractmethod
    async def get_repository_info(self) -> Repository:
        """Get repository information."""
        pass

    @abstractmethod
    async def get_issue_timeline(self, issue_number: int) -> List[Dict[str, Any]]:
        """Get issue timeline events."""
        pass


class GitHubRepository(GitHubRepositoryInterface):
    """GitHub repository implementation with caching and rate limiting."""

    def __init__(self, owner: str, repo_name: str, token: str):
        self.owner = owner
        self.repo_name = repo_name
        self.token = token
        self.logger = get_logger("github_repository")
        self.config = get_config()

        # Initialize GitHub clients
        self.github = Github(token)
        self.repo = self.github.get_repo(f"{owner}/{repo_name}")

        # HTTP client for async operations
        self.http_client = httpx.AsyncClient(
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": f"xSWE-Agent/{self.config.version}",
            },
            timeout=30.0,
        )

        # Rate limiting
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = datetime.now()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.http_client.aclose()

    async def get_issues(self, criteria: SearchCriteria) -> List[Issue]:
        """Get issues based on search criteria with async pagination."""
        self.logger.info("Fetching issues", criteria=criteria.__dict__)

        try:
            issues = []
            page = 1

            while True:
                # Check rate limit
                await self._check_rate_limit()

                # Build query parameters
                params = self._build_query_params(criteria, page)

                # Make API request
                url = (
                    f"https://api.github.com/repos/{self.owner}/{self.repo_name}/issues"
                )
                response = await self.http_client.get(url, params=params)

                # Update rate limit info
                self._update_rate_limit_info(response.headers)

                if response.status_code != 200:
                    self.logger.error(
                        "Failed to fetch issues",
                        status_code=response.status_code,
                        response=response.text,
                    )
                    break

                data = response.json()

                if not data:  # No more issues
                    break

                # Convert to Issue objects
                for issue_data in data:
                    # Skip pull requests (GitHub API returns PRs as issues)
                    if issue_data.get("pull_request"):
                        continue

                    issue = Issue.from_dict(issue_data)
                    issues.append(issue)

                # Check if we got a full page
                if len(data) < criteria.per_page:
                    break

                page += 1

            self.logger.info(f"Fetched {len(issues)} issues")
            return issues

        except Exception as e:
            self.logger.exception("Error fetching issues", error=str(e))
            raise

    async def get_issue(self, issue_number: int) -> Optional[Issue]:
        """Get a specific issue by number."""
        self.logger.info(f"Fetching issue #{issue_number}")

        try:
            await self._check_rate_limit()

            url = f"https://api.github.com/repos/{self.owner}/{self.repo_name}/issues/{issue_number}"
            response = await self.http_client.get(url)

            self._update_rate_limit_info(response.headers)

            if response.status_code == 404:
                self.logger.warning(f"Issue #{issue_number} not found")
                return None

            if response.status_code != 200:
                self.logger.error(
                    f"Failed to fetch issue #{issue_number}",
                    status_code=response.status_code,
                    response=response.text,
                )
                return None

            data = response.json()

            # Skip if it's a pull request
            if data.get("pull_request"):
                return None

            issue = Issue.from_dict(data)
            self.logger.info(f"Successfully fetched issue #{issue_number}")
            return issue

        except Exception as e:
            self.logger.exception(f"Error fetching issue #{issue_number}", error=str(e))
            return None

    async def get_repository_info(self) -> Repository:
        """Get repository information."""
        self.logger.info("Fetching repository info")

        try:
            await self._check_rate_limit()

            url = f"https://api.github.com/repos/{self.owner}/{self.repo_name}"
            response = await self.http_client.get(url)

            self._update_rate_limit_info(response.headers)

            if response.status_code != 200:
                self.logger.error(
                    "Failed to fetch repository info",
                    status_code=response.status_code,
                    response=response.text,
                )
                raise Exception(f"Failed to fetch repository: {response.status_code}")

            data = response.json()
            repo = Repository.from_dict(data)

            self.logger.info("Successfully fetched repository info")
            return repo

        except Exception as e:
            self.logger.exception("Error fetching repository info", error=str(e))
            raise

    async def get_issue_timeline(self, issue_number: int) -> List[Dict[str, Any]]:
        """Get issue timeline events."""
        self.logger.info(f"Fetching timeline for issue #{issue_number}")

        try:
            await self._check_rate_limit()

            url = f"https://api.github.com/repos/{self.owner}/{self.repo_name}/issues/{issue_number}/timeline"
            headers = {
                **self.http_client.headers,
                "Accept": "application/vnd.github.mockingbird-preview+json",
            }

            response = await self.http_client.get(url, headers=headers)

            self._update_rate_limit_info(response.headers)

            if response.status_code != 200:
                self.logger.error(
                    f"Failed to fetch timeline for issue #{issue_number}",
                    status_code=response.status_code,
                    response=response.text,
                )
                return []

            timeline = response.json()
            self.logger.info(
                f"Fetched {len(timeline)} timeline events for issue #{issue_number}"
            )
            return timeline

        except Exception as e:
            self.logger.exception(
                f"Error fetching timeline for issue #{issue_number}", error=str(e)
            )
            return []

    async def get_issues_stream(
        self, criteria: SearchCriteria
    ) -> AsyncGenerator[Issue, None]:
        """Stream issues one by one for large datasets."""
        self.logger.info("Starting issue stream", criteria=criteria.__dict__)

        page = 1
        while True:
            await self._check_rate_limit()

            params = self._build_query_params(criteria, page)
            url = f"https://api.github.com/repos/{self.owner}/{self.repo_name}/issues"
            response = await self.http_client.get(url, params=params)

            self._update_rate_limit_info(response.headers)

            if response.status_code != 200:
                break

            data = response.json()
            if not data:
                break

            for issue_data in data:
                if issue_data.get("pull_request"):
                    continue

                issue = Issue.from_dict(issue_data)
                yield issue

            if len(data) < criteria.per_page:
                break

            page += 1

    def _build_query_params(
        self, criteria: SearchCriteria, page: int = 1
    ) -> Dict[str, Any]:
        """Build query parameters for GitHub API."""
        params = {
            "page": page,
            "per_page": criteria.per_page,
            "sort": criteria.sort,
            "direction": criteria.direction,
        }

        if criteria.state:
            params["state"] = criteria.state.value

        if criteria.labels:
            params["labels"] = ",".join(criteria.labels)

        if criteria.assignee:
            params["assignee"] = criteria.assignee

        if criteria.creator:
            params["creator"] = criteria.creator

        if criteria.milestone:
            params["milestone"] = criteria.milestone

        if criteria.since:
            params["since"] = criteria.since.isoformat()

        return params

    async def _check_rate_limit(self):
        """Check and handle GitHub API rate limiting."""
        now = datetime.now()

        if self.rate_limit_remaining <= 10 and now < self.rate_limit_reset:
            # Wait until rate limit resets
            wait_time = (self.rate_limit_reset - now).total_seconds()
            self.logger.warning(
                f"Rate limit nearly exceeded, waiting {wait_time:.1f} seconds"
            )
            await asyncio.sleep(wait_time)

    def _update_rate_limit_info(self, headers: Dict[str, str]):
        """Update rate limit information from response headers."""
        try:
            self.rate_limit_remaining = int(headers.get("X-RateLimit-Remaining", 5000))
            reset_timestamp = int(headers.get("X-RateLimit-Reset", 0))
            self.rate_limit_reset = datetime.fromtimestamp(reset_timestamp)

            self.logger.debug(
                "Updated rate limit info",
                remaining=self.rate_limit_remaining,
                reset_at=self.rate_limit_reset.isoformat(),
            )
        except (ValueError, TypeError):
            pass


class CachedGitHubRepository(GitHubRepositoryInterface):
    """GitHub repository with caching layer."""

    def __init__(self, base_repo: GitHubRepository, cache_ttl: int = 3600):
        self.base_repo = base_repo
        self.cache_ttl = cache_ttl
        self.logger = get_logger("cached_github_repository")
        self._cache: Dict[str, tuple] = {}  # key -> (data, timestamp)

    async def get_issues(self, criteria: SearchCriteria) -> List[Issue]:
        """Get cached issues or fetch from API."""
        cache_key = self._get_cache_key("issues", criteria)

        # Check cache first
        if self._is_cache_valid(cache_key):
            self.logger.debug("Returning cached issues")
            return self._cache[cache_key][0]

        # Fetch from API and cache
        issues = await self.base_repo.get_issues(criteria)
        self._cache[cache_key] = (issues, datetime.now())

        return issues

    async def get_issue(self, issue_number: int) -> Optional[Issue]:
        """Get cached issue or fetch from API."""
        cache_key = f"issue_{issue_number}"

        if self._is_cache_valid(cache_key):
            self.logger.debug(f"Returning cached issue #{issue_number}")
            return self._cache[cache_key][0]

        issue = await self.base_repo.get_issue(issue_number)
        if issue:
            self._cache[cache_key] = (issue, datetime.now())

        return issue

    async def get_repository_info(self) -> Repository:
        """Get cached repository info or fetch from API."""
        cache_key = "repository_info"

        if self._is_cache_valid(cache_key):
            self.logger.debug("Returning cached repository info")
            return self._cache[cache_key][0]

        repo_info = await self.base_repo.get_repository_info()
        self._cache[cache_key] = (repo_info, datetime.now())

        return repo_info

    async def get_issue_timeline(self, issue_number: int) -> List[Dict[str, Any]]:
        """Get cached issue timeline or fetch from API."""
        cache_key = f"timeline_{issue_number}"

        if self._is_cache_valid(cache_key):
            self.logger.debug(f"Returning cached timeline for issue #{issue_number}")
            return self._cache[cache_key][0]

        timeline = await self.base_repo.get_issue_timeline(issue_number)
        self._cache[cache_key] = (timeline, datetime.now())

        return timeline

    def _get_cache_key(self, prefix: str, criteria: SearchCriteria) -> str:
        """Generate cache key for search criteria."""
        key_parts = [
            prefix,
            str(criteria.state),
            ",".join(criteria.labels or []),
            criteria.assignee or "",
            criteria.creator or "",
            criteria.milestone or "",
            criteria.since.isoformat() if criteria.since else "",
            criteria.until.isoformat() if criteria.until else "",
            criteria.sort,
            criteria.direction,
        ]
        return "_".join(key_parts)

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is valid."""
        if cache_key not in self._cache:
            return False

        data, timestamp = self._cache[cache_key]
        age = (datetime.now() - timestamp).total_seconds()

        return age < self.cache_ttl

    def clear_cache(self):
        """Clear all cached data."""
        self._cache.clear()
        self.logger.info("Cache cleared")


def create_github_repository() -> GitHubRepositoryInterface:
    """Factory function to create GitHub repository instance."""
    config = get_config()

    base_repo = GitHubRepository(
        owner=config.github.repo_owner,
        repo_name=config.github.repo_name,
        token=config.github.token,
    )

    # Wrap with caching if enabled
    if config.cache.type != "none":
        return CachedGitHubRepository(base_repo, config.cache.ttl)

    return base_repo
