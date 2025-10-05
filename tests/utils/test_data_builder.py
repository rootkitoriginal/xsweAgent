"""
Test data builders for consistent test data generation.

Provides fluent builders for creating test data objects.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass

from src.github_monitor.models import (
    Issue,
    IssueState,
    GitHubUser,
    IssuePriority,
    IssueType
)
from src.gemini_integration.models import CodeSnippet


class IssueBuilder:
    """Fluent builder for creating Issue objects.
    
    Example:
        >>> issue = (IssueBuilder()
        ...     .with_title("Fix bug")
        ...     .with_state(IssueState.OPEN)
        ...     .with_priority(IssuePriority.HIGH)
        ...     .created_days_ago(5)
        ...     .build())
    """
    
    def __init__(self):
        """Initialize the builder with defaults."""
        self._id = 1
        self._number = 1
        self._title = "Test Issue"
        self._body = "Test issue description"
        self._state = IssueState.OPEN
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
        self._closed_at = None
        self._user = GitHubUser(
            id=12345,
            login="test_user",
            name="Test User",
            email="test@example.com"
        )
        self._assignee = None
        self._assignees = []
        self._labels = []
        self._milestone = None
        self._comments = 0
        self._html_url = "https://github.com/test/repo/issues/1"
        self._priority = IssuePriority.MEDIUM
        self._issue_type = IssueType.BUG
        
    def with_id(self, issue_id: int) -> "IssueBuilder":
        """Set the issue ID."""
        self._id = issue_id
        return self
    
    def with_number(self, number: int) -> "IssueBuilder":
        """Set the issue number."""
        self._number = number
        self._html_url = f"https://github.com/test/repo/issues/{number}"
        return self
    
    def with_title(self, title: str) -> "IssueBuilder":
        """Set the issue title."""
        self._title = title
        return self
    
    def with_body(self, body: str) -> "IssueBuilder":
        """Set the issue body."""
        self._body = body
        return self
    
    def with_state(self, state: IssueState) -> "IssueBuilder":
        """Set the issue state."""
        self._state = state
        return self
    
    def with_priority(self, priority: IssuePriority) -> "IssueBuilder":
        """Set the issue priority."""
        self._priority = priority
        return self
    
    def with_type(self, issue_type: IssueType) -> "IssueBuilder":
        """Set the issue type."""
        self._issue_type = issue_type
        return self
    
    def with_labels(self, labels: List[str]) -> "IssueBuilder":
        """Set the issue labels."""
        self._labels = labels
        return self
    
    def with_assignee(self, user: GitHubUser) -> "IssueBuilder":
        """Set the issue assignee."""
        self._assignee = user
        self._assignees = [user]
        return self
    
    def with_comments(self, count: int) -> "IssueBuilder":
        """Set the number of comments."""
        self._comments = count
        return self
    
    def created_days_ago(self, days: int) -> "IssueBuilder":
        """Set the creation date relative to now."""
        self._created_at = datetime.now() - timedelta(days=days)
        return self
    
    def updated_days_ago(self, days: int) -> "IssueBuilder":
        """Set the update date relative to now."""
        self._updated_at = datetime.now() - timedelta(days=days)
        return self
    
    def closed_days_ago(self, days: int) -> "IssueBuilder":
        """Set the closed date relative to now."""
        self._closed_at = datetime.now() - timedelta(days=days)
        self._state = IssueState.CLOSED
        return self
    
    def build(self) -> Issue:
        """Build the Issue object.
        
        Returns:
            Configured Issue object
        """
        return Issue(
            id=self._id,
            number=self._number,
            title=self._title,
            body=self._body,
            state=self._state,
            created_at=self._created_at,
            updated_at=self._updated_at,
            closed_at=self._closed_at,
            user=self._user,
            assignee=self._assignee,
            assignees=self._assignees,
            labels=self._labels,
            milestone=self._milestone,
            comments=self._comments,
            html_url=self._html_url,
            priority=self._priority,
            issue_type=self._issue_type
        )


class IssueListBuilder:
    """Builder for creating lists of issues with common patterns.
    
    Example:
        >>> issues = (IssueListBuilder()
        ...     .add_open_issues(5)
        ...     .add_closed_issues(3)
        ...     .with_time_spread(30)  # spread over 30 days
        ...     .build())
    """
    
    def __init__(self):
        """Initialize the builder."""
        self._issues: List[Issue] = []
        self._counter = 1
        
    def add_open_issue(
        self,
        title: Optional[str] = None,
        priority: IssuePriority = IssuePriority.MEDIUM,
        issue_type: IssueType = IssueType.BUG,
        days_ago: int = 0
    ) -> "IssueListBuilder":
        """Add a single open issue.
        
        Args:
            title: Issue title (auto-generated if None)
            priority: Issue priority
            issue_type: Issue type
            days_ago: How many days ago it was created
            
        Returns:
            Self for chaining
        """
        if title is None:
            title = f"Open Issue {self._counter}"
        
        issue = (IssueBuilder()
                 .with_number(self._counter)
                 .with_title(title)
                 .with_state(IssueState.OPEN)
                 .with_priority(priority)
                 .with_type(issue_type)
                 .created_days_ago(days_ago)
                 .build())
        
        self._issues.append(issue)
        self._counter += 1
        return self
    
    def add_closed_issue(
        self,
        title: Optional[str] = None,
        priority: IssuePriority = IssuePriority.MEDIUM,
        issue_type: IssueType = IssueType.BUG,
        created_days_ago: int = 7,
        closed_days_ago: int = 1
    ) -> "IssueListBuilder":
        """Add a single closed issue.
        
        Args:
            title: Issue title (auto-generated if None)
            priority: Issue priority
            issue_type: Issue type
            created_days_ago: How many days ago it was created
            closed_days_ago: How many days ago it was closed
            
        Returns:
            Self for chaining
        """
        if title is None:
            title = f"Closed Issue {self._counter}"
        
        issue = (IssueBuilder()
                 .with_number(self._counter)
                 .with_title(title)
                 .with_state(IssueState.CLOSED)
                 .with_priority(priority)
                 .with_type(issue_type)
                 .created_days_ago(created_days_ago)
                 .closed_days_ago(closed_days_ago)
                 .build())
        
        self._issues.append(issue)
        self._counter += 1
        return self
    
    def add_open_issues(self, count: int) -> "IssueListBuilder":
        """Add multiple open issues.
        
        Args:
            count: Number of issues to add
            
        Returns:
            Self for chaining
        """
        for i in range(count):
            self.add_open_issue(days_ago=i)
        return self
    
    def add_closed_issues(self, count: int) -> "IssueListBuilder":
        """Add multiple closed issues.
        
        Args:
            count: Number of issues to add
            
        Returns:
            Self for chaining
        """
        for i in range(count):
            self.add_closed_issue(
                created_days_ago=i + 10,
                closed_days_ago=i
            )
        return self
    
    def with_priority_distribution(
        self,
        high: int = 2,
        medium: int = 5,
        low: int = 3
    ) -> "IssueListBuilder":
        """Add issues with specific priority distribution.
        
        Args:
            high: Number of high priority issues
            medium: Number of medium priority issues
            low: Number of low priority issues
            
        Returns:
            Self for chaining
        """
        for i in range(high):
            self.add_open_issue(priority=IssuePriority.HIGH, days_ago=i)
        
        for i in range(medium):
            self.add_open_issue(priority=IssuePriority.MEDIUM, days_ago=i)
        
        for i in range(low):
            self.add_open_issue(priority=IssuePriority.LOW, days_ago=i)
        
        return self
    
    def build(self) -> List[Issue]:
        """Build the list of issues.
        
        Returns:
            List of configured Issue objects
        """
        return self._issues


class CodeSnippetBuilder:
    """Builder for creating CodeSnippet objects.
    
    Example:
        >>> snippet = (CodeSnippetBuilder()
        ...     .with_language("python")
        ...     .with_content("def hello(): pass")
        ...     .build())
    """
    
    def __init__(self):
        """Initialize the builder."""
        self._content = "print('Hello, World!')"
        self._language = "python"
        self._file_path = "test.py"
        
    def with_content(self, content: str) -> "CodeSnippetBuilder":
        """Set the code content."""
        self._content = content
        return self
    
    def with_language(self, language: str) -> "CodeSnippetBuilder":
        """Set the programming language."""
        self._language = language
        return self
    
    def with_file_path(self, file_path: str) -> "CodeSnippetBuilder":
        """Set the file path."""
        self._file_path = file_path
        return self
    
    def build(self) -> CodeSnippet:
        """Build the CodeSnippet object.
        
        Returns:
            Configured CodeSnippet object
        """
        return CodeSnippet(
            content=self._content,
            language=self._language,
            file_path=self._file_path
        )


def create_sample_issues(
    total: int = 10,
    open_ratio: float = 0.6
) -> List[Issue]:
    """Quick function to create sample issues.
    
    Args:
        total: Total number of issues
        open_ratio: Ratio of open to total issues (0.0 to 1.0)
        
    Returns:
        List of Issue objects
    """
    num_open = int(total * open_ratio)
    num_closed = total - num_open
    
    return (IssueListBuilder()
            .add_open_issues(num_open)
            .add_closed_issues(num_closed)
            .build())
