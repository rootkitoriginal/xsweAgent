"""
MCP Server - GitHub Router
Handles API endpoints related to GitHub data.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request

from ...config.logging_config import get_logger
from ...github_monitor.models import Issue
from ...github_monitor.service import GitHubIssuesService
from ...utils import CircuitBreakerPolicies, RetryPolicies, circuit_breaker, retry, track_api_calls

logger = get_logger(__name__)
router = APIRouter()


# Dependency to get the GitHub service from app state
def get_github_service(request: Request) -> GitHubIssuesService:
    return request.app.state.github_service


@router.get("/issues", response_model=List[Issue])
@retry(policy=RetryPolicies.GITHUB_API)
@track_api_calls("github_issues")
async def get_all_issues(service: GitHubIssuesService = Depends(get_github_service)):
    """
    Retrieve all issues from the configured GitHub repository.
    """
    try:
        issues = await service.get_all_issues()
        if not issues:
            raise HTTPException(status_code=404, detail="No issues found.")
        logger.info("Retrieved issues successfully", count=len(issues))
        return issues
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve GitHub issues: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve issues from GitHub."
        )


@router.get("/issues/summary", response_model=dict)
@retry(policy=RetryPolicies.GITHUB_API)
@track_api_calls("github_summary")
async def get_issues_summary(
    service: GitHubIssuesService = Depends(get_github_service),
):
    """
    Get a summary of open and closed issues.
    """
    try:
        summary = await service.get_issue_summary()
        logger.info("Issues summary generated successfully")
        return summary
    except Exception as e:
        logger.error(f"Failed to get issues summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate issue summary.")
