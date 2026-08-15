from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services.providers.base_tts import TTSProviderError
from app.services.providers.openrouter_tts import OpenRouterTTSProvider
from app.services.providers.tts_manager import TTSProviderManager


@pytest.fixture(autouse=True)
def mock_voice_env(monkeypatch):
    """Ensure voice features and OPENROUTER_API_KEY are configured for unit tests."""
    monkeypatch.setattr(settings, "openrouter_api_key", "sk-or-v1-fake-test-key")
    monkeypatch.setattr(settings, "voice_enabled", True)


@pytest.fixture
def client():
    return TestClient(app)


def test_openrouter_tts_provider_properties():
    provider = OpenRouterTTSProvider()
    assert provider.name == "openrouter"
    assert provider.is_configured is True


@pytest.mark.asyncio
async def test_openrouter_tts_synthesize_success():
    provider = OpenRouterTTSProvider()
    fake_audio = b"\xff\xf3\x40\xc0" + b"\x00" * 100

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = lambda: None
        mock_response.content = fake_audio
        mock_post.return_value = mock_response

        audio_bytes = await provider.synthesize("Hello Friday")
        assert audio_bytes == fake_audio
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["json"]["model"] == settings.friday_tts_model
        assert call_kwargs["json"]["input"] == "Hello Friday"
        assert call_kwargs["json"]["voice"] == settings.friday_tts_voice
        assert call_kwargs["json"]["response_format"] == "mp3"


@pytest.mark.asyncio
async def test_openrouter_tts_empty_text_raises_error():
    provider = OpenRouterTTSProvider()
    with pytest.raises(TTSProviderError, match="Empty or blank text"):
        await provider.synthesize("   ")


@pytest.mark.asyncio
async def test_tts_manager_primary_success():
    manager = TTSProviderManager()
    fake_audio = b"\xff\xf3\x40\xc0\x00"

    with patch.object(
        manager.openrouter_provider, "synthesize", new_callable=AsyncMock
    ) as mock_openrouter:
        mock_openrouter.return_value = fake_audio

        audio_bytes, media_type, provider_name = await manager.synthesize("Test speech")

        assert audio_bytes == fake_audio
        assert media_type == "audio/mpeg"
        assert provider_name == "openrouter"
        mock_openrouter.assert_called_once()


@pytest.mark.asyncio
async def test_tts_manager_error_when_openrouter_fails():
    manager = TTSProviderManager()

    with patch.object(
        manager.openrouter_provider,
        "synthesize",
        side_effect=TTSProviderError("OpenRouter failed"),
    ):
        with pytest.raises(TTSProviderError, match="All TTS providers failed"):
            await manager.synthesize("Fallback test")


def test_voice_speak_endpoint_success(client):
    fake_audio = b"\xff\xf3\x40\xc0" * 10

    with patch(
        "app.services.providers.openrouter_tts.OpenRouterTTSProvider.synthesize",
        new_callable=AsyncMock,
    ) as mock_synthesize:
        mock_synthesize.return_value = fake_audio

        response = client.post("/voice/speak", json={"text": "Hello FRIDAY"})

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"
        assert response.content == fake_audio


def test_voice_speak_stream_endpoint_success(client):
    async def mock_stream_gen(*args, **kwargs):
        yield b"chunk1"
        yield b"chunk2"

    with patch(
        "app.services.providers.openrouter_tts.OpenRouterTTSProvider.stream_synthesize"
    ) as mock_stream:
        mock_stream.side_effect = mock_stream_gen

        response = client.post("/voice/speak/stream", json={"text": "Streaming test"})

        assert response.status_code == 200
        assert (
            response.headers["content-type"] == "audio/mpeg; charset=utf-8"
            or response.headers["content-type"] == "audio/mpeg"
        )
        assert response.content == b"chunk1chunk2"


def test_voice_speak_endpoint_disabled_returns_503(client, monkeypatch):
    """Verify production 503 behavior when voice_enabled is False."""
    monkeypatch.setattr(settings, "voice_enabled", False)
    response = client.post("/voice/speak", json={"text": "Hello FRIDAY"})
    assert response.status_code == 503
    assert "Voice features are disabled" in str(response.json())


def test_voice_speak_stream_endpoint_disabled_returns_503(client, monkeypatch):
    """Verify production 503 behavior when voice_enabled is False for stream endpoint."""
    monkeypatch.setattr(settings, "voice_enabled", False)
    response = client.post("/voice/speak/stream", json={"text": "Streaming test"})
    assert response.status_code == 503
    assert "Voice features are disabled" in str(response.json())
