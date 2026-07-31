import pytest
from app.memory.schemas import Entity, EntityType, EntityAttribute, Relationship
from app.schemas.memory import MemoryType
from app.utils.helpers import generate_uuid, get_utc_now


@pytest.mark.asyncio
async def test_entity_storage(storage):
    entity_id = "person_test123"
    now = get_utc_now()
    
    entity = Entity(
        id=entity_id,
        type=EntityType.PERSON,
        name="Bruce Wayne",
        confidence=1.0,
        created_at=now,
        updated_at=now
    )
    
    # Save entity
    await storage.save_entity(entity)
    
    # Retrieve
    fetched = await storage.get_entity(entity_id)
    assert fetched is not None
    assert fetched.name == "Bruce Wayne"
    assert fetched.type == EntityType.PERSON

    # Get by name or alias
    fetched_by_name = await storage.get_entity_by_name_or_alias("Bruce Wayne")
    assert fetched_by_name is not None
    assert fetched_by_name.id == entity_id


@pytest.mark.asyncio
async def test_aliases(storage):
    entity_id = "person_bruce"
    now = get_utc_now()
    entity = Entity(
        id=entity_id,
        type=EntityType.PERSON,
        name="Bruce Wayne",
        confidence=1.0,
        created_at=now,
        updated_at=now
    )
    await storage.save_entity(entity)

    # Add alias
    await storage.add_entity_alias(entity_id, "Batman")
    
    # Verify alias lookup
    fetched = await storage.get_entity_by_name_or_alias("Batman")
    assert fetched is not None
    assert fetched.id == entity_id

    aliases = await storage.get_entity_aliases(entity_id)
    assert "Batman" in aliases


@pytest.mark.asyncio
async def test_attributes(storage):
    entity_id = "person_tony"
    now = get_utc_now()
    entity = Entity(
        id=entity_id,
        type=EntityType.PERSON,
        name="Tony Stark",
        confidence=1.0,
        created_at=now,
        updated_at=now
    )
    await storage.save_entity(entity)

    attr = EntityAttribute(
        id=generate_uuid(),
        entity_id=entity_id,
        key="suit",
        value="Iron Man Mark 85",
        confidence=1.0,
        created_at=now,
        updated_at=now
    )
    await storage.save_entity_attribute(attr)

    attrs = await storage.get_entity_attributes(entity_id)
    assert len(attrs) == 1
    assert attrs[0].key == "suit"
    assert attrs[0].value == "Iron Man Mark 85"


@pytest.mark.asyncio
async def test_relationships(storage):
    e1_id = "person_user"
    e2_id = "project_friday"
    now = get_utc_now()
    
    await storage.save_entity(Entity(id=e1_id, type=EntityType.PERSON, name="Boss", created_at=now, updated_at=now))
    await storage.save_entity(Entity(id=e2_id, type=EntityType.PROJECT, name="FRIDAY", created_at=now, updated_at=now))

    rel = Relationship(
        id=generate_uuid(),
        source_id=e1_id,
        target_id=e2_id,
        relation_type="works_on",
        weight=1.0,
        created_at=now,
        updated_at=now
    )
    await storage.save_relationship(rel)

    rels = await storage.get_relationships(e1_id)
    assert len(rels) == 1
    assert rels[0].relation_type == "works_on"


@pytest.mark.asyncio
async def test_cognitive_memories(storage):
    memory_id = generate_uuid()
    await storage.save_cognitive_memory(
        memory_id=memory_id,
        memory_type=MemoryType.SEMANTIC,
        content="User likes dark mode theme",
        importance=8,
        confidence=1.0,
        reason="User settings update",
    )

    metadata = await storage.get_memory_metadata(memory_id)
    assert metadata is not None
    assert metadata["importance_score"] == 8
    assert metadata["confidence_score"] == 1.0
    assert metadata["verification_status"] == "unverified"
