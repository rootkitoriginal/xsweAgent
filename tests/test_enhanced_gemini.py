"""
Tests for enhanced Gemini AI integration with multiple analysis types.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.gemini_integration import (
    AIConfig,
    AnalysisStatus,
    CodeSnippet,
    GeminiAnalyzer,
    GeminiClient,
    PriorityLevel,
    SentimentType,
)
from src.github_monitor.models import Issue, Label


@pytest.fixture
def mock_gemini_client():
    """Fixture for a mocked GeminiClient."""
    client = AsyncMock(spec=GeminiClient)
    client.model_name = "gemini-2.5-flash"
    return client


@pytest.fixture
def sample_issue():
    """Fixture for a sample GitHub issue."""
    return Issue(
        id=123,
        number=1,
        title="Fix critical bug in authentication",
        body="Users cannot login after recent update",
        state="open",
        labels=[Label(id=1, name="bug", color="red")],
        created_at=None,
        updated_at=None,
    )


# ========== GeminiClient Enhanced Tests ==========


@pytest.mark.asyncio
async def test_gemini_client_with_config(monkeypatch):
    """Test GeminiClient initialization with custom config."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key")

    config = AIConfig(
        model="gemini-2.5-flash", temperature=0.3, max_output_tokens=4096
    )

    with patch("google.generativeai.GenerativeModel"):
        client = GeminiClient(config=config)
        assert client.model_name == "gemini-2.5-flash"
        assert client.config.temperature == 0.3


@pytest.mark.asyncio
async def test_gemini_client_batch_analyze(monkeypatch):
    """Test batch analysis functionality."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key")

    with patch("google.generativeai.GenerativeModel"):
        from src.gemini_integration.models import AIAnalysisRequest, AnalysisType

        client = GeminiClient()

        # Mock the _process_single_request method
        with patch.object(client, "_process_single_request") as mock_process:
            mock_process.return_value = MagicMock(
                request_id="123",
                analysis_type=AnalysisType.CODE_ANALYSIS,
                status=AnalysisStatus.COMPLETED,
            )

            requests = [
                AIAnalysisRequest(
                    analysis_type=AnalysisType.CODE_ANALYSIS,
                    data={"code": "print('hello')"},
                )
            ]

            results = await client.batch_analyze(requests)
            assert len(results) == 1
            assert results[0].status == AnalysisStatus.COMPLETED


@pytest.mark.asyncio
async def test_gemini_client_usage_tracking(monkeypatch):
    """Test usage tracking for cost monitoring."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key")

    with patch(
        "google.generativeai.GenerativeModel.generate_content_async"
    ) as mock_generate:
        mock_response = AsyncMock()
        mock_response.text = "Generated text"
        mock_response.usage_metadata = {"total_token_count": 150}
        mock_generate.return_value = mock_response

        client = GeminiClient()
        await client.generate_content("test prompt")

        stats = client.get_usage_stats()
        assert stats["total_requests"] == 1
        assert stats["total_tokens"] == 150


# ========== Issue Analysis Tests ==========


@pytest.mark.asyncio
async def test_issue_analysis_success(mock_gemini_client, sample_issue):
    """Test successful issue analysis."""
    mock_response = {
        "status": AnalysisStatus.COMPLETED,
        "text": json.dumps(
            {
                "category": "bug",
                "severity": "high",
                "estimated_hours": 4.5,
                "root_cause": "Authentication token validation failure",
                "labels": ["security", "authentication"],
                "confidence": 0.95,
            }
        ),
        "usage_metadata": {"total_token_count": 200},
    }
    mock_gemini_client.generate_content.return_value = mock_response

    analyzer = GeminiAnalyzer(client=mock_gemini_client)
    result = await analyzer.issue_analysis(sample_issue)

    assert result.status == AnalysisStatus.COMPLETED
    assert result.category == "bug"
    assert result.severity == "high"
    assert result.estimated_resolution_hours == 4.5
    assert "security" in result.recommended_labels
    assert result.confidence_score == 0.95


@pytest.mark.asyncio
async def test_issue_analysis_parsing_error(mock_gemini_client, sample_issue):
    """Test issue analysis with parsing error."""
    mock_response = {
        "status": AnalysisStatus.COMPLETED,
        "text": "Invalid JSON response",
        "usage_metadata": {},
    }
    mock_gemini_client.generate_content.return_value = mock_response

    analyzer = GeminiAnalyzer(client=mock_gemini_client)
    result = await analyzer.issue_analysis(sample_issue)

    assert result.status == AnalysisStatus.FAILED
    assert "Failed to parse" in result.error_message


# ========== Trend Prediction Tests ==========


@pytest.mark.asyncio
async def test_trend_prediction_success(mock_gemini_client):
    """Test successful trend prediction."""
    historical_data = [
        {"week": 1, "issues": 10, "resolution_time": 24},
        {"week": 2, "issues": 15, "resolution_time": 30},
        {"week": 3, "issues": 12, "resolution_time": 22},
    ]

    mock_response = {
        "status": AnalysisStatus.COMPLETED,
        "text": json.dumps(
            {
                "predicted_issues": 14,
                "predicted_resolution_time": 26.5,
                "quality_trend": "stable",
                "workload_forecast": "stable",
                "confidence": 0.85,
                "insights": ["Issue volume is relatively stable"],
                "recommendations": ["Maintain current team size"],
            }
        ),
        "usage_metadata": {"total_token_count": 250},
    }
    mock_gemini_client.generate_content.return_value = mock_response

    analyzer = GeminiAnalyzer(client=mock_gemini_client)
    result = await analyzer.trend_prediction(historical_data)

    assert result.status == AnalysisStatus.COMPLETED
    assert result.predicted_issue_count == 14
    assert result.predicted_resolution_time == 26.5
    assert result.quality_trend == "stable"
    assert len(result.insights) > 0
    assert len(result.recommendations) > 0


# ========== Sentiment Analysis Tests ==========


@pytest.mark.asyncio
async def test_sentiment_analysis_positive(mock_gemini_client):
    """Test sentiment analysis with positive sentiment."""
    text = "This is an excellent feature! Really love it."

    mock_response = {
        "status": AnalysisStatus.COMPLETED,
        "text": json.dumps(
            {
                "sentiment": "positive",
                "confidence": 0.92,
                "positive_score": 0.9,
                "negative_score": 0.05,
                "neutral_score": 0.05,
                "key_phrases": ["excellent feature", "love it"],
                "emotional_tone": "enthusiastic and appreciative",
            }
        ),
        "usage_metadata": {"total_token_count": 100},
    }
    mock_gemini_client.generate_content.return_value = mock_response

    analyzer = GeminiAnalyzer(client=mock_gemini_client)
    result = await analyzer.sentiment_analysis(text)

    assert result.status == AnalysisStatus.COMPLETED
    assert result.sentiment == SentimentType.POSITIVE
    assert result.confidence_score == 0.92
    assert result.positive_score > result.negative_score


@pytest.mark.asyncio
async def test_sentiment_analysis_negative(mock_gemini_client):
    """Test sentiment analysis with negative sentiment."""
    text = "This is broken and frustrating. Doesn't work at all."

    mock_response = {
        "status": AnalysisStatus.COMPLETED,
        "text": json.dumps(
            {
                "sentiment": "negative",
                "confidence": 0.88,
                "positive_score": 0.1,
                "negative_score": 0.85,
                "neutral_score": 0.05,
                "key_phrases": ["broken", "frustrating", "doesn't work"],
                "emotional_tone": "frustrated and disappointed",
            }
        ),
        "usage_metadata": {"total_token_count": 100},
    }
    mock_gemini_client.generate_content.return_value = mock_response

    analyzer = GeminiAnalyzer(client=mock_gemini_client)
    result = await analyzer.sentiment_analysis(text)

    assert result.status == AnalysisStatus.COMPLETED
    assert result.sentiment == SentimentType.NEGATIVE
    assert result.negative_score > result.positive_score


# ========== Priority Analysis Tests ==========


@pytest.mark.asyncio
async def test_priority_analysis_critical(mock_gemini_client, sample_issue):
    """Test priority analysis for critical issue."""
    mock_response = {
        "status": AnalysisStatus.COMPLETED,
        "text": json.dumps(
            {
                "priority": "critical",
                "business_impact": 0.95,
                "technical_complexity": 0.6,
                "urgency": 0.98,
                "strategic_alignment": 0.85,
                "overall_score": 0.90,
                "justification": "Authentication is critical for all users",
                "estimated_effort": 8.0,
                "dependencies": ["user-service", "auth-middleware"],
            }
        ),
        "usage_metadata": {"total_token_count": 180},
    }
    mock_gemini_client.generate_content.return_value = mock_response

    analyzer = GeminiAnalyzer(client=mock_gemini_client)
    result = await analyzer.priority_analysis(sample_issue)

    assert result.status == AnalysisStatus.COMPLETED
    assert result.priority == PriorityLevel.CRITICAL
    assert result.business_impact_score > 0.9
    assert result.urgency_score > 0.9
    assert len(result.dependencies) > 0


@pytest.mark.asyncio
async def test_priority_analysis_low(mock_gemini_client):
    """Test priority analysis for low priority issue."""
    low_priority_issue = Issue(
        id=124,
        number=2,
        title="Update documentation typo",
        body="Fix small typo in README",
        state="open",
        labels=[Label(id=2, name="documentation", color="blue")],
        created_at=None,
        updated_at=None,
    )

    mock_response = {
        "status": AnalysisStatus.COMPLETED,
        "text": json.dumps(
            {
                "priority": "low",
                "business_impact": 0.2,
                "technical_complexity": 0.1,
                "urgency": 0.15,
                "strategic_alignment": 0.3,
                "overall_score": 0.2,
                "justification": "Minor documentation fix with low impact",
                "estimated_effort": 0.5,
                "dependencies": [],
            }
        ),
        "usage_metadata": {"total_token_count": 150},
    }
    mock_gemini_client.generate_content.return_value = mock_response

    analyzer = GeminiAnalyzer(client=mock_gemini_client)
    result = await analyzer.priority_analysis(low_priority_issue)

    assert result.status == AnalysisStatus.COMPLETED
    assert result.priority == PriorityLevel.LOW
    assert result.business_impact_score < 0.3
    assert result.estimated_effort_hours < 1.0


# ========== Collaboration Analysis Tests ==========


@pytest.mark.asyncio
async def test_collaboration_analysis_success(mock_gemini_client):
    """Test successful collaboration analysis."""
    team_data = {
        "team_size": 5,
        "avg_review_time": 12,
        "code_review_participation": 0.8,
        "knowledge_sharing_sessions": 3,
    }

    mock_response = {
        "status": AnalysisStatus.COMPLETED,
        "text": json.dumps(
            {
                "communication_score": 0.85,
                "knowledge_sharing": 0.78,
                "efficiency": 0.82,
                "bottlenecks": ["Code review turnaround time"],
                "top_collaborators": ["alice", "bob", "charlie"],
                "team_health": 0.83,
                "insights": ["Team collaboration is generally strong"],
                "recommendations": ["Consider async code review tools"],
            }
        ),
        "usage_metadata": {"total_token_count": 200},
    }
    mock_gemini_client.generate_content.return_value = mock_response

    analyzer = GeminiAnalyzer(client=mock_gemini_client)
    result = await analyzer.collaboration_analysis(team_data)

    assert result.status == AnalysisStatus.COMPLETED
    assert result.team_health_score > 0.8
    assert len(result.top_collaborators) > 0
    assert len(result.insights) > 0
    assert len(result.recommendations) > 0


# ========== Code Analysis Backward Compatibility ==========


@pytest.mark.asyncio
async def test_code_analyzer_backward_compatibility(mock_gemini_client):
    """Test that CodeAnalyzer maintains backward compatibility."""
    from src.gemini_integration import CodeAnalyzer

    mock_response = {
        "status": AnalysisStatus.COMPLETED,
        "text": json.dumps(
            {
                "summary": "Simple Python print statement",
                "complexity_score": 0.1,
                "maintainability_index": 0.95,
                "suggestions": [],
                "tags": ["python", "simple"],
            }
        ),
        "usage_metadata": {"total_token_count": 100},
    }
    mock_gemini_client.generate_content.return_value = mock_response

    analyzer = CodeAnalyzer(client=mock_gemini_client)
    snippet = CodeSnippet(content="print('hello')", language="python")

    result = await analyzer.analyze_code(snippet)

    assert result.is_successful()
    assert result.report.complexity_score == 0.1
