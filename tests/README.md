# xSwE Agent Testing Framework

Comprehensive testing infrastructure for the xSwE Agent project, providing robust test coverage, performance benchmarks, and mock utilities.

## 📁 Directory Structure

```
tests/
├── __init__.py                    # Test package initialization
├── conftest.py                    # Shared fixtures and configuration
├── pytest.ini                     # pytest configuration (in root)
├── README.md                      # This file
│
├── utils/                         # Test utilities and mocks
│   ├── mock_github.py            # GitHub API simulator
│   ├── mock_gemini.py            # Gemini AI API simulator
│   ├── test_data_builder.py     # Fluent data builders
│   └── assertions.py             # Custom assertion helpers
│
├── fixtures/                      # Reusable test fixtures
│   ├── analytics_fixtures.py     # Analytics test fixtures
│   └── github_fixtures.py        # GitHub integration fixtures
│
├── integration/                   # Integration tests
│   ├── test_github_integration.py
│   ├── test_analytics_integration.py
│   └── test_charts_integration.py
│
├── performance/                   # Performance benchmarks
│   ├── test_analytics_performance.py
│   └── test_concurrent_load.py
│
├── infrastructure/                # Infrastructure component tests
│   └── (Future: retry, circuit breaker, metrics tests)
│
└── (unit tests in root)          # Existing unit tests
    ├── test_analytics.py
    ├── test_config.py
    ├── test_gemini_integration.py
    ├── test_github_monitor.py
    └── test_mcp_server.py
```

## 🚀 Quick Start

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit                    # Unit tests only
pytest -m integration             # Integration tests
pytest -m performance             # Performance tests
pytest -m "not slow"              # Skip slow tests

# Run tests by directory
pytest tests/integration/         # All integration tests
pytest tests/performance/         # All performance tests

# Run specific test file
pytest tests/test_analytics.py

# Run with coverage
pytest --cov=src --cov-report=html

# Verbose output
pytest -v

# Show test durations
pytest --durations=10
```

### Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Integration tests with mocked dependencies
- `@pytest.mark.performance` - Performance and benchmark tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.github_api` - Tests requiring GitHub API
- `@pytest.mark.gemini_api` - Tests requiring Gemini API

## 🛠️ Test Utilities

### MockGitHubAPI

Configurable GitHub API simulator with realistic responses:

```python
from tests.utils.mock_github import MockGitHubAPI, MockGitHubConfig

# Create mock API
mock_api = MockGitHubAPI()
mock_api.add_issue("Bug: Login fails", IssueState.OPEN, created_days_ago=5)
mock_api.add_issue("Feature: Dashboard", IssueState.CLOSED, closed_days_ago=2)

# Get issues
issues = mock_api.get_issues()

# Simulate errors
config = MockGitHubConfig(simulate_rate_limit=True)
error_api = MockGitHubAPI(config)
```

### MockGeminiAPI

AI API simulator for testing code analysis:

```python
from tests.utils.mock_gemini import MockGeminiAPI, create_mock_gemini_client

# Create mock API
mock_api = MockGeminiAPI()
result = await mock_api.generate_content("def foo(): pass")

# With custom quality scores
client = create_mock_gemini_client(quality_score=90.0)
```

### Test Data Builders

Fluent builders for creating test data:

```python
from tests.utils.test_data_builder import IssueBuilder, IssueListBuilder

# Build single issue
issue = (IssueBuilder()
         .with_title("Test Issue")
         .with_state(IssueState.OPEN)
         .with_priority(IssuePriority.HIGH)
         .created_days_ago(5)
         .build())

# Build issue list
issues = (IssueListBuilder()
          .add_open_issues(10)
          .add_closed_issues(5)
          .with_priority_distribution(high=3, medium=7, low=5)
          .build())
```

### Custom Assertions

Specialized assertions for testing:

```python
from tests.utils.assertions import MetricsAssertions, PerformanceAssertions

# Validate metrics
MetricsAssertions.assert_metrics_structure(metrics)
MetricsAssertions.assert_positive_metric(metrics, "throughput")
MetricsAssertions.assert_percentage(metrics, "completion_rate")

# Validate performance
PerformanceAssertions.assert_execution_time(duration, 2.0, "Analysis")
PerformanceAssertions.assert_memory_usage(memory_mb, 100.0, "Processing")
```

## 📊 Test Coverage

### Integration Tests

**GitHub Integration** (`test_github_integration.py`)
- Complete workflow testing (fetch → process → analyze)
- Issue filtering and search
- Timeline and repository info retrieval
- Error handling (network, auth, rate limits)
- **Status:** 11/11 tests passing ✅

**Analytics Integration** (`test_analytics_integration.py`)
- Full analytics pipeline
- Multi-strategy coordination
- Productivity, velocity, burndown, quality analysis
- Custom configurations
- Edge cases (all open, all closed, insufficient data)
- **Status:** 6/14 tests passing ⚠️

**Charts Integration** (`test_charts_integration.py`)
- Chart generation from analytics data
- Multiple chart types (bar, line, pie, time series)
- Custom styling and export formats
- Concurrent chart generation
- **Status:** API compatibility fixes needed ⚠️

### Performance Tests

**Analytics Performance** (`test_analytics_performance.py`)
- Dataset scaling (10 → 1000 issues)
- Repeated analysis performance
- Concurrent analysis (5+ requests)
- Strategy execution timing
- Memory efficiency
- Cache performance impact
- Scalability validation
- **Tests:** 10 comprehensive benchmarks

**Concurrent Load** (`test_concurrent_load.py`)
- Concurrent analytics requests (10-50 concurrent)
- Mixed operations (analytics + charts)
- Burst traffic handling
- Sustained load testing
- Resource cleanup verification
- Error rate under load
- Memory stability
- **Tests:** 11 stress tests

## 🎯 Fixtures

### Analytics Fixtures

Located in `tests/fixtures/analytics_fixtures.py`:

```python
# Use in tests
def test_analysis(analytics_engine, sample_issues_medium):
    results = await analytics_engine.analyze(sample_issues_medium, "test/repo")
    assert len(results) > 0
```

Available fixtures:
- `analytics_config` - Standard configuration
- `analytics_engine` - Configured engine
- `productivity_strategy` - Productivity analysis
- `velocity_strategy` - Velocity analysis
- `sample_issues_small` - 10 issues
- `sample_issues_medium` - 50 issues
- `sample_issues_large` - 200 issues

### GitHub Fixtures

Located in `tests/fixtures/github_fixtures.py`:

```python
# Use in tests
def test_repository(mock_github_api):
    issues = mock_github_api.get_issues()
    assert len(issues) > 0
```

Available fixtures:
- `github_user` - Mock user
- `github_issue` - Single issue
- `github_issues_list` - List of 10 issues
- `mock_github_api` - Configured API mock
- `github_repository_with_patch` - Patched repository

## 📈 Performance Benchmarks

### Expected Performance Targets

| Operation | Dataset Size | Target Time | Current |
|-----------|-------------|-------------|---------|
| Analytics | 10 issues | < 1s | ✅ Pass |
| Analytics | 100 issues | < 3s | ✅ Pass |
| Analytics | 1000 issues | < 10s | ✅ Pass |
| Concurrent (10) | 50 issues each | < 10s | ✅ Pass |
| Concurrent (50) | 20 issues each | < 30s | ✅ Pass |

### Memory Targets

- Analytics processing: < 100MB increase
- Large dataset (1000 issues): < 200MB total
- Concurrent operations: No memory leaks

## 🔧 Writing New Tests

### Unit Test Template

```python
import pytest
from src.module import function_to_test

def test_function_behavior():
    """Test that function works correctly."""
    # Arrange
    input_data = {"key": "value"}
    
    # Act
    result = function_to_test(input_data)
    
    # Assert
    assert result is not None
    assert result.key == "value"
```

### Integration Test Template

```python
import pytest
from tests.utils.mock_github import MockGitHubAPI

@pytest.mark.integration
class TestFeatureIntegration:
    """Integration tests for feature."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete workflow."""
        # Setup
        mock_api = MockGitHubAPI()
        mock_api.add_issue("Test", IssueState.OPEN)
        
        # Execute
        result = await process_workflow(mock_api)
        
        # Verify
        assert result.success
```

### Performance Test Template

```python
import pytest
import time
from tests.utils.assertions import PerformanceAssertions

@pytest.mark.performance
@pytest.mark.slow
class TestFeaturePerformance:
    """Performance tests for feature."""
    
    @pytest.mark.asyncio
    async def test_operation_performance(self):
        """Test operation completes within time limit."""
        # Measure
        start = time.time()
        result = await expensive_operation()
        duration = time.time() - start
        
        # Assert
        PerformanceAssertions.assert_execution_time(
            duration, 2.0, "Expensive operation"
        )
```

## 🐛 Debugging Tests

### Verbose Output

```bash
# Show detailed test output
pytest -vv

# Show print statements
pytest -s

# Show local variables on failure
pytest -l

# Drop into debugger on failure
pytest --pdb
```

### Running Single Tests

```bash
# Run specific test
pytest tests/test_file.py::TestClass::test_method

# Run tests matching pattern
pytest -k "test_pattern"

# Run last failed tests
pytest --lf

# Run failed tests first
pytest --ff
```

## 📝 Best Practices

1. **Use Fixtures** - Leverage existing fixtures instead of recreating test data
2. **Mock External APIs** - Always mock GitHub, Gemini, and other external APIs
3. **Parametrize Tests** - Use `@pytest.mark.parametrize` for multiple scenarios
4. **Clear Test Names** - Use descriptive names: `test_fetch_issues_filters_by_state`
5. **One Assert Per Concept** - Focus tests on single behaviors
6. **Fast Tests** - Keep unit tests under 100ms
7. **Independent Tests** - Tests should not depend on each other
8. **Clean Up** - Use fixtures and cleanup to avoid state leakage

## 🎓 Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

## 📞 Support

For questions or issues with tests:
1. Check existing test examples in the relevant directory
2. Review test utilities in `tests/utils/`
3. Consult the main project README
4. Check pytest documentation for advanced features

---

**Last Updated:** 2025-10-05  
**Test Coverage:** 17+ integration tests, 21+ performance tests  
**Framework Version:** 1.0.0
