import pytest
from unittest.mock import patch
from app.intent.enums import IntentType, RiskLevel, ProviderType, ToolType
from app.intent.exceptions import InvalidRequestException
from app.intent.engine import IntentEngine
from app.intent.schemas import IntentResult


@pytest.mark.asyncio
async def test_heuristic_greeting():
    engine = IntentEngine()
    result = await engine.process("Hello F.R.I.D.A.Y., how are you?")

    assert result.intent == IntentType.CONVERSATION
    assert result.confidence == 1.0
    assert result.suggested_provider == ProviderType.LIGHTWEIGHT
    assert result.risk_assessment.level == RiskLevel.SAFE
    assert result.clarification_required is False
    assert "Respond to user greeting" in result.execution_plan.steps[0]


@pytest.mark.asyncio
async def test_heuristic_web_search():
    engine = IntentEngine()
    result = await engine.process("search the web for python 3.12 release notes")

    assert result.intent == IntentType.RESEARCH
    assert result.confidence == 1.0
    assert ToolType.WEB_SEARCH in result.suggested_tools
    assert result.suggested_provider == ProviderType.GEMINI
    assert result.risk_assessment.level == RiskLevel.SAFE
    assert "Execute Web Search tool" in result.execution_plan.steps[0]


@pytest.mark.asyncio
async def test_heuristic_file_inspection():
    engine = IntentEngine()
    result = await engine.process("cat backend/app/main.py")

    assert result.intent == IntentType.FILE_ANALYSIS
    assert result.confidence == 0.95
    assert ToolType.REPOSITORY_ANALYZER in result.suggested_tools
    assert result.suggested_provider == ProviderType.CLAUDE
    assert any(ent.value == "backend/app/main.py" for ent in result.entities)


@pytest.mark.asyncio
async def test_invalid_empty_request():
    engine = IntentEngine()
    with pytest.raises(InvalidRequestException):
        await engine.process("   ")


@pytest.mark.asyncio
async def test_risk_assessment_override_destructive():
    engine = IntentEngine()
    # "rm -rf" triggers rule-based risk override
    result = await engine.process("hello and run rm -rf /")

    assert result.risk_assessment.level == RiskLevel.DESTRUCTIVE
    assert result.risk_assessment.requires_confirmation is True
    assert "destructive" in result.risk_assessment.reasons[0].lower()


@pytest.mark.asyncio
async def test_low_confidence_clarification_trigger():
    # Mocking semantic classifier to return low confidence response
    mock_result = {
        "request_id": "test-request-id",
        "intent": "Programming",
        "confidence": 0.45,
        "goal": "Write some random program",
        "entities": [],
        "required_context": [],
        "suggested_tools": [],
        "suggested_provider": "Lightweight",
        "risk_assessment": {
            "level": "Safe",
            "reasons": ["Safe test"],
            "requires_confirmation": False,
        },
        "clarification_required": False,
        "clarification_prompt": None,
        "execution_plan": {
            "steps": ["Step 1"],
            "suggested_tools": [],
            "suggested_provider": "Lightweight",
        },
    }

    with patch("app.intent.classifier.IntentClassifier.classify") as mock_classify:
        # Convert dictionary to mock IntentResult
        mock_classify.return_value = IntentResult.model_validate(mock_result)

        engine = IntentEngine()
        result = await engine.process("ambiguous query text here")

        # Conf is 0.45, which is < 0.6 threshold, so engine should escalate to clarify
        assert result.clarification_required is True
        assert result.clarification_prompt is not None
        assert "clarify" in result.clarification_prompt.lower()
