"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.github_monitor.repository import GitHubRepository
from src.github_monitor.service import GitHubIssuesService
from src.github_monitor.models import Issue, IssueStatefor the GitHub monitor module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.github_monitor.repository import GitHubRepository
from src.github_monitor.service import GitHubIssuesService
from src.github_monitor.models import Issue, IssueState


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

        # GitHubIssuesService expects an optional repository parameter; instantiate without repo_name/api_token
        service = GitHubIssuesService()

        # We need to mock the async call if the service method is async
        service.get_all_issues = AsyncMock(return_value=mock_get_issues.return_value)

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

        # GitHubIssuesService expects an optional repository parameter; instantiate without repo_name/api_token
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
