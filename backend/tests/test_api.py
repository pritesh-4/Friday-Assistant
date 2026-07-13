from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.database import database
from app.main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Run every test against an isolated database and the offline LLM fallback."""
    database.configure(f"sqlite:///{(tmp_path / 'friday-test.db').as_posix()}")
    monkeypatch.setattr(settings, "openai_api_key", None)
    with TestClient(app) as test_client:
        yield test_client


def test_health_and_readiness(client: TestClient):
    assert client.get("/").json() == {"message": "FRIDAY API is online."}
    assert client.get("/health").json() == {"status": "ok", "service": "FRIDAY API"}
    assert client.get("/health/ready").json() == {"status": "ok", "database": "ready"}


def test_chat_persists_messages_and_uses_offline_fallback(client: TestClient):
    response = client.post("/chat", json={"message": "Remember this project plan."})

    assert response.status_code == 201
    payload = response.json()
    assert payload["provider"] == "local-fallback"
    assert payload["userMessage"]["content"] == "Remember this project plan."
    assert payload["assistantMessage"]["role"] == "assistant"

    conversation_id = payload["conversation"]["id"]
    messages = client.get(f"/chat/{conversation_id}/messages")
    assert messages.status_code == 200
    assert [message["role"] for message in messages.json()] == ["user", "assistant"]

    conversations = client.get("/chat").json()
    assert conversations[0]["id"] == conversation_id


def test_memory_settings_notes_and_tasks_are_persisted(client: TestClient):
    memory = client.post(
        "/memory",
        json={"title": "Preferred style", "value": "Concise answers", "category": "preferences"},
    )
    assert memory.status_code == 201
    assert client.get("/memory?query=concise").json()[0]["id"] == memory.json()["id"]

    settings_response = client.put(
        "/settings",
        json={
            "theme": "dark",
            "animations": True,
            "voiceEnabled": False,
            "sidebarCollapsed": True,
            "memoryEnabled": True,
            "notificationsEnabled": False,
        },
    )
    assert settings_response.status_code == 200
    assert settings_response.json()["sidebarCollapsed"] is True

    note = client.post("/notes", json={"title": "MVP", "content": "Ship the text path first."})
    assert note.status_code == 201
    assert client.get("/notes").json()[0]["id"] == note.json()["id"]

    task = client.post("/tasks", json={"title": "Run tests", "priority": "high"})
    assert task.status_code == 201
    completed = client.patch(f"/tasks/{task.json()['id']}", json={"status": "completed"})
    assert completed.json()["status"] == "completed"
