import pytest
from unittest.mock import patch, AsyncMock
from app.memory.memory_service import CognitiveMemoryService
from app.schemas.cme import (
    CMEExtraction,
    CMEExtractedEntity,
    CMEExtractedRelationship,
    CMEExtractedMemory,
    CMEEntityType,
)
from app.schemas.memory import MemoryType


@pytest.mark.asyncio
async def test_process_interaction_cme_v2():
    service = CognitiveMemoryService()

    # Mock the V2 extraction containing the answers to the four questions
    mock_extraction = CMEExtraction(
        should_remember=True,
        what_happened="Bruce defends Gotham from villains.",
        who_involved=["Bruce", "Gotham"],
        what_changed="Entity status active",
        what_remember="Bruce protects Gotham City",
        entities=[
            CMEExtractedEntity(
                name="Bruce",
                type=CMEEntityType.PERSON,
                aliases=["Batman"],
                attributes={"city": "Gotham"},
            )
        ],
        relationships=[
            CMEExtractedRelationship(
                source_entity_name="Bruce",
                target_entity_name="Gotham",
                relation_type="protects",
                weight=1.0,
            )
        ],
        memories=[
            CMEExtractedMemory(
                memory_type=MemoryType.SEMANTIC,
                content="Bruce defends Gotham",
                importance_score=7,
                confidence=1.0,
            )
        ],
        commands=[],
    )

    with (
        patch.object(
            service.extractor, "extract", new_callable=AsyncMock
        ) as mock_extract,
        patch.object(
            service.consolidator, "consolidate_memory", new_callable=AsyncMock
        ) as mock_consolidate,
    ):
        mock_extract.return_value = mock_extraction
        mock_consolidate.return_value = "mem_123"

        # Process message
        await service.process_interaction("Bruce defends Gotham", "conv_123")

        mock_extract.assert_called_once_with("Bruce defends Gotham")

        # Verify entity resolution occurred
        resolved = await service.repository.get_entity_by_name_or_alias("Bruce")
        assert resolved is not None
        assert resolved.name == "Bruce"

        # Verify relationship edge was added to the graph
        edges = await service.graph.get_edges_for_node(resolved.id)
        assert len(edges) == 1
        assert edges[0].relation_type == "protects"

        # Verify memory consolidation call
        mock_consolidate.assert_called_once()
        args, kwargs = mock_consolidate.call_args
        assert kwargs["memory_type"] == MemoryType.SEMANTIC
        assert kwargs["content"] == "Bruce defends Gotham"
        assert kwargs["importance"] == 7
        assert kwargs["conversation_id"] == "conv_123"
