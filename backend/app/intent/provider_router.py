from typing import Dict
from app.intent.enums import IntentType, ProviderType


class ProviderRouter:
    """Dynamically routes intents to the optimal AI provider based on configuration."""

    def __init__(self, routing_rules: Dict[IntentType, ProviderType] = None):
        self.routing_rules = routing_rules or {
            IntentType.PROGRAMMING: ProviderType.CODER_MODEL,
            IntentType.CODE_GENERATION: ProviderType.CODER_MODEL,
            IntentType.DEBUGGING: ProviderType.CLAUDE,
            IntentType.REPOSITORY_ANALYSIS: ProviderType.CLAUDE,
            IntentType.CODE_REVIEW: ProviderType.CLAUDE,
            IntentType.DEPLOYMENT: ProviderType.CLAUDE,
            IntentType.FILE_ANALYSIS: ProviderType.CLAUDE,
            IntentType.PLANNING: ProviderType.CLAUDE,
            IntentType.RESEARCH: ProviderType.GEMINI,
            IntentType.SEARCH: ProviderType.GEMINI,
            IntentType.LEARNING: ProviderType.GEMINI,
            IntentType.VISION: ProviderType.VISION_MODEL,
            IntentType.IMAGE_ANALYSIS: ProviderType.VISION_MODEL,
            IntentType.CREATIVE: ProviderType.GPT,
            IntentType.WRITING: ProviderType.GPT,
            IntentType.CONVERSATION: ProviderType.LIGHTWEIGHT,
            IntentType.VOICE_COMMAND: ProviderType.LIGHTWEIGHT,
            IntentType.SYSTEM_COMMAND: ProviderType.LIGHTWEIGHT,
            IntentType.SCHEDULING: ProviderType.LIGHTWEIGHT,
            IntentType.MEMORY_RECALL: ProviderType.LIGHTWEIGHT,
            IntentType.AUTOMATION: ProviderType.LIGHTWEIGHT,
            IntentType.GENERAL_QUESTION: ProviderType.LIGHTWEIGHT,
            IntentType.UNKNOWN: ProviderType.LIGHTWEIGHT,
        }

    def route(self, intent: IntentType) -> ProviderType:
        """
        Determines the suggested provider for a given intent type.
        """
        return self.routing_rules.get(intent, ProviderType.LIGHTWEIGHT)
