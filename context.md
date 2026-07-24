# Project Context & State: F.R.I.D.A.Y.

This file gives a concise, high-level summary of the **F.R.I.D.A.Y.** codebase architecture, the current implementation state, and the next development steps. It is intended to save context for future assistants.

---

## Project Overview & Tech Stack

F.R.I.D.A.Y. is a prototype voice-first personal AI operating companion.

* **Frontend**: React 19 + Vite 8 + React Router DOM v7 for SPA routing.
    * Styling and animations: Tailwind CSS v4, Framer Motion.
    * Graphics: HTML5 Canvas and WebGL custom fragment shaders.
* **Backend**: FastAPI (Python 3.x) + Uvicorn + Pydantic v2 validation.

---

## Codebase Architecture Map

* **`/src`** (React frontend)
    * `pages/`: Views for `Home` (landing page with the active F.R.I.D.A.Y. orb), `Chat` (interactive workspace), `Vision` (roadmap details), and `About` (inspiration and boundaries).
    * `components/`:
        * [`Orb.jsx`](src/components/Orb.jsx): Interactive central component that morphs between the `idle`, `listening`, `processing`, and `speaking` states.
        * [`ShaderBackground.jsx`](src/components/ShaderBackground.jsx): Canvas-based shader background that renders a digital matrix grid.
        * `ChatWindow.jsx`, `ChatMessage.jsx`, `ChatInput.jsx`, `Sidebar.jsx`: Chat dashboard layout components.
    * `services/`: Core logic helpers such as `chatService.js`, `notesService.js`, `tasksService.js`, `voiceService.js`, and `settingsService.js`.
    * `data/`: Mock data storage that matches the expected API schemas.
* **`/backend`** (FastAPI)
    * `app/main.py`: Application startup, CORS configuration, and router mounting.
    * `app/api/routes/`: API endpoint modules for chat, files, health, memory, settings, and voice.
    * `app/agents/`: AI agents for memory, routing, and task execution.
    * `app/services/`: Core logic for LLM interaction, memory, files, and voice processing.
    * `app/core/`: Configuration, logging, and security setup.
    * `app/db/`: Database configuration and initialization.
    * `app/schemas/`: Pydantic models grouped into chat, common, and memory schemas.

---

## Current Implementation State

> [!NOTE]
> The application is a **fully functional integrated system** with frontend and backend connected.

### 1. Frontend State
* **State**: Complete React SPA with responsive routing, animated components (Framer Motion), custom WebGL shaders, and a unified `VoiceOverlay` for full-screen voice interaction.
* **Services**: Frontend services (`src/services/*.js`) now make real HTTP requests to the backend (`API_BASE_URL`) via `fetch`.
* **Voice**: Fully integrated with a deterministic `VoiceStateMachine` managing microphone recording, transcription, LLM processing, and TTS playback in a unified, race-condition-free pipeline.

### 2. Backend State
* **Persistence**: SQLite database is fully implemented and connected for storing conversations, messages, memories, notes, and tasks.
* **LLM / AI**: Dynamic provider routing supports Groq, Gemini, OpenRouter, and Nvidia. Includes fallback chains and system prompt injection.
* **Voice Services**: Integrated with Faster-Whisper (STT) and Kokoro-ONNX (TTS). Models are lazily loaded into memory in a thread-safe manner to support production deployments (e.g., Render) without startup timeouts. Models are downloaded during the build phase via `scripts/download_models.py`.
* **Deployment**: Configured for Render via `render.yaml` with production-grade MIME validation and environment variables.

---

## Recommended Roadmap for Future Work

When continuing development on F.R.I.D.A.Y., focus on the following milestones:

1. **Real-time Streaming**:
    * Upgrade the HTTP `/voice/transcribe` and LLM endpoints to use WebSockets for real-time streaming of speech-to-text and text-to-speech to reduce latency.
2. **Authentication & Multi-User**:
    * Implement JWT-based authentication so multiple users can have their own isolated workspaces, conversations, and memories.
3. **Advanced RAG / Vector Memory**:
    * Upgrade the current relational memory system to a true Vector Store (e.g., Qdrant or Pinecone) for semantic similarity search across past conversations.
4. **Voice Activity Detection (VAD)**:
    * Replace the current hardcoded silence timeout with Web Audio API energy detection (or a lightweight WebAssembly VAD) for more natural conversation interruption and end-of-speech detection.

## Extra Notes

* Keep this document short and factual so it stays useful as a handoff note.
* Update the architecture map whenever a new major feature, route, service, or backend module is added.
* Deployment configuration is managed centrally in `render.yaml`.
