import logging
import threading
from typing import Optional

from app.intent.classifier import IntentClassifier
from app.intent.confidence import ConfidenceEngine
from app.intent.context_analyzer import ContextAnalyzer
from app.intent.entity_extractor import EntityExtractor
from app.intent.gateway import IntentGateway
from app.intent.goal_extractor import GoalExtractor
from app.intent.planner import Planner
from app.intent.provider_router import ProviderRouter
from app.intent.risk_analyzer import RiskAnalyzer
from app.intent.enums import IntentType
from app.intent.schemas import IntentResult

_log = logging.getLogger("intent.engine")


class IntentEngine:
    """
    Facade Singleton coordinator for Cognitive Core V1 Intent Engine.
    Handles the entire pipeline validation -> classification -> extraction -> planning.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(IntentEngine, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self.gateway = IntentGateway()
        self.classifier = IntentClassifier()
        self.goal_extractor = GoalExtractor()
        self.entity_extractor = EntityExtractor()
        self.context_analyzer = ContextAnalyzer()
        self.risk_analyzer = RiskAnalyzer()
        self.provider_router = ProviderRouter()
        self.confidence_engine = ConfidenceEngine(threshold=0.6)
        self.planner = Planner()

        self._initialized = True

    async def process(
        self, message: str, conversation_id: Optional[str] = None
    ) -> IntentResult:
        """
        Coordinates the intent extraction pipeline for an incoming user query.
        """
        # 1. Gatekeep validation
        cleaned_message = self.gateway.validate_and_preprocess(message)

        # 2. Classify intent (heuristics or semantic LLM)
        result = await self.classifier.classify(cleaned_message, conversation_id)

        # 3. Post-process Goal
        result.goal = self.goal_extractor.extract(result.goal)

        # 4. Supplemental Entity Extraction (Heuristics)
        heuristic_entities = self.entity_extractor.extract_heuristics(cleaned_message)
        existing_entity_vals = {e.value.lower() for e in result.entities}
        for ent in heuristic_entities:
            if ent.value.lower() not in existing_entity_vals:
                result.entities.append(ent)

        # 5. Supplemental Context Analysis (Heuristics)
        heuristic_contexts = self.context_analyzer.analyze(cleaned_message)
        existing_context_sources = {c.source for c in result.required_context}
        for ctx in heuristic_contexts:
            if ctx.source not in existing_context_sources:
                result.required_context.append(ctx)

        # 6. Safety scan and Risk Analysis override
        rules_risk = self.risk_analyzer.assess(cleaned_message)
        if (
            rules_risk.requires_confirmation
            or rules_risk.level != result.risk_assessment.level
        ):
            result.risk_assessment = rules_risk

        # 7. Route to provider
        result.suggested_provider = self.provider_router.route(result.intent)

        # 8. Check confidence and trigger clarification override (only if not unknown)
        if result.intent != IntentType.UNKNOWN:
            is_clarify, prompt = self.confidence_engine.evaluate(
                result.intent, result.confidence
            )
            if is_clarify:
                result.clarification_required = True
                result.clarification_prompt = prompt

        # 9. Formulate final execution plan
        if not result.execution_plan or not result.execution_plan.steps:
            result.execution_plan = self.planner.generate_plan(
                result.intent, result.suggested_provider, result.goal
            )
            result.suggested_tools = result.execution_plan.suggested_tools
        else:
            if not result.suggested_tools and result.execution_plan.suggested_tools:
                result.suggested_tools = result.execution_plan.suggested_tools
            elif result.suggested_tools and not result.execution_plan.suggested_tools:
                result.execution_plan.suggested_tools = result.suggested_tools

        _log.info(
            f"[INTENT-ENGINE] Processed query: '{cleaned_message[:30]}...' -> "
            f"Intent: {result.intent.value} (Conf: {result.confidence * 100:.0f}%), "
            f"Goal: '{result.goal}', Clarify: {result.clarification_required}"
        )

        return result
