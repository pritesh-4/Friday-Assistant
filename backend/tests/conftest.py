"""
Shared pytest fixtures for the FRIDAY backend test suite.

All fixtures in this file are automatically discovered by pytest and available
to every test module without explicit import.

Isolation strategy:
- Each test gets its own temporary SQLite database.
- The OpenAI API key is patched to None to force the offline fallback.
- The TestClient handles the FastAPI lifespan (startup/shutdown) automatically.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.database import database
from app.main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """
    Provide an isolated TestClient for each test.

    - Uses a fresh SQLite database in a temporary directory.
    - Disables the OpenAI API key to ensure the offline fallback is used.
    - The FastAPI lifespan (DB initialisation) runs automatically via TestClient.
    """
    database.configure(f"sqlite:///{(tmp_path / 'friday-test.db').as_posix()}")
    monkeypatch.setattr(settings, "groq_api_key", None)
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "openrouter_api_key", None)
    monkeypatch.setattr(settings, "nvidia_api_key", None)
    monkeypatch.setattr(settings, "voice_enabled", True)
    monkeypatch.setattr(settings, "uploads_directory", tmp_path / "uploads")
    monkeypatch.setattr(settings, "voice_uploads_directory", tmp_path / "voice_uploads")
    
    # Mock whisper and TTS initialization to prevent downloading large models during tests
    from unittest.mock import patch, MagicMock, AsyncMock, PropertyMock
    import sys
    
    # Fake modules for main.py startup check
    mock_module = MagicMock()
    sys.modules['faster_whisper'] = mock_module
    sys.modules['ctranslate2'] = mock_module
    sys.modules['av'] = mock_module
    sys.modules['tokenizers'] = mock_module
    
    mock_subprocess_result = MagicMock()
    mock_subprocess_result.stdout = "1.5"
    mock_subprocess_result.stderr = ""
    
    mock_transcribe_result = {
        "transcript": "Test transcript",
        "detected_language": "en",
        "confidence": 0.99,
        "duration": 1.5,
        "segments": [{"id": 1, "start": 0.0, "end": 1.5, "text": "Test transcript"}],
        "metadata": {"all_language_probs": None}
    }

    with patch("app.ai.whisper.engine.WhisperEngine.is_loaded", new_callable=PropertyMock, return_value=True), \
         patch("app.ai.whisper.engine.WhisperEngine.load_model", return_value=None), \
         patch("app.ai.whisper.engine.WhisperEngine.transcribe", new_callable=AsyncMock, return_value=mock_transcribe_result), \
         patch("app.ai.tts.loader.initialize_tts_model", return_value=True), \
         patch("app.ai.tts.loader.is_tts_available", return_value=True), \
         patch("app.services.voice.speech_service.SpeechService.synthesize", new_callable=AsyncMock, return_value=b"fake_audio"), \
         patch("app.services.voice.transcription_service.subprocess.run", return_value=mock_subprocess_result), \
         patch("app.services.voice_service.subprocess.run", return_value=mock_subprocess_result), \
         patch("shutil.which", return_value="/usr/bin/ffmpeg"):
        with TestClient(app) as test_client:
            yield test_client
