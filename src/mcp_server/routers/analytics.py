"""
MCP Server - Analytics Router
Handles API endpoints for running data analysis.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict

from ...analytics.engine import AnalyticsEngine, AnalysisResult
from ...github_monitor.service import GitHubIssuesService

logger = logging.getLogger(__name__)
router = APIRouter()


# Dependency to get services from app state
def get_analytics_engine(request: Request) -> AnalyticsEngine:
    return request.app.state.analytics_engine

def get_github_service(request: Request) -> GitHubIssuesService:
    return request.app.state.github_service


@router.post("/run", response_model=Dict[str, AnalysisResult])
async def run_analysis(
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine),
    github_service: GitHubIssuesService = Depends(get_github_service)
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
            
        return results
    except Exception as e:
        logger.error(f"Failed to run analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred during analysis: {e}")


@router.get("/summary", response_model=dict)
async def get_analysis_summary(
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine),
    github_service: GitHubIssuesService = Depends(get_github_service)
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
            raise HTTPException(status_code=400, detail="Analysis produced no results to summarize.")

        summary = await analytics_engine.get_summary_insights(analysis_results)
        return summary
    except Exception as e:
        logger.error(f"Failed to get analysis summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate analysis summary: {e}")
