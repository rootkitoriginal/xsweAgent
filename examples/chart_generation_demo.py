"""
Chart Generation Demo - Demonstrating the enhanced chart generation capabilities.

This example shows how to use the ChartFactory and ChartGenerator with:
- Multiple backends (Matplotlib and Plotly)
- Different chart types (including new TIME_SERIES and HEATMAP)
- Various export formats (PNG, SVG, PDF, HTML)
- Infrastructure integration (retry logic, metrics, error handling)
"""

from datetime import datetime, timedelta
from pathlib import Path

from src.charts import (
    ChartBackend,
    ChartFactory,
    ChartGenerator,
    ChartType,
    ExportFormat,
    ExportOptions,
)
from src.config.logging_config import get_logger
from src.utils import get_metrics_collector

logger = get_logger(__name__)


def create_output_directory():
    """Create output directory for generated charts."""
    output_dir = Path("exports/charts")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def demo_bar_chart():
    """Demonstrate bar chart generation."""
    logger.info("Generating bar chart demo")

    # Create chart configuration using factory
    config = ChartFactory.create(
        chart_type=ChartType.BAR,
        data={"x": ["Open", "Closed", "In Progress"], "y": [15, 45, 12]},
        title="Issues by Status",
        x_label="Status",
        y_label="Count",
    )

    # Generate chart with Matplotlib (PNG)
    generator = ChartGenerator(config, backend=ChartBackend.MATPLOTLIB)
    result = generator.generate(ExportOptions(format=ExportFormat.PNG))

    output_dir = create_output_directory()
    result.save(output_dir / "bar_chart.png")
    logger.info(f"Bar chart saved to {output_dir / 'bar_chart.png'}")


def demo_time_series_chart():
    """Demonstrate time series chart with trend analysis."""
    logger.info("Generating time series chart demo")

    # Generate sample time series data
    dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]
    issue_counts = [10 + i * 0.5 + (i % 7) * 2 for i in range(30)]

    config = ChartFactory.create(
        chart_type=ChartType.TIME_SERIES,
        data={"x": dates, "y": issue_counts},
        title="Issue Creation Trend (Last 30 Days)",
        x_label="Date",
        y_label="Issues Created",
        backend=ChartBackend.MATPLOTLIB,
    )

    generator = ChartGenerator(config)
    result = generator.generate(ExportOptions(format=ExportFormat.PNG, dpi=200))

    output_dir = create_output_directory()
    result.save(output_dir / "time_series.png")
    logger.info(f"Time series chart saved to {output_dir / 'time_series.png'}")


def demo_heatmap_chart():
    """Demonstrate heatmap for activity patterns."""
    logger.info("Generating heatmap chart demo")

    # Sample activity data (days x hours)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    activity_data = [
        [2, 1, 0, 0, 0, 0, 1, 3, 8, 12, 10, 8, 6, 10, 12, 9, 5, 3, 2, 1, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 2, 5, 10, 15, 12, 9, 7, 11, 14, 10, 6, 4, 2, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 3, 7, 11, 14, 13, 10, 8, 12, 15, 11, 7, 5, 3, 1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0, 2, 6, 9, 13, 11, 8, 6, 10, 13, 9, 5, 3, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 2, 4, 7, 10, 8, 6, 5, 8, 10, 7, 4, 2, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 3, 2, 2, 3, 4, 3, 2, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 1, 1, 2, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0],
    ]

    hours = [f"{h:02d}:00" for h in range(24)]

    config = ChartFactory.create(
        chart_type=ChartType.HEATMAP,
        data={"x": hours, "y": activity_data},
        title="Development Activity Heatmap (Day x Hour)",
        x_label="Hour of Day",
        y_label="Day of Week",
    )

    generator = ChartGenerator(config)
    result = generator.generate(ExportOptions(format=ExportFormat.PNG))

    output_dir = create_output_directory()
    result.save(output_dir / "heatmap.png")
    logger.info(f"Heatmap saved to {output_dir / 'heatmap.png'}")


def demo_plotly_interactive():
    """Demonstrate interactive Plotly chart with HTML export."""
    logger.info("Generating interactive Plotly chart demo")

    # Sample velocity data
    sprints = [f"Sprint {i}" for i in range(1, 11)]
    completed = [23, 28, 25, 32, 30, 35, 33, 38, 36, 40]
    committed = [25, 30, 30, 35, 32, 35, 35, 40, 38, 42]

    config = ChartFactory.create(
        chart_type=ChartType.BAR,
        data={"x": sprints, "y": {"Completed": completed, "Committed": committed}},
        title="Team Velocity (Interactive)",
        x_label="Sprint",
        y_label="Story Points",
        backend=ChartBackend.PLOTLY,
    )

    generator = ChartGenerator(config, backend=ChartBackend.PLOTLY)
    result = generator.generate(ExportOptions(format=ExportFormat.HTML))

    output_dir = create_output_directory()
    result.save(output_dir / "interactive_velocity.html")
    logger.info(
        f"Interactive chart saved to {output_dir / 'interactive_velocity.html'}"
    )


def demo_multiple_formats():
    """Demonstrate exporting the same chart in multiple formats."""
    logger.info("Generating multi-format chart demo")

    config = ChartFactory.create(
        chart_type=ChartType.PIE,
        data={"x": ["Backend", "Frontend", "DevOps", "Testing"], "y": [40, 30, 20, 10]},
        title="Work Distribution by Type",
        x_label="Type",
        y_label="Percentage",
    )

    output_dir = create_output_directory()

    # Export as PNG
    generator = ChartGenerator(config)
    png_result = generator.generate(ExportOptions(format=ExportFormat.PNG))
    png_result.save(output_dir / "pie_chart.png")

    # Export as SVG
    svg_result = generator.generate(ExportOptions(format=ExportFormat.SVG))
    svg_result.save(output_dir / "pie_chart.svg")

    # Export as PDF
    pdf_result = generator.generate(ExportOptions(format=ExportFormat.PDF))
    pdf_result.save(output_dir / "pie_chart.pdf")

    logger.info("Multi-format charts saved (PNG, SVG, PDF)")


def demo_metrics_collection():
    """Demonstrate metrics collection during chart generation."""
    logger.info("Generating charts with metrics collection")

    metrics = get_metrics_collector()

    # Generate multiple charts to collect metrics
    for i in range(3):
        config = ChartFactory.create(
            chart_type=ChartType.LINE,
            data={"x": list(range(10)), "y": [j * (i + 1) for j in range(10)]},
            title=f"Sample Chart {i+1}",
            x_label="X",
            y_label="Y",
        )

        generator = ChartGenerator(config)
        generator.generate()

    # Display metrics
    stats = metrics.get_stats("chart_generation")
    logger.info(f"Chart generation metrics: {stats}")
    logger.info(
        f"Average generation time: {stats.get('avg_ms', 0):.2f}ms"
    )


def main():
    """Run all chart generation demos."""
    logger.info("Starting chart generation demonstrations")

    try:
        # Run demos
        demo_bar_chart()
        demo_time_series_chart()
        demo_heatmap_chart()
        demo_plotly_interactive()
        demo_multiple_formats()
        demo_metrics_collection()

        logger.info("All chart generation demos completed successfully!")
        logger.info("Check the exports/charts/ directory for generated charts")

    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
