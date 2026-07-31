import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from app.db.database import database
from app.db.vector_store import vector_store
from app.services.llm_service import LLMService

from app.storage.repository import MemoryRepository
from app.knowledge_graph.graph import KnowledgeGraph
from app.knowledge_graph.context_engine import ContextEngine
from app.planning.executive import ExecutivePlanner
from app.agents.router_agent import RouterAgent


@pytest.fixture(autouse=True)
async def setup_test_db(tmp_path: Path):
    """Isolate database path and run migrations."""
    db_file = tmp_path / "friday-planning-test.db"
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
def context_engine(graph, repository):
    return ContextEngine(graph, repository)


@pytest.fixture
def executive_planner(graph, repository):
    llm_mock = MagicMock(spec=LLMService)
    # mock empty providers to force default/fallback planning or set up mocks in test
    llm_mock.available_providers = {}
    return ExecutivePlanner(database, llm_mock, ContextEngine(graph, repository))


@pytest.fixture
def router_agent():
    return RouterAgent()
