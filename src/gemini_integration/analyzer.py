"""
Gemini Code Analyzer
Uses the Gemini client to perform high-level code analysis tasks.
"""

import logging
import json
from typing import Optional, List
import uuid

from .client import GeminiClient
from .models import CodeSnippet, AnalysisResult, CodeReport, Suggestion, AnalysisStatus

logger = logging.getLogger(__name__)


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
            model_used=self.client.model_name
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
            logger.error(f"Code analysis failed for request {request_id}: {e}", exc_info=True)
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
                    suggested_change=s.get("suggested_change")
                ) for s in data.get("suggestions", [])
            ]

            return CodeReport(
                summary=data.get("summary"),
                complexity_score=float(data.get("complexity_score", 0.0)),
                maintainability_index=float(data.get("maintainability_index", 0.0)),
                suggestions=suggestions,
                tags=data.get("tags", [])
            )

        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.error(f"Failed to parse Gemini response: {e}\nResponse text: {response_text[:500]}...")
            return None
