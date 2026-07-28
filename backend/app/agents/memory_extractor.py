"""Agent for extracting and classifying long-term cognitive memories."""

import json

from app.core.logging import get_logger
from app.schemas.memory import ExtractedMemory
from app.services.llm_service import LLMService

_log = get_logger("agents.memory_extractor")

SYSTEM_PROMPT = """You are F.R.I.D.A.Y.'s Cognitive Memory Extractor.
Your job is to analyze the user's latest message and extract any information that should be stored in long-term memory.
Do NOT extract ephemeral chat, conversational pleasantries, or information already known.
If no long-term memory should be extracted, output {"should_remember": false}.

Memory Types:
1. "semantic": Facts about the user (e.g. "User likes dark mode", "User is a student", "User prefers Python").
2. "episodic": Events (e.g. "User started learning Rust today", "User fixed a bug"). Needs an event_title, timeline_date (approximate), and details.
3. "procedural": Workflows or instructions on how to do things (e.g. "Always write tests first", "Use absolute imports"). Needs a workflow_name and steps.
4. "project": Specifics about a project (e.g. "We are building FRIDAY using FastAPI"). Needs a project_name and content.

Provide an importance_score from 1-10 (10 being critical core identity/preference, 1 being trivial).
Provide a reason for storing this memory.

Output JSON EXACTLY matching this schema:
{
  "should_remember": true | false,
  "memory_type": "semantic" | "episodic" | "procedural" | "project" | null,
  "importance_score": 1-10 | null,
  "reason": "..." | null,
  "content": "..." | null,          // For semantic/project
  "event_title": "..." | null,      // For episodic
  "timeline_date": "..." | null,    // For episodic
  "workflow_name": "..." | null,    // For procedural
  "project_name": "..." | null,     // For project
  "confidence": 0.0-1.0 | null      // For semantic
}
"""

class MemoryExtractor:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def extract_memory(self, user_message: str) -> ExtractedMemory | None:
        """Run the LLM to extract memory from a user message."""
        provider = self.llm_service.get_fallback_provider()
        if not provider:
            _log.warning("No LLM provider available for memory extraction.")
            return None

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract memory from this message:\n\n{user_message}"}
        ]

        try:
            result = await provider.generate_response(messages)
            
            # Very basic JSON cleanup if the model wraps it in markdown blocks
            raw_text = result.content.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
                
            data = json.loads(raw_text.strip())
            return ExtractedMemory(**data)
            
        except Exception as e:
            _log.error(f"Failed to extract memory: {e}")
            return None
