import pytest
from app.memory.schemas import EntityType
from app.memory.identity import IdentitySystem


def test_generate_entity_id():
    id_person = IdentitySystem.generate_entity_id(EntityType.PERSON)
    id_project = IdentitySystem.generate_entity_id(EntityType.PROJECT)
    
    assert id_person.startswith("person_")
    assert id_project.startswith("project_")
    assert len(id_person) > 8


@pytest.mark.asyncio
async def test_resolve_or_create_identity(identity_system):
    entity = await identity_system.resolve_or_create_identity(
        name="Peter Parker",
        entity_type=EntityType.PERSON
    )
    
    assert entity.id.startswith("person_")
    assert entity.name == "Peter Parker"

    # Fetch again, should return the exact same entity profile
    entity_duplicate = await identity_system.resolve_or_create_identity(
        name="Peter Parker",
        entity_type=EntityType.PERSON
    )
    assert entity_duplicate.id == entity.id


@pytest.mark.asyncio
async def test_resolve_aliases(identity_system):
    entity = await identity_system.resolve_or_create_identity(
        name="Clark Kent",
        entity_type=EntityType.PERSON
    )

    await identity_system.add_alias(entity.id, "Superman")

    # Resolve via alias
    resolved = await identity_system.resolve_or_create_identity(
        name="Superman",
        entity_type=EntityType.PERSON
    )
    assert resolved.id == entity.id

    profile = await identity_system.get_entity_profile(entity.id)
    assert "Superman" in profile["aliases"]
