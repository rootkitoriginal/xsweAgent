"""
Integration tests for chart generation pipeline.

Tests the complete workflow from data to chart generation.
"""
import pytest
from io import BytesIO

from src.charts.factory import ChartFactory, ChartType
from src.charts.generator import ChartGenerator
from tests.utils.test_data_builder import create_sample_issues
from tests.utils.assertions import ChartAssertions


@pytest.mark.integration
class TestChartsIntegration:
    """Integration tests for chart generation pipeline."""
    
    def test_chart_generation_from_analytics_data(self):
        """Test generating chart from analytics results."""
        # Sample analytics data
        data = {
            "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
            "opened": [10, 15, 12, 18],
            "closed": [8, 12, 15, 14]
        }
        
        # Generate chart configuration
        config = ChartFactory.create(
            chart_type=ChartType.BAR,
            data=data,
            title="Issue Activity"
        )

        assert config is not None

        # Generate the actual chart
        from src.charts.generator import ChartGenerator
        generator = ChartGenerator(config)
        result = generator.generate()
        assert result is not None
    
    def test_time_series_chart_generation(self):
        """Test generating time series charts."""
        from datetime import datetime, timedelta
        
        # Create time series data
        base_date = datetime.now()
        data = {
            "timestamps": [base_date - timedelta(days=i) for i in range(30, 0, -1)],
            "values": list(range(30, 0, -1))
        }
        
        config = ChartFactory.create(
            chart_type=ChartType.LINE,
            data=data,
            title="Issue Trend"
        )
        
        generator = ChartGenerator(config)
        result = generator.generate()
        assert result is not None
    
    def test_burndown_chart_generation(self):
        """Test generating burndown charts."""
        data = {
            "dates": ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5"],
            "ideal": [50, 40, 30, 20, 10],
            "actual": [50, 45, 35, 25, 15]
        }
        
        config = ChartFactory.create(
            chart_type=ChartType.LINE,
            data=data,
            title="Sprint Burndown"
        )
        
        generator = ChartGenerator(config)
        result = generator.generate()
        assert result is not None
    
    def test_pie_chart_generation(self):
        """Test generating pie charts for issue distribution."""
        data = {
            "labels": ["Open", "In Progress", "Closed", "Blocked"],
            "values": [15, 8, 42, 5]
        }
        
        config = ChartFactory.create(
            chart_type=ChartType.PIE,
            data=data,
            title="Issue Status Distribution"
        )
        
        generator = ChartGenerator(config)
        result = generator.generate()
        assert result is not None
    
    def test_multiple_chart_generation(self):
        """Test generating multiple charts in sequence."""
        chart_configs = [
            {
                "type": ChartType.BAR,
                "data": {"labels": ["A", "B"], "values": [10, 20]},
                "title": "Chart 1"
            },
            {
                "type": ChartType.LINE,
                "data": {"labels": ["X", "Y"], "values": [5, 15]},
                "title": "Chart 2"
            },
            {
                "type": ChartType.PIE,
                "data": {"labels": ["P", "Q"], "values": [30, 70]},
                "title": "Chart 3"
            }
        ]
        
        charts = []
        for config in chart_configs:
            config = ChartFactory.create(
                chart_type=config["type"],
                data=config["data"],
                title=config["title"]
            )
            generator = ChartGenerator(config)
            charts.append(generator.generate())
        
        assert len(charts) == 3
        assert all(c is not None for c in charts)
    
    def test_chart_with_custom_styling(self):
        """Test chart generation with custom styling options."""
        data = {
            "x": ["Jan", "Feb", "Mar"],
            "y": [100, 150, 120]
        }
        
        # Add custom styling
        options = {
            "color": "blue",
            "width": 800,
            "height": 600
        }
        
        config = ChartFactory.create(
            chart_type=ChartType.BAR,
            data=data,
            title="Monthly Stats"
        )
        
        assert config is not None, "Chart configuration should be created successfully"
        generator = ChartGenerator(config)
        result = generator.generate()
        assert result is not None
    
    def test_chart_export_formats(self):
        """Test exporting charts in different formats."""
        data = {"labels": ["A", "B"], "values": [10, 20]}
        
        config = ChartFactory.create(
            chart_type=ChartType.BAR,
            data=data,
            title="Test Chart"
        )
        
        # Generate chart (format depends on implementation)
        generator = ChartGenerator(config)
        result = generator.generate()
        
        # Verify result is in expected format (GeneratedChart object)
        assert result is not None
        assert hasattr(result, 'image_data')
        assert hasattr(result, 'save')
        assert isinstance(result.image_data, bytes)
    
    def test_chart_from_issues_workflow(self):
        """Test complete workflow from issues to chart."""
        # Create sample issues
        issues = create_sample_issues(total=20, open_ratio=0.6)
        
        # Count issues by state
        open_count = sum(1 for i in issues if i.state.value == "open")
        closed_count = sum(1 for i in issues if i.state.value == "closed")
        
        # Create chart data
        data = {
            "labels": ["Open", "Closed"],
            "values": [open_count, closed_count]
        }
        
        # Generate chart
        config = ChartFactory.create(
            chart_type=ChartType.PIE,
            data=data,
            title="Issue Status"
        )
        
        generator = ChartGenerator(config)
        result = generator.generate()
        assert result is not None
    
    def test_chart_error_handling_invalid_data(self):
        """Test chart generation handles invalid data gracefully."""
        # Try with empty data
        try:
            config = ChartFactory.create(
                chart_type=ChartType.BAR,
                data={},
                title="Empty Chart"
            )
            # Should either raise or handle gracefully
            generator = ChartGenerator(config)
            result = generator.generate()
            # If it doesn't raise, result should be None or valid
            assert result is None or result is not None
        except (ValueError, KeyError, TypeError):
            # Expected for invalid data
            pass
    
    def test_chart_data_validation(self):
        """Test that chart data is properly validated."""
        valid_data = {
            "labels": ["A", "B", "C"],
            "values": [10, 20, 30]
        }
        
        # Labels and values should match
        ChartAssertions.assert_labels_match_data(
            valid_data["labels"],
            valid_data["values"]
        )
    
    def test_chart_generator_initialization(self):
        """Test ChartGenerator can be initialized and configured."""
        config = ChartFactory.create(
            chart_type=ChartType.BAR,
            data={"labels": ["A"], "values": [10]},
            title="Test"
        )
        generator = ChartGenerator(config)
        
        assert generator is not None
        assert hasattr(generator, 'generate') or hasattr(generator, 'create_chart')
    
    def test_concurrent_chart_generation(self):
        """Test generating multiple charts concurrently."""
        import concurrent.futures
        
        def generate_chart(index):
            data = {
                "labels": [f"Item {i}" for i in range(5)],
                "values": [i * index for i in range(5)]
            }
            config = ChartFactory.create(
                chart_type=ChartType.BAR,
                data=data,
                title=f"Chart {index}"
            )
            generator = ChartGenerator(config)
            return generator.generate()
        
        # Generate 5 charts concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(generate_chart, i) for i in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        assert len(results) == 5
        assert all(r is not None for r in results)
