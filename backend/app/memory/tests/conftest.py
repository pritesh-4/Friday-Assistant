import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

from app.core.config import settings
from app.db.database import database
from app.db.vector_store import vector_store

# CME V2 imports
from app.storage.repository import MemoryRepository
from app.identity.registry import IdentityRegistry
from app.identity.resolver import IdentityResolver
from app.knowledge_graph.graph import KnowledgeGraph
from app.knowledge_graph.traversal import GraphTraversal
from app.ranking.ranker import MemoryRanker
from app.memory.scorer import ImportanceScorer
from app.memory.conflict_resolver import ConflictResolver
from app.memory.consolidator import MemoryConsolidator
from app.memory.retrieval import MemoryRetrieval


@pytest.fixture(autouse=True)
async def setup_test_db(tmp_path: Path):
    """Isolate database path and run migrations."""
    db_file = tmp_path / "friday-cme-test.db"
    database.configure(f"sqlite:///{db_file.as_posix()}")
    await database.initialize()
    
    # Mock vector_store methods
    vector_store.add_memory = AsyncMock(return_value=None)
    vector_store.update_memory = AsyncMock(return_value=None)
    vector_store.delete_memory = AsyncMock(return_value=None)
    vector_store.search = AsyncMock(return_value=[])

    yield


@pytest.fixture
def repository():
    return MemoryRepository(database, vector_store)


@pytest.fixture
def registry(repository):
    return IdentityRegistry(repository)


@pytest.fixture
def resolver(registry, repository):
    return IdentityResolver(registry, repository)


@pytest.fixture
def graph(repository):
    return KnowledgeGraph(repository)


@pytest.fixture
def traversal(graph, repository):
    return GraphTraversal(graph, repository)


@pytest.fixture
def ranker():
    return MemoryRanker()


@pytest.fixture
def scorer():
    return ImportanceScorer()


@pytest.fixture
def conflict_resolver(repository):
    return ConflictResolver(repository)


@pytest.fixture
def consolidator(repository, conflict_resolver):
    return MemoryConsolidator(repository, conflict_resolver)


@pytest.fixture
def retrieval(repository, traversal, ranker):
    return MemoryRetrieval(repository, traversal, ranker)
