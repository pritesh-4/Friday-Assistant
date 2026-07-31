"""Cognitive Memory Engine (CME) V2 Coordinator Service."""

from app.core.logging import get_logger
from app.db.database import database
from app.db.vector_store import vector_store
from app.schemas.cme import CMEEntityType
from app.schemas.memory import (
    CognitiveMemoryPayload,
    ExtractedMemory,
    MemoryMetadata,
    MemoryType,
)
from app.services.llm_service import LLMService

# Import Identity Engine V1 & CME V2 modules
from app.storage.repository import MemoryRepository
from app.identity import IdentityService, IdentityType
from app.knowledge_graph.graph import KnowledgeGraph
from app.knowledge_graph.traversal import GraphTraversal
from app.ranking.ranker import MemoryRanker
from app.memory.manager import MemoryManager
from app.memory.extractor import MemoryExtractor
from app.memory.scorer import ImportanceScorer
from app.memory.conflict_resolver import ConflictResolver
from app.memory.consolidator import MemoryConsolidator
from app.memory.retrieval import MemoryRetrieval

logger = get_logger("memory.cme_service")


def map_cme_type_to_identity_type(cme_type: CMEEntityType) -> IdentityType:
    """Helper to map CME entity types to Identity Engine enum types."""
    mapping = {
        CMEEntityType.PERSON: IdentityType.PERSON,
        CMEEntityType.PROJECT: IdentityType.PROJECT,
        CMEEntityType.ORGANIZATION: IdentityType.ORGANIZATION,
        CMEEntityType.AI_MODEL: IdentityType.AI_MODEL,
        CMEEntityType.APPLICATION: IdentityType.APPLICATION,
        CMEEntityType.PRODUCT: IdentityType.APPLICATION,
        CMEEntityType.REPOSITORY: IdentityType.REPOSITORY,
        CMEEntityType.CONCEPT: IdentityType.DOCUMENT,
        CMEEntityType.LOCATION: IdentityType.PLACE,
        CMEEntityType.TOOL: IdentityType.DEVICE,
        CMEEntityType.FRAMEWORK: IdentityType.FRAMEWORK,
        CMEEntityType.OTHER: IdentityType.DOCUMENT,
    }
    return mapping.get(cme_type, IdentityType.DOCUMENT)


class CognitiveMemoryService:
    """The central coordinator for CME V2 operations, managing context, graphs, and consolidation."""

    def __init__(self, identity_service: IdentityService | None = None) -> None:
        # Dependency Injection (Repository Pattern, no global state)
        self.repository = MemoryRepository(database, vector_store)
        self.identity_service = identity_service or IdentityService(
            database, LLMService()
        )
        self.graph = KnowledgeGraph(self.repository)
        self.traversal = GraphTraversal(self.graph, self.repository)
        self.ranker = MemoryRanker()
        self.manager = MemoryManager()
        self.extractor = MemoryExtractor(LLMService())
        self.scorer = ImportanceScorer()
        self.conflict_resolver = ConflictResolver(self.repository)
        self.consolidator = MemoryConsolidator(self.repository, self.conflict_resolver)
        self.retrieval = MemoryRetrieval(self.repository, self.traversal, self.ranker)

    async def retrieve_relevant_memories(
        self, query: str, limit_per_type: int = 3
    ) -> dict[str, list[dict]]:
        """Retrieve and rank context matches across memory layers."""
        return await self.retrieval.retrieve_context(query, limit_per_type)

    async def process_interaction(
        self, user_message: str, conversation_id: str | None = None
    ) -> str | None:
        """
        Runs the CME V2 extraction and updates lifecycle:
        1. LLM extracts entities, attributes, relations, and answers the 'Four Core Questions'.
        2. Logs the answers to the core questions.
        3. Executes explicit memory commands synchronously.
        4. Resolves entities and updates attributes (checking for conflicts).
        5. Saves/strengthens relationships in the Knowledge Graph.
        6. Consolidates (deduplicates & merges) cognitive memories.
        """
        extracted = await self.extractor.extract(user_message)
        if not extracted or not extracted.should_remember:
            return None

        # Log the Four Core Questions Answers
        logger.info(
            f"=== COGNITIVE MEMORY ENGINE V2 EVENT ANALYSIS ===\n"
            f"- WHAT HAPPENED: {extracted.what_happened}\n"
            f"- WHO WAS INVOLVED: {', '.join(extracted.who_involved) if extracted.who_involved else 'None'}\n"
            f"- WHAT CHANGED: {extracted.what_changed}\n"
            f"- WHAT SHOULD BE REMEMBERED: {extracted.what_remember}"
        )

        # 1. Process explicit user correction/forget commands
        command_responses = []
        for cmd in extracted.commands:
            logger.info(f"CME Command received: {cmd.action} on {cmd.target_type}")
            # Map resolving target checks
            resp = await self.identity_service.find_entity(
                cmd.query
            ) or await self.identity_service.find_by_alias(cmd.query)
            if cmd.action == "forget":
                if cmd.target_type in ("entity", "person", "project") and resp:
                    await self.identity_service.delete_entity(resp.id)
                    command_responses.append(
                        f"I have forgotten all records regarding '{resp.canonical_name}'."
                    )
                elif cmd.target_type == "memory":
                    # Search and delete memory matching query
                    docs = await self.repository.vector_store.search(
                        "semantic_memories", cmd.query, n_results=1
                    )
                    if docs and docs[0].get("distance", 1.0) < 0.4:
                        await self.repository.delete_cognitive_memory(
                            docs[0]["id"], MemoryType.SEMANTIC
                        )
                        command_responses.append(
                            f"I have forgotten the details matching '{cmd.query}'."
                        )
            elif (
                cmd.action in ("correct", "update")
                and cmd.target_type == "attribute"
                and resp
            ):
                parts = cmd.query.split(":")
                key = parts[1].strip() if len(parts) > 1 else "info"
                await self.identity_service.enrich_attribute(
                    resp.id, key, cmd.update_value or "", 1.0
                )
                command_responses.append(
                    f"I have corrected {resp.canonical_name}'s {key} to '{cmd.update_value}'."
                )

        # 2. Resolve entities & attributes (with conflict resolution)
        resolved_entity_ids = {}
        for ent in extracted.entities:
            # Resolve to canonical ID
            cme_type = map_cme_type_to_identity_type(CMEEntityType(ent.type.value))
            canonical = await self.identity_service.resolve_entity(
                ent.name, cme_type, ent.confidence
            )
            resolved_entity_ids[ent.name] = canonical.id

            # Aliases
            for alias in ent.aliases:
                await self.identity_service.add_alias(canonical.id, alias)

            # Attributes (Conflict resolver)
            for key, val in ent.attributes.items():
                await self.identity_service.enrich_attribute(
                    canonical.id, key, val, ent.confidence
                )

        # 3. Resolve and save relationships in Knowledge Graph
        for rel in extracted.relationships:
            src_id = resolved_entity_ids.get(rel.source_entity_name)
            tgt_id = resolved_entity_ids.get(rel.target_entity_name)

            if not src_id:
                ent = await self.identity_service.find_entity(
                    rel.source_entity_name
                ) or await self.identity_service.find_by_alias(rel.source_entity_name)
                if ent:
                    src_id = ent.id
                else:
                    canonical = await self.identity_service.resolve_entity(
                        rel.source_entity_name, IdentityType.DOCUMENT, 0.5
                    )
                    src_id = canonical.id
            if not tgt_id:
                ent = await self.identity_service.find_entity(
                    rel.target_entity_name
                ) or await self.identity_service.find_by_alias(rel.target_entity_name)
                if ent:
                    tgt_id = ent.id
                else:
                    canonical = await self.identity_service.resolve_entity(
                        rel.target_entity_name, IdentityType.DOCUMENT, 0.5
                    )
                    tgt_id = canonical.id

            if src_id and tgt_id:
                await self.identity_service.add_relationship(
                    src_id, tgt_id, rel.relation_type, rel.weight
                )

        # 4. Consolidate and store cognitive memories (Deduplication Check)
        for mem in extracted.memories:
            await self.consolidator.consolidate_memory(
                memory_type=mem.memory_type,
                content=mem.content,
                importance=mem.importance_score,
                confidence=mem.confidence,
                reason=mem.reason or "Extracted by CME V2",
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
        """Wrapper interface mapping legacy requests into consolidator stores."""
        if (
            not extracted.should_remember
            or not extracted.memory_type
            or not extracted.content
        ):
            return

        await self.consolidator.consolidate_memory(
            memory_type=extracted.memory_type,
            content=extracted.content,
            importance=extracted.importance_score or 5,
            confidence=extracted.confidence or 1.0,
            reason=extracted.reason or "Legacy wrapper mapping",
            event_title=extracted.event_title,
            timeline_date=extracted.timeline_date,
            workflow_name=extracted.workflow_name,
            project_name=extracted.project_name,
        )

    async def get_all_memories(self) -> list[CognitiveMemoryPayload]:
        """Fetch all stored memories with full UI backward compatibility."""
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
        """Delete a cognitive memory."""
        return await self.repository.delete_cognitive_memory(memory_id, memory_type)
