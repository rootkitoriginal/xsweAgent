"""
Chart Generator - Renders charts using multiple plotting libraries.
This module supports Matplotlib (static) and Plotly (interactive) backends.
"""

import io
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional, Union

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.io import to_image, write_html

from ..config.logging_config import get_logger
from ..utils import (
    ChartGenerationError,
    RetryPolicies,
    retry,
    track_api_calls,
)
from .models import (
    ChartBackend,
    ChartConfiguration,
    ChartResult,
    ChartStyling,
    ChartType,
    ExportFormat,
    ExportOptions,
    GeneratedChart,
)

logger = get_logger(__name__)


class ChartGenerator:
    """
    Generates chart images from ChartConfiguration data using multiple backends.

    Supports:
    - Matplotlib: Static high-quality charts (PNG, SVG, PDF)
    - Plotly: Interactive web-based charts (HTML, PNG, SVG)
    """

    def __init__(self, config: ChartConfiguration, backend: Optional[ChartBackend] = None):
        self.config = config
        self._styling = config.styling
        self._backend = backend or config.backend

        # Initialize matplotlib if using that backend
        if self._backend == ChartBackend.MATPLOTLIB:
            self._fig, self._ax = plt.subplots(
                figsize=self._styling.figure_size, dpi=self._styling.dpi
            )
        else:
            self._fig = None
            self._plotly_fig = None

    @retry(policy=RetryPolicies.FAST)
    @track_api_calls('chart_generation')
    def generate(self, export_options: Optional[ExportOptions] = None) -> Union[GeneratedChart, ChartResult]:
        """
        Generate the chart based on the configuration.

        Args:
            export_options: Optional export configuration (format, quality, etc.)

        Returns:
            GeneratedChart or ChartResult object with image data and metadata.
        """
        start_time = time.time()
        export_opts = export_options or ExportOptions()

        try:
            if self._backend == ChartBackend.MATPLOTLIB:
                result = self._generate_matplotlib(export_opts)
            else:
                result = self._generate_plotly(export_opts)

            # Calculate generation time
            generation_time_ms = (time.time() - start_time) * 1000

            # Return ChartResult if using new format, GeneratedChart for backward compatibility
            if isinstance(result, GeneratedChart):
                return result

            # Log performance
            logger.info(
                f"Generated {self.config.chart_type.value} chart",
                chart_type=self.config.chart_type.value,
                backend=self._backend.value,
                format=export_opts.format.value,
                generation_time_ms=generation_time_ms,
                data_points=len(self.config.x_data),
            )

            return result

        except Exception as e:
            logger.error(
                f"Failed to generate chart '{self.config.title}'",
                error=str(e),
                chart_type=self.config.chart_type.value,
                backend=self._backend.value,
            )
            if self._fig:
                plt.close(self._fig)
            raise ChartGenerationError(
                f"Chart generation failed: {str(e)}",
                details={
                    "chart_type": self.config.chart_type.value,
                    "backend": self._backend.value,
                }
            )

    def _generate_matplotlib(self, export_options: ExportOptions) -> GeneratedChart:
        """Generate chart using Matplotlib backend."""
        self._apply_styling()

        chart_method_map = {
            ChartType.BAR: self._create_bar_chart,
            ChartType.LINE: self._create_line_chart,
            ChartType.PIE: self._create_pie_chart,
            ChartType.SCATTER: self._create_scatter_chart,
            ChartType.AREA: self._create_area_chart,
            ChartType.HISTOGRAM: self._create_histogram,
            ChartType.BURNDOWN: self._create_burndown_chart,
            ChartType.VELOCITY: self._create_velocity_chart,
            ChartType.TIME_SERIES: self._create_time_series_chart,
            ChartType.HEATMAP: self._create_heatmap_chart,
        }

        chart_method = chart_method_map.get(self.config.chart_type)

        if not chart_method:
            raise ValueError(f"Unsupported chart type: {self.config.chart_type}")

        chart_method()
        self._set_labels_and_title()

        # Export to specified format
        img_buffer = io.BytesIO()
        export_format = export_options.format.value

        # Map export format to matplotlib format
        if export_format == "png":
            fmt = "png"
        elif export_format == "svg":
            fmt = "svg"
        elif export_format == "pdf":
            fmt = "pdf"
        else:
            fmt = "png"  # Default to PNG

        self._fig.savefig(
            img_buffer,
            format=fmt,
            bbox_inches="tight",
            transparent=export_options.transparent or self._styling.transparent_background,
            dpi=export_options.dpi,
        )
        img_buffer.seek(0)

        plt.close(self._fig)

        filename = f"{self.config.title.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{fmt}"

        return GeneratedChart(
            filename=filename,
            image_data=img_buffer.getvalue(),
            format=fmt,
            chart_type=self.config.chart_type,
            metadata=self._get_metadata(),
        )

    def _generate_plotly(self, export_options: ExportOptions) -> GeneratedChart:
        """Generate chart using Plotly backend."""
        chart_method_map = {
            ChartType.BAR: self._create_plotly_bar,
            ChartType.LINE: self._create_plotly_line,
            ChartType.PIE: self._create_plotly_pie,
            ChartType.SCATTER: self._create_plotly_scatter,
            ChartType.AREA: self._create_plotly_area,
            ChartType.HISTOGRAM: self._create_plotly_histogram,
            ChartType.TIME_SERIES: self._create_plotly_time_series,
            ChartType.HEATMAP: self._create_plotly_heatmap,
        }

        chart_method = chart_method_map.get(self.config.chart_type)

        if not chart_method:
            raise ValueError(f"Unsupported chart type for Plotly: {self.config.chart_type}")

        self._plotly_fig = chart_method()

        # Apply styling
        self._plotly_fig.update_layout(
            title=self.config.title,
            xaxis_title=self.config.x_label,
            yaxis_title=self.config.y_label,
            font=dict(family=self._styling.font_family, size=self._styling.font_size),
            showlegend=self._styling.show_legend,
        )

        # Export to specified format
        export_format = export_options.format.value

        if export_format == "html":
            # Export as HTML
            html_buffer = io.StringIO()
            write_html(self._plotly_fig, html_buffer, include_plotlyjs='cdn')
            html_content = html_buffer.getvalue()
            filename = f"{self.config.title.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d%H%M%S')}.html"

            return GeneratedChart(
                filename=filename,
                image_data=html_content.encode('utf-8'),
                format="html",
                chart_type=self.config.chart_type,
                metadata=self._get_metadata(),
            )
        else:
            # Export as static image (PNG, SVG)
            img_bytes = to_image(
                self._plotly_fig,
                format=export_format if export_format in ["png", "svg"] else "png",
                width=export_options.width or 1200,
                height=export_options.height or 800,
            )

            filename = f"{self.config.title.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{export_format}"

            return GeneratedChart(
                filename=filename,
                image_data=img_bytes,
                format=export_format,
                chart_type=self.config.chart_type,
                metadata=self._get_metadata(),
            )

    def export(self, format: ExportFormat) -> bytes:
        """
        Export chart to specified format.

        Args:
            format: Export format (PNG, SVG, PDF, HTML)

        Returns:
            Chart data as bytes
        """
        export_options = ExportOptions(format=format)
        result = self.generate(export_options)
        return result.image_data

    def _apply_styling(self) -> None:
        """Apply styling configurations to the chart plot."""
        plt.style.use(
            "seaborn-v0_8-whitegrid" if self._styling.grid else "seaborn-v0_8-white"
        )
        plt.rcParams["font.family"] = self._styling.font_family
        plt.rcParams["font.size"] = self._styling.font_size

        if self._styling.transparent_background:
            self._fig.patch.set_alpha(0.0)
            self._ax.patch.set_alpha(0.0)

    def _set_labels_and_title(self) -> None:
        """Set titles and labels for the chart."""
        self._ax.set_title(
            self.config.title, fontsize=self._styling.title_font_size, fontweight="bold"
        )
        if self.config.sub_title:
            self._ax.text(
                0.5,
                1.01,
                self.config.sub_title,
                ha="center",
                va="bottom",
                transform=self._ax.transAxes,
                fontsize=self._styling.font_size * 0.9,
                color="gray",
            )

        self._ax.set_xlabel(self.config.x_label, fontsize=self._styling.font_size)
        self._ax.set_ylabel(self.config.y_label, fontsize=self._styling.font_size)

        if self._styling.show_legend and self.config.chart_type != ChartType.PIE:
            self._ax.legend()

    def _get_metadata(self) -> Dict[str, Any]:
        """Generate metadata for the chart."""
        return {
            "title": self.config.title,
            "chart_type": self.config.chart_type.value,
            "timestamp": datetime.now().isoformat(),
            "x_axis": self.config.x_label,
            "y_axis": self.config.y_label,
            "data_points": len(self.config.x_data),
        }

    # --- Chart Creation Methods ---

    def _create_bar_chart(self) -> None:
        if isinstance(self.config.y_data, dict):  # Stacked or grouped bar
            df = pd.DataFrame(self.config.y_data, index=self.config.x_data)
            df.plot(
                kind="bar", stacked=True, ax=self._ax, colormap=self._styling.palette
            )
        else:
            self._ax.bar(
                self.config.x_data, self.config.y_data, label=self.config.y_label
            )

    def _create_line_chart(self) -> None:
        x_data = self.config.x_data
        # Auto-format dates if x-axis is datetime
        if all(isinstance(i, datetime) for i in x_data):
            x_data = mdates.date2num(x_data)
            self._ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            self._fig.autofmt_xdate()

        if isinstance(self.config.y_data, dict):
            for label, y_values in self.config.y_data.items():
                self._ax.plot(x_data, y_values, label=label, marker="o", linestyle="-")
        else:
            self._ax.plot(
                x_data,
                self.config.y_data,
                label=self.config.y_label,
                marker="o",
                linestyle="-",
            )

    def _create_pie_chart(self) -> None:
        self._ax.pie(
            self.config.y_data,
            labels=self.config.x_data,
            autopct="%1.1f%%",
            startangle=90,
            colors=plt.get_cmap(self._styling.palette).colors,
        )
        self._ax.axis(
            "equal"
        )  # Equal aspect ratio ensures that pie is drawn as a circle.
        self._ax.legend(
            self.config.x_data, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1)
        )

    def _create_scatter_chart(self) -> None:
        self._ax.scatter(
            self.config.x_data, self.config.y_data, label=self.config.y_label
        )

    def _create_area_chart(self) -> None:
        if isinstance(self.config.y_data, dict):
            self._ax.stackplot(
                self.config.x_data,
                self.config.y_data.values(),
                labels=self.config.y_data.keys(),
                alpha=0.7,
            )
        else:
            self._ax.fill_between(self.config.x_data, self.config.y_data, alpha=0.5)

    def _create_histogram(self) -> None:
        self._ax.hist(self.config.y_data, bins="auto", label=self.config.y_label)

    def _create_burndown_chart(self) -> None:
        self._create_line_chart()  # Base line chart
        if self.config.ideal_line:
            self._ax.plot(
                self.config.x_data,
                self.config.ideal_line,
                label="Ideal Burndown",
                linestyle="--",
                color="red",
            )
        self._ax.legend()

    def _create_velocity_chart(self) -> None:
        self._create_bar_chart()  # Base bar chart
        if self.config.average_line is not None:
            self._ax.axhline(
                y=self.config.average_line,
                color="r",
                linestyle="--",
                label=f"Average Velocity ({self.config.average_line:.2f})",
            )
        self._ax.legend()

    def _create_time_series_chart(self) -> None:
        """Create time series chart with date handling."""
        x_data = self.config.x_data

        # Auto-format dates if x-axis is datetime
        if all(isinstance(i, datetime) for i in x_data):
            x_data = mdates.date2num(x_data)
            self._ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            self._fig.autofmt_xdate()

        if isinstance(self.config.y_data, dict):
            for label, y_values in self.config.y_data.items():
                self._ax.plot(x_data, y_values, label=label, marker="o", linestyle="-")
        else:
            self._ax.plot(
                x_data,
                self.config.y_data,
                label=self.config.y_label,
                marker="o",
                linestyle="-",
            )

        self._ax.grid(True, alpha=0.3)
        if self._styling.show_legend:
            self._ax.legend()

    def _create_heatmap_chart(self) -> None:
        """Create heatmap for correlation or activity patterns."""
        # Expect y_data to be 2D array or dict of lists
        if isinstance(self.config.y_data, dict):
            # Convert dict to 2D array
            data = pd.DataFrame(self.config.y_data)
            heatmap_data = data.values
            y_labels = data.columns
        elif isinstance(self.config.y_data, list) and len(self.config.y_data) > 0:
            if isinstance(self.config.y_data[0], list):
                heatmap_data = np.array(self.config.y_data)
                y_labels = None
            else:
                # Single row heatmap
                heatmap_data = np.array([self.config.y_data])
                y_labels = None
        else:
            raise ValueError("Heatmap requires 2D data structure")

        im = self._ax.imshow(heatmap_data, cmap=self._styling.palette, aspect="auto")

        # Set ticks
        if self.config.x_data:
            self._ax.set_xticks(np.arange(len(self.config.x_data)))
            self._ax.set_xticklabels(self.config.x_data, rotation=45, ha="right")

        if y_labels is not None:
            self._ax.set_yticks(np.arange(len(y_labels)))
            self._ax.set_yticklabels(y_labels)

        # Add colorbar
        self._fig.colorbar(im, ax=self._ax)

        # Add text annotations if data is small enough
        if heatmap_data.shape[0] <= 20 and heatmap_data.shape[1] <= 20:
            for i in range(heatmap_data.shape[0]):
                for j in range(heatmap_data.shape[1]):
                    text = self._ax.text(
                        j, i, f"{heatmap_data[i, j]:.1f}",
                        ha="center", va="center", color="w", fontsize=8
                    )

    # --- Plotly Chart Creation Methods ---

    def _create_plotly_bar(self) -> go.Figure:
        """Create bar chart with Plotly."""
        if isinstance(self.config.y_data, dict):
            fig = go.Figure()
            for label, values in self.config.y_data.items():
                fig.add_trace(go.Bar(x=self.config.x_data, y=values, name=label))
        else:
            fig = go.Figure(data=[go.Bar(x=self.config.x_data, y=self.config.y_data)])
        return fig

    def _create_plotly_line(self) -> go.Figure:
        """Create line chart with Plotly."""
        if isinstance(self.config.y_data, dict):
            fig = go.Figure()
            for label, values in self.config.y_data.items():
                fig.add_trace(go.Scatter(
                    x=self.config.x_data, y=values, mode='lines+markers', name=label
                ))
        else:
            fig = go.Figure(data=[go.Scatter(
                x=self.config.x_data, y=self.config.y_data, mode='lines+markers'
            )])
        return fig

    def _create_plotly_pie(self) -> go.Figure:
        """Create pie chart with Plotly."""
        fig = go.Figure(data=[go.Pie(
            labels=self.config.x_data,
            values=self.config.y_data
        )])
        return fig

    def _create_plotly_scatter(self) -> go.Figure:
        """Create scatter plot with Plotly."""
        fig = go.Figure(data=[go.Scatter(
            x=self.config.x_data,
            y=self.config.y_data,
            mode='markers'
        )])
        return fig

    def _create_plotly_area(self) -> go.Figure:
        """Create area chart with Plotly."""
        if isinstance(self.config.y_data, dict):
            fig = go.Figure()
            for label, values in self.config.y_data.items():
                fig.add_trace(go.Scatter(
                    x=self.config.x_data, y=values, fill='tonexty', name=label
                ))
        else:
            fig = go.Figure(data=[go.Scatter(
                x=self.config.x_data,
                y=self.config.y_data,
                fill='tozeroy'
            )])
        return fig

    def _create_plotly_histogram(self) -> go.Figure:
        """Create histogram with Plotly."""
        fig = go.Figure(data=[go.Histogram(x=self.config.y_data)])
        return fig

    def _create_plotly_time_series(self) -> go.Figure:
        """Create time series chart with Plotly."""
        if isinstance(self.config.y_data, dict):
            fig = go.Figure()
            for label, values in self.config.y_data.items():
                fig.add_trace(go.Scatter(
                    x=self.config.x_data, y=values, mode='lines+markers', name=label
                ))
        else:
            fig = go.Figure(data=[go.Scatter(
                x=self.config.x_data,
                y=self.config.y_data,
                mode='lines+markers'
            )])

        # Configure time axis
        fig.update_xaxes(type='date')
        return fig

    def _create_plotly_heatmap(self) -> go.Figure:
        """Create heatmap with Plotly."""
        if isinstance(self.config.y_data, dict):
            data = pd.DataFrame(self.config.y_data)
            z_data = data.values
            y_labels = data.columns.tolist()
        elif isinstance(self.config.y_data, list):
            z_data = np.array(self.config.y_data)
            y_labels = None
        else:
            z_data = np.array([[val] for val in self.config.y_data])
            y_labels = None

        fig = go.Figure(data=go.Heatmap(
            z=z_data,
            x=self.config.x_data,
            y=y_labels,
            colorscale='Viridis'
        ))
        return fig
