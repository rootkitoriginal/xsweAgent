"""
Example: Analytics Engine Usage

This example demonstrates how to use the analytics engine to analyze
GitHub issues data without infrastructure dependencies.
"""

import asyncio
from datetime import datetime, timedelta

# Import analytics engine
from src.analytics.engine import AnalyticsConfiguration, create_analytics_engine
from src.github_monitor.models import Issue, IssueState


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


async def demonstrate_analytics():
    """Demonstrate analytics engine functionality."""
    print("\\n🧮 DEMONSTRATING ANALYTICS ENGINE")
    print("=" * 50)
    
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
    
    # Run analysis
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
    
    print(f"\\n  � Analysis Statistics:")
    print(f"    Total analyses: {len(results)}")
    print(f"    Issues processed: {len(issues)}")
    
    return results


async def main():
    """Run analytics demonstration."""
    print("\\n" + "=" * 50)
    print("  Analytics Engine Demonstration")
    print("=" * 50)
    
    # Run demonstration
    results = await demonstrate_analytics()
    
    print("\\n" + "=" * 50)
    print("  ✅ Analytics demonstration completed successfully!")
    print("=" * 50 + "\\n")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())