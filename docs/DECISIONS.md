# DECISIONS

> **Purpose**: Maintain an Architecture Decision Record (ADR).
> **Scope**: Major technical choices and their rationales.
> **Last Updated**: 2026-07-13
> **Related Documents**: [ARCHITECTURE.md](./ARCHITECTURE.md)

## Quick Summary
A log of significant architectural and technical decisions made during the development of FRIDAY.

---

## 1. Why React for the Frontend?
**Decision**: Use React (Vite) for the web UI.
**Rationale**: React's ecosystem for fluid animations (Framer Motion) and its component-based architecture perfectly align with the goal of creating a dynamic, state-driven UI (The Orb).

## 2. Why FastAPI for the Backend?
**Decision**: Use FastAPI over Flask or Django or Node/Express.
**Rationale**: 
- High performance (async support).
- Native WebSocket support for audio streaming.
- Automatic Pydantic validation and Swagger UI generation.
- Python is the dominant ecosystem for AI/LLM integration (LangChain, LlamaIndex, OpenAI SDK).

## 3. Why Not Tailwind? (Or Why Vanilla CSS/Modules?)
**Decision**: Prefer Vanilla CSS / CSS Modules with a strict design token system.
**Rationale**: FRIDAY relies heavily on complex glassmorphism, precise drop shadows, and spring physics. While Tailwind is fast for standard layouts, the highly custom, premium aesthetic of FRIDAY (Apple × Iron Man) requires deep, specific CSS tuning that becomes unwieldy in utility classes.

## 4. Why Voice First?
**Decision**: Optimize for audio over text.
**Rationale**: True assistant immersion requires hands-free interaction. Text is a fallback. The UI is designed around auditory states (Listening, Speaking) rather than a chat box.

## 5. Why a Router Agent?
**Decision**: Use a router pattern rather than a single massive LLM prompt.
**Rationale**: Splitting tasks (e.g., determining intent vs executing a search) saves tokens, reduces latency, and allows us to use smaller, faster models for simple tasks and heavy models only when necessary.

## 6. Why Not Electron Yet?
**Decision**: Launch as a web app first.
**Rationale**: Speed to MVP. Electron adds packaging complexity. The web app can be wrapped in Electron or Tauri in Milestone 6 once the core architecture is stable.
