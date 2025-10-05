# Test Execution Guide

Quick reference for running tests in the xSwE Agent project.

## 🚀 Quick Commands

### Run All Tests
```bash
pytest
```

### Run by Test Type
```bash
# Unit tests only (fast)
pytest -m unit

# Integration tests
pytest -m integration

# Performance tests
pytest -m performance

# Skip slow tests
pytest -m "not slow"

# Only slow/performance tests
pytest -m "slow or performance"
```

### Run by Directory
```bash
# All integration tests
pytest tests/integration/

# All performance tests
pytest tests/performance/

# Specific test file
pytest tests/test_analytics.py

# Specific test class
pytest tests/integration/test_github_integration.py::TestGitHubIntegration

# Specific test method
pytest tests/integration/test_github_integration.py::TestGitHubIntegration::test_fetch_and_process_issues_workflow
```

### Coverage Reports
```bash
# Run with coverage
pytest --cov=src

# Generate HTML report
pytest --cov=src --cov-report=html

# Open coverage report (after generating)
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# Coverage with missing lines
pytest --cov=src --cov-report=term-missing

# Fail if coverage < 90%
pytest --cov=src --cov-fail-under=90
```

### Output Control
```bash
# Verbose output
pytest -v

# Very verbose (show full test names)
pytest -vv

# Show print statements
pytest -s

# Short traceback
pytest --tb=short

# Line-only traceback
pytest --tb=line

# No traceback
pytest --tb=no

# Show local variables on failure
pytest -l
```

### Debugging
```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger at start of test
pytest --trace

# Run last failed tests
pytest --lf

# Run failed tests first, then others
pytest --ff

# Stop after first failure
pytest -x

# Stop after N failures
pytest --maxfail=3
```

### Performance & Profiling
```bash
# Show slowest 10 tests
pytest --durations=10

# Show all test durations
pytest --durations=0

# With timing breakdown
pytest -vv --durations=10
```

### Parallel Execution
```bash
# Install pytest-xdist first
pip install pytest-xdist

# Run with 4 workers
pytest -n 4

# Run with auto CPU detection
pytest -n auto
```

## 📊 Test Organization

### Current Test Statistics
- **Unit Tests**: 12 existing test files
- **Integration Tests**: 31 tests (17 passing)
- **Performance Tests**: 21 tests
- **Total Test Files**: 23+
- **Mock Utilities**: 3 comprehensive simulators
- **Custom Assertions**: 5 specialized classes
- **Test Fixtures**: 20+ reusable fixtures

### Test Markers Usage
```python
# Mark as unit test
@pytest.mark.unit
def test_function():
    pass

# Mark as integration test
@pytest.mark.integration
@pytest.mark.asyncio
async def test_workflow():
    pass

# Mark as performance test
@pytest.mark.performance
@pytest.mark.slow
def test_benchmark():
    pass

# Mark as requiring external API
@pytest.mark.github_api
def test_github():
    pass

# Combine markers
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_expensive_operation():
    pass
```

## 🎯 Common Test Scenarios

### Testing Analytics
```bash
# All analytics tests
pytest tests/test_analytics.py tests/integration/test_analytics_integration.py

# With coverage
pytest tests/test_analytics.py --cov=src/analytics --cov-report=term-missing

# Performance tests only
pytest tests/performance/test_analytics_performance.py -v
```

### Testing GitHub Integration
```bash
# Unit tests
pytest tests/test_github_monitor.py

# Integration tests
pytest tests/integration/test_github_integration.py

# Both
pytest -k "github" -v
```

### Testing Charts
```bash
# Unit tests
pytest tests/test_charts.py

# Integration tests
pytest tests/integration/test_charts_integration.py

# All chart-related
pytest -k "chart"
```

### Testing MCP Server
```bash
# Server tests
pytest tests/test_mcp_server.py

# With output
pytest tests/test_mcp_server.py -v -s
```

## 🔍 Test Selection

### By Pattern
```bash
# Run tests matching pattern
pytest -k "test_fetch"

# Multiple patterns (OR)
pytest -k "fetch or create"

# Exclude pattern
pytest -k "not slow"

# Complex expressions
pytest -k "github and (fetch or create)"
```

### By Path
```bash
# Multiple files
pytest tests/test_analytics.py tests/test_github_monitor.py

# Wildcard
pytest tests/test_*.py

# Exclude directory
pytest tests/ --ignore=tests/performance/
```

## 📈 Continuous Integration

### CI/CD Commands
```bash
# Full test suite with coverage
pytest tests/ --cov=src --cov-report=xml --cov-report=term --cov-fail-under=90

# Fast tests only (for quick feedback)
pytest -m "not slow" --tb=short

# Integration tests with retries
pytest tests/integration/ --maxfail=5

# Performance tests (separate job)
pytest tests/performance/ -v --durations=0
```

### Generate Reports
```bash
# JUnit XML (for CI)
pytest --junitxml=test-results.xml

# HTML report
pip install pytest-html
pytest --html=test-report.html

# JSON report
pip install pytest-json-report
pytest --json-report --json-report-file=test-results.json
```

## 🐛 Troubleshooting

### Common Issues

**Tests not found:**
```bash
# Clear cache
pytest --cache-clear

# Show collection
pytest --collect-only
```

**Import errors:**
```bash
# Ensure package installed in development mode
pip install -e .

# Or run from project root
PYTHONPATH=. pytest tests/
```

**Async test issues:**
```bash
# Ensure pytest-asyncio installed
pip install pytest-asyncio

# Check asyncio mode in pytest.ini
grep asyncio_mode pytest.ini
```

**Fixture issues:**
```bash
# Show available fixtures
pytest --fixtures

# Show fixture setup
pytest --setup-show tests/test_file.py
```

**Warnings:**
```bash
# Show warnings
pytest -W default

# Treat warnings as errors
pytest -W error

# Ignore specific warning
pytest -W ignore::DeprecationWarning
```

## 📝 Best Practices

### Before Committing
```bash
# Run fast tests
pytest -m "not slow" --tb=short

# Check coverage
pytest --cov=src --cov-report=term-missing

# Run linting (if configured)
flake8 tests/
black --check tests/
```

### Daily Development
```bash
# Watch mode (with pytest-watch)
pip install pytest-watch
ptw tests/

# Quick feedback loop
pytest --lf -x -v
```

### Performance Testing
```bash
# Run performance suite
pytest tests/performance/ -v --durations=10

# Single performance test
pytest tests/performance/test_analytics_performance.py::TestAnalyticsPerformance::test_small_dataset_performance -v -s
```

## 🎓 Advanced Usage

### Parametrized Tests
```bash
# Run specific parameter
pytest tests/test_file.py::test_func[param1]

# Show parameter combinations
pytest --collect-only tests/test_file.py
```

### Custom Options
```bash
# Define in conftest.py
def pytest_addoption(parser):
    parser.addoption("--integration", action="store_true")

# Use in test
@pytest.mark.skipif(not request.config.getoption("--integration"))

# Run with custom option
pytest --integration
```

### Plugins
```bash
# Install useful plugins
pip install pytest-timeout pytest-retry pytest-ordering

# Use timeout
pytest --timeout=300

# Retry failures
pytest --reruns 3
```

## 📞 Getting Help

```bash
# Pytest help
pytest --help

# Show markers
pytest --markers

# Show fixtures
pytest --fixtures

# Version info
pytest --version
```

## 🔗 Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest plugins](https://docs.pytest.org/en/latest/reference/plugin_list.html)

---

**Quick Reference Card:**
```bash
pytest                        # Run all tests
pytest -v                     # Verbose
pytest -m integration         # Integration tests only
pytest --cov=src             # With coverage
pytest --lf                  # Last failed
pytest -x                    # Stop on first failure
pytest -k "pattern"          # Match pattern
pytest --durations=10        # Show slowest tests
```
