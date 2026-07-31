import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from app.db.database import database
from app.db.vector_store import vector_store
from app.services.llm_service import LLMService

from app.storage.repository import MemoryRepository
from app.identity import IdentityService
from app.knowledge_graph.graph import KnowledgeGraph
from app.knowledge_graph.traversal import GraphTraversal
from app.knowledge_graph.context_engine import ContextEngine


@pytest.fixture(autouse=True)
async def setup_test_db(tmp_path: Path):
    """Isolate database path and run migrations."""
    db_file = tmp_path / "friday-kg-test.db"
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
def graph(repository):
    return KnowledgeGraph(repository)


@pytest.fixture
def traversal(graph, repository):
    return GraphTraversal(graph, repository)


@pytest.fixture
def context_engine(graph, repository):
    return ContextEngine(graph, repository)


@pytest.fixture
def identity_service():
    llm_mock = MagicMock(spec=LLMService)
    return IdentityService(database, llm_mock)
