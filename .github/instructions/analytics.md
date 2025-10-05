# Analytics Module (`src/analytics/`)

## Purpose
Analytics engine with multiple strategies for analyzing GitHub issues data.

## Key Patterns

### Strategy Pattern
```python
class AnalyticsStrategy(Protocol):
    async def execute(self, issues: List[Issue]) -> AnalysisResult:
        """Execute analysis strategy."""
        ...

class ProductivityStrategy(AnalyticsStrategy):
    """Calculate productivity metrics: time-to-close, throughput, velocity."""
    async def execute(self, issues: List[Issue]) -> AnalysisResult:
        # Calculate metrics
        avg_time = calculate_average_resolution_time(issues)
        throughput = calculate_throughput(issues)
        return AnalysisResult(data={"avg_time": avg_time, "throughput": throughput})
```

### Common Metrics
- **Productivity**: avg_time_to_close, throughput, velocity, lead_time
- **Quality**: bug_density, reopen_rate, first_response_time
- **Workload**: open_issues, backlog_age, assignment_distribution

## Best Practices
- Always validate input data (empty lists, missing fields)
- Use pandas/numpy for large datasets
- Return structured `AnalysisResult` objects
- Handle timezone-aware datetime objects
- Cache expensive calculations

## Testing
```python
@pytest.fixture
def sample_issues():
    return [Issue(number=1, state="closed", created_at="2024-01-01", closed_at="2024-01-02")]

async def test_strategy(sample_issues):
    strategy = ProductivityStrategy()
    result = await strategy.execute(sample_issues)
    assert result.data["avg_time"] > 0
```
