import pytest
from app.identity.schemas import IdentityType


@pytest.mark.asyncio
async def test_resolver_resolve_entity_type_upgrade(resolver, repository):
    # Resolve first as DOCUMENT
    e1 = await resolver.resolve_entity("Friday", IdentityType.DOCUMENT, 0.8)
    assert e1.type == IdentityType.DOCUMENT

    # Resolve later as PROJECT
    e2 = await resolver.resolve_entity("Friday", IdentityType.PROJECT, 0.9)

    # Assert same ID was reused but type upgraded
    assert e2.id == e1.id
    assert e2.type == IdentityType.PROJECT

    fetched = await repository.get_entity(e1.id)
    assert fetched.type == IdentityType.PROJECT
    assert "Upgraded identity type to 'project'" in fetched.source_history


@pytest.mark.asyncio
async def test_resolver_merge_profiles(
    resolver, repository, alias_manager, relationship_manager
):
    # 1. Register Tony Stark & Iron Man
    e1 = await resolver.resolve_entity("Tony Stark", IdentityType.PERSON)
    e2 = await resolver.resolve_entity("Iron Man", IdentityType.PERSON)

    await repository.save_entity_attribute(e1.id, "home", "Malibu", 1.0)
    await repository.save_entity_attribute(e2.id, "suit", "Mark 85", 0.9)

    # Add direct relationship for secondary
    await relationship_manager.add_relationship(e2.id, e1.id, "colleague_of", 1.0)

    # 2. Merge e2 -> e1
    await resolver.merge_entities(e1.id, e2.id)

    # e2 is removed
    assert await repository.get_entity(e2.id) is None

    # e1 inherits aliases, attributes, relationships
    aliases = await alias_manager.get_aliases(e1.id)
    assert "Iron Man" in aliases

    attrs = await repository.get_entity_attributes(e1.id)
    keys = {a["key"]: a["value"] for a in attrs}
    assert keys["home"] == "Malibu"
    assert keys["suit"] == "Mark 85"

    # Relationships redirected to e1
    rels = await relationship_manager.get_entity_relationships(e1.id)
    assert len(rels) == 1
    assert rels[0].source_id == e1.id
    assert rels[0].target_id == e1.id
