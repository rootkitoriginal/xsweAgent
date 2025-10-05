"""
MCP Server - Analytics Router
Handles API endpoints for running data analysis.
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Request

from ...analytics.engine import AnalysisResult, AnalyticsEngine
from ...config.logging_config import get_logger
from ...github_monitor.service import GitHubIssuesService
from ...utils import CircuitBreakerPolicies, RetryPolicies, circuit_breaker, retry, track_api_calls

logger = get_logger(__name__)
router = APIRouter()


# Dependency to get services from app state
def get_analytics_engine(request: Request) -> AnalyticsEngine:
    return request.app.state.analytics_engine


def get_github_service(request: Request) -> GitHubIssuesService:
    return request.app.state.github_service


@router.post("/run", response_model=Dict[str, AnalysisResult])
@retry(RetryPolicies.STANDARD)
@track_api_calls("analytics_run")
async def run_analysis(
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine),
    github_service: GitHubIssuesService = Depends(get_github_service),
):
    """
    Run a full analysis on the repository data.
    """
    try:
        issues = await github_service.get_all_issues()
        if not issues:
            raise HTTPException(status_code=404, detail="No issues found to analyze.")

        repo_name = github_service.repo_name
        results = await analytics_engine.analyze(issues, repo_name)

        if not results:
            raise HTTPException(status_code=400, detail="Analysis produced no results.")

        logger.info("Analysis completed successfully", issue_count=len(issues))
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"An error occurred during analysis: {e}"
        )


@router.get("/summary", response_model=dict)
@retry(RetryPolicies.STANDARD)
@track_api_calls("analytics_summary")
async def get_analysis_summary(
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine),
    github_service: GitHubIssuesService = Depends(get_github_service),
):
    """
    Get a high-level summary and insights from the latest analysis.
    """
    try:
        issues = await github_service.get_all_issues()
        if not issues:
            raise HTTPException(status_code=404, detail="No issues found to analyze.")

        repo_name = github_service.repo_name
        analysis_results = await analytics_engine.analyze(issues, repo_name)

        if not analysis_results:
            raise HTTPException(
                status_code=400, detail="Analysis produced no results to summarize."
            )

        summary = await analytics_engine.get_summary_insights(analysis_results)
        logger.info("Analysis summary generated successfully")
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate analysis summary: {e}"
        )
