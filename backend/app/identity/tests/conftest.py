import pytest
from pathlib import Path
from unittest.mock import MagicMock

from app.db.database import database
from app.services.llm_service import LLMService

from app.identity import (
    IdentityRepository,
    IdentityRegistry,
    AliasManager,
    RelationshipManager,
    ProfileBuilder,
    IdentityResolver,
    ConfidenceEngine,
    IdentityService,
)


@pytest.fixture(autouse=True)
async def setup_test_db(tmp_path: Path):
    """Isolate database path and run all migrations (including Migration 7)."""
    db_file = tmp_path / "friday-identity-test.db"
    database.configure(f"sqlite:///{db_file.as_posix()}")
    await database.initialize()
    yield


@pytest.fixture
def repository():
    return IdentityRepository(database)


@pytest.fixture
def registry(repository):
    return IdentityRegistry(repository)


@pytest.fixture
def alias_manager(repository):
    return AliasManager(repository)


@pytest.fixture
def relationship_manager(repository):
    return RelationshipManager(repository)


@pytest.fixture
def profile_builder(repository):
    return ProfileBuilder(repository)


@pytest.fixture
def resolver(registry, repository, alias_manager, profile_builder):
    return IdentityResolver(registry, repository, alias_manager, profile_builder)


@pytest.fixture
def confidence_engine():
    return ConfidenceEngine()


@pytest.fixture
def service():
    llm_mock = MagicMock(spec=LLMService)
    return IdentityService(database, llm_mock)
