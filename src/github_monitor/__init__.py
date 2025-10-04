"""
GitHub Monitor Package.
Provides comprehensive GitHub repository monitoring and analytics.
"""

from .models import (
    Issue,
    IssueState,
    IssuePriority,
    IssueType,
    GitHubUser,
    Label,
    Milestone,
    Repository,
    PullRequest,
)

from .repository import (
    GitHubRepositoryInterface,
    GitHubRepository,
    CachedGitHubRepository,
    SearchCriteria,
    create_github_repository,
)

from .service import GitHubIssuesService, IssueMetrics, ProductivityMetrics

__all__ = [
    # Models
    "Issue",
    "IssueState",
    "IssuePriority",
    "IssueType",
    "GitHubUser",
    "Label",
    "Milestone",
    "Repository",
    "PullRequest",
    # Repository
    "GitHubRepositoryInterface",
    "GitHubRepository",
    "CachedGitHubRepository",
    "SearchCriteria",
    "create_github_repository",
    # Service
    "GitHubIssuesService",
    "IssueMetrics",
    "ProductivityMetrics",
]
