# AGENT_CONTEXT

> **Purpose**: Rapid onboarding for AI coding assistants (Claude, GPT, Gemini, Cursor).
> **Scope**: Project summary, rules, architecture, and current state.
> **Last Updated**: 2026-08-03
> **Related Documents**: [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md), [ARCHITECTURE.md](./ARCHITECTURE.md)

## Quick Summary
You are reading the context file for **FRIDAY**, an advanced, voice-first AI assistant. This document provides everything you need to modify the codebase safely and accurately without scanning the entire repo.

---

## 1. Project Summary
FRIDAY is a decoupled application:
- **Frontend**: React 19 + Vite 8 utilizing Framer Motion for high-end "Apple x Iron Man" aesthetic fluid animations centered around a responsive, morphing "Orb".
- **Backend**: Python 3.x (FastAPI) handling API routes, WebSockets for duplex voice audio, and AI agent routing.

## 2. Current Architecture
- **UI**: State-driven React components. Global state manages the agent's status (`idle`, `listening`, `thinking`, `speaking`).
- **Backend**: An agentic framework using an **Executive Planner** and **Intent Engine** to route queries. Utilizes a multi-tiered **Cognitive Memory Engine (CME V2)** with background consolidation and a semantic **Knowledge Graph** backed by SQLite and ChromaDB.

## 3. Folder Structure
- `/src`: React frontend components, page views, and context providers directly in the project root.
- `/public`: Static public assets for the frontend.
- `/backend/app/`: FastAPI application code.
  - `agents/`: specialized AI agents and tool routing.
  - `api/`: API router modules (chat, planning, background, settings, voice websocket stream).
  - `identity/`: Entity registry, validation, and alias resolver database.
  - `intent/`: Input classification, heuristics, and risk analysis.
  - `knowledge_graph/`: Nodes, relationships, traversals, and pathfinding.
  - `memory/`: Memory consolidation, conflict resolver, extraction, and vector index.
  - `planning/`: Executive planning, goal decomposition, and DAG execution scheduler.
  - `services/`: Business services (LLM, Voice STT/TTS, background worker).
  - `tools/`: External tool definitions and execution manager.

## 4. Coding Standards & Conventions
- **Language**: JS/JSX for frontend. Python (Type-hinted, PEP 8) for backend.
- **CSS**: Tailwind CSS v4 using the `@tailwindcss/vite` plugin. Declare theme custom extensions (glassmorphism, cyan glows) inside `@theme` in `src/index.css`.
- **Backend**: Use `async`/`await` for all I/O. Validate data strictly with Pydantic v2 schemas. Avoid SQLAlchemy ORM; perform clean async SQLite transactions using the unified custom database utility (`app.db.database`).
- **Simplicity**: Write concise, testable code with clean documentation.

## 5. Current Development Stage (What is built)
- We are currently in **Milestone 4/5**.
- Core Foundations, Router Agent, Cognitive Memory Engine V2, Identity Engine, Knowledge Graph, Background Jobs, and full-duplex WebSocket real-time audio with speculative STT and barge-in are fully implemented and verified via unit tests.
- *Refer to [ROADMAP.md](./ROADMAP.md) for progress details.*

## 6. Features Planned
- Host OS local computer control daemon (executing shell commands, file management).
- Desktop packaging via Electron or Tauri.
- Safe execution sandbox strategy and permission verification overlays.

## 7. Features Explicitly Rejected
- Complex dashboard-style text-heavy layouts (the UI must remain voice-focused and ambient).
- High latency voice responses (everything must stream speculatively to maintain natural interaction flow).

## 8. How to Safely Modify the Project
- **Frontend UI Changes**: Ensure animations use Framer Motion springs. Test the Orb's transitions. Keep custom layouts aligned with Tailwind CSS v4 theme directives.
- **Backend Changes**: Keep route handlers in `/api/routes/` thin; isolate business logic in services or engines.
- **Modifying Agents/Tools**: Declare tool parameter definitions as valid JSON Schemas in `app/tools/` and update registries.

## 9. Design Philosophy
- **Aesthetics Matter**: The UI must look premium (deep blacks `#050505`, subtle glowing highlights, fine text).
- **Speed**: Speculatively stream text/audio chunks. Use background threads for heavy calculations (consolidation, memory indexing).

## 10. Common Pitfalls
- Storing SQLite connection instances across separate processes (use `app.db.database` which is thread-safe and async).
- Blocking the FastAPI event loop with synchronous file writes or synchronous requests.
- Providing Tailwind v3 utility classes or configuration structures that are deprecated in v4.
