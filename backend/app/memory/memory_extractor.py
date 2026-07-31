"""LLM Extraction Agent for Autonomous Memory & Identity System (AMIS)."""

import json
from app.core.logging import get_logger
from app.memory.schemas import AMISExtraction
from app.services.llm_service import LLMService

logger = get_logger("memory.extractor")

SYSTEM_PROMPT = """You are F.R.I.D.A.Y.'s Cognitive Memory and Identity Extractor.
Analyze the user's message and extract structured memory, entity, relationship graph, and command details.

Guidelines:
1. "should_remember": Set to true if any entities, attributes, relationships, memories, or commands are extracted.
2. "entities": Extract real-world objects/people mentioned. Distinguish types: 'person', 'project', 'organization', 'ai_model', 'application', 'product', 'repository', 'concept', 'location', 'tool', 'framework'. Extract attributes (e.g., role, preference, habits) and alternative names/aliases.
3. "relationships": Identify links between entities. Example: ("User", "works_on", "FRIDAY"). Use specific relation_type: 'works_on', 'uses', 'runs_on', 'friend_of', 'colleague_of', 'likes', 'member_of', 'built_with', etc.
4. "memories": Extract distinct memory facts:
   - "semantic": Permanent facts ("User prefers Python").
   - "episodic": Events ("User launched new site"). Needs event_title, timeline_date, details.
   - "procedural": Workflows/instructions ("Use absolute imports"). Needs workflow_name, steps.
   - "project": Project details ("Building FRIDAY using FastAPI"). Needs project_name, content.
   Provide an importance_score (1-10) and confidence (0.0-1.0).
5. "commands": If the user explicitly asks to forget, correct, or update something (e.g., "Forget that I like coffee", "That's wrong, my friend's name is John", "Update my age to 25"), extract it.
   - action: 'forget' or 'update' or 'correct'
   - target_type: 'entity' or 'attribute' or 'relationship' or 'memory'
   - query: The text search query to locate the item (for attributes, use "EntityName:attribute_key", e.g., "User:age")
   - update_value: The new value for updates/corrections.

Output JSON ONLY, conforming EXACTLY to this schema structure:
{
  "should_remember": true | false,
  "entities": [
    {
      "name": "Alex",
      "type": "person",
      "aliases": ["Alexander"],
      "attributes": {"likes": "Marvel movies", "job": "Developer"},
      "confidence": 1.0
    }
  ],
  "relationships": [
    {
      "source_entity_name": "Alex",
      "target_entity_name": "Marvel",
      "relation_type": "likes",
      "weight": 1.0
    }
  ],
  "memories": [
    {
      "memory_type": "semantic" | "episodic" | "procedural" | "project",
      "content": "Alex likes Marvel movies and is a Developer",
      "importance_score": 5,
      "confidence": 1.0,
      "event_title": null,
      "timeline_date": null,
      "workflow_name": null,
      "project_name": null,
      "reason": "User declared friend preferences"
    }
  ],
  "commands": [
    {
      "action": "forget" | "update" | "correct",
      "target_type": "entity" | "attribute" | "relationship" | "memory",
      "query": "search query or EntityName:attribute_key",
      "update_value": "new value if update",
      "details": null
    }
  ]
}
"""


class AMISMemeoryExtractor:
    """Agent that runs LLM to extract structures (entities, relations, commands) from conversation."""

    def __init__(self, llm_service: LLMService) -> None:
        self.llm_service = llm_service

    async def extract(self, user_message: str) -> AMISExtraction | None:
        """Analyze message via LLM and return structured extraction schema."""
        provider = self.llm_service.get_fallback_provider()
        if not provider:
            logger.warning("No LLM provider available for AMIS memory extraction.")
            return None

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Extract memory from this message:\n\n{user_message}",
            },
        ]

        try:
            result = await provider.generate_response(messages)
            raw_text = result.content.strip()

            # Clean JSON markdown blocks
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            data = json.loads(raw_text.strip())
            return AMISExtraction(**data)

        except Exception as e:
            logger.error(f"Failed to extract memory via LLM: {e}")
            return None
