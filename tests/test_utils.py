"""
Enhanced test utilities for the xSwE Agent project.
Provides helpers for mocking, data generation, and common assertions.
"""
import pytest
import asyncio
from typing import Dict, Any, List, Optional
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta
import json
import tempfile
import os

from src.github_monitor.models import Issue, GitHubUser, IssueState, IssuePriority, IssueType


class MockDataGenerator:
    """Generate realistic test data for various scenarios."""
    
    @staticmethod
    def github_issues(
        count: int = 10,
        state_distribution: Optional[Dict[str, float]] = None,
        date_range_days: int = 30
    ) -> List[Issue]:
        """
        Generate realistic GitHub issues with proper distribution.
        
        Args:
            count: Number of issues to generate
            state_distribution: {'open': 0.6, 'closed': 0.4} 
            date_range_days: Spread creation dates over N days
        """
        if state_distribution is None:
            state_distribution = {'open': 0.6, 'closed': 0.4}
        
        issues = []
        open_count = int(count * state_distribution['open'])
        
        for i in range(count):
            # Determine state
            state = IssueState.OPEN if i < open_count else IssueState.CLOSED
            
            # Generate realistic dates
            created_days_ago = (i / count) * date_range_days
            created_at = datetime.now() - timedelta(days=created_days_ago)
            
            # Updated within last few days
            updated_at = created_at + timedelta(
                days=min(created_days_ago * 0.8, date_range_days * 0.9)
            )
            
            # Closed date for closed issues
            closed_at = None
            if state == IssueState.CLOSED:
                closed_at = updated_at - timedelta(days=1)
            
            # Generate user
            user = GitHubUser(
                id=1000 + i,
                login=f"user_{i:02d}",
                name=f"Test User {i}",
                email=f"user{i}@example.com"
            )
            
            # Assignee (60% chance)
            assignee = user if i % 5 < 3 else None
            assignees = [assignee] if assignee else []
            
            # Issue type distribution
            issue_types = [IssueType.BUG, IssueType.FEATURE, IssueType.ENHANCEMENT, IssueType.DOCUMENTATION]
            issue_type = issue_types[i % len(issue_types)]
            
            # Priority distribution (bell curve)
            if i % 10 < 1:
                priority = IssuePriority.CRITICAL
            elif i % 10 < 3:
                priority = IssuePriority.HIGH
            elif i % 10 < 7:
                priority = IssuePriority.MEDIUM
            else:
                priority = IssuePriority.LOW
            
            issue = Issue(
                id=i + 1,
                number=i + 1,
                title=f"Issue #{i+1}: {issue_type.value.title()} - Priority {priority.value}",
                body=f"Detailed description for issue {i+1}. This is a {issue_type.value} issue with {priority.value} priority.",
                state=state,
                created_at=created_at,
                updated_at=updated_at,
                closed_at=closed_at,
                user=user,
                assignee=assignee,
                assignees=assignees,
                labels=[],
                milestone=None,
                comments=i % 15,  # 0-14 comments
                html_url=f"https://github.com/test/repo/issues/{i+1}",
                priority=priority,
                issue_type=issue_type
            )
            
            issues.append(issue)
        
        return issues
    
    @staticmethod
    def analytics_metrics() -> Dict[str, Any]:
        """Generate realistic analytics metrics."""
        return {
            "productivity_metrics": {
                "avg_resolution_time": 4.2,
                "throughput": 2.8,
                "velocity": 18,
                "cycle_time": 3.1,
                "lead_time": 5.7
            },
            "quality_metrics": {
                "bug_rate": 0.15,
                "rework_rate": 0.08,
                "customer_satisfaction": 4.2,
                "defect_density": 2.3
            },
            "team_metrics": {
                "active_contributors": 8,
                "avg_commits_per_day": 15.3,
                "code_review_time": 1.8,
                "deployment_frequency": 0.9
            }
        }
    
    @staticmethod
    def time_series_data(days: int = 30) -> Dict[str, List]:
        """Generate time series data for charts."""
        dates = []
        opened = []
        closed = []
        
        for i in range(days):
            date = datetime.now() - timedelta(days=days-i-1)
            dates.append(date.strftime('%Y-%m-%d'))
            
            # Simulate realistic patterns
            day_of_week = date.weekday()
            
            # Less activity on weekends
            weekend_factor = 0.3 if day_of_week >= 5 else 1.0
            
            # Base activity with some randomness
            base_opened = 3 + (i % 7) * weekend_factor
            base_closed = 2 + ((i + 3) % 6) * weekend_factor
            
            opened.append(int(base_opened))
            closed.append(int(base_closed))
        
        return {
            "dates": dates,
            "opened": opened,
            "closed": closed,
            "cumulative": [o - c for o, c in zip(opened, closed)]
        }


class MockAsyncContext:
    """Helper for mocking async context managers."""
    
    def __init__(self, return_value=None):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class APIResponseMocker:
    """Mock external API responses with realistic scenarios."""
    
    @staticmethod
    def github_api_success(issues_count: int = 10):
        """Mock successful GitHub API response."""
        return {
            "status_code": 200,
            "json_data": {
                "total_count": issues_count,
                "items": [
                    {
                        "id": i + 1,
                        "number": i + 1,
                        "title": f"Test Issue {i + 1}",
                        "body": f"Description {i + 1}",
                        "state": "open" if i % 2 == 0 else "closed",
                        "created_at": (datetime.now() - timedelta(days=i)).isoformat(),
                        "updated_at": datetime.now().isoformat(),
                        "user": {"login": "test_user", "id": 12345},
                        "assignee": None,
                        "labels": [],
                        "milestone": None,
                        "comments": i % 5,
                        "html_url": f"https://github.com/test/repo/issues/{i + 1}"
                    }
                    for i in range(issues_count)
                ]
            }
        }
    
    @staticmethod
    def github_api_rate_limit():
        """Mock GitHub API rate limit response."""
        return {
            "status_code": 403,
            "json_data": {
                "message": "API rate limit exceeded",
                "documentation_url": "https://docs.github.com/rest/overview/resources-in-the-rest-api#rate-limiting"
            },
            "headers": {
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int((datetime.now() + timedelta(hours=1)).timestamp()))
            }
        }
    
    @staticmethod
    def gemini_api_success():
        """Mock successful Gemini API response."""
        return {
            "status_code": 200,
            "response_text": """
            Quality Assessment: 8.5/10
            
            **Strengths:**
            - Clean, readable code structure
            - Proper error handling implementation
            - Good documentation coverage
            
            **Areas for Improvement:**
            - Add type hints for better IDE support
            - Consider using dataclasses for data structures
            - Implement more comprehensive logging
            
            **Security Considerations:**
            - No security issues detected
            - Input validation is appropriate
            
            **Performance Notes:**
            - Algorithm complexity is acceptable O(n)
            - Memory usage is efficient
            
            **Maintainability:** HIGH
            **Complexity Score:** 3.2/10
            """
        }
    
    @staticmethod
    def gemini_api_error():
        """Mock Gemini API error response."""
        return {
            "status_code": 400,
            "error_message": "Invalid request: prompt too long"
        }


class TestFileManager:
    """Manage temporary files and directories for tests."""
    
    def __init__(self):
        self.temp_files = []
        self.temp_dirs = []
    
    def create_temp_file(self, content: str, suffix: str = ".json") -> str:
        """Create temporary file with content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        self.temp_files.append(temp_path)
        return temp_path
    
    def create_temp_dir(self) -> str:
        """Create temporary directory."""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def cleanup(self):
        """Clean up all temporary files and directories."""
        for file_path in self.temp_files:
            try:
                os.unlink(file_path)
            except FileNotFoundError:
                pass
        
        import shutil
        for dir_path in self.temp_dirs:
            try:
                shutil.rmtree(dir_path)
            except FileNotFoundError:
                pass
        
        self.temp_files.clear()
        self.temp_dirs.clear()


# Test assertion helpers
class AssertionHelpers:
    """Common assertion patterns for xSwE Agent tests."""
    
    @staticmethod
    def assert_issue_structure(issue: Issue):
        """Assert issue has proper structure."""
        assert isinstance(issue, Issue)
        assert hasattr(issue, 'id')
        assert hasattr(issue, 'number')
        assert hasattr(issue, 'title')
        assert hasattr(issue, 'state')
        assert hasattr(issue, 'created_at')
        assert issue.id is not None
        assert issue.number is not None
        assert issue.title is not None
        assert isinstance(issue.state, IssueState)
    
    @staticmethod
    def assert_analytics_result(result: Dict[str, Any]):
        """Assert analytics result has expected structure."""
        assert isinstance(result, dict)
        
        # Check for required top-level keys
        required_keys = ['productivity_metrics', 'issue_metrics', 'trends']
        for key in required_keys:
            if key in result:
                assert isinstance(result[key], dict)
    
    @staticmethod
    def assert_chart_data(data: Dict[str, Any]):
        """Assert chart data has proper structure."""
        assert isinstance(data, dict)
        assert 'labels' in data
        assert 'data' in data or 'datasets' in data
        assert isinstance(data['labels'], list)
    
    @staticmethod
    def assert_api_response_structure(response: Dict[str, Any]):
        """Assert API response has proper structure."""
        assert isinstance(response, dict)
        assert 'status' in response or 'success' in response
        assert 'data' in response or 'error' in response


# Performance testing helpers
class PerformanceHelpers:
    """Helpers for performance and load testing."""
    
    @staticmethod
    async def measure_execution_time(coro):
        """Measure coroutine execution time."""
        start = datetime.now()
        result = await coro
        end = datetime.now()
        execution_time = (end - start).total_seconds()
        return result, execution_time
    
    @staticmethod
    def create_large_dataset(size: int) -> List[Dict[str, Any]]:
        """Create large dataset for performance testing."""
        return [
            {
                "id": i,
                "data": f"test_data_{i}" * 100,  # Make it substantial
                "timestamp": datetime.now().isoformat(),
                "nested": {"key": f"value_{i}", "list": list(range(10))}
            }
            for i in range(size)
        ]


# Export main classes for easy import
__all__ = [
    'MockDataGenerator',
    'MockAsyncContext', 
    'APIResponseMocker',
    'TestFileManager',
    'AssertionHelpers',
    'PerformanceHelpers'
]