import pytest
from app.schemas.cme import CMEEntity, CMEEntityType, CMEEntityAttribute, CMEExtractedEntity, CMEExplicitCommand
from app.utils.helpers import get_utc_now, generate_uuid


@pytest.mark.asyncio
async def test_resolve_attribute_conflicts(conflict_resolver, repository):
    entity_id = "person_test_conflicts"
    now = get_utc_now()
    await repository.save_entity(
        CMEEntity(id=entity_id, type=CMEEntityType.PERSON, name="Steve Rogers", created_at=now, updated_at=now)
    )

    # Initial attribute
    await conflict_resolver.resolve_attribute_conflict(entity_id, "job", "Soldier", 0.8)

    # Overwrite attribute
    await conflict_resolver.resolve_attribute_conflict(entity_id, "job", "Avenger", 0.8)

    attributes = await repository.get_entity_attributes(entity_id)
    job_attr = next(a for a in attributes if a.key == "job")
    prev_job_attr = next(a for a in attributes if a.key == "previous_job")

    assert job_attr.value == "Avenger"
    assert prev_job_attr.value == "Soldier"


@pytest.mark.asyncio
async def test_resolver_merge_entities(resolver, repository):
    now = get_utc_now()
    # 1. Create two separate entities
    e1 = await resolver.resolve_canonical("Tony Stark", CMEEntityType.PERSON)
    e2 = await resolver.resolve_canonical("Iron Man", CMEEntityType.PERSON)

    await repository.save_entity_attribute(
        CMEEntityAttribute(id=generate_uuid(), entity_id=e1.id, key="intellect", value="genius", confidence=1.0, created_at=now, updated_at=now)
    )
    await repository.save_entity_attribute(
        CMEEntityAttribute(id=generate_uuid(), entity_id=e2.id, key="suit", value="Mark 85", confidence=1.0, created_at=now, updated_at=now)
    )

    # 2. Merge them
    await resolver.merge_entities(e1.id, e2.id)

    # e2 should be deleted
    assert await repository.get_entity(e2.id) is None

    # e1 should inherit attributes
    e1_profile = await resolver.get_entity_profile(e1.id)
    assert "Iron Man" in e1_profile["aliases"]
    assert e1_profile["attributes"]["suit"] == "Mark 85"
    assert e1_profile["attributes"]["intellect"] == "genius"
