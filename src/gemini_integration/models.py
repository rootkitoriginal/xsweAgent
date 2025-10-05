"""
Gemini Integration - Data Models
Defines data structures for Gemini API interactions and code analysis results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class AnalysisStatus(Enum):
    """Status of a code analysis task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisType(Enum):
    """Types of AI analysis."""

    CODE_ANALYSIS = "code_analysis"
    ISSUE_ANALYSIS = "issue_analysis"
    TREND_PREDICTION = "trend_prediction"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    PRIORITY_ANALYSIS = "priority_analysis"
    COLLABORATION_ANALYSIS = "collaboration_analysis"


class SentimentType(Enum):
    """Sentiment classification."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class PriorityLevel(Enum):
    """Priority levels for issues."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ========== Code Analysis Models ==========


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


# ========== Issue Analysis Models ==========


@dataclass
class IssueInsightResult:
    """Result of issue intelligence analysis."""

    request_id: str
    status: AnalysisStatus
    category: Optional[str] = None  # bug, feature, enhancement, etc.
    severity: Optional[str] = None  # critical, high, medium, low
    estimated_resolution_hours: Optional[float] = None
    similar_issues: List[str] = field(default_factory=list)
    root_cause: Optional[str] = None
    recommended_labels: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    error_message: Optional[str] = None
    model_used: Optional[str] = None
    usage_metadata: Optional[Dict[str, Any]] = None


# ========== Trend Analysis Models ==========


@dataclass
class TrendForecast:
    """Prediction of future trends."""

    request_id: str
    status: AnalysisStatus
    predicted_issue_count: Optional[int] = None
    predicted_resolution_time: Optional[float] = None
    quality_trend: Optional[str] = None  # improving, stable, declining
    workload_forecast: Optional[str] = None  # increasing, stable, decreasing
    confidence_score: float = 0.0
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    model_used: Optional[str] = None
    usage_metadata: Optional[Dict[str, Any]] = None


# ========== Sentiment Analysis Models ==========


@dataclass
class SentimentResult:
    """Result of sentiment analysis."""

    request_id: str
    status: AnalysisStatus
    sentiment: Optional[SentimentType] = None
    confidence_score: float = 0.0
    positive_score: float = 0.0
    negative_score: float = 0.0
    neutral_score: float = 0.0
    key_phrases: List[str] = field(default_factory=list)
    emotional_tone: Optional[str] = None
    error_message: Optional[str] = None
    model_used: Optional[str] = None
    usage_metadata: Optional[Dict[str, Any]] = None


# ========== Priority Analysis Models ==========


@dataclass
class PriorityRecommendation:
    """AI-powered priority recommendation for issues."""

    request_id: str
    status: AnalysisStatus
    priority: Optional[PriorityLevel] = None
    business_impact_score: float = 0.0
    technical_complexity_score: float = 0.0
    urgency_score: float = 0.0
    strategic_alignment_score: float = 0.0
    overall_priority_score: float = 0.0
    justification: Optional[str] = None
    recommended_assignee: Optional[str] = None
    estimated_effort_hours: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    model_used: Optional[str] = None
    usage_metadata: Optional[Dict[str, Any]] = None


# ========== Collaboration Analysis Models ==========


@dataclass
class CollaborationInsights:
    """Team collaboration and workflow insights."""

    request_id: str
    status: AnalysisStatus
    communication_score: float = 0.0
    knowledge_sharing_score: float = 0.0
    collaboration_efficiency: float = 0.0
    bottlenecks: List[str] = field(default_factory=list)
    top_collaborators: List[str] = field(default_factory=list)
    team_health_score: float = 0.0
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    model_used: Optional[str] = None
    usage_metadata: Optional[Dict[str, Any]] = None


# ========== General AI Request/Response Models ==========


@dataclass
class AIAnalysisRequest:
    """Generic AI analysis request."""

    analysis_type: AnalysisType
    data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None


@dataclass
class AIAnalysisResult:
    """Generic AI analysis result."""

    request_id: str
    analysis_type: AnalysisType
    status: AnalysisStatus
    result: Any  # Type depends on analysis_type
    error_message: Optional[str] = None
    model_used: Optional[str] = None
    usage_metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)


# ========== Configuration Models ==========


@dataclass
class AIConfig:
    """Configuration for AI operations."""

    model: str = "gemini-2.5-flash"
    temperature: float = 0.2
    top_p: float = 0.9
    top_k: int = 20
    max_output_tokens: int = 2048
    timeout: float = 30.0
    # Safety settings
    enable_safety_checks: bool = True
    max_input_length: int = 10000
    max_output_length: int = 5000


@dataclass
class PromptTemplate:
    """Reusable prompt template."""

    name: str
    template: str
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)

    def render(self, **kwargs) -> str:
        """Render template with provided values."""
        # Check required fields
        missing = [f for f in self.required_fields if f not in kwargs]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        return self.template.format(**kwargs)


@dataclass
class SafetyFilter:
    """Input/output validation and safety checks."""

    max_length: int = 10000
    blocked_patterns: List[str] = field(default_factory=list)
    allowed_languages: Optional[List[str]] = None

    def validate_input(self, text: str) -> tuple[bool, Optional[str]]:
        """Validate input text for safety."""
        if len(text) > self.max_length:
            return False, f"Input exceeds max length of {self.max_length}"

        for pattern in self.blocked_patterns:
            if pattern.lower() in text.lower():
                return False, f"Input contains blocked pattern: {pattern}"

        return True, None
