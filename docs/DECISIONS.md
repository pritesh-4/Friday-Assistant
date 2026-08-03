# DECISIONS

> **Purpose**: Maintain an Architecture Decision Record (ADR).
> **Scope**: Major technical choices and their rationales.
> **Last Updated**: 2026-08-03
> **Related Documents**: [ARCHITECTURE.md](./ARCHITECTURE.md)

## Quick Summary
A log of significant architectural and technical decisions made during the development of FRIDAY.

---

## 1. Why React for the Frontend?
- **Decision**: Use React 19 (Vite 8) for the web UI.
- **Rationale**: React's ecosystem for fluid animations (Framer Motion) and its component-based architecture perfectly align with the goal of creating a dynamic, state-driven UI (The Orb).

## 2. Why FastAPI for the Backend?
- **Decision**: Use FastAPI over Flask, Django, or Express.
- **Rationale**: 
  - High performance (asynchronous event loop).
  - Native WebSocket support for raw audio streaming.
  - Automatic Pydantic validation and Swagger UI generation.
  - Python is the dominant ecosystem for AI/LLM integration.

## 3. Adoption of Tailwind CSS v4
- **Decision**: Adopt Tailwind CSS v4 as the styling engine, integrated via the `@tailwindcss/vite` compiler.
- **Rationale**: Tailwind CSS v4 provides exceptional performance and compilation speeds. Combining utility class structure with custom theme directives (e.g. glassmorphic borders, glowing pointers) declared via `@theme` in `src/index.css` offers a robust balance between rapid layouts and fine-grained visual details.

## 4. Why Voice First?
- **Decision**: Optimize for audio stream interfaces.
- **Rationale**: Conversational realism is enhanced by speech. Text is a fallback. The UI is centered around auditory states (Listening, Processing, Speaking, Idle).

## 5. Why a Router Agent & Executive Planner?
- **Decision**: Use an Executive Planner to generate subtask DAGs and route to agents, rather than a single monolithic prompt.
- **Rationale**: Separates tasks (classifying intent, planning, tool usage, final summary), which reduces prompt size, optimizes latency, and lets us use cheaper/faster LLM providers for simple tasks.

## 6. Web App Launch Before Electron
- **Decision**: Build and launch a web SPA first.
- **Rationale**: Speeds up architecture stability. Packaging into Electron or Tauri is deferred to Milestone 6 once APIs and streaming states are fully verified.

## 7. Thread-Safe Direct SQLite Access
- **Decision**: Use a custom async sqlite wrapper (`app.db.database`) for raw SQL transactions instead of SQLAlchemy ORM.
- **Rationale**: Minimizes CPU overhead and thread blocks in FastAPI, ensuring that voice processing and streaming database accesses happen with sub-millisecond latencies.

## 8. Multi-Layer Memory (CME V2) + Semantic Knowledge Graph
- **Decision**: Implement a multi-layered Cognitive Memory Engine (CME V2) paired with a semantic Knowledge Graph.
- **Rationale**: Separates immediate details (working memory) from persistent similarity records (ChromaDB vectors) and relational links (graph nodes/edges), giving FRIDAY a rich, human-like contextual reasoning ability.
