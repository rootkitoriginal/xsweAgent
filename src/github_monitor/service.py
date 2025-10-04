"""
GitHub Issues Service.
High-level service for monitoring and analyzing GitHub issues.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio

from ..config import get_config
from ..config.logging_config import get_logger
from .repository import GitHubRepositoryInterface, create_github_repository, SearchCriteria
from .models import Issue, IssueState, IssuePriority, IssueType


@dataclass
class IssueMetrics:
    """Metrics calculated from issues data."""
    total_issues: int
    open_issues: int
    closed_issues: int
    average_time_to_close_hours: Optional[float]
    median_time_to_close_hours: Optional[float]
    issues_by_priority: Dict[str, int]
    issues_by_type: Dict[str, int]
    issues_by_assignee: Dict[str, int]
    recent_activity: int  # Issues created in last 7 days
    stale_issues: int  # Open issues older than 30 days


@dataclass
class ProductivityMetrics:
    """Productivity metrics for the development team."""
    issues_created_per_day: float
    issues_closed_per_day: float
    throughput: float  # Closed / Created ratio
    cycle_time_average_hours: Optional[float]
    lead_time_average_hours: Optional[float]
    work_in_progress: int  # Open issues with assignees
    backlog_size: int  # Open issues without assignees


class GitHubIssuesService:
    """Service for monitoring and analyzing GitHub issues."""
    
    def __init__(self, repository: Optional[GitHubRepositoryInterface] = None):
        self.repository = repository or create_github_repository()
        self.logger = get_logger("github_issues_service")
        self.config = get_config()
    
    async def get_all_issues(self, 
                           days_back: int = 90,
                           include_closed: bool = True) -> List[Issue]:
        """Get all issues from the specified time period."""
        self.logger.info(f"Fetching all issues from last {days_back} days")
        
        since = datetime.now() - timedelta(days=days_back)
        
        # Get open issues
        open_criteria = SearchCriteria(
            state=IssueState.OPEN,
            since=since,
            sort="created",
            direction="desc",
            per_page=100
        )
        
        all_issues = []
        
        try:
            # Fetch open issues
            open_issues = await self.repository.get_issues(open_criteria)
            all_issues.extend(open_issues)
            
            # Fetch closed issues if requested
            if include_closed:
                closed_criteria = SearchCriteria(
                    state=IssueState.CLOSED,
                    since=since,
                    sort="updated",  # Use updated for closed issues
                    direction="desc",
                    per_page=100
                )
                
                closed_issues = await self.repository.get_issues(closed_criteria)
                all_issues.extend(closed_issues)
            
            self.logger.info(f"Fetched {len(all_issues)} total issues")
            return all_issues
            
        except Exception as e:
            self.logger.exception("Error fetching all issues", error=str(e))
            raise
    
    async def calculate_issue_metrics(self, issues: List[Issue]) -> IssueMetrics:
        """Calculate comprehensive metrics from issues list."""
        self.logger.info(f"Calculating metrics for {len(issues)} issues")
        
        if not issues:
            return IssueMetrics(
                total_issues=0,
                open_issues=0,
                closed_issues=0,
                average_time_to_close_hours=None,
                median_time_to_close_hours=None,
                issues_by_priority={},
                issues_by_type={},
                issues_by_assignee={},
                recent_activity=0,
                stale_issues=0
            )
        
        # Basic counts
        total_issues = len(issues)
        open_issues = sum(1 for issue in issues if issue.is_open)
        closed_issues = sum(1 for issue in issues if issue.is_closed)
        
        # Time to close calculations
        close_times = [
            issue.time_to_close for issue in issues 
            if issue.time_to_close is not None
        ]
        
        avg_time_to_close = None
        median_time_to_close = None
        
        if close_times:
            avg_time_to_close = sum(close_times) / len(close_times)
            close_times_sorted = sorted(close_times)
            n = len(close_times_sorted)
            median_time_to_close = (
                close_times_sorted[n // 2] if n % 2 == 1
                else (close_times_sorted[n // 2 - 1] + close_times_sorted[n // 2]) / 2
            )
        
        # Group by priority
        issues_by_priority = {}
        for priority in IssuePriority:
            count = sum(1 for issue in issues if issue.priority == priority)
            if count > 0:
                issues_by_priority[priority.value] = count
        
        # Group by type
        issues_by_type = {}
        for issue_type in IssueType:
            count = sum(1 for issue in issues if issue.issue_type == issue_type)
            if count > 0:
                issues_by_type[issue_type.value] = count
        
        # Group by assignee
        issues_by_assignee = {}
        for issue in issues:
            if issue.assignee:
                assignee = issue.assignee.login
                issues_by_assignee[assignee] = issues_by_assignee.get(assignee, 0) + 1
            
            # Also count additional assignees
            for assignee in issue.assignees:
                assignee_login = assignee.login
                issues_by_assignee[assignee_login] = issues_by_assignee.get(assignee_login, 0) + 1
        
        # Recent activity (last 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_activity = sum(
            1 for issue in issues 
            if issue.created_at and issue.created_at.replace(tzinfo=None) >= seven_days_ago
        )
        
        # Stale issues (open issues older than 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        stale_issues = sum(
            1 for issue in issues 
            if issue.is_open and issue.created_at and 
            issue.created_at.replace(tzinfo=None) <= thirty_days_ago
        )
        
        metrics = IssueMetrics(
            total_issues=total_issues,
            open_issues=open_issues,
            closed_issues=closed_issues,
            average_time_to_close_hours=avg_time_to_close,
            median_time_to_close_hours=median_time_to_close,
            issues_by_priority=issues_by_priority,
            issues_by_type=issues_by_type,
            issues_by_assignee=issues_by_assignee,
            recent_activity=recent_activity,
            stale_issues=stale_issues
        )
        
        self.logger.info("Metrics calculated successfully", metrics=metrics.__dict__)
        return metrics
    
    async def calculate_productivity_metrics(self, 
                                           issues: List[Issue], 
                                           days_back: int = 30) -> ProductivityMetrics:
        """Calculate productivity metrics for the development team."""
        self.logger.info(f"Calculating productivity metrics for {len(issues)} issues over {days_back} days")
        
        if not issues:
            return ProductivityMetrics(
                issues_created_per_day=0.0,
                issues_closed_per_day=0.0,
                throughput=0.0,
                cycle_time_average_hours=None,
                lead_time_average_hours=None,
                work_in_progress=0,
                backlog_size=0
            )
        
        # Filter issues for the specified period
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Issues created in the period
        created_in_period = [
            issue for issue in issues
            if issue.created_at and issue.created_at.replace(tzinfo=None) >= cutoff_date
        ]
        
        # Issues closed in the period
        closed_in_period = [
            issue for issue in issues
            if (issue.closed_at and 
                issue.closed_at.replace(tzinfo=None) >= cutoff_date and
                issue.is_closed)
        ]
        
        # Calculate daily rates
        issues_created_per_day = len(created_in_period) / days_back
        issues_closed_per_day = len(closed_in_period) / days_back
        
        # Calculate throughput (efficiency ratio)
        throughput = issues_closed_per_day / issues_created_per_day if issues_created_per_day > 0 else 0.0
        
        # Cycle time (average time from start to completion)
        cycle_times = [
            issue.time_to_close for issue in closed_in_period
            if issue.time_to_close is not None
        ]
        cycle_time_average = sum(cycle_times) / len(cycle_times) if cycle_times else None
        
        # Lead time (same as cycle time for issues)
        lead_time_average = cycle_time_average
        
        # Work in progress (open issues with assignees)
        work_in_progress = sum(
            1 for issue in issues
            if issue.is_open and issue.has_assignee
        )
        
        # Backlog size (open issues without assignees)
        backlog_size = sum(
            1 for issue in issues
            if issue.is_open and not issue.has_assignee
        )
        
        metrics = ProductivityMetrics(
            issues_created_per_day=issues_created_per_day,
            issues_closed_per_day=issues_closed_per_day,
            throughput=throughput,
            cycle_time_average_hours=cycle_time_average,
            lead_time_average_hours=lead_time_average,
            work_in_progress=work_in_progress,
            backlog_size=backlog_size
        )
        
        self.logger.info("Productivity metrics calculated", metrics=metrics.__dict__)
        return metrics
    
    async def get_issues_by_milestone(self) -> Dict[str, List[Issue]]:
        """Group issues by milestone."""
        self.logger.info("Fetching issues grouped by milestone")
        
        try:
            # Get all issues
            criteria = SearchCriteria(state=IssueState.ALL, per_page=100)
            issues = await self.repository.get_issues(criteria)
            
            # Group by milestone
            issues_by_milestone = {}
            
            for issue in issues:
                milestone_name = issue.milestone.title if issue.milestone else "No Milestone"
                
                if milestone_name not in issues_by_milestone:
                    issues_by_milestone[milestone_name] = []
                
                issues_by_milestone[milestone_name].append(issue)
            
            self.logger.info(f"Grouped issues into {len(issues_by_milestone)} milestones")
            return issues_by_milestone
            
        except Exception as e:
            self.logger.exception("Error grouping issues by milestone", error=str(e))
            raise
    
    async def get_trending_issues(self, days: int = 7) -> List[Issue]:
        """Get issues with recent high activity."""
        self.logger.info(f"Finding trending issues from last {days} days")
        
        try:
            since = datetime.now() - timedelta(days=days)
            
            criteria = SearchCriteria(
                state=IssueState.ALL,
                since=since,
                sort="comments",  # Sort by comment count
                direction="desc",
                per_page=50
            )
            
            issues = await self.repository.get_issues(criteria)
            
            # Filter for issues with significant activity
            trending_issues = [
                issue for issue in issues
                if issue.comments >= 5 or  # Has comments
                (issue.updated_at and 
                 (datetime.now() - issue.updated_at.replace(tzinfo=None)).days <= 2)  # Recently updated
            ]
            
            self.logger.info(f"Found {len(trending_issues)} trending issues")
            return trending_issues
            
        except Exception as e:
            self.logger.exception("Error finding trending issues", error=str(e))
            raise
    
    async def get_performance_report(self, days_back: int = 30) -> Dict[str, Any]:
        """Generate a comprehensive performance report."""
        self.logger.info(f"Generating performance report for last {days_back} days")
        
        try:
            # Get all issues
            issues = await self.get_all_issues(days_back=days_back)
            
            # Calculate metrics
            issue_metrics = await self.calculate_issue_metrics(issues)
            productivity_metrics = await self.calculate_productivity_metrics(issues, days_back)
            
            # Get additional insights
            issues_by_milestone = await self.get_issues_by_milestone()
            trending_issues = await self.get_trending_issues(days=7)
            
            report = {
                "report_date": datetime.now().isoformat(),
                "period_days": days_back,
                "repository": f"{self.config.github.repo_owner}/{self.config.github.repo_name}",
                "issue_metrics": issue_metrics.__dict__,
                "productivity_metrics": productivity_metrics.__dict__,
                "milestones_count": len(issues_by_milestone),
                "trending_issues_count": len(trending_issues),
                "top_contributors": list(issue_metrics.issues_by_assignee.keys())[:5],
                "health_indicators": {
                    "throughput_healthy": productivity_metrics.throughput >= 0.8,
                    "stale_issues_concern": issue_metrics.stale_issues > 10,
                    "backlog_manageable": productivity_metrics.backlog_size <= 50
                }
            }
            
            self.logger.info("Performance report generated successfully")
            return report
            
        except Exception as e:
            self.logger.exception("Error generating performance report", error=str(e))
            raise
    
    async def monitor_repository_health(self) -> Dict[str, Any]:
        """Monitor overall repository health and return status."""
        self.logger.info("Monitoring repository health")
        
        try:
            # Get repository info
            repo_info = await self.repository.get_repository_info()
            
            # Get recent issues
            recent_issues = await self.get_all_issues(days_back=7, include_closed=True)
            
            # Calculate health metrics
            open_issues = sum(1 for issue in recent_issues if issue.is_open)
            closed_this_week = sum(1 for issue in recent_issues if issue.is_closed)
            
            health_score = min(100, max(0, 100 - (open_issues * 2) + (closed_this_week * 5)))
            
            health_status = {
                "timestamp": datetime.now().isoformat(),
                "repository": repo_info.full_name,
                "health_score": health_score,
                "open_issues_total": repo_info.open_issues_count,
                "open_issues_recent": open_issues,
                "closed_this_week": closed_this_week,
                "status": (
                    "excellent" if health_score >= 80 else
                    "good" if health_score >= 60 else
                    "needs_attention" if health_score >= 40 else
                    "critical"
                ),
                "recommendations": []
            }
            
            # Add recommendations based on health
            if open_issues > 20:
                health_status["recommendations"].append("Consider prioritizing issue resolution")
            
            if closed_this_week < 3:
                health_status["recommendations"].append("Low issue resolution rate this week")
            
            self.logger.info("Repository health check completed", health_score=health_score)
            return health_status
            
        except Exception as e:
            self.logger.exception("Error monitoring repository health", error=str(e))
            raise