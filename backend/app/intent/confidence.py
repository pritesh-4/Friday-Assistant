from typing import Optional, Tuple
from app.intent.enums import IntentType


class ConfidenceEngine:
    """Evaluates classification scores and handles low-confidence clarification triggers."""

    def __init__(self, threshold: float = 0.6):
        self.threshold = threshold

    def evaluate(
        self, intent: IntentType, confidence: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Evaluate confidence score. If below threshold, trigger clarification prompt.
        """
        if confidence < self.threshold:
            prompt = (
                f"I detected your request might relate to {intent.value}, but I want to be certain. "
                "Could you clarify exactly what you are trying to accomplish?"
            )
            return True, prompt

        return False, None
