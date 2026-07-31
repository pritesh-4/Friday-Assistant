import pytest
import shutil
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

from app.core.config import settings
from app.db.database import database
from app.db.vector_store import vector_store
from app.memory.storage import MemoryStorage
from app.memory.identity import IdentitySystem
from app.memory.entity_resolution import EntityResolutionSystem
from app.memory.knowledge_graph import KnowledgeGraphSystem
from app.memory.ranking import MemoryRanker
from app.memory.retrieval import MemoryRetrievalOrchestrator
from app.memory.memory_extractor import AMISMemeoryExtractor


@pytest.fixture(autouse=True)
async def setup_test_db(tmp_path: Path):
    """Isolate database path and run all migrations."""
    db_file = tmp_path / "friday-memory-test.db"
    database.configure(f"sqlite:///{db_file.as_posix()}")
    await database.initialize()
    
    # Mock vector_store methods to avoid disk/network ops in basic tests
    vector_store.add_memory = AsyncMock(return_value=None)
    vector_store.update_memory = AsyncMock(return_value=None)
    vector_store.delete_memory = AsyncMock(return_value=None)
    vector_store.search = AsyncMock(return_value=[])

    yield

    # Cleanup database connection
    try:
        # SQLite connection is synchronous under the hood, but in-process pool
        pass
    except Exception:
        pass


@pytest.fixture
def storage():
    return MemoryStorage()


@pytest.fixture
def identity_system(storage):
    return IdentitySystem(storage)


@pytest.fixture
def entity_resolution(storage, identity_system):
    return EntityResolutionSystem(storage, identity_system)


@pytest.fixture
def knowledge_graph(storage):
    return KnowledgeGraphSystem(storage)


@pytest.fixture
def ranker():
    return MemoryRanker()


@pytest.fixture
def retrieval(storage, knowledge_graph, ranker):
    return MemoryRetrievalOrchestrator(storage, knowledge_graph, ranker)
