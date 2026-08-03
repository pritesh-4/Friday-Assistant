# Project Context & State: F.R.I.D.A.Y.

This file gives a concise, high-level summary of the **F.R.I.D.A.Y.** codebase architecture, the current implementation state, and the next development steps. It is intended to save context for future assistants.

---

## Project Overview & Tech Stack

F.R.I.D.A.Y. is a prototype voice-first personal AI operating companion.

* **Frontend**: React 19 + Vite 8 + React Router DOM v7 for SPA routing.
    * Styling and animations: Tailwind CSS v4, Framer Motion.
    * Graphics: HTML5 Canvas and WebGL custom fragment shaders.
* **Backend**: FastAPI (Python 3.x) + Uvicorn + Pydantic v2 validation.
    * Database: SQLite database for relational storage + ChromaDB vector store for semantic memory context.

---

## Codebase Architecture Map

* **`/src`** (React frontend in project root)
    * `pages/`: Views for `Home` (landing page with the active F.R.I.D.A.Y. orb), `Chat` (interactive workspace), `Vision` (roadmap details), and `About` (inspiration and boundaries).
    * `components/`: Reusable components: [`Orb.jsx`](src/components/Orb.jsx) (morphing states), [`ShaderBackground.jsx`](src/components/ShaderBackground.jsx), `ChatWindow.jsx`, `ChatMessage.jsx`, `ChatInput.jsx`, `Sidebar.jsx`.
    * `services/`: Core logic communication helpers (`chatService.js`, `notesService.js`, `tasksService.js`, `voiceService.js`, and `settingsService.js`).
* **`/backend`** (FastAPI in backend subfolder)
    * `app/main.py`: Application startup, CORS configuration, background worker initialization, scheduler triggers, and WebSocket route mounting.
    * `app/api/routes/`: API endpoint modules for chat, files, health, memory, settings, voice (and WebSocket duplex stream), planning, and background jobs.
    * `app/agents/`: AI agents including `RouterAgent`, `PlannerAgent`, `MemoryAgent`, and specialized tool-calling agents (`WebResearchAgent`).
    * `app/identity/`: Entity Registry & Resolution Engine (disambiguation, validation, confidence scores, alias repository, user profiles).
    * `app/intent/`: Intent Engine (classifier, prompt injection, risk analyzer, goal extractor).
    * `app/knowledge_graph/`: Knowledge Graph Engine (directed relationship links, shortest path, BFS traversals, transit reasoning, explainable paths).
    * `app/memory/`: Cognitive Memory Engine V2 (multi-tier memory manager, autonomous consolidator, conflict resolver).
    * `app/planning/`: Executive Planner (mission plan generation, structured goals, milestones and task DAGs).
    * `app/ranking/`: Scorer and ranking algorithms for memory retrieval.
    * `app/tools/`: Tool registration (`executor.py`, `registry.py`, `web_research.py`).
    * `app/services/`: Core services (LLM providers gateway, voice, jobs, notifications).

---

## Current Implementation State

> [!NOTE]
> The application is a **fully functional integrated system** with frontend and backend connected.

### 1. Frontend State
* **State**: Complete React SPA with responsive routing, animated components (Framer Motion), custom WebGL shaders, and a unified `VoiceOverlay` for full-screen voice interaction.
* **Services**: Frontend services make real HTTP requests to the backend (`API_BASE_URL`) via `fetch`.
* **Voice**: Fully integrated with a deterministic `VoiceStateMachine` managing microphone recording, transcription, LLM processing, and TTS playback.

### 2. Backend State
* **Persistence**: SQLite database is fully connected for storing conversations, messages, milestones, tasks, notes, and background job details.
* **Memory & Graph**: Fully functioning Cognitive Memory Engine (CME V2) and Knowledge Graph (KG) with automated background consolidation, conflict resolution, entity resolution, and hybrid ChromaDB search.
* **LLM / AI**: Dynamic provider routing supports Groq, Gemini, OpenRouter, and Nvidia. Falling back safely and injecting context dynamically.
* **Voice Services**: Integrated with Faster-Whisper (STT) and Kokoro-ONNX (TTS).
* **Duplex Streaming**: Full-duplex WebSocket route `/stream` supports raw audio uploads, speculative rolling transcription every 800ms, speculative memory prefetching, text generation streaming, and immediate barge-in interruption.
* **Background Worker**: Queue-based background workers run tasks and scheduler evaluations, sending job status updates and notifications.

---

## Recommended Roadmap for Future Work

When continuing development on F.R.I.D.A.Y., focus on the following milestones:

1. **Computer Control & Local Daemon**:
    * Develop a lightweight local daemon allowing FRIDAY to read files, run terminal commands, and control window setups on the host machine.
2. **Desktop App Packaging**:
    * Wrap the frontend using Electron or Tauri to allow desktop integrations like global keyboard shortcuts.
3. **Advanced Security Sandboxing**:
    * Implement safe execution restrictions and permission confirmations for local shell tool executions.
4. **Authentication & Multi-User Support**:
    * Migrate schemas and implement JWT authentication if deploying in a shared environment.

## Extra Notes

* Keep this document short and factual so it stays useful as a handoff note.
* Update the architecture map whenever a new major package, route, or service is added.
