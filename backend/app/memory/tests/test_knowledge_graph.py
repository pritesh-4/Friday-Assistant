import pytest
from app.memory.schemas import Entity, EntityType
from app.utils.helpers import get_utc_now


@pytest.mark.asyncio
async def test_connected_neighborhood(knowledge_graph, storage):
    now = get_utc_now()
    # Create entities: User -> Friday -> FastAPI -> Render
    await storage.save_entity(Entity(id="user_1", type=EntityType.PERSON, name="Boss", created_at=now, updated_at=now))
    await storage.save_entity(Entity(id="friday_1", type=EntityType.PROJECT, name="FRIDAY", created_at=now, updated_at=now))
    await storage.save_entity(Entity(id="fastapi_1", type=EntityType.FRAMEWORK, name="FastAPI", created_at=now, updated_at=now))
    await storage.save_entity(Entity(id="render_1", type=EntityType.ORGANIZATION, name="Render", created_at=now, updated_at=now))

    # Add relationships
    await knowledge_graph.add_relationship("user_1", "friday_1", "works_on", 1.0)
    await knowledge_graph.add_relationship("friday_1", "fastapi_1", "uses", 1.0)
    await knowledge_graph.add_relationship("fastapi_1", "render_1", "runs_on", 1.0)

    # 1. Get neighborhood of 'user_1' (max_hops = 2)
    # Should include:
    # user_1 (0-hop: weight 1.0)
    # friday_1 (1-hop: weight 0.5)
    # fastapi_1 (2-hop: weight 0.25)
    # NOT render_1 (3-hop)
    neighborhood = await knowledge_graph.get_connected_neighborhood(["user_1"], max_hops=2)

    assert "user_1" in neighborhood
    assert neighborhood["user_1"] == 1.0

    assert "friday_1" in neighborhood
    assert neighborhood["friday_1"] == 0.5

    assert "fastapi_1" in neighborhood
    assert neighborhood["fastapi_1"] == 0.25

    assert "render_1" not in neighborhood
