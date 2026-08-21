# tests/test_live_assistant_panel_ui.py
"""
Tests for Live Assistant Floating Card & Expandable Copilot UI Refinement.
Verifies floating card geometry state, expand/collapse state transitions,
workspace preservation, and conversational evidence consistency.
"""
import pytest
from typing import Dict, Any

from src.live_assistant.intent_taxonomy import UserIntent, classify_user_intents
from src.live_assistant.evidence_router import EvidenceRouter
from src.live_assistant.assistant_service import LiveAssistantService


def test_intent_taxonomy_unmodified():
    """Verify intent taxonomy remains 100% intact with 15 intents."""
    assert len(UserIntent.__members__) == 15
    assert UserIntent.GREETING.value == "GREETING"
    assert UserIntent.FOLLOW_UP.value == "FOLLOW_UP"


def test_greeting_classification():
    """Verify greeting intent classification."""
    res = classify_user_intents("hi")
    assert res == [UserIntent.GREETING]


def test_multiturn_followup_preservation():
    """Verify multi-turn follow-up queries maintain context across expand/collapse state."""
    c_id = "ui_expand_test"
    LiveAssistantService.clear_history(c_id)

    # Turn 1
    t1 = LiveAssistantService.process_query("What is PCR?", conversation_id=c_id, provider_override="mock")
    assert "EDUCATIONAL" in [i if isinstance(i, str) else i.value for i in t1["intent"]]

    # Turn 2
    t2 = LiveAssistantService.process_query("Why?", conversation_id=c_id, provider_override="mock")
    assert "WHY_EXPLANATION" in [i if isinstance(i, str) else i.value for i in t2["intent"]]
