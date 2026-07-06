"""Azure OpenAI client wrapper with retry logic, cost calculation, and logging."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

from openai import AsyncAzureOpenAI, AsyncOpenAI, APIConnectionError, APITimeoutError, RateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

import sqlite3
from app.features.provider.encryption import decrypt_api_key
from app.config import Settings
from app.core.exceptions import AIServiceError

logger = logging.getLogger("pocket.ai.client")


def _get_default_provider_sync(settings: Settings) -> dict[str, Any] | None:
    try:
        db_url = settings.database_url
        path = db_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
        
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT provider_type, endpoint, api_version, deployment_chat, "
            "deployment_chat_mini, deployment_embedding, api_key_encrypted "
            "FROM providers WHERE is_default = 1 AND deleted_at IS NULL LIMIT 1"
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "provider_type": row[0],
                "endpoint": row[1],
                "api_version": row[2],
                "deployment_chat": row[3],
                "deployment_chat_mini": row[4],
                "deployment_embedding": row[5],
                "api_key": decrypt_api_key(row[6] or "")
            }
    except Exception as e:
        logger.debug("Failed to fetch default provider from database: %s", e)
    return None


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
        rates = {
            "gpt-4.1": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
            "gpt-4.1-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
        }
        
        model_key = "gpt-4.1"
        for key in sorted(rates.keys(), key=len, reverse=True):
            if key in self.model:
                model_key = key
                break
                
        rate = rates[model_key]
        self.cost = (self.prompt_tokens * rate["input"]) + (self.completion_tokens * rate["output"])
        return self.cost


class AzureAIClient:
    """Centralized client for Azure OpenAI and compatible LLMs. Manages database configurations, authentication, retries, and costs."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._provider = _get_default_provider_sync(settings)
        
        if self._provider:
            provider_type = self._provider["provider_type"]
            endpoint = self._provider["endpoint"]
            api_key = self._provider["api_key"]
            api_version = self._provider["api_version"]
            
            if provider_type in ("openai", "openai_compatible"):
                self._client = AsyncOpenAI(
                    base_url=endpoint,
                    api_key=api_key,
                )
                logger.info("AI Client initialized using OpenAI-compatible default provider from database.")
            else:
                self._client = AsyncAzureOpenAI(
                    azure_endpoint=endpoint,
                    api_key=api_key,
                    api_version=api_version,
                )
                logger.info("AI Client initialized using Azure OpenAI default provider from database.")
        else:
            if settings.azure_openai_endpoint and settings.azure_openai_api_key:
                self._client = AsyncAzureOpenAI(
                    azure_endpoint=settings.azure_openai_endpoint,
                    api_key=settings.azure_openai_api_key,
                    api_version=settings.azure_openai_api_version,
                )
                logger.info("AI Client initialized using environment settings.")
            else:
                self._client = None
                logger.warning("Azure OpenAI API settings not fully configured. AI client will fail if called.")

    def _ensure_client(self) -> None:
        if self._client is None:
            raise AIServiceError(
                "Azure OpenAI client is not initialized. Please configure POCKET_AZURE_OPENAI_ENDPOINT "
                "and POCKET_AZURE_OPENAI_API_KEY in the .env file or register an active default provider in settings."
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
        
        # Intercept and map models dynamically if a database provider is active
        if self._provider:
            if model == self._settings.azure_openai_deployment_chat:
                deployment = self._provider["deployment_chat"] or model
            elif model == self._settings.azure_openai_deployment_chat_mini:
                deployment = self._provider["deployment_chat_mini"] or model
            elif model is None:
                deployment = self._provider["deployment_chat"] or self._settings.azure_openai_deployment_chat
            else:
                deployment = model
        else:
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
        # Intercept and map embedding model dynamically if a database provider is active
        if self._provider:
            if model == self._settings.azure_openai_deployment_embedding:
                deployment = self._provider["deployment_embedding"] or model
            elif model is None:
                deployment = self._provider["deployment_embedding"] or self._settings.azure_openai_deployment_embedding
            else:
                deployment = model
        else:
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
