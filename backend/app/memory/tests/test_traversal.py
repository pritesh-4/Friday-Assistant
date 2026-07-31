import pytest
from app.schemas.cme import CMEEntity, CMEEntityType
from app.utils.helpers import get_utc_now


@pytest.mark.asyncio
async def test_transitive_reasoning_inference(graph, traversal, repository):
    now = get_utc_now()
    # Setup graph nodes
    # Alex (person) works_on -> ProjectA (project) uses -> FastAPI (framework)
    await repository.save_entity(CMEEntity(id="person_alex", type=CMEEntityType.PERSON, name="Alex", created_at=now, updated_at=now))
    await repository.save_entity(CMEEntity(id="project_a", type=CMEEntityType.PROJECT, name="Project A", created_at=now, updated_at=now))
    await repository.save_entity(CMEEntity(id="framework_fastapi", type=CMEEntityType.FRAMEWORK, name="FastAPI", created_at=now, updated_at=now))

    # Add edges
    await graph.add_edge("person_alex", "project_a", "works_on", 1.0)
    await graph.add_edge("project_a", "framework_fastapi", "uses", 1.0)

    # Resolve transitive path works_on -> uses
    inferred_tech_ids = await traversal.infer_path_targets("person_alex", ["works_on", "uses"])

    assert len(inferred_tech_ids) == 1
    assert inferred_tech_ids[0] == "framework_fastapi"

    # Verify that if we query framework_fastapi, we find the framework name
    inferred_node = await repository.get_entity(inferred_tech_ids[0])
    assert inferred_node is not None
    assert inferred_node.name == "FastAPI"
