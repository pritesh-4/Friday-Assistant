import pytest
from app.schemas.cme import CMEEntity, CMEEntityType, CMEEntityAttribute, CMERelationship
from app.schemas.memory import MemoryType
from app.utils.helpers import generate_uuid, get_utc_now


@pytest.mark.asyncio
async def test_entity_repository(repository):
    entity_id = "person_bruce"
    now = get_utc_now()
    
    entity = CMEEntity(
        id=entity_id,
        type=CMEEntityType.PERSON,
        name="Bruce Wayne",
        confidence=1.0,
        created_at=now,
        updated_at=now
    )
    
    await repository.save_entity(entity)
    
    fetched = await repository.get_entity(entity_id)
    assert fetched is not None
    assert fetched.name == "Bruce Wayne"
    assert fetched.type == CMEEntityType.PERSON

    fetched_by_name = await repository.get_entity_by_name_or_alias("Bruce Wayne")
    assert fetched_by_name is not None
    assert fetched_by_name.id == entity_id


@pytest.mark.asyncio
async def test_repository_aliases(repository):
    entity_id = "person_bruce"
    now = get_utc_now()
    entity = CMEEntity(
        id=entity_id,
        type=CMEEntityType.PERSON,
        name="Bruce Wayne",
        confidence=1.0,
        created_at=now,
        updated_at=now
    )
    await repository.save_entity(entity)

    await repository.add_entity_alias(entity_id, "Batman")
    
    fetched = await repository.get_entity_by_name_or_alias("Batman")
    assert fetched is not None
    assert fetched.id == entity_id

    aliases = await repository.get_entity_aliases(entity_id)
    assert "Batman" in aliases


@pytest.mark.asyncio
async def test_repository_attributes(repository):
    entity_id = "person_tony"
    now = get_utc_now()
    entity = CMEEntity(
        id=entity_id,
        type=CMEEntityType.PERSON,
        name="Tony Stark",
        confidence=1.0,
        created_at=now,
        updated_at=now
    )
    await repository.save_entity(entity)

    attr = CMEEntityAttribute(
        id=generate_uuid(),
        entity_id=entity_id,
        key="suit",
        value="Iron Man Mark 85",
        confidence=1.0,
        created_at=now,
        updated_at=now
    )
    await repository.save_entity_attribute(attr)

    attrs = await repository.get_entity_attributes(entity_id)
    assert len(attrs) == 1
    assert attrs[0].key == "suit"
    assert attrs[0].value == "Iron Man Mark 85"


@pytest.mark.asyncio
async def test_repository_relationships(repository):
    e1_id = "person_user"
    e2_id = "project_friday"
    now = get_utc_now()
    
    await repository.save_entity(CMEEntity(id=e1_id, type=CMEEntityType.PERSON, name="Boss", created_at=now, updated_at=now))
    await repository.save_entity(CMEEntity(id=e2_id, type=CMEEntityType.PROJECT, name="FRIDAY", created_at=now, updated_at=now))

    rel = CMERelationship(
        id=generate_uuid(),
        source_id=e1_id,
        target_id=e2_id,
        relation_type="works_on",
        weight=1.0,
        created_at=now,
        updated_at=now
    )
    await repository.save_relationship(rel)

    rels = await repository.get_relationships(e1_id)
    assert len(rels) == 1
    assert rels[0].relation_type == "works_on"


@pytest.mark.asyncio
async def test_repository_cognitive_memories(repository):
    memory_id = generate_uuid()
    await repository.save_cognitive_memory(
        memory_id=memory_id,
        memory_type=MemoryType.SEMANTIC,
        content="User prefers Cursor editor",
        importance=9,
        confidence=1.0,
        reason="User explicit comment",
    )

    metadata = await repository.get_memory_metadata(memory_id)
    assert metadata is not None
    assert metadata["importance_score"] == 9
    assert metadata["confidence_score"] == 1.0
    assert metadata["verification_status"] == "unverified"
