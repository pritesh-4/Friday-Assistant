import pytest
from app.identity.schemas import IdentityType


@pytest.mark.asyncio
async def test_entity_registry_lifecycle_and_history(service):
    # 1. Create entity with display name, tags, and metadata
    entity = await service.create_entity(
        name="Jarvis AI",
        entity_type=IdentityType.AI_MODEL,
        display_name="J.A.R.V.I.S.",
        description="Tony Stark's primary assistant.",
        metadata={"architecture": "Transformer", "core": "Friday precursor"},
        tags=["ai", "assistant", "stark"],
        editor="Stark Industries",
        reason="Deploy JARVIS V1",
    )

    assert entity.id.startswith("model_")
    assert entity.canonical_name == "Jarvis AI"
    assert entity.display_name == "J.A.R.V.I.S."
    assert "ai" in entity.tags
    assert entity.version == 1
    assert entity.visit_count == 1  # 1 on register

    # Verify initial history is logged
    history = await service.get_history(entity.id)
    assert len(history) == 1
    assert history[0]["version"] == 1
    assert history[0]["editor"] == "Stark Industries"
    assert history[0]["reason"] == "Deploy JARVIS V1"

    # 2. Update properties, increments version
    updated = await service.update_entity(
        entity_id=entity.id,
        updates={
            "display_name": "J.A.R.V.I.S. Core",
            "metadata": {
                "architecture": "Transformer",
                "core": "Friday precursor",
                "active": True,
            },
            "tags": ["ai", "assistant", "stark", "legacy"],
        },
        editor="Pepper Potts",
        reason="Upgrade framework core integration",
    )

    assert updated.version == 2
    assert updated.display_name == "J.A.R.V.I.S. Core"
    assert "legacy" in updated.tags
    assert updated.metadata["active"] is True

    # Verify history logs new version
    history2 = await service.get_history(entity.id)
    assert len(history2) == 2
    assert history2[0]["version"] == 2
    assert history2[0]["editor"] == "Pepper Potts"
    assert history2[0]["reason"] == "Upgrade framework core integration"

    # 3. Rollback back to version 1
    rolled = await service.rollback(
        entity_id=entity.id,
        target_version=1,
        editor="System Restore",
        reason="Framework rollback check",
    )

    assert rolled is not None
    assert rolled.version == 3
    assert rolled.display_name == "J.A.R.V.I.S."
    assert "legacy" not in rolled.tags
    assert "active" not in rolled.metadata

    # Visit count checking
    fetched = await service.get_entity(entity.id)
    assert fetched.visit_count >= 3


@pytest.mark.asyncio
async def test_entity_registry_search_strategies(service):
    # Register test entities
    e1 = await service.create_entity(
        name="Gotham City",
        entity_type=IdentityType.PLACE,
        tags=["location", "dark-knight"],
        metadata={"climate": "rainy", "population": 10000000},
    )
    e2 = await service.create_entity(
        name="Metropolis City",
        entity_type=IdentityType.PLACE,
        tags=["location", "man-of-steel"],
        metadata={"climate": "sunny", "population": 8000000},
    )

    await service.add_alias(e1.id, "Wayne County")

    # 1. Exact Match
    f1 = await service.find_entity("Gotham City")
    assert f1 is not None
    assert f1.id == e1.id

    # 2. Alias Match
    f2 = await service.find_by_alias("Wayne County")
    assert len(f2) == 1
    assert f2[0].id == e1.id

    # 3. Fuzzy Match
    f3 = await service.search(query="City")
    assert len(f3) == 2

    # 4. Type Match
    f4 = await service.search(entity_type=IdentityType.PLACE)
    assert len(f4) >= 2

    # 5. Tag Search
    f5 = await service.search(tag="man-of-steel")
    assert len(f5) == 1
    assert f5[0].id == e2.id

    # 6. Metadata Search
    f6 = await service.search(metadata_filters={"climate": "rainy"})
    assert len(f6) == 1
    assert f6[0].id == e1.id

    # 7. Hybrid Search
    f7 = await service.search(
        query="City", tag="location", metadata_filters={"climate": "sunny"}
    )
    assert len(f7) == 1
    assert f7[0].id == e2.id
