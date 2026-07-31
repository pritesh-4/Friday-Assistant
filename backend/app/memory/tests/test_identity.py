import pytest
from app.schemas.cme import CMEEntityType
from app.identity.registry import IdentityRegistry


def test_registry_generate_id():
    id_person = IdentityRegistry.generate_id(CMEEntityType.PERSON)
    id_project = IdentityRegistry.generate_id(CMEEntityType.PROJECT)
    
    assert id_person.startswith("person_")
    assert id_project.startswith("project_")
    assert len(id_person) > 8


@pytest.mark.asyncio
async def test_resolver_resolve_canonical(resolver):
    entity = await resolver.resolve_canonical(
        name="Peter Parker",
        entity_type=CMEEntityType.PERSON
    )
    
    assert entity.id.startswith("person_")
    assert entity.name == "Peter Parker"

    # Fetch again, should return the exact same entity profile
    entity_duplicate = await resolver.resolve_canonical(
        name="Peter Parker",
        entity_type=CMEEntityType.PERSON
    )
    assert entity_duplicate.id == entity.id


@pytest.mark.asyncio
async def test_resolver_aliases(resolver, registry):
    entity = await resolver.resolve_canonical(
        name="Clark Kent",
        entity_type=CMEEntityType.PERSON
    )

    await registry.register_alias(entity.id, "Superman")

    # Resolve via alias
    resolved = await resolver.resolve_canonical(
        name="Superman",
        entity_type=CMEEntityType.PERSON
    )
    assert resolved.id == entity.id

    profile = await resolver.get_entity_profile(entity.id)
    assert "Superman" in profile["aliases"]
