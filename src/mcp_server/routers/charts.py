"""
MCP Server - Charts Router
Handles API endpoints for generating and retrieving charts.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from ...analytics.engine import AnalyticsEngine
from ...config.logging_config import get_logger
from ...github_monitor.service import GitHubIssuesService
from ...utils import RetryPolicies, retry, track_api_calls

# Optional imports for charts functionality
try:
    from ...charts.factory import ChartFactory
    from ...charts.generator import ChartGenerator
    from ...charts.models import ChartType

    CHARTS_AVAILABLE = True
except ImportError:
    ChartFactory = None
    ChartGenerator = None
    ChartType = None
    CHARTS_AVAILABLE = False

logger = get_logger(__name__)
router = APIRouter()


# Dependency to get services from app state
def get_analytics_engine(request: Request) -> AnalyticsEngine:
    return request.app.state.analytics_engine


def get_github_service(request: Request) -> GitHubIssuesService:
    return request.app.state.github_service


@router.get("/generate/{analysis_type}", response_class=Response)
@retry(policy=RetryPolicies.STANDARD)
@track_api_calls("chart_generation")
async def generate_chart_for_analysis(
    analysis_type: str,
    chart_type: Optional[str] = None,
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine),
    github_service: GitHubIssuesService = Depends(get_github_service),
):
    """
    Generate a chart for a specific analysis type.

    Args:
        analysis_type: The name of the analysis (e.g., 'productivity', 'velocity').
        chart_type: Optional specific chart type (e.g., 'bar', 'pie').
    """
    if not CHARTS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Charts functionality not available. Install matplotlib and plotly.",
        )

    try:
        # 1. Get data
        issues = await github_service.get_all_issues()
        if not issues:
            raise HTTPException(
                status_code=404, detail="No issues found to generate chart."
            )

        # 2. Run analysis
        repo_name = github_service.repo_name
        analysis_results = await analytics_engine.analyze(issues, repo_name)

        result_to_chart = analysis_results.get(analysis_type.lower())
        if not result_to_chart:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis type '{analysis_type}' not found or produced no result.",
            )

        # 3. Create chart configuration from factory
        selected_chart_type = ChartType(chart_type.lower()) if chart_type else None
        chart_data = ChartFactory.create_chart(result_to_chart, selected_chart_type)

        if not chart_data:
            raise HTTPException(
                status_code=400,
                detail=f"Could not create a chart for '{analysis_type}'.",
            )

        # 4. Generate chart image
        generator = ChartGenerator(chart_data.config)
        generated_chart = generator.generate()

        logger.info(
            "Chart generated successfully",
            analysis_type=analysis_type,
            chart_type=chart_type,
        )

        # 5. Return image as response
        return Response(content=generated_chart.image_data, media_type="image/png")

    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid chart type or analysis type provided."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate chart: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate chart: {e}")
