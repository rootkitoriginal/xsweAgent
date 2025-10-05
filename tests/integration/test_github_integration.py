"""
Integration tests for GitHub API integration.

Tests the complete GitHub monitoring workflow with mocked API responses.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

from src.github_monitor.repository import GitHubRepository
from src.github_monitor.service import GitHubIssuesService
from src.github_monitor.models import Issue, IssueState
from tests.utils.mock_github import MockGitHubAPI, create_mock_github_repository
from tests.utils.test_data_builder import IssueListBuilder


@pytest.mark.integration
class TestGitHubIntegration:
    """Integration tests for GitHub API workflow."""
    
    @pytest.mark.asyncio
    async def test_fetch_and_process_issues_workflow(self):
        """Test complete workflow of fetching and processing issues."""
        # Setup mock GitHub API
        mock_api = MockGitHubAPI()
        mock_api.add_issue("Bug: Login fails", IssueState.OPEN, created_days_ago=5)
        mock_api.add_issue("Feature: Add search", IssueState.OPEN, created_days_ago=3)
        mock_api.add_issue("Bug: Memory leak", IssueState.CLOSED, created_days_ago=10, closed_days_ago=2)
        
        with patch('github.Github') as MockGithub:
            mock_repo = MagicMock()
            mock_repo.get_issues.return_value = mock_api.get_issues()
            
            mock_client = MockGithub.return_value
            mock_client.get_repo.return_value = mock_repo
            
            # Test repository layer
            repo = GitHubRepository(repo_name="test/repo", api_token="fake_token")
            issues = repo.get_issues()
            
            assert len(issues) == 3
            assert isinstance(issues[0], Issue)
            
            # Verify issue properties
            open_issues = [i for i in issues if i.state == IssueState.OPEN]
            closed_issues = [i for i in issues if i.state == IssueState.CLOSED]
            
            assert len(open_issues) == 2
            assert len(closed_issues) == 1
    
    @pytest.mark.asyncio
    async def test_issue_filtering_and_search(self):
        """Test issue filtering by various criteria."""
        mock_api = MockGitHubAPI()
        
        # Create issues with different states and dates
        for i in range(5):
            mock_api.add_issue(
                f"Open Issue {i}",
                IssueState.OPEN,
                created_days_ago=i
            )
        
        for i in range(3):
            mock_api.add_issue(
                f"Closed Issue {i}",
                IssueState.CLOSED,
                created_days_ago=i + 10,
                closed_days_ago=i
            )
        
        with patch('github.Github') as MockGithub:
            mock_repo = MagicMock()
            mock_repo.get_issues.return_value = mock_api.get_issues()
            
            mock_client = MockGithub.return_value
            mock_client.get_repo.return_value = mock_repo
            
            repo = GitHubRepository(repo_name="test/repo", api_token="fake_token")
            
            # Test filtering issues
            all_issues = repo.get_issues()
            open_issues = [i for i in all_issues if i.state == IssueState.OPEN]
            closed_issues = [i for i in all_issues if i.state == IssueState.CLOSED]
            
            assert len(open_issues) == 5
            assert len(closed_issues) == 3
    
    @pytest.mark.asyncio
    async def test_issue_timeline_retrieval(self):
        """Test retrieving issue timeline events."""
        with patch('github.Github') as MockGithub:
            # Create mock timeline events
            mock_events = []
            for i in range(3):
                event = MagicMock()
                event.event = "commented" if i % 2 == 0 else "labeled"
                event.created_at = datetime.now() - timedelta(days=i)
                mock_events.append(event)
            
            mock_issue = MagicMock()
            mock_issue.get_timeline.return_value = mock_events
            
            mock_repo = MagicMock()
            mock_repo.get_issue.return_value = mock_issue
            
            mock_client = MockGithub.return_value
            mock_client.get_repo.return_value = mock_repo
            
            repo = GitHubRepository(repo_name="test/repo", api_token="fake_token")
            timeline = await repo.get_issue_timeline(1)
            
            assert len(timeline) == 3
            assert timeline[0]["event"] in ["commented", "labeled"]
    
    @pytest.mark.asyncio
    async def test_repository_info_retrieval(self):
        """Test retrieving repository information."""
        with patch('github.Github') as MockGithub:
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
            
            mock_client = MockGithub.return_value
            mock_client.get_repo.return_value = mock_repo
            
            repo = GitHubRepository(repo_name="test/repo", api_token="fake_token")
            repo_info = await repo.get_repository_info()
            
            assert repo_info is not None
            assert repo_info.full_name == "test/test-repo"
            assert repo_info.open_issues_count == 10
            assert repo_info.stargazers_count == 50
    
    @pytest.mark.asyncio
    async def test_error_handling_network_failure(self):
        """Test error handling when network fails."""
        with patch('github.Github') as MockGithub:
            mock_repo = MagicMock()
            mock_repo.get_issues.side_effect = Exception("Network error")
            
            mock_client = MockGithub.return_value
            mock_client.get_repo.return_value = mock_repo
            
            repo = GitHubRepository(repo_name="test/repo", api_token="fake_token")
            
            # Should return empty list instead of raising
            issues = repo.get_issues()
            assert issues == []
    
    @pytest.mark.asyncio
    async def test_error_handling_auth_failure(self):
        """Test error handling when authentication fails."""
        with patch('github.Github') as MockGithub:
            mock_client = MockGithub.return_value
            mock_client.get_repo.side_effect = Exception("Bad credentials")
            
            repo = GitHubRepository(repo_name="test/repo", api_token="bad_token")
            
            # Should handle auth error gracefully
            issues = repo.get_issues()
            assert issues == []
    
    @pytest.mark.asyncio
    async def test_issue_summary_generation(self):
        """Test generating summary of issues."""
        mock_api = MockGitHubAPI()
        
        # Create diverse set of issues
        for i in range(10):
            state = IssueState.OPEN if i % 3 == 0 else IssueState.CLOSED
            mock_api.add_issue(
                f"Issue {i}",
                state=state,
                created_days_ago=i,
                closed_days_ago=i // 2 if state == IssueState.CLOSED else None
            )
        
        with patch('github.Github') as MockGithub:
            mock_repo = MagicMock()
            mock_repo.get_issues.return_value = mock_api.get_issues()
            
            mock_client = MockGithub.return_value
            mock_client.get_repo.return_value = mock_repo
            
            repo = GitHubRepository(repo_name="test/repo", api_token="fake_token")
            issues = repo.get_issues()
            
            # Calculate summary from issues
            total = len(issues)
            open_count = sum(1 for i in issues if i.state == IssueState.OPEN)
            closed_count = sum(1 for i in issues if i.state == IssueState.CLOSED)
            
            assert total == 10
            assert open_count + closed_count == total
    
    @pytest.mark.asyncio
    async def test_rate_limit_handling(self):
        """Test handling of GitHub API rate limits."""
        mock_api = MockGitHubAPI()
        mock_api.config.simulate_rate_limit = True
        
        # Add issues that will trigger rate limit
        for i in range(15):
            mock_api.add_issue(f"Issue {i}", IssueState.OPEN)
        
        with patch('github.Github') as MockGithub:
            mock_repo = MagicMock()
            
            # First call succeeds
            mock_repo.get_issues.return_value = mock_api.get_issues()
            
            mock_client = MockGithub.return_value
            mock_client.get_repo.return_value = mock_repo
            
            repo = GitHubRepository(repo_name="test/repo", api_token="fake_token")
            
            # Multiple calls should be handled
            for _ in range(3):
                issues = repo.get_issues()
                # Should either return issues or empty list, but not crash
                assert isinstance(issues, list)
