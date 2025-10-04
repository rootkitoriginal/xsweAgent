"""
Charts Module - Data models for chart generation.
Defines data structures for chart data, configuration, and styling.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from enum import Enum


class ChartType(Enum):
    """Enum for different types of charts."""
    
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"
    HISTOGRAM = "histogram"
    BURNDOWN = "burndown"  # Specialized chart
    VELOCITY = "velocity"  # Specialized chart


@dataclass
class ChartStyling:
    """Configuration for chart styling and appearance."""
    
    palette: str = "viridis"
    grid: bool = True
    show_legend: bool = True
    font_family: str = "sans-serif"
    font_size: int = 12
    title_font_size: int = 16
    figure_size: tuple = (12, 7)
    dpi: int = 150
    transparent_background: bool = False
    custom_colors: Optional[Dict[str, str]] = None


@dataclass
class ChartConfiguration:
    """
    Configuration for a single chart, including data, type, and styling.
    """
    
    title: str
    x_label: str
    y_label: str
    chart_type: ChartType
    
    # Data fields
    x_data: List[Any]
    y_data: Union[List[Any], Dict[str, List[Any]]]
    
    # Optional configuration
    sub_title: Optional[str] = None
    styling: ChartStyling = field(default_factory=ChartStyling)
    annotations: Optional[Dict[str, Any]] = None
    
    # For specialized charts
    ideal_line: Optional[List[float]] = None  # For burndown charts
    average_line: Optional[float] = None  # For velocity charts


@dataclass
class ChartData:
    """
    Represents the data and configuration needed to generate a chart.
    This model is passed to the chart generator.
    """
    
    config: ChartConfiguration
    
    # Raw data for reference
    raw_data: Optional[List[Dict[str, Any]]] = None
    
    # Metadata
    generated_at: Optional[str] = None
    source_repository: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chart data to a dictionary for serialization."""
        return {
            "title": self.config.title,
            "chart_type": self.config.chart_type.value,
            "x_label": self.config.x_label,
            "y_label": self.config.y_label,
            "data_points": len(self.config.x_data),
            "source": self.source_repository
        }


@dataclass
class GeneratedChart:
    """
    Represents a generated chart, including the image data and metadata.
    """
    
    filename: str
    image_data: bytes
    format: str  # e.g., "png", "svg"
    chart_type: ChartType
    metadata: Dict[str, Any]
    
    def save(self, path: str) -> None:
        """Save the chart image to a file."""
        with open(path, "wb") as f:
            f.write(self.image_data)