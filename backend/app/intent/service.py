from typing import Optional
from app.intent.schemas import IntentResult
from app.intent.engine import IntentEngine


class IntentService:
    """Service wrapper for Cognitive Core V1 Intent Engine, supporting dependency injection."""

    def __init__(self) -> None:
        self.engine = IntentEngine()

    async def analyze_request(
        self, message: str, conversation_id: Optional[str] = None
    ) -> IntentResult:
        """
        Public service interface to analyze any incoming user prompt.
        """
        return await self.engine.process(message, conversation_id)
