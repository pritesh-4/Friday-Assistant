"""Persistence and retrieval service for long-term cognitive memories."""

from app.core.logging import get_logger
from app.db.database import database
from app.db.vector_store import vector_store
from app.schemas.memory import (
    CognitiveMemoryPayload,
    ExtractedMemory,
    MemoryMetadata,
    MemoryType,
)
from app.utils.helpers import generate_uuid, get_utc_now

logger = get_logger(__name__)


class CognitiveMemoryService:
    """Persist and retrieve cognitive user memories using SQL + Vector search."""

    async def save_extracted_memory(self, extracted: ExtractedMemory) -> None:
        """Takes an LLM-extracted memory, deduplicates it, and stores it in SQL + Vector DB."""
        if not extracted.should_remember or not extracted.memory_type:
            return

        memory_id = generate_uuid()
        now = get_utc_now().isoformat()
        
        # Deduplication check via Vector DB could be added here
        # (e.g. search for highly similar facts, if > 0.9 similarity, update instead of insert)

        collection_name = f"{extracted.memory_type.value}_memories"
        
        # 1. Save to SQLite specific table
        if extracted.memory_type == MemoryType.SEMANTIC:
            if not extracted.content:
                return
            await database.execute(
                "INSERT INTO semantic_memories (id, fact, confidence, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (memory_id, extracted.content, extracted.confidence or 1.0, now, now)
            )
            # 2. Save to Vector DB
            await vector_store.add_memory(
                collection_name=collection_name,
                memory_id=memory_id,
                text=extracted.content,
                metadata={"type": "semantic"}
            )
            
        elif extracted.memory_type == MemoryType.EPISODIC:
            if not extracted.event_title or not extracted.content:
                return
            await database.execute(
                "INSERT INTO episodic_memories (id, event_title, timeline_date, details, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (memory_id, extracted.event_title, extracted.timeline_date, extracted.content, now, now)
            )
            await vector_store.add_memory(
                collection_name=collection_name,
                memory_id=memory_id,
                text=f"{extracted.event_title} on {extracted.timeline_date}: {extracted.content}",
                metadata={"type": "episodic"}
            )

        elif extracted.memory_type == MemoryType.PROCEDURAL:
            if not extracted.workflow_name or not extracted.content:
                return
            await database.execute(
                "INSERT INTO procedural_memories (id, workflow_name, steps, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (memory_id, extracted.workflow_name, extracted.content, now, now)
            )
            await vector_store.add_memory(
                collection_name=collection_name,
                memory_id=memory_id,
                text=f"{extracted.workflow_name}: {extracted.content}",
                metadata={"type": "procedural"}
            )
            
        elif extracted.memory_type == MemoryType.PROJECT:
            if not extracted.project_name or not extracted.content:
                return
            # Check if project exists
            project = await database.fetch_one("SELECT id FROM projects WHERE lower(name) = ?", (extracted.project_name.lower(),))
            if not project:
                project_id = generate_uuid()
                await database.execute(
                    "INSERT INTO projects (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (project_id, extracted.project_name, now, now)
                )
            else:
                project_id = project["id"]
                
            await database.execute(
                "INSERT INTO project_memories (id, project_id, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (memory_id, project_id, extracted.content, now, now)
            )
            await vector_store.add_memory(
                collection_name=collection_name,
                memory_id=memory_id,
                text=f"Project {extracted.project_name}: {extracted.content}",
                metadata={"type": "project", "project_id": project_id}
            )

        # 3. Save Metadata
        await database.execute(
            """
            INSERT INTO memory_metadata (id, memory_type, memory_id, importance_score, reason, retrieval_count, created_at)
            VALUES (?, ?, ?, ?, ?, 0, ?)
            """,
            (generate_uuid(), extracted.memory_type.value, memory_id, extracted.importance_score or 5, extracted.reason or "", now)
        )
        logger.info(f"Saved {extracted.memory_type.value} memory: {memory_id}")


    async def retrieve_relevant_memories(self, query: str, limit_per_type: int = 3) -> dict[str, list[dict]]:
        """Retrieve most relevant memories across types using Semantic Search."""
        results = {
            "semantic": [],
            "episodic": [],
            "procedural": [],
            "project": []
        }
        
        # Search all collections
        for mem_type in results.keys():
            collection = f"{mem_type}_memories"
            docs = await vector_store.search(collection, query, n_results=limit_per_type)
            results[mem_type] = docs
            
            # Update observability: increment retrieval_count
            for doc in docs:
                await database.execute(
                    "UPDATE memory_metadata SET retrieval_count = retrieval_count + 1 WHERE memory_id = ?",
                    (doc["id"],)
                )
                
        return results

    async def get_all_memories(self) -> list[CognitiveMemoryPayload]:
        """Fetch all memories for the UI Manager."""
        payloads = []
        
        metadata_rows = await database.fetch_all("SELECT * FROM memory_metadata ORDER BY created_at DESC")
        for row in metadata_rows:
            mem_type = row["memory_type"]
            mem_id = row["memory_id"]
            
            content = ""
            updated_at = None
            
            if mem_type == "semantic":
                mem = await database.fetch_one("SELECT fact, updated_at FROM semantic_memories WHERE id = ?", (mem_id,))
                if mem:
                    content = mem["fact"]
                    updated_at = mem["updated_at"]
            elif mem_type == "episodic":
                mem = await database.fetch_one("SELECT event_title, timeline_date, details, updated_at FROM episodic_memories WHERE id = ?", (mem_id,))
                if mem:
                    content = f"{mem['event_title']} ({mem['timeline_date']}): {mem['details']}"
                    updated_at = mem["updated_at"]
            elif mem_type == "procedural":
                mem = await database.fetch_one("SELECT workflow_name, steps, updated_at FROM procedural_memories WHERE id = ?", (mem_id,))
                if mem:
                    content = f"{mem['workflow_name']}: {mem['steps']}"
                    updated_at = mem["updated_at"]
            elif mem_type == "project":
                mem = await database.fetch_one("SELECT project_id, content, updated_at FROM project_memories WHERE id = ?", (mem_id,))
                if mem:
                    project = await database.fetch_one("SELECT name FROM projects WHERE id = ?", (mem["project_id"],))
                    pname = project["name"] if project else "Unknown"
                    content = f"[{pname}] {mem['content']}"
                    updated_at = mem["updated_at"]
                    
            if content:
                payloads.append(CognitiveMemoryPayload(
                    id=mem_id,
                    memory_type=MemoryType(mem_type),
                    content=content,
                    metadata=MemoryMetadata(**dict(row)),
                    created_at=row["created_at"],
                    updated_at=updated_at
                ))
                
        return payloads

    async def delete_memory(self, memory_id: str, memory_type: MemoryType) -> bool:
        """Delete a memory completely from SQL and Vector DB."""
        collection_name = f"{memory_type.value}_memories"
        table_name = collection_name
        
        # 1. Delete SQL Metadata
        await database.execute("DELETE FROM memory_metadata WHERE memory_id = ?", (memory_id,))
        
        # 2. Delete SQL Record
        deleted = await database.execute(f"DELETE FROM {table_name} WHERE id = ?", (memory_id,))
        
        # 3. Delete Vector DB Record
        if deleted:
            await vector_store.delete_memory(collection_name, memory_id)
            return True
        return False
