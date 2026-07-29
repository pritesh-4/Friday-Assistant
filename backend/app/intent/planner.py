from app.intent.enums import IntentType, ToolType, ProviderType
from app.intent.schemas import ExecutionPlan


class Planner:
    """Assembles and refines execution plans for downstream task layers."""

    def generate_plan(
        self, intent: IntentType, provider: ProviderType, goal: str
    ) -> ExecutionPlan:
        """
        Produce a structured execution plan block based on resolved classification properties.
        """
        steps = [f"Identify action parameters for goal: '{goal}'"]
        tools = []

        if intent in (IntentType.PROGRAMMING, IntentType.CODE_GENERATION):
            steps.append("Formulate implementation strategy")
            steps.append("Generate proposed code changes")
            tools.append(ToolType.REPOSITORY_ANALYZER)

        elif intent == IntentType.DEBUGGING:
            steps.append("Inspect diagnostic log or trace")
            steps.append("Formulate root cause repair solution")
            tools.append(ToolType.REPOSITORY_ANALYZER)
            tools.append(ToolType.CODE_EXECUTOR)

        elif intent in (IntentType.RESEARCH, IntentType.SEARCH):
            steps.append("Formulate semantic search query strings")
            steps.append("Query search providers and synthesize results")
            tools.append(ToolType.WEB_SEARCH)

        else:
            steps.append("Generate direct assistant text reply")

        return ExecutionPlan(
            steps=steps, suggested_tools=tools, suggested_provider=provider
        )
