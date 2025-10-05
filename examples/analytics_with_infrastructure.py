"""
Example: Analytics Engine with Infrastructure Integration (Simplified)

This example demonstrates how to use the analytics engine with basic
infrastructure utilities (retry, metrics collection).
"""

import asyncio
from datetime import datetime, timedelta

# Import analytics engine and utilities
from src.analytics.engine import AnalyticsConfiguration, create_analytics_engine
from src.github_monitor.models import Issue, IssueState
from src.utils import get_metrics_collector, track_api_calls


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


async def demonstrate_analytics_with_metrics():
    """Demonstrate analytics engine with metrics collection."""
    print("\\n🧮 DEMONSTRATING ANALYTICS ENGINE WITH METRICS")
    print("=" * 60)
    
    # Reset metrics for clean demonstration
    collector = get_metrics_collector()
    
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
    print("\\n  Running comprehensive analysis...")
    results = await engine.analyze(issues, "demo/repository", config)
    
    print(f"\\n  ✅ Analysis completed! Generated {len(results)} reports:")
    for analysis_type, result in results.items():
        print(f"\\n    📊 {analysis_type.upper()}")
        print(f"       Summary: {result.summary}")
        if result.score is not None:
            print(f"       Score: {result.score:.2f}")
        if result.recommendations:
            print(f"       Recommendations: {len(result.recommendations)}")
            for rec in result.recommendations[:2]:  # Show first 2
                print(f"         - {rec}")
    
    # Show metrics collected during analysis
    print("\\n  📊 Metrics from Analysis:")
    
    # Show analytics-related metrics - this will depend on what's actually collected
    # Since track_api_calls is used, let's check for those metrics
    all_metrics = collector.get_all_metrics()
    if 'counters' in all_metrics:
        for metric_name, value in all_metrics['counters'].items():
            if 'analytics' in metric_name.lower() and value > 0:
                print(f"    {metric_name}: {value}")


@track_api_calls('demo_function')
async def demo_function_with_tracking():
    """Demo function to show metrics tracking."""
    await asyncio.sleep(0.1)  # Simulate some work
    return "demo_result"


async def demonstrate_metrics_tracking():
    """Demonstrate metrics tracking."""
    print("\\n📊 DEMONSTRATING METRICS TRACKING")
    print("=" * 60)
    
    collector = get_metrics_collector()
    
    # Call tracked function multiple times
    print("  Calling tracked function...")
    for i in range(5):
        result = await demo_function_with_tracking()
        print(f"    Call {i+1}: {result}")
    
    # Show collected metrics
    print("\\n  📈 Collected Metrics:")
    all_metrics = collector.get_all_metrics()
    
    if 'counters' in all_metrics:
        for metric_name, value in all_metrics['counters'].items():
            if 'demo_function' in metric_name:
                print(f"    {metric_name}: {value}")


async def main():
    """Run all demonstrations."""
    print("\\n" + "=" * 60)
    print("  Analytics Engine with Infrastructure Integration")
    print("  Simplified Demonstration")
    print("=" * 60)
    
    # Run demonstrations
    await demonstrate_metrics_tracking()
    await demonstrate_analytics_with_metrics()
    
    print("\\n" + "=" * 60)
    print("  ✅ All demonstrations completed successfully!")
    print("=" * 60 + "\\n")


if __name__ == "__main__":
    asyncio.run(main())