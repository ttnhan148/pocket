"""Azure OpenAI client wrapper with retry logic, cost calculation, and logging."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

from openai import AsyncAzureOpenAI, APIConnectionError, APITimeoutError, RateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import Settings
from app.core.exceptions import AIServiceError

logger = logging.getLogger("pocket.ai.client")


@dataclass
class ChatResult:
    """Represents the result of a chat completion request."""
    content: str
    finish_reason: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    latency_ms: int | None = None
    cost: float = 0.0

    def compute_cost(self) -> float:
        """Compute the cost of the completion based on model token rates."""
        # Rates per token (approximate based on Azure OpenAI pricing)
        # Rates per 1,000,000 tokens:
        # GPT-4.0/4.1 (gpt-4o level): input $2.50, output $10.00
        # GPT-4.0-mini/4.1-mini: input $0.15, output $0.60
        # Default: fallback rates
        rates = {
            "gpt-4.1": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
            "gpt-4.1-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
        }
        
        # Match base model name (check more specific keys first)
        model_key = "gpt-4.1"
        for key in sorted(rates.keys(), key=len, reverse=True):
            if key in self.model:
                model_key = key
                break
                
        rate = rates[model_key]
        self.cost = (self.prompt_tokens * rate["input"]) + (self.completion_tokens * rate["output"])
        return self.cost


class AzureAIClient:
    """Centralized client for Azure OpenAI. Manages authentication, retries, and costs."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        # Only initialize the internal OpenAI client if credentials are provided
        if settings.azure_openai_endpoint and settings.azure_openai_api_key:
            self._client = AsyncAzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
            )
        else:
            self._client = None
            logger.warning("Azure OpenAI API settings not fully configured. AI client will fail if called.")

    def _ensure_client(self) -> None:
        if self._client is None:
            raise AIServiceError(
                "Azure OpenAI client is not initialized. Please configure POCKET_AZURE_OPENAI_ENDPOINT "
                "and POCKET_AZURE_OPENAI_API_KEY in the .env file."
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((APIConnectionError, APITimeoutError, RateLimitError)),
        reraise=True,
    )
    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: dict[str, Any] | None = None,
        timeout: float = 60.0,
    ) -> ChatResult:
        """Execute chat completion request with retry handling."""
        self._ensure_client()
        deployment = model or self._settings.azure_openai_deployment_chat
        
        start_time = time.monotonic()
        try:
            response = await self._client.chat.completions.create(
                model=deployment,
                messages=messages,  # type: ignore
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,  # type: ignore
                timeout=timeout,
            )
            latency_ms = int((time.monotonic() - start_time) * 1000)
            
            prompt_tokens = response.usage.prompt_tokens if response.usage else 0
            completion_tokens = response.usage.completion_tokens if response.usage else 0
            total_tokens = response.usage.total_tokens if response.usage else 0
            
            result = ChatResult(
                content=response.choices[0].message.content or "",
                finish_reason=response.choices[0].finish_reason or "stop",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                model=deployment,
                latency_ms=latency_ms,
            )
            result.compute_cost()
            
            logger.info(
                "AI Chat Completion Success: model=%s, tokens=%d, cost=$%.6f, latency=%dms",
                deployment,
                result.total_tokens,
                result.cost,
                latency_ms,
            )
            return result
            
        except Exception as e:
            logger.error("Azure OpenAI chat API error: %s", str(e), exc_info=True)
            if isinstance(e, (APIConnectionError, APITimeoutError, RateLimitError)):
                # Let tenacity retry this
                raise
            raise AIServiceError(f"Azure OpenAI error: {str(e)}")

    async def chat_json(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Execute chat completion with JSON mode, returning parsed dict."""
        result = await self.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        try:
            return json.loads(result.content)
        except json.JSONDecodeError as e:
            logger.error("AI JSON response failed to parse: %s", result.content)
            raise AIServiceError(f"AI response was not valid JSON: {str(e)}")

    async def embed(
        self,
        texts: list[str],
        *,
        model: str | None = None,
        dimensions: int | None = None,
    ) -> list[list[float]]:
        """Generate embeddings using Azure OpenAI model."""
        self._ensure_client()
        deployment = model or self._settings.azure_openai_deployment_embedding
        
        try:
            kwargs = {}
            if dimensions is not None:
                kwargs["dimensions"] = dimensions
                
            response = await self._client.embeddings.create(
                model=deployment,
                input=texts,
                **kwargs,  # type: ignore
            )
            
            # Simple log (input count and deployment)
            logger.info(
                "AI Embeddings Success: model=%s, count=%d",
                deployment,
                len(texts),
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error("Azure OpenAI embedding API error: %s", str(e), exc_info=True)
            raise AIServiceError(f"Azure OpenAI Embedding error: {str(e)}")
