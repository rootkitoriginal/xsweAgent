"""
Mock GitHub API utilities for testing.

Provides configurable GitHub API simulator with various response scenarios.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from unittest.mock import MagicMock, AsyncMock
from dataclasses import dataclass

from src.github_monitor.models import Issue, IssueState, GitHubUser, IssuePriority, IssueType


@dataclass
class MockGitHubConfig:
    """Configuration for MockGitHubAPI behavior."""
    
    simulate_rate_limit: bool = False
    simulate_network_error: bool = False
    simulate_auth_error: bool = False
    simulate_slow_response: bool = False
    response_delay_ms: int = 0
    rate_limit_remaining: int = 5000
    rate_limit_reset_in: int = 3600


class MockGitHubAPI:
    """Configurable GitHub API simulator for testing.
    
    Provides realistic GitHub API responses with various scenarios:
    - Normal operation
    - Rate limiting
    - Network errors
    - Authentication failures
    - Slow responses
    
    Example:
        >>> mock_api = MockGitHubAPI()
        >>> mock_api.add_issue("Test Issue", IssueState.OPEN)
        >>> issues = mock_api.get_issues()
    """
    
    def __init__(self, config: Optional[MockGitHubConfig] = None):
        """Initialize mock GitHub API.
        
        Args:
            config: Configuration for mock behavior
        """
        self.config = config or MockGitHubConfig()
        self._issues: List[Issue] = []
        self._issue_counter = 1
        self._call_count = 0
        
    def add_issue(
        self,
        title: str,
        state: IssueState = IssueState.OPEN,
        created_days_ago: int = 0,
        closed_days_ago: Optional[int] = None,
        labels: Optional[List[str]] = None,
        priority: IssuePriority = IssuePriority.MEDIUM,
        issue_type: IssueType = IssueType.BUG,
    ) -> Issue:
        """Add a mock issue to the repository.
        
        Args:
            title: Issue title
            state: Issue state (OPEN or CLOSED)
            created_days_ago: How many days ago the issue was created
            closed_days_ago: How many days ago the issue was closed (if closed)
            labels: List of label names
            priority: Issue priority
            issue_type: Issue type
            
        Returns:
            The created Issue object
        """
        user = GitHubUser(
            id=12345,
            login="test_user",
            name="Test User",
            email="test@example.com"
        )
        
        created_at = datetime.now() - timedelta(days=created_days_ago)
        closed_at = None
        if state == IssueState.CLOSED and closed_days_ago is not None:
            closed_at = datetime.now() - timedelta(days=closed_days_ago)
        
        issue = Issue(
            id=self._issue_counter,
            number=self._issue_counter,
            title=title,
            body=f"Description for {title}",
            state=state,
            created_at=created_at,
            updated_at=datetime.now(),
            closed_at=closed_at,
            user=user,
            assignee=user if self._issue_counter % 2 == 0 else None,
            assignees=[user] if self._issue_counter % 2 == 0 else [],
            labels=labels or [],
            milestone=None,
            comments=self._issue_counter % 5,
            html_url=f"https://github.com/test/repo/issues/{self._issue_counter}",
            priority=priority,
            issue_type=issue_type
        )
        
        self._issues.append(issue)
        self._issue_counter += 1
        return issue
    
    def get_issues(
        self,
        state: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[Issue]:
        """Get issues from the mock repository.
        
        Args:
            state: Filter by state ('open', 'closed', 'all')
            since: Filter issues updated since this date
            
        Returns:
            List of Issue objects
            
        Raises:
            Exception: If rate limit is exceeded or other errors are simulated
        """
        self._call_count += 1
        
        # Simulate various error conditions
        if self.config.simulate_rate_limit and self._call_count > 10:
            raise Exception("API rate limit exceeded")
        
        if self.config.simulate_network_error:
            raise Exception("Network error: Connection refused")
        
        if self.config.simulate_auth_error:
            raise Exception("Bad credentials")
        
        # Filter issues
        issues = self._issues.copy()
        
        if state == "open":
            issues = [i for i in issues if i.state == IssueState.OPEN]
        elif state == "closed":
            issues = [i for i in issues if i.state == IssueState.CLOSED]
        
        if since:
            issues = [i for i in issues if i.updated_at >= since]
        
        return issues
    
    def get_issue(self, issue_number: int) -> Optional[Issue]:
        """Get a specific issue by number.
        
        Args:
            issue_number: Issue number to retrieve
            
        Returns:
            Issue object or None if not found
        """
        for issue in self._issues:
            if issue.number == issue_number:
                return issue
        return None
    
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get rate limit information.
        
        Returns:
            Dictionary with rate limit info
        """
        return {
            "remaining": self.config.rate_limit_remaining - self._call_count,
            "limit": 5000,
            "reset": datetime.now() + timedelta(seconds=self.config.rate_limit_reset_in)
        }
    
    def reset(self):
        """Reset the mock API state."""
        self._issues.clear()
        self._issue_counter = 1
        self._call_count = 0


def create_mock_github_repository(
    num_issues: int = 10,
    open_ratio: float = 0.6,
) -> MagicMock:
    """Create a fully mocked GitHub repository object.
    
    Args:
        num_issues: Number of issues to create
        open_ratio: Ratio of open to total issues (0.0 to 1.0)
        
    Returns:
        MagicMock object configured as a GitHub repository
    """
    mock_api = MockGitHubAPI()
    
    # Create issues with specified open ratio
    num_open = int(num_issues * open_ratio)
    
    for i in range(num_open):
        mock_api.add_issue(
            f"Open Issue {i+1}",
            state=IssueState.OPEN,
            created_days_ago=i
        )
    
    for i in range(num_issues - num_open):
        mock_api.add_issue(
            f"Closed Issue {i+1}",
            state=IssueState.CLOSED,
            created_days_ago=i + 10,
            closed_days_ago=i
        )
    
    # Create mock repository
    mock_repo = MagicMock()
    mock_repo.get_issues = MagicMock(return_value=mock_api.get_issues())
    mock_repo.get_issue = MagicMock(side_effect=mock_api.get_issue)
    
    # Mock repository info
    mock_repo.full_name = "test/repo"
    mock_repo.open_issues_count = num_open
    mock_repo.stargazers_count = 100
    mock_repo.forks_count = 20
    
    return mock_repo


async def create_async_mock_github_repository(
    num_issues: int = 10,
    open_ratio: float = 0.6,
) -> AsyncMock:
    """Create a fully mocked async GitHub repository object.
    
    Args:
        num_issues: Number of issues to create
        open_ratio: Ratio of open to total issues (0.0 to 1.0)
        
    Returns:
        AsyncMock object configured as a GitHub repository
    """
    mock_api = MockGitHubAPI()
    
    # Create issues
    num_open = int(num_issues * open_ratio)
    
    for i in range(num_open):
        mock_api.add_issue(
            f"Open Issue {i+1}",
            state=IssueState.OPEN,
            created_days_ago=i
        )
    
    for i in range(num_issues - num_open):
        mock_api.add_issue(
            f"Closed Issue {i+1}",
            state=IssueState.CLOSED,
            created_days_ago=i + 10,
            closed_days_ago=i
        )
    
    # Create async mock repository
    mock_repo = AsyncMock()
    mock_repo.get_issues = AsyncMock(return_value=mock_api.get_issues())
    mock_repo.get_issue = AsyncMock(side_effect=mock_api.get_issue)
    
    return mock_repo
