"""
MCP Server - AI Router
Handles API endpoints for Gemini AI analysis.
"""

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ...config.logging_config import get_logger
from ...github_monitor.service import GitHubIssuesService
from ...utils import RetryPolicies, retry, track_api_calls

# Optional imports for AI functionality
try:
    from ...gemini_integration import CodeAnalyzer, GeminiClient
except ImportError:
    CodeAnalyzer = None
    GeminiClient = None

logger = get_logger(__name__)
router = APIRouter()


# Request/Response Models
class CodeAnalysisRequest(BaseModel):
    """Request model for code analysis."""

    code: str = Field(..., description="Code snippet to analyze")
    language: Optional[str] = Field(None, description="Programming language")
    context: Optional[str] = Field(None, description="Additional context")


class IssueAnalysisRequest(BaseModel):
    """Request model for issue analysis."""

    issue_numbers: List[int] = Field(..., description="Issue numbers to analyze")
    analysis_type: Optional[str] = Field(
        "comprehensive", description="Type of analysis to perform"
    )


class SentimentAnalysisRequest(BaseModel):
    """Request model for sentiment analysis."""

    texts: List[str] = Field(..., description="Texts to analyze sentiment")


class PredictionRequest(BaseModel):
    """Request model for trend prediction."""

    metric: str = Field(..., description="Metric to predict")
    historical_data: List[float] = Field(..., description="Historical data points")


# Dependencies
def get_gemini_client(request: Request) -> Optional[GeminiClient]:
    """Get Gemini client from app state."""
    return getattr(request.app.state, "gemini_client", None)


def get_github_service(request: Request) -> GitHubIssuesService:
    """Get GitHub service from app state."""
    return request.app.state.github_service


@router.post("/analyze/code")
@retry(policy=RetryPolicies.GEMINI_API)
@track_api_calls("ai_code_analysis")
async def analyze_code(
    request: CodeAnalysisRequest,
    gemini_client: Optional[GeminiClient] = Depends(get_gemini_client),
):
    """
    Analyze code with AI and provide insights.

    Args:
        request: Code analysis request with code snippet

    Returns:
        Analysis results with quality assessment and suggestions
    """
    if not gemini_client:
        raise HTTPException(
            status_code=503, detail="AI service not available. Configure GEMINI_API_KEY."
        )

    try:
        analyzer = CodeAnalyzer(gemini_client)
        result = await analyzer.analyze_code(
            code=request.code,
            language=request.language,
            context=request.context,
        )

        logger.info(
            "Code analysis completed",
            language=request.language,
            code_length=len(request.code),
        )

        return {
            "status": "success",
            "analysis": result,
            "metadata": {
                "language": request.language,
                "code_length": len(request.code),
            },
        }
    except Exception as e:
        logger.error(f"Code analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze code: {str(e)}"
        )


@router.post("/analyze/issues")
@retry(policy=RetryPolicies.GEMINI_API)
@track_api_calls("ai_issue_analysis")
async def analyze_issues(
    request: IssueAnalysisRequest,
    gemini_client: Optional[GeminiClient] = Depends(get_gemini_client),
    github_service: GitHubIssuesService = Depends(get_github_service),
):
    """
    Analyze GitHub issues with AI to provide insights and recommendations.

    Args:
        request: Issue analysis request with issue numbers

    Returns:
        AI-powered analysis of the issues
    """
    if not gemini_client:
        raise HTTPException(
            status_code=503, detail="AI service not available. Configure GEMINI_API_KEY."
        )

    try:
        # Fetch issues
        all_issues = await github_service.get_all_issues()
        selected_issues = [
            issue for issue in all_issues if issue.number in request.issue_numbers
        ]

        if not selected_issues:
            raise HTTPException(
                status_code=404,
                detail=f"No issues found for numbers: {request.issue_numbers}",
            )

        # Prepare issue data for AI analysis
        issue_texts = []
        for issue in selected_issues:
            issue_text = f"Issue #{issue.number}: {issue.title}\n{issue.body or ''}"
            issue_texts.append(issue_text)

        # Analyze with AI
        analyzer = CodeAnalyzer(gemini_client)
        combined_text = "\n\n".join(issue_texts)

        # Use AI to analyze the issues
        prompt = f"""Analyze the following GitHub issues and provide:
1. Common themes or patterns
2. Priority recommendations
3. Potential solutions
4. Risk assessment

Issues:
{combined_text}
"""

        result = await gemini_client.generate(prompt)

        logger.info(
            "Issue analysis completed",
            issue_count=len(selected_issues),
            analysis_type=request.analysis_type,
        )

        return {
            "status": "success",
            "issues_analyzed": len(selected_issues),
            "analysis": result,
            "metadata": {
                "issue_numbers": request.issue_numbers,
                "analysis_type": request.analysis_type,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Issue analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze issues: {str(e)}"
        )


@router.post("/sentiment")
@retry(policy=RetryPolicies.GEMINI_API)
@track_api_calls("ai_sentiment_analysis")
async def analyze_sentiment(
    request: SentimentAnalysisRequest,
    gemini_client: Optional[GeminiClient] = Depends(get_gemini_client),
):
    """
    Perform sentiment analysis on texts.

    Args:
        request: Sentiment analysis request with texts

    Returns:
        Sentiment analysis results
    """
    if not gemini_client:
        raise HTTPException(
            status_code=503, detail="AI service not available. Configure GEMINI_API_KEY."
        )

    try:
        results = []

        for text in request.texts:
            prompt = f"""Analyze the sentiment of the following text. 
Provide: 
1. Overall sentiment (positive/negative/neutral)
2. Confidence score (0-1)
3. Key emotional indicators
4. Brief explanation

Text: {text}
"""
            result = await gemini_client.generate(prompt)
            results.append({"text": text[:100] + "...", "sentiment": result})

        logger.info("Sentiment analysis completed", text_count=len(request.texts))

        return {
            "status": "success",
            "results": results,
            "metadata": {"text_count": len(request.texts)},
        }
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze sentiment: {str(e)}"
        )


@router.post("/predict")
@retry(policy=RetryPolicies.GEMINI_API)
@track_api_calls("ai_prediction")
async def predict_trends(
    request: PredictionRequest,
    gemini_client: Optional[GeminiClient] = Depends(get_gemini_client),
):
    """
    Predict future trends based on historical data.

    Args:
        request: Prediction request with metric and historical data

    Returns:
        Trend predictions and insights
    """
    if not gemini_client:
        raise HTTPException(
            status_code=503, detail="AI service not available. Configure GEMINI_API_KEY."
        )

    try:
        # Prepare data summary
        data_summary = {
            "count": len(request.historical_data),
            "min": min(request.historical_data),
            "max": max(request.historical_data),
            "avg": sum(request.historical_data) / len(request.historical_data),
        }

        prompt = f"""Analyze the following time series data for the metric '{request.metric}' and provide:
1. Trend direction (increasing/decreasing/stable)
2. Predictions for next 3-5 time periods
3. Confidence level
4. Key insights and recommendations

Historical data: {request.historical_data}
Summary: {data_summary}
"""

        result = await gemini_client.generate(prompt)

        logger.info("Trend prediction completed", metric=request.metric)

        return {
            "status": "success",
            "metric": request.metric,
            "prediction": result,
            "data_summary": data_summary,
        }
    except Exception as e:
        logger.error(f"Trend prediction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to predict trends: {str(e)}"
        )


@router.get("/status")
async def get_ai_status(
    gemini_client: Optional[GeminiClient] = Depends(get_gemini_client),
):
    """
    Get AI service status and availability.

    Returns:
        AI service status information
    """
    return {
        "available": gemini_client is not None,
        "service": "Google Gemini 2.5 Flash",
        "features": [
            "Code analysis",
            "Issue intelligence",
            "Sentiment analysis",
            "Trend prediction",
        ],
    }
