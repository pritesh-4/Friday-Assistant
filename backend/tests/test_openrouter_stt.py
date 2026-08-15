from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import settings
from app.services.providers.base_stt import STTProviderError
from app.services.providers.openrouter_stt import OpenRouterWhisperTurbo
from app.services.providers.stt_manager import STTProviderManager


@pytest.fixture(autouse=True)
def mock_openrouter_api_key(monkeypatch):
    """Ensure OPENROUTER_API_KEY is configured for unit tests."""
    monkeypatch.setattr(settings, "openrouter_api_key", "sk-or-v1-fake-test-key")


def test_openrouter_stt_properties():
    provider = OpenRouterWhisperTurbo()
    assert provider.name == "openrouter_whisper"
    assert provider.is_configured is True


@pytest.mark.asyncio
async def test_openrouter_stt_validation():
    provider = OpenRouterWhisperTurbo()

    # Empty payload
    with pytest.raises(STTProviderError, match="empty or too small"):
        provider.validate_audio(b"")

    # Too small payload
    with pytest.raises(STTProviderError, match="empty or too small"):
        provider.validate_audio(b"short")

    # Invalid MIME
    with pytest.raises(STTProviderError, match="Unsupported audio MIME type"):
        provider.validate_audio(b"x" * 200, mime_type="invalid/mime")


@pytest.mark.asyncio
async def test_openrouter_stt_transcribe_success():
    provider = OpenRouterWhisperTurbo()
    fake_audio = b"RIFF" + b"\x00" * 200

    with patch.object(
        provider.client, "transcribe_audio", new_callable=AsyncMock
    ) as mock_transcribe:
        mock_transcribe.return_value = {
            "text": "Hello Friday STT",
            "language": "en",
        }

        res = await provider.transcribe(
            fake_audio, filename="test.wav", mime_type="audio/wav"
        )

        assert res["transcript"] == "Hello Friday STT"
        assert res["detected_language"] == "en"
        assert res["provider"] == "openrouter_whisper"
        mock_transcribe.assert_called_once()


@pytest.mark.asyncio
async def test_stt_manager_fallback_to_faster_whisper():
    manager = STTProviderManager()
    fake_audio = b"RIFF" + b"\x00" * 200

    with (
        patch.object(
            manager.openrouter_provider,
            "transcribe",
            side_effect=STTProviderError("OpenRouter 402 Payment Required"),
        ),
        patch.object(
            manager.faster_whisper_provider, "transcribe", new_callable=AsyncMock
        ) as mock_local,
    ):
        mock_local.return_value = {
            "transcript": "Local fallback transcript",
            "detected_language": "en",
            "confidence": 0.98,
            "duration": 1.5,
            "provider": "faster_whisper",
        }

        res = await manager.transcribe(fake_audio)

        assert res["transcript"] == "Local fallback transcript"
        assert res["provider"] == "faster_whisper"
        mock_local.assert_called_once()
