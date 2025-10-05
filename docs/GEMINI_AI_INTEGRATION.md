# Enhanced Gemini AI Integration

## Overview

The enhanced Gemini AI integration provides comprehensive AI-powered analysis capabilities using Google's Gemini 2.5 Flash model. Built on a robust infrastructure with retry logic, circuit breakers, and comprehensive monitoring.

## Features

### 🤖 Analysis Capabilities

1. **Code Analysis** - Quality assessment, complexity scoring, and improvement suggestions
2. **Issue Intelligence** - Automatic categorization, severity assessment, and insights
3. **Trend Prediction** - Forecasting future patterns based on historical data
4. **Sentiment Analysis** - Emotional tone detection in text
5. **Priority Analysis** - Smart issue prioritization with business impact scoring
6. **Collaboration Insights** - Team health and workflow analysis

### 🛡️ Infrastructure Features

- **Retry Logic** - Automatic retry with exponential backoff and jitter
- **Circuit Breaker** - Protection against cascading failures
- **Health Checks** - Continuous service availability monitoring
- **Metrics Tracking** - Performance monitoring and cost tracking
- **Rate Limiting** - Intelligent request throttling

## Architecture

```
src/
├── gemini_integration/
│   ├── __init__.py           # Public API exports
│   ├── client.py             # Enhanced Gemini client with infrastructure
│   ├── analyzer.py           # Multiple analysis capabilities
│   └── models.py             # Data models for all analysis types
└── utils/
    ├── __init__.py           # Infrastructure exports
    ├── retry.py              # Retry logic with backoff strategies
    ├── circuit_breaker.py    # Circuit breaker pattern
    ├── health_checks.py      # Health monitoring
    ├── metrics.py            # Metrics tracking
    └── exceptions.py         # Custom exceptions
```

## Quick Start

### Basic Usage

```python
import asyncio
from src.gemini_integration import GeminiAnalyzer, CodeSnippet

async def main():
    # Initialize analyzer
    analyzer = GeminiAnalyzer()
    
    # Analyze code
    snippet = CodeSnippet(
        content="def hello(): return 'world'",
        language="python"
    )
    
    result = await analyzer.analyze_code(snippet)
    
    if result.is_successful():
        print(f"Complexity: {result.report.complexity_score}")
        print(f"Maintainability: {result.report.maintainability_index}")

asyncio.run(main())
```

### Custom Configuration

```python
from src.gemini_integration import GeminiClient, GeminiAnalyzer, AIConfig

# Custom AI configuration
config = AIConfig(
    model="gemini-2.5-flash",
    temperature=0.2,
    max_output_tokens=4096,
    timeout=60.0,
    enable_safety_checks=True
)

# Create client with config
client = GeminiClient(config=config)
analyzer = GeminiAnalyzer(client=client)
```

## Analysis Types

### 1. Code Analysis

Analyzes code quality, complexity, and provides improvement suggestions.

```python
from src.gemini_integration import GeminiAnalyzer, CodeSnippet

analyzer = GeminiAnalyzer()

snippet = CodeSnippet(
    content=your_code,
    language="python",
    filename="example.py",
    context="Optional context about the code"
)

result = await analyzer.analyze_code(snippet)

print(f"Summary: {result.report.summary}")
print(f"Complexity: {result.report.complexity_score}")
print(f"Suggestions: {len(result.report.suggestions)}")
```

**Output Structure:**
- `summary`: Brief code overview
- `complexity_score`: 0.0-1.0 (0=simple, 1=complex)
- `maintainability_index`: 0.0-1.0 (0=hard to maintain, 1=easy)
- `suggestions`: List of improvement recommendations
- `tags`: Relevant tags for the code

### 2. Issue Intelligence

Provides smart analysis of GitHub issues with categorization and insights.

```python
from src.gemini_integration import GeminiAnalyzer
from src.github_monitor.models import Issue

analyzer = GeminiAnalyzer()

result = await analyzer.issue_analysis(issue)

print(f"Category: {result.category}")  # bug, feature, enhancement, etc.
print(f"Severity: {result.severity}")  # critical, high, medium, low
print(f"Estimated Hours: {result.estimated_resolution_hours}")
print(f"Root Cause: {result.root_cause}")
```

**Output Structure:**
- `category`: Issue type (bug, feature, enhancement, documentation, question)
- `severity`: Severity level (critical, high, medium, low)
- `estimated_resolution_hours`: Estimated time to resolve
- `root_cause`: Likely root cause of the issue
- `recommended_labels`: Suggested labels for the issue
- `confidence_score`: AI confidence in the analysis

### 3. Trend Prediction

Forecasts future patterns based on historical data.

```python
analyzer = GeminiAnalyzer()

historical_data = [
    {"week": 1, "issues": 10, "resolution_time": 24},
    {"week": 2, "issues": 15, "resolution_time": 28},
    # ... more data points
]

result = await analyzer.trend_prediction(historical_data)

print(f"Predicted Issues: {result.predicted_issue_count}")
print(f"Predicted Resolution Time: {result.predicted_resolution_time}")
print(f"Quality Trend: {result.quality_trend}")  # improving, stable, declining
```

**Output Structure:**
- `predicted_issue_count`: Forecasted number of issues
- `predicted_resolution_time`: Expected resolution time
- `quality_trend`: Direction of quality (improving, stable, declining)
- `workload_forecast`: Expected workload (increasing, stable, decreasing)
- `insights`: Key insights from the analysis
- `recommendations`: Actionable recommendations

### 4. Sentiment Analysis

Detects emotional tone and sentiment in text.

```python
analyzer = GeminiAnalyzer()

text = "This is an amazing feature! Really love it."

result = await analyzer.sentiment_analysis(text)

print(f"Sentiment: {result.sentiment}")  # positive, neutral, negative, mixed
print(f"Confidence: {result.confidence_score}")
print(f"Positive Score: {result.positive_score}")
```

**Output Structure:**
- `sentiment`: Overall sentiment (positive, neutral, negative, mixed)
- `confidence_score`: Confidence in the classification
- `positive_score`, `negative_score`, `neutral_score`: Individual scores
- `key_phrases`: Important phrases identified
- `emotional_tone`: Description of emotional tone

### 5. Priority Analysis

Provides AI-powered priority recommendations for issues.

```python
analyzer = GeminiAnalyzer()

result = await analyzer.priority_analysis(issue)

print(f"Priority: {result.priority}")  # critical, high, medium, low
print(f"Business Impact: {result.business_impact_score}")
print(f"Technical Complexity: {result.technical_complexity_score}")
print(f"Urgency: {result.urgency_score}")
```

**Output Structure:**
- `priority`: Recommended priority level
- `business_impact_score`: Business impact (0.0-1.0)
- `technical_complexity_score`: Technical complexity (0.0-1.0)
- `urgency_score`: Urgency level (0.0-1.0)
- `strategic_alignment_score`: Strategic importance (0.0-1.0)
- `overall_priority_score`: Combined priority score
- `justification`: Explanation for the priority
- `estimated_effort_hours`: Expected effort required

### 6. Collaboration Analysis

Analyzes team collaboration patterns and provides insights.

```python
analyzer = GeminiAnalyzer()

team_data = {
    "team_size": 5,
    "avg_review_time": 12,
    "code_review_participation": 0.8,
    # ... more metrics
}

result = await analyzer.collaboration_analysis(team_data)

print(f"Team Health: {result.team_health_score}")
print(f"Communication Score: {result.communication_score}")
```

**Output Structure:**
- `team_health_score`: Overall team health (0.0-1.0)
- `communication_score`: Communication effectiveness (0.0-1.0)
- `knowledge_sharing_score`: Knowledge sharing quality (0.0-1.0)
- `collaboration_efficiency`: Collaboration efficiency (0.0-1.0)
- `bottlenecks`: Identified workflow bottlenecks
- `top_collaborators`: Most active collaborators
- `insights`: Key insights about team dynamics
- `recommendations`: Improvement recommendations

## Infrastructure Integration

### Retry Logic

Automatic retry with exponential backoff for resilient API calls.

```python
from src.utils import retry, RetryPolicies

@retry(RetryPolicies.GEMINI_API)
async def my_function():
    # Your API call
    pass
```

**Available Policies:**
- `RetryPolicies.GEMINI_API` - For AI API calls (3 attempts, exponential backoff)
- `RetryPolicies.GITHUB_API` - For GitHub API (5 attempts)
- `RetryPolicies.FAST_FAIL` - Quick failure (2 attempts)
- `RetryPolicies.CRITICAL` - Aggressive retry (10 attempts)

### Circuit Breaker

Protects against cascading failures.

```python
from src.utils import circuit_breaker, CircuitBreakerPolicies

@circuit_breaker(CircuitBreakerPolicies.GEMINI_API, name="my_service")
async def my_function():
    # Your API call
    pass
```

**Available Policies:**
- `CircuitBreakerPolicies.GEMINI_API` - For AI services
- `CircuitBreakerPolicies.GITHUB_API` - For GitHub API
- `CircuitBreakerPolicies.CRITICAL` - For critical services

### Metrics Tracking

Track performance and usage metrics.

```python
from src.utils import track_api_calls, get_metrics_tracker

@track_api_calls("my_operation")
async def my_function():
    # Your operation
    pass

# Get metrics
tracker = get_metrics_tracker()
metrics = tracker.get_metrics("my_operation")
print(f"Success Rate: {metrics.get_success_rate():.2f}%")
print(f"Avg Duration: {metrics.avg_duration_ms:.2f}ms")
```

### Health Checks

Monitor service availability.

```python
from src.utils import HealthCheck, HealthStatus

async def check_gemini_health():
    # Your health check logic
    pass

health_check = HealthCheck("gemini_service", check_gemini_health)
result = await health_check.perform_check()

if result.status == HealthStatus.HEALTHY:
    print("Service is healthy")
```

## Usage Tracking

Monitor AI usage and costs.

```python
client = GeminiClient()

# Make API calls...
await client.generate_content("prompt 1")
await client.generate_content("prompt 2")

# Get usage statistics
stats = client.get_usage_stats()
print(f"Total Requests: {stats['total_requests']}")
print(f"Total Tokens: {stats['total_tokens']}")
```

## Error Handling

The integration provides comprehensive error handling:

```python
from src.utils import (
    AIServiceError,
    RateLimitError,
    RetryExhaustedError,
    CircuitBreakerOpenError
)

try:
    result = await analyzer.analyze_code(snippet)
except RateLimitError:
    print("Rate limit exceeded")
except RetryExhaustedError:
    print("All retry attempts failed")
except CircuitBreakerOpenError:
    print("Service is temporarily unavailable")
except AIServiceError as e:
    print(f"AI service error: {e}")
```

## Configuration

### Environment Variables

```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional
GEMINI_MODEL=gemini-2.5-flash
GEMINI_RATE_LIMIT_PER_MINUTE=60
```

### AIConfig Options

```python
config = AIConfig(
    model="gemini-2.5-flash",           # Model to use
    temperature=0.2,                     # Creativity (0.0-1.0)
    top_p=0.9,                          # Nucleus sampling
    top_k=20,                           # Top-k sampling
    max_output_tokens=2048,             # Max response length
    timeout=30.0,                       # Request timeout
    enable_safety_checks=True,          # Enable safety filters
    max_input_length=10000,             # Max input length
    max_output_length=5000              # Max output length
)
```

## Best Practices

1. **Use Batch Operations**: Group similar analyses for better performance
2. **Configure Timeouts**: Set appropriate timeouts for your use case
3. **Monitor Usage**: Track token usage to manage costs
4. **Handle Errors**: Implement proper error handling for production use
5. **Cache Results**: Cache AI responses when appropriate
6. **Rate Limiting**: Respect API rate limits

## Examples

See complete examples in:
- `examples/gemini_ai_enhanced_demo.py` - Comprehensive demo of all features
- `tests/test_enhanced_gemini.py` - Test examples for each capability

## Performance

- **Code Analysis**: ~2-5 seconds per analysis
- **Issue Analysis**: ~1-3 seconds per issue
- **Sentiment Analysis**: ~0.5-2 seconds per text
- **Trend Prediction**: ~3-7 seconds depending on data size
- **Priority Analysis**: ~1-3 seconds per issue
- **Collaboration Analysis**: ~2-5 seconds per team

## Limitations

- API rate limits: 60 requests per minute (configurable)
- Max input length: 10,000 characters (configurable)
- Max output length: 5,000 characters (configurable)
- Token costs: Based on Gemini 2.5 Flash pricing

## Troubleshooting

### Common Issues

1. **"Gemini API key is not configured"**
   - Set `GEMINI_API_KEY` environment variable

2. **Rate limit errors**
   - Reduce request frequency or increase rate limit configuration

3. **Circuit breaker open**
   - Service is temporarily unavailable, wait for recovery period

4. **Timeout errors**
   - Increase timeout in AIConfig or reduce input size

## Support

For issues or questions:
- Check documentation: `docs/GEMINI_AI_INTEGRATION.md`
- Review examples: `examples/gemini_ai_enhanced_demo.py`
- Run tests: `pytest tests/test_enhanced_gemini.py`

## License

Part of xSwE Agent - See main project LICENSE
