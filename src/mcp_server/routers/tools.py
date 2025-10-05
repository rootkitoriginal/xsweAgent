"""
MCP Server - Tools Router
Handles MCP tool management and execution endpoints.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ...config.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


class ToolDefinition(BaseModel):
    """MCP tool definition."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Tool parameters schema"
    )
    category: str = Field(default="general", description="Tool category")


class ToolExecutionRequest(BaseModel):
    """Tool execution request."""

    tool: str = Field(..., description="Tool name to execute")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Tool parameters"
    )


# Define available MCP tools
MCP_TOOLS = [
    ToolDefinition(
        name="get_issues_metrics",
        description="Get metrics and analytics for GitHub issues",
        parameters={
            "repository": {"type": "string", "required": False},
            "state": {"type": "string", "enum": ["open", "closed", "all"]},
        },
        category="github",
    ),
    ToolDefinition(
        name="generate_chart",
        description="Generate visualization charts from data",
        parameters={
            "chart_type": {"type": "string", "required": True},
            "analysis_type": {"type": "string", "required": True},
        },
        category="charts",
    ),
    ToolDefinition(
        name="analyze_code",
        description="Analyze code with AI and provide insights",
        parameters={
            "code": {"type": "string", "required": True},
            "language": {"type": "string", "required": False},
        },
        category="ai",
    ),
    ToolDefinition(
        name="get_productivity_report",
        description="Generate comprehensive productivity report",
        parameters={
            "time_range": {"type": "string", "required": False},
        },
        category="analytics",
    ),
    ToolDefinition(
        name="analyze_issues",
        description="AI-powered issue analysis and recommendations",
        parameters={
            "issue_numbers": {"type": "array", "items": {"type": "integer"}},
        },
        category="ai",
    ),
    ToolDefinition(
        name="check_system_health",
        description="Check system health and component status",
        parameters={},
        category="monitoring",
    ),
]


@router.get("/list", response_model=List[ToolDefinition])
async def list_tools(category: Optional[str] = None):
    """
    List all available MCP tools.

    Args:
        category: Optional category filter

    Returns:
        List of available tools
    """
    if category:
        filtered_tools = [t for t in MCP_TOOLS if t.category == category]
        return filtered_tools

    return MCP_TOOLS


@router.get("/categories")
async def list_tool_categories():
    """
    List all tool categories.

    Returns:
        List of unique tool categories
    """
    categories = list(set(tool.category for tool in MCP_TOOLS))
    return {
        "categories": sorted(categories),
        "total": len(categories),
    }


@router.get("/{tool_name}")
async def get_tool_definition(tool_name: str):
    """
    Get definition for a specific tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Tool definition
    """
    tool = next((t for t in MCP_TOOLS if t.name == tool_name), None)

    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")

    return tool


@router.post("/call")
async def call_tool(
    request: ToolExecutionRequest,
    app_request: Request,
):
    """
    Execute an MCP tool.

    Args:
        request: Tool execution request
        app_request: FastAPI request for accessing app state

    Returns:
        Tool execution result
    """
    # Verify tool exists
    tool = next((t for t in MCP_TOOLS if t.name == request.tool), None)

    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {request.tool}")

    logger.info(f"Executing tool: {request.tool}", parameters=request.parameters)

    try:
        # Route to appropriate handler based on tool
        if request.tool == "get_issues_metrics":
            from .github import get_all_issues, get_issues_summary

            github_service = app_request.app.state.github_service
            summary = await github_service.get_issue_summary()
            return {
                "tool": request.tool,
                "status": "success",
                "result": summary,
            }

        elif request.tool == "generate_chart":
            return {
                "tool": request.tool,
                "status": "success",
                "message": "Chart generation requires direct API call to /api/v1/charts/generate",
            }

        elif request.tool == "analyze_code":
            return {
                "tool": request.tool,
                "status": "success",
                "message": "Code analysis requires direct API call to /api/v1/ai/analyze/code",
            }

        elif request.tool == "get_productivity_report":
            analytics_engine = app_request.app.state.analytics_engine
            github_service = app_request.app.state.github_service

            issues = await github_service.get_all_issues()
            results = await analytics_engine.analyze(
                issues, github_service.repo_name
            )

            return {
                "tool": request.tool,
                "status": "success",
                "result": results,
            }

        elif request.tool == "analyze_issues":
            return {
                "tool": request.tool,
                "status": "success",
                "message": "Issue analysis requires direct API call to /api/v1/ai/analyze/issues",
            }

        elif request.tool == "check_system_health":
            from ...utils import get_health_check_registry

            registry = get_health_check_registry()
            results = await registry.check_all()
            overall = await registry.get_overall_status()

            return {
                "tool": request.tool,
                "status": "success",
                "result": {
                    "overall_status": overall.value,
                    "components": {
                        name: result.status.value for name, result in results.items()
                    },
                },
            }

        else:
            raise HTTPException(
                status_code=501,
                detail=f"Tool execution not implemented: {request.tool}",
            )

    except Exception as e:
        logger.error(f"Tool execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Tool execution failed: {str(e)}"
        )


@router.get("/statistics/usage")
async def get_tool_usage_statistics():
    """
    Get tool usage statistics.

    Returns:
        Usage statistics for all tools
    """
    from ...utils import get_metrics_collector

    collector = get_metrics_collector()
    counters = collector.get_counters()

    # Filter tool-related metrics
    tool_calls = {
        k: v for k, v in counters.items() if "tool_call" in k.lower()
    }

    return {
        "tool_calls": tool_calls,
        "total_calls": sum(tool_calls.values()),
    }
