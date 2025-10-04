"""
Chart Generator - Renders charts using a plotting library.
This module uses Matplotlib to create and save chart images.
"""

import io
import logging
from datetime import datetime
from typing import Dict, Any

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

from .models import ChartConfiguration, GeneratedChart, ChartStyling, ChartType


logger = logging.getLogger(__name__)


class ChartGenerator:
    """
    Generates chart images from ChartConfiguration data using Matplotlib.
    """

    def __init__(self, config: ChartConfiguration):
        self.config = config
        self._styling = config.styling
        self._fig, self._ax = plt.subplots(
            figsize=self._styling.figure_size, dpi=self._styling.dpi
        )

    def generate(self) -> GeneratedChart:
        """
        Generate the chart based on the configuration.

        Returns:
            GeneratedChart object with image data and metadata.
        """
        try:
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
            }

            chart_method = chart_method_map.get(self.config.chart_type)

            if not chart_method:
                raise ValueError(f"Unsupported chart type: {self.config.chart_type}")

            chart_method()

            self._set_labels_and_title()

            # Save chart to a byte buffer
            img_buffer = io.BytesIO()
            self._fig.savefig(
                img_buffer,
                format="png",
                bbox_inches="tight",
                transparent=self._styling.transparent_background,
            )
            img_buffer.seek(0)

            plt.close(self._fig)

            filename = f"{self.config.title.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"

            return GeneratedChart(
                filename=filename,
                image_data=img_buffer.getvalue(),
                format="png",
                chart_type=self.config.chart_type,
                metadata=self._get_metadata(),
            )

        except Exception as e:
            logger.error(f"Failed to generate chart '{self.config.title}': {e}")
            plt.close(self._fig)
            raise

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
