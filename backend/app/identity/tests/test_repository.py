import pytest
from app.identity.schemas import IdentityEntity, IdentityType
from app.utils.helpers import get_utc_now


@pytest.mark.asyncio
async def test_repository_save_and_get_entity(repository):
    entity_id = "person_bruce"
    now = get_utc_now()

    entity = IdentityEntity(
        id=entity_id,
        type=IdentityType.PERSON,
        display_name="Bruce Wayne",
        canonical_name="Bruce Wayne",
        aliases=["Bruce"],
        description="Billionaire playboy by day, Batman by night.",
        metadata={"city": "Gotham", "net_worth": "billions"},
        confidence=0.95,
        created_at=now,
        updated_at=now,
        status="active",
        version=1,
        source_history=["Manual registry registration"],
    )

    await repository.save_entity(entity)

    fetched = await repository.get_entity(entity_id)
    assert fetched is not None
    assert fetched.canonical_name == "Bruce Wayne"
    assert fetched.display_name == "Bruce Wayne"
    assert fetched.type == IdentityType.PERSON
    assert fetched.metadata["city"] == "Gotham"
    assert fetched.confidence == 0.95
    assert "Manual registry registration" in fetched.source_history


@pytest.mark.asyncio
async def test_repository_search_entities(repository):
    now = get_utc_now()
    await repository.save_entity(
        IdentityEntity(
            id="proj_friday",
            type=IdentityType.PROJECT,
            display_name="FRIDAY Assistant",
            canonical_name="FRIDAY Assistant",
            created_at=now,
            updated_at=now,
        )
    )
    await repository.save_entity(
        IdentityEntity(
            id="tech_fastapi",
            type=IdentityType.TECHNOLOGY,
            display_name="FastAPI Framework",
            canonical_name="FastAPI Framework",
            created_at=now,
            updated_at=now,
        )
    )

    results = await repository.search_entities("friday")
    assert len(results) == 1
    assert results[0].id == "proj_friday"

    results_all = await repository.get_all_entities()
    assert len(results_all) == 2
