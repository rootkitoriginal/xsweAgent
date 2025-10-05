"""
Gemini Integration - Data Models
Defines data structures for Gemini API interactions and code analysis results.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AnalysisStatus(Enum):
    """Status of a code analysis task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CodeSnippet:
    """Represents a piece of code to be analyzed."""

    content: str
    language: str
    filename: Optional[str] = None
    context: Optional[str] = None  # e.g., related issue description


@dataclass
class Suggestion:
    """A single suggestion for code improvement."""

    line_start: int
    line_end: int
    description: str
    category: str  # e.g., "Performance", "Security", "Style"
    severity: str  # e.g., "High", "Medium", "Low"
    suggested_change: Optional[str] = None


@dataclass
class CodeReport:
    """A comprehensive report generated from code analysis."""

    summary: str
    complexity_score: float  # e.g., 0.0 to 1.0
    maintainability_index: float
    suggestions: List[Suggestion]
    tags: List[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """The result of a Gemini code analysis request."""

    request_id: str
    status: AnalysisStatus
    report: Optional[CodeReport] = None
    error_message: Optional[str] = None
    model_used: Optional[str] = None
    usage_metadata: Optional[Dict[str, Any]] = None  # Tokens, cost, etc.

    def is_successful(self) -> bool:
        return self.status == AnalysisStatus.COMPLETED and self.report is not None
