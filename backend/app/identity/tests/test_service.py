import pytest
from app.identity.schemas import IdentityType


@pytest.mark.asyncio
async def test_identity_service_public_apis(service):
    # 1. Create entities
    e1 = await service.create_entity(
        name="Peter Parker",
        entity_type=IdentityType.PERSON,
        display_name="Spider-Man",
        description="Queens hero.",
        metadata={"suit": "Iron Spider"},
    )

    assert e1.id.startswith("person_")

    # 2. Get entity
    fetched = await service.get_entity(e1.id)
    assert fetched.canonical_name == "Peter Parker"

    # 3. Find entity
    found = await service.find_entity("Peter Parker")
    assert found.id == e1.id

    # 4. Resolve entity
    resolved = await service.resolve_entity("Peter Parker", IdentityType.PERSON)
    assert resolved.id == e1.id

    # 5. Search entities
    results = await service.search_entities("Spider-Man")
    assert len(results) == 1
    assert results[0].id == e1.id

    # 6. Profile query
    profile = await service.get_entity_profile(e1.id)
    assert profile["entity"].canonical_name == "Peter Parker"
    assert profile["entity"].metadata["suit"] == "Iron Spider"

    # Test attributes enrichment
    await service.enrich_attribute(e1.id, "editor", "Cursor", 1.0)
    profile = await service.get_entity_profile(e1.id)
    assert profile["attributes"]["editor"] == "Cursor"
