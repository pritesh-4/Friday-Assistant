"""LLM Extraction Agent for Cognitive Memory Engine CME V2."""

import json
from app.core.logging import get_logger
from app.schemas.cme import CMEExtraction
from app.services.llm_service import LLMService

logger = get_logger("memory.extractor")

SYSTEM_PROMPT = """You are F.R.I.D.A.Y.'s Cognitive Memory Engine V2 Extractor.
Your job is to analyze the conversation turn and construct a structured cognitive map of the event.

You must answer the following Four Core Questions in your extraction:
1. "what_happened": Summarize the primary event, action, or fact shared.
2. "who_involved": List names of entities (people, organizations, AI models) involved.
3. "what_changed": Describe what preference, relation, or status was updated (e.g. "User switched favorite editor from VS Code to Cursor").
4. "what_remember": State what long-term fact or concept F.R.I.D.A.Y. should retain.

Extraction Schema Details:
- "should_remember": Set to true if any factual or relational information is being stored or modified.
- "entities": Identify real-world entity nodes mentioned: Name, Type ('person', 'project', 'organization', 'ai_model', 'application', 'product', 'repository', 'concept', 'location', 'tool', 'framework'), list of aliases, and key-value attributes.
- "relationships": Directed graph edges connecting entities. Source name, Target name, relation_type (e.g., 'works_on', 'uses', 'friend_of', 'likes'), and weight (0.0 to 1.0).
- "memories": Long-term factual recollections. Categorize as MemoryType ('semantic', 'episodic', 'procedural', 'project') with importance_score (1-10) and confidence (0.0-1.0).
- "commands": Identify explicit commands to forget or correct (e.g. "Forget that I use Windows", "That is incorrect, my job is Netflix").
  - action: 'forget', 'update', 'correct'
  - target_type: 'entity', 'attribute', 'relationship', 'memory'
  - query: Search string, or "EntityName:attribute_key"
  - update_value: New value if action is update/correct

Provide your response in raw JSON format conforming EXACTLY to the following schema structure:
{
  "should_remember": true | false,
  "what_happened": "...",
  "who_involved": ["..."],
  "what_changed": "...",
  "what_remember": "...",
  "entities": [
    {
      "name": "Bruce",
      "type": "person",
      "aliases": ["Batman"],
      "attributes": {"home": "Wayne Manor", "favorite_tool": "Batarang"},
      "confidence": 1.0
    }
  ],
  "relationships": [
    {
      "source_entity_name": "Bruce",
      "target_entity_name": "Gotham",
      "relation_type": "protects",
      "weight": 1.0
    }
  ],
  "memories": [
    {
      "memory_type": "semantic" | "episodic" | "procedural" | "project",
      "content": "Bruce Wayne protects Gotham City and lives in Wayne Manor",
      "importance_score": 7,
      "confidence": 1.0,
      "event_title": null,
      "timeline_date": null,
      "workflow_name": null,
      "project_name": null,
      "reason": "User declared identity facts"
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


class MemoryExtractor:
    """Invokes LLM provider to extract structured representations and answer memory questions."""

    def __init__(self, llm_service: LLMService) -> None:
        self.llm_service = llm_service

    async def extract(self, user_message: str) -> CMEExtraction | None:
        """Run LLM extraction over the user message."""
        provider = self.llm_service.get_fallback_provider()
        if not provider:
            logger.warning("No LLM provider configured for CME memory extraction.")
            return None

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Extract memory from user input:\n\n{user_message}",
            },
        ]

        try:
            result = await provider.generate_response(messages)
            raw_text = result.content.strip()

            # Trim markdown
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            data = json.loads(raw_text.strip())
            return CMEExtraction(**data)

        except Exception as e:
            logger.error(f"CME memory extraction failed: {e}")
            return None
