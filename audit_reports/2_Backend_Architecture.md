# 2. Backend Architecture

## System Design
The backend is a monolithic FastAPI application written in Python 3.11, structured heavily around dependency injection and a multi-layered service architecture.

## Component Breakdown

1. **API Layer (pp/api/)**:
   - \chat.py\: SSE streaming orchestrator for LLM generation.
   - \oice.py\: Audio ingestion, VAD state orchestration, and Whisper inference.
   - \memory.py\: Endpoints for fetching/managing user memories.
   - \planning.py\ & \ackground.py\: Task tracking and background execution triggers.

2. **Core (pp/core/)**:
   - Contains \config.py\ for pydantic \BaseSettings\ management.
   - \logging.py\ and \middleware.py\ implement structured JSON-like logs injected with contextvars (\equest_id\, \conversation_id\).
   - \ate_limit.py\ uses \slowapi\ to guard heavy inference endpoints.

3. **Services Layer (pp/services/)**:
   - \llm_service.py\: High-level wrapper over providers.
   - \streaming_coordinator.py\: Thread-safe async iterators ensuring no broken generator crashes during network disconnects.
   - \memory_service.py\: Core memory synthesis logic, deduplication, and decay tracking.

4. **Agents & Tools (pp/agents/, \pp/tools/\)**:
   - Extensible tool registry. Implements permission boundaries (\SAFE\, \DESTRUCTIVE\).

## Technical Debt & Findings
- **Error Handling**: Standardized to \ErrorResponse\ schema across all handlers.
- **Background Tasks**: Handled by asyncio queues instead of robust Redis/Celery queues. This limits horizontal scalability, though it satisfies V1.0 requirements.
- **Provider Redundancy**: Providers share a base class, but exception wrapping needs to be verified for unified timeout handling.
