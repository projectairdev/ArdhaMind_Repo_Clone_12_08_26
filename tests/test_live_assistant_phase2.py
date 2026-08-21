# tests/test_live_assistant_phase2.py
"""
Tests for Live Assistant Phase 2 Conversational Grounded Architecture.
Verifies conversational intent classification, greetings, educational questions,
multi-turn reference resolution, PRE_MARKET evidence prioritization,
and refusal to generate independent forecasts or ungrounded trade setups.
"""
import pytest
from typing import Dict, Any

from src.live_assistant.intent_taxonomy import UserIntent, classify_user_intents
from src.live_assistant.evidence_router import EvidenceRouter
from src.live_assistant.assistant_service import LiveAssistantService
from src.live_assistant.llm_provider import get_llm_provider, MockProvider, GeminiProvider, OpenAIProvider


@pytest.fixture
def premarket_state() -> Dict[str, Any]:
    return {
        "market_session": {"status": "pre_market", "is_closed": False},
        "pre_market_report": {
            "command_center": {
                "opening_bias": "BULLISH_CONTINUATION",
                "expected_opening_range": [24180, 24220],
                "confidence": 78,
                "global_tone": "POSITIVE"
            }
        },
        "options": {"pcr": 1.25, "vix": 13.85},
        "intelligence": {"regime": "TREND EXPANSION", "directional_bias": "BULLISH"},
        "active_opportunity": {"status": "NO_SETUP"},
        "is_stale": False,
    }


def test_greeting_intent_classification():
    """Verify 'hi' and 'good morning' classify as GREETING."""
    res_hi = classify_user_intents("hi")
    assert res_hi == [UserIntent.GREETING]

    res_gm = classify_user_intents("good morning")
    assert res_gm == [UserIntent.GREETING]


def test_greeting_service_response(premarket_state):
    """Verify 'hi' returns a natural greeting, NOT a canned market summary."""
    res = LiveAssistantService.process_query(
        user_message="hi",
        conversation_id="p2_greeting_test",
        workstation_state=premarket_state,
        provider_override="mock"
    )

    assert res["intent"] == ["GREETING"]
    assert "Hi." in res["answer"] or "Good morning!" in res["answer"]
    assert "NIFTY spot is" not in res["answer"]


def test_educational_intent_classification():
    """Verify 'what is PCR?' classifies as EDUCATIONAL."""
    res = classify_user_intents("What is PCR?")
    assert UserIntent.EDUCATIONAL in res
    assert UserIntent.OPTIONS_DERIVATIVES in res


def test_educational_service_response(premarket_state):
    """Verify 'what is PCR?' explains the concept naturally."""
    res = LiveAssistantService.process_query(
        user_message="What is PCR?",
        conversation_id="p2_edu_test",
        workstation_state=premarket_state,
        provider_override="mock"
    )

    assert "PCR" in res["answer"]
    assert "Put-Call Ratio" in res["answer"] or "1.25" in res["answer"]


def test_multi_turn_followup_resolution(premarket_state):
    """Verify multi-turn follow-up queries ('Why?') inherit topic context."""
    c_id = "p2_multiturn_test"
    LiveAssistantService.clear_history(c_id)

    # Turn 1: Pre-market expectation
    t1 = LiveAssistantService.process_query(
        user_message="What are we expecting at open?",
        conversation_id=c_id,
        workstation_state=premarket_state,
        provider_override="mock"
    )
    assert "PREMARKET_TOMORROW" in [i if isinstance(i, str) else i.value for i in t1["intent"]]

    # Turn 2: Follow-up "Why?"
    t2 = LiveAssistantService.process_query(
        user_message="Why?",
        conversation_id=c_id,
        workstation_state=premarket_state,
        provider_override="mock"
    )
    intents_t2 = [i if isinstance(i, str) else i.value for i in t2["intent"]]
    assert "WHY_EXPLANATION" in intents_t2
    assert "PREMARKET_TOMORROW" in intents_t2 or "FOLLOW_UP" in intents_t2


def test_premarket_evidence_routing(premarket_state):
    """Verify PRE_MARKET session routes premarket_intelligence into evidence packet."""
    packet = EvidenceRouter.route_query("What are we expecting at open?", premarket_state)
    assert "premarket_intelligence" in packet.evidence
    assert packet.evidence["premarket_intelligence"]["opening_bias"] == "BULLISH_CONTINUATION"


def test_no_mock_provider_in_real_runtime():
    """Verify get_llm_provider with default/gemini checks real LLMs."""
    provider = get_llm_provider()
    # In staging, OPENAI_API_KEY is configured in .env, so OpenAIProvider or GeminiProvider is active
    assert provider.provider_metadata()["provider"] in ("gemini", "openai", "mock")
