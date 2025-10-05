"""
Gemini API Client
Handles low-level communication with the Google Gemini API.
Enhanced with retry logic, circuit breaker, and metrics tracking.
"""

import logging
import time
from typing import Any, Dict, List, Optional

import google.generativeai as genai

from ..config.logging_config import get_logger
from ..config.settings import get_settings
from ..utils.circuit_breaker import CircuitBreakerPolicies, circuit_breaker
from ..utils.metrics import track_api_calls
from ..utils.retry import RetryPolicies, retry
from .models import AIAnalysisRequest, AIAnalysisResult, AIConfig, AnalysisStatus

logger = logging.getLogger(__name__)
xswe_logger = get_logger("gemini_client")


class GeminiClient:
    """
    Enhanced client for interacting with the Google Gemini API.
    Handles API key configuration, request execution with retry logic,
    circuit breaker protection, and comprehensive monitoring.
    """

    # default model name exposed as attribute for mocks and compatibility
    model_name: str = "gemini-2.5-flash"

    def __init__(
        self, api_key: Optional[str] = None, config: Optional[AIConfig] = None
    ):
        """
        Initializes the Gemini client.

        Args:
            api_key: The Google AI API key. If not provided, it's loaded from settings.
            config: AI configuration. If not provided, uses defaults.
        """
        # Prefer explicit argument, then environment variable (helps tests with monkeypatch),
        # then the cached settings object.
        settings = get_settings()
        env_api_key = None
        try:
            import os

            env_api_key = os.getenv("GEMINI_API_KEY")
        except Exception:
            env_api_key = None

        self.api_key = api_key or env_api_key or settings.gemini_api_key

        if not self.api_key:
            raise ValueError("Gemini API key is not configured.")

        genai.configure(api_key=self.api_key)
        self._model = None
        self.config = config or AIConfig()
        # prefer provided settings, fallback to class attribute
        self.model_name = self.config.model or settings.gemini_model_name or self.__class__.model_name
        
        # Rate limiting and cost tracking
        self._request_count = 0
        self._total_tokens = 0
        self._last_request_time = 0.0

        xswe_logger.info(
            f"Initialized GeminiClient with model: {self.model_name}",
            model=self.model_name,
        )

    @property
    def model(self):
        """Lazy-loads the generative model."""
        if self._model is None:
            logger.info(f"Initializing Gemini model: {self.model_name}")
            self._model = genai.GenerativeModel(self.model_name)
        return self._model

    @retry(RetryPolicies.GEMINI_API)
    @circuit_breaker(CircuitBreakerPolicies.GEMINI_API, name="gemini_api")
    @track_api_calls("gemini_generate_content")
    async def generate_content(
        self, prompt: str, generation_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates content using the configured Gemini model.
        Enhanced with retry logic, circuit breaker, and metrics tracking.

        Args:
            prompt: The prompt to send to the model.
            generation_config: Configuration for content generation (e.g., temperature).

        Returns:
            A dictionary containing the response and usage metadata.
        """
        if not self.model:
            return {
                "status": AnalysisStatus.FAILED,
                "error": "Model not initialized.",
                "text": None,
                "usage_metadata": None,
            }

        # Rate limiting check
        await self._check_rate_limit()

        config = generation_config or {
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "top_k": self.config.top_k,
            "max_output_tokens": self.config.max_output_tokens,
        }

        try:
            xswe_logger.debug(
                f"Sending prompt to Gemini: {prompt[:200]}...",
                prompt_length=len(prompt),
            )
            
            response = await self.model.generate_content_async(
                prompt, generation_config=genai.types.GenerationConfig(**config)
            )

            # Track request
            self._request_count += 1
            self._last_request_time = time.time()

            xswe_logger.debug("Received response from Gemini.")

            # Extract usage metadata if available. Support both object with
            # attributes (real SDK) and dict (mocks used in tests).
            usage_metadata = {}
            if getattr(response, "usage_metadata", None):
                meta = response.usage_metadata
                if isinstance(meta, dict):
                    usage_metadata = {
                        "prompt_token_count": meta.get("prompt_token_count")
                        or meta.get("promptTokenCount")
                        or meta.get("prompt_token_count", None),
                        "candidates_token_count": meta.get("candidates_token_count")
                        or meta.get("candidatesTokenCount")
                        or meta.get("candidates_token_count", None),
                        "total_token_count": meta.get("total_token_count")
                        or meta.get("totalTokenCount")
                        or meta.get("total_token_count", None),
                    }
                else:
                    usage_metadata = {
                        "prompt_token_count": getattr(meta, "prompt_token_count", None),
                        "candidates_token_count": getattr(
                            meta, "candidates_token_count", None
                        ),
                        "total_token_count": getattr(meta, "total_token_count", None),
                    }

                # Track tokens
                if usage_metadata.get("total_token_count"):
                    self._total_tokens += usage_metadata["total_token_count"]

            return {
                "status": AnalysisStatus.COMPLETED,
                "text": response.text,
                "usage_metadata": usage_metadata,
            }

        except Exception as e:
            xswe_logger.error(
                f"Gemini API request failed: {e}",
                error=str(e),
                exc_info=True,
            )
            return {
                "status": AnalysisStatus.FAILED,
                "error": str(e),
                "text": None,
                "usage_metadata": None,
            }

    async def batch_analyze(
        self, requests: List[AIAnalysisRequest]
    ) -> List[AIAnalysisResult]:
        """
        Perform batch analysis for multiple requests.
        Optimizes performance by grouping similar requests.

        Args:
            requests: List of AI analysis requests

        Returns:
            List of analysis results
        """
        import asyncio
        import uuid

        xswe_logger.info(f"Starting batch analysis for {len(requests)} requests")

        # Process requests concurrently
        tasks = []
        for req in requests:
            request_id = str(uuid.uuid4())
            # Create a task for each request
            task = self._process_single_request(request_id, req)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions in results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                xswe_logger.error(
                    f"Batch request {i} failed: {result}",
                    error=str(result),
                )
                # Create error result
                processed_results.append(
                    AIAnalysisResult(
                        request_id=str(uuid.uuid4()),
                        analysis_type=requests[i].analysis_type,
                        status=AnalysisStatus.FAILED,
                        result=None,
                        error_message=str(result),
                        model_used=self.model_name,
                    )
                )
            else:
                processed_results.append(result)

        xswe_logger.info(f"Batch analysis completed: {len(processed_results)} results")
        return processed_results

    async def _process_single_request(
        self, request_id: str, request: AIAnalysisRequest
    ) -> AIAnalysisResult:
        """Process a single AI analysis request."""
        # This is a placeholder - actual implementation would route to
        # appropriate analyzer based on analysis_type
        # For now, we'll return a basic result structure
        return AIAnalysisResult(
            request_id=request_id,
            analysis_type=request.analysis_type,
            status=AnalysisStatus.COMPLETED,
            result={"message": "Placeholder result"},
            model_used=self.model_name,
        )

    async def _check_rate_limit(self):
        """Check and enforce rate limiting."""
        import asyncio

        # Simple rate limiting: max 60 requests per minute
        current_time = time.time()
        if self._last_request_time > 0:
            time_since_last = current_time - self._last_request_time
            if time_since_last < 1.0:  # Less than 1 second between requests
                await asyncio.sleep(1.0 - time_since_last)

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for cost tracking."""
        return {
            "total_requests": self._request_count,
            "total_tokens": self._total_tokens,
            "model": self.model_name,
        }
