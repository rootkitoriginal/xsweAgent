# Utils Infrastructure

Comprehensive infrastructure components for resilient, observable, and production-ready applications.

## Components

### 1. Retry Logic (`retry.py`)

Configurable retry mechanism with multiple backoff strategies.

**Features:**
- Multiple backoff strategies (LINEAR, EXPONENTIAL, with/without JITTER)
- Pre-configured policies for common scenarios
- Support for both sync and async functions
- Configurable max attempts and delays

**Usage:**

```python
from src.utils import retry, RetryPolicies

# Using pre-configured policy
@retry(RetryPolicies.STANDARD)
async def fetch_data():
    return await external_api_call()

# Custom policy
from src.utils import RetryPolicy, BackoffStrategy

@retry(RetryPolicy(
    max_attempts=5,
    base_delay=2.0,
    max_delay=30.0,
    backoff_strategy=BackoffStrategy.EXPONENTIAL_JITTER
))
async def critical_operation():
    return await important_call()
```

**Available Policies:**
- `RetryPolicies.FAST` - Quick retries (2 attempts, 0.5s base)
- `RetryPolicies.STANDARD` - Balanced approach (3 attempts, 1s base)
- `RetryPolicies.AGGRESSIVE` - For critical ops (5 attempts, 2s base)
- `RetryPolicies.MCP_TOOLS` - MCP-specific (2 attempts, 1s base)
- `RetryPolicies.GITHUB_API` - GitHub API optimized (3 attempts, 2s base)
- `RetryPolicies.AI_API` - AI service optimized (3 attempts, 1s base)

### 2. Circuit Breaker (`circuit_breaker.py`)

Prevents cascading failures by detecting failures and opening the circuit.

**States:**
- **CLOSED**: Normal operation
- **OPEN**: Failures detected, rejecting requests
- **HALF_OPEN**: Testing if service recovered

**Usage:**

```python
from src.utils import CircuitBreaker, CircuitBreakerPolicies

# Using pre-configured policy
breaker = CircuitBreaker(CircuitBreakerPolicies.STANDARD)

@breaker
async def call_external_service():
    return await external_call()

# Check circuit state
state = breaker.get_state()
print(f"State: {state['state']}, Failures: {state['failure_count']}")
```

**Available Policies:**
- `CircuitBreakerPolicies.STANDARD` - Balanced (5 failures, 60s timeout)
- `CircuitBreakerPolicies.AGGRESSIVE` - Strict (3 failures, 120s timeout)
- `CircuitBreakerPolicies.LENIENT` - Tolerant (10 failures, 30s timeout)
- `CircuitBreakerPolicies.MCP_TOOLS` - MCP-specific (5 failures, 60s timeout)
- `CircuitBreakerPolicies.EXTERNAL_API` - External services (4 failures, 90s timeout)

### 3. Health Checks (`health_checks.py`)

Comprehensive health monitoring system for all components.

**Usage:**

```python
from src.utils import HealthCheck, HealthCheckRegistry, HealthStatus, HealthCheckResult

# Define health check
async def check_database():
    await db.ping()
    return HealthCheckResult(
        component="database",
        status=HealthStatus.HEALTHY,
        message="Database connection OK"
    )

# Register health check
registry = HealthCheckRegistry()
registry.register(HealthCheck("database", check_database, timeout=5.0, critical=True))

# Run health checks
results = await registry.check_all()
overall_status = await registry.get_overall_status()
```

**Health Status Levels:**
- `HealthStatus.HEALTHY` - Component operating normally
- `HealthStatus.DEGRADED` - Component has issues but functional
- `HealthStatus.UNHEALTHY` - Component is not functioning

### 4. Metrics Collection (`metrics.py`)

Performance monitoring and Prometheus-compatible metrics.

**Usage:**

```python
from src.utils import MetricsCollector, track_api_calls, get_metrics_collector

# Get global collector
collector = get_metrics_collector()

# Record metrics
collector.record("api_response_time_ms", 150.5)
collector.increment("api_calls_total", 1, labels={"endpoint": "/api/v1/issues"})

# Use decorator for automatic tracking
@track_api_calls("my_endpoint")
async def my_function():
    return await do_work()

# Get metrics
metrics = collector.get_metrics()
prometheus_text = collector.get_prometheus_format()
```

**Metric Types:**
- **Gauges**: Point-in-time values (aggregated with min/max/avg)
- **Counters**: Monotonically increasing values

### 5. Custom Exceptions (`exceptions.py`)

Specialized exceptions for better error handling.

**Available Exceptions:**
- `XSWEAgentError` - Base exception
- `RetryExhaustedError` - Retry attempts exhausted
- `CircuitBreakerError` - Circuit breaker is open
- `HealthCheckError` - Health check failed
- `RateLimitError` - Rate limit exceeded

## Integration Patterns

### Combining Retry + Circuit Breaker

```python
from src.utils import retry, circuit_breaker, RetryPolicies, CircuitBreakerPolicies

breaker = CircuitBreaker(CircuitBreakerPolicies.EXTERNAL_API)

@retry(RetryPolicies.STANDARD)
@breaker
async def resilient_call():
    return await external_service()
```

### With Metrics Tracking

```python
from src.utils import retry, track_api_calls, RetryPolicies

@retry(RetryPolicies.GITHUB_API)
@track_api_calls("github_issues")
async def fetch_github_issues():
    return await github_api.get_issues()
```

### Complete Integration

```python
from src.utils import (
    retry,
    circuit_breaker,
    track_api_calls,
    RetryPolicies,
    CircuitBreakerPolicies,
)

breaker = CircuitBreaker(CircuitBreakerPolicies.STANDARD)

@retry(RetryPolicies.STANDARD)
@breaker
@track_api_calls("critical_endpoint")
async def production_ready_endpoint():
    """Fully instrumented endpoint with retry, circuit breaker, and metrics."""
    return await critical_operation()
```

## Best Practices

1. **Always use retry for external calls**: Network calls, API requests, database queries
2. **Apply circuit breakers to protect downstream services**: Prevent cascade failures
3. **Register health checks for all critical components**: Enable proactive monitoring
4. **Track metrics for all API endpoints**: Observe performance and usage patterns
5. **Use pre-configured policies when possible**: They're tuned for common scenarios
6. **Combine patterns for production-ready code**: Retry + Circuit Breaker + Metrics

## Testing

Run the infrastructure tests:

```bash
pytest tests/test_utils_infrastructure.py -v
```

All components are thoroughly tested with unit tests covering:
- Retry success and failure scenarios
- Circuit breaker state transitions
- Health check execution and aggregation
- Metrics collection and Prometheus export

## Performance Considerations

- **Retry**: Adds latency on failures (controlled by backoff strategy)
- **Circuit Breaker**: Minimal overhead when closed, fails fast when open
- **Health Checks**: Run with timeouts to prevent blocking
- **Metrics**: Lightweight in-memory collection, minimal impact

## Monitoring

Use the infrastructure to monitor itself:

```python
# Register health checks
from src.utils import get_health_check_registry

registry = get_health_check_registry()
checks = registry.list_checks()

# Get metrics
from src.utils import get_metrics_collector

collector = get_metrics_collector()
stats = collector.get_stats()
```
