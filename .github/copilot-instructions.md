# GitHub Copilot Instructions - xSwE Agent

## Project Overview

**xSwE Agent** is a sophisticated GitHub Issues monitoring and analytics platform that combines:
- GitHub API integration for issue tracking
- Advanced analytics engine with multiple strategies
- AI-powered insights using Google Gemini 2.5 Flash
- Interactive chart generation
- MCP (Model Context Protocol) server for tool integration

## Architecture & Design Patterns

### Core Patterns Used
- **Repository Pattern**: `GitHubRepository` and `CachedGitHubRepository` for data access
- **Strategy Pattern**: `AnalyticsStrategy` for different analysis approaches
- **Factory Pattern**: `ChartFactory` for generating different chart types
- **Singleton Pattern**: Configuration and settings management
- **Dependency Injection**: Service initialization and management

### Project Structure
```
src/
├── analytics/          # Analytics engine with strategies
├── charts/            # Chart generation (matplotlib, plotly)
├── config/            # Configuration and settings (Pydantic)
├── gemini_integration/# AI integration with Gemini
├── github_monitor/    # GitHub API integration
└── mcp_server/        # MCP server endpoints
```

## Code Style & Standards

### Python Version
- **Target**: Python 3.10+
- **Use modern Python features**: type hints, dataclasses, async/await

### Code Formatting
- **Black**: Line length 88 characters
- **isort**: Import organization with black profile
- **flake8**: Linting with custom rules (see `.flake8`)

### Type Hints
- **Always use type hints** for function parameters and return types
- Use `Optional[T]` for nullable types
- Use `List[T]`, `Dict[K, V]` for collections (or `list[T]`, `dict[K, V]` in Python 3.9+)

### Pydantic Models
- **Use Pydantic V2** (migration completed)
- Use `@field_validator` instead of `@validator`
- Use `model_config` for configuration
- Always provide Field descriptions for documentation

### Error Handling
- Use specific exception types
- Always log errors with context
- Provide meaningful error messages
- Implement retry logic for external APIs

### Async/Await
- Use `async/await` for I/O operations
- GitHub API calls should be async
- Gemini API calls should be async
- Use `asyncio.gather()` for parallel operations

## Testing Standards

### Test Structure
- **pytest** is the test framework
- Place tests in `tests/` directory
- Name test files: `test_<module_name>.py`
- Use fixtures for common setup

### Test Coverage
- **Target**: >90% code coverage
- Every new feature must have tests
- Test happy path and edge cases
- Mock external API calls (GitHub, Gemini)

### Test Patterns
```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture
def sample_fixture():
    """Clear docstring explaining the fixture."""
    return SomeObject()

@pytest.mark.asyncio
async def test_async_function():
    """Test async functions with pytest-asyncio."""
    result = await some_async_function()
    assert result is not None
```

## Common Patterns & Best Practices

### Configuration
```python
from src.config import get_config

settings = get_config()
github_token = settings.github.token
```

### GitHub API Integration
```python
from src.github_monitor import GitHubRepository

repo = GitHubRepository(
    repo_name="owner/repo",
    api_token=settings.github.token
)
issues = repo.get_issues(criteria=SearchCriteria(state="open"))
```

### Caching
```python
from src.github_monitor import CachedGitHubRepository

# Use cached version for better performance
cached_repo = CachedGitHubRepository(
    repo_name="owner/repo",
    api_token=settings.github.token,
    default_ttl=300  # 5 minutes
)
```

### Analytics
```python
from src.analytics import AnalyticsEngine, ProductivityStrategy

engine = AnalyticsEngine(strategy=ProductivityStrategy())
results = await engine.analyze(issues)
```

### Gemini Integration
```python
from src.gemini_integration import GeminiAnalyzer

analyzer = GeminiAnalyzer(api_key=settings.gemini.api_key)
insights = await analyzer.analyze_code(code_snippet)
```

### Chart Generation
```python
from src.charts import ChartFactory, ChartType

chart = ChartFactory.create(
    chart_type=ChartType.TIME_SERIES,
    data=analytics_results
)
chart_image = chart.generate()
```

## Documentation Standards

### Docstrings
Use Google-style docstrings:

```python
def calculate_metrics(issues: List[Issue]) -> Dict[str, float]:
    """Calculate productivity metrics from issues.
    
    Args:
        issues: List of GitHub issues to analyze
        
    Returns:
        Dictionary containing calculated metrics:
        - avg_time: Average resolution time in hours
        - throughput: Issues resolved per day
        
    Raises:
        ValueError: If issues list is empty
        
    Example:
        >>> issues = repo.get_issues()
        >>> metrics = calculate_metrics(issues)
        >>> print(metrics['throughput'])
        2.5
    """
    if not issues:
        raise ValueError("Issues list cannot be empty")
    # implementation...
```

### Comments
- Use comments to explain **why**, not **what**
- Avoid obvious comments
- Use TODO comments for future improvements: `# TODO: Implement caching`

## API Integration Guidelines

### GitHub API
- Always check rate limits
- Implement exponential backoff for retries
- Use pagination for large result sets
- Cache responses when possible

### Gemini API
- Keep prompts clear and structured
- Handle API errors gracefully
- Implement timeout handling
- Log API usage for monitoring

## Security Considerations

### Secrets Management
- Never hardcode API keys or tokens
- Use environment variables or secrets management
- Validate all external inputs
- Sanitize data before logging

### Data Privacy
- Don't log sensitive information
- Mask tokens in logs
- Follow GDPR guidelines for user data

## Performance Optimization

### Caching Strategy
- Use `CachedGitHubRepository` for repeated queries
- Configure appropriate TTLs
- Implement cache invalidation
- Monitor cache hit rates

### Database Queries
- Use indexes on frequently queried fields
- Batch operations when possible
- Implement pagination for large datasets

### Async Operations
- Use `asyncio.gather()` for parallel API calls
- Implement connection pooling
- Set appropriate timeouts

## Common Issues & Solutions

### Rate Limiting
```python
# Always check rate limits before making requests
if repo.is_rate_limited():
    logger.warning("Rate limit reached, waiting...")
    await asyncio.sleep(repo.time_until_reset())
```

### Memory Management
```python
# Process large datasets in chunks
async def process_issues_in_batches(issues, batch_size=100):
    for i in range(0, len(issues), batch_size):
        batch = issues[i:i + batch_size]
        await process_batch(batch)
```

### Error Recovery
```python
# Implement retry logic with exponential backoff
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def fetch_with_retry():
    return await api_call()
```

## Git Workflow

### Branch Naming
- `feature/description` - New features
- `fix/description` - Bug fixes
- `refactor/description` - Code refactoring
- `docs/description` - Documentation updates

### Commit Messages
Follow Conventional Commits:
- `feat: Add new chart type`
- `fix: Resolve rate limiting issue`
- `docs: Update API documentation`
- `refactor: Improve caching logic`
- `test: Add tests for analytics engine`

### PR Guidelines
- Keep PRs focused and small
- Write clear descriptions
- Include tests
- Update documentation
- Wait for CI to pass

## Development Commands

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Format code
black .
isort .

# Lint
flake8 .

# Type check
mypy src/

# Run tests
pytest
pytest --cov=src tests/  # With coverage

# Run specific test
pytest tests/test_analytics.py -v

# Run server
uvicorn src.mcp_server.main:app --reload
```

## Resources & Documentation

- **GitHub API**: https://docs.github.com/en/rest
- **Google Gemini**: https://ai.google.dev/docs
- **Pydantic V2**: https://docs.pydantic.dev/2.0/
- **FastAPI**: https://fastapi.tiangolo.com/
- **MCP Protocol**: https://modelcontextprotocol.io/

## When in Doubt

1. **Check existing code** for similar patterns
2. **Follow the architecture** - respect the design patterns
3. **Write tests first** - TDD when possible
4. **Keep it simple** - KISS principle
5. **Ask for review** - collaboration is key

---

**Remember**: Code quality > Speed. Write maintainable, tested, and documented code.
