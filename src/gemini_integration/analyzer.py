"""
Gemini AI Analyzer
Enhanced analyzer with multiple analysis capabilities including code analysis,
issue intelligence, trend prediction, sentiment analysis, and more.
"""

import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from ..config.logging_config import get_logger
from ..github_monitor.models import Issue
from ..utils.metrics import track_api_calls
from ..utils.retry import RetryPolicies, retry
from .client import GeminiClient
from .models import (
    AnalysisResult,
    AnalysisStatus,
    CodeReport,
    CodeSnippet,
    CollaborationInsights,
    IssueInsightResult,
    PriorityLevel,
    PriorityRecommendation,
    SentimentResult,
    SentimentType,
    Suggestion,
    TrendForecast,
)

logger = logging.getLogger(__name__)
xswe_logger = get_logger("gemini_analyzer")


class CodeAnalyzer:
    """
    Analyzes code snippets using the Gemini AI model.
    Constructs prompts, parses responses, and formats results.
    """

    def __init__(self, client: Optional[GeminiClient] = None):
        """
        Initializes the CodeAnalyzer.

        Args:
            client: An instance of GeminiClient. If not provided, a new one is created.
        """
        self.client = client or GeminiClient()

    async def analyze_code(self, snippet: CodeSnippet) -> AnalysisResult:
        """
        Performs a comprehensive analysis of a given code snippet.

        Args:
            snippet: The code snippet to analyze.

        Returns:
            An AnalysisResult object with the detailed report.
        """
        request_id = str(uuid.uuid4())

        prompt = self._build_analysis_prompt(snippet)

        result = AnalysisResult(
            request_id=request_id,
            status=AnalysisStatus.RUNNING,
            model_used=self.client.model_name,
        )

        try:
            api_response = await self.client.generate_content(prompt)

            result.usage_metadata = api_response.get("usage_metadata")

            if api_response["status"] == AnalysisStatus.FAILED:
                result.status = AnalysisStatus.FAILED
                result.error_message = api_response.get("error", "Unknown API error")
                return result

            report = self._parse_response(api_response["text"])

            if report:
                result.status = AnalysisStatus.COMPLETED
                result.report = report
            else:
                result.status = AnalysisStatus.FAILED
                result.error_message = "Failed to parse model response."

        except Exception as e:
            logger.error(
                f"Code analysis failed for request {request_id}: {e}", exc_info=True
            )
            result.status = AnalysisStatus.FAILED
            result.error_message = str(e)

        return result

    def _build_analysis_prompt(self, snippet: CodeSnippet) -> str:
        """Constructs the detailed prompt for the Gemini model."""

        prompt = f"""
        Analyze the following {snippet.language} code snippet.
        Filename: {snippet.filename or 'N/A'}

        Context:
        {snippet.context or 'No additional context provided.'}

        Code to analyze:
        ```
        {snippet.content}
        ```

        Provide a detailed analysis in JSON format. The JSON object must have the following structure:
        {{
          "summary": "A brief, one-paragraph summary of the code's purpose and quality.",
          "complexity_score": "A float between 0.0 (simple) and 1.0 (very complex).",
          "maintainability_index": "A float between 0.0 (hard to maintain) and 1.0 (easy to maintain).",
          "suggestions": [
            {{
              "line_start": <int>,
              "line_end": <int>,
              "description": "A clear explanation of the issue and why it matters.",
              "category": "<'Performance'|'Security'|'Style'|'Best Practice'|'Error Prone'>",
              "severity": "<'High'|'Medium'|'Low'>",
              "suggested_change": "Optional: A code block with the suggested fix."
            }}
          ],
          "tags": ["An", "array", "of", "relevant", "tags", "like", "api-call", "data-processing"]
        }}

        Ensure the output is a single, valid JSON object and nothing else.
        """
        return prompt

    def _parse_response(self, response_text: str) -> Optional[CodeReport]:
        """Parses the JSON response from the model into a CodeReport."""
        try:
            # Clean up the response to extract only the JSON part
            json_str = response_text.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]

            data = json.loads(json_str)

            suggestions = [
                Suggestion(
                    line_start=s.get("line_start"),
                    line_end=s.get("line_end"),
                    description=s.get("description"),
                    category=s.get("category"),
                    severity=s.get("severity"),
                    suggested_change=s.get("suggested_change"),
                )
                for s in data.get("suggestions", [])
            ]

            return CodeReport(
                summary=data.get("summary"),
                complexity_score=float(data.get("complexity_score", 0.0)),
                maintainability_index=float(data.get("maintainability_index", 0.0)),
                suggestions=suggestions,
                tags=data.get("tags", []),
            )

        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.error(
                f"Failed to parse Gemini response: {e}\nResponse text: {response_text[:500]}..."
            )
            return None

    # ========== Issue Intelligence ==========

    @retry(policy=RetryPolicies.GEMINI_API)
    @track_api_calls("gemini_issue_analysis")
    async def issue_analysis(self, issue: Issue) -> IssueInsightResult:
        """
        Analyze GitHub issue to provide intelligent insights.

        Args:
            issue: GitHub issue to analyze

        Returns:
            IssueInsightResult with categorization, severity, and insights
        """
        request_id = str(uuid.uuid4())
        
        prompt = self._build_issue_analysis_prompt(issue)
        
        result = IssueInsightResult(
            request_id=request_id,
            status=AnalysisStatus.RUNNING,
            model_used=self.client.model_name,
        )

        try:
            api_response = await self.client.generate_content(prompt)
            result.usage_metadata = api_response.get("usage_metadata")

            if api_response["status"] == AnalysisStatus.FAILED:
                result.status = AnalysisStatus.FAILED
                result.error_message = api_response.get("error", "Unknown API error")
                return result

            insights = self._parse_issue_insights(api_response["text"])
            if insights:
                result.status = AnalysisStatus.COMPLETED
                result.category = insights.get("category")
                result.severity = insights.get("severity")
                result.estimated_resolution_hours = insights.get("estimated_hours")
                result.root_cause = insights.get("root_cause")
                result.recommended_labels = insights.get("labels", [])
                result.confidence_score = insights.get("confidence", 0.0)
            else:
                result.status = AnalysisStatus.FAILED
                result.error_message = "Failed to parse issue insights"

        except Exception as e:
            xswe_logger.error(f"Issue analysis failed: {e}", exc_info=True)
            result.status = AnalysisStatus.FAILED
            result.error_message = str(e)

        return result

    def _build_issue_analysis_prompt(self, issue: Issue) -> str:
        """Build prompt for issue analysis."""
        return f"""
        Analyze the following GitHub issue and provide intelligent insights.
        
        Issue Title: {issue.title}
        Issue Body: {issue.body or 'No description provided'}
        Labels: {', '.join([label.name for label in issue.labels]) if issue.labels else 'None'}
        State: {issue.state}
        
        Provide analysis in JSON format:
        {{
          "category": "<bug|feature|enhancement|documentation|question>",
          "severity": "<critical|high|medium|low>",
          "estimated_hours": <float>,
          "root_cause": "Brief description of likely root cause",
          "labels": ["recommended", "labels"],
          "confidence": <float 0.0-1.0>
        }}
        
        Ensure output is valid JSON only.
        """

    def _parse_issue_insights(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse issue analysis response."""
        try:
            json_str = response_text.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            return json.loads(json_str.strip())
        except (json.JSONDecodeError, TypeError) as e:
            xswe_logger.error(f"Failed to parse issue insights: {e}")
            return None

    # ========== Trend Prediction ==========

    @retry(policy=RetryPolicies.GEMINI_API)
    @track_api_calls("gemini_trend_prediction")
    async def trend_prediction(
        self, historical_data: List[Dict[str, Any]]
    ) -> TrendForecast:
        """
        Predict future trends based on historical data.

        Args:
            historical_data: List of historical metrics and data points

        Returns:
            TrendForecast with predictions and insights
        """
        request_id = str(uuid.uuid4())
        
        prompt = self._build_trend_prediction_prompt(historical_data)
        
        result = TrendForecast(
            request_id=request_id,
            status=AnalysisStatus.RUNNING,
            model_used=self.client.model_name,
        )

        try:
            api_response = await self.client.generate_content(prompt)
            result.usage_metadata = api_response.get("usage_metadata")

            if api_response["status"] == AnalysisStatus.FAILED:
                result.status = AnalysisStatus.FAILED
                result.error_message = api_response.get("error")
                return result

            forecast = self._parse_trend_forecast(api_response["text"])
            if forecast:
                result.status = AnalysisStatus.COMPLETED
                result.predicted_issue_count = forecast.get("predicted_issues")
                result.predicted_resolution_time = forecast.get("predicted_resolution_time")
                result.quality_trend = forecast.get("quality_trend")
                result.workload_forecast = forecast.get("workload_forecast")
                result.confidence_score = forecast.get("confidence", 0.0)
                result.insights = forecast.get("insights", [])
                result.recommendations = forecast.get("recommendations", [])
            else:
                result.status = AnalysisStatus.FAILED
                result.error_message = "Failed to parse trend forecast"

        except Exception as e:
            xswe_logger.error(f"Trend prediction failed: {e}", exc_info=True)
            result.status = AnalysisStatus.FAILED
            result.error_message = str(e)

        return result

    def _build_trend_prediction_prompt(
        self, historical_data: List[Dict[str, Any]]
    ) -> str:
        """Build prompt for trend prediction."""
        data_summary = json.dumps(historical_data[-10:], indent=2)  # Last 10 data points
        return f"""
        Analyze the following historical data and predict future trends.
        
        Historical Data:
        {data_summary}
        
        Provide predictions in JSON format:
        {{
          "predicted_issues": <int>,
          "predicted_resolution_time": <float hours>,
          "quality_trend": "<improving|stable|declining>",
          "workload_forecast": "<increasing|stable|decreasing>",
          "confidence": <float 0.0-1.0>,
          "insights": ["Key insight 1", "Key insight 2"],
          "recommendations": ["Recommendation 1", "Recommendation 2"]
        }}
        
        Ensure output is valid JSON only.
        """

    def _parse_trend_forecast(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse trend forecast response."""
        try:
            json_str = response_text.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            return json.loads(json_str.strip())
        except (json.JSONDecodeError, TypeError) as e:
            xswe_logger.error(f"Failed to parse trend forecast: {e}")
            return None

    # ========== Sentiment Analysis ==========

    @retry(policy=RetryPolicies.GEMINI_API)
    @track_api_calls("gemini_sentiment_analysis")
    async def sentiment_analysis(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of text (comments, descriptions, etc.).

        Args:
            text: Text to analyze

        Returns:
            SentimentResult with sentiment classification and scores
        """
        request_id = str(uuid.uuid4())
        
        prompt = self._build_sentiment_prompt(text)
        
        result = SentimentResult(
            request_id=request_id,
            status=AnalysisStatus.RUNNING,
            model_used=self.client.model_name,
        )

        try:
            api_response = await self.client.generate_content(prompt)
            result.usage_metadata = api_response.get("usage_metadata")

            if api_response["status"] == AnalysisStatus.FAILED:
                result.status = AnalysisStatus.FAILED
                result.error_message = api_response.get("error")
                return result

            sentiment = self._parse_sentiment(api_response["text"])
            if sentiment:
                result.status = AnalysisStatus.COMPLETED
                sentiment_str = sentiment.get("sentiment", "neutral")
                result.sentiment = SentimentType(sentiment_str.lower())
                result.confidence_score = sentiment.get("confidence", 0.0)
                result.positive_score = sentiment.get("positive_score", 0.0)
                result.negative_score = sentiment.get("negative_score", 0.0)
                result.neutral_score = sentiment.get("neutral_score", 0.0)
                result.key_phrases = sentiment.get("key_phrases", [])
                result.emotional_tone = sentiment.get("emotional_tone")
            else:
                result.status = AnalysisStatus.FAILED
                result.error_message = "Failed to parse sentiment"

        except Exception as e:
            xswe_logger.error(f"Sentiment analysis failed: {e}", exc_info=True)
            result.status = AnalysisStatus.FAILED
            result.error_message = str(e)

        return result

    def _build_sentiment_prompt(self, text: str) -> str:
        """Build prompt for sentiment analysis."""
        return f"""
        Analyze the sentiment of the following text.
        
        Text: {text[:1000]}
        
        Provide sentiment analysis in JSON format:
        {{
          "sentiment": "<positive|neutral|negative|mixed>",
          "confidence": <float 0.0-1.0>,
          "positive_score": <float 0.0-1.0>,
          "negative_score": <float 0.0-1.0>,
          "neutral_score": <float 0.0-1.0>,
          "key_phrases": ["phrase1", "phrase2"],
          "emotional_tone": "Brief description of emotional tone"
        }}
        
        Ensure output is valid JSON only.
        """

    def _parse_sentiment(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse sentiment analysis response."""
        try:
            json_str = response_text.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            return json.loads(json_str.strip())
        except (json.JSONDecodeError, TypeError) as e:
            xswe_logger.error(f"Failed to parse sentiment: {e}")
            return None

    # ========== Priority Analysis ==========

    @retry(policy=RetryPolicies.GEMINI_API)
    @track_api_calls("gemini_priority_analysis")
    async def priority_analysis(self, issue: Issue) -> PriorityRecommendation:
        """
        Provide AI-powered priority recommendation for an issue.

        Args:
            issue: GitHub issue to analyze

        Returns:
            PriorityRecommendation with priority level and justification
        """
        request_id = str(uuid.uuid4())
        
        prompt = self._build_priority_prompt(issue)
        
        result = PriorityRecommendation(
            request_id=request_id,
            status=AnalysisStatus.RUNNING,
            model_used=self.client.model_name,
        )

        try:
            api_response = await self.client.generate_content(prompt)
            result.usage_metadata = api_response.get("usage_metadata")

            if api_response["status"] == AnalysisStatus.FAILED:
                result.status = AnalysisStatus.FAILED
                result.error_message = api_response.get("error")
                return result

            priority = self._parse_priority(api_response["text"])
            if priority:
                result.status = AnalysisStatus.COMPLETED
                priority_str = priority.get("priority", "medium")
                result.priority = PriorityLevel(priority_str.lower())
                result.business_impact_score = priority.get("business_impact", 0.0)
                result.technical_complexity_score = priority.get("technical_complexity", 0.0)
                result.urgency_score = priority.get("urgency", 0.0)
                result.strategic_alignment_score = priority.get("strategic_alignment", 0.0)
                result.overall_priority_score = priority.get("overall_score", 0.0)
                result.justification = priority.get("justification")
                result.estimated_effort_hours = priority.get("estimated_effort")
                result.dependencies = priority.get("dependencies", [])
            else:
                result.status = AnalysisStatus.FAILED
                result.error_message = "Failed to parse priority"

        except Exception as e:
            xswe_logger.error(f"Priority analysis failed: {e}", exc_info=True)
            result.status = AnalysisStatus.FAILED
            result.error_message = str(e)

        return result

    def _build_priority_prompt(self, issue: Issue) -> str:
        """Build prompt for priority analysis."""
        return f"""
        Analyze this GitHub issue and recommend a priority level.
        
        Title: {issue.title}
        Body: {issue.body or 'No description'}
        Labels: {', '.join([label.name for label in issue.labels]) if issue.labels else 'None'}
        
        Provide priority analysis in JSON format:
        {{
          "priority": "<critical|high|medium|low>",
          "business_impact": <float 0.0-1.0>,
          "technical_complexity": <float 0.0-1.0>,
          "urgency": <float 0.0-1.0>,
          "strategic_alignment": <float 0.0-1.0>,
          "overall_score": <float 0.0-1.0>,
          "justification": "Brief explanation of priority",
          "estimated_effort": <float hours>,
          "dependencies": ["dependency1", "dependency2"]
        }}
        
        Ensure output is valid JSON only.
        """

    def _parse_priority(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse priority analysis response."""
        try:
            json_str = response_text.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            return json.loads(json_str.strip())
        except (json.JSONDecodeError, TypeError) as e:
            xswe_logger.error(f"Failed to parse priority: {e}")
            return None

    # ========== Collaboration Analysis ==========

    @retry(policy=RetryPolicies.GEMINI_API)
    @track_api_calls("gemini_collaboration_analysis")
    async def collaboration_analysis(
        self, team_data: Dict[str, Any]
    ) -> CollaborationInsights:
        """
        Analyze team collaboration patterns and provide insights.

        Args:
            team_data: Dictionary with team collaboration data

        Returns:
            CollaborationInsights with team health and recommendations
        """
        request_id = str(uuid.uuid4())
        
        prompt = self._build_collaboration_prompt(team_data)
        
        result = CollaborationInsights(
            request_id=request_id,
            status=AnalysisStatus.RUNNING,
            model_used=self.client.model_name,
        )

        try:
            api_response = await self.client.generate_content(prompt)
            result.usage_metadata = api_response.get("usage_metadata")

            if api_response["status"] == AnalysisStatus.FAILED:
                result.status = AnalysisStatus.FAILED
                result.error_message = api_response.get("error")
                return result

            insights = self._parse_collaboration(api_response["text"])
            if insights:
                result.status = AnalysisStatus.COMPLETED
                result.communication_score = insights.get("communication_score", 0.0)
                result.knowledge_sharing_score = insights.get("knowledge_sharing", 0.0)
                result.collaboration_efficiency = insights.get("efficiency", 0.0)
                result.bottlenecks = insights.get("bottlenecks", [])
                result.top_collaborators = insights.get("top_collaborators", [])
                result.team_health_score = insights.get("team_health", 0.0)
                result.insights = insights.get("insights", [])
                result.recommendations = insights.get("recommendations", [])
            else:
                result.status = AnalysisStatus.FAILED
                result.error_message = "Failed to parse collaboration insights"

        except Exception as e:
            xswe_logger.error(f"Collaboration analysis failed: {e}", exc_info=True)
            result.status = AnalysisStatus.FAILED
            result.error_message = str(e)

        return result

    def _build_collaboration_prompt(self, team_data: Dict[str, Any]) -> str:
        """Build prompt for collaboration analysis."""
        data_summary = json.dumps(team_data, indent=2)
        return f"""
        Analyze team collaboration patterns based on this data.
        
        Team Data:
        {data_summary}
        
        Provide collaboration insights in JSON format:
        {{
          "communication_score": <float 0.0-1.0>,
          "knowledge_sharing": <float 0.0-1.0>,
          "efficiency": <float 0.0-1.0>,
          "bottlenecks": ["bottleneck1", "bottleneck2"],
          "top_collaborators": ["user1", "user2"],
          "team_health": <float 0.0-1.0>,
          "insights": ["insight1", "insight2"],
          "recommendations": ["recommendation1", "recommendation2"]
        }}
        
        Ensure output is valid JSON only.
        """

    def _parse_collaboration(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse collaboration analysis response."""
        try:
            json_str = response_text.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            return json.loads(json_str.strip())
        except (json.JSONDecodeError, TypeError) as e:
            xswe_logger.error(f"Failed to parse collaboration insights: {e}")
            return None


# GeminiAnalyzer extends CodeAnalyzer for backward compatibility
# and provides all enhanced AI analysis capabilities
class GeminiAnalyzer(CodeAnalyzer):
    """
    Enhanced AI-powered analyzer with multiple analysis capabilities.
    
    Provides all CodeAnalyzer functionality plus:
    - Issue intelligence and categorization
    - Trend prediction and forecasting
    - Sentiment analysis
    - Priority recommendations
    - Collaboration insights
    """

    def __init__(self, client: Optional[GeminiClient] = None):
        """
        Initialize the enhanced analyzer.

        Args:
            client: GeminiClient instance. If not provided, creates a new one.
        """
        super().__init__(client)
        xswe_logger.info("Initialized GeminiAnalyzer with enhanced capabilities")
