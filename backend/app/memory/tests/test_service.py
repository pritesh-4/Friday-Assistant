import pytest
from unittest.mock import patch, AsyncMock
from app.memory.memory_service import CognitiveMemoryService
from app.memory.schemas import (
    AMISExtraction,
    ExtractedEntity,
    ExtractedRelationship,
    ExtractedMemoryV2,
    EntityType,
)
from app.schemas.memory import MemoryType


@pytest.mark.asyncio
async def test_process_interaction_with_extracted_data():
    service = CognitiveMemoryService()

    # Mock the LLM extractor output
    mock_extraction = AMISExtraction(
        should_remember=True,
        entities=[
            ExtractedEntity(
                name="Bruce",
                type=EntityType.PERSON,
                aliases=["Batman"],
                attributes={"city": "Gotham"},
            )
        ],
        relationships=[
            ExtractedRelationship(
                source_entity_name="Bruce",
                target_entity_name="Gotham",
                relation_type="protects",
                weight=1.0,
            )
        ],
        memories=[
            ExtractedMemoryV2(
                memory_type=MemoryType.SEMANTIC,
                content="Bruce defends Gotham",
                importance_score=7,
                confidence=1.0,
            )
        ],
        commands=[],
    )

    with (
        patch.object(service.extractor, "extract", new_callable=AsyncMock) as mock_extract,
        patch.object(service.storage, "save_cognitive_memory", new_callable=AsyncMock) as mock_save_mem,
    ):
        mock_extract.return_value = mock_extraction

        # Run process_interaction
        await service.process_interaction("Bruce defends Gotham", "conv_123")

        # Verify entity resolution and saving occurred
        mock_extract.assert_called_once_with("Bruce defends Gotham")
        
        # Check that entity Bruce was saved in database
        resolved = await service.storage.get_entity_by_name_or_alias("Bruce")
        assert resolved is not None
        assert resolved.name == "Bruce"

        # Check attributes
        attrs = await service.storage.get_entity_attributes(resolved.id)
        assert len(attrs) == 1
        assert attrs[0].key == "city"
        assert attrs[0].value == "Gotham"

        # Check memory saving mock call
        mock_save_mem.assert_called_once()
        args, kwargs = mock_save_mem.call_args
        assert kwargs["memory_type"] == MemoryType.SEMANTIC
        assert kwargs["content"] == "Bruce defends Gotham"
        assert kwargs["importance"] == 7
        assert kwargs["conversation_id"] == "conv_123"
