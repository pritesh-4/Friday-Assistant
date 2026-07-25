from typing import Any

class ContextBuilder:
    """Builds the final prompt context containing system instructions, memories, and history."""

    system_prompt = (
        "You are F.R.I.D.A.Y., a highly intelligent personal AI companion. "
        "You possess a Long-Term Cognitive Memory System. You remember facts, projects, events, and workflows about the user. "
        "Use the provided context to personalize your responses. Do not explicitly say 'I see in your memory', just seamlessly incorporate the knowledge."
    )

    def build_messages(
        self,
        session_messages: list[dict[str, Any]],
        memories: dict[str, list[dict]],
    ) -> list[dict[str, Any]]:
        """
        Constructs the final list of messages for the LLM.

        Args:
            session_messages: A list of dicts with 'role' and 'content', representing recent history.
            memories: Dictionary of retrieved memories categorized by type.
        """
        messages: list[dict[str, Any]] = [{"role": "system", "content": self.system_prompt}]
        
        memory_context = ""
        
        if memories.get("semantic"):
            memory_context += "Facts about the User:\n"
            for doc in memories["semantic"]:
                memory_context += f"- {doc['document']}\n"
                
        if memories.get("episodic"):
            memory_context += "\nImportant Events & Timeline:\n"
            for doc in memories["episodic"]:
                memory_context += f"- {doc['document']}\n"
                
        if memories.get("procedural"):
            memory_context += "\nUser Workflows & Preferences:\n"
            for doc in memories["procedural"]:
                memory_context += f"- {doc['document']}\n"
                
        if memories.get("project"):
            memory_context += "\nCurrent Projects:\n"
            for doc in memories["project"]:
                memory_context += f"- {doc['document']}\n"

        if memory_context.strip():
            messages.append(
                {
                    "role": "system",
                    "content": f"=== COGNITIVE MEMORY RETRIEVAL ===\n{memory_context.strip()}",
                }
            )

        # Extend with recent session messages
        messages.extend(
            {"role": msg["role"], "content": msg["content"]}
            for msg in session_messages
            if msg["role"] in {"user", "assistant", "system"}
        )
        return messages
