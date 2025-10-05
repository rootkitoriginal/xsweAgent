# Charts Module (`src/charts/`)

## Purpose
Generate interactive and static charts from analytics data using matplotlib and plotly.

## Key Components

### Factory Pattern
```python
class ChartFactory:
    """Factory for creating different chart types."""
    
    @classmethod
    def create(cls, chart_type: ChartType, data: ChartData, config: ChartConfig) -> bytes:
        generator = cls._generators[chart_type]
        return generator.generate(data, config)
```

### Chart Types
- **LINE/TIME_SERIES**: Trends over time, continuous data
- **BAR**: Comparing categories, discrete data
- **PIE**: Proportions, percentages
- **HEATMAP**: Correlation, density, patterns
- **BOX_PLOT**: Statistical distribution, outliers
- **SCATTER**: Correlation between two variables

## Implementation Pattern
```python
class TimeSeriesGenerator:
    def generate(self, data: ChartData, config: ChartConfig) -> bytes:
        if config.interactive:
            return self._generate_plotly(data, config)
        return self._generate_matplotlib(data, config)
    
    def _generate_matplotlib(self, data, config) -> bytes:
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        ax.plot(data.x_values, data.y_values)
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        plt.close(fig)  # Important: prevent memory leaks
        return buffer.getvalue()
```

## Best Practices

### Data Validation
```python
def validate_chart_data(data: ChartData, chart_type: ChartType) -> None:
    if not data.x_values or not data.y_values:
        raise ValueError("Empty data")
    if len(data.x_values) != len(data.y_values):
        raise ValueError("x and y must have same length")
```

### Color Management
```python
ColorPalette.DEFAULT = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
ColorPalette.COLORBLIND = ["#0173b2", "#de8f05", "#029e73", "#cc78bc", "#ca9161"]
```

### Memory Management
- Always call `plt.close(fig)` after saving
- Downsample large datasets (>1000 points)
- Use BytesIO for in-memory operations

## Testing
```python
def test_chart_generation(sample_chart_data):
    config = ChartConfig(chart_type=ChartType.BAR, title="Test")
    image_bytes = ChartFactory.create(ChartType.BAR, sample_chart_data, config)
    
    # Verify it's a valid PNG
    assert image_bytes.startswith(b'\x89PNG')
```
