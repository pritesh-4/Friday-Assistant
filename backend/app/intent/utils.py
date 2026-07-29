import re
from typing import Optional, Dict, Any
from app.intent.enums import (
    IntentType,
    RiskLevel,
    ProviderType,
    ToolType,
    ContextSource,
)


def match_heuristics(message: str) -> Optional[Dict[str, Any]]:
    """
    Perform fast rule-based regex matching for common operations.
    Returns a dict that can be used to construct IntentResult if matched, otherwise None.
    Execution time is typically <1ms.
    """
    msg = message.strip().lower()

    # 1. Greetings & Conversation
    if re.match(
        r"^(hi|hello|hey|g'day|yo|howdy|sup|how are you|good morning|good afternoon|good evening|who are you|what is your name)\b",
        msg,
    ):
        return {
            "intent": IntentType.CONVERSATION,
            "confidence": 1.0,
            "goal": "Engage in social conversation",
            "entities": [],
            "required_context": [
                {
                    "source": ContextSource.CONVERSATION,
                    "reason": "Follow conversational flow",
                    "confidence": 1.0,
                }
            ],
            "suggested_tools": [],
            "suggested_provider": ProviderType.LIGHTWEIGHT,
            "risk_assessment": {
                "level": RiskLevel.SAFE,
                "reasons": ["Social conversation has no system execution risk"],
                "requires_confirmation": False,
            },
            "clarification_required": False,
            "clarification_prompt": None,
            "execution_plan": {
                "steps": ["Respond to user greeting and maintain active context"],
                "suggested_tools": [],
                "suggested_provider": ProviderType.LIGHTWEIGHT,
            },
        }

    # 2. Web Search
    search_match = re.match(
        r"^(search the web for|web search|search for|google|lookup)\s+(.+)$", msg
    )
    if search_match:
        query_val = search_match.group(2)
        return {
            "intent": IntentType.RESEARCH,
            "confidence": 1.0,
            "goal": f"Perform research query: {query_val}",
            "entities": [
                {"value": query_val, "category": "search_query", "confidence": 1.0}
            ],
            "required_context": [
                {
                    "source": ContextSource.WEB_SEARCH,
                    "reason": "Fetch search query results",
                    "confidence": 1.0,
                }
            ],
            "suggested_tools": [ToolType.WEB_SEARCH],
            "suggested_provider": ProviderType.GEMINI,
            "risk_assessment": {
                "level": RiskLevel.SAFE,
                "reasons": ["Web searching is safe"],
                "requires_confirmation": False,
            },
            "clarification_required": False,
            "clarification_prompt": None,
            "execution_plan": {
                "steps": ["Execute Web Search tool", "Summarize results and respond"],
                "suggested_tools": [ToolType.WEB_SEARCH],
                "suggested_provider": ProviderType.GEMINI,
            },
        }

    # 3. Tasks & Todo
    if re.match(r"^(list tasks|show tasks|todo|todo list|get tasks|task list)\b", msg):
        return {
            "intent": IntentType.AUTOMATION,
            "confidence": 1.0,
            "goal": "Retrieve list of active project tasks",
            "entities": [],
            "required_context": [
                {
                    "source": ContextSource.SYSTEM_STATE,
                    "reason": "Query task list",
                    "confidence": 1.0,
                }
            ],
            "suggested_tools": [ToolType.PLANNER],
            "suggested_provider": ProviderType.LIGHTWEIGHT,
            "risk_assessment": {
                "level": RiskLevel.SAFE,
                "reasons": ["Listing tasks is safe and read-only"],
                "requires_confirmation": False,
            },
            "clarification_required": False,
            "clarification_prompt": None,
            "execution_plan": {
                "steps": [
                    "Read active tasks list from task store",
                    "Render task board",
                ],
                "suggested_tools": [ToolType.PLANNER],
                "suggested_provider": ProviderType.LIGHTWEIGHT,
            },
        }

    # 4. File inspection
    file_match = re.search(
        r"\b(view|read|inspect|show|display|cat)\s+([\w\-\./]+\.(py|js|jsx|json|html|css|txt|md|yml|yaml|ini|env))\b",
        msg,
    )
    if file_match:
        file_path = file_match.group(2)
        return {
            "intent": IntentType.FILE_ANALYSIS,
            "confidence": 0.95,
            "goal": f"Analyze contents of file: {file_path}",
            "entities": [{"value": file_path, "category": "file", "confidence": 1.0}],
            "required_context": [
                {
                    "source": ContextSource.FILES,
                    "reason": "Read target file content",
                    "confidence": 0.95,
                }
            ],
            "suggested_tools": [ToolType.REPOSITORY_ANALYZER],
            "suggested_provider": ProviderType.CLAUDE,
            "risk_assessment": {
                "level": RiskLevel.SAFE,
                "reasons": ["Reading local workspace files is read-only and safe"],
                "requires_confirmation": False,
            },
            "clarification_required": False,
            "clarification_prompt": None,
            "execution_plan": {
                "steps": [
                    f"Load contents of file {file_path}",
                    "Analyze and return explanation",
                ],
                "suggested_tools": [ToolType.REPOSITORY_ANALYZER],
                "suggested_provider": ProviderType.CLAUDE,
            },
        }

    # 5. Git Status / Git diff
    if re.match(
        r"^(git status|git diff|show git changes|git changes|whats modified)\b", msg
    ):
        return {
            "intent": IntentType.REPOSITORY_ANALYSIS,
            "confidence": 1.0,
            "goal": "Analyze git working tree status and modifications",
            "entities": [],
            "required_context": [
                {
                    "source": ContextSource.REPOSITORY,
                    "reason": "Query git working directory status",
                    "confidence": 1.0,
                }
            ],
            "suggested_tools": [ToolType.GIT_ANALYZER],
            "suggested_provider": ProviderType.CLAUDE,
            "risk_assessment": {
                "level": RiskLevel.SAFE,
                "reasons": ["Git status and diff are safe, read-only queries"],
                "requires_confirmation": False,
            },
            "clarification_required": False,
            "clarification_prompt": None,
            "execution_plan": {
                "steps": [
                    "Run git status and git diff commands",
                    "Parse modifications and summarize",
                ],
                "suggested_tools": [ToolType.GIT_ANALYZER],
                "suggested_provider": ProviderType.CLAUDE,
            },
        }

    return None


def parse_json_markdown(text: str) -> dict:
    """
    Safely extract JSON object from markdown block or raw text.
    """
    import json

    cleaned = text.strip()

    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Extract block matching ```json ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding the first '{' and last '}'
    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        candidate = cleaned[start_idx : end_idx + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not parse valid JSON from text response.")
