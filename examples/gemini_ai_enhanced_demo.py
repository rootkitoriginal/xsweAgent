"""
Enhanced Gemini AI Integration Demo
Demonstrates the multiple analysis capabilities of the enhanced Gemini AI system.
"""

import asyncio
from datetime import datetime

from src.gemini_integration import (
    AIConfig,
    CodeSnippet,
    GeminiAnalyzer,
    GeminiClient,
)
from src.github_monitor.models import Issue, Label


async def demo_code_analysis():
    """Demonstrate code analysis capabilities."""
    print("\n" + "=" * 60)
    print("1. CODE ANALYSIS DEMO")
    print("=" * 60)

    # Initialize client with custom config
    config = AIConfig(
        model="gemini-2.5-flash",
        temperature=0.2,
        max_output_tokens=2048,
    )
    client = GeminiClient(config=config)
    analyzer = GeminiAnalyzer(client=client)

    # Analyze a code snippet
    snippet = CodeSnippet(
        content="""
def process_user_data(users):
    result = []
    for user in users:
        if user['age'] > 18:
            result.append(user)
    return result
""",
        language="python",
        filename="user_processor.py",
        context="Function to filter adult users",
    )

    print("\nAnalyzing code snippet...")
    result = await analyzer.analyze_code(snippet)

    if result.is_successful():
        print(f"\n✓ Analysis completed successfully!")
        print(f"  Model: {result.model_used}")
        print(f"\n  Summary: {result.report.summary}")
        print(f"  Complexity Score: {result.report.complexity_score:.2f}")
        print(f"  Maintainability: {result.report.maintainability_index:.2f}")
        print(f"  Tags: {', '.join(result.report.tags)}")

        if result.report.suggestions:
            print(f"\n  Suggestions ({len(result.report.suggestions)}):")
            for i, suggestion in enumerate(result.report.suggestions[:3], 1):
                print(f"    {i}. [{suggestion.severity}] {suggestion.description}")
    else:
        print(f"✗ Analysis failed: {result.error_message}")

    print(f"\n  Token Usage: {result.usage_metadata}")


async def demo_issue_analysis():
    """Demonstrate issue intelligence analysis."""
    print("\n" + "=" * 60)
    print("2. ISSUE INTELLIGENCE DEMO")
    print("=" * 60)

    analyzer = GeminiAnalyzer()

    # Create a sample issue
    issue = Issue(
        id=1,
        number=42,
        title="Critical: Authentication service failing",
        body="Users are unable to login. Getting 500 errors from auth service. "
        "Started happening after recent deployment.",
        state="open",
        labels=[Label(id=1, name="bug", color="red")],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    print(f"\nAnalyzing issue #{issue.number}: {issue.title}")
    result = await analyzer.issue_analysis(issue)

    if result.status.value == "completed":
        print(f"\n✓ Issue Analysis completed!")
        print(f"  Category: {result.category}")
        print(f"  Severity: {result.severity}")
        print(f"  Estimated Resolution: {result.estimated_resolution_hours} hours")
        print(f"  Confidence: {result.confidence_score:.2%}")
        print(f"  Root Cause: {result.root_cause}")
        print(f"  Recommended Labels: {', '.join(result.recommended_labels)}")
    else:
        print(f"✗ Analysis failed: {result.error_message}")


async def demo_sentiment_analysis():
    """Demonstrate sentiment analysis."""
    print("\n" + "=" * 60)
    print("3. SENTIMENT ANALYSIS DEMO")
    print("=" * 60)

    analyzer = GeminiAnalyzer()

    # Analyze positive sentiment
    positive_text = "This is an amazing feature! Really love how it works. Great job!"
    print(f"\nAnalyzing text: '{positive_text[:50]}...'")
    result = await analyzer.sentiment_analysis(positive_text)

    if result.status.value == "completed":
        print(f"\n✓ Sentiment: {result.sentiment.value.upper()}")
        print(f"  Confidence: {result.confidence_score:.2%}")
        print(f"  Positive: {result.positive_score:.2%}")
        print(f"  Negative: {result.negative_score:.2%}")
        print(f"  Neutral: {result.neutral_score:.2%}")
        print(f"  Emotional Tone: {result.emotional_tone}")
    else:
        print(f"✗ Analysis failed: {result.error_message}")


async def demo_priority_analysis():
    """Demonstrate priority recommendation."""
    print("\n" + "=" * 60)
    print("4. PRIORITY ANALYSIS DEMO")
    print("=" * 60)

    analyzer = GeminiAnalyzer()

    issue = Issue(
        id=2,
        number=43,
        title="Payment processing completely broken",
        body="Critical bug: Customers cannot complete purchases. "
        "Affecting all payment providers. Revenue impact is significant.",
        state="open",
        labels=[
            Label(id=1, name="bug", color="red"),
            Label(id=2, name="payment", color="yellow"),
        ],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    print(f"\nAnalyzing priority for issue #{issue.number}")
    result = await analyzer.priority_analysis(issue)

    if result.status.value == "completed":
        print(f"\n✓ Priority Recommendation: {result.priority.value.upper()}")
        print(f"  Business Impact: {result.business_impact_score:.2%}")
        print(f"  Technical Complexity: {result.technical_complexity_score:.2%}")
        print(f"  Urgency: {result.urgency_score:.2%}")
        print(f"  Overall Score: {result.overall_priority_score:.2%}")
        print(f"  Justification: {result.justification}")
        print(f"  Estimated Effort: {result.estimated_effort_hours} hours")
    else:
        print(f"✗ Analysis failed: {result.error_message}")


async def demo_trend_prediction():
    """Demonstrate trend prediction."""
    print("\n" + "=" * 60)
    print("5. TREND PREDICTION DEMO")
    print("=" * 60)

    analyzer = GeminiAnalyzer()

    # Historical data
    historical_data = [
        {"week": 1, "issues_opened": 15, "issues_closed": 12, "avg_resolution_hours": 24},
        {"week": 2, "issues_opened": 18, "issues_closed": 14, "avg_resolution_hours": 28},
        {"week": 3, "issues_opened": 22, "issues_closed": 16, "avg_resolution_hours": 32},
        {"week": 4, "issues_opened": 25, "issues_closed": 18, "avg_resolution_hours": 36},
    ]

    print("\nPredicting trends based on 4 weeks of data...")
    result = await analyzer.trend_prediction(historical_data)

    if result.status.value == "completed":
        print(f"\n✓ Trend Forecast:")
        print(f"  Predicted Issues: {result.predicted_issue_count}")
        print(f"  Predicted Resolution Time: {result.predicted_resolution_time} hours")
        print(f"  Quality Trend: {result.quality_trend}")
        print(f"  Workload Forecast: {result.workload_forecast}")
        print(f"  Confidence: {result.confidence_score:.2%}")

        if result.insights:
            print(f"\n  Key Insights:")
            for insight in result.insights:
                print(f"    • {insight}")

        if result.recommendations:
            print(f"\n  Recommendations:")
            for rec in result.recommendations:
                print(f"    • {rec}")
    else:
        print(f"✗ Analysis failed: {result.error_message}")


async def demo_collaboration_analysis():
    """Demonstrate collaboration insights."""
    print("\n" + "=" * 60)
    print("6. COLLABORATION ANALYSIS DEMO")
    print("=" * 60)

    analyzer = GeminiAnalyzer()

    # Team collaboration data
    team_data = {
        "team_size": 5,
        "avg_review_time_hours": 12,
        "code_review_participation_rate": 0.85,
        "pair_programming_sessions": 8,
        "knowledge_sharing_meetings": 2,
        "cross_functional_prs": 15,
        "avg_pr_comments": 4.2,
    }

    print("\nAnalyzing team collaboration patterns...")
    result = await analyzer.collaboration_analysis(team_data)

    if result.status.value == "completed":
        print(f"\n✓ Collaboration Insights:")
        print(f"  Team Health Score: {result.team_health_score:.2%}")
        print(f"  Communication: {result.communication_score:.2%}")
        print(f"  Knowledge Sharing: {result.knowledge_sharing_score:.2%}")
        print(f"  Efficiency: {result.collaboration_efficiency:.2%}")

        if result.bottlenecks:
            print(f"\n  Identified Bottlenecks:")
            for bottleneck in result.bottlenecks:
                print(f"    ⚠ {bottleneck}")

        if result.top_collaborators:
            print(f"\n  Top Collaborators: {', '.join(result.top_collaborators)}")

        if result.recommendations:
            print(f"\n  Recommendations:")
            for rec in result.recommendations:
                print(f"    • {rec}")
    else:
        print(f"✗ Analysis failed: {result.error_message}")


async def demo_usage_tracking():
    """Demonstrate usage tracking and cost monitoring."""
    print("\n" + "=" * 60)
    print("7. USAGE TRACKING DEMO")
    print("=" * 60)

    client = GeminiClient()

    # Simulate some API calls
    await client.generate_content("Test prompt 1")
    await client.generate_content("Test prompt 2")

    # Get usage stats
    stats = client.get_usage_stats()
    print(f"\n✓ Usage Statistics:")
    print(f"  Total Requests: {stats['total_requests']}")
    print(f"  Total Tokens: {stats['total_tokens']}")
    print(f"  Model: {stats['model']}")


async def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("ENHANCED GEMINI AI INTEGRATION DEMO")
    print("=" * 60)
    print("\nThis demo showcases the multiple AI analysis capabilities:")
    print("1. Code Analysis - Quality, complexity, and suggestions")
    print("2. Issue Intelligence - Categorization and insights")
    print("3. Sentiment Analysis - Emotional tone detection")
    print("4. Priority Analysis - Smart issue prioritization")
    print("5. Trend Prediction - Forecasting future patterns")
    print("6. Collaboration Analysis - Team health insights")
    print("7. Usage Tracking - Cost and usage monitoring")

    try:
        # Note: These demos will fail without a valid GEMINI_API_KEY
        # Uncomment individual demos as needed with proper API key

        # await demo_code_analysis()
        # await demo_issue_analysis()
        # await demo_sentiment_analysis()
        # await demo_priority_analysis()
        # await demo_trend_prediction()
        # await demo_collaboration_analysis()
        # await demo_usage_tracking()

        print("\n" + "=" * 60)
        print("Demo completed!")
        print("=" * 60)
        print(
            "\nNote: To run live demos, set GEMINI_API_KEY environment variable"
        )
        print("and uncomment the desired demo functions in main().")

    except Exception as e:
        print(f"\n✗ Demo error: {e}")
        print(
            "\nMake sure GEMINI_API_KEY is set in your environment to run live demos."
        )


if __name__ == "__main__":
    asyncio.run(main())
