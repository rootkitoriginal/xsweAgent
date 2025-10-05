# Infrastructure Utilities Documentation

This document describes the infrastructure utilities available in xSwE Agent for building robust, production-ready analytics.

## Overview

The infrastructure utilities provide:
- **Retry Mechanism**: Automatic retry with configurable policies and exponential backoff
- **Circuit Breaker**: Protect against cascading failures in external dependencies
- **Metrics Collection**: Track performance and operational metrics
- **Health Checks**: Monitor system health and dependencies
- **Custom Exceptions**: Hierarchical exception handling

## Table of Contents

- [Retry Mechanism](#retry-mechanism)
- [Circuit Breaker](#circuit-breaker)
- [Metrics Collection](#metrics-collection)
- [Health Checks](#health-checks)
- [Exceptions](#exceptions)
- [Integration Examples](#integration-examples)

---

## Retry Mechanism

### Overview

The retry mechanism automatically retries failed operations with configurable policies and exponential backoff.

### Features

- Configurable retry policies (max attempts, wait strategy, backoff)
- Exponential and fixed wait strategies
- Exception type filtering
- Automatic logging of retry attempts

### Predefined Policies

#### `RetryPolicies.GITHUB_API`
For GitHub API calls with exponential backoff:
- Max attempts: 5
- Wait: 2-60 seconds (exponential, 2x multiplier)
- Exceptions: `GitHubAPIException`

#### `RetryPolicies.GEMINI_API`
For Gemini API calls with shorter backoff:
- Max attempts: 3
- Wait: 1-30 seconds (exponential, 2x multiplier)
- Exceptions: `GeminiException`

#### `RetryPolicies.ANALYTICS`
For analytics processing with fixed wait:
- Max attempts: 3
- Wait: 5 seconds (fixed)
- Exceptions: All exceptions

#### `RetryPolicies.DEFAULT`
General purpose retry:
- Max attempts: 3
- Wait: 1-10 seconds (exponential, 2x multiplier)
- Exceptions: All exceptions

### Usage

```python
from src.utils import retry_with_policy, RetryPolicies

# Use predefined policy
@retry_with_policy(RetryPolicies.GITHUB_API)
async def fetch_github_issues():
    # API call that may fail
    pass

# Create custom policy
from src.utils import RetryPolicy

custom_policy = RetryPolicy(
    max_attempts=5,
    wait_strategy="exponential",
    wait_min=2.0,
    wait_max=30.0,
    multiplier=2.0,
    exception_types=(ConnectionError,)
)

@retry_with_policy(custom_policy)
async def my_function():
    # Operation to retry
    pass
```

---

## Circuit Breaker

### Overview

Circuit breaker pattern prevents cascading failures by opening the circuit after a threshold of failures, allowing the system to fail fast.

### States

- **CLOSED**: Normal operation, all calls go through
- **OPEN**: Circuit broken, calls fail immediately
- **HALF_OPEN**: Testing recovery, limited calls allowed

### Features

- Automatic state transitions based on failures/successes
- Configurable failure and success thresholds
- Timeout before attempting recovery
- Thread-safe operation with async locks

### Predefined Policies

#### `CircuitBreakerPolicies.GITHUB_API`
- Failure threshold: 5
- Success threshold: 2
- Timeout: 60 seconds

#### `CircuitBreakerPolicies.GEMINI_API`
- Failure threshold: 3
- Success threshold: 2
- Timeout: 30 seconds

#### `CircuitBreakerPolicies.DEFAULT`
- Failure threshold: 5
- Success threshold: 2
- Timeout: 60 seconds

### Usage

```python
from src.utils import circuit_breaker, CircuitBreakerPolicies

@circuit_breaker(name="github_api", policy=CircuitBreakerPolicies.GITHUB_API)
async def call_github_api():
    # API call
    pass

# Manual circuit breaker management
from src.utils import get_circuit_breaker

breaker = get_circuit_breaker("github_api", CircuitBreakerPolicies.GITHUB_API)
state = breaker.get_state()  # Get current state
breaker.reset()  # Manually reset circuit
```

---

## Metrics Collection

### Overview

In-memory metrics collection for monitoring application performance and operations.

### Metric Types

#### Counter
Monotonically increasing value for counting events:
```python
from src.utils import get_metrics_collector

collector = get_metrics_collector()
collector.increment_counter("api_calls", 1.0, endpoint="github")
count = collector.get_counter("api_calls", endpoint="github")
```

#### Gauge
Point-in-time value that can increase or decrease:
```python
collector.set_gauge("active_connections", 42.0)
value = collector.get_gauge("active_connections")
```

#### Histogram
Statistical distribution of values:
```python
collector.observe_histogram("response_size_bytes", 1024.0)
stats = collector.get_histogram_stats("response_size_bytes")
# Returns: count, sum, min, max, avg
```

#### Timer
Track timing/duration measurements:
```python
collector.record_timing("api_call_duration", 123.5, endpoint="github")
stats = collector.get_timer_stats("api_call_duration", endpoint="github")
# Returns: count, total_ms, min_ms, max_ms, avg_ms
```

### Decorators

#### Track API Calls
Automatically track API call success/failure and timing:

```python
from src.utils import track_api_calls

@track_api_calls('github')
async def fetch_issues():
    # API call
    pass

# Automatically records:
# - github_calls_total (counter with status=success/error)
# - github_call_duration (timer in milliseconds)
```

### Usage Examples

```python
from src.utils import get_metrics_collector, track_api_calls

# Get the global collector
collector = get_metrics_collector()

# Track counters
collector.increment_counter("requests", 1.0, method="GET")
collector.increment_counter("requests", 1.0, method="POST")

# Track gauges
collector.set_gauge("queue_size", 15.0)

# Track histograms
for value in [100, 150, 200, 180, 120]:
    collector.observe_histogram("request_size", value)

# Get statistics
stats = collector.get_histogram_stats("request_size")
print(f"Average: {stats['avg']}, Min: {stats['min']}, Max: {stats['max']}")

# Get all metrics
all_metrics = collector.get_all_metrics()
print(all_metrics)

# Reset metrics
collector.reset()
```

---

## Health Checks

### Overview

Health check system for monitoring service availability and dependencies.

### Health Status

- `HEALTHY`: Service is operational
- `DEGRADED`: Service has issues but is functional
- `UNHEALTHY`: Service is not operational
- `UNKNOWN`: Health status cannot be determined

### Features

- Async health check execution
- Timeout protection for checks
- Concurrent check execution
- Overall system health calculation

### Usage

```python
from src.utils import register_health_check, get_health_registry

# Register a health check
async def check_database():
    # Check if database is accessible
    try:
        # Perform actual check
        return True
    except Exception:
        return False

register_health_check("database", check_database, timeout=5.0)

# Run all health checks
registry = get_health_registry()
results = await registry.check_all()

for name, result in results.items():
    print(f"{name}: {result.status.value} - {result.message}")

# Get overall system status
overall = await registry.get_overall_status()
print(f"System: {overall.value}")
```

### Creating Custom Health Checks

```python
from src.utils import HealthCheck, HealthCheckResult, HealthStatus

class DatabaseHealthCheck(HealthCheck):
    def __init__(self, db_client):
        super().__init__(name="database", timeout=5.0)
        self.db = db_client
    
    async def _perform_check(self) -> HealthCheckResult:
        try:
            # Perform database ping
            await self.db.ping()
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                message="Database is responsive"
            )
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Database error: {str(e)}"
            )

# Register custom check
registry = get_health_registry()
registry.register(DatabaseHealthCheck(db_client))
```

---

## Exceptions

### Exception Hierarchy

```
XSWEException (base)
├── GitHubAPIException
│   └── RateLimitException
├── GeminiException
├── AnalyticsException
├── ConfigurationException
└── CircuitBreakerException
```

### Usage

```python
from src.utils import GitHubAPIException, RateLimitException

async def fetch_data():
    try:
        # API call
        pass
    except RateLimitException as e:
        # Handle rate limiting specifically
        await asyncio.sleep(60)
    except GitHubAPIException as e:
        # Handle other GitHub errors
        logger.error(f"GitHub API error: {e}")
```

---

## Integration Examples

### Complete Analytics Integration

The analytics engine integrates all infrastructure utilities:

```python
from src.analytics.engine import create_analytics_engine, AnalyticsConfiguration
from src.utils import get_metrics_collector, get_health_registry

# Create analytics engine (strategies have retry and metrics built-in)
engine = await create_analytics_engine()

# Run analysis (automatic retry, metrics, logging)
results = await engine.analyze(issues, "my/repo")

# Check metrics collected
collector = get_metrics_collector()
analytics_calls = collector.get_counter("analytics_engine_calls_total", status="success")
print(f"Successful analytics runs: {analytics_calls}")

# Verify health
registry = get_health_registry()
health_results = await registry.check_all()
```

### Custom Strategy with Infrastructure

```python
from src.analytics.strategies import AnalysisStrategy, AnalysisType, AnalysisResult
from src.utils import retry_with_policy, track_api_calls, RetryPolicies

class MyCustomStrategy(AnalysisStrategy):
    def get_analysis_type(self) -> AnalysisType:
        return AnalysisType.CUSTOM
    
    @retry_with_policy(RetryPolicies.ANALYTICS)
    @track_api_calls('analytics_custom')
    async def analyze(self, issues, **kwargs):
        # Analysis logic with automatic retry and metrics
        return AnalysisResult(
            analysis_type=self.get_analysis_type(),
            summary="Custom analysis complete"
        )
```

### Combining Retry and Circuit Breaker

```python
from src.utils import retry_with_policy, circuit_breaker, RetryPolicies, CircuitBreakerPolicies

@circuit_breaker(name="external_api", policy=CircuitBreakerPolicies.DEFAULT)
@retry_with_policy(RetryPolicies.DEFAULT)
async def call_external_api():
    # This function has:
    # 1. Retry on transient failures
    # 2. Circuit breaker to fail fast when service is down
    pass
```

---

## Best Practices

### 1. Choose Appropriate Policies

- Use `GITHUB_API` policy for GitHub API calls
- Use `GEMINI_API` policy for AI service calls
- Use `ANALYTICS` policy for internal processing
- Create custom policies for specific needs

### 2. Combine Decorators Wisely

Order matters when stacking decorators:

```python
# Recommended order:
@circuit_breaker(...)      # Outermost: fail fast when circuit is open
@retry_with_policy(...)    # Middle: retry transient failures
@track_api_calls(...)      # Innermost: track all attempts
async def my_function():
    pass
```

### 3. Monitor Metrics

Regularly check metrics to identify issues:

```python
collector = get_metrics_collector()

# Check error rates
total = collector.get_counter("api_calls_total", status="success")
errors = collector.get_counter("api_calls_total", status="error")
error_rate = errors / (total + errors) if (total + errors) > 0 else 0

if error_rate > 0.1:  # More than 10% errors
    logger.warning(f"High error rate: {error_rate:.1%}")
```

### 4. Use Health Checks for Critical Dependencies

```python
# Register checks for all external dependencies
register_health_check("github_api", check_github_connectivity)
register_health_check("gemini_api", check_gemini_connectivity)
register_health_check("database", check_database_connection)
```

### 5. Log with Correlation IDs

Use correlation IDs to trace requests through the system:

```python
import uuid
from src.config.logging_config import get_logger

logger = get_logger(__name__)
correlation_id = str(uuid.uuid4())
logger = logger.bind(correlation_id=correlation_id)

logger.info("Processing started", correlation_id=correlation_id)
```

---

## Testing Infrastructure

The infrastructure utilities include comprehensive tests:

```bash
# Run infrastructure tests
pytest tests/test_utils.py -v

# Run all tests including analytics integration
pytest tests/test_analytics.py tests/test_utils.py -v
```

---

## Performance Considerations

### Retry Overhead

Retries add latency on failures. Configure policies appropriately:
- Use shorter backoff for low-latency operations
- Use exponential backoff for external APIs
- Limit max attempts to prevent excessive delays

### Circuit Breaker Memory

Circuit breakers maintain state in memory. Reset periodically if needed:

```python
breaker = get_circuit_breaker("api_name")
breaker.reset()  # Clear state
```

### Metrics Memory Usage

Metrics are stored in memory. Reset periodically in long-running services:

```python
collector = get_metrics_collector()
collector.reset()  # Clear all metrics
```

---

## Troubleshooting

### Retry Not Working

Check that:
1. Exception type matches policy
2. Function is async (for async retry)
3. Decorator order is correct

### Circuit Breaker Not Opening

Verify:
1. Failure threshold is being reached
2. Exception type is expected
3. Circuit breaker name is consistent

### Metrics Not Recording

Ensure:
1. Decorator is applied correctly
2. Function completes (not interrupted)
3. Collector is not reset prematurely

---

## API Reference

See individual module docstrings for complete API documentation:

- `src/utils/retry.py` - Retry mechanism
- `src/utils/circuit_breaker.py` - Circuit breaker pattern
- `src/utils/metrics.py` - Metrics collection
- `src/utils/health_checks.py` - Health check system
- `src/utils/exceptions.py` - Custom exceptions
