import logging
import uuid
from typing import Optional

from app.intent.enums import IntentType, RiskLevel, ProviderType
from app.intent.prompts import INTENT_SYSTEM_PROMPT
from app.intent.schemas import (
    IntentResult,
    ContextRequirement,
    RiskAssessment,
    ExecutionPlan,
)
from app.intent.utils import match_heuristics, parse_json_markdown
from app.services.llm_service import LLMService

_log = logging.getLogger("intent.classifier")


class IntentClassifier:
    """
    Classifies user intent using rule-based heuristics (<5ms)
    with a fallback to semantic LLM classification (<300ms).
    """

    def __init__(self) -> None:
        self.llm_service = LLMService()

    async def classify(
        self, message: str, conversation_id: Optional[str] = None
    ) -> IntentResult:
        request_id = str(uuid.uuid4())

        # 1. Try rule-based fast path heuristics
        heuristic_res = match_heuristics(message)
        if heuristic_res:
            _log.info(
                f"[INTENT-HEURISTIC] Fast matched intent: {heuristic_res['intent']}"
            )
            heuristic_res["request_id"] = request_id
            return IntentResult.model_validate(heuristic_res)

        # 2. Semantic analysis via default configured LLM provider
        _log.info(
            "[INTENT-SEMANTIC] No heuristic match. Calling semantic classifier LLM..."
        )

        provider = self.llm_service.get_fallback_provider()
        if not provider:
            _log.warning(
                "[INTENT-SEMANTIC] No LLM provider configured. Using local fallback."
            )
            return self._get_fallback_result(request_id, message)

        try:
            prompt_messages = [
                {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Analyze query: '{message}'\nConversation ID: {conversation_id or 'none'}",
                },
            ]

            result = await provider.generate_response(prompt_messages)
            extracted_json = parse_json_markdown(result.content)

            # Add metadata keys
            extracted_json["request_id"] = request_id

            # Validate schema
            return IntentResult.model_validate(extracted_json)

        except Exception as exc:
            _log.error(
                f"[INTENT-SEMANTIC] LLM classification failed: {exc}", exc_info=True
            )
            return self._get_fallback_result(request_id, message)

    def _get_fallback_result(self, request_id: str, message: str) -> IntentResult:
        """
        Produces a safe, read-only fallback result to ensure the request pipeline never hangs.
        """
        return IntentResult(
            request_id=request_id,
            intent=IntentType.UNKNOWN,
            confidence=0.5,
            goal="Process raw user message",
            entities=[],
            required_context=[
                ContextRequirement(
                    source="Conversation",
                    reason="Read conversational history",
                    confidence=0.8,
                )
            ],
            suggested_tools=[],
            suggested_provider=ProviderType.LIGHTWEIGHT,
            risk_assessment=RiskAssessment(
                level=RiskLevel.SAFE,
                reasons=["Fallback bypass execution is inherently safe"],
                requires_confirmation=False,
            ),
            clarification_required=False,
            clarification_prompt=None,
            execution_plan=ExecutionPlan(
                steps=["Pass prompt directly to default conversational provider"],
                suggested_tools=[],
                suggested_provider=ProviderType.LIGHTWEIGHT,
            ),
        )
