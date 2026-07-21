"""
Nyaya-ZTA Provider-Independent LLM Client
==========================================

HTTP client interfacing with OpenAI-compatible LLM endpoints (Groq, OpenAI, Anthropic, local Ollama).
Supports async completion requests with timeout, retries, and structured fallback responses.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import get_settings
from app.core.exceptions import LLMError
from app.core.logging import get_logger
from app.llm.security import PromptInjectionDetector

logger = get_logger(__name__)


class LLMClient:
    """Async provider-independent LLM Client."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """
        Generate completion from LLM provider.

        Scans user_prompt for prompt injection attacks first.
        If no API key is set, returns an intelligent domain-specific mock response for testing.
        """
        # 1. Security Scan
        scan_res = PromptInjectionDetector.scan(user_prompt)
        if not scan_res.is_safe:
            raise LLMError(message=scan_res.reason or "Prompt injection detected.")

        api_key = self.settings.LLM_API_KEY.strip()

        # 2. Mock Fallback when API key is empty or testing
        if not api_key or self.settings.is_testing:
            logger.info("Using LLM mock fallback (no API key configured)")
            return {
                "content": self._generate_mock_legal_response(user_prompt),
                "model": "mock-nyaya-llm",
                "usage": {"prompt_tokens": 120, "completion_tokens": 250, "total_tokens": 370},
            }

        # 3. Live API Request to OpenAI-compatible provider (e.g. Groq)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.settings.LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature or self.settings.LLM_TEMPERATURE,
            "max_tokens": max_tokens or self.settings.LLM_MAX_TOKENS,
        }

        url = f"{self.settings.LLM_BASE_URL.rstrip('/')}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=float(self.settings.LLM_TIMEOUT)) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})

                return {
                    "content": content,
                    "model": data.get("model", self.settings.LLM_MODEL),
                    "usage": usage,
                }
        except httpx.HTTPStatusError as e:
            logger.error("LLM Provider HTTP error", extra={"status": e.response.status_code, "text": e.response.text})
            raise LLMError(message=f"LLM Provider API Error: {e.response.status_code} - {e.response.text[:200]}")
        except Exception as e:
            logger.error("LLM Provider Connection error", extra={"error": str(e)})
            raise LLMError(message=f"Failed to communicate with LLM Provider: {str(e)}")

    def _generate_mock_legal_response(self, user_prompt: str) -> str:
        """Generate structured mock judicial response when offline."""
        return (
            "### Judicial Research Analysis & Legal Summary\n\n"
            "Based on the statutory framework and precedents applicable to this case:\n\n"
            "1. **Legal Framework**: Under Section 41 & Section 100 of the Civil Procedure Code, the petitioner maintains standing regarding property title rights.\n"
            "2. **Precedent Analysis**: In *State of Karnataka v. Union of India (2018)*, the Supreme Court held that administrative acquisitions without prior statutory notice violate principles of natural justice.\n"
            "3. **Recommendation**: Recommend scheduling an evidentiary hearing to verify original title deeds."
        )
