from unittest.mock import patch

import pytest


@pytest.fixture
def mock_upload():
    with patch("app.services.voice_service.VoiceService.upload_audio") as mock:
        mock.return_value = {"filename": "test.webm", "upload_id": "123", "status": "completed"}
        yield mock

@pytest.fixture
def mock_transcribe():
    with patch("app.services.voice.transcription_service.TranscriptionService.transcribe") as mock:
        mock.return_value = {
            "transcript": "Hello world",
            "detected_language": "en",
            "confidence": 0.99,
            "duration": 2.0,
            "processing_time": 0.5,
            "segments": [{"id": 0, "start": 0.0, "end": 2.0, "text": "Hello world"}],
            "metadata": None
        }
        yield mock

def test_get_voice_status(client):
    response = client.get("/voice")
    assert response.status_code == 200
    assert response.json()["available"] is True
    
def test_transcribe_voice_success(client, mock_upload, mock_transcribe):
    # Simulate a file upload
    file_content = b"fake audio content"
    files = {"file": ("test.webm", file_content, "audio/webm")}
    
    response = client.post("/voice/transcribe", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["transcript"] == "Hello world"
    assert data["detected_language"] == "en"
    assert data["confidence"] == 0.99
    assert data["duration"] == 2.0
    assert len(data["segments"]) == 1
    
    mock_upload.assert_called_once()
    mock_transcribe.assert_called_once()

def test_transcribe_voice_upload_failure(client):
    with patch("app.services.voice_service.VoiceService.upload_audio") as mock:
        # We can simulate an exception
        from fastapi import HTTPException
        mock.side_effect = HTTPException(status_code=400, detail="Empty filename")
        
        file_content = b"fake audio content"
        files = {"file": ("test.webm", file_content, "audio/webm")}
        
        response = client.post("/voice/transcribe", files=files)
        assert response.status_code == 400
        assert "Empty filename" in response.json()["detail"]

def test_transcribe_voice_inference_failure(client, mock_upload):
    with patch("app.services.voice.transcription_service.TranscriptionService.transcribe") as mock:
        from fastapi import HTTPException
        mock.side_effect = HTTPException(status_code=500, detail="Failed to transcribe audio file due to an internal error.")
        
        file_content = b"fake audio content"
        files = {"file": ("test.webm", file_content, "audio/webm")}
        
        response = client.post("/voice/transcribe", files=files)
        assert response.status_code == 500
        assert "internal error" in response.json()["detail"]
