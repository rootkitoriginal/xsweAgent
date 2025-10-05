"""
Chart Factory - Creates chart configurations from analytics results.
This module acts as a factory for generating ChartData objects.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..analytics.strategies import AnalysisResult, AnalysisType
from ..config.logging_config import get_logger
from ..utils import retry, RetryPolicies
from .models import ChartBackend, ChartConfiguration, ChartData, ChartType

logger = get_logger(__name__)


class ChartFactory:
    """
    Factory class to create chart configurations from analytics results or raw data.
    Supports multiple chart types and backends with infrastructure integration.
    """

    @staticmethod
    @retry(policy=RetryPolicies.FAST)
    def create(
        chart_type: ChartType,
        data: Any,
        backend: ChartBackend = ChartBackend.MATPLOTLIB,
        **kwargs
    ) -> Optional[ChartConfiguration]:
        """
        Create a chart configuration with specified type and backend.

        This is the main factory method for creating charts from raw data.

        Args:
            chart_type: Type of chart to create
            data: Chart data (format depends on chart type)
            backend: Rendering backend (matplotlib or plotly)
            **kwargs: Additional configuration (title, labels, styling, etc.)

        Returns:
            ChartConfiguration ready for rendering

        Example:
            config = ChartFactory.create(
                chart_type=ChartType.TIME_SERIES,
                data={"dates": [...], "values": [...]},
                backend=ChartBackend.PLOTLY,
                title="Issue Trends",
                x_label="Date",
                y_label="Count"
            )
        """
        try:
            # Extract common parameters
            title = kwargs.get("title", f"{chart_type.value.title()} Chart")
            x_label = kwargs.get("x_label", "X Axis")
            y_label = kwargs.get("y_label", "Y Axis")

            # Parse data based on format
            if isinstance(data, dict):
                x_data = data.get("x_data", data.get("x", []))
                y_data = data.get("y_data", data.get("y", []))
            elif isinstance(data, tuple) and len(data) == 2:
                x_data, y_data = data
            else:
                raise ValueError("Data must be dict with x/y keys or tuple of (x, y)")

            config = ChartConfiguration(
                title=title,
                x_label=x_label,
                y_label=y_label,
                chart_type=chart_type,
                x_data=x_data,
                y_data=y_data,
                backend=backend,
                **{k: v for k, v in kwargs.items() if k not in ["title", "x_label", "y_label"]}
            )

            logger.info(
                "Created chart configuration",
                chart_type=chart_type.value,
                backend=backend.value,
                data_points=len(x_data)
            )

            return config

        except Exception as e:
            logger.error(
                "Failed to create chart configuration",
                chart_type=chart_type.value,
                error=str(e)
            )
            return None

    @staticmethod
    def create_chart(
        analysis_result: AnalysisResult, chart_type: Optional[ChartType] = None
    ) -> Optional[ChartData]:
        """
        Create a chart configuration based on the analysis result.

        Legacy method for backward compatibility with analytics integration.

        Args:
            analysis_result: The result from an analytics strategy.
            chart_type: Optional specific chart type to generate.

        Returns:
            A ChartData object ready for rendering, or None if not applicable.
        """

        handler_map = {
            AnalysisType.PRODUCTIVITY: ChartFactory._create_productivity_chart,
            AnalysisType.VELOCITY: ChartFactory._create_velocity_chart,
            AnalysisType.BURNDOWN: ChartFactory._create_burndown_chart,
            AnalysisType.QUALITY: ChartFactory._create_quality_score_chart,
        }

        handler = handler_map.get(analysis_result.analysis_type)

        if not handler:
            logger.warning(
                f"No chart handler for analysis type: {analysis_result.analysis_type}"
            )
            return None

        try:
            return handler(analysis_result, chart_type)
        except Exception as e:
            logger.error(
                f"Failed to create chart for {analysis_result.analysis_type}: {e}"
            )
            return None

    # --- Chart Creation Handlers ---

    @staticmethod
    def _create_productivity_chart(
        result: AnalysisResult, chart_type: Optional[ChartType]
    ) -> Optional[ChartData]:
        """Creates charts for productivity analysis."""

        # Default to a bar chart of open vs closed issues
        if chart_type is None or chart_type == ChartType.BAR:
            metrics = result.metrics
            if "open_issues" not in metrics or "closed_issues" not in metrics:
                return None

            config = ChartConfiguration(
                title="Open vs. Closed Issues",
                x_label="Status",
                y_label="Number of Issues",
                chart_type=ChartType.BAR,
                x_data=["Open", "Closed"],
                y_data=[metrics["open_issues"], metrics["closed_issues"]],
            )
            return ChartData(
                config=config, source_repository=result.context.repository_name
            )

        # Pie chart of issue states
        if chart_type == ChartType.PIE:
            if "issues_by_state" not in result.details:
                return None

            labels = list(result.details["issues_by_state"].keys())
            sizes = list(result.details["issues_by_state"].values())

            config = ChartConfiguration(
                title="Issue Distribution by State",
                x_label="State",
                y_label="Count",
                chart_type=ChartType.PIE,
                x_data=labels,
                y_data=sizes,
            )
            return ChartData(
                config=config, source_repository=result.context.repository_name
            )

        return None

    @staticmethod
    def _create_velocity_chart(
        result: AnalysisResult, chart_type: Optional[ChartType]
    ) -> Optional[ChartData]:
        """Creates a velocity chart."""
        if "velocity_per_period" not in result.details:
            return None

        periods = [p["period"] for p in result.details["velocity_per_period"]]
        velocities = [p["completed"] for p in result.details["velocity_per_period"]]

        config = ChartConfiguration(
            title="Team Velocity",
            x_label="Period",
            y_label="Issues Completed",
            chart_type=ChartType.BAR,
            x_data=periods,
            y_data=velocities,
            average_line=result.metrics.get("average_velocity"),
        )
        return ChartData(
            config=config, source_repository=result.context.repository_name
        )

    @staticmethod
    def _create_burndown_chart(
        result: AnalysisResult, chart_type: Optional[ChartType]
    ) -> Optional[ChartData]:
        """Creates a burndown chart."""
        if "burndown_data" not in result.details:
            return None

        dates = [d["date"] for d in result.details["burndown_data"]]
        remaining = [d["remaining"] for d in result.details["burndown_data"]]
        ideal = [d["ideal"] for d in result.details["burndown_data"]]

        config = ChartConfiguration(
            title="Sprint Burndown Chart",
            x_label="Date",
            y_label="Remaining Work (Issues)",
            chart_type=ChartType.BURNDOWN,
            x_data=dates,
            y_data={"Actual": remaining},
            ideal_line=ideal,
        )
        return ChartData(
            config=config, source_repository=result.context.repository_name
        )

    @staticmethod
    def _create_quality_score_chart(
        result: AnalysisResult, chart_type: Optional[ChartType]
    ) -> Optional[ChartData]:
        """Creates a chart for quality scores over time."""
        if "quality_trend" not in result.details:
            return None

        dates = [d["date"] for d in result.details["quality_trend"]]
        scores = [d["score"] for d in result.details["quality_trend"]]

        config = ChartConfiguration(
            title="Quality Score Over Time",
            x_label="Date",
            y_label="Quality Score",
            chart_type=ChartType.LINE,
            x_data=dates,
            y_data=scores,
        )
        return ChartData(
            config=config, source_repository=result.context.repository_name
        )
