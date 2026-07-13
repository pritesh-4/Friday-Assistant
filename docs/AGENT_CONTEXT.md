# AGENT_CONTEXT

> **Purpose**: Rapid onboarding for AI coding assistants (Claude, GPT, Gemini, Cursor).
> **Scope**: Project summary, rules, architecture, and current state.
> **Last Updated**: 2026-07-13
> **Related Documents**: [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md), [ARCHITECTURE.md](./ARCHITECTURE.md)

## Quick Summary
You are reading the context file for **FRIDAY**, an advanced, voice-first AI assistant. This document provides everything you need to modify the codebase safely and accurately without scanning the entire repo.

---

## 1. Project Summary
FRIDAY is a decoupled application:
- **Frontend**: React (Vite) utilizing Framer Motion for high-end "Apple x Iron Man" aesthetic fluid animations centered around a responsive "Orb".
- **Backend**: Python (FastAPI) handling API routes, WebSockets for audio, and AI agent routing.

## 2. Current Architecture
- **UI**: State-driven React components. Global state manages the agent's status (`idle`, `listening`, `thinking`, `speaking`).
- **Backend**: A Router Agent pattern evaluates user intent, accesses Memory (via SQLAlchemy DB), and calls LLMs or local Tools.

## 3. Folder Structure
- `/frontend/src/components/`: Reusable UI.
- `/frontend/src/styles/`: Design tokens (Vanilla CSS/Modules). Avoid Tailwind unless explicitly instructed.
- `/backend/app/api/`: FastAPI routes.
- `/backend/app/agents/`: AI logic and tool definitions.
- `/backend/app/services/`: Business logic.

## 4. Coding Standards & Conventions
- **Language**: JS/JSX for frontend. Python (Type-hinted) for backend.
- **CSS**: Strict adherence to the `UI_DESIGN_SYSTEM`. Use glassmorphism, deep space blacks (`#050505`), and cyan glows.
- **Backend**: Use `async`/`await` for all I/O. Validate data heavily with Pydantic.
- **Simplicity**: Do not over-engineer. Write concise code.

## 5. Current MVP Stage (What is built)
- We are currently in **Milestone 1/2**. 
- The foundational architecture is planned, and initial repositories are set up.
- *Refer to [ROADMAP.md](./ROADMAP.md) for exact progress.*

## 6. Features Planned
- Voice input/output via WebSockets.
- SQLite/PostgreSQL memory integration.
- Desktop app wrapper (Electron).

## 7. Features Explicitly Rejected
- Complex dashboard-style UIs (the UI must remain unobtrusive).
- Replacing search engines for simple facts.
- Multi-user authentication (designed as a single-user personal assistant for now).

## 8. How to Safely Modify the Project
- **Frontend UI Changes**: Ensure animations use Framer Motion springs, not linear CSS transitions. Test all 4 Orb states.
- **Backend Changes**: Keep route handlers in `/api/` thin; put logic in `/services/`.
- **Modifying Agents**: Update tool schemas and Pydantic models when changing what the LLM can execute.

## 9. Design Philosophy
- **Aesthetics Matter**: The UI must look premium.
- **Speed**: Minimize Time-To-First-Byte (TTFB) on backend responses.

## 10. Common Pitfalls
- Storing state in the frontend that should be managed by the backend session.
- Blocking the event loop in FastAPI with synchronous code.
- Using heavy filled icons instead of clean, stroked icons.

> [!TIP]
> When asked to implement a new feature, first identify if it requires a UI state change, a new API route, or a new Agent Tool. Modify the respective decoupled components.
