# tests/test_live_assistant_pipeline.py
"""
Tests for Live Assistant Conversational Pipeline & Temporal Reference Resolver.
Verifies session context disambiguation, historical query targeting,
pre-market intelligence routing, and real LLM provider response quality.
"""
import pytest
from typing import Dict, Any

from src.live_assistant.intent_taxonomy import UserIntent, TemporalTarget, classify_user_intents
from src.live_assistant.evidence_router import EvidenceRouter
from src.live_assistant.assistant_service import LiveAssistantService


@pytest.fixture
def premarket_canonical_state() -> Dict[str, Any]:
    return {
        "market_session": {"status": "closed", "is_closed": True},
        "market_insights_phase": "PRE_MARKET",
        "pre_market_report": {
            "command_center": {
                "opening_bias": "BULLISH_CONTINUATION",
                "expected_opening_range": [24180, 24220],
                "confidence": 78,
                "global_tone": "POSITIVE"
            }
        },
        "post_market_report": {
            "nifty_snapshot": {
                "open": 24155.20,
                "high": 24285.60,
                "low": 24120.40,
                "close": 24231.85,
                "change": "+76.65 (+0.32%)"
            }
        },
        "options": {"pcr": 1.25, "vix": 13.85, "max_pain": 24200, "call_wall": 24300, "put_wall": 24000},
        "intelligence": {"regime": "TREND EXPANSION", "directional_bias": "BULLISH"},
        "active_opportunity": {"status": "NO_SETUP"},
        "is_stale": False,
    }


def test_greeting_no_closed_baseline(premarket_canonical_state):
    """Verify 'Hello there' at 03:xx IST references PRE_MARKET phase and NOT 'CLOSED baseline'."""
    res = LiveAssistantService.process_query(
        user_message="Hello there",
        conversation_id="pipe_greeting_test",
        workstation_state=premarket_canonical_state,
        provider_override="mock"
    )

    assert "PRE_MARKET" in res["answer"] or "pre-market" in res["answer"].lower()
    assert "CLOSED baseline" not in res["answer"]


def test_historical_query_targeting(premarket_canonical_state):
    """Verify 'what happened in the market yesterday' maps to SESSION_HISTORY and PREVIOUS_COMPLETED_SESSION."""
    from src.live_assistant.intent_taxonomy import classify_user_query_with_temporal
    intents, temporal_target = classify_user_query_with_temporal("what happened in the market yesterday")
    assert UserIntent.SESSION_HISTORY in intents
    assert temporal_target == TemporalTarget.PREVIOUS_COMPLETED_SESSION

    packet = EvidenceRouter.route_query(
        "what happened in the market yesterday", premarket_canonical_state, temporal_target_override=temporal_target
    )
    assert "session_history" in packet.evidence
    assert packet.evidence["session_history"]["target_session"] == "PREVIOUS_COMPLETED_SESSION"


def test_premarket_query_targeting(premarket_canonical_state):
    """Verify 'What are we expecting at open?' maps to PREMARKET_TOMORROW and CURRENT_PRE_MARKET."""
    from src.live_assistant.intent_taxonomy import classify_user_query_with_temporal
    intents, temporal_target = classify_user_query_with_temporal("What are we expecting at open?")
    assert UserIntent.PREMARKET_TOMORROW in intents
    assert temporal_target == TemporalTarget.CURRENT_PRE_MARKET

    packet = EvidenceRouter.route_query(
        "What are we expecting at open?", premarket_canonical_state, temporal_target_override=temporal_target
    )
    assert "premarket_intelligence" in packet.evidence
    assert packet.evidence["premarket_intelligence"]["opening_bias"] == "BULLISH_CONTINUATION"


def test_full_5_turn_conversation_sequence(premarket_canonical_state):
    """Verify the exact 5-question multi-turn conversation sequence."""
    c_id = "pipe_5turn_test"
    LiveAssistantService.clear_history(c_id)

    # Turn 1: Hello there
    t1 = LiveAssistantService.process_query("Hello there", conversation_id=c_id, workstation_state=premarket_canonical_state)
    assert "CLOSED baseline" not in t1["answer"]

    # Turn 2: What happened in the market yesterday?
    t2 = LiveAssistantService.process_query("What happened in the market yesterday?", conversation_id=c_id, workstation_state=premarket_canonical_state)
    assert "SESSION_HISTORY" in [i if isinstance(i, str) else i.value for i in t2["intent"]]

    # Turn 3: What are we expecting at open?
    t3 = LiveAssistantService.process_query("What are we expecting at open?", conversation_id=c_id, workstation_state=premarket_canonical_state)
    assert "PREMARKET_TOMORROW" in [i if isinstance(i, str) else i.value for i in t3["intent"]]

    # Turn 4: Why?
    t4 = LiveAssistantService.process_query("Why?", conversation_id=c_id, workstation_state=premarket_canonical_state)
    assert "WHY_EXPLANATION" in [i if isinstance(i, str) else i.value for i in t4["intent"]]

    # Turn 5: What about options?
    t5 = LiveAssistantService.process_query("What about options?", conversation_id=c_id, workstation_state=premarket_canonical_state)
    assert "OPTIONS_DERIVATIVES" in [i if isinstance(i, str) else i.value for i in t5["intent"]]
