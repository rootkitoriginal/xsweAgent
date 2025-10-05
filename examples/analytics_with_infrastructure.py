"""
Example: Analytics Engine with Infrastructure Integration

This example demonstrates how to use the analytics engine with the complete
infrastructure utilities (retry, circuit breaker, metrics, health checks).
"""

import asyncio
from datetime import datetime, timedelta

# Import analytics engine and utilities
from src.analytics.engine import AnalyticsConfiguration, create_analytics_engine
from src.github_monitor.models import Issue, IssueState
from src.utils import (
    CircuitBreakerPolicies,
    RetryPolicies,
    get_circuit_breaker,
    get_health_registry,
    get_metrics_collector,
    register_health_check,
)


async def create_sample_issues():
    """Create sample issues for demonstration."""
    now = datetime.now()
    return [
        Issue(
            id=i,
            number=i,
            title=f"Issue {i}",
            state=IssueState.OPEN if i % 3 == 0 else IssueState.CLOSED,
            created_at=now - timedelta(days=i * 2),
            closed_at=now - timedelta(days=i) if i % 3 != 0 else None,
        )
        for i in range(1, 21)
    ]


async def setup_health_checks():
    """Setup health checks for the system."""
    
    async def check_analytics_engine():
        """Check if analytics engine is operational."""
        try:
            # Simple check: can we create an engine?
            engine = await create_analytics_engine()
            return engine is not None
        except Exception:
            return False

    async def check_metrics_collector():
        """Check if metrics collector is working."""
        try:
            collector = get_metrics_collector()
            collector.increment_counter("health_check_test", 1.0)
            return True
        except Exception:
            return False

    # Register health checks
    register_health_check("analytics_engine", check_analytics_engine, timeout=5.0)
    register_health_check("metrics_collector", check_metrics_collector, timeout=5.0)
    
    print("✅ Health checks registered")


async def demonstrate_retry_mechanism():
    """Demonstrate retry mechanism with different policies."""
    print("\n🔄 DEMONSTRATING RETRY MECHANISM")
    print("=" * 60)
    
    from src.utils import retry_with_policy
    
    attempt_count = 0
    
    @retry_with_policy(RetryPolicies.ANALYTICS)
    async def flaky_operation():
        """Operation that fails a few times then succeeds."""
        nonlocal attempt_count
        attempt_count += 1
        print(f"  Attempt {attempt_count}...")
        
        if attempt_count < 3:
            raise Exception("Temporary failure")
        return "Success!"
    
    try:
        result = await flaky_operation()
        print(f"  ✅ Operation succeeded after {attempt_count} attempts: {result}")
    except Exception as e:
        print(f"  ❌ Operation failed: {e}")


async def demonstrate_circuit_breaker():
    """Demonstrate circuit breaker pattern."""
    print("\n⚡ DEMONSTRATING CIRCUIT BREAKER")
    print("=" * 60)
    
    from src.utils import circuit_breaker
    
    # Get/reset the circuit breaker
    breaker = get_circuit_breaker("demo_api", CircuitBreakerPolicies.DEFAULT)
    breaker.reset()
    
    call_count = 0
    
    @circuit_breaker(name="demo_api", policy=CircuitBreakerPolicies.DEFAULT)
    async def unreliable_api_call():
        """API call that always fails for demonstration."""
        nonlocal call_count
        call_count += 1
        raise Exception("API Error")
    
    # Try calling multiple times
    failure_threshold = CircuitBreakerPolicies.DEFAULT.failure_threshold
    
    print(f"  Calling unreliable API (failure threshold: {failure_threshold})...")
    
    for i in range(failure_threshold + 2):
        try:
            await unreliable_api_call()
        except Exception as e:
            error_type = type(e).__name__
            print(f"  Call {i+1}: ❌ {error_type}: {str(e)[:50]}")
    
    print(f"  Circuit breaker state: {breaker.get_state().value}")
    print(f"  Total API calls made: {call_count} (stopped at threshold)")


async def demonstrate_metrics_collection():
    """Demonstrate metrics collection."""
    print("\n📊 DEMONSTRATING METRICS COLLECTION")
    print("=" * 60)
    
    collector = get_metrics_collector()
    collector.reset()
    
    # Simulate some API calls
    print("  Recording metrics...")
    collector.increment_counter("api_calls", 1.0, endpoint="github")
    collector.increment_counter("api_calls", 1.0, endpoint="github")
    collector.increment_counter("api_calls", 1.0, endpoint="gemini")
    
    # Record some response times
    collector.record_timing("api_response_time", 125.5, endpoint="github")
    collector.record_timing("api_response_time", 98.3, endpoint="github")
    collector.record_timing("api_response_time", 210.7, endpoint="gemini")
    
    # Record some values
    collector.observe_histogram("issue_count", 15.0)
    collector.observe_histogram("issue_count", 22.0)
    collector.observe_histogram("issue_count", 18.0)
    
    # Display metrics
    print("\n  📈 Collected Metrics:")
    print(f"    GitHub API calls: {collector.get_counter('api_calls', endpoint='github')}")
    print(f"    Gemini API calls: {collector.get_counter('api_calls', endpoint='gemini')}")
    
    github_timing = collector.get_timer_stats("api_response_time", endpoint="github")
    print(f"    GitHub avg response: {github_timing['avg_ms']:.1f}ms")
    
    issue_stats = collector.get_histogram_stats("issue_count")
    print(f"    Issue count stats: avg={issue_stats['avg']:.1f}, min={issue_stats['min']}, max={issue_stats['max']}")


async def demonstrate_health_checks():
    """Demonstrate health check system."""
    print("\n🏥 DEMONSTRATING HEALTH CHECKS")
    print("=" * 60)
    
    registry = get_health_registry()
    
    print("  Running health checks...")
    results = await registry.check_all()
    
    for name, result in results.items():
        status_icon = "✅" if result.status.value == "healthy" else "❌"
        print(f"    {status_icon} {name}: {result.status.value}")
        if result.message:
            print(f"       Message: {result.message}")
    
    overall = await registry.get_overall_status()
    print(f"\n  Overall system status: {overall.value}")


async def demonstrate_analytics_with_infrastructure():
    """Demonstrate analytics engine with full infrastructure."""
    print("\n🧮 DEMONSTRATING ANALYTICS ENGINE WITH INFRASTRUCTURE")
    print("=" * 60)
    
    # Create sample issues
    issues = await create_sample_issues()
    print(f"  Created {len(issues)} sample issues")
    
    # Create analytics engine
    config = AnalyticsConfiguration(
        minimum_issues_for_analysis=5,
        time_window_days=90,
    )
    engine = await create_analytics_engine(configuration=config)
    print(f"  Registered strategies: {engine.get_registered_strategies()}")
    
    # Run analysis (this will use retry, metrics, and logging)
    print("\n  Running comprehensive analysis...")
    results = await engine.analyze(issues, "demo/repository", config)
    
    print(f"\n  ✅ Analysis completed! Generated {len(results)} reports:")
    for analysis_type, result in results.items():
        print(f"\n    📊 {analysis_type.upper()}")
        print(f"       Summary: {result.summary}")
        if result.score is not None:
            print(f"       Score: {result.score:.2f}")
        if result.recommendations:
            print(f"       Recommendations: {len(result.recommendations)}")
            for rec in result.recommendations[:2]:  # Show first 2
                print(f"         - {rec}")
    
    # Show metrics collected during analysis
    print("\n  📊 Metrics from Analysis:")
    collector = get_metrics_collector()
    
    # Show analytics-related metrics
    for metric_name in ["analytics_engine_calls_total", "analytics_productivity_calls_total"]:
        success_count = collector.get_counter(metric_name, status="success")
        if success_count > 0:
            print(f"    {metric_name}: {success_count}")


async def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("  Analytics Engine with Infrastructure Integration")
    print("  Complete Demonstration")
    print("=" * 60)
    
    # Setup
    await setup_health_checks()
    
    # Run demonstrations
    await demonstrate_retry_mechanism()
    await demonstrate_circuit_breaker()
    await demonstrate_metrics_collection()
    await demonstrate_health_checks()
    await demonstrate_analytics_with_infrastructure()
    
    print("\n" + "=" * 60)
    print("  ✅ All demonstrations completed successfully!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
