"""
Tests for enhanced MCP Server with new routers and infrastructure.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.config import settings
from src.mcp_server.main import app

# Clear settings cache for tests
settings.get_settings.cache_clear()
settings.SETTINGS_CACHE = None


@pytest.fixture
def client():
    """Fixture for the FastAPI TestClient."""
    with TestClient(app) as c:
        yield c


class TestRootAndHealth:
    """Tests for root and health endpoints."""

    def test_root_endpoint(self, client):
        """Test the root endpoint returns API structure."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "application" in data
        assert "version" in data
        assert "api_endpoints" in data
        assert "github" in data["api_endpoints"]
        assert "ai" in data["api_endpoints"]
        assert "health" in data["api_endpoints"]

    def test_basic_health_endpoint(self, client):
        """Test the basic /health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert "application" in data


class TestHealthRouter:
    """Tests for the health monitoring router."""

    def test_health_status_endpoint(self, client):
        """Test the /api/v1/health/status endpoint."""
        response = client.get("/api/v1/health/status")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "components" in data

    def test_health_components_endpoint(self, client):
        """Test the /api/v1/health/components endpoint."""
        response = client.get("/api/v1/health/components")
        assert response.status_code == 200

        data = response.json()
        assert "components" in data
        assert "total" in data

    def test_health_metrics_endpoint(self, client):
        """Test the /api/v1/health/metrics endpoint."""
        response = client.get("/api/v1/health/metrics")
        assert response.status_code == 200

        data = response.json()
        assert "total_checks" in data

    def test_health_list_endpoint(self, client):
        """Test the /api/v1/health/list endpoint."""
        response = client.get("/api/v1/health/list")
        assert response.status_code == 200

        data = response.json()
        assert "checks" in data
        assert "total" in data
        assert isinstance(data["checks"], list)


class TestMetricsRouter:
    """Tests for the metrics router."""

    def test_metrics_summary_endpoint(self, client):
        """Test the /api/v1/metrics/summary endpoint."""
        response = client.get("/api/v1/metrics/summary")
        assert response.status_code == 200

        data = response.json()
        assert "metrics" in data
        assert "stats" in data  # Updated to match new API

    def test_metrics_performance_endpoint(self, client):
        """Test the /api/v1/metrics/performance endpoint."""
        response = client.get("/api/v1/metrics/performance")
        assert response.status_code == 200

        data = response.json()
        assert "performance_metrics" in data
        assert "api_calls" in data

    def test_metrics_health_endpoint(self, client):
        """Test the /api/v1/metrics/health endpoint."""
        response = client.get("/api/v1/metrics/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data


class TestMCPToolsRouter:
    """Tests for MCP tools router."""

    def test_list_tools_endpoint(self, client):
        """Test the /api/v1/mcp/tools/list endpoint."""
        response = client.get("/api/v1/mcp/tools/list")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Check tool structure
        tool = data[0]
        assert "name" in tool
        assert "description" in tool
        assert "category" in tool

    def test_list_tool_categories_endpoint(self, client):
        """Test the /api/v1/mcp/tools/categories endpoint."""
        response = client.get("/api/v1/mcp/tools/categories")
        assert response.status_code == 200

        data = response.json()
        assert "categories" in data
        assert "total" in data
        assert isinstance(data["categories"], list)

    def test_get_specific_tool_endpoint(self, client):
        """Test getting a specific tool definition."""
        response = client.get("/api/v1/mcp/tools/get_issues_metrics")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "get_issues_metrics"
        assert "description" in data

    def test_get_nonexistent_tool_endpoint(self, client):
        """Test getting a non-existent tool."""
        response = client.get("/api/v1/mcp/tools/nonexistent_tool")
        assert response.status_code == 404


class TestMCPResourcesRouter:
    """Tests for MCP resources router."""

    def test_list_resources_endpoint(self, client):
        """Test the /api/v1/mcp/resources/list endpoint."""
        response = client.get("/api/v1/mcp/resources/list")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Check resource structure
        resource = data[0]
        assert "uri" in resource
        assert "name" in resource
        assert "description" in resource

    def test_list_resource_categories_endpoint(self, client):
        """Test the /api/v1/mcp/resources/categories endpoint."""
        response = client.get("/api/v1/mcp/resources/categories")
        assert response.status_code == 200

        data = response.json()
        assert "categories" in data
        assert "total" in data

    def test_search_resources_endpoint(self, client):
        """Test the /api/v1/mcp/resources/search endpoint."""
        response = client.get("/api/v1/mcp/resources/search?query=github")
        assert response.status_code == 200

        data = response.json()
        assert "query" in data
        assert "results" in data
        assert data["query"] == "github"


class TestAIRouter:
    """Tests for AI router."""

    def test_ai_status_endpoint(self, client):
        """Test the /api/v1/ai/status endpoint."""
        response = client.get("/api/v1/ai/status")
        assert response.status_code == 200

        data = response.json()
        assert "available" in data
        assert "service" in data
        assert "features" in data


class TestMiddleware:
    """Tests for middleware functionality."""

    def test_correlation_id_header(self, client):
        """Test that correlation ID is added to response."""
        response = client.get("/")
        assert "X-Correlation-ID" in response.headers

    def test_response_time_header(self, client):
        """Test that response time is added to response."""
        response = client.get("/")
        assert "X-Response-Time" in response.headers


class TestOpenAPIDocumentation:
    """Tests for OpenAPI documentation."""

    def test_openapi_json_endpoint(self, client):
        """Test that OpenAPI schema is available."""
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200

        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_docs_endpoint(self, client):
        """Test that Swagger UI is available."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_endpoint(self, client):
        """Test that ReDoc is available."""
        response = client.get("/redoc")
        assert response.status_code == 200
