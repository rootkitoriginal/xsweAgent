"""
Fixtures for GitHub integration testing.

Provides pre-configured GitHub mocks and data for testing.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta

from src.github_monitor.models import Issue, IssueState, GitHubUser, IssuePriority, IssueType
from src.github_monitor.repository import GitHubRepository
from src.github_monitor.service import GitHubIssuesService
from tests.utils.mock_github import MockGitHubAPI, create_mock_github_repository


@pytest.fixture
def github_user():
    """Provide standard GitHub user."""
    return GitHubUser(
        id=12345,
        login="test_user",
        name="Test User",
        email="test@example.com"
    )


@pytest.fixture
def github_issue(github_user):
    """Provide single GitHub issue."""
    return Issue(
        id=1,
        number=1,
        title="Test Issue",
        body="This is a test issue",
        state=IssueState.OPEN,
        created_at=datetime.now() - timedelta(days=5),
        updated_at=datetime.now(),
        closed_at=None,
        user=github_user,
        assignee=github_user,
        assignees=[github_user],
        labels=["bug", "priority:high"],
        milestone=None,
        comments=3,
        html_url="https://github.com/test/repo/issues/1",
        priority=IssuePriority.HIGH,
        issue_type=IssueType.BUG
    )


@pytest.fixture
def github_issues_list(github_user):
    """Provide list of GitHub issues."""
    issues = []
    
    for i in range(10):
        state = IssueState.OPEN if i % 3 == 0 else IssueState.CLOSED
        closed_at = datetime.now() - timedelta(days=i) if state == IssueState.CLOSED else None
        
        issue = Issue(
            id=i + 1,
            number=i + 1,
            title=f"Issue {i+1}",
            body=f"Description for issue {i+1}",
            state=state,
            created_at=datetime.now() - timedelta(days=i + 10),
            updated_at=datetime.now() - timedelta(days=i),
            closed_at=closed_at,
            user=github_user,
            assignee=github_user if i % 2 == 0 else None,
            assignees=[github_user] if i % 2 == 0 else [],
            labels=["bug"] if i % 2 == 0 else ["feature"],
            milestone=None,
            comments=i % 5,
            html_url=f"https://github.com/test/repo/issues/{i+1}",
            priority=IssuePriority.MEDIUM,
            issue_type=IssueType.BUG if i % 2 == 0 else IssueType.FEATURE
        )
        issues.append(issue)
    
    return issues


@pytest.fixture
def mock_github_api():
    """Provide configured MockGitHubAPI."""
    api = MockGitHubAPI()
    
    # Add sample issues
    api.add_issue("Bug: Login fails", IssueState.OPEN, created_days_ago=5)
    api.add_issue("Feature: Add dashboard", IssueState.OPEN, created_days_ago=3)
    api.add_issue("Bug: Memory leak", IssueState.CLOSED, created_days_ago=10, closed_days_ago=2)
    api.add_issue("Enhancement: Improve UI", IssueState.CLOSED, created_days_ago=8, closed_days_ago=1)
    
    return api


@pytest.fixture
def mock_github_repository(mock_github_api):
    """Provide mocked GitHub repository."""
    return create_mock_github_repository(num_issues=10, open_ratio=0.6)


@pytest.fixture
def github_repository_with_patch(mock_github_api):
    """Provide GitHub repository with patched API calls."""
    with patch('github.Github') as MockGithub:
        mock_repo = MagicMock()
        mock_repo.get_issues.return_value = mock_github_api.get_issues()
        
        mock_client = MockGithub.return_value
        mock_client.get_repo.return_value = mock_repo
        
        repo = GitHubRepository(repo_name="test/repo", api_token="fake_token")
        yield repo


@pytest.fixture
async def github_issues_service(github_repository_with_patch):
    """Provide GitHub issues service with mocked repository."""
    return GitHubIssuesService(repository=github_repository_with_patch)


@pytest.fixture
def github_api_rate_limit_info():
    """Provide rate limit information."""
    return {
        "remaining": 4500,
        "limit": 5000,
        "reset": datetime.now() + timedelta(hours=1),
        "used": 500
    }


@pytest.fixture
def github_timeline_events():
    """Provide mock timeline events."""
    events = []
    
    event_types = ["commented", "labeled", "assigned", "closed", "reopened"]
    
    for i, event_type in enumerate(event_types):
        event = {
            "event": event_type,
            "created_at": datetime.now() - timedelta(days=i),
            "actor": "test_user",
            "data": {}
        }
        events.append(event)
    
    return events


@pytest.fixture
def github_repository_info():
    """Provide mock repository information."""
    return {
        "id": 12345,
        "name": "test-repo",
        "full_name": "test/test-repo",
        "description": "A test repository",
        "private": False,
        "html_url": "https://github.com/test/test-repo",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "pushed_at": "2024-01-15T00:00:00Z",
        "open_issues_count": 10,
        "forks_count": 5,
        "stargazers_count": 50,
        "watchers_count": 25
    }


@pytest.fixture
def mock_github_client_with_errors():
    """Provide GitHub client that simulates errors."""
    with patch('github.Github') as MockGithub:
        mock_client = MockGithub.return_value
        mock_repo = MagicMock()
        
        # Simulate network error
        mock_repo.get_issues.side_effect = Exception("Network error")
        mock_client.get_repo.return_value = mock_repo
        
        yield mock_client
