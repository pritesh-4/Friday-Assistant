"""Recognition agent: parses conversation text using LLM to extract entities and relations."""

import json
from app.core.logging import get_logger
from app.identity.schemas import IdentityExtraction
from app.services.llm_service import LLMService

logger = get_logger("identity.recognizer")

SYSTEM_PROMPT = """You are F.R.I.D.A.Y.'s Identity Recognition Engine.
Your job is to identify every entity and relationship mentioned in the user message.

Supported Entity Types:
- user, person, friend, family, colleague, organization, company, project, repository, technology, framework, api, ai_model, application, book, movie, place, device, event, task, goal, file, document

For each entity, extract:
1. "name": Canonical name of the entity.
2. "type": One of the supported types listed above.
3. "aliases": Nicknames, abbreviations, or alternate labels.
4. "attributes": Key-value pairs of traits or preferences.
5. "confidence": Value from 0.0 to 1.0.
6. "description": Brief context description if available.

For each relationship, extract:
1. "source_name": Source entity name.
2. "target_name": Target entity name.
3. "relation_type": Edge relationship type (e.g. 'friend_of', 'works_on', 'owns', 'uses', 'created', 'member_of', 'located_in', 'depends_on', 'likes', 'prefers').
4. "confidence": Value from 0.0 to 1.0.
5. "evidence": Direct quote or context sentence supporting this link.

Response Schema Format (Raw JSON):
{
  "should_register": true | false,
  "entities": [
    {
      "name": "...",
      "type": "...",
      "aliases": [...],
      "attributes": {...},
      "confidence": 1.0,
      "description": "..."
    }
  ],
  "relationships": [
    {
      "source_name": "...",
      "target_name": "...",
      "relation_type": "...",
      "confidence": 1.0,
      "evidence": "..."
    }
  ]
}
"""


class IdentityRecognizer:
    """Uses LLM to recognize entity profiles and relationship edges in conversation turns."""

    def __init__(self, llm_service: LLMService) -> None:
        self.llm_service = llm_service

    async def recognize(self, text: str) -> IdentityExtraction | None:
        """Call LLM extraction over message text."""
        provider = self.llm_service.get_fallback_provider()
        if not provider:
            logger.warning("No LLM provider configured for Identity Engine recognizer.")
            return None

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Extract identities and relationships from:\n\n{text}",
            },
        ]

        try:
            result = await provider.generate_response(messages)
            raw_text = result.content.strip()

            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            data = json.loads(raw_text.strip())
            return IdentityExtraction(**data)

        except Exception as e:
            logger.error(f"Identity recognition failed: {e}")
            return None
