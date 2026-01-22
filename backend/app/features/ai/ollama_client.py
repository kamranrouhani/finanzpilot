"""Ollama API client for LLM interactions."""
import json
from typing import Any, Dict, Optional

import httpx

from app.config import settings


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0):
        """Initialize Ollama client.

        Args:
            base_url: Ollama API base URL (defaults to settings.OLLAMA_HOST)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or settings.OLLAMA_HOST
        self.timeout = timeout

    async def chat(
        self,
        model: str,
        messages: list[Dict[str, str]],
        temperature: float = 0.1,
        format: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send chat request to Ollama.

        Args:
            model: Model name (e.g., "qwen2.5:7b")
            messages: List of message dicts with role and content
            temperature: Sampling temperature (0.0-1.0)
            format: Optional response format ("json" for JSON output)

        Returns:
            Response dict from Ollama

        Raises:
            httpx.HTTPError: If request fails
            ValueError: If response is invalid
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }

        if format:
            payload["format"] = format

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException as e:
                raise ValueError(f"Ollama request timed out after {self.timeout}s") from e
            except httpx.HTTPError as e:
                raise ValueError(f"Ollama request failed: {str(e)}") from e

    async def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.1,
        format: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send generation request to Ollama.

        Args:
            model: Model name
            prompt: Text prompt
            temperature: Sampling temperature
            format: Optional response format ("json")

        Returns:
            Response dict from Ollama

        Raises:
            ValueError: If request fails
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }

        if format:
            payload["format"] = format

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException as e:
                raise ValueError(f"Ollama request timed out after {self.timeout}s") from e
            except httpx.HTTPError as e:
                raise ValueError(f"Ollama request failed: {str(e)}") from e

    def extract_json_from_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and parse JSON from Ollama response.

        Args:
            response: Ollama API response

        Returns:
            Parsed JSON dict

        Raises:
            ValueError: If JSON parsing fails
        """
        message = response.get("message", {})
        content = message.get("content", "")

        if not content:
            # Try response field for generate API
            content = response.get("response", "")

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON from Ollama response: {content}") from e


# Singleton instance
ollama_client = OllamaClient()
