"""
Tests for enhanced chart functionality including new backends and export formats.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from src.charts import (
    ChartBackend,
    ChartConfiguration,
    ChartFactory,
    ChartGenerator,
    ChartResult,
    ChartType,
    ExportFormat,
    ExportOptions,
)


class TestChartModels:
    """Test enhanced chart models."""

    def test_chart_backend_enum(self):
        """Test ChartBackend enum values."""
        assert ChartBackend.MATPLOTLIB.value == "matplotlib"
        assert ChartBackend.PLOTLY.value == "plotly"

    def test_export_format_enum(self):
        """Test ExportFormat enum values."""
        assert ExportFormat.PNG.value == "png"
        assert ExportFormat.SVG.value == "svg"
        assert ExportFormat.PDF.value == "pdf"
        assert ExportFormat.HTML.value == "html"
        assert ExportFormat.JSON.value == "json"

    def test_export_options_defaults(self):
        """Test ExportOptions default values."""
        options = ExportOptions()
        assert options.format == ExportFormat.PNG
        assert options.dpi == 150
        assert options.transparent is False
        assert options.quality == 95

    def test_chart_configuration_with_backend(self):
        """Test ChartConfiguration with backend selection."""
        config = ChartConfiguration(
            title="Test Chart",
            x_label="X",
            y_label="Y",
            chart_type=ChartType.LINE,
            x_data=[1, 2, 3],
            y_data=[4, 5, 6],
            backend=ChartBackend.PLOTLY,
        )
        assert config.backend == ChartBackend.PLOTLY
        assert config.chart_type == ChartType.LINE


class TestChartFactory:
    """Test enhanced ChartFactory functionality."""

    def test_create_simple_chart(self):
        """Test creating chart with factory create method."""
        config = ChartFactory.create(
            chart_type=ChartType.BAR,
            data={"x": ["A", "B", "C"], "y": [10, 20, 30]},
            title="Test Bar Chart",
            x_label="Categories",
            y_label="Values",
        )

        assert config is not None
        assert config.title == "Test Bar Chart"
        assert config.chart_type == ChartType.BAR
        assert config.x_data == ["A", "B", "C"]
        assert config.y_data == [10, 20, 30]

    def test_create_chart_with_backend(self):
        """Test creating chart with specific backend."""
        config = ChartFactory.create(
            chart_type=ChartType.LINE,
            data=(["A", "B", "C"], [1, 2, 3]),
            backend=ChartBackend.PLOTLY,
            title="Plotly Chart",
        )

        assert config is not None
        assert config.backend == ChartBackend.PLOTLY

    def test_create_time_series_chart(self):
        """Test creating time series chart."""
        dates = [datetime.now() - timedelta(days=i) for i in range(5)]
        values = [10, 15, 12, 18, 20]

        config = ChartFactory.create(
            chart_type=ChartType.TIME_SERIES,
            data={"x": dates, "y": values},
            title="Time Series",
            x_label="Date",
            y_label="Value",
        )

        assert config is not None
        assert config.chart_type == ChartType.TIME_SERIES
        assert len(config.x_data) == 5

    def test_create_heatmap_chart(self):
        """Test creating heatmap chart."""
        config = ChartFactory.create(
            chart_type=ChartType.HEATMAP,
            data={
                "x": ["Mon", "Tue", "Wed"],
                "y": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
            },
            title="Activity Heatmap",
        )

        assert config is not None
        assert config.chart_type == ChartType.HEATMAP


class TestChartGeneratorMatplotlib:
    """Test ChartGenerator with Matplotlib backend."""

    @patch("matplotlib.pyplot.savefig")
    @patch("matplotlib.pyplot.close")
    def test_generate_bar_chart(self, mock_close, mock_savefig):
        """Test generating bar chart with matplotlib."""
        config = ChartConfiguration(
            title="Test Bar",
            x_label="X",
            y_label="Y",
            chart_type=ChartType.BAR,
            x_data=["A", "B", "C"],
            y_data=[10, 20, 30],
            backend=ChartBackend.MATPLOTLIB,
        )

        generator = ChartGenerator(config)
        result = generator.generate()

        assert result is not None
        assert result.chart_type == ChartType.BAR
        assert result.format in ["png", "svg", "pdf"]

    @patch("matplotlib.pyplot.savefig")
    @patch("matplotlib.pyplot.close")
    def test_generate_time_series(self, mock_close, mock_savefig):
        """Test generating time series chart."""
        dates = [datetime.now() - timedelta(days=i) for i in range(5)]
        config = ChartConfiguration(
            title="Time Series",
            x_label="Date",
            y_label="Value",
            chart_type=ChartType.TIME_SERIES,
            x_data=dates,
            y_data=[10, 15, 12, 18, 20],
            backend=ChartBackend.MATPLOTLIB,
        )

        generator = ChartGenerator(config)
        result = generator.generate()

        assert result is not None
        assert result.chart_type == ChartType.TIME_SERIES

    @patch("matplotlib.pyplot.savefig")
    @patch("matplotlib.pyplot.close")
    def test_generate_heatmap(self, mock_close, mock_savefig):
        """Test generating heatmap chart."""
        config = ChartConfiguration(
            title="Heatmap",
            x_label="X",
            y_label="Y",
            chart_type=ChartType.HEATMAP,
            x_data=["A", "B", "C"],
            y_data=[[1, 2, 3], [4, 5, 6], [7, 8, 9]],
            backend=ChartBackend.MATPLOTLIB,
        )

        generator = ChartGenerator(config)
        result = generator.generate()

        assert result is not None
        assert result.chart_type == ChartType.HEATMAP


class TestChartGeneratorPlotly:
    """Test ChartGenerator with Plotly backend."""

    @patch("plotly.io.to_image")
    def test_generate_plotly_bar_chart(self, mock_to_image):
        """Test generating bar chart with plotly."""
        mock_to_image.return_value = b"fake_image_data"

        config = ChartConfiguration(
            title="Plotly Bar",
            x_label="X",
            y_label="Y",
            chart_type=ChartType.BAR,
            x_data=["A", "B", "C"],
            y_data=[10, 20, 30],
            backend=ChartBackend.PLOTLY,
        )

        generator = ChartGenerator(config, backend=ChartBackend.PLOTLY)
        result = generator.generate()

        assert result is not None
        assert result.chart_type == ChartType.BAR

    @patch("plotly.io.write_html")
    def test_generate_plotly_html(self, mock_write_html):
        """Test generating HTML chart with plotly."""
        mock_write_html.side_effect = lambda fig, buf, **kwargs: buf.write(
            "<html>chart</html>"
        )

        config = ChartConfiguration(
            title="Interactive Chart",
            x_label="X",
            y_label="Y",
            chart_type=ChartType.LINE,
            x_data=[1, 2, 3],
            y_data=[4, 5, 6],
            backend=ChartBackend.PLOTLY,
        )

        export_options = ExportOptions(format=ExportFormat.HTML)
        generator = ChartGenerator(config, backend=ChartBackend.PLOTLY)
        result = generator.generate(export_options)

        assert result is not None
        assert result.format == "html"

    @patch("plotly.io.to_image")
    def test_generate_plotly_time_series(self, mock_to_image):
        """Test generating time series with plotly."""
        mock_to_image.return_value = b"fake_image_data"

        dates = [datetime.now() - timedelta(days=i) for i in range(5)]
        config = ChartConfiguration(
            title="Time Series",
            x_label="Date",
            y_label="Value",
            chart_type=ChartType.TIME_SERIES,
            x_data=dates,
            y_data=[10, 15, 12, 18, 20],
            backend=ChartBackend.PLOTLY,
        )

        generator = ChartGenerator(config, backend=ChartBackend.PLOTLY)
        result = generator.generate()

        assert result is not None


class TestExportFormats:
    """Test different export formats."""

    @patch("matplotlib.pyplot.savefig")
    @patch("matplotlib.pyplot.close")
    def test_export_png(self, mock_close, mock_savefig):
        """Test exporting as PNG."""
        config = ChartConfiguration(
            title="Test",
            x_label="X",
            y_label="Y",
            chart_type=ChartType.BAR,
            x_data=[1, 2, 3],
            y_data=[4, 5, 6],
        )

        export_options = ExportOptions(format=ExportFormat.PNG, dpi=300)
        generator = ChartGenerator(config)
        result = generator.generate(export_options)

        assert result.format == "png"

    @patch("matplotlib.pyplot.savefig")
    @patch("matplotlib.pyplot.close")
    def test_export_svg(self, mock_close, mock_savefig):
        """Test exporting as SVG."""
        config = ChartConfiguration(
            title="Test",
            x_label="X",
            y_label="Y",
            chart_type=ChartType.LINE,
            x_data=[1, 2, 3],
            y_data=[4, 5, 6],
        )

        export_options = ExportOptions(format=ExportFormat.SVG)
        generator = ChartGenerator(config)
        result = generator.generate(export_options)

        assert result.format == "svg"

    @patch("matplotlib.pyplot.savefig")
    @patch("matplotlib.pyplot.close")
    def test_export_pdf(self, mock_close, mock_savefig):
        """Test exporting as PDF."""
        config = ChartConfiguration(
            title="Test",
            x_label="X",
            y_label="Y",
            chart_type=ChartType.SCATTER,
            x_data=[1, 2, 3],
            y_data=[4, 5, 6],
        )

        export_options = ExportOptions(format=ExportFormat.PDF)
        generator = ChartGenerator(config)
        result = generator.generate(export_options)

        assert result.format == "pdf"


class TestBackwardCompatibility:
    """Test that existing functionality still works."""

    @patch("matplotlib.pyplot.savefig")
    @patch("matplotlib.pyplot.close")
    def test_legacy_generate_method(self, mock_close, mock_savefig):
        """Test that old generate() signature still works."""
        config = ChartConfiguration(
            title="Legacy Test",
            x_label="X",
            y_label="Y",
            chart_type=ChartType.BAR,
            x_data=[1, 2],
            y_data=[3, 4],
        )

        generator = ChartGenerator(config)
        result = generator.generate()  # No export_options

        assert result is not None
        assert hasattr(result, "image_data")
        assert hasattr(result, "format")
