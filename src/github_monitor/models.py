"""
Data models for GitHub entities.
Defines the structure of issues, pull requests, and other GitHub objects.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class IssueState(str, Enum):
    """GitHub issue state enumeration."""

    OPEN = "open"
    CLOSED = "closed"
    ALL = "all"


class IssuePriority(str, Enum):
    """Issue priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class IssueType(str, Enum):
    """Issue type classification."""

    BUG = "bug"
    FEATURE = "feature"
    ENHANCEMENT = "enhancement"
    DOCUMENTATION = "documentation"
    QUESTION = "question"
    OTHER = "other"


@dataclass
class GitHubUser:
    """GitHub user representation."""

    id: int
    login: str
    name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    html_url: Optional[str] = None
    type: str = "User"  # User, Bot, Organization

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GitHubUser":
        """Create GitHubUser from GitHub API response."""
        return cls(
            id=data.get("id"),
            login=data.get("login"),
            name=data.get("name"),
            email=data.get("email"),
            avatar_url=data.get("avatar_url"),
            html_url=data.get("html_url"),
            type=data.get("type", "User"),
        )


@dataclass
class Label:
    """GitHub label representation."""

    id: int
    name: str
    color: str
    description: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Label":
        """Create Label from GitHub API response."""
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            color=data.get("color"),
            description=data.get("description"),
        )


@dataclass
class Milestone:
    """GitHub milestone representation."""

    id: int
    number: int
    title: str
    description: Optional[str] = None
    state: str = "open"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    due_on: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    open_issues: int = 0
    closed_issues: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Milestone":
        """Create Milestone from GitHub API response."""
        return cls(
            id=data.get("id"),
            number=data.get("number"),
            title=data.get("title"),
            description=data.get("description"),
            state=data.get("state", "open"),
            created_at=cls._parse_datetime(data.get("created_at")),
            updated_at=cls._parse_datetime(data.get("updated_at")),
            due_on=cls._parse_datetime(data.get("due_on")),
            closed_at=cls._parse_datetime(data.get("closed_at")),
            open_issues=data.get("open_issues", 0),
            closed_issues=data.get("closed_issues", 0),
        )

    @staticmethod
    def _parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
        """Parse GitHub datetime string."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None


@dataclass
class Issue:
    """GitHub issue representation with enhanced analytics fields."""

    id: int
    number: int
    title: str
    body: Optional[str] = None
    state: IssueState = IssueState.OPEN
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    user: Optional[GitHubUser] = None
    assignee: Optional[GitHubUser] = None
    assignees: List[GitHubUser] = field(default_factory=list)
    labels: List[Label] = field(default_factory=list)
    milestone: Optional[Milestone] = None
    comments: int = 0
    html_url: Optional[str] = None

    # Analytics fields
    priority: IssuePriority = IssuePriority.UNKNOWN
    issue_type: IssueType = IssueType.OTHER
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Issue":
        """Create Issue from GitHub API response."""
        # Parse user
        user_data = data.get("user")
        user = GitHubUser.from_dict(user_data) if user_data else None

        # Parse assignee
        assignee_data = data.get("assignee")
        assignee = GitHubUser.from_dict(assignee_data) if assignee_data else None

        # Parse assignees
        assignees = []
        for assignee_data in data.get("assignees", []):
            assignees.append(GitHubUser.from_dict(assignee_data))

        # Parse labels
        labels = []
        for label_data in data.get("labels", []):
            labels.append(Label.from_dict(label_data))

        # Parse milestone
        milestone_data = data.get("milestone")
        milestone = Milestone.from_dict(milestone_data) if milestone_data else None

        issue = cls(
            id=data.get("id"),
            number=data.get("number"),
            title=data.get("title"),
            body=data.get("body"),
            state=IssueState(data.get("state", "open")),
            created_at=cls._parse_datetime(data.get("created_at")),
            updated_at=cls._parse_datetime(data.get("updated_at")),
            closed_at=cls._parse_datetime(data.get("closed_at")),
            user=user,
            assignee=assignee,
            assignees=assignees,
            labels=labels,
            milestone=milestone,
            comments=data.get("comments", 0),
            html_url=data.get("html_url"),
        )

        # Analyze issue for priority and type
        issue._analyze_issue()

        return issue

    def _analyze_issue(self):
        """Analyze issue content to determine priority and type."""
        # Extract priority from labels
        priority_labels = {
            "critical": IssuePriority.CRITICAL,
            "high": IssuePriority.HIGH,
            "medium": IssuePriority.MEDIUM,
            "low": IssuePriority.LOW,
            "priority: critical": IssuePriority.CRITICAL,
            "priority: high": IssuePriority.HIGH,
            "priority: medium": IssuePriority.MEDIUM,
            "priority: low": IssuePriority.LOW,
        }

        for label in self.labels:
            label_name = label.name.lower()
            if label_name in priority_labels:
                self.priority = priority_labels[label_name]
                break

        # Extract type from labels
        type_labels = {
            "bug": IssueType.BUG,
            "feature": IssueType.FEATURE,
            "enhancement": IssueType.ENHANCEMENT,
            "documentation": IssueType.DOCUMENTATION,
            "question": IssueType.QUESTION,
            "docs": IssueType.DOCUMENTATION,
            "feat": IssueType.FEATURE,
            "fix": IssueType.BUG,
        }

        for label in self.labels:
            label_name = label.name.lower()
            if label_name in type_labels:
                self.issue_type = type_labels[label_name]
                break

    @staticmethod
    def _parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
        """Parse GitHub datetime string."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    @property
    def is_open(self) -> bool:
        """Check if issue is open."""
        return self.state == IssueState.OPEN

    @property
    def is_closed(self) -> bool:
        """Check if issue is closed."""
        return self.state == IssueState.CLOSED

    @property
    def time_to_close(self) -> Optional[float]:
        """Calculate time to close in hours."""
        if not self.is_closed or not self.created_at or not self.closed_at:
            return None

        delta = self.closed_at - self.created_at
        return delta.total_seconds() / 3600

    @property
    def age_in_hours(self) -> Optional[float]:
        """Calculate issue age in hours."""
        if not self.created_at:
            return None

        end_time = (
            self.closed_at if self.is_closed else datetime.now(self.created_at.tzinfo)
        )
        delta = end_time - self.created_at
        return delta.total_seconds() / 3600

    @property
    def has_assignee(self) -> bool:
        """Check if issue has any assignee."""
        return self.assignee is not None or len(self.assignees) > 0

    @property
    def label_names(self) -> List[str]:
        """Get list of label names."""
        return [label.name for label in self.labels]

    def to_dict(self) -> Dict[str, Any]:
        """Convert issue to dictionary for serialization."""
        return {
            "id": self.id,
            "number": self.number,
            "title": self.title,
            "body": self.body,
            "state": self.state.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "user": self.user.login if self.user else None,
            "assignee": self.assignee.login if self.assignee else None,
            "assignees": [a.login for a in self.assignees],
            "labels": self.label_names,
            "milestone": self.milestone.title if self.milestone else None,
            "comments": self.comments,
            "html_url": self.html_url,
            "priority": self.priority.value,
            "issue_type": self.issue_type.value,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "time_to_close": self.time_to_close,
            "age_in_hours": self.age_in_hours,
        }


@dataclass
class PullRequest:
    """GitHub pull request representation."""

    id: int
    number: int
    title: str
    body: Optional[str] = None
    state: str = "open"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    merged_at: Optional[datetime] = None
    user: Optional[GitHubUser] = None
    assignee: Optional[GitHubUser] = None
    assignees: List[GitHubUser] = field(default_factory=list)
    labels: List[Label] = field(default_factory=list)
    milestone: Optional[Milestone] = None
    html_url: Optional[str] = None

    # PR specific fields
    head_sha: Optional[str] = None
    base_sha: Optional[str] = None
    is_draft: bool = False
    mergeable: Optional[bool] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PullRequest":
        """Create PullRequest from GitHub API response."""
        # Similar parsing logic as Issue
        # Implementation would be similar to Issue.from_dict()
        pass  # Placeholder for now

    @property
    def is_merged(self) -> bool:
        """Check if PR is merged."""
        return self.merged_at is not None

    @property
    def time_to_merge(self) -> Optional[float]:
        """Calculate time to merge in hours."""
        if not self.is_merged or not self.created_at or not self.merged_at:
            return None

        delta = self.merged_at - self.created_at
        return delta.total_seconds() / 3600


@dataclass
class Repository:
    """GitHub repository representation."""

    id: int
    name: str
    full_name: str
    description: Optional[str] = None
    private: bool = False
    html_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    pushed_at: Optional[datetime] = None

    # Repository stats
    open_issues_count: int = 0
    forks_count: int = 0
    stargazers_count: int = 0
    watchers_count: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Repository":
        """Create Repository from GitHub API response."""
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            full_name=data.get("full_name"),
            description=data.get("description"),
            private=data.get("private", False),
            html_url=data.get("html_url"),
            created_at=cls._parse_datetime(data.get("created_at")),
            updated_at=cls._parse_datetime(data.get("updated_at")),
            pushed_at=cls._parse_datetime(data.get("pushed_at")),
            open_issues_count=data.get("open_issues_count", 0),
            forks_count=data.get("forks_count", 0),
            stargazers_count=data.get("stargazers_count", 0),
            watchers_count=data.get("watchers_count", 0),
        )

    @staticmethod
    def _parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
        """Parse GitHub datetime string."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
