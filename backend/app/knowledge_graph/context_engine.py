"""Context Engine: constructs compact, high-signal context packages for LLM prompt enrichment."""

from typing import Any, Dict, List
from app.core.logging import get_logger
from app.identity.schemas import IdentityEntity, IdentityType
from app.knowledge_graph.graph import KnowledgeGraph

logger = get_logger("knowledge_graph.context_engine")


class ContextEngine:
    """Extracts the smallest relevant subgraph and memory set for query context."""

    def __init__(self, graph: KnowledgeGraph, repository: Any) -> None:
        self.graph = graph
        self.repository = repository

    async def build_context(self, query: str, limit: int = 3) -> Dict[str, Any]:
        """
        Identify active entities, preferences, goals, and projects.
        Returns a structured dictionary of relevant context elements.
        """
        logger.info(f"Building context package for query: {query}")

        # 1. Identify seed nodes mentioned in query
        matched_entities = await self.graph.search(
            query=query, search_type="hybrid", limit=5
        )

        seed_ids = [e.id for e in matched_entities]

        # 2. Walk the graph (1-2 hops) to find neighbors and edges
        neighborhood = {}
        if seed_ids:
            try:
                neighborhood = await self.graph.expand(seed_ids[0], hops=2)
            except Exception as e:
                logger.warning(f"Neighborhood expansion failed: {e}")

        nodes: List[IdentityEntity] = neighborhood.get("nodes", matched_entities)
        edges = neighborhood.get("edges", [])

        # 3. Separate categories
        projects = []
        goals = []
        memories = []
        preferences = []
        facts = []

        # Identify USER nodes to extract preferences
        user_ids = []
        try:
            all_entities = await self.repository.get_all_entities()
            for ent in all_entities:
                if hasattr(ent, "type") and ent.type == IdentityType.USER:
                    user_ids.append(ent.id)
        except Exception as e:
            logger.debug(f"Failed to fetch entities for user resolution: {e}")

        # Fetch preferences linked to user (likes, prefers, interested_in)
        for uid in user_ids:
            try:
                user_edges = await self.graph.get_edges_for_node(uid)
                for edge in user_edges:
                    if edge.relation_type in ("likes", "prefers", "interested_in"):
                        target = await self.graph.find(edge.target_id)
                        if not target:
                            target = await self.repository.get_entity(edge.target_id)
                        t_name = target.name if target else edge.target_id
                        pref_str = f"User {edge.relation_type} '{t_name}'"
                        if edge.evidence:
                            pref_str += f" (evidence: {edge.evidence})"
                        preferences.append(pref_str)
            except Exception as e:
                logger.debug(f"Failed to resolve user edges: {e}")

        for node in nodes:
            if (
                node.type == IdentityType.PROJECT
                or node.type == IdentityType.REPOSITORY
            ):
                projects.append(node)
            elif node.type == IdentityType.GOAL or node.type == IdentityType.TASK:
                goals.append(node)
            elif node.type == IdentityType.MEMORY:
                memories.append(node)
            elif node.type in (
                IdentityType.PERSON,
                IdentityType.COMPANY,
                IdentityType.ORGANIZATION,
            ):
                facts.append(node)

        # 4. Format relationships to human-readable strings
        relations_formatted = []
        for edge in edges:
            try:
                src = await self.repository.get_entity(edge.source_id)
                tgt = await self.repository.get_entity(edge.target_id)
                s_name = src.name if src else edge.source_id
                t_name = tgt.name if tgt else edge.target_id
                rel_str = f"'{s_name}' -[{edge.relation_type}]-> '{t_name}' (confidence: {edge.confidence:.2f})"
                relations_formatted.append(rel_str)
            except Exception:
                pass

        # 5. Extract vector-based memories relevant to the query/entities
        semantic_contexts = []
        if seed_ids:
            for entity in matched_entities[:2]:
                try:
                    mem_results = await self.repository.vector_store.search(
                        collection_name="semantic_memories",
                        query=entity.canonical_name,
                        n_results=limit,
                    )
                    for r in mem_results:
                        semantic_contexts.append(r["document"])
                except Exception as e:
                    logger.debug(
                        f"Failed to fetch memories for entity {entity.canonical_name}: {e}"
                    )

        # Dedup semantic contexts
        semantic_contexts = list(set(semantic_contexts))

        return {
            "query": query,
            "relevant_nodes": nodes,
            "relevant_relationships": relations_formatted[:10],
            "relevant_memories": semantic_contexts[:limit],
            "relevant_projects": projects[:limit],
            "relevant_goals": goals[:limit],
            "relevant_preferences": preferences[:limit],
            "relevant_facts": facts[:limit],
        }

    def format_as_markdown(self, context_package: Dict[str, Any]) -> str:
        """Format the context package into a minimized, high-signal markdown block for LLM prompts."""
        lines = ["### CONTEXT ENGINE MODEL INFORMATION"]

        if context_package["relevant_preferences"]:
            lines.append("#### Preferences:")
            for p in context_package["relevant_preferences"]:
                lines.append(f"- {p}")

        if context_package["relevant_projects"]:
            lines.append("#### Active Projects:")
            for p in context_package["relevant_projects"]:
                lines.append(
                    f"- {p.canonical_name}: {p.description or 'No description'}"
                )

        if context_package["relevant_goals"]:
            lines.append("#### Active Goals/Tasks:")
            for g in context_package["relevant_goals"]:
                status_str = f" [{g.status}]" if hasattr(g, "status") else ""
                lines.append(
                    f"- {g.canonical_name}{status_str}: {g.description or 'No description'}"
                )

        if context_package["relevant_relationships"]:
            lines.append("#### Structural Relationships:")
            for r in context_package["relevant_relationships"]:
                lines.append(f"- {r}")

        if context_package["relevant_facts"]:
            lines.append("#### Entity Facts:")
            for f in context_package["relevant_facts"]:
                lines.append(
                    f"- '{f.canonical_name}' ({f.type.value}): {f.description or 'No description'}"
                )

        if context_package["relevant_memories"]:
            lines.append("#### Associated Memories:")
            for m in context_package["relevant_memories"]:
                lines.append(f"- {m}")

        if len(lines) == 1:
            return ""

        return "\n".join(lines)
