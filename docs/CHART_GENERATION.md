# Chart Generation System

## Overview

The xSwE Agent chart generation system provides a comprehensive, production-ready solution for creating various types of visualizations with multiple backends and export formats.

## Features

### 🎨 Chart Types

- **BAR**: Comparative metrics and distributions
- **LINE**: Trends and continuous data
- **PIE**: Proportional distributions
- **SCATTER**: Correlation analysis
- **AREA**: Cumulative trends
- **HISTOGRAM**: Frequency distributions
- **TIME_SERIES**: Time-based trends with date handling
- **HEATMAP**: Activity patterns and correlations
- **BURNDOWN**: Sprint progress tracking
- **VELOCITY**: Team performance metrics

### 🖼️ Backends

1. **Matplotlib** (Static Charts)
   - High-quality static images
   - Print-ready outputs
   - Formats: PNG, SVG, PDF

2. **Plotly** (Interactive Charts)
   - Web-based interactive visualizations
   - Hover tooltips and zoom capabilities
   - Formats: HTML, PNG, SVG

### 📦 Export Formats

- **PNG**: Raster images with configurable DPI
- **SVG**: Scalable vector graphics
- **PDF**: Print-ready documents
- **HTML**: Interactive web charts (Plotly only)
- **JSON**: Chart configuration data

### 🛡️ Infrastructure Integration

- **Retry Logic**: Automatic retry with exponential backoff
- **Circuit Breaker**: Protection against cascading failures
- **Performance Metrics**: Execution time tracking
- **Health Checks**: Service monitoring
- **Structured Logging**: Detailed operation logs
- **Error Handling**: Comprehensive exception management

## Usage

### Basic Example

```python
from src.charts import ChartFactory, ChartGenerator, ChartType, ChartBackend

# Create chart configuration
config = ChartFactory.create(
    chart_type=ChartType.BAR,
    data={"x": ["Q1", "Q2", "Q3", "Q4"], "y": [25, 32, 28, 35]},
    title="Quarterly Performance",
    x_label="Quarter",
    y_label="Issues Closed"
)

# Generate chart
generator = ChartGenerator(config)
result = generator.generate()

# Save to file
result.save("quarterly_performance.png")
```

### Time Series Example

```python
from datetime import datetime, timedelta
from src.charts import ChartFactory, ChartType

# Generate date range
dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]
values = [10, 12, 15, 13, 18, 20, 22, ...]  # 30 values

config = ChartFactory.create(
    chart_type=ChartType.TIME_SERIES,
    data={"x": dates, "y": values},
    title="Issue Creation Trend",
    x_label="Date",
    y_label="Issues Created"
)

generator = ChartGenerator(config)
result = generator.generate()
```

### Interactive Plotly Chart

```python
from src.charts import ChartBackend, ExportFormat, ExportOptions

config = ChartFactory.create(
    chart_type=ChartType.LINE,
    data={"x": [1, 2, 3, 4, 5], "y": [10, 15, 12, 18, 20]},
    title="Interactive Chart",
    backend=ChartBackend.PLOTLY
)

generator = ChartGenerator(config, backend=ChartBackend.PLOTLY)
result = generator.generate(ExportOptions(format=ExportFormat.HTML))
result.save("interactive_chart.html")
```

### Heatmap Example

```python
# Activity heatmap (days x hours)
config = ChartFactory.create(
    chart_type=ChartType.HEATMAP,
    data={
        "x": ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
        "y": [
            [1, 0, 5, 12, 8, 2],  # Monday
            [0, 0, 6, 14, 10, 1], # Tuesday
            [1, 0, 7, 15, 9, 2],  # Wednesday
            # ... more days
        ]
    },
    title="Development Activity Heatmap"
)

generator = ChartGenerator(config)
result = generator.generate()
```

### Multiple Export Formats

```python
from src.charts import ExportFormat, ExportOptions

config = ChartFactory.create(
    chart_type=ChartType.PIE,
    data={"x": ["Backend", "Frontend", "DevOps"], "y": [50, 30, 20]},
    title="Work Distribution"
)

generator = ChartGenerator(config)

# Export as PNG
png_result = generator.generate(ExportOptions(format=ExportFormat.PNG, dpi=300))
png_result.save("chart.png")

# Export as SVG
svg_result = generator.generate(ExportOptions(format=ExportFormat.SVG))
svg_result.save("chart.svg")

# Export as PDF
pdf_result = generator.generate(ExportOptions(format=ExportFormat.PDF))
pdf_result.save("chart.pdf")
```

### With Infrastructure Features

```python
from src.utils import retry, track_execution_time, RetryPolicies
from src.config.logging_config import get_logger, with_correlation

logger = get_logger(__name__)

@retry(RetryPolicies.DEFAULT)
@track_execution_time('custom_chart_generation')
@with_correlation
def generate_custom_chart(data):
    """Generate chart with full infrastructure support."""
    config = ChartFactory.create(
        chart_type=ChartType.BAR,
        data=data,
        title="Custom Chart"
    )
    
    generator = ChartGenerator(config)
    result = generator.generate()
    
    logger.info(
        "Chart generated successfully",
        chart_type=config.chart_type.value,
        data_points=len(config.x_data)
    )
    
    return result
```

## Advanced Usage

### Custom Styling

```python
from src.charts import ChartConfiguration, ChartStyling

styling = ChartStyling(
    palette="plasma",
    grid=True,
    show_legend=True,
    font_family="Arial",
    font_size=14,
    title_font_size=18,
    figure_size=(16, 9),
    dpi=300,
    transparent_background=False
)

config = ChartConfiguration(
    title="Styled Chart",
    x_label="X Axis",
    y_label="Y Axis",
    chart_type=ChartType.LINE,
    x_data=[1, 2, 3],
    y_data=[4, 5, 6],
    styling=styling
)

generator = ChartGenerator(config)
result = generator.generate()
```

### Multi-Series Charts

```python
config = ChartFactory.create(
    chart_type=ChartType.LINE,
    data={
        "x": ["Jan", "Feb", "Mar", "Apr", "May"],
        "y": {
            "Open": [10, 15, 12, 18, 14],
            "Closed": [8, 12, 10, 16, 13],
            "In Progress": [5, 7, 6, 9, 7]
        }
    },
    title="Issue Status Over Time"
)
```

### Correlation ID Tracking

```python
from src.config.logging_config import with_correlation

@with_correlation
async def process_chart_request(chart_config):
    """All logs in this function will include a correlation_id."""
    generator = ChartGenerator(chart_config)
    result = await generator.generate()
    return result
```

## Performance Considerations

### Memory Management

The chart generator is optimized for memory efficiency:

- Charts are generated on-demand
- Image buffers are properly closed after use
- Large datasets are processed in chunks when possible

### Caching

Consider implementing caching for frequently generated charts:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_chart(chart_key: str):
    # Generate and cache chart
    pass
```

### Metrics Collection

Monitor chart generation performance:

```python
from src.utils import get_metrics_collector

metrics = get_metrics_collector()

# After generating charts
stats = metrics.get_stats("chart_generation")
print(f"Average time: {stats['avg_ms']:.2f}ms")
print(f"Charts generated: {stats['count']}")
```

## Error Handling

The system includes comprehensive error handling:

```python
from src.utils import ChartGenerationError

try:
    config = ChartFactory.create(...)
    generator = ChartGenerator(config)
    result = generator.generate()
except ChartGenerationError as e:
    logger.error(f"Chart generation failed: {e.message}")
    logger.error(f"Details: {e.details}")
```

## Health Checks

Monitor chart generation service health:

```python
from src.utils import HealthCheck

health = HealthCheck()

def check_chart_service():
    try:
        # Quick test chart generation
        config = ChartFactory.create(
            chart_type=ChartType.BAR,
            data={"x": [1], "y": [1]},
            title="Health Check"
        )
        generator = ChartGenerator(config)
        generator.generate()
        return True
    except:
        return False

health.register("chart_service", check_chart_service)
status = health.check("chart_service")
```

## Best Practices

1. **Choose the Right Backend**
   - Use Matplotlib for high-quality static images
   - Use Plotly for interactive web visualizations

2. **Optimize Export Settings**
   - Use appropriate DPI for target medium (screen: 150, print: 300)
   - Choose SVG for scalable graphics
   - Use HTML for web-based interactivity

3. **Handle Errors Gracefully**
   - Always wrap chart generation in try-except blocks
   - Use retry logic for transient failures
   - Log errors with context

4. **Monitor Performance**
   - Track execution times with metrics
   - Set up health checks for production systems
   - Use circuit breakers for external dependencies

5. **Leverage Infrastructure**
   - Use @retry decorator for resilience
   - Apply @track_execution_time for monitoring
   - Use @with_correlation for request tracing

## Integration with Analytics

The chart system integrates seamlessly with analytics:

```python
from src.analytics import AnalyticsEngine, ProductivityStrategy
from src.charts import ChartFactory

# Run analytics
engine = AnalyticsEngine(strategy=ProductivityStrategy())
results = await engine.analyze(issues)

# Create charts from results
chart_data = ChartFactory.create_chart(results)
if chart_data:
    generator = ChartGenerator(chart_data.config)
    chart = generator.generate()
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Verify matplotlib and plotly are available

2. **Memory Issues**
   - Reduce image DPI for large datasets
   - Process data in batches
   - Close figures explicitly

3. **Format Not Supported**
   - Check backend compatibility (HTML requires Plotly)
   - Verify export format is available for chosen backend

## Examples

See `examples/chart_generation_demo.py` for comprehensive demonstrations of all features.

## API Reference

### ChartFactory

- `create(chart_type, data, backend, **kwargs)`: Create chart configuration
- `create_chart(analysis_result, chart_type)`: Create from analytics result

### ChartGenerator

- `__init__(config, backend)`: Initialize generator
- `generate(export_options)`: Generate chart
- `export(format)`: Export to specific format

### Models

- `ChartType`: Enum of chart types
- `ChartBackend`: Enum of rendering backends
- `ExportFormat`: Enum of export formats
- `ChartConfiguration`: Chart configuration dataclass
- `ExportOptions`: Export settings dataclass
- `ChartResult`: Generated chart result

## Contributing

When adding new chart types:

1. Add enum value to `ChartType`
2. Implement matplotlib method `_create_<type>_chart()`
3. Implement plotly method `_create_plotly_<type>()`
4. Add tests in `tests/test_chart_enhancements.py`
5. Update this documentation

## License

Part of xSwE Agent - See main LICENSE file
