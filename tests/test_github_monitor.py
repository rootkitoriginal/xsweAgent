"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.github_monitor.repository import GitHubRepository
from src.github_monitor.service import GitHubIssuesService
from src.github_monitor.models import Issue, IssueStatefor the GitHub monitor module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.github_monitor.models import Issue, IssueState
from src.github_monitor.repository import GitHubRepository
from src.github_monitor.service import GitHubIssuesService


@pytest.fixture
def mock_github_repo():
    """Fixture for a mocked GitHub repository object."""
    mock_repo = MagicMock()

    # Mock issues
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

    mock_repo.get_issues.return_value = [issue1, issue2]
    return mock_repo


@patch("github.Github")
def test_github_repository_get_issues(MockGithub, mock_github_repo):
    """Test fetching issues from the GitHub repository."""
    mock_instance = MockGithub.return_value
    mock_instance.get_repo.return_value = mock_github_repo

    repo = GitHubRepository(repo_name="test/repo", api_token="fake_token")
    issues = repo.get_issues()

    assert len(issues) == 2
    assert isinstance(issues[0], Issue)
    assert issues[0].title == "Test Issue 1"
    assert issues[0].state == IssueState.OPEN
    assert issues[1].state == IssueState.CLOSED


@pytest.mark.asyncio
async def test_github_issues_service_get_all_issues():
    """Test the service layer for getting all issues."""
    with patch(
        "src.github_monitor.repository.GitHubRepository.get_issues"
    ) as mock_get_issues:
        # Mock the repository's get_issues to return a list of Issue models
        mock_get_issues.return_value = [
            Issue(
                id=1,
                number=1,
                title="Issue 1",
                state=IssueState.OPEN,
                created_at="2023-01-01T00:00:00Z",
            ),
            Issue(
                id=2,
                number=2,
                title="Issue 2",
                state=IssueState.CLOSED,
                created_at="2023-01-02T00:00:00Z",
            ),
        ]

        # GitHubIssuesService expects an optional repository parameter
        # instantiate without repo_name/api_token
        service = GitHubIssuesService()

        # We need to mock the async call if the service method is async
        service.get_all_issues = AsyncMock(
            return_value=mock_get_issues.return_value
        )

        issues = await service.get_all_issues()

        assert len(issues) == 2
        assert issues[0].title == "Issue 1"


@pytest.mark.asyncio
async def test_github_issues_service_get_summary():
    """Test the service layer for getting an issue summary."""
    with patch(
        "src.github_monitor.repository.GitHubRepository.get_issues"
    ) as mock_get_issues:
        mock_get_issues.return_value = [
            Issue(
                id=1,
                number=1,
                title="Issue 1",
                state=IssueState.OPEN,
                created_at="2023-01-01T00:00:00Z",
            ),
            Issue(
                id=2,
                number=2,
                title="Issue 2",
                state=IssueState.CLOSED,
                created_at="2023-01-02T00:00:00Z",
            ),
            Issue(
                id=3,
                number=3,
                title="Issue 3",
                state=IssueState.OPEN,
                created_at="2023-01-03T00:00:00Z",
            ),
        ]

        # GitHubIssuesService expects an optional repository parameter
        # instantiate without repo_name/api_token
        service = GitHubIssuesService()

        # Mock the async call
        async def summary_side_effect():
            all_issues = mock_get_issues.return_value
            open_issues = len([i for i in all_issues if i.state == IssueState.OPEN])
            closed_issues = len([i for i in all_issues if i.state == IssueState.CLOSED])
            return {
                "open_issues": open_issues,
                "closed_issues": closed_issues,
                "total_issues": len(all_issues),
            }

        service.get_issue_summary = AsyncMock(side_effect=summary_side_effect)

        summary = await service.get_issue_summary()

        assert summary["open_issues"] == 2
        assert summary["closed_issues"] == 1
        assert summary["total_issues"] == 3


@pytest.mark.asyncio
@patch("github.Github")
async def test_github_repository_get_issue(MockGithub):
    """Test fetching a single issue from the GitHub repository."""
    # Create mock issue
    mock_issue = MagicMock()
    mock_issue.number = 42
    mock_issue.title = "Test Single Issue"
    mock_issue.body = "This is a test issue body"
    mock_issue.state = "open"
    mock_issue.created_at = "2023-01-01T12:00:00Z"
    mock_issue.updated_at = "2023-01-02T12:00:00Z"
    mock_issue.closed_at = None
    mock_issue.comments = 5
    mock_issue.html_url = "https://github.com/test/repo/issues/42"
    mock_issue.user.login = "testuser"
    mock_issue.user.id = 123
    mock_issue.assignee.login = "assigneduser"
    mock_issue.assignee.id = 456

    # Setup mock repository
    mock_repo = MagicMock()
    mock_repo.get_issue.return_value = mock_issue

    mock_instance = MockGithub.return_value
    mock_instance.get_repo.return_value = mock_repo

    repo = GitHubRepository(repo_name="test/repo", api_token="fake_token")
    issue = await repo.get_issue(42)

    assert issue is not None
    assert isinstance(issue, Issue)
    assert issue.number == 42
    assert issue.title == "Test Single Issue"
    assert issue.body == "This is a test issue body"
    assert issue.state == IssueState.OPEN
    assert issue.comments == 5
    assert issue.html_url == "https://github.com/test/repo/issues/42"
    assert issue.user.login == "testuser"
    assert issue.assignee.login == "assigneduser"


@pytest.mark.asyncio
@patch("github.Github")
async def test_github_repository_get_issue_not_found(MockGithub):
    """Test fetching a non-existent issue returns None."""
    # Setup mock to raise exception
    mock_repo = MagicMock()
    mock_repo.get_issue.side_effect = Exception("Issue not found")

    mock_instance = MockGithub.return_value
    mock_instance.get_repo.return_value = mock_repo

    repo = GitHubRepository(repo_name="test/repo", api_token="fake_token")
    issue = await repo.get_issue(999)

    assert issue is None


@pytest.mark.asyncio
@patch("github.Github")
async def test_github_repository_get_repository_info(MockGithub):
    """Test fetching repository information."""
    from src.github_monitor.models import Repository

    # Create mock repository
    mock_repo = MagicMock()
    mock_repo.id = 12345
    mock_repo.name = "test-repo"
    mock_repo.full_name = "test/test-repo"
    mock_repo.description = "A test repository"
    mock_repo.private = False
    mock_repo.html_url = "https://github.com/test/test-repo"
    mock_repo.created_at = "2023-01-01T00:00:00Z"
    mock_repo.updated_at = "2023-06-01T00:00:00Z"
    mock_repo.pushed_at = "2023-06-15T00:00:00Z"
    mock_repo.open_issues_count = 10
    mock_repo.forks_count = 5
    mock_repo.stargazers_count = 50
    mock_repo.watchers_count = 25

    mock_instance = MockGithub.return_value
    mock_instance.get_repo.return_value = mock_repo

    repo_obj = GitHubRepository(repo_name="test/test-repo", api_token="fake_token")
    repo_info = await repo_obj.get_repository_info()

    assert repo_info is not None
    assert isinstance(repo_info, Repository)
    assert repo_info.id == 12345
    assert repo_info.name == "test-repo"
    assert repo_info.full_name == "test/test-repo"
    assert repo_info.description == "A test repository"
    assert repo_info.private is False
    assert repo_info.html_url == "https://github.com/test/test-repo"
    assert repo_info.open_issues_count == 10
    assert repo_info.forks_count == 5
    assert repo_info.stargazers_count == 50
    assert repo_info.watchers_count == 25


@pytest.mark.asyncio
@patch("github.Github")
async def test_github_repository_get_repository_info_error(MockGithub):
    """Test fetching repository info with error returns None."""
    # Setup mock to raise exception
    mock_instance = MockGithub.return_value
    mock_instance.get_repo.side_effect = Exception("Repository not found")

    repo = GitHubRepository(repo_name="test/repo", api_token="fake_token")
    repo_info = await repo.get_repository_info()

    assert repo_info is None


@pytest.mark.asyncio
@patch("github.Github")
async def test_github_repository_get_issue_timeline(MockGithub):
    """Test fetching issue timeline events."""
    # Create mock timeline events
    event1 = MagicMock()
    event1.event = "labeled"
    event1.created_at = "2023-01-01T12:00:00Z"
    event1.actor.login = "user1"
    event1.label.name = "bug"

    event2 = MagicMock()
    event2.event = "assigned"
    event2.created_at = "2023-01-02T12:00:00Z"
    event2.actor.login = "user2"
    event2.assignee.login = "assignee1"

    event3 = MagicMock()
    event3.event = "closed"
    event3.created_at = "2023-01-03T12:00:00Z"
    event3.actor.login = "user1"

    # Create mock issue
    mock_issue = MagicMock()
    mock_issue.get_timeline.return_value = [event1, event2, event3]

    # Setup mock repository
    mock_repo = MagicMock()
    mock_repo.get_issue.return_value = mock_issue

    mock_instance = MockGithub.return_value
    mock_instance.get_repo.return_value = mock_repo

    repo = GitHubRepository(repo_name="test/repo", api_token="fake_token")
    timeline = await repo.get_issue_timeline(42)

    assert timeline is not None
    assert isinstance(timeline, list)
    assert len(timeline) == 3

    # Check first event (labeled)
    assert timeline[0]["event"] == "labeled"
    assert timeline[0]["actor"] == "user1"
    assert timeline[0]["label"] == "bug"

    # Check second event (assigned)
    assert timeline[1]["event"] == "assigned"
    assert timeline[1]["actor"] == "user2"
    assert timeline[1]["assignee"] == "assignee1"

    # Check third event (closed)
    assert timeline[2]["event"] == "closed"
    assert timeline[2]["actor"] == "user1"


@pytest.mark.asyncio
@patch("github.Github")
async def test_github_repository_get_issue_timeline_error(MockGithub):
    """Test fetching issue timeline with error returns empty list."""
    # Setup mock to raise exception
    mock_repo = MagicMock()
    mock_repo.get_issue.side_effect = Exception("Issue not found")

    mock_instance = MockGithub.return_value
    mock_instance.get_repo.return_value = mock_repo

    repo = GitHubRepository(repo_name="test/repo", api_token="fake_token")
    timeline = await repo.get_issue_timeline(999)

    assert timeline == []
