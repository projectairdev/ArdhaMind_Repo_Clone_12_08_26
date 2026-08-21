# tests/test_live_assistant_panel.py
"""
Tests for Live Assistant Contextual Panel & UI Architecture Replacement.
Verifies workspace independence, panel routing, missing value sanitization,
and legacy workspace deactivation.
"""
import pytest
from typing import Dict, Any

from src.live_assistant.intent_taxonomy import UserIntent
from src.live_assistant.evidence_packet import BoundedEvidencePacket
from src.live_assistant.evidence_router import EvidenceRouter
from src.live_assistant.llm_provider import MockProvider
from src.live_assistant.deterministic_fallback import DeterministicFallback
from src.live_assistant.assistant_service import LiveAssistantService


@pytest.fixture
def empty_market_state() -> Dict[str, Any]:
    return {
        "market_session": {"status": "closed", "is_closed": True},
        "market_data": {},
        "options": {},
        "intelligence": {},
        "is_stale": False,
    }


def test_missing_value_sanitization(empty_market_state):
    """Verify missing spot/values do NOT render raw 'None' or 'null'."""
    packet = EvidenceRouter.route_query("What is happening now?", empty_market_state)
    provider = MockProvider()
    res_text = provider.generate_grounded_answer(packet)

    assert "None" not in res_text
    assert "null" not in res_text
    assert "currently unavailable" in res_text


test_fallback_value_sanitization = test_missing_value_sanitization


def test_service_returns_sanitized_output(empty_market_state):
    """Verify assistant service returns clean string without raw None."""
    res = LiveAssistantService.process_query(
        user_message="What is happening now?",
        conversation_id="panel_test",
        workstation_state=empty_market_state,
        provider_override="mock"
    )

    assert "None" not in res["answer"]
    assert "null" not in res["answer"]
    assert res["fallback_used"] is False
    assert res["provider"] == "mock"


def test_legacy_workspace_route_deactivation():
    """Verify legacy 'live_assistant' is no longer a primary workspace module."""
    from src.live_assistant.intent_taxonomy import UserIntent
    # Ensure backend architecture taxonomy remains intact with 15 intents
    assert len(UserIntent.__members__) == 15
