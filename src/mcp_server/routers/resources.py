"""
MCP Server - Resources Router
Handles MCP resource discovery and management endpoints.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ...config.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


class ResourceDefinition(BaseModel):
    """MCP resource definition."""

    uri: str = Field(..., description="Resource URI")
    name: str = Field(..., description="Resource name")
    description: str = Field(..., description="Resource description")
    mime_type: str = Field(default="application/json", description="MIME type")
    category: str = Field(default="data", description="Resource category")


# Define available MCP resources
MCP_RESOURCES = [
    ResourceDefinition(
        uri="github://issues",
        name="GitHub Issues",
        description="Access to GitHub repository issues",
        mime_type="application/json",
        category="github",
    ),
    ResourceDefinition(
        uri="github://repository",
        name="Repository Information",
        description="GitHub repository metadata and statistics",
        mime_type="application/json",
        category="github",
    ),
    ResourceDefinition(
        uri="analytics://metrics",
        name="Analytics Metrics",
        description="Calculated analytics and metrics",
        mime_type="application/json",
        category="analytics",
    ),
    ResourceDefinition(
        uri="analytics://reports",
        name="Analytics Reports",
        description="Generated analytics reports",
        mime_type="application/json",
        category="analytics",
    ),
    ResourceDefinition(
        uri="charts://generated",
        name="Generated Charts",
        description="Visualization charts and graphs",
        mime_type="image/png",
        category="visualization",
    ),
    ResourceDefinition(
        uri="health://status",
        name="System Health Status",
        description="Current system health and component status",
        mime_type="application/json",
        category="monitoring",
    ),
    ResourceDefinition(
        uri="metrics://prometheus",
        name="Prometheus Metrics",
        description="Metrics in Prometheus format",
        mime_type="text/plain",
        category="monitoring",
    ),
]


@router.get("/list", response_model=List[ResourceDefinition])
async def list_resources(category: Optional[str] = None):
    """
    List all available MCP resources.

    Args:
        category: Optional category filter

    Returns:
        List of available resources
    """
    if category:
        filtered_resources = [r for r in MCP_RESOURCES if r.category == category]
        return filtered_resources

    return MCP_RESOURCES


@router.get("/categories")
async def list_resource_categories():
    """
    List all resource categories.

    Returns:
        List of unique resource categories
    """
    categories = list(set(resource.category for resource in MCP_RESOURCES))
    return {
        "categories": sorted(categories),
        "total": len(categories),
    }


@router.get("/read")
async def read_resource(
    uri: str,
    app_request: Request,
):
    """
    Read a resource by URI.

    Args:
        uri: Resource URI
        app_request: FastAPI request for accessing app state

    Returns:
        Resource content
    """
    # Verify resource exists
    resource = next((r for r in MCP_RESOURCES if r.uri == uri), None)

    if not resource:
        raise HTTPException(status_code=404, detail=f"Resource not found: {uri}")

    logger.info(f"Reading resource: {uri}")

    try:
        # Route to appropriate handler based on URI
        if uri == "github://issues":
            github_service = app_request.app.state.github_service
            issues = await github_service.get_all_issues()
            return {
                "uri": uri,
                "content": [issue.dict() for issue in issues],
                "mime_type": resource.mime_type,
            }

        elif uri == "github://repository":
            github_service = app_request.app.state.github_service
            summary = await github_service.get_issue_summary()
            return {
                "uri": uri,
                "content": {
                    "name": github_service.repo_name,
                    "statistics": summary,
                },
                "mime_type": resource.mime_type,
            }

        elif uri == "analytics://metrics":
            analytics_engine = app_request.app.state.analytics_engine
            github_service = app_request.app.state.github_service

            issues = await github_service.get_all_issues()
            results = await analytics_engine.analyze(
                issues, github_service.repo_name
            )

            return {
                "uri": uri,
                "content": results,
                "mime_type": resource.mime_type,
            }

        elif uri == "analytics://reports":
            analytics_engine = app_request.app.state.analytics_engine
            github_service = app_request.app.state.github_service

            issues = await github_service.get_all_issues()
            results = await analytics_engine.analyze(
                issues, github_service.repo_name
            )
            summary = await analytics_engine.get_summary_insights(results)

            return {
                "uri": uri,
                "content": summary,
                "mime_type": resource.mime_type,
            }

        elif uri == "health://status":
            from ...utils import get_health_check_registry

            registry = get_health_check_registry()
            results = await registry.check_all()
            overall = await registry.get_system_health()

            return {
                "uri": uri,
                "content": {
                    "overall_status": overall.value,
                    "components": {
                        name: {
                            "status": result.status.value,
                            "message": result.message,
                        }
                        for name, result in results.items()
                    },
                },
                "mime_type": resource.mime_type,
            }

        elif uri == "metrics://prometheus":
            from ...utils import get_metrics_collector

            collector = get_metrics_collector()
            prometheus_text = collector.get_prometheus_format()

            return {
                "uri": uri,
                "content": prometheus_text,
                "mime_type": resource.mime_type,
            }

        elif uri == "charts://generated":
            return {
                "uri": uri,
                "content": {
                    "message": "Chart generation requires specific chart type",
                    "endpoint": "/api/v1/charts/generate/{analysis_type}",
                },
                "mime_type": "application/json",
            }

        else:
            raise HTTPException(
                status_code=501,
                detail=f"Resource reading not implemented: {uri}",
            )

    except Exception as e:
        logger.error(f"Resource read failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to read resource: {str(e)}"
        )


@router.get("/search")
async def search_resources(
    query: str,
    category: Optional[str] = None,
):
    """
    Search for resources.

    Args:
        query: Search query
        category: Optional category filter

    Returns:
        Matching resources
    """
    resources = MCP_RESOURCES

    if category:
        resources = [r for r in resources if r.category == category]

    # Simple text search in name and description
    query_lower = query.lower()
    matching = [
        r
        for r in resources
        if query_lower in r.name.lower() or query_lower in r.description.lower()
    ]

    return {
        "query": query,
        "category": category,
        "results": matching,
        "count": len(matching),
    }


@router.get("/{uri:path}")
async def get_resource_definition(uri: str):
    """
    Get definition for a specific resource.

    Args:
        uri: Resource URI

    Returns:
        Resource definition
    """
    resource = next((r for r in MCP_RESOURCES if r.uri == uri), None)

    if not resource:
        raise HTTPException(status_code=404, detail=f"Resource not found: {uri}")

    return resource
