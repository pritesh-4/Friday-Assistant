import pytest
from unittest.mock import AsyncMock

from app.utils.helpers import get_utc_now
from app.identity.schemas import IdentityEntity, IdentityType, IdentityRelationship
from app.schemas.cme import CMEEntity, CMEEntityType


@pytest.mark.asyncio
async def test_node_lifecycle_and_updates(graph, repository):
    now = get_utc_now()
    
    # 1. Create Node
    node = IdentityEntity(
        id="lang_python",
        type=IdentityType.PROGRAMMING_LANGUAGE,
        display_name="Python 3",
        canonical_name="python",
        aliases=["python3", "py"],
        description="A powerful general purpose language.",
        metadata={"creator": "Guido van Rossum"},
        confidence=1.0,
        created_at=now,
        updated_at=now,
        status="active",
        version=1,
        tags=["backend", "ai"]
    )
    
    created = await graph.create_node(node)
    assert created.id == "lang_python"
    assert created.canonical_name == "python"
    
    # Check retrieval
    fetched = await graph.find("python")
    assert fetched is not None
    assert fetched.display_name == "Python 3"
    assert "backend" in fetched.tags
    
    # Check alias match
    fetched_alias = await graph.find("python3")
    assert fetched_alias is not None
    assert fetched_alias.id == "lang_python"
    
    # 2. Update Node
    updated = await graph.update_node(
        node_id="lang_python",
        updates={
            "display_name": "Python 3.12",
            "metadata": {"creator": "Guido van Rossum", "typing": "strong"},
            "tags": ["backend", "ai", "scripting"]
        }
    )
    
    assert updated is not None
    assert updated.display_name == "Python 3.12"
    assert updated.version == 2
    assert "scripting" in updated.tags
    assert updated.metadata["typing"] == "strong"
    
    # 3. Delete Node
    await graph.delete_node("lang_python")
    fetched_after_delete = await graph.find("python")
    assert fetched_after_delete is None


@pytest.mark.asyncio
async def test_edge_lifecycle_and_merge(graph):
    # Setup test nodes
    now = get_utc_now()
    node_a = IdentityEntity(
        id="user_alex",
        type=IdentityType.USER,
        display_name="Alex Mercer",
        canonical_name="alex",
        created_at=now,
        updated_at=now,
    )
    node_b = IdentityEntity(
        id="proj_friday",
        type=IdentityType.PROJECT,
        display_name="FRIDAY Assistant",
        canonical_name="friday",
        created_at=now,
        updated_at=now,
    )
    
    await graph.create_node(node_a)
    await graph.create_node(node_b)
    
    # 1. Create Edge
    await graph.create_edge(
        source_id="user_alex",
        target_id="proj_friday",
        relation_type="works_on",
        weight=1.0,
        confidence=0.9,
        evidence="Observed commits.",
        direction="directed"
    )
    
    edges = await graph.get_edges_for_node("user_alex")
    assert len(edges) == 1
    assert edges[0].relation_type == "works_on"
    assert edges[0].weight == 1.0
    assert edges[0].confidence == 0.9
    assert edges[0].direction == "directed"
    
    # 2. Update Edge
    await graph.update_edge(
        source_id="user_alex",
        target_id="proj_friday",
        relation_type="works_on",
        updates={"weight": 2.5, "confidence": 1.0}
    )
    
    edges_updated = await graph.get_edges_for_node("user_alex")
    assert edges_updated[0].weight == 2.5
    assert edges_updated[0].confidence == 1.0
    
    # 3. Merge Edge (Strengthen recurring edge)
    await graph.merge_edge(
        source_id="user_alex",
        target_id="proj_friday",
        relation_type="works_on",
        weight=1.0,
        confidence=0.8,
        evidence="Additional user statement."
    )
    
    edges_merged = await graph.get_edges_for_node("user_alex")
    assert edges_merged[0].weight == 3.5  # 2.5 + 1.0
    assert edges_merged[0].confidence == 1.0  # max(1.0, 0.8)
    assert "Additional user statement." in edges_merged[0].evidence
    
    # 4. Delete Edge
    await graph.delete_edge("user_alex", "proj_friday", "works_on")
    edges_after_delete = await graph.get_edges_for_node("user_alex")
    assert len(edges_after_delete) == 0


@pytest.mark.asyncio
async def test_merge_duplicate_nodes(graph):
    now = get_utc_now()
    
    # Create two duplicate nodes
    node_a = IdentityEntity(
        id="person_alex_m",
        type=IdentityType.PERSON,
        display_name="Alex Mercer",
        canonical_name="alex mercer",
        created_at=now,
        updated_at=now,
        tags=["developer"]
    )
    
    node_b = IdentityEntity(
        id="person_alex",
        type=IdentityType.PERSON,
        display_name="Alex",
        canonical_name="alex",
        created_at=now,
        updated_at=now,
        tags=["stark-employee"]
    )
    
    node_c = IdentityEntity(
        id="proj_atlas",
        type=IdentityType.PROJECT,
        display_name="Atlas",
        canonical_name="atlas",
        created_at=now,
        updated_at=now,
    )
    
    await graph.create_node(node_a)
    await graph.create_node(node_b)
    await graph.create_node(node_c)
    
    # Link them
    await graph.create_edge("person_alex_m", "proj_atlas", "works_on")
    await graph.create_edge("proj_atlas", "person_alex", "assigned_to")
    
    # Merge B into A
    await graph.merge_nodes(source_id="person_alex", target_id="person_alex_m")
    
    # B should be deleted
    assert await graph.find("alex") is not None  # Resolves as alias of A now
    
    # Fetch A to verify property merge
    merged = await graph.find("alex mercer")
    assert merged is not None
    assert "developer" in merged.tags
    assert "stark-employee" in merged.tags
    
    # Verify redirected relationships
    # person_alex_m should have works_on to proj_atlas
    # and proj_atlas should have assigned_to to person_alex_m (redirected target)
    edges_a = await graph.get_edges_for_node("person_alex_m")
    assert len(edges_a) == 2
    
    relation_types = [e.relation_type for e in edges_a]
    assert "works_on" in relation_types
    assert "assigned_to" in relation_types


@pytest.mark.asyncio
async def test_traversal_shortest_path_explain(graph, traversal):
    now = get_utc_now()
    
    # Create chain: Alex (person) works_on Atlas (project) uses FastAPI (framework) hosted_on Render (company)
    n1 = IdentityEntity(id="p_alex", type=IdentityType.PERSON, display_name="Alex", canonical_name="alex", created_at=now, updated_at=now)
    n2 = IdentityEntity(id="proj_atlas", type=IdentityType.PROJECT, display_name="Atlas", canonical_name="atlas", created_at=now, updated_at=now)
    n3 = IdentityEntity(id="f_fastapi", type=IdentityType.FRAMEWORK, display_name="FastAPI", canonical_name="fastapi", created_at=now, updated_at=now)
    n4 = IdentityEntity(id="c_render", type=IdentityType.COMPANY, display_name="Render", canonical_name="render", created_at=now, updated_at=now)
    
    await graph.create_node(n1)
    await graph.create_node(n2)
    await graph.create_node(n3)
    await graph.create_node(n4)
    
    await graph.create_edge("p_alex", "proj_atlas", "works_on")
    await graph.create_edge("proj_atlas", "f_fastapi", "uses")
    await graph.create_edge("f_fastapi", "c_render", "hosted_on")
    
    # 1. Shortest path
    path = await graph.shortest_path("p_alex", "c_render")
    assert path == ["p_alex", "proj_atlas", "f_fastapi", "c_render"]
    
    # 2. Traverse relevance weight check
    weights = await graph.traverse("p_alex", max_hops=2)
    assert weights["p_alex"] == 1.0
    assert weights["proj_atlas"] == 0.5
    assert weights["f_fastapi"] == 0.25
    assert "c_render" not in weights
    
    # 3. Path explanation
    explanation = await graph.explain("p_alex", "c_render")
    assert "'alex' works_on 'atlas'" in explanation
    assert "which uses 'fastapi'" in explanation
    assert "which hosted_on 'render'" in explanation
    
    # 4. Reason (transitive target query)
    targets = await graph.reason("p_alex", ["works_on", "uses"])
    assert len(targets) == 1
    assert targets[0].id == "f_fastapi"
    assert targets[0].canonical_name == "fastapi"


@pytest.mark.asyncio
async def test_subgraph_extraction(graph):
    now = get_utc_now()
    n1 = IdentityEntity(id="n1", type=IdentityType.PERSON, display_name="N1", canonical_name="n1", created_at=now, updated_at=now)
    n2 = IdentityEntity(id="n2", type=IdentityType.PROJECT, display_name="N2", canonical_name="n2", created_at=now, updated_at=now)
    n3 = IdentityEntity(id="n3", type=IdentityType.FRAMEWORK, display_name="N3", canonical_name="n3", created_at=now, updated_at=now)
    
    await graph.create_node(n1)
    await graph.create_node(n2)
    await graph.create_node(n3)
    
    await graph.create_edge("n1", "n2", "likes")
    await graph.create_edge("n2", "n3", "uses")
    await graph.create_edge("n1", "n3", "prefers")
    
    sub = await graph.subgraph(["n1", "n3"])
    assert len(sub["nodes"]) == 2
    assert len(sub["edges"]) == 1
    assert sub["edges"][0].relation_type == "prefers"


@pytest.mark.asyncio
async def test_search_modes(graph, repository):
    now = get_utc_now()
    n = IdentityEntity(
        id="site_wiki",
        type=IdentityType.WEBSITE,
        display_name="Wikipedia",
        canonical_name="wikipedia",
        tags=["knowledge", "reference"],
        created_at=now,
        updated_at=now
    )
    await graph.create_node(n)
    
    # Exact search
    results_exact = await graph.search("wikipedia", search_type="exact")
    assert len(results_exact) == 1
    assert results_exact[0].id == "site_wiki"
    
    # Relationship search
    await graph.create_node(
        IdentityEntity(id="p_user", type=IdentityType.USER, display_name="User", canonical_name="user", created_at=now, updated_at=now)
    )
    await graph.create_edge("p_user", "site_wiki", "uses")
    
    results_rel = await graph.search("uses", search_type="relationship")
    assert len(results_rel) >= 2
    
    # Mock ChromaDB for Semantic/Hybrid search
    repository.vector_store.search = AsyncMock(return_value=[{"id": "site_wiki", "distance": 0.1}])
    results_semantic = await graph.search("encyclopedia", search_type="semantic")
    assert len(results_semantic) == 1
    assert results_semantic[0].id == "site_wiki"
    
    results_hybrid = await graph.search("encyclopedia", search_type="hybrid")
    assert len(results_hybrid) == 1
    assert results_hybrid[0].id == "site_wiki"


@pytest.mark.asyncio
async def test_context_engine(graph, context_engine, repository):
    now = get_utc_now()
    
    # Register user node
    u_node = IdentityEntity(
        id="user_me",
        type=IdentityType.USER,
        display_name="Alex Mercer",
        canonical_name="alex mercer",
        created_at=now,
        updated_at=now
    )
    await graph.create_node(u_node)
    
    # Add preferences edge
    p_node = IdentityEntity(
        id="lang_python",
        type=IdentityType.PROGRAMMING_LANGUAGE,
        display_name="Python",
        canonical_name="python",
        created_at=now,
        updated_at=now
    )
    await graph.create_node(p_node)
    await graph.create_edge("user_me", "lang_python", "prefers", evidence="Explicitly stated python preference.")
    
    # Add project node
    proj_node = IdentityEntity(
        id="proj_friday",
        type=IdentityType.PROJECT,
        display_name="FRIDAY AI",
        canonical_name="friday AI",
        description="F.R.I.D.A.Y. Assistant world model.",
        created_at=now,
        updated_at=now
    )
    await graph.create_node(proj_node)
    await graph.create_edge("user_me", "proj_friday", "works_on")
    
    # Build context
    context = await context_engine.build_context("python projects")
    
    assert len(context["relevant_nodes"]) > 0
    assert len(context["relevant_preferences"]) > 0
    assert context["relevant_preferences"][0] == "User prefers 'python' (evidence: Explicitly stated python preference.)"
    
    # Format markdown
    md = context_engine.format_as_markdown(context)
    assert "### CONTEXT ENGINE MODEL INFORMATION" in md
    assert "Preferences:" in md
    assert "User prefers 'python'" in md
    assert "Active Projects:" in md
    assert "friday AI" in md
