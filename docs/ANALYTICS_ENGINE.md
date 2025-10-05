# Analytics Engine Documentation

The Analytics Engine provides comprehensive analysis of GitHub issues data using the Strategy Pattern with integrated infrastructure utilities.

## Overview

The Analytics Engine coordinates multiple analysis strategies to provide insights into:
- **Productivity**: Team throughput, velocity, cycle times
- **Velocity**: Development velocity trends over time
- **Burndown**: Milestone progress tracking
- **Quality**: Bug ratios, quality metrics

All strategies include:
- ✅ Automatic retry on failures
- ✅ Metrics collection for monitoring
- ✅ Circuit breaker protection
- ✅ Structured logging with correlation IDs

## Quick Start

```python
from src.analytics.engine import create_analytics_engine
from src.github_monitor.models import Issue

# Create analytics engine with default strategies
engine = await create_analytics_engine()

# Analyze issues
results = await engine.analyze(
    issues=my_issues,
    repository_name="owner/repo"
)

# Access results
for analysis_type, result in results.items():
    print(f"{analysis_type}: {result.summary}")
    print(f"Score: {result.score}")
    for rec in result.recommendations:
        print(f"  - {rec}")
```

## Architecture

### Strategy Pattern

The engine uses the Strategy Pattern for different types of analysis:

```
AnalyticsEngine
├── ProductivityAnalysisStrategy
├── VelocityAnalysisStrategy
├── BurndownAnalysisStrategy
└── QualityAnalysisStrategy
```

Each strategy:
1. Implements `AnalysisStrategy` interface
2. Has `@retry_with_policy` for fault tolerance
3. Has `@track_api_calls` for metrics
4. Returns `AnalysisResult` with standardized format

### Data Flow

```
Issues → AnalyticsEngine → Strategies → Results
                ↓              ↓          ↓
           Filtering      Analytics   Metrics
           Validation     Processing  Logging
           Context        Retry       Cache
```

## Configuration

### AnalyticsConfiguration

Configure engine behavior:

```python
from src.analytics.engine import AnalyticsConfiguration, AnalysisType

config = AnalyticsConfiguration(
    enabled_analyses={
        AnalysisType.PRODUCTIVITY,
        AnalysisType.VELOCITY,
        AnalysisType.QUALITY,
    },
    time_window_days=90,              # Analysis time window
    minimum_issues_for_analysis=5,   # Minimum issues required
    velocity_calculation_period=14,   # Days for velocity
    trend_analysis_periods=4,         # Periods for trends
    cache_results=True,               # Enable caching
    cache_ttl_minutes=30,             # Cache TTL
    slow_resolution_threshold_days=30, # Threshold for slow issues
    high_activity_threshold=10,       # Comments threshold
)

engine = await create_analytics_engine(configuration=config)
```

## Analysis Strategies

### 1. Productivity Analysis

Analyzes team productivity metrics.

**Metrics:**
- Total issues created/closed
- Completion rate
- Daily creation/closure averages
- Velocity (issues per day)
- Average cycle time
- Median cycle time
- Work in progress (WIP)
- Throughput ratio

**Example:**
```python
from src.analytics.strategies import ProductivityAnalysisStrategy

strategy = ProductivityAnalysisStrategy()
result = await strategy.analyze(issues, days_back=30)

print(f"Velocity: {result.metrics['velocity']} issues/day")
print(f"Completion rate: {result.metrics['completion_rate_percent']}%")
print(f"Average cycle time: {result.metrics['avg_resolution_time_days']} days")
```

**Recommendations Generated:**
- Low completion rate warnings
- High WIP alerts
- Long cycle time notifications

### 2. Velocity Analysis

Analyzes development velocity trends over time.

**Metrics:**
- Weekly velocity data
- Average velocity
- Velocity trend (improving/declining/stable)
- Peak and lowest velocity
- Net change per week

**Example:**
```python
from src.analytics.strategies import VelocityAnalysisStrategy

strategy = VelocityAnalysisStrategy()
result = await strategy.analyze(issues, weeks_back=8)

print(f"Average velocity: {result.metrics['average_velocity']} issues/week")
print(f"Trend: {result.metrics['velocity_trend']}")
```

**Recommendations Generated:**
- Declining velocity warnings
- Low velocity alerts

### 3. Burndown Analysis

Analyzes milestone progress and burndown.

**Metrics:**
- Total issues in milestone
- Completed issues
- Remaining issues
- Completion rate
- Daily burndown data
- Ideal completion rate

**Example:**
```python
from src.analytics.strategies import BurndownAnalysisStrategy

strategy = BurndownAnalysisStrategy()
result = await strategy.analyze(issues, milestone="v2.0")

print(f"Progress: {result.metrics['completed_issues']}/{result.metrics['total_issues']}")
print(f"Completion: {result.metrics['completion_rate_percent']}%")
```

**Recommendations Generated:**
- Milestone at-risk warnings
- Scope reduction suggestions

### 4. Quality Analysis

Analyzes code quality indicators from issues.

**Metrics:**
- Bug count and ratio
- Feature count
- Priority distribution
- Critical issues open
- Average bug fix time
- Quality score (0-100)

**Example:**
```python
from src.analytics.strategies import QualityAnalysisStrategy

strategy = QualityAnalysisStrategy()
result = await strategy.analyze(issues)

print(f"Quality score: {result.metrics['quality_score']}/100")
print(f"Bug ratio: {result.metrics['bug_ratio_percent']}%")
print(f"Critical open: {result.metrics['critical_issues_open']}")
```

**Recommendations Generated:**
- High bug ratio alerts
- Critical issue warnings
- Long bug fix time notifications

## Custom Strategies

Create custom analysis strategies:

```python
from src.analytics.strategies import (
    AnalysisStrategy, 
    AnalysisType, 
    AnalysisResult
)
from src.utils import retry_with_policy, track_api_calls, RetryPolicies

class CustomAnalysisStrategy(AnalysisStrategy):
    """Custom analysis strategy."""
    
    def get_analysis_type(self) -> AnalysisType:
        return AnalysisType.CUSTOM  # Define custom type
    
    @retry_with_policy(RetryPolicies.ANALYTICS)
    @track_api_calls('analytics_custom')
    async def analyze(self, issues, **kwargs):
        # Custom analysis logic
        data = {
            "custom_metric": len(issues) * 2,
            "another_metric": 42,
        }
        
        return AnalysisResult(
            analysis_type=self.get_analysis_type(),
            data=data,
            summary="Custom analysis completed",
            recommendations=["Consider X", "Review Y"],
            score=0.85,
        )

# Register with engine
engine = await create_analytics_engine()
engine.register_strategy(CustomAnalysisStrategy())

# Use in analysis
results = await engine.analyze(issues, "repo")
```

## Caching

The engine includes built-in result caching:

```python
# Enable caching (default)
config = AnalyticsConfiguration(
    cache_results=True,
    cache_ttl_minutes=30
)

engine = await create_analytics_engine(configuration=config)

# First call: performs analysis
results1 = await engine.analyze(issues, "repo")

# Second call: uses cache (if within TTL)
results2 = await engine.analyze(issues, "repo")  # Fast!

# Clear cache manually
engine.clear_cache()

# Get cache statistics
stats = engine.get_cache_stats()
print(f"Cached results: {stats['total_cached_results']}")
```

## Error Handling

The engine provides comprehensive error handling:

### Automatic Retry

All strategies automatically retry on failures:

```python
# Strategies retry up to 3 times (configurable)
# with 5-second wait between attempts
result = await strategy.analyze(issues)  # Retries automatically
```

### Circuit Breaker

Can be added for external API protection:

```python
from src.utils import circuit_breaker, CircuitBreakerPolicies

@circuit_breaker(name="analytics", policy=CircuitBreakerPolicies.DEFAULT)
async def run_analytics():
    engine = await create_analytics_engine()
    return await engine.analyze(issues, "repo")
```

### Graceful Degradation

Engine continues even if some strategies fail:

```python
# If one strategy fails, others still run
results = await engine.analyze(issues, "repo")
# Returns results from successful strategies only
```

## Monitoring and Metrics

### Built-in Metrics

The engine automatically collects metrics:

```python
from src.utils import get_metrics_collector

collector = get_metrics_collector()

# Check analytics metrics
engine_calls = collector.get_counter("analytics_engine_calls_total", status="success")
productivity_calls = collector.get_counter("analytics_productivity_calls_total")

# Get timing statistics
timing = collector.get_timer_stats("analytics_engine_call_duration")
print(f"Average duration: {timing['avg_ms']}ms")
```

### Available Metrics

- `analytics_engine_calls_total`: Total engine calls (success/error)
- `analytics_<strategy>_calls_total`: Per-strategy calls
- `analytics_engine_call_duration`: Engine call duration
- `analytics_<strategy>_call_duration`: Per-strategy duration
- `analytics_insufficient_data`: Insufficient data count
- `analytics_empty_window`: Empty time window count
- `analytics_last_run_count`: Last run result count

### Logging

All operations include structured logging:

```python
# Logs include correlation IDs for tracing
await engine.analyze(issues, "repo")

# Log output:
# INFO: Starting analysis correlation_id=abc-123 repository=owner/repo
# INFO: Analyzing productivity for 50 issues
# INFO: Completed analysis correlation_id=abc-123 analysis_count=4
```

## Health Checks

Register health checks for the analytics system:

```python
from src.utils import register_health_check

async def check_analytics_engine():
    """Check if analytics engine is operational."""
    try:
        engine = await create_analytics_engine()
        return len(engine.get_registered_strategies()) > 0
    except Exception:
        return False

register_health_check("analytics_engine", check_analytics_engine)
```

## Advanced Usage

### Parallel Analysis

Strategies run concurrently for performance:

```python
# All enabled strategies run in parallel
results = await engine.analyze(issues, "repo")
# Uses asyncio.gather() internally
```

### Context Information

Access analysis context:

```python
results = await engine.analyze(issues, "repo")

# Each result includes context
for name, result in results.items():
    print(f"Analysis: {name}")
    print(f"Timestamp: {result.timestamp}")
    print(f"Metadata: {result.metadata}")
```

### Summary Insights

Get high-level insights:

```python
results = await engine.analyze(issues, "repo")
insights = await engine.get_summary_insights(results)

print(f"Overall health: {insights['overall_health']}")
print(f"Key metrics: {insights['key_metrics']}")
print(f"Recommendations: {insights['recommendations']}")
print(f"Alerts: {insights['alerts']}")
```

## Testing

### Test Analytics Engine

```python
import pytest
from src.analytics.engine import create_analytics_engine

@pytest.mark.asyncio
async def test_analytics():
    engine = await create_analytics_engine()
    results = await engine.analyze(test_issues, "test/repo")
    
    assert "productivity" in results
    assert results["productivity"].score is not None
```

### Test Custom Strategy

```python
@pytest.mark.asyncio
async def test_custom_strategy():
    strategy = CustomAnalysisStrategy()
    result = await strategy.analyze(test_issues)
    
    assert result.summary
    assert result.data
    assert result.recommendations
```

### Mock Infrastructure

```python
from unittest.mock import patch

@pytest.mark.asyncio
async def test_with_metrics():
    with patch('src.utils.get_metrics_collector') as mock:
        # Test with mocked metrics
        pass
```

## Performance Optimization

### Time Window

Limit analysis time window for large datasets:

```python
config = AnalyticsConfiguration(
    time_window_days=30  # Analyze last 30 days only
)
```

### Selective Strategies

Enable only needed strategies:

```python
config = AnalyticsConfiguration(
    enabled_analyses={
        AnalysisType.PRODUCTIVITY,
        AnalysisType.QUALITY,
    }
)
```

### Caching

Use caching for repeated analyses:

```python
config = AnalyticsConfiguration(
    cache_results=True,
    cache_ttl_minutes=60
)
```

## Best Practices

1. **Use appropriate time windows**: Balance between data volume and analysis depth
2. **Enable caching**: Reduce computation for repeated analyses
3. **Monitor metrics**: Track performance and errors
4. **Handle empty results**: Check if analysis returned results
5. **Configure thresholds**: Adjust thresholds for your project
6. **Register health checks**: Monitor analytics availability
7. **Use correlation IDs**: Trace requests through the system

## Troubleshooting

### No Results Returned

Check:
- Minimum issues threshold (default: 5)
- Time window configuration
- Issue data quality (created_at, closed_at)

### Poor Performance

Optimize:
- Reduce time window
- Enable caching
- Disable unused strategies
- Filter issues before analysis

### Inconsistent Metrics

Verify:
- Issue data completeness
- Time zone consistency
- Calculation periods

## Examples

See `examples/analytics_with_infrastructure.py` for a complete demonstration.

## API Reference

### AnalyticsEngine

```python
class AnalyticsEngine:
    async def analyze(
        issues: List[Issue],
        repository_name: str,
        custom_config: Optional[AnalyticsConfiguration] = None
    ) -> Dict[str, AnalysisResult]
    
    def register_strategy(strategy: AnalysisStrategy) -> None
    def unregister_strategy(analysis_type: AnalysisType) -> bool
    def get_registered_strategies() -> List[AnalysisType]
    def clear_cache() -> None
    def get_cache_stats() -> Dict[str, int]
    async def get_summary_insights(results: Dict[str, AnalysisResult]) -> Dict[str, Any]
```

### AnalysisResult

```python
@dataclass
class AnalysisResult:
    analysis_type: AnalysisType
    timestamp: datetime
    data: Dict[str, Any]
    summary: str
    recommendations: List[str]
    metadata: Optional[Dict[str, Any]]
    score: Optional[float]
    metrics: Optional[Dict[str, Any]]
    details: Optional[Dict[str, Any]]
    context: Optional[Any]
```

## Further Reading

- [Infrastructure Documentation](INFRASTRUCTURE.md)
- [GitHub Monitor Integration](../src/github_monitor/README.md)
- [Chart Generation](../src/charts/README.md)
