"""
Gemini API Client
Handles low-level communication with the Google Gemini API.
"""

import logging
import google.generativeai as genai
from typing import Optional, Dict, Any

from ..config import get_config
from .models import AnalysisStatus

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    A client for interacting with the Google Gemini API.
    Handles API key configuration and request execution.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initializes the Gemini client.
        
        Args:
            api_key: The Google AI API key. If not provided, it's loaded from settings.
        """
    settings = get_config()
    self.api_key = api_key or settings.gemini_api_key
        
        if not self.api_key:
            raise ValueError("Gemini API key is not configured.")
            
        genai.configure(api_key=self.api_key)
        self._model = None
    self.model_name = settings.gemini_model_name
        
    @property
    def model(self):
        """Lazy-loads the generative model."""
        if self._model is None:
            logger.info(f"Initializing Gemini model: {self.model_name}")
            self._model = genai.GenerativeModel(self.model_name)
        return self._model

    async def generate_content(
        self, 
        prompt: str,
        generation_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates content using the configured Gemini model.

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
                "usage_metadata": None
            }
            
        config = generation_config or {
            "temperature": 0.2,
            "top_p": 0.9,
            "top_k": 20,
            "max_output_tokens": 2048,
        }

        try:
            logger.debug(f"Sending prompt to Gemini: {prompt[:200]}...")
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(**config)
            )
            
            logger.debug("Received response from Gemini.")
            
            # Extract usage metadata if available
            usage_metadata = {}
            if response.usage_metadata:
                usage_metadata = {
                    "prompt_token_count": response.usage_metadata.prompt_token_count,
                    "candidates_token_count": response.usage_metadata.candidates_token_count,
                    "total_token_count": response.usage_metadata.total_token_count,
                }

            return {
                "status": AnalysisStatus.COMPLETED,
                "text": response.text,
                "usage_metadata": usage_metadata
            }

        except Exception as e:
            logger.error(f"Gemini API request failed: {e}", exc_info=True)
            return {
                "status": AnalysisStatus.FAILED,
                "error": str(e),
                "text": None,
                "usage_metadata": None
            }
