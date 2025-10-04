"""
Analytics Engine Module - Main analytics coordination engine.
Manages multiple analysis strategies and provides consolidated insights.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Type
import logging
from dataclasses import dataclass, field

from ..github_monitor.models import Issue, IssueState
from .strategies import AnalysisStrategy, AnalysisResult, AnalysisType


logger = logging.getLogger(__name__)


@dataclass
class AnalyticsConfiguration:
    """Configuration for analytics engine behavior."""

    enabled_analyses: Set[AnalysisType] = field(
        default_factory=lambda: {
            AnalysisType.PRODUCTIVITY,
            AnalysisType.VELOCITY,
            AnalysisType.BURNDOWN,
            AnalysisType.QUALITY,
        }
    )

    time_window_days: int = 90
    minimum_issues_for_analysis: int = 5
    velocity_calculation_period: int = 14  # days for velocity calculations
    trend_analysis_periods: int = 4  # number of periods for trend analysis
    cache_results: bool = True
    cache_ttl_minutes: int = 30

    # Analysis thresholds
    slow_resolution_threshold_days: int = 30
    high_activity_threshold: int = 10  # comments/updates
    quality_score_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "resolution_time": 0.3,
            "comment_quality": 0.25,
            "documentation": 0.2,
            "testing": 0.15,
            "code_review": 0.1,
        }
    )


@dataclass
class AnalyticsContext:
    """Context information for analytics processing."""

    repository_name: str
    analysis_timestamp: datetime
    data_freshness: datetime
    total_issues: int
    issues_in_window: int
    configuration: AnalyticsConfiguration
    metadata: Dict[str, Any] = field(default_factory=dict)


class AnalyticsEngine:
    """
    Main analytics engine that coordinates multiple analysis strategies
    to provide comprehensive insights into GitHub issues data.
    """

    def __init__(self, configuration: Optional[AnalyticsConfiguration] = None):
        self.config = configuration or AnalyticsConfiguration()
        self._strategies: Dict[AnalysisType, AnalysisStrategy] = {}
        self._result_cache: Dict[str, tuple] = {}  # (result, timestamp)
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def register_strategy(self, strategy: AnalysisStrategy) -> None:
        """Register an analysis strategy with the engine."""
        self._strategies[strategy.analysis_type] = strategy
        self._logger.info(f"Registered strategy: {strategy.analysis_type.value}")

    def unregister_strategy(self, analysis_type: AnalysisType) -> bool:
        """Unregister an analysis strategy."""
        if analysis_type in self._strategies:
            del self._strategies[analysis_type]
            self._logger.info(f"Unregistered strategy: {analysis_type.value}")
            return True
        return False

    def get_registered_strategies(self) -> List[AnalysisType]:
        """Get list of currently registered analysis types."""
        return list(self._strategies.keys())

    async def analyze(
        self,
        issues: List[Issue],
        repository_name: str,
        custom_config: Optional[AnalyticsConfiguration] = None,
    ) -> Dict[str, AnalysisResult]:
        """
        Run comprehensive analysis on GitHub issues data.

        Args:
            issues: List of GitHub issues to analyze
            repository_name: Name of the repository being analyzed
            custom_config: Optional custom configuration for this analysis

        Returns:
            Dictionary mapping analysis type names to results
        """
        config = custom_config or self.config

        # Validate input data
        if len(issues) < config.minimum_issues_for_analysis:
            self._logger.warning(
                f"Insufficient issues for analysis: {len(issues)} < {config.minimum_issues_for_analysis}"
            )
            return {}

        # Create analysis context
        context = self._create_context(issues, repository_name, config)

        # Filter issues by time window
        filtered_issues = self._filter_issues_by_timeframe(
            issues, config.time_window_days
        )

        if not filtered_issues:
            self._logger.warning("No issues found in specified time window")
            return {}

        # Run enabled analyses
        results = {}
        analysis_tasks = []

        for analysis_type in config.enabled_analyses:
            if analysis_type not in self._strategies:
                self._logger.warning(
                    f"No strategy registered for {analysis_type.value}"
                )
                continue

            # Check cache first
            cache_key = self._get_cache_key(analysis_type, context)
            if config.cache_results and self._is_cache_valid(
                cache_key, config.cache_ttl_minutes
            ):
                cached_result, _ = self._result_cache[cache_key]
                results[analysis_type.value] = cached_result
                continue

            # Create analysis task
            strategy = self._strategies[analysis_type]
            task = self._run_strategy_analysis(strategy, filtered_issues, context)
            analysis_tasks.append((analysis_type, task))

        # Execute analyses concurrently
        if analysis_tasks:
            task_results = await asyncio.gather(
                *[task for _, task in analysis_tasks], return_exceptions=True
            )

            for (analysis_type, _), result in zip(analysis_tasks, task_results):
                if isinstance(result, Exception):
                    self._logger.error(
                        f"Analysis failed for {analysis_type.value}: {result}"
                    )
                    continue

                results[analysis_type.value] = result

                # Cache successful results
                if config.cache_results:
                    cache_key = self._get_cache_key(analysis_type, context)
                    self._result_cache[cache_key] = (result, datetime.now())

        self._logger.info(f"Completed analysis with {len(results)} successful results")
        return results

    async def _run_strategy_analysis(
        self, strategy: AnalysisStrategy, issues: List[Issue], context: AnalyticsContext
    ) -> AnalysisResult:
        """Run a single strategy analysis with error handling."""
        try:
            return await strategy.analyze(issues, context)
        except Exception as e:
            self._logger.error(f"Strategy {strategy.analysis_type.value} failed: {e}")
            raise

    def _create_context(
        self, issues: List[Issue], repository_name: str, config: AnalyticsConfiguration
    ) -> AnalyticsContext:
        """Create analysis context from current state."""
        now = datetime.now()

        # Calculate data freshness (most recent issue update)
        data_freshness = now
        if issues:
            latest_update = max(
                issue.updated_at for issue in issues if issue.updated_at
            )
            if latest_update:
                data_freshness = latest_update

        # Filter issues for time window calculation
        window_start = now - timedelta(days=config.time_window_days)
        issues_in_window = len(
            [
                issue
                for issue in issues
                if issue.created_at and issue.created_at >= window_start
            ]
        )

        return AnalyticsContext(
            repository_name=repository_name,
            analysis_timestamp=now,
            data_freshness=data_freshness,
            total_issues=len(issues),
            issues_in_window=issues_in_window,
            configuration=config,
            metadata={
                "engine_version": "1.0",
                "analysis_strategies": [t.value for t in config.enabled_analyses],
                "cache_enabled": config.cache_results,
            },
        )

    def _filter_issues_by_timeframe(
        self, issues: List[Issue], days: int
    ) -> List[Issue]:
        """Filter issues to those created within the specified timeframe."""
        cutoff_date = datetime.now() - timedelta(days=days)

        return [
            issue
            for issue in issues
            if issue.created_at and issue.created_at >= cutoff_date
        ]

    def _get_cache_key(
        self, analysis_type: AnalysisType, context: AnalyticsContext
    ) -> str:
        """Generate cache key for analysis result."""
        return f"{analysis_type.value}:{context.repository_name}:{context.issues_in_window}:{context.configuration.time_window_days}"

    def _is_cache_valid(self, cache_key: str, ttl_minutes: int) -> bool:
        """Check if cached result is still valid."""
        if cache_key not in self._result_cache:
            return False

        _, cached_time = self._result_cache[cache_key]
        age_minutes = (datetime.now() - cached_time).total_seconds() / 60

        return age_minutes <= ttl_minutes

    def clear_cache(self) -> None:
        """Clear all cached analysis results."""
        self._result_cache.clear()
        self._logger.info("Analytics cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get statistics about cache usage."""
        return {
            "total_cached_results": len(self._result_cache),
            "cache_size_bytes": sum(
                len(str(result)) for result, _ in self._result_cache.values()
            ),
        }

    async def get_summary_insights(
        self, analysis_results: Dict[str, AnalysisResult]
    ) -> Dict[str, Any]:
        """
        Generate high-level summary insights from analysis results.

        Args:
            analysis_results: Dictionary of analysis results

        Returns:
            Summary insights and key metrics
        """
        insights = {
            "overall_health": "unknown",
            "key_metrics": {},
            "recommendations": [],
            "alerts": [],
            "trends": {},
        }

        if not analysis_results:
            return insights

        # Extract key metrics from each analysis
        total_score = 0
        score_count = 0

        for analysis_name, result in analysis_results.items():
            if result.score is not None:
                total_score += result.score
                score_count += 1

            # Add key metrics
            if result.metrics:
                insights["key_metrics"][analysis_name] = result.metrics

            # Extract recommendations
            if result.recommendations:
                insights["recommendations"].extend(result.recommendations)

            # Check for alerts based on thresholds
            if result.score is not None and result.score < 0.5:
                insights["alerts"].append(
                    f"Low performance in {analysis_name}: {result.score:.2f}"
                )

        # Calculate overall health score
        if score_count > 0:
            overall_score = total_score / score_count

            if overall_score >= 0.8:
                insights["overall_health"] = "excellent"
            elif overall_score >= 0.6:
                insights["overall_health"] = "good"
            elif overall_score >= 0.4:
                insights["overall_health"] = "fair"
            else:
                insights["overall_health"] = "needs_attention"

        return insights


# Factory function for creating pre-configured analytics engine
async def create_analytics_engine(
    configuration: Optional[AnalyticsConfiguration] = None,
) -> AnalyticsEngine:
    """
    Factory function to create a fully configured analytics engine.

    Args:
        configuration: Optional custom configuration

    Returns:
        Configured AnalyticsEngine instance
    """
    from .strategies import (
        ProductivityAnalysisStrategy,
        VelocityAnalysisStrategy,
        BurndownAnalysisStrategy,
        QualityAnalysisStrategy,
    )

    engine = AnalyticsEngine(configuration)

    # Register default strategies
    engine.register_strategy(ProductivityAnalysisStrategy())
    engine.register_strategy(VelocityAnalysisStrategy())
    engine.register_strategy(BurndownAnalysisStrategy())
    engine.register_strategy(QualityAnalysisStrategy())

    return engine
