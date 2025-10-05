"""
Mock Gemini API utilities for testing.

Provides configurable Gemini AI API simulator with various response scenarios.
"""
import json
from typing import Dict, Any, Optional, List
from unittest.mock import AsyncMock, MagicMock
from dataclasses import dataclass

from src.gemini_integration.models import AnalysisStatus


@dataclass
class MockGeminiConfig:
    """Configuration for MockGeminiAPI behavior."""
    
    simulate_api_error: bool = False
    simulate_rate_limit: bool = False
    simulate_timeout: bool = False
    simulate_invalid_response: bool = False
    response_quality_score: float = 85.0
    response_delay_ms: int = 0


class MockGeminiAPI:
    """Configurable Gemini API simulator for testing.
    
    Provides realistic Gemini AI API responses with various scenarios:
    - Normal operation with code analysis
    - API errors
    - Rate limiting
    - Timeouts
    - Invalid/malformed responses
    
    Example:
        >>> mock_api = MockGeminiAPI()
        >>> result = await mock_api.analyze_code("def foo(): pass")
        >>> assert result["quality_score"] > 0
    """
    
    def __init__(self, config: Optional[MockGeminiConfig] = None):
        """Initialize mock Gemini API.
        
        Args:
            config: Configuration for mock behavior
        """
        self.config = config or MockGeminiConfig()
        self._call_count = 0
        
    async def generate_content(
        self,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate content using mock Gemini API.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters
            
        Returns:
            Mock API response with analysis
            
        Raises:
            Exception: If errors are simulated
        """
        self._call_count += 1
        
        # Simulate various error conditions
        if self.config.simulate_api_error:
            raise Exception("Gemini API error: Service unavailable")
        
        if self.config.simulate_rate_limit and self._call_count > 10:
            raise Exception("Rate limit exceeded")
        
        if self.config.simulate_timeout:
            raise TimeoutError("Request timed out")
        
        if self.config.simulate_invalid_response:
            return {
                "status": AnalysisStatus.FAILED,
                "text": "This is not valid JSON and cannot be parsed",
                "usage_metadata": {}
            }
        
        # Generate realistic code analysis response
        analysis = {
            "summary": "Code analysis completed successfully",
            "complexity_score": 3.5,
            "maintainability_index": self.config.response_quality_score / 100,
            "quality_score": self.config.response_quality_score,
            "suggestions": [
                "Consider adding type hints for better code clarity",
                "Add docstrings to document function behavior",
                "Implement error handling for edge cases"
            ],
            "issues_found": [
                "Missing input validation",
                "No error handling for None values"
            ],
            "tags": ["python", "code-quality", "maintainability"]
        }
        
        return {
            "status": AnalysisStatus.COMPLETED,
            "text": json.dumps(analysis),
            "usage_metadata": {
                "prompt_token_count": len(prompt.split()),
                "candidates_token_count": 150,
                "total_token_count": len(prompt.split()) + 150
            }
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get mock model information.
        
        Returns:
            Model information dictionary
        """
        return {
            "name": "gemini-1.5-flash-mock",
            "version": "001",
            "max_tokens": 8192,
            "temperature": 0.7
        }
    
    def reset(self):
        """Reset the mock API state."""
        self._call_count = 0


def create_mock_gemini_client(
    quality_score: float = 85.0,
    simulate_errors: bool = False
) -> AsyncMock:
    """Create a fully mocked Gemini client.
    
    Args:
        quality_score: Quality score to return in responses
        simulate_errors: Whether to simulate API errors
        
    Returns:
        AsyncMock configured as a Gemini client
    """
    config = MockGeminiConfig(
        simulate_api_error=simulate_errors,
        response_quality_score=quality_score
    )
    mock_api = MockGeminiAPI(config)
    
    client = AsyncMock()
    client.generate_content = AsyncMock(side_effect=mock_api.generate_content)
    client.get_model_info = MagicMock(return_value=mock_api.get_model_info())
    
    return client


def create_mock_analysis_response(
    summary: str = "Good code quality",
    complexity_score: float = 3.5,
    quality_score: float = 85.0,
    suggestions: Optional[List[str]] = None,
    issues_found: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create a mock analysis response.
    
    Args:
        summary: Analysis summary
        complexity_score: Code complexity score
        quality_score: Overall quality score
        suggestions: List of improvement suggestions
        issues_found: List of issues found
        
    Returns:
        Mock analysis response dictionary
    """
    if suggestions is None:
        suggestions = ["Add type hints", "Improve error handling"]
    
    if issues_found is None:
        issues_found = ["Missing docstring"]
    
    return {
        "status": AnalysisStatus.COMPLETED,
        "text": json.dumps({
            "summary": summary,
            "complexity_score": complexity_score,
            "quality_score": quality_score,
            "maintainability_index": quality_score / 100,
            "suggestions": suggestions,
            "issues_found": issues_found,
            "tags": ["python", "analysis"]
        }),
        "usage_metadata": {
            "total_token_count": 250
        }
    }


class MockGeminiResponseBuilder:
    """Builder for creating complex mock Gemini responses.
    
    Example:
        >>> builder = MockGeminiResponseBuilder()
        >>> response = (builder
        ...     .with_quality_score(90)
        ...     .with_suggestion("Use async/await")
        ...     .with_issue("Memory leak detected")
        ...     .build())
    """
    
    def __init__(self):
        """Initialize the builder."""
        self._summary = "Code analysis completed"
        self._complexity = 3.5
        self._quality = 85.0
        self._suggestions: List[str] = []
        self._issues: List[str] = []
        self._tags: List[str] = ["python"]
        
    def with_summary(self, summary: str) -> "MockGeminiResponseBuilder":
        """Set the summary."""
        self._summary = summary
        return self
    
    def with_complexity_score(self, score: float) -> "MockGeminiResponseBuilder":
        """Set the complexity score."""
        self._complexity = score
        return self
    
    def with_quality_score(self, score: float) -> "MockGeminiResponseBuilder":
        """Set the quality score."""
        self._quality = score
        return self
    
    def with_suggestion(self, suggestion: str) -> "MockGeminiResponseBuilder":
        """Add a suggestion."""
        self._suggestions.append(suggestion)
        return self
    
    def with_issue(self, issue: str) -> "MockGeminiResponseBuilder":
        """Add an issue."""
        self._issues.append(issue)
        return self
    
    def with_tag(self, tag: str) -> "MockGeminiResponseBuilder":
        """Add a tag."""
        self._tags.append(tag)
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build the mock response.
        
        Returns:
            Complete mock response dictionary
        """
        return {
            "status": AnalysisStatus.COMPLETED,
            "text": json.dumps({
                "summary": self._summary,
                "complexity_score": self._complexity,
                "quality_score": self._quality,
                "maintainability_index": self._quality / 100,
                "suggestions": self._suggestions,
                "issues_found": self._issues,
                "tags": self._tags
            }),
            "usage_metadata": {
                "total_token_count": 250
            }
        }
