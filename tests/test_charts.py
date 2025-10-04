"""
Tests for the Chart Generation module.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

from src.charts.factory import ChartFactory
from src.charts.generator import ChartGenerator
from src.charts.models import ChartType, ChartConfiguration
from src.analytics.strategies import AnalysisResult, AnalysisType


@pytest.fixture
def productivity_analysis_result():
    """Fixture for a sample productivity analysis result."""
    context = MagicMock()
    context.repository_name = "test/repo"
    return AnalysisResult(
        analysis_type=AnalysisType.PRODUCTIVITY,
        score=0.8,
        summary="Good productivity.",
        metrics={"open_issues": 10, "closed_issues": 40},
        details={"issues_by_state": {"open": 10, "closed": 40}},
        context=context,
    )


def test_chart_factory_productivity_bar(productivity_analysis_result):
    """Test creating a bar chart from a productivity result."""
    chart_data = ChartFactory.create_chart(productivity_analysis_result, ChartType.BAR)

    assert chart_data is not None
    config = chart_data.config
    assert config.chart_type == ChartType.BAR
    assert config.title == "Open vs. Closed Issues"
    assert config.x_data == ["Open", "Closed"]
    assert config.y_data == [10, 40]


def test_chart_factory_productivity_pie(productivity_analysis_result):
    """Test creating a pie chart from a productivity result."""
    chart_data = ChartFactory.create_chart(productivity_analysis_result, ChartType.PIE)

    assert chart_data is not None
    config = chart_data.config
    assert config.chart_type == ChartType.PIE
    assert config.title == "Issue Distribution by State"
    assert config.x_data == ["open", "closed"]
    assert config.y_data == [10, 40]


@patch("matplotlib.pyplot.show")
def test_chart_generator(mock_show):
    """Test the ChartGenerator produces an image."""
    config = ChartConfiguration(
        title="Test Chart",
        x_label="X",
        y_label="Y",
        chart_type=ChartType.LINE,
        x_data=[1, 2, 3],
        y_data=[2, 4, 6],
    )

    generator = ChartGenerator(config)
    generated_chart = generator.generate()

    assert generated_chart is not None
    assert generated_chart.format == "png"
    assert len(generated_chart.image_data) > 0
    assert generated_chart.filename.startswith("test_chart")
