"""
Tests for the Gemini Integration module.
"""

import pytest
from unittest.mock import AsyncMock, patch
import json

from src.gemini_integration.client import GeminiClient
from src.gemini_integration.analyzer import CodeAnalyzer
from src.gemini_integration.models import CodeSnippet, AnalysisStatus


@pytest.fixture
def mock_gemini_client():
    """Fixture for a mocked GeminiClient."""
    client = AsyncMock(spec=GeminiClient)
    return client


@pytest.mark.asyncio
async def test_gemini_client_success(monkeypatch):
    """Test successful content generation from GeminiClient."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key")
    
    with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate:
        mock_response = AsyncMock()
        mock_response.text = "Generated text"
        mock_response.usage_metadata = {"total_token_count": 100}
        mock_generate.return_value = mock_response
        
        client = GeminiClient()
        response = await client.generate_content("test prompt")
        
        assert response["status"] == AnalysisStatus.COMPLETED
        assert response["text"] == "Generated text"
        assert response["usage_metadata"]["total_token_count"] == 100


@pytest.mark.asyncio
async def test_code_analyzer_success(mock_gemini_client):
    """Test successful code analysis."""
    
    # Mock the response from the Gemini client
    mock_api_response = {
        "status": AnalysisStatus.COMPLETED,
        "text": json.dumps({
            "summary": "This is a test summary.",
            "complexity_score": 0.5,
            "maintainability_index": 0.8,
            "suggestions": [],
            "tags": ["test"]
        }),
        "usage_metadata": {"total_token_count": 200}
    }
    mock_gemini_client.generate_content.return_value = mock_api_response
    
    analyzer = CodeAnalyzer(client=mock_gemini_client)
    snippet = CodeSnippet(content="print('hello')", language="python")
    
    result = await analyzer.analyze_code(snippet)
    
    assert result.is_successful()
    assert result.report.summary == "This is a test summary."
    assert result.report.complexity_score == 0.5
    assert result.usage_metadata["total_token_count"] == 200


@pytest.mark.asyncio
async def test_code_analyzer_parsing_error(mock_gemini_client):
    """Test handling of a malformed JSON response from the model."""
    
    mock_api_response = {
        "status": AnalysisStatus.COMPLETED,
        "text": "This is not valid JSON.",
        "usage_metadata": {}
    }
    mock_gemini_client.generate_content.return_value = mock_api_response
    
    analyzer = CodeAnalyzer(client=mock_gemini_client)
    snippet = CodeSnippet(content="code", language="python")
    
    result = await analyzer.analyze_code(snippet)
    
    assert not result.is_successful()
    assert result.status == AnalysisStatus.FAILED
    assert "Failed to parse model response" in result.error_message
