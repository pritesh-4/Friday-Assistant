# API_REFERENCE

> **Purpose**: Document all backend API endpoints and WebSockets.
> **Scope**: FastAPI routes.
> **Last Updated**: 2026-08-03
> **Related Documents**: [BACKEND_ARCHITECTURE.md](./BACKEND_ARCHITECTURE.md)

## Quick Summary
Reference for all REST and WebSocket endpoints available on the FRIDAY backend.

---

## 1. System & Diagnostics

### `GET /`
- **Purpose**: Verify the backend is online and fetch basic version specs.

### `GET /health`
- **Purpose**: Basic health probe.
- **Response**: `{ "status": "healthy", "version": "0.1.0", "uptime_seconds": 12.3 }`

### `GET /health/ready`
- **Purpose**: Readiness check for database and core subsystems.

---

## 2. Conversations

### `POST /chat`
- **Purpose**: Send a message to the agent and retrieve a response.
- **Request**:
  ```json
  {
    "message": "Write a note about the new plan",
    "conversation_id": "conv_98765"
  }
  ```
- **Response**: Streams SSE messages or returns:
  ```json
  {
    "reply": "I've saved the note.",
    "conversation_id": "conv_98765"
  }
  ```

---

## 3. Real-Time WebSocket Duplex Voice

### `WebSocket /voice/stream` (Alias: `/api/voice/stream`)
- **Purpose**: Real-time full-duplex conversational voice mode.
- **Authentication**: Optional token-based verification via query parameters: `ws://localhost:8000/voice/stream?token=<secret_key>`.
- **Inbound Data Formats**:
  - **Raw Audio Chunks**: Float32 raw audio binary packages (16kHz sample rate).
  - **Control Commands (JSON)**:
    - `{ "type": "start", "conversation_id": "..." }`
    - `{ "type": "stop" }`
    - `{ "type": "interrupt" }` (Barge-in command to cancel current speaker task)
- **Outbound Event Streams (JSON)**:
  - `{ "type": "session_started" }`
  - `{ "type": "status", "state": "transcribing" | "processing_intent" }`
  - `{ "type": "transcript", "text": "...", "final": false | true }` (Speculative STT streams)
  - `{ "type": "interrupted" }` (Acknowledge barge-in)
  - `{ "type": "done" }` (Finished speaker turn)

---

## 4. Voice Utility endpoints

### `GET /voice`
- **Purpose**: Returns capabilities and status of Whisper (STT) and Kokoro (TTS).

### `GET /voice/health`
- **Purpose**: Detailed engine dependencies and readiness statistics.

### `POST /voice/upload`
- **Purpose**: Upload a voice audio file, validating MIME types and sizes.

### `POST /voice/orchestrate`
- **Purpose**: Synchronously run STT, LLM generation, and TTS for an uploaded audio file.

### `POST /voice/orchestrate/stream`
- **Purpose**: Streams SSE token responses for an uploaded audio file.

### `POST /voice/transcribe`
- **Purpose**: Converts uploaded audio file to text transcription.

### `POST /voice/speak`
- **Purpose**: Synthesizes text to a WAV audio binary.

---

## 5. Planning & Goals

### `GET /planning/goals`
- **Purpose**: Retrieves all structured goals.

### `GET /planning/goals/{goal_id}`
- **Purpose**: Returns the target goal along with its Milestones and Task DAG dependencies.

### `POST /planning/goals`
- **Purpose**: Manually creates a new goal structure and evaluates immediate tasks.

### `PATCH /planning/tasks/{task_id}/status`
- **Purpose**: Update a task status (e.g. "pending", "in_progress", "completed") and recalculate DAG scheduling.

---

## 6. Background Jobs & Notifications

### `GET /background/jobs`
- **Purpose**: List queued and processing asynchronous jobs.

### `POST /background/jobs`
- **Purpose**: Enqueue a new long-running job.

### `GET /background/notifications`
- **Purpose**: List system notifications.

### `PATCH /background/notifications/{notif_id}/read`
- **Purpose**: Acknowledge and clear a notification.
