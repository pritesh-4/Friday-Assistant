"""Vector database integration using ChromaDB for cognitive memory."""

import asyncio
from pathlib import Path

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from app.core.logging import get_logger
from app.db.database import database

_log = get_logger("db.vector_store")


class VectorStore:
    """Manages the ChromaDB client and memory collections."""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path).parent / "chroma_db"
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        _log.info(f"Initializing ChromaDB at {self.db_path}")
        
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Use default MiniLM embedding function (runs locally)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        # Initialize collections
        self.semantic = self.client.get_or_create_collection(
            name="semantic_memories",
            embedding_function=self.embedding_fn
        )
        self.episodic = self.client.get_or_create_collection(
            name="episodic_memories",
            embedding_function=self.embedding_fn
        )
        self.procedural = self.client.get_or_create_collection(
            name="procedural_memories",
            embedding_function=self.embedding_fn
        )
        self.project = self.client.get_or_create_collection(
            name="project_memories",
            embedding_function=self.embedding_fn
        )
        
    async def add_memory(self, collection_name: str, memory_id: str, text: str, metadata: dict | None = None) -> None:
        """Add a memory to the vector store asynchronously."""
        def operation():
            collection = self.client.get_collection(collection_name)
            collection.add(
                documents=[text],
                metadatas=[metadata] if metadata else None,
                ids=[memory_id]
            )
        await asyncio.to_thread(operation)
        
    async def update_memory(self, collection_name: str, memory_id: str, text: str, metadata: dict | None = None) -> None:
        """Update an existing memory in the vector store."""
        def operation():
            collection = self.client.get_collection(collection_name)
            collection.update(
                documents=[text],
                metadatas=[metadata] if metadata else None,
                ids=[memory_id]
            )
        await asyncio.to_thread(operation)
        
    async def delete_memory(self, collection_name: str, memory_id: str) -> None:
        """Delete a memory from the vector store."""
        def operation():
            collection = self.client.get_collection(collection_name)
            collection.delete(ids=[memory_id])
        await asyncio.to_thread(operation)

    async def search(self, collection_name: str, query: str, n_results: int = 5, where: dict | None = None) -> list[dict]:
        """Search for relevant memories in a specific collection."""
        def operation():
            collection = self.client.get_collection(collection_name)
            # collection.count() checks if we have any data to avoid errors on empty search
            if collection.count() == 0:
                return []
                
            results = collection.query(
                query_texts=[query],
                n_results=min(n_results, collection.count()),
                where=where
            )
            
            # Reformat ChromaDB output to a list of dicts
            formatted_results = []
            if results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    formatted_results.append({
                        "id": results["ids"][0][i],
                        "document": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0.0
                    })
            return formatted_results
            
        return await asyncio.to_thread(operation)


vector_store = VectorStore(str(database.path))
