# ROADMAP

> **Purpose**: Break down development into clear milestones.
> **Scope**: Project timeline and feature planning.
> **Last Updated**: 2026-08-03
> **Related Documents**: [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md)

## Quick Summary
The FRIDAY development roadmap details completed features and lists target milestones for local desktop integration and production scaling.

---

## Milestone 1: MVP 1 (Core Foundations) - **[COMPLETE]**
- [x] Initialize frontend repository (React/Vite).
- [x] Initialize backend repository (FastAPI).
- [x] Implement basic Orb UI component with Idle and Thinking states.
- [x] Create basic `/chat` text endpoint connecting to a single LLM provider.
- [x] Establish system documentation.

## Milestone 2: MVP 2 (Tooling & Architecture) - **[COMPLETE]**
- [x] Implement Router Agent pattern in the backend.
- [x] Add basic tool calling capabilities (e.g., Web Search).
- [x] Implement UI for ChatMessage and sidebar pages (Notes, Tasks).
- [x] Refine Orb animations (Speaking, Listening, Idle, Thinking).

## Milestone 3: Memory - **[COMPLETE]**
- [x] Implement Session (short-term) memory.
- [x] Integrate SQLite database for persistent user data (milestones, tasks, notes).
- [x] Implement long-term cognitive memory (CME V2) extraction, consolidation, and conflict resolution.
- [x] Integrate ChromaDB vector store for semantic memory indexing.
- [x] Implement semantic Knowledge Graph (nodes, edges, BFS traversals, path explanation).

## Milestone 4: Voice First - **[COMPLETE]**
- [x] Integrate Speech-to-Text (STT) model loader (Faster-Whisper).
- [x] Integrate Text-to-Speech (TTS) voice generator (Kokoro-ONNX).
- [x] Implement full-duplex WebSocket `/voice/stream` route for real-time bidirectional audio.
- [x] Implement speculative STT and speculative memory prefetching.
- [x] Connect Orb states (Listening, Speaking, Processing) to live WebSocket status frames.
- [x] Implement real-time user interruption barge-in detection and instant task cancellation.

---

## Milestone 5: Computer Control - *Current*
- [ ] Develop a local daemon/agent to allow FRIDAY to interact with the host OS.
- [ ] Add tools for folder searching, file modifications, and local terminal script runs.
- [ ] Implement strict security sandboxing, containerizations, and permission verification overlays.

## Milestone 6: Desktop App - *Next*
- [ ] Package the React frontend into an Electron or Tauri desktop application wrapper.
- [ ] Add global OS-level hotkeys to summond/hide the Orb from anywhere.
- [ ] Implement borderless and transparent overlays for visual integration on desktop.

## Milestone 7: Production & Scaling
- [ ] Implement user authentication schemas (JWT authentication) for multi-tenant support.
- [ ] Performance optimizations, latency reduction, and model caching.
- [ ] Expand automated test coverages.
