from unittest.mock import patch

import pytest
from fastapi import HTTPException
from app.core.config import settings


@pytest.fixture(autouse=True)
def mock_voice_env(monkeypatch):
    """Ensure voice features and OPENROUTER_API_KEY are configured for unit tests."""
    monkeypatch.setattr(settings, "openrouter_api_key", "sk-or-v1-fake-test-key")
    monkeypatch.setattr(settings, "voice_enabled", True)


@pytest.fixture
def mock_transcribe():
    with patch(
        "app.services.voice.transcription_service.TranscriptionService.transcribe"
    ) as mock:
        mock.return_value = {
            "transcript": "Hello world",
            "detected_language": "en",
            "confidence": 0.99,
            "duration": 2.0,
            "processing_time": 0.5,
            "segments": [{"id": 0, "start": 0.0, "end": 2.0, "text": "Hello world"}],
            "metadata": None,
        }
        yield mock


@pytest.fixture
def mock_orchestrator():
    with patch(
        "app.services.voice.orchestrator.VoiceOrchestrator.process_conversation"
    ) as mock:
        mock.return_value = {
            "transcript": "Hello world",
            "response": "Hello to you too!",
            "conversation_id": "conv_123",
            "latency": {"stt": 1.0, "provider": 2.0, "total": 3.0},
        }
        yield mock


@pytest.fixture
def mock_orchestrator_stream():
    async def mock_stream(*args, **kwargs):
        yield 'data: {"type": "transcript", "text": "Hello world"}\n\n'
        yield 'data: {"type": "chunk", "content": "Hello to you too!"}\n\n'
        yield 'data: {"type": "done"}\n\n'

    with patch(
        "app.services.voice.orchestrator.VoiceOrchestrator.stream_conversation"
    ) as mock:
        mock.side_effect = mock_stream
        yield mock


def test_get_voice_status(client):
    response = client.get("/voice")
    assert response.status_code == 200
    assert response.json()["available"] is True


def test_transcribe_voice_success(client, mock_transcribe):
    file_content = b"fake audio content"
    files = {"file": ("test.webm", file_content, "audio/webm")}

    response = client.post("/voice/transcribe", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["transcript"] == "Hello world"
    assert data["detected_language"] == "en"

    mock_transcribe.assert_called_once()


def test_transcribe_voice_upload_failure(client):
    file_content = b"fake audio content"
    files = {"file": ("test.webm", file_content, "application/json")}

    response = client.post("/voice/transcribe", files=files)
    assert response.status_code == 415
    assert "Unsupported MIME type" in response.json()["error"]["message"]


def test_transcribe_voice_inference_failure(client):
    with patch(
        "app.services.voice.transcription_service.TranscriptionService.transcribe"
    ) as mock:
        mock.side_effect = HTTPException(
            status_code=500,
            detail="Failed to transcribe audio file due to an internal error.",
        )

        file_content = b"fake audio content"
        files = {"file": ("test.webm", file_content, "audio/webm")}

        response = client.post("/voice/transcribe", files=files)
        assert response.status_code == 500
        assert "internal error" in response.json()["error"]["message"]


def test_orchestrate_voice_success(client, mock_orchestrator):
    file_content = b"fake audio content"
    files = {"file": ("test.webm", file_content, "audio/webm")}
    data = {"conversation_id": "conv_123"}

    response = client.post("/voice/orchestrate", files=files, data=data)

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["transcript"] == "Hello world"
    assert res_data["response"] == "Hello to you too!"
    assert res_data["conversation_id"] == "conv_123"

    mock_orchestrator.assert_called_once()


def test_orchestrate_voice_stream_success(client, mock_orchestrator_stream):
    file_content = b"fake audio content"
    files = {"file": ("test.webm", file_content, "audio/webm")}
    data = {"conversation_id": "conv_123"}

    response = client.post("/voice/orchestrate/stream", files=files, data=data)

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    content = response.content.decode("utf-8")
    assert 'data: {"type": "transcript", "text": "Hello world"}' in content
    assert 'data: {"type": "chunk", "content": "Hello to you too!"}' in content
    assert 'data: {"type": "done"}' in content

    mock_orchestrator_stream.assert_called_once()


@patch("app.ai.whisper.engine.WhisperEngine.transcribe_array")
@pytest.mark.asyncio
async def test_transcribe_array_success(mock_transcribe_arr):
    mock_transcribe_arr.return_value = {
        "transcript": "Hello from memory",
        "detected_language": "en",
        "confidence": 0.99,
        "duration": 2.0,
        "segments": [],
        "metadata": {},
    }
    from app.services.voice.transcription_service import TranscriptionService
    import numpy as np

    service = TranscriptionService()
    fake_samples = np.zeros(16000, dtype=np.float32)
    res = await service.transcribe_array(fake_samples)

    assert res["transcript"] == "Hello from memory"
    assert res["detected_language"] == "en"
    mock_transcribe_arr.assert_called_once_with(fake_samples)
