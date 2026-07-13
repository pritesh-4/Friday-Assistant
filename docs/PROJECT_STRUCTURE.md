# PROJECT_STRUCTURE

> **Purpose**: Document every folder in the repository.
> **Scope**: Entire monorepo or split repos.
> **Last Updated**: 2026-07-13
> **Related Documents**: [FRONTEND_ARCHITECTURE.md](./FRONTEND_ARCHITECTURE.md), [BACKEND_ARCHITECTURE.md](./BACKEND_ARCHITECTURE.md)

## Quick Summary
A comprehensive map of the project directory structure.

---

## Root

```text
/
├── frontend/   # The React/Vite web application
├── backend/    # The Python/FastAPI server application
└── docs/       # Project documentation (this folder)
```

## Frontend (`/frontend`)

```text
src/
├── assets/       # Static files (images, sounds, fonts)
├── components/   # Reusable React components (Orb, Cards, Buttons)
├── hooks/        # Custom React hooks (useAudio, useWebSocket)
├── layouts/      # Page wrappers defining structure
├── pages/        # Top-level view components (Home, Settings)
├── services/     # API/WebSocket client logic
├── store/        # State management configuration
├── styles/       # CSS modules, design tokens, global styles
└── utils/        # Helper functions, formatters, constants
```

## Backend (`/backend`)

```text
app/
├── api/          
│   └── routers/  # FastAPI route definitions grouped by domain
├── core/         # Configuration, environment loading, security
├── db/           # Database setup and connection management
├── models/       # SQLAlchemy ORM models (Database schema)
├── schemas/      # Pydantic models (API validation)
├── services/     # Business logic, external API integrations
├── agents/       # AI logic, prompts, orchestrators
│   └── tools/    # Tool definitions executable by the LLM
└── utils/        # Backend helper functions
```
