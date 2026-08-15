"""Focused unit tests for the Groq LLM provider and streaming fallback."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.agents.router_agent import RouterAgent
from app.core.config import settings
from app.services.providers.base import LLMProviderError, LLMResult
from app.services.providers.groq import GroqProvider


@pytest.fixture(autouse=True)
def mock_provider_env(monkeypatch):
    """Set mock provider keys for isolated unit testing."""
    monkeypatch.setattr(settings, "groq_api_key", "gsk-fake-test-key-for-unit-testing")
    monkeypatch.setattr(settings, "groq_model", "llama-3.3-70b-versatile")
    monkeypatch.setattr(
        settings, "fallback_chain", ["groq", "gemini", "openrouter", "nvidia"]
    )


def test_groq_provider_properties(monkeypatch):
    provider = GroqProvider()
    assert provider.name == "groq"
    assert provider.is_configured is True
    assert provider.supports_vision is False

    monkeypatch.setattr(settings, "groq_api_key", None)
    assert provider.is_configured is False


@pytest.mark.asyncio
async def test_groq_generate_response_payload_and_url():
    provider = GroqProvider()
    test_messages = [{"role": "user", "content": "Hello FRIDAY"}]

    mock_response_data = {
        "id": "chatcmpl-test",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Hello! How can I assist you?",
                },
                "finish_reason": "stop",
            }
        ],
    }

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None

    with patch(
        "httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response
    ) as mock_post:
        result = await provider.generate_response(test_messages)

        assert isinstance(result, LLMResult)
        assert result.content == "Hello! How can I assist you?"
        assert result.provider == "groq"
        assert result.model == "llama-3.3-70b-versatile"
        assert result.finish_reason == "stop"

        mock_post.assert_called_once()
        call_args, call_kwargs = mock_post.call_args
        assert call_args[0] == "https://api.groq.com/openai/v1/chat/completions"
        assert (
            call_kwargs["headers"]["Authorization"]
            == "Bearer gsk-fake-test-key-for-unit-testing"
        )
        assert call_kwargs["headers"]["Content-Type"] == "application/json"
        assert call_kwargs["json"]["model"] == "llama-3.3-70b-versatile"
        assert call_kwargs["json"]["messages"] == test_messages


@pytest.mark.asyncio
async def test_groq_stream_response_success():
    provider = GroqProvider()
    test_messages = [{"role": "user", "content": "Tell me a joke"}]

    sse_lines = [
        'data: {"choices": [{"delta": {"content": "Why did "}}]}',
        'data: {"choices": [{"delta": {"content": "the AI "}}]}',
        'data: {"choices": [{"delta": {"content": "cross the road?"}}]}',
        "data: [DONE]",
    ]

    async def mock_aiter_lines():
        for line in sse_lines:
            yield line

    mock_stream_response = MagicMock()
    mock_stream_response.status_code = 200
    mock_stream_response.raise_for_status.return_value = None
    mock_stream_response.aiter_lines = mock_aiter_lines

    class MockAsyncStreamContext:
        async def __aenter__(self):
            return mock_stream_response

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None

    with patch(
        "httpx.AsyncClient.stream", return_value=MockAsyncStreamContext()
    ) as mock_stream:
        chunks = []
        async for chunk in provider.stream_response(test_messages):
            chunks.append(chunk)

        assert "".join(chunks) == "Why did the AI cross the road?"
        mock_stream.assert_called_once()
        call_args, call_kwargs = mock_stream.call_args
        assert call_args[0] == "POST"
        assert call_args[1] == "https://api.groq.com/openai/v1/chat/completions"
        assert call_kwargs["json"]["stream"] is True
        assert call_kwargs["json"]["model"] == "llama-3.3-70b-versatile"


@pytest.mark.asyncio
async def test_groq_raises_when_unconfigured(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", None)
    provider = GroqProvider()

    with pytest.raises(LLMProviderError, match="Groq is not configured"):
        await provider.generate_response([{"role": "user", "content": "Hi"}])

    with pytest.raises(LLMProviderError, match="Groq is not configured"):
        async for _ in provider.stream_response([{"role": "user", "content": "Hi"}]):
            pass


@pytest.mark.asyncio
async def test_groq_http_error_handling():
    provider = GroqProvider()
    test_messages = [{"role": "user", "content": "Hello"}]

    mock_request = httpx.Request(
        "POST", "https://api.groq.com/openai/v1/chat/completions"
    )
    mock_response = httpx.Response(status_code=404, request=mock_request)
    http_err = httpx.HTTPStatusError(
        "Client error '404 Not Found' for URL: https://api.groq.com/openai/v1/chat/completions",
        request=mock_request,
        response=mock_response,
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=http_err):
        with pytest.raises(LLMProviderError, match="groq API error"):
            await provider.generate_response(test_messages)


@pytest.mark.asyncio
async def test_router_agent_stream_fallback_when_groq_fails(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "fake-gemini-key")

    router = RouterAgent()
    messages = [{"role": "user", "content": "Hello"}]

    async def mock_groq_stream_fail(*args, **kwargs):
        raise LLMProviderError("groq API streaming error: Client error '404 Not Found'")
        yield ""  # pragma: no cover

    async def mock_gemini_stream_success(*args, **kwargs):
        yield "Hello from Gemini fallback!"

    with (
        patch.object(
            router.executive_planner, "plan", new_callable=AsyncMock
        ) as mock_plan,
        patch(
            "app.services.providers.groq.GroqProvider.stream_response",
            side_effect=mock_groq_stream_fail,
        ),
        patch(
            "app.services.providers.gemini.GeminiProvider.stream_response",
            side_effect=mock_gemini_stream_success,
        ),
    ):
        mock_mission = MagicMock()
        mock_mission.primary_goal = "Chat"
        mock_mission.risks.requires_confirmation = False
        mock_mission.risks.level.value = "safe"
        mock_mission.tools = []
        mock_plan.return_value = mock_mission

        collected = []
        async for chunk in router.route_and_stream(messages):
            collected.append(chunk)

        assert "".join(collected) == "Hello from Gemini fallback!"
