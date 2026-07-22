"""Integration tests for the FRIDAY API.

The ``client`` fixture is defined in ``conftest.py`` and injected automatically.
"""

from fastapi.testclient import TestClient


def test_health_and_readiness(client: TestClient):
    root = client.get("/").json()
    assert root["message"] == "FRIDAY API is online."
    assert root["version"]

    health = client.get("/health").json()
    assert health["status"] == "ok"
    assert health["service"] == "FRIDAY API"
    assert health["version"]

    ready = client.get("/health/ready").json()
    assert ready["status"] == "ok"
    assert ready["database"] == "ready"


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
    assert [m["role"] for m in messages.json()] == ["user", "assistant"]

    conversations = client.get("/chat").json()
    assert conversations[0]["id"] == conversation_id


def test_memory_crud_and_search(client: TestClient):
    # Create
    memory = client.post(
        "/memory",
        json={"title": "Preferred style", "value": "Concise answers", "category": "preferences"},
    )
    assert memory.status_code == 201
    memory_id = memory.json()["id"]

    # Search
    assert client.get("/memory?query=concise").json()[0]["id"] == memory_id

    # Get by ID
    fetched = client.get(f"/memory/{memory_id}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == memory_id

    # Categories
    cats = client.get("/memory/categories").json()
    assert "preferences" in cats

    # Update
    updated = client.patch(f"/memory/{memory_id}", json={"value": "Very concise answers"})
    assert updated.status_code == 200
    assert "Very concise" in updated.json()["value"]

    # Pin
    pinned = client.post(f"/memory/{memory_id}/pin")
    assert pinned.status_code == 200
    assert pinned.json()["pinned"] is True

    # Unpin
    unpinned = client.delete(f"/memory/{memory_id}/pin")
    assert unpinned.status_code == 200
    assert unpinned.json()["pinned"] is False

    # Delete
    deleted = client.delete(f"/memory/{memory_id}")
    assert deleted.status_code == 204
    assert client.get(f"/memory/{memory_id}").status_code == 404


def test_settings_notes_and_tasks(client: TestClient):
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

    # Notes CRUD
    note = client.post("/notes", json={"title": "MVP", "content": "Ship the text path first."})
    assert note.status_code == 201
    note_id = note.json()["id"]
    assert client.get("/notes").json()[0]["id"] == note_id
    assert client.get(f"/notes/{note_id}").status_code == 200
    patched = client.patch(f"/notes/{note_id}", json={"title": "MVP v2"})
    assert patched.status_code == 200
    assert patched.json()["title"] == "MVP v2"

    # Tasks CRUD
    task = client.post("/tasks", json={"title": "Run tests", "priority": "high"})
    assert task.status_code == 201
    completed = client.patch(f"/tasks/{task.json()['id']}", json={"status": "completed"})
    assert completed.json()["status"] == "completed"


def test_voice_status(client: TestClient):
    response = client.get("/voice")
    assert response.status_code == 200
    assert response.json()["available"] is False

    assert client.post("/voice/transcribe").status_code == 501
    assert client.post("/voice/synthesize").status_code == 501


def test_voice_upload(client: TestClient):
    # Success upload
    res = client.post(
        "/voice/upload",
        files={"file": ("test.webm", b"fake audio content", "audio/webm")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert "upload_id" in data
    assert data["mime_type"] == "audio/webm"
    assert data["size"] == len(b"fake audio content")

    # Invalid MIME type
    res2 = client.post(
        "/voice/upload",
        files={"file": ("test.txt", b"fake text content", "text/plain")},
    )
    assert res2.status_code == 415
    assert "Unsupported media type" in res2.json()["detail"]

    # Empty file
    res3 = client.post(
        "/voice/upload",
        files={"file": ("empty.webm", b"", "audio/webm")},
    )
    assert res3.status_code == 400
    assert "Empty file upload" in res3.json()["detail"]


def test_404_returns_consistent_envelope(client: TestClient):
    response = client.get("/nonexistent-path")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_file_upload_and_deletion(client: TestClient):
    # Upload text file
    response = client.post(
        "/files",
        files={"file": ("test_doc.txt", b"Hello Friday project context", "text/plain")},
    )
    assert response.status_code == 201
    uploaded = response.json()
    assert uploaded["name"] == "test_doc.txt"
    file_id = uploaded["id"]

    # List files
    files_list = client.get("/files").json()
    assert any(f["id"] == file_id for f in files_list)

    # Delete file
    delete_res = client.delete(f"/files/{file_id}")
    assert delete_res.status_code == 204


def test_document_parser(tmp_path):
    from app.services.document_parser import DocumentParser

    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("FRIDAY AI assistant context", encoding="utf-8")
    assert DocumentParser.parse(txt_file, "text/plain") == "FRIDAY AI assistant context"

    json_file = tmp_path / "sample.json"
    json_file.write_text('{"key": "value"}', encoding="utf-8")
    assert "key" in DocumentParser.parse(json_file, "application/json")


def test_tool_manager():
    from app.tools import tool_manager

    tools_prompt = tool_manager.get_tools_prompt()
    assert "web_search" in tools_prompt


def test_router_agent_vision_detection_and_sanitization():
    from app.agents.router_agent import RouterAgent

    agent = RouterAgent()
    multimodal_messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What is in this diagram?"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,iVBORw0KGgo..."}},
            ],
        }
    ]
    assert agent._contains_images(multimodal_messages) is True

    sanitized = agent._sanitize_for_text_only(multimodal_messages)
    assert "[Attached Image]" in sanitized[0]["content"]


