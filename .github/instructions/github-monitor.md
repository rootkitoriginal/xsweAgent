# GitHub Monitor Module (`src/github_monitor/`)

## Purpose
GitHub API integration with caching, rate limiting, and pagination support.

## Key Components

### Repository Pattern
```python
class GitHubRepository:
    """GitHub API client with rate limiting and pagination."""
    
    async def get_issues(self, criteria: SearchCriteria) -> List[Issue]:
        # Check rate limit
        if self.is_rate_limited():
            await self._wait_for_rate_limit()
        
        # Fetch with pagination
        issues = await self._fetch_all_pages(criteria)
        return issues
```

### Caching (Decorator Pattern)
```python
class CachedGitHubRepository:
    """Cached wrapper for GitHubRepository with TTL support."""
    
    def __init__(self, repo_name: str, api_token: str, default_ttl: int = 300):
        self._repository = GitHubRepository(repo_name, api_token)
        self._cache = {}
```

## Best Practices

### Rate Limiting
- Always check `is_rate_limited()` before requests
- Use `time_until_reset()` to wait appropriately
- Update rate limit info from response headers

### Retry Logic
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def _fetch_with_retry(self, endpoint: str) -> Dict:
    return await self._make_request(endpoint)
```

### Security
- Never log API tokens (mask with `_mask_token()`)
- Use Bearer token authentication
- Store tokens in environment variables

## Testing
```python
@pytest.fixture
def mock_github_api(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = [{"number": 1, "title": "Test"}]
    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)
    return mock_response
```
