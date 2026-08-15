from unittest.mock import patch, AsyncMock
import pytest
from app.core.config import settings


@pytest.fixture(autouse=True)
def mock_voice_env(monkeypatch):
    """Ensure voice features and OPENROUTER_API_KEY are configured for unit tests."""
    monkeypatch.setattr(settings, "openrouter_api_key", "sk-or-v1-fake-test-key")
    monkeypatch.setattr(settings, "voice_enabled", True)


def test_websocket_voice_stream_success(client):
    """
    Test the full-duplex WebSocket voice stream endpoint.
    Verifies that the reader, writer, and STT loops execute correctly.
    """
    mock_transcribe_result = {
        "transcript": "hello Friday",
        "detected_language": "en",
        "confidence": 0.99,
        "duration": 1.5,
        "segments": [],
        "metadata": {},
    }

    async def mock_stream_chat(*args, **kwargs):
        yield 'data: {"type": "status", "status": "processing_intent"}\n\n'
        yield 'data: {"type": "metadata", "conversationId": "test_conv", "title": "test"}\n\n'
        yield 'data: {"type": "chunk", "content": "Hello! How can I help you today?"}\n\n'
        yield 'data: {"type": "sentence", "content": "Hello!"}\n\n'
        yield 'data: {"type": "sentence", "content": "How can I help you today?"}\n\n'
        yield 'data: {"type": "done"}\n\n'

    with (
        patch(
            "app.ai.whisper.engine.WhisperEngine.transcribe_array",
            new_callable=AsyncMock,
            return_value=mock_transcribe_result,
        ),
        patch(
            "app.services.streaming_coordinator.StreamingCoordinator.stream_chat",
            side_effect=mock_stream_chat,
        ),
    ):
        with client.websocket_connect("/api/voice/stream") as websocket:
            # 1. Send start command
            websocket.send_json({"type": "start", "conversation_id": "test_conv"})
            resp = websocket.receive_json()
            assert resp["type"] == "session_started"

            # 2. Send dummy audio bytes
            websocket.send_bytes(b"\x00" * 3200)

            # 3. Send stop command to finalize turn
            websocket.send_json({"type": "stop"})

            # 4. Await processing status
            resp = websocket.receive_json()
            assert resp["type"] == "status"
            assert resp["state"] == "transcribing"

            # 5. Await transcript output
            resp = websocket.receive_json()
            assert resp["type"] == "transcript"
            assert resp["text"] == "hello Friday"
            assert resp["final"] is True

            # 6. Await intent status
            resp = websocket.receive_json()
            assert resp["type"] == "status"
            assert resp["state"] == "processing_intent"

            # 7. Await stream metadata & chunks
            resp = websocket.receive_json()
            assert resp["type"] == "status"
            assert resp["status"] == "processing_intent"

            resp = websocket.receive_json()
            assert resp["type"] == "metadata"
            assert resp["conversationId"] == "test_conv"

            resp = websocket.receive_json()
            assert resp["type"] == "chunk"
            assert resp["content"] == "Hello! How can I help you today?"

            resp = websocket.receive_json()
            assert resp["type"] == "sentence"

            resp = websocket.receive_json()
            assert resp["type"] == "sentence"

            resp = websocket.receive_json()
            assert resp["type"] == "done"


def test_websocket_voice_stream_interrupt(client):
    """
    Test the barge-in/interruption cancellation trigger on the WebSocket.
    """
    mock_transcribe_result = {
        "transcript": "hello Friday",
        "detected_language": "en",
        "confidence": 0.99,
        "duration": 1.5,
        "segments": [],
        "metadata": {},
    }

    # Simulate an LLM stream that hangs/generates slow to verify interruption cancels it
    async def mock_stream_chat_slow(*args, **kwargs):
        yield 'data: {"type": "status", "status": "processing_intent"}\n\n'
        import asyncio

        try:
            # Sleep to allow the client to trigger interrupt
            await asyncio.sleep(5)
            yield 'data: {"type": "chunk", "content": "I should not reach this"}\n\n'
        except asyncio.CancelledError:
            # Expected when interrupted/cancelled
            raise

    with (
        patch(
            "app.ai.whisper.engine.WhisperEngine.transcribe_array",
            new_callable=AsyncMock,
            return_value=mock_transcribe_result,
        ),
        patch(
            "app.services.streaming_coordinator.StreamingCoordinator.stream_chat",
            side_effect=mock_stream_chat_slow,
        ),
    ):
        with client.websocket_connect("/api/voice/stream") as websocket:
            websocket.send_json({"type": "start", "conversation_id": "test_conv"})
            websocket.receive_json()  # session_started

            websocket.send_bytes(b"\x00" * 3200)
            websocket.send_json({"type": "stop"})

            # Transcribing status
            websocket.receive_json()
            # Final transcript
            websocket.receive_json()
            # Processing intent status
            websocket.receive_json()
            # stream_chat first yield
            websocket.receive_json()

            # Now, send an interrupt frame to trigger cancellation
            websocket.send_json({"type": "interrupt"})

            # Verify the task gets cancelled and backend yields 'interrupted' event
            resp = websocket.receive_json()
            assert resp["type"] == "interrupted"
