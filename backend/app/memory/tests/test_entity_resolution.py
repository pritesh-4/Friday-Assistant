import pytest
from app.memory.schemas import Entity, EntityType, EntityAttribute, ExtractedEntity, ExplicitCommand
from app.utils.helpers import get_utc_now, generate_uuid


@pytest.mark.asyncio
async def test_resolve_attribute_conflicts(entity_resolution, storage):
    entity_id = "person_test_conflicts"
    now = get_utc_now()
    await storage.save_entity(
        Entity(id=entity_id, type=EntityType.PERSON, name="Steve Rogers", created_at=now, updated_at=now)
    )

    # Initial attribute: job is "Soldier" (confidence 0.8)
    await entity_resolution.resolve_attribute(entity_id, "job", "Soldier", 0.8)

    # Resolve with same confidence: should update value and save old value as historical history
    await entity_resolution.resolve_attribute(entity_id, "job", "Avenger", 0.8)

    attributes = await storage.get_entity_attributes(entity_id)
    # Should have key 'job' with 'Avenger', and key 'previous_job' with 'Soldier'
    job_attr = next(a for a in attributes if a.key == "job")
    prev_job_attr = next(a for a in attributes if a.key == "previous_job")

    assert job_attr.value == "Avenger"
    assert prev_job_attr.value == "Soldier"


@pytest.mark.asyncio
async def test_merge_entities(entity_resolution, storage, identity_system):
    now = get_utc_now()
    # 1. Create two separate entities
    e1 = await identity_system.resolve_or_create_identity("Tony Stark", EntityType.PERSON)
    e2 = await identity_system.resolve_or_create_identity("Iron Man", EntityType.PERSON)

    await storage.save_entity_attribute(
        EntityAttribute(id=generate_uuid(), entity_id=e1.id, key="intellect", value="genius", confidence=1.0, created_at=now, updated_at=now)
    )
    await storage.save_entity_attribute(
        EntityAttribute(id=generate_uuid(), entity_id=e2.id, key="suit", value="Mark 85", confidence=1.0, created_at=now, updated_at=now)
    )

    # 2. Merge them
    await entity_resolution.merge_entities(e1.id, e2.id)

    # e2 should be deleted
    assert await storage.get_entity(e2.id) is None

    # e1 should inherit attributes and have "Iron Man" as alias
    e1_profile = await identity_system.get_entity_profile(e1.id)
    assert "Iron Man" in e1_profile["aliases"]
    assert e1_profile["attributes"]["suit"] == "Mark 85"
    assert e1_profile["attributes"]["intellect"] == "genius"


@pytest.mark.asyncio
async def test_handle_user_correction_attribute(entity_resolution, storage, identity_system):
    entity = await identity_system.resolve_or_create_identity("Natasha", EntityType.PERSON)
    await entity_resolution.resolve_attribute(entity.id, "codename", "Black Widow", 1.0)

    command = ExplicitCommand(
        action="correct",
        target_type="attribute",
        query="Natasha:codename",
        update_value="Yelena"
    )

    resp = await entity_resolution.handle_user_correction(command)
    assert "corrected" in resp

    attributes = await storage.get_entity_attributes(entity.id)
    code_attr = next(a for a in attributes if a.key == "codename")
    assert code_attr.value == "Yelena"
