# BACKEND_ARCHITECTURE

> **Purpose**: Explain the backend structure, routing, services, and data models.
> **Scope**: Server-side application (FastAPI).
> **Last Updated**: 2026-07-13
> **Related Documents**: [ARCHITECTURE.md](./ARCHITECTURE.md), [AI_ARCHITECTURE.md](./AI_ARCHITECTURE.md)

## Quick Summary
The backend is a high-performance Python application built with FastAPI. It serves as the bridge between the client UI, the AI reasoning layer, and long-term memory storage.

## Folder Structure

```text
app/
├── api/          # Route definitions (endpoints, websockets)
├── core/         # Config, security, and global app settings
├── db/           # Database connections and migrations
├── models/       # ORM models (SQLAlchemy)
├── schemas/      # Pydantic models for validation / serialization
├── services/     # Business logic (e.g., user management, audio processing)
├── agents/       # AI logic, prompts, tool definitions, and routing
└── utils/        # Shared helper functions
```

## Core Components

### API Routes (`app/api/`)
Endpoints are strictly separated by domain.
- `routers/chat.py`
- `routers/memory.py`
- `routers/audio.py`

### Services (`app/services/`)
Decouples business logic from HTTP transport.
- Keep route handlers thin. All complex data manipulation happens here.

### Agents (`app/agents/`)
Houses the AI orchestration logic. Connects to `services/` when a tool requires internal data.

### Schemas and Models
- **Schemas (`app/schemas/`)**: Pydantic models define what data goes in and out of the API.
- **Models (`app/models/`)**: SQLAlchemy models define the database structure.

## Future Scalability
- **Async First**: All I/O bound operations (DB, LLM calls) must be `async`.
- **Statelessness**: REST APIs remain stateless; session states are stored in Redis or DB.
- **Worker Queues**: Heavy background tasks (e.g., long document processing) will be offloaded to Celery or RQ workers.
