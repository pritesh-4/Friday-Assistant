"""
FastAPI dependency providers for the FRIDAY backend.

All service and manager instances are created here and exposed as FastAPI
``Depends``-compatible callables.  This gives us:

- **Testability**: Tests can override any dependency via ``app.dependency_overrides``.
- **Singleton control**: Services share database access through the global ``database``
  singleton without re-instantiating on every request.
- **Loose coupling**: Routes import *providers*, never concrete service classes.

Usage in a route:
    from fastapi import Depends
    from app.api.dependencies import get_memory_service
    from app.services.memory_service import MemoryService

    @router.get("")
    async def list_memories(service: MemoryService = Depends(get_memory_service)):
        ...
"""

from app.memory import MemoryManager, memory_manager, CognitiveMemoryService
from app.services.chat_service import ChatService
from app.services.file_service import FileService
from app.services.settings_service import SettingsService
from app.services.streaming_coordinator import StreamingCoordinator
from app.services.voice.speech_service import SpeechService
from app.services.voice.transcription_service import TranscriptionService
from app.services.voice.orchestrator import VoiceOrchestrator
from app.services.voice_service import VoiceService
from app.services.workspace_service import WorkspaceService
from app.services.llm_service import LLMService
from app.tools.manager import ToolManager
from app.agents.agent_manager import AgentManager
from app.agents.scheduler import ExecutionScheduler

# ── Singleton instances ────────────────────────────────────────────────────────
# Created once at module load time and reused across all requests.
# These are module-level singletons — not class attributes — so they remain
# injectable and replaceable in tests via dependency_overrides.

_chat_service = ChatService()
_memory_service = CognitiveMemoryService()
_workspace_service = WorkspaceService()
_settings_service = SettingsService()
_file_service = FileService()
_streaming_coordinator = StreamingCoordinator()

_voice_service: VoiceService | None = None
_transcription_service: TranscriptionService | None = None
_speech_service: SpeechService | None = None
_voice_orchestrator: VoiceOrchestrator | None = None

_llm_service = LLMService()
_tool_manager = ToolManager()
_agent_manager = AgentManager(_llm_service, _tool_manager)
_scheduler = ExecutionScheduler(_agent_manager)


# ── Provider functions ─────────────────────────────────────────────────────────


def get_chat_service() -> ChatService:
    """Provide the shared ChatService instance."""
    return _chat_service


def get_memory_service() -> CognitiveMemoryService:
    """Provide the shared CognitiveMemoryService instance."""
    return _memory_service


def get_workspace_service() -> WorkspaceService:
    """Provide the shared WorkspaceService instance."""
    return _workspace_service


def get_settings_service() -> SettingsService:
    """Provide the shared SettingsService instance."""
    return _settings_service


def get_file_service() -> FileService:
    """Provide the shared FileService instance."""
    return _file_service


def get_voice_service() -> VoiceService:
    """Provide the shared VoiceService instance."""
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService()
    return _voice_service


def get_transcription_service() -> TranscriptionService:
    """Provide the shared TranscriptionService instance."""
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = TranscriptionService()
    return _transcription_service


def get_speech_service() -> SpeechService:
    """Provide the shared SpeechService instance."""
    global _speech_service
    if _speech_service is None:
        _speech_service = SpeechService()
    return _speech_service


def get_voice_orchestrator() -> VoiceOrchestrator:
    """Provide the shared VoiceOrchestrator instance."""
    global _voice_orchestrator
    if _voice_orchestrator is None:
        _voice_orchestrator = VoiceOrchestrator()
    return _voice_orchestrator


def get_streaming_coordinator() -> StreamingCoordinator:
    """Provide the shared StreamingCoordinator instance."""
    return _streaming_coordinator


def get_memory_manager() -> MemoryManager:
    """
    Provide the shared MemoryManager instance.

    The memory manager holds all in-process session contexts and coordinates
    between short-term session state and the long-term memory service.
    """
    return memory_manager


def get_llm_service() -> LLMService:
    """Provide the shared LLMService instance."""
    return _llm_service


def get_tool_manager() -> ToolManager:
    """Provide the shared ToolManager instance."""
    return _tool_manager


def get_agent_manager() -> AgentManager:
    """Provide the shared AgentManager instance."""
    return _agent_manager


def get_scheduler() -> ExecutionScheduler:
    """Provide the shared ExecutionScheduler instance."""
    return _scheduler
