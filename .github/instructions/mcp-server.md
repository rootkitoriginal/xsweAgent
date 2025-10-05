# MCP Server Module (`src/mcp_server/`)

## Purpose
FastAPI-based MCP (Model Context Protocol) server providing REST API endpoints for all features.

## Architecture

### Main Application (`main.py`)
```python
from fastapi import FastAPI
from .routers import github, analytics, charts
from .services.lifespan import lifespan

app = FastAPI(
    title="xSwE Agent API",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(github.router, prefix="/api/github", tags=["GitHub"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(charts.router, prefix="/api/charts", tags=["Charts"])
```

### Routers Structure
- **github.py**: GitHub API endpoints (issues, search, rate limits)
- **analytics.py**: Analytics endpoints (run strategies, get insights)
- **charts.py**: Chart generation endpoints (create, export)

## Endpoint Patterns

### GET Endpoints
```python
@router.get("/issues")
async def list_issues(
    state: Optional[str] = Query("all", regex="^(open|closed|all)$"),
    labels: Optional[List[str]] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100)
) -> IssuesResponse:
    """List GitHub issues with filtering."""
    criteria = SearchCriteria(state=state, labels=labels)
    issues = await github_service.get_issues(criteria)
    return paginate_response(issues, page, per_page)
```

### POST Endpoints
```python
@router.post("/analytics/run")
async def run_analysis(request: AnalysisRequest) -> AnalysisResponse:
    """Run analytics strategy on issues."""
    strategy = get_strategy(request.strategy_type)
    engine = AnalyticsEngine(strategy)
    results = await engine.analyze(request.issues)
    return AnalysisResponse(results=results)
```

### File Download Endpoints
```python
@router.post("/charts/generate")
async def generate_chart(request: ChartRequest) -> Response:
    """Generate and download chart image."""
    chart_bytes = ChartFactory.create(
        request.chart_type,
        request.data,
        request.config
    )
    return Response(
        content=chart_bytes,
        media_type="image/png",
        headers={"Content-Disposition": "attachment; filename=chart.png"}
    )
```

## Best Practices

### Dependency Injection
```python
from fastapi import Depends

async def get_github_repository() -> GitHubRepository:
    """Dependency for GitHub repository."""
    settings = get_config()
    return CachedGitHubRepository(
        repo_name=settings.github.repo_name,
        api_token=settings.github.token
    )

@router.get("/issues")
async def list_issues(
    repo: GitHubRepository = Depends(get_github_repository)
):
    return await repo.get_issues()
```

### Error Handling
```python
from fastapi import HTTPException, status

@router.get("/issues/{issue_number}")
async def get_issue(issue_number: int):
    try:
        issue = await github_service.get_issue(issue_number)
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Issue #{issue_number} not found"
            )
        return issue
    except GitHubAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub API error: {str(e)}"
        )
```

### Request Validation
```python
from pydantic import BaseModel, Field, field_validator

class AnalysisRequest(BaseModel):
    strategy_type: str = Field(..., pattern="^(productivity|status|trend)$")
    date_range: Optional[DateRange] = None
    
    @field_validator("date_range")
    @classmethod
    def validate_date_range(cls, v):
        if v and v.end < v.start:
            raise ValueError("end date must be after start date")
        return v
```

### Response Models
```python
class IssueResponse(BaseModel):
    number: int
    title: str
    state: str
    created_at: datetime
    
    model_config = {"from_attributes": True}

class PaginatedResponse(BaseModel):
    items: List[IssueResponse]
    total: int
    page: int
    per_page: int
    pages: int
```

## Lifespan Management

### Service Initialization
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting xSwE Agent API...")
    
    # Initialize services
    app.state.github_service = await init_github_service()
    app.state.analytics_engine = await init_analytics_engine()
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await app.state.github_service.close()
```

## Testing

### Test Client
```python
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    return TestClient(app)

def test_list_issues(client):
    response = client.get("/api/github/issues?state=open")
    assert response.status_code == 200
    assert "items" in response.json()
```

### Async Testing
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_run_analysis():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/analytics/run",
            json={"strategy_type": "productivity"}
        )
        assert response.status_code == 200
```

### Mock Dependencies
```python
def mock_github_repository():
    return Mock(spec=GitHubRepository)

app.dependency_overrides[get_github_repository] = mock_github_repository
```

## CORS Configuration
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"]
)
```

## OpenAPI Documentation
```python
@router.post(
    "/analytics/run",
    summary="Run analytics strategy",
    description="Execute analytics strategy on GitHub issues data",
    responses={
        200: {"description": "Analysis results"},
        400: {"description": "Invalid request"},
        502: {"description": "External API error"}
    }
)
async def run_analysis(request: AnalysisRequest) -> AnalysisResponse:
    pass
```
