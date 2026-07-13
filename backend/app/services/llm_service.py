from dataclasses import dataclass
from collections.abc import Sequence

import httpx

from app.core.config import settings


class LLMProviderError(RuntimeError):
    """Raised when a configured provider cannot produce a response."""


@dataclass(frozen=True)
class LLMResult:
    content: str
    provider: str


class LLMService:
    """Generate chat replies through OpenAI when configured, or an offline fallback."""

    async def generate_response(
        self, messages: Sequence[dict[str, str]]
    ) -> LLMResult:
        if not settings.openai_api_key:
            return LLMResult(
                content=(
                    "I saved your message to this conversation. Configure "
                    "OPENAI_API_KEY in backend/.env to enable AI-generated replies."
                ),
                provider="local-fallback",
            )

        payload = {"model": settings.openai_model, "messages": list(messages)}
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        timeout = httpx.Timeout(settings.llm_request_timeout_seconds)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMProviderError("The configured OpenAI provider is unavailable.") from exc

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError("The OpenAI provider returned an invalid response.") from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMProviderError("The OpenAI provider returned an empty response.")
        return LLMResult(content=content.strip(), provider="openai")
