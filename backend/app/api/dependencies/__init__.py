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

from app.memory.memory_manager import MemoryManager, memory_manager
from app.services.chat_service import ChatService
from app.services.file_service import FileService
from app.services.memory_service import MemoryService
from app.services.settings_service import SettingsService
from app.services.voice_service import VoiceService
from app.services.voice.transcription_service import TranscriptionService
from app.services.workspace_service import WorkspaceService

from app.services.voice.speech_service import SpeechService

# ── Singleton instances ────────────────────────────────────────────────────────
# Created once at module load time and reused across all requests.
# These are module-level singletons — not class attributes — so they remain
# injectable and replaceable in tests via dependency_overrides.

_chat_service = ChatService()
_memory_service = MemoryService()
_workspace_service = WorkspaceService()
_settings_service = SettingsService()
_file_service = FileService()
_voice_service = VoiceService()
_transcription_service = TranscriptionService()
_speech_service = SpeechService()


# ── Provider functions ─────────────────────────────────────────────────────────

def get_chat_service() -> ChatService:
    """Provide the shared ChatService instance."""
    return _chat_service


def get_memory_service() -> MemoryService:
    """Provide the shared MemoryService instance."""
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
    return _voice_service


def get_transcription_service() -> TranscriptionService:
    """Provide the shared TranscriptionService instance."""
    return _transcription_service

def get_speech_service() -> SpeechService:
    """Provide the shared SpeechService instance."""
    return _speech_service


def get_memory_manager() -> MemoryManager:
    """
    Provide the shared MemoryManager instance.

    The memory manager holds all in-process session contexts and coordinates
    between short-term session state and the long-term memory service.
    """
    return memory_manager
