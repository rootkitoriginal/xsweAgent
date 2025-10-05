"""
Test fixtures and configuration for xSwE Agent.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
from datetime import datetime, timedelta
import asyncio
import os

# Set test environment
os.environ["TESTING"] = "true"
os.environ["LOG_LEVEL"] = "ERROR"

from src.config import get_config
from src.github_monitor.models import Issue, GitHubUser, IssueState, IssuePriority, IssueType
from src.gemini_integration.models import CodeSnippet, AnalysisResult


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_config():
    """Provide test configuration."""
    return get_config()


# ========================================
# GitHub API Mocks and Fixtures
# ========================================

@pytest.fixture
def mock_github_user():
    """Mock GitHub user."""
    return GitHubUser(
        id=123456,
        login="test_user",
        name="Test User",
        email="test@example.com"
    )


@pytest.fixture
def mock_github_issue(mock_github_user):
    """Mock GitHub issue."""
    return Issue(
        id=1,
        number=1,
        title="Test Issue",
        body="Test issue description",
        state=IssueState.OPEN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        user=mock_github_user,
        assignee=mock_github_user,
        assignees=[mock_github_user],
        labels=[],
        milestone=None,
        comments=0,
        html_url="https://github.com/owner/repo/issues/1",
        priority=IssuePriority.MEDIUM,
        issue_type=IssueType.BUG
    )


@pytest.fixture
def mock_issues_list(mock_github_issue):
    """Mock list of GitHub issues."""
    issues = []
    for i in range(5):
        issue = mock_github_issue.__class__(
            **{**mock_github_issue.__dict__, 
               'id': i+1, 
               'number': i+1,
               'title': f"Test Issue {i+1}"}
        )
        issues.append(issue)
    return issues


@pytest.fixture
def mock_github_repository():
    """Mock GitHub repository with common methods."""
    repo = MagicMock()
    
    # Mock async methods
    repo.get_issues = AsyncMock()
    repo.get_issue = AsyncMock()
    repo.get_repository_info = AsyncMock()
    repo.get_issue_timeline = AsyncMock()
    
    # Mock repository info
    repo_info = MagicMock()
    repo_info.full_name = "owner/repo"
    repo_info.open_issues_count = 10
    repo_info.stargazers_count = 100
    repo_info.forks_count = 20
    repo.get_repository_info.return_value = repo_info
    
    return repo


@pytest.fixture
def mock_github_api():
    """Mock entire GitHub API responses."""
    with patch('github.Github') as mock_github:
        mock_client = MagicMock()
        mock_repo = MagicMock()
        
        # Setup chain: Github() -> get_repo() -> get_issues()
        mock_github.return_value = mock_client
        mock_client.get_repo.return_value = mock_repo
        
        # Mock issues data
        mock_issues_data = []
        for i in range(3):
            mock_issue = MagicMock()
            mock_issue.number = i + 1
            mock_issue.title = f"Test Issue {i+1}"
            mock_issue.body = f"Description {i+1}"
            mock_issue.state = "open"
            mock_issue.created_at = datetime.now() - timedelta(days=i)
            mock_issue.updated_at = datetime.now()
            mock_issue.closed_at = None
            mock_issue.user.login = "test_user"
            mock_issue.assignee = None
            mock_issue.assignees = []
            mock_issue.labels = []
            mock_issue.milestone = None
            mock_issue.comments = 0
            mock_issue.html_url = f"https://github.com/owner/repo/issues/{i+1}"
            mock_issues_data.append(mock_issue)
        
        mock_repo.get_issues.return_value = mock_issues_data
        yield mock_github


# ========================================
# Gemini API Mocks and Fixtures  
# ========================================

@pytest.fixture
def mock_code_snippet():
    """Mock code snippet for analysis."""
    return CodeSnippet(
        content='''
def calculate_metrics(issues):
    """Calculate basic metrics from issues."""
    if not issues:
        return {}

    total = len(issues)
    open_issues = sum(1 for i in issues if i.state == "open")

    return {
        "total": total,
        "open": open_issues,
        "closed": total - open_issues
    }
        '''.strip(),
        language="python",
        filename="src/analytics/metrics.py"
    )
@pytest.fixture
def mock_analysis_result():
    """Mock Gemini analysis result."""
    return AnalysisResult(
        quality_score=85.0,
        suggestions=["Add type hints", "Improve error handling"],
        issues_found=["Missing docstring tests"],
        complexity_score=3.2,
        maintainability="GOOD",
        summary="Well structured function with room for improvement"
    )


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini API client."""
    client = MagicMock()
    client.analyze_code = AsyncMock()
    client.generate_content = AsyncMock()
    
    # Mock successful responses
    mock_response = MagicMock()
    mock_response.text = '''
    {
        "quality_score": 85.0,
        "suggestions": ["Add type hints", "Improve error handling"],
        "issues_found": ["Missing docstring tests"],
        "complexity_score": 3.2,
        "maintainability": "GOOD",
        "summary": "Well structured function with room for improvement"
    }
    '''
    client.generate_content.return_value = mock_response
    
    return client


@pytest.fixture
def mock_gemini_api():
    """Mock Gemini API completely."""
    with patch('google.generativeai.configure'), \
         patch('google.generativeai.GenerativeModel') as mock_model:
        
        mock_instance = MagicMock()
        mock_model.return_value = mock_instance
        
        # Mock generate_content method
        mock_response = MagicMock()
        mock_response.text = '''
        Quality Score: 85/100
        
        Suggestions:
        1. Add type hints for better code clarity
        2. Implement proper error handling
        
        Issues Found:
        - Missing docstring in helper function
        
        Overall: Good code structure with room for improvement.
        '''
        mock_instance.generate_content.return_value = mock_response
        
        yield mock_model


# ========================================
# Analytics and Charts Fixtures
# ========================================

@pytest.fixture
def mock_analytics_result():
    """Mock analytics calculation result."""
    return {
        "productivity_metrics": {
            "avg_resolution_time": 3.5,  # days
            "throughput": 2.3,  # issues per day
            "velocity": 15,  # story points per sprint
        },
        "issue_status_metrics": {
            "total_issues": 50,
            "open_issues": 15,
            "closed_issues": 35,
            "open_rate": 0.3,
            "close_rate": 0.7
        },
        "trends": {
            "weekly_opened": [5, 3, 7, 4, 6],
            "weekly_closed": [4, 5, 6, 3, 7]
        }
    }


@pytest.fixture
def mock_chart_data():
    """Mock data for chart generation."""
    return {
        "labels": ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"],
        "opened": [5, 3, 7, 4, 6],
        "closed": [4, 5, 6, 3, 7],
        "cumulative": [1, -1, 0, 1, 0]
    }


# ========================================
# Database and Cache Fixtures
# ========================================

@pytest.fixture
def mock_cache():
    """Mock cache implementation."""
    cache_data = {}
    
    class MockCache:
        async def get(self, key: str):
            return cache_data.get(key)
        
        async def set(self, key: str, value: Any, ttl: int = 300):
            cache_data[key] = value
        
        async def delete(self, key: str):
            cache_data.pop(key, None)
        
        async def clear(self):
            cache_data.clear()
    
    return MockCache()


# ========================================
# HTTP and Network Fixtures
# ========================================

@pytest.fixture
def mock_http_session():
    """Mock HTTP session for external API calls."""
    session = MagicMock()
    
    # Mock successful response
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"status": "success"}
    response.text = '{"status": "success"}'
    
    session.get.return_value = response
    session.post.return_value = response
    
    return session


# ========================================
# Test Utilities
# ========================================

class TestHelpers:
    """Utility class for common test operations."""
    
    @staticmethod
    def create_mock_issues(count: int = 5) -> List[Issue]:
        """Create a list of mock issues."""
        issues = []
        for i in range(count):
            user = GitHubUser(
                id=i+100, 
                login=f"user_{i}", 
                name=f"User {i}",
                email=f"user{i}@example.com"
            )
            
            issue = Issue(
                id=i+1,
                number=i+1,
                title=f"Issue {i+1}",
                body=f"Description for issue {i+1}",
                state=IssueState.OPEN if i % 2 == 0 else IssueState.CLOSED,
                created_at=datetime.now() - timedelta(days=i),
                updated_at=datetime.now(),
                closed_at=datetime.now() if i % 2 == 1 else None,
                user=user,
                assignee=user if i % 3 == 0 else None,
                assignees=[user] if i % 3 == 0 else [],
                labels=[],
                milestone=None,
                comments=i,
                html_url=f"https://github.com/test/repo/issues/{i+1}",
                priority=IssuePriority.MEDIUM,
                issue_type=IssueType.BUG if i % 2 == 0 else IssueType.FEATURE
            )
            issues.append(issue)
        
        return issues
    
    @staticmethod
    def assert_metrics_structure(metrics: Dict[str, Any]):
        """Assert that metrics have expected structure."""
        assert isinstance(metrics, dict)
        assert "total_issues" in metrics
        assert "open_issues" in metrics
        assert "closed_issues" in metrics
        assert isinstance(metrics["total_issues"], int)
        assert isinstance(metrics["open_issues"], int)
        assert isinstance(metrics["closed_issues"], int)


@pytest.fixture
def test_helpers():
    """Provide test helper utilities."""
    return TestHelpers


# ========================================
# Parametrized Test Data
# ========================================

@pytest.fixture(params=[
    {"state": "open", "count": 5},
    {"state": "closed", "count": 3},
    {"state": "all", "count": 8}
])
def issue_state_scenarios(request):
    """Parametrized fixture for different issue state scenarios."""
    return request.param


@pytest.fixture(params=[
    {"days": 7, "expected_recent": 2},
    {"days": 30, "expected_recent": 5}, 
    {"days": 90, "expected_recent": 8}
])
def time_period_scenarios(request):
    """Parametrized fixture for different time period scenarios."""
    return request.param