# BACKEND_ARCHITECTURE

> **Purpose**: Explain the backend structure, routing, services, and data models.
> **Scope**: Server-side application (FastAPI).
> **Last Updated**: 2026-08-03
> **Related Documents**: [ARCHITECTURE.md](./ARCHITECTURE.md), [AI_ARCHITECTURE.md](./AI_ARCHITECTURE.md)

## Quick Summary
The backend is a high-performance Python application built with FastAPI. It coordinates API endpoints, manages long-term memory structures, executes task scheduler queues, and handles full-duplex WebSocket connections for voice interactions.

## Folder Structure

```text
app/
├── agents/       # AI logic (RouterAgent, base classes, WebResearchAgent)
├── api/          # Route controller endpoint definitions (chat, voice, planning, etc.)
├── core/         # Config variables, logging setting, rate limiter setup
├── db/           # sqlite thread-safe database connector, schema initialization scripts
├── identity/     # Entity registry resolver, validators, aliases records
├── intent/       # Intent classification engine, safety risks analyses
├── knowledge_graph/# Semantic entity relationship node/edge traversals
├── memory/       # CME V2 consolidator and conflict resolver
├── planning/     # Executive planner mission strategies, Goal DAG models
├── ranking/      # Context score rankers for memories
├── schemas/      # Pydantic v2 schemas for endpoint validation
├── services/     # Core services (LLMProviders, STT/TTS engine loading, background worker)
├── storage/      # Memory repository abstraction layers
├── tools/        # Extensible agent tools (web search, calculator, shell executor)
└── utils/        # General backend helper utilities
```

## Core Infrastructure Components

### 1. Unified SQLite & Vector Storage
- **SQLite Database (`app/db/database.py`)**: Uses a single, shared, thread-safe asynchronous sqlite interface (`Database`) for CRUD queries, avoiding SQLAlchemy ORM overhead. It initializes DB schemas dynamically on startup.
- **ChromaDB (`app/db/vector_store.py`)**: Handles embedding indexing and semantic similarities retrieval across cognitive memories and canonical graph entities.

### 2. Async Background Worker & Scheduler
- **Background Worker (`app/services/worker.py`)**: A queue-based background task runner spawned on lifespan startup that handles long-running jobs asynchronously.
- **Execution Scheduler (`app/agents/scheduler.py`)**: Evaluates dependent execution steps in goal-milestone DAGs, unblocking and triggering parallel tasks.

### 3. Voice Pipelines
- **STT (Speech-to-Text)**: Powered by `faster-whisper` (`distil-large-v3`).
- **TTS (Text-to-Speech)**: Powered by `kokoro-onnx` using an ONNX runtime.
- **Lazy Engine Loaders**: Large models are downloaded during the build phase and loaded into memory on the first STT/TTS request to prevent startup timeouts on deployment environments (e.g. Render).
- **WebSocket Streaming (`app/api/routes/voice.py`)**: Handles full-duplex streams. The reader gathers float32 audio buffers, the speculative loop runs STT every 800ms, and the generator streams LLM token events and synthesized TTS bytes, with immediate task-cancellation on user interruption (barge-in).

## Coding Standards & Conventions
- **Async I/O**: Direct async SQLite queries, async HTTP calls, and WebSocket loops are mandatory.
- **Strict Validation**: All API endpoints must declare type-hinted Pydantic v2 schemas.
- **Thin Routers**: Isolate endpoint logic to routers. Complex transactions and business calculations belong in services or subsystem engines.
