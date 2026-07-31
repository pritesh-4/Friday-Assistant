import pytest
from app.schemas.cme import CMEEntity, CMEEntityType
from app.knowledge_graph.relationships import get_default_weight
from app.utils.helpers import get_utc_now


def test_default_weights_baseline():
    assert get_default_weight("owns") == 1.0
    assert get_default_weight("uses") == 0.8
    assert get_default_weight("unknown_rel") == 0.5


@pytest.mark.asyncio
async def test_traversal_connected_neighborhood(graph, traversal, repository):
    now = get_utc_now()
    await repository.save_entity(
        CMEEntity(
            id="user_1",
            type=CMEEntityType.PERSON,
            name="Boss",
            created_at=now,
            updated_at=now,
        )
    )
    await repository.save_entity(
        CMEEntity(
            id="friday_1",
            type=CMEEntityType.PROJECT,
            name="FRIDAY",
            created_at=now,
            updated_at=now,
        )
    )
    await repository.save_entity(
        CMEEntity(
            id="fastapi_1",
            type=CMEEntityType.FRAMEWORK,
            name="FastAPI",
            created_at=now,
            updated_at=now,
        )
    )
    await repository.save_entity(
        CMEEntity(
            id="render_1",
            type=CMEEntityType.ORGANIZATION,
            name="Render",
            created_at=now,
            updated_at=now,
        )
    )

    await graph.add_edge("user_1", "friday_1", "works_on", 1.0)
    await graph.add_edge("friday_1", "fastapi_1", "uses", 1.0)
    await graph.add_edge("fastapi_1", "render_1", "runs_on", 1.0)

    neighborhood = await traversal.get_connected_neighborhood(["user_1"], max_hops=2)

    assert "user_1" in neighborhood
    assert neighborhood["user_1"] == 1.0

    assert "friday_1" in neighborhood
    assert neighborhood["friday_1"] == 0.5

    assert "fastapi_1" in neighborhood
    assert neighborhood["fastapi_1"] == 0.25

    assert "render_1" not in neighborhood
