# ROADMAP

> **Purpose**: Break down development into clear milestones.
> **Scope**: Project timeline and feature planning.
> **Last Updated**: 2026-07-13
> **Related Documents**: [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md)

## Quick Summary
The FRIDAY development roadmap focuses on establishing a robust text-based MVP first, then layering on voice, memory, and advanced computer control capabilities.

---

## Milestone 1: MVP 1 (Core Foundations) - *Current*
- [ ] Initialize frontend repository (React/Vite).
- [ ] Initialize backend repository (FastAPI).
- [ ] Implement basic Orb UI component with Idle and Thinking states.
- [ ] Create basic `/chat` text endpoint connecting to a single LLM provider.
- [ ] Establish system documentation.

## Milestone 2: MVP 2 (Tooling & Architecture)
- [ ] Implement Router Agent pattern in the backend.
- [ ] Add basic tool calling capabilities (e.g., Time, Weather).
- [ ] Implement UI for ToolExecutionCards.
- [ ] Refine Orb animations.

## Milestone 3: Memory
- [ ] Implement Session (short-term) memory.
- [ ] Integrate a database (SQLite/PostgreSQL) for user data.
- [ ] Implement long-term memory extraction and retrieval (Vector DB).

## Milestone 4: Voice First
- [ ] Integrate Speech-to-Text (STT) provider.
- [ ] Integrate Text-to-Speech (TTS) provider.
- [ ] Implement WebSocket `/ws/audio` route for streaming.
- [ ] Connect Orb states (Listening, Speaking) to live audio streams.

## Milestone 5: Computer Control
- [ ] Develop a local daemon to allow FRIDAY to interact with the host OS.
- [ ] Add tools for file reading, writing, and terminal execution.
- [ ] Implement strict security sandboxing for local actions.

## Milestone 6: Desktop App
- [ ] Package the web frontend into an Electron or Tauri desktop application.
- [ ] Add global keyboard shortcuts to summon FRIDAY from anywhere.
- [ ] Implement transparent/borderless window modes for the Orb.

## Milestone 7: Production
- [ ] Finalize UI/UX polish.
- [ ] Extensive performance optimization and latency reduction.
- [ ] Comprehensive testing suite.
- [ ] Public release / deployment guides.

## Future Vision
- Native iOS/Android companion apps.
- Complete Multi-Agent orchestration.
- Integration with local hardware (e.g., smarthome devices).
- Fully private offline execution via local LLMs.
