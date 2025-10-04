"""
Tests for the MCP Server (API endpoints).
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

# It's important to patch settings before importing the app
from src.config import settings
settings.get_settings.cache_clear()
settings.SETTINGS_CACHE = None

from src.mcp_server.main import app
from src.github_monitor.models import Issue, IssueState


@pytest.fixture
def client():
    """Fixture for the FastAPI TestClient."""
    with TestClient(app) as c:
        yield c


def test_read_root(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["application"] == "xSweAgent"


def test_health_endpoint(client):
    """Test the /health endpoint returns OK."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert data.get("application") == "xSweAgent"


@patch('..src.mcp_server.routers.github.get_github_service')
def test_get_all_issues_endpoint(mock_get_service, client):
    """Test the /github/issues endpoint."""
    
    # Mock the service method
    mock_service_instance = AsyncMock()
    mock_service_instance.get_all_issues.return_value = [
        Issue(id=1, title="API Test Issue", state=IssueState.OPEN, created_at="2023-01-01T00:00:00Z")
    ]
    mock_get_service.return_value = mock_service_instance
    
    response = client.get("/api/v1/github/issues")
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "API Test Issue"


@patch('..src.mcp_server.routers.analytics.get_analytics_engine')
@patch('..src.mcp_server.routers.analytics.get_github_service')
def test_run_analysis_endpoint(mock_get_github, mock_get_analytics, client):
    """Test the /analytics/run endpoint."""
    
    # Mock GitHub service
    mock_github_service = AsyncMock()
    mock_github_service.get_all_issues.return_value = [Issue(id=1, title="Issue", state=IssueState.OPEN, created_at="2023-01-01")]
    mock_get_github.return_value = mock_github_service
    
    # Mock Analytics engine
    mock_analytics_engine = AsyncMock()
    mock_analytics_engine.analyze.return_value = {
        "productivity": {"score": 0.9, "summary": "Excellent"}
    }
    mock_get_analytics.return_value = mock_analytics_engine
    
    response = client.post("/api/v1/analytics/run")
    
    assert response.status_code == 200
    assert "productivity" in response.json()
    assert response.json()["productivity"]["score"] == 0.9
