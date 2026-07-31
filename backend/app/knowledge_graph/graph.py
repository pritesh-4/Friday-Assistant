"""Knowledge Graph structure: manages graph node and link persistence and query algorithms."""

import json
from datetime import datetime
from typing import Any, Optional

from app.core.logging import get_logger
from app.utils.helpers import generate_uuid, get_utc_now
from app.schemas.cme import CMERelationship
from app.identity.schemas import IdentityEntity, IdentityRelationship, IdentityType
from app.identity.repository import IdentityRepository

logger = get_logger("knowledge_graph.graph")


class KnowledgeGraph:
    """Manages semantic links between entity nodes and implements advanced graph query APIs."""

    def __init__(self, repository: Any) -> None:
        self.repository = repository
        self.db = repository.db
        # local IdentityRepository helper to reuse SQL mapping/saving
        self.identity_repo = IdentityRepository(self.db)

    # ── Node Operations ────────────────────────────────────────────────────────

    async def create_node(self, node: IdentityEntity) -> IdentityEntity:
        """Create and register a new canonical entity node, and index it in ChromaDB."""
        await self.identity_repo.save_entity(node)
        await self.identity_repo.add_entity_alias(node.id, node.canonical_name)
        
        # Save all other aliases
        for alias in node.aliases:
            if alias.strip().lower() != node.canonical_name.strip().lower():
                await self.identity_repo.add_entity_alias(node.id, alias)
        
        # Index node in ChromaDB vector store for semantic search
        try:
            text_content = f"{node.canonical_name} {node.description or ''}"
            await self.repository.vector_store.add_memory(
                collection_name="entities",
                memory_id=node.id,
                text=text_content,
                metadata={"type": node.type.value, "name": node.canonical_name}
            )
        except Exception as e:
            logger.warning(f"Failed to add entity {node.id} to vector store: {e}")
            
        logger.info(f"Created graph node: {node.id} ({node.canonical_name})")
        return node

    async def delete_node(self, node_id: str) -> None:
        """Delete a node and all cascading edges."""
        await self.identity_repo.delete_entity(node_id)
        try:
            await self.repository.vector_store.delete_memory(
                collection_name="entities",
                memory_id=node_id
            )
        except Exception as e:
            logger.warning(f"Failed to delete entity {node_id} from vector store: {e}")
        logger.info(f"Deleted graph node: {node_id}")

    async def update_node(self, node_id: str, updates: dict[str, Any]) -> Optional[IdentityEntity]:
        """Update node properties and synchronize with vector store."""
        entity = await self.identity_repo.get_entity(node_id)
        if not entity:
            return None
        
        # Apply updates
        for k, v in updates.items():
            if hasattr(entity, k) and k not in ("id", "type"):
                setattr(entity, k, v)
                
        entity.updated_at = get_utc_now()
        entity.version += 1
        await self.identity_repo.save_entity(entity)
        
        # Save change log history
        editor = updates.get("editor", "system")
        reason = updates.get("reason", "Property update")
        await self.identity_repo.save_history(entity.id, entity.version, editor, reason)
        
        # Sync with ChromaDB
        try:
            text_content = f"{entity.canonical_name} {entity.description or ''}"
            await self.repository.vector_store.update_memory(
                collection_name="entities",
                memory_id=entity.id,
                text=text_content,
                metadata={"type": entity.type.value, "name": entity.canonical_name}
            )
        except Exception as e:
            logger.warning(f"Failed to update vector store for entity {node_id}: {e}")
            
        logger.info(f"Updated graph node: {node_id}")
        return entity

    async def merge_nodes(
        self, source_id: str, target_id: str, editor: str = "system", reason: str = "Merge duplicate nodes"
    ) -> None:
        """Merge a duplicate source node into target node, rewriting all relationships."""
        if source_id == target_id:
            return
            
        source = await self.identity_repo.get_entity(source_id)
        target = await self.identity_repo.get_entity(target_id)
        if not source or not target:
            raise ValueError(f"Nodes must exist to merge. Source: {source_id}, Target: {target_id}")
            
        # 1. Fetch source details before deletion to avoid DB cascade wipeouts
        src_aliases = await self.identity_repo.get_entity_aliases(source_id)
        relationships = await self.identity_repo.get_relationships(source_id)
        
        # 2. Clean up/delete source node first
        await self.delete_node(source_id)
        
        # 3. Merge properties into target
        tgt_aliases = await self.identity_repo.get_entity_aliases(target_id)
        merged_aliases = list(set(src_aliases + tgt_aliases + [source.canonical_name, target.canonical_name]))
        merged_tags = list(set(source.tags + target.tags))
        merged_metadata = {**source.metadata, **target.metadata}
        
        description = target.description
        if source.description and source.description not in (description or ""):
            description = f"{description or ''}\nMerged info: {source.description}".strip()
            
        confidence = max(source.confidence, target.confidence)
        source_history = target.source_history + source.source_history + [
            f"Merged source node {source_id} into target at {get_utc_now().isoformat()}"
        ]
        
        target.aliases = merged_aliases
        target.tags = merged_tags
        target.metadata = merged_metadata
        target.description = description
        target.confidence = confidence
        target.source_history = source_history
        target.version += 1
        target.updated_at = get_utc_now()
        
        await self.identity_repo.save_entity(target)
        for alias in merged_aliases:
            await self.identity_repo.add_entity_alias(target_id, alias)
            
        await self.identity_repo.save_history(target_id, target.version, editor, reason)
        
        # 4. Re-route and save all relationships
        for rel in relationships:
            new_source_id = target_id if rel.source_id == source_id else rel.source_id
            new_target_id = target_id if rel.target_id == source_id else rel.target_id
            
            # Avoid self-loops
            if new_source_id == new_target_id:
                continue
                
            await self.merge_edge(
                source_id=new_source_id,
                target_id=new_target_id,
                relation_type=rel.relation_type,
                weight=rel.weight,
                confidence=rel.confidence,
                evidence=f"{rel.evidence or ''} (Inherited from merged node {source_id})".strip(),
                direction=rel.direction
            )
            
        logger.info(f"Successfully merged node {source_id} into {target_id}")

    # ── Edge Operations ────────────────────────────────────────────────────────

    async def create_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        weight: float = 1.0,
        confidence: float = 1.0,
        evidence: Optional[str] = None,
        direction: str = "directed"
    ) -> None:
        """Insert a directed edge link."""
        if source_id == target_id:
            return
            
        relationship = IdentityRelationship(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type.strip().lower(),
            weight=weight,
            confidence=confidence,
            evidence=evidence,
            direction=direction,
            timestamp=get_utc_now()
        )
        await self.identity_repo.save_relationship(relationship)
        logger.debug(f"Added link: {source_id} -[{relation_type}]-> {target_id}")

    async def add_edge(
        self, source_id: str, target_id: str, relation_type: str, weight: float = 1.0
    ) -> None:
        """Insert or strengthen a directed edge link (backward compatibility)."""
        await self.create_edge(source_id, target_id, relation_type, weight=weight)

    async def delete_edge(self, source_id: str, target_id: str, relation_type: str) -> None:
        """Remove a relationship edge."""
        await self.db.execute(
            "DELETE FROM relationships WHERE source_id = ? AND target_id = ? AND relation_type = ?",
            (source_id, target_id, relation_type.strip().lower())
        )
        logger.debug(f"Deleted edge: {source_id} -[{relation_type}]-> {target_id}")

    async def update_edge(self, source_id: str, target_id: str, relation_type: str, updates: dict[str, Any]) -> None:
        """Update an existing edge link's properties."""
        now = get_utc_now().isoformat()
        set_clauses = []
        params = []
        for k, v in updates.items():
            if k in ("weight", "confidence", "evidence", "direction"):
                set_clauses.append(f"{k} = ?")
                params.append(v)
        if not set_clauses:
            return
            
        set_clauses.append("updated_at = ?")
        params.append(now)
        
        params.extend([source_id, target_id, relation_type.strip().lower()])
        query = f"UPDATE relationships SET {', '.join(set_clauses)} WHERE source_id = ? AND target_id = ? AND relation_type = ?"
        await self.db.execute(query, params)

    async def merge_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        weight: float = 1.0,
        confidence: float = 1.0,
        evidence: Optional[str] = None,
        direction: str = "directed"
    ) -> None:
        """Strengthen edge weight, merge confidence, and update evidence for a link."""
        rel_clean = relation_type.strip().lower()
        existing = await self.db.fetch_one(
            "SELECT id, weight, confidence, evidence FROM relationships WHERE source_id = ? AND target_id = ? AND relation_type = ?",
            (source_id, target_id, rel_clean)
        )
        if existing:
            new_weight = min(existing["weight"] + weight, 5.0)
            new_confidence = max(existing["confidence"], confidence)
            merged_evidence = existing["evidence"] or ""
            if evidence and evidence not in merged_evidence:
                merged_evidence = f"{merged_evidence}\n{evidence}".strip()
            
            await self.update_edge(
                source_id,
                target_id,
                rel_clean,
                {
                    "weight": new_weight,
                    "confidence": new_confidence,
                    "evidence": merged_evidence,
                    "direction": direction
                }
            )
        else:
            await self.create_edge(
                source_id, target_id, rel_clean, weight=weight, confidence=confidence, evidence=evidence, direction=direction
            )

    # ── Compatibility getters ──────────────────────────────────────────────────

    async def get_edges_for_node(self, entity_id: str) -> list[CMERelationship]:
        """Fetch all links touching this node mapped to CMERelationship."""
        rows = await self.db.fetch_all(
            "SELECT * FROM relationships WHERE source_id = ? OR target_id = ?",
            (entity_id, entity_id),
        )
        return [
            CMERelationship(
                id=row["id"],
                source_id=row["source_id"],
                target_id=row["target_id"],
                relation_type=row["relation_type"],
                weight=row["weight"],
                confidence=row.get("confidence") or 1.0,
                evidence=row.get("evidence"),
                direction=row.get("direction") or "directed",
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            for row in rows
        ]

    async def get_all_edges(self) -> list[CMERelationship]:
        """Fetch all links in the graph mapped to CMERelationship."""
        rows = await self.db.fetch_all("SELECT * FROM relationships")
        return [
            CMERelationship(
                id=row["id"],
                source_id=row["source_id"],
                target_id=row["target_id"],
                relation_type=row["relation_type"],
                weight=row["weight"],
                confidence=row.get("confidence") or 1.0,
                evidence=row.get("evidence"),
                direction=row.get("direction") or "directed",
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            for row in rows
        ]

    # ── Advanced Query APIs ────────────────────────────────────────────────────

    async def find(self, name: str) -> Optional[IdentityEntity]:
        """Locates entity by primary canonical name or aliases."""
        return await self.identity_repo.get_entity_by_name_or_alias(name)

    async def traverse(self, start_id: str, max_hops: int = 2) -> dict[str, float]:
        """BFS traversal from start node, returning a relevance weight map decaying with hop count."""
        relevance_map: dict[str, float] = {start_id: 1.0}
        queue = [(start_id, 0)]
        
        edges = await self.get_all_edges()
        adj: dict[str, list[str]] = {}
        for edge in edges:
            adj.setdefault(edge.source_id, []).append(edge.target_id)
            if edge.direction != "directed":
                adj.setdefault(edge.target_id, []).append(edge.source_id)
            else:
                # Still traverse backwards for general hop relevance, but at lower default weight
                adj.setdefault(edge.target_id, []).append(edge.source_id)
                
        head = 0
        while head < len(queue):
            node_id, hops = queue[head]
            head += 1
            if hops >= max_hops:
                continue
                
            neighbors = adj.get(node_id, [])
            for neighbor in neighbors:
                if neighbor not in relevance_map:
                    next_hops = hops + 1
                    multiplier = 1.0 / (2**next_hops)
                    relevance_map[neighbor] = multiplier
                    queue.append((neighbor, next_hops))
                    
        return relevance_map

    async def expand(self, node_id: str, hops: int = 1) -> dict[str, Any]:
        """Expand node neighborhood up to hops, returning nodes and edges."""
        relevance_map = await self.traverse(node_id, max_hops=hops)
        expanded_ids = list(relevance_map.keys())
        return await self.subgraph(expanded_ids)

    async def shortest_path(self, start_id: str, end_id: str) -> Optional[list[str]]:
        """Find the shortest path of node IDs from start_id to end_id."""
        if start_id == end_id:
            return [start_id]
            
        edges = await self.get_all_edges()
        adj: dict[str, list[str]] = {}
        for edge in edges:
            adj.setdefault(edge.source_id, []).append(edge.target_id)
            adj.setdefault(edge.target_id, []).append(edge.source_id)
            
        queue = [[start_id]]
        visited = {start_id}
        
        head = 0
        while head < len(queue):
            path = queue[head]
            head += 1
            node = path[-1]
            if node == end_id:
                return path
                
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = list(path) + [neighbor]
                    queue.append(new_path)
        return None

    async def neighbours(self, node_id: str) -> list[dict[str, Any]]:
        """Return immediate direct and indirect neighbors with connecting relationships."""
        edges = await self.get_edges_for_node(node_id)
        res = []
        for edge in edges:
            neighbor_id = edge.target_id if edge.source_id == node_id else edge.source_id
            neighbor = await self.identity_repo.get_entity(neighbor_id)
            if neighbor:
                res.append({
                    "node": neighbor,
                    "relationship": edge
                })
        return res

    async def reason(self, start_id: str, path: list[str]) -> list[IdentityEntity]:
        """Infers target nodes by following a transitive relationship chain."""
        if not path:
            entity = await self.identity_repo.get_entity(start_id)
            return [entity] if entity else []
            
        current_ids = {start_id}
        edges = await self.get_all_edges()
        
        for rel_type in path:
            next_ids = set()
            rel_type_lower = rel_type.strip().lower()
            for edge in edges:
                if edge.source_id in current_ids and edge.relation_type == rel_type_lower:
                    next_ids.add(edge.target_id)
            current_ids = next_ids
            if not current_ids:
                break
                
        res = []
        for nid in current_ids:
            entity = await self.identity_repo.get_entity(nid)
            if entity:
                res.append(entity)
        return res

    async def subgraph(self, node_ids: list[str]) -> dict[str, Any]:
        """Extract the connecting nodes and relationship edges for a subset of node IDs."""
        nodes = []
        for nid in node_ids:
            node = await self.identity_repo.get_entity(nid)
            if node:
                nodes.append(node)
                
        edges = await self.get_all_edges()
        sub_edges = []
        node_set = set(node_ids)
        for edge in edges:
            if edge.source_id in node_set and edge.target_id in node_set:
                sub_edges.append(edge)
                
        return {"nodes": nodes, "edges": sub_edges}

    async def explain(self, start_id: str, end_id: str) -> str:
        """Generate a natural language explanation of the path connecting two nodes."""
        path = await self.shortest_path(start_id, end_id)
        start_node = await self.identity_repo.get_entity(start_id)
        end_node = await self.identity_repo.get_entity(end_id)
        s_name = start_node.canonical_name if start_node else start_id
        e_name = end_node.canonical_name if end_node else end_id
        
        if not path:
            return f"No connection path was found between '{s_name}' and '{e_name}'."
            
        all_edges = await self.get_all_edges()
        steps = []
        for i in range(len(path) - 1):
            u_id = path[i]
            v_id = path[i+1]
            u_node = await self.identity_repo.get_entity(u_id)
            v_node = await self.identity_repo.get_entity(v_id)
            u_name = u_node.canonical_name if u_node else u_id
            v_name = v_node.canonical_name if v_node else v_id
            
            rel_str = "is connected to"
            for edge in all_edges:
                if edge.source_id == u_id and edge.target_id == v_id:
                    rel_str = f"{edge.relation_type}"
                    break
                elif edge.target_id == u_id and edge.source_id == v_id:
                    rel_str = f"is connected via {edge.relation_type} from"
                    break
            steps.append((u_name, rel_str, v_name))
            
        sentence_parts = []
        for u, r, v in steps:
            if not sentence_parts:
                sentence_parts.append(f"'{u}' {r} '{v}'")
            else:
                sentence_parts.append(f"which {r} '{v}'")
                
        return ", ".join(sentence_parts) + "."

    async def search(
        self,
        query: Optional[str] = None,
        search_type: str = "hybrid",
        entity_type: Optional[IdentityType] = None,
        tag: Optional[str] = None,
        metadata_filters: Optional[dict] = None,
        limit: int = 20
    ) -> list[IdentityEntity]:
        """
        Search graph nodes with multiple search styles: exact, semantic, relationship, subgraph, expansion, hybrid.
        """
        matched_nodes: list[IdentityEntity] = []
        s_type = search_type.lower().strip()
        
        # Helper to scan if query contains known entity name/alias as a substring
        substring_matched: list[IdentityEntity] = []
        if query:
            q_lower = query.lower()
            all_ents = await self.identity_repo.get_all_entities()
            for ent in all_ents:
                aliases = await self.identity_repo.get_entity_aliases(ent.id)
                for name in [ent.canonical_name, ent.display_name] + aliases:
                    if name:
                        name_clean = name.strip().lower()
                        if len(name_clean) > 2 and name_clean in q_lower:
                            substring_matched.append(ent)
                            break
        
        if s_type == "exact":
            if query:
                entity = await self.identity_repo.get_entity_by_name_or_alias(query)
                if entity:
                    matched_nodes = [entity]
                else:
                    matched_nodes = substring_matched
            else:
                matched_nodes = await self.identity_repo.search_registry(
                    entity_type=entity_type, tag=tag, metadata_filters=metadata_filters, limit=limit
                )
                
        elif s_type == "semantic":
            if query:
                try:
                    vector_results = await self.repository.vector_store.search(
                        collection_name="entities",
                        query=query,
                        n_results=limit
                    )
                    for res in vector_results:
                        entity = await self.identity_repo.get_entity(res["id"])
                        if entity:
                            matched_nodes.append(entity)
                except Exception as e:
                    logger.warning(f"ChromaDB semantic search failed: {e}")
                    matched_nodes = await self.identity_repo.search_entities(query)
                
                # Merge in substring matches if empty
                if not matched_nodes:
                    matched_nodes = substring_matched
            else:
                matched_nodes = await self.identity_repo.search_registry(
                    entity_type=entity_type, tag=tag, metadata_filters=metadata_filters, limit=limit
                )
                
        elif s_type == "relationship":
            if query:
                rel_type = query.strip().lower()
                rows = await self.db.fetch_all(
                    "SELECT DISTINCT source_id, target_id FROM relationships WHERE relation_type = ?",
                    (rel_type,)
                )
                node_ids = set()
                for r in rows:
                    node_ids.add(r["source_id"])
                    node_ids.add(r["target_id"])
                for nid in node_ids:
                    entity = await self.identity_repo.get_entity(nid)
                    if entity:
                        matched_nodes.append(entity)
                        
        elif s_type == "subgraph":
            seeds = await self.identity_repo.search_registry(
                query=query, entity_type=entity_type, tag=tag, metadata_filters=metadata_filters, limit=limit
            )
            if not seeds and substring_matched:
                seeds = substring_matched
            node_ids = [s.id for s in seeds]
            subg = await self.subgraph(node_ids)
            matched_nodes = subg["nodes"]
            
        elif s_type == "entity_expansion":
            seeds = await self.identity_repo.search_registry(
                query=query, entity_type=entity_type, tag=tag, metadata_filters=metadata_filters, limit=1
            )
            if not seeds and substring_matched:
                seeds = substring_matched[:1]
            if seeds:
                node_id = seeds[0].id
                neighborhood = await self.expand(node_id, hops=1)
                matched_nodes = neighborhood["nodes"]
                
        else:  # hybrid
            exact_nodes = []
            if query:
                entity = await self.identity_repo.get_entity_by_name_or_alias(query)
                if entity:
                    exact_nodes.append(entity)
                fuzzy = await self.identity_repo.search_entities(query)
                exact_nodes.extend(fuzzy)
                exact_nodes.extend(substring_matched)
                
                try:
                    vector_results = await self.repository.vector_store.search(
                        collection_name="entities",
                        query=query,
                        n_results=limit
                    )
                    for res in vector_results:
                        entity = await self.identity_repo.get_entity(res["id"])
                        if entity:
                            exact_nodes.append(entity)
                except Exception as e:
                    logger.debug(f"ChromaDB search ignored: {e}")
                    
            seen = set()
            for node in exact_nodes:
                if node.id in seen:
                    continue
                seen.add(node.id)
                if entity_type and node.type != entity_type:
                    continue
                if tag and tag.lower() not in [t.lower() for t in node.tags]:
                    continue
                if metadata_filters:
                    match = True
                    for k, v in metadata_filters.items():
                        if node.metadata.get(k) != v:
                            match = False
                            break
                    if not match:
                        continue
                matched_nodes.append(node)
                
            if not matched_nodes:
                matched_nodes = await self.identity_repo.search_registry(
                    query=query, entity_type=entity_type, tag=tag, metadata_filters=metadata_filters, limit=limit
                )
                
        return matched_nodes[:limit]
