"""
Custom assertions for testing metrics and analytics.

Provides specialized assertion methods for common test patterns.
"""
from typing import Dict, Any, List, Optional
import pytest


class MetricsAssertions:
    """Custom assertions for metrics validation."""
    
    @staticmethod
    def assert_metrics_structure(
        metrics: Dict[str, Any],
        required_keys: Optional[List[str]] = None
    ):
        """Assert that metrics have expected structure.
        
        Args:
            metrics: Metrics dictionary to validate
            required_keys: List of required keys (uses defaults if None)
        """
        if required_keys is None:
            required_keys = ["total_issues", "open_issues", "closed_issues"]
        
        assert isinstance(metrics, dict), "Metrics must be a dictionary"
        
        for key in required_keys:
            assert key in metrics, f"Missing required metric: {key}"
        
        # Validate numeric types
        for key in ["total_issues", "open_issues", "closed_issues"]:
            if key in metrics:
                assert isinstance(metrics[key], (int, float)), \
                    f"{key} must be numeric, got {type(metrics[key])}"
    
    @staticmethod
    def assert_positive_metric(metrics: Dict[str, Any], key: str):
        """Assert that a metric exists and is positive.
        
        Args:
            metrics: Metrics dictionary
            key: Key to check
        """
        assert key in metrics, f"Metric {key} not found"
        value = metrics[key]
        assert isinstance(value, (int, float)), \
            f"{key} must be numeric, got {type(value)}"
        assert value >= 0, f"{key} must be non-negative, got {value}"
    
    @staticmethod
    def assert_ratio(
        metrics: Dict[str, Any],
        numerator_key: str,
        denominator_key: str,
        expected_ratio: float,
        tolerance: float = 0.1
    ):
        """Assert that a ratio between two metrics is within expected range.
        
        Args:
            metrics: Metrics dictionary
            numerator_key: Key for numerator
            denominator_key: Key for denominator
            expected_ratio: Expected ratio value
            tolerance: Acceptable deviation from expected ratio
        """
        assert numerator_key in metrics, f"Metric {numerator_key} not found"
        assert denominator_key in metrics, f"Metric {denominator_key} not found"
        
        numerator = metrics[numerator_key]
        denominator = metrics[denominator_key]
        
        assert denominator > 0, f"Denominator {denominator_key} must be positive"
        
        actual_ratio = numerator / denominator
        lower_bound = expected_ratio - tolerance
        upper_bound = expected_ratio + tolerance
        
        assert lower_bound <= actual_ratio <= upper_bound, \
            f"Ratio {numerator_key}/{denominator_key} = {actual_ratio:.2f} " \
            f"not in expected range [{lower_bound:.2f}, {upper_bound:.2f}]"
    
    @staticmethod
    def assert_percentage(metrics: Dict[str, Any], key: str):
        """Assert that a metric is a valid percentage (0-100).
        
        Args:
            metrics: Metrics dictionary
            key: Key to check
        """
        assert key in metrics, f"Metric {key} not found"
        value = metrics[key]
        assert isinstance(value, (int, float)), \
            f"{key} must be numeric, got {type(value)}"
        assert 0 <= value <= 100, \
            f"{key} must be between 0 and 100, got {value}"


class AnalyticsAssertions:
    """Custom assertions for analytics validation."""
    
    @staticmethod
    def assert_analysis_result_structure(result: Dict[str, Any]):
        """Assert that an analysis result has expected structure.
        
        Args:
            result: Analysis result dictionary
        """
        assert isinstance(result, dict), "Result must be a dictionary"
        assert "analysis_type" in result or len(result) > 0, \
            "Result must contain analysis_type or analysis data"
    
    @staticmethod
    def assert_time_series_data(
        data: List[Any],
        min_points: int = 2,
        check_chronological: bool = True
    ):
        """Assert that time series data is valid.
        
        Args:
            data: List of time series data points
            min_points: Minimum number of required data points
            check_chronological: Whether to check chronological order
        """
        assert isinstance(data, list), "Time series data must be a list"
        assert len(data) >= min_points, \
            f"Time series must have at least {min_points} points, got {len(data)}"
        
        if check_chronological and len(data) > 1:
            # Check if data has timestamps
            if hasattr(data[0], 'timestamp'):
                for i in range(len(data) - 1):
                    assert data[i].timestamp <= data[i + 1].timestamp, \
                        f"Time series not in chronological order at index {i}"


class ChartAssertions:
    """Custom assertions for chart validation."""
    
    @staticmethod
    def assert_chart_data_structure(
        chart_data: Dict[str, Any],
        required_keys: Optional[List[str]] = None
    ):
        """Assert that chart data has expected structure.
        
        Args:
            chart_data: Chart data dictionary
            required_keys: List of required keys
        """
        if required_keys is None:
            required_keys = ["labels", "data"]
        
        assert isinstance(chart_data, dict), "Chart data must be a dictionary"
        
        for key in required_keys:
            assert key in chart_data, f"Missing required key: {key}"
    
    @staticmethod
    def assert_labels_match_data(
        labels: List[Any],
        data: List[Any]
    ):
        """Assert that labels and data have matching lengths.
        
        Args:
            labels: List of labels
            data: List of data points
        """
        assert isinstance(labels, list), "Labels must be a list"
        assert isinstance(data, list), "Data must be a list"
        assert len(labels) == len(data), \
            f"Labels ({len(labels)}) and data ({len(data)}) lengths must match"


class PerformanceAssertions:
    """Custom assertions for performance validation."""
    
    @staticmethod
    def assert_execution_time(
        duration_seconds: float,
        max_seconds: float,
        operation_name: str = "Operation"
    ):
        """Assert that execution time is within acceptable range.
        
        Args:
            duration_seconds: Actual execution time
            max_seconds: Maximum acceptable time
            operation_name: Name of the operation for error messages
        """
        assert isinstance(duration_seconds, (int, float)), \
            "Duration must be numeric"
        assert duration_seconds >= 0, "Duration must be non-negative"
        assert duration_seconds <= max_seconds, \
            f"{operation_name} took {duration_seconds:.2f}s, " \
            f"expected < {max_seconds:.2f}s"
    
    @staticmethod
    def assert_memory_usage(
        memory_mb: float,
        max_mb: float,
        operation_name: str = "Operation"
    ):
        """Assert that memory usage is within acceptable range.
        
        Args:
            memory_mb: Actual memory usage in MB
            max_mb: Maximum acceptable memory in MB
            operation_name: Name of the operation for error messages
        """
        assert isinstance(memory_mb, (int, float)), \
            "Memory usage must be numeric"
        assert memory_mb >= 0, "Memory usage must be non-negative"
        assert memory_mb <= max_mb, \
            f"{operation_name} used {memory_mb:.2f}MB, " \
            f"expected < {max_mb:.2f}MB"


class APIResponseAssertions:
    """Custom assertions for API response validation."""
    
    @staticmethod
    def assert_success_response(
        response: Dict[str, Any],
        expected_status: int = 200
    ):
        """Assert that API response indicates success.
        
        Args:
            response: API response dictionary
            expected_status: Expected HTTP status code
        """
        assert isinstance(response, dict), "Response must be a dictionary"
        
        if "status_code" in response:
            assert response["status_code"] == expected_status, \
                f"Expected status {expected_status}, got {response['status_code']}"
        
        if "status" in response:
            assert response["status"] in ["ok", "success"], \
                f"Unexpected status: {response['status']}"
    
    @staticmethod
    def assert_error_response(
        response: Dict[str, Any],
        expected_error_message: Optional[str] = None
    ):
        """Assert that API response indicates an error.
        
        Args:
            response: API response dictionary
            expected_error_message: Expected error message (substring match)
        """
        assert isinstance(response, dict), "Response must be a dictionary"
        
        # Check for error indicators
        has_error = (
            "error" in response or
            "error_message" in response or
            (response.get("status") == "error")
        )
        
        assert has_error, "Response does not indicate an error"
        
        if expected_error_message:
            error_msg = (
                response.get("error") or
                response.get("error_message") or
                response.get("message", "")
            )
            assert expected_error_message in str(error_msg), \
                f"Expected error message containing '{expected_error_message}', " \
                f"got '{error_msg}'"


# Convenience functions for direct use in tests
def assert_metrics_valid(metrics: Dict[str, Any]):
    """Quick assertion for valid metrics structure."""
    MetricsAssertions.assert_metrics_structure(metrics)


def assert_positive(metrics: Dict[str, Any], key: str):
    """Quick assertion for positive metric value."""
    MetricsAssertions.assert_positive_metric(metrics, key)


def assert_percentage(metrics: Dict[str, Any], key: str):
    """Quick assertion for percentage value."""
    MetricsAssertions.assert_percentage(metrics, key)


def assert_execution_under(duration: float, max_seconds: float):
    """Quick assertion for execution time."""
    PerformanceAssertions.assert_execution_time(duration, max_seconds)
