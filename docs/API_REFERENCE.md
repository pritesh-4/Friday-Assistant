# API_REFERENCE

> **Purpose**: Document all backend API endpoints and WebSockets.
> **Scope**: FastAPI routes.
> **Last Updated**: 2026-07-13
> **Related Documents**: [BACKEND_ARCHITECTURE.md](./BACKEND_ARCHITECTURE.md)

## Quick Summary
Reference for all REST and WebSocket endpoints available on the FRIDAY backend.

---

## System

### `GET /health`
**Purpose**: Basic health check to ensure the backend is running.
**Response**: 
```json
{ "status": "ok", "version": "0.1.0" }
```
**Future Changes**: Add database and LLM provider connectivity checks.

---

## Conversation

### `POST /chat`
**Purpose**: Send a text message to the agent and receive a text response.
**Request**:
```json
{ "message": "What is my schedule today?", "session_id": "12345" }
```
**Response**:
```json
{ "reply": "You have a meeting at 3 PM.", "tools_used": ["calendar"] }
```

### `WebSocket /ws/audio`
**Purpose**: Bidirectional streaming of audio data.
**Flow**:
1. Client connects and streams binary audio (PCM/Opus).
2. Server processes audio via STT (Speech-to-Text).
3. Server routes text to Agent.
4. Server generates TTS (Text-to-Speech) audio and streams it back to client.
5. Server sends control messages (e.g., `state: thinking`, `state: speaking`) via JSON over the same socket.
**Future Changes**: Implement WebRTC for lower latency.

---

## Memory

### `GET /memory/{session_id}`
**Purpose**: Retrieve the context or summary of a specific session.
**Response**: Array of message objects or a generated summary string.

### `DELETE /memory/{session_id}`
**Purpose**: Clear the memory for a specific session.
**Response**: `200 OK`

---

## Settings

### `GET /settings/providers`
**Purpose**: List available LLM providers (OpenAI, Anthropic, Local).
**Response**:
```json
{
  "providers": ["openai", "anthropic", "ollama"],
  "active": "openai"
}
```

---

## Workspace

### `GET /notes` and `POST /notes`
**Purpose**: Retrieve and create workspace notes for persistent context.

### `GET /tasks`, `POST /tasks`, `PATCH /tasks/{id}`
**Purpose**: Manage actionable items and to-do lists within the workspace.
