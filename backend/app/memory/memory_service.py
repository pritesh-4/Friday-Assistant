"""Unified Cognitive Memory Service coordinating storage, retrieval, and extraction."""

from app.core.logging import get_logger
from app.db.database import database
from app.memory.schemas import AMISExtraction, ExtractedMemoryV2
from app.memory.storage import MemoryStorage
from app.memory.identity import IdentitySystem
from app.memory.entity_resolution import EntityResolutionSystem
from app.memory.knowledge_graph import KnowledgeGraphSystem
from app.memory.ranking import MemoryRanker
from app.memory.retrieval import MemoryRetrievalOrchestrator
from app.memory.memory_extractor import AMISMemeoryExtractor
from app.schemas.memory import (
    CognitiveMemoryPayload,
    ExtractedMemory,
    MemoryMetadata,
    MemoryType,
)
from app.utils.helpers import generate_uuid, get_utc_now
from app.services.llm_service import LLMService

logger = get_logger("memory.service")


class CognitiveMemoryService:
    """Orchestrates short-term and long-term memory operations for F.R.I.D.A.Y."""

    def __init__(self) -> None:
        self.storage = MemoryStorage()
        self.identity_system = IdentitySystem(self.storage)
        self.entity_resolution = EntityResolutionSystem(self.storage, self.identity_system)
        self.knowledge_graph = KnowledgeGraphSystem(self.storage)
        self.ranker = MemoryRanker()
        self.retrieval = MemoryRetrievalOrchestrator(
            self.storage, self.knowledge_graph, self.ranker
        )
        self.extractor = AMISMemeoryExtractor(LLMService())

    async def retrieve_relevant_memories(
        self, query: str, limit_per_type: int = 3
    ) -> dict[str, list[dict]]:
        """Retrieve and rank relevant memories across all layers."""
        return await self.retrieval.retrieve_context(query, limit_per_type)

    async def process_interaction(
        self, user_message: str, conversation_id: str | None = None
    ) -> str | None:
        """
        Extract memories from a user interaction.
        Detects explicit command instructions (forget, update, correct) and runs them.
        Updates entities, attributes, graph links, and stores cognitive memories.
        Returns a response message if a correction/forget command was processed.
        """
        extracted = await self.extractor.extract(user_message)
        if not extracted or not extracted.should_remember:
            return None

        # 1. Process explicit user memory commands first
        command_responses = []
        for cmd in extracted.commands:
            logger.info(f"Processing memory command: {cmd.action} on {cmd.target_type}")
            resp = await self.entity_resolution.handle_user_correction(cmd)
            command_responses.append(resp)

        # 2. Resolve entities and attributes
        resolved_entities = await self.entity_resolution.resolve_extracted_entities(
            extracted.entities
        )

        # 3. Resolve relationships
        for rel in extracted.relationships:
            source_id = resolved_entities.get(rel.source_entity_name)
            target_id = resolved_entities.get(rel.target_entity_name)

            if not source_id:
                # Fallback check database
                ent = await self.storage.get_entity_by_name_or_alias(rel.source_entity_name)
                if ent:
                    source_id = ent.id

            if not target_id:
                ent = await self.storage.get_entity_by_name_or_alias(rel.target_entity_name)
                if ent:
                    target_id = ent.id

            # If both endpoints are resolved, save graph edge
            if source_id and target_id:
                await self.knowledge_graph.add_relationship(
                    source_id, target_id, rel.relation_type, rel.weight
                )

        # 4. Save new cognitive memories
        for mem in extracted.memories:
            memory_id = generate_uuid()
            await self.storage.save_cognitive_memory(
                memory_id=memory_id,
                memory_type=mem.memory_type,
                content=mem.content,
                importance=mem.importance_score,
                confidence=mem.confidence,
                reason=mem.reason or "Extracted by AMIS",
                conversation_id=conversation_id,
                event_title=mem.event_title,
                timeline_date=mem.timeline_date,
                workflow_name=mem.workflow_name,
                project_name=mem.project_name,
            )

        if command_responses:
            return "\n".join(command_responses)
        return None

    async def save_extracted_memory(self, extracted: ExtractedMemory) -> None:
        """
        Legacy compatibility interface wrapper.
        Converts the standard ExtractedMemory payload into the new storage format.
        """
        if (
            not extracted.should_remember
            or not extracted.memory_type
            or not extracted.content
        ):
            return

        memory_id = generate_uuid()
        await self.storage.save_cognitive_memory(
            memory_id=memory_id,
            memory_type=extracted.memory_type,
            content=extracted.content,
            importance=extracted.importance_score or 5,
            confidence=extracted.confidence or 1.0,
            reason=extracted.reason or "Legacy extraction integration",
            event_title=extracted.event_title,
            timeline_date=extracted.timeline_date,
            workflow_name=extracted.workflow_name,
            project_name=extracted.project_name,
        )

    async def get_all_memories(self) -> list[CognitiveMemoryPayload]:
        """Fetch all memories for the UI manager (with full compatibility)."""
        payloads = []
        metadata_rows = await database.fetch_all(
            "SELECT * FROM memory_metadata ORDER BY created_at DESC"
        )
        for row in metadata_rows:
            mem_type = row["memory_type"]
            mem_id = row["memory_id"]

            content = ""
            updated_at = None

            if mem_type == "semantic":
                mem = await database.fetch_one(
                    "SELECT fact, updated_at FROM semantic_memories WHERE id = ?",
                    (mem_id,),
                )
                if mem:
                    content = mem["fact"]
                    updated_at = mem["updated_at"]
            elif mem_type == "episodic":
                mem = await database.fetch_one(
                    "SELECT event_title, timeline_date, details, updated_at FROM episodic_memories WHERE id = ?",
                    (mem_id,),
                )
                if mem:
                    content = f"{mem['event_title']} ({mem['timeline_date']}): {mem['details']}"
                    updated_at = mem["updated_at"]
            elif mem_type == "procedural":
                mem = await database.fetch_one(
                    "SELECT workflow_name, steps, updated_at FROM procedural_memories WHERE id = ?",
                    (mem_id,),
                )
                if mem:
                    content = f"{mem['workflow_name']}: {mem['steps']}"
                    updated_at = mem["updated_at"]
            elif mem_type == "project":
                mem = await database.fetch_one(
                    "SELECT project_id, content, updated_at FROM project_memories WHERE id = ?",
                    (mem_id,),
                )
                if mem:
                    project = await database.fetch_one(
                        "SELECT name FROM projects WHERE id = ?", (mem["project_id"],)
                    )
                    pname = project["name"] if project else "Unknown"
                    content = f"[{pname}] {mem['content']}"
                    updated_at = mem["updated_at"]

            if content:
                payloads.append(
                    CognitiveMemoryPayload(
                        id=mem_id,
                        memory_type=MemoryType(mem_type),
                        content=content,
                        metadata=MemoryMetadata(
                            id=row["id"],
                            memory_type=MemoryType(row["memory_type"]),
                            memory_id=row["memory_id"],
                            importance_score=row["importance_score"],
                            reason=row["reason"],
                            retrieval_count=row["retrieval_count"],
                            created_at=row["created_at"],
                        ),
                        created_at=row["created_at"],
                        updated_at=updated_at,
                    )
                )

        return payloads

    async def delete_memory(self, memory_id: str, memory_type: MemoryType) -> bool:
        """Permanently delete a cognitive memory."""
        return await self.storage.delete_cognitive_memory(memory_id, memory_type)
