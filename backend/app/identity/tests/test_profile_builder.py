import pytest
from app.identity.schemas import IdentityType


@pytest.mark.asyncio
async def test_profile_enrichment_history_archive(
    profile_builder, registry, repository
):
    entity = await registry.register_entity("Natasha Romanoff", IdentityType.PERSON)

    # 1. Add key 'role' with 0.8 confidence
    await profile_builder.enrich_profile_attribute(entity.id, "role", "KGB Agent", 0.8)

    # 2. Overwrite role with higher/equal confidence
    await profile_builder.enrich_profile_attribute(entity.id, "role", "Avenger", 0.9)

    attrs = await repository.get_entity_attributes(entity.id)

    # 'role' should be Avenger, 'previous_role' should be KGB Agent
    role_attr = next(a for a in attrs if a["key"] == "role")
    prev_role_attr = next(a for a in attrs if a["key"] == "previous_role")

    assert role_attr["value"] == "Avenger"
    assert prev_role_attr["value"] == "KGB Agent"


@pytest.mark.asyncio
async def test_profile_enrichment_lower_confidence_rejected(
    profile_builder, registry, repository
):
    entity = await registry.register_entity("Steve Rogers", IdentityType.PERSON)

    # 1. High confidence trait
    await profile_builder.enrich_profile_attribute(
        entity.id, "favorite_food", "Apple Pie", 1.0
    )

    # 2. Lower confidence trait update
    await profile_builder.enrich_profile_attribute(
        entity.id, "favorite_food", "Shawarma", 0.5
    )

    attrs = await repository.get_entity_attributes(entity.id)
    food_attr = next(
        a for a in attrs if a["key"] == "role" or a["key"] == "favorite_food"
    )

    # Should remain Apple Pie
    assert food_attr["value"] == "Apple Pie"
