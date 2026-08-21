# tests/test_live_assistant_synthesis.py
"""
Tests for Live Assistant Phase 3 — Evidence Synthesis, Causal Attribution & Precise Answer Planning.
Verifies query decomposition, AnswerAct resolution, driver ranking, contribution vs causation distinction,
temporal institutional validity protection, direct answer first planning, and follow-up GroundingValidator behavior.
"""
import pytest
from typing import Dict, Any

from src.live_assistant.intent_taxonomy import AnswerAct, TemporalTarget, decompose_query, UserIntent
from src.live_assistant.evidence_router import EvidenceRouter
from src.live_assistant.evidence_synthesis import EvidenceSynthesizer, CausalConfidence
from src.live_assistant.answer_planner import AnswerPlanner
from src.live_assistant.assistant_service import LiveAssistantService
from src.live_assistant.grounding_validator import GroundingValidator


@pytest.fixture
def canonical_premarket_state() -> Dict[str, Any]:
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


def test_query_decomposition_compound_query():
    """Verify compound query 'what happened in the market yesterday, why that much raise?' splits into subqueries."""
    subq = decompose_query("what happened in the market yesterday, why that much raise?")
    assert len(subq) == 2
    assert subq[0].answer_act == AnswerAct.SUMMARY
    assert subq[1].answer_act == AnswerAct.CAUSE
    assert subq[1].temporal_target == TemporalTarget.PREVIOUS_COMPLETED_SESSION


def test_evidence_synthesis_driver_ranking(canonical_premarket_state):
    """Verify EvidenceSynthesizer ranks breadth and sector leadership drivers."""
    subq = decompose_query("Why did NIFTY rise yesterday?")
    packet = EvidenceRouter.route_query("Why did NIFTY rise yesterday?", canonical_premarket_state)
    synth = EvidenceSynthesizer.synthesize(subq, packet)

    assert synth.primary_answer_act == AnswerAct.CAUSE
    assert len(synth.ranked_drivers) >= 2
    assert synth.ranked_drivers[0].factor_name == "Broad Market Participation"
    assert synth.ranked_drivers[0].confidence == CausalConfidence.STRONG_CONTRIBUTOR


def test_institutional_context_temporal_protection(canonical_premarket_state):
    """Verify FII/DII data is marked as post-session context rather than intraday trigger."""
    subq = decompose_query("Did FII buying cause yesterday's rise?")
    packet = EvidenceRouter.route_query("Did FII buying cause yesterday's rise?", canonical_premarket_state)
    synth = EvidenceSynthesizer.synthesize(subq, packet)

    assert synth.institutional_context.get("availability") == "POST_CLOSE"


def test_answer_planner_direct_answer_lead(canonical_premarket_state):
    """Verify AnswerPlanner creates direct-answer-first leads."""
    subq = decompose_query("Why did NIFTY rise yesterday?")
    packet = EvidenceRouter.route_query("Why did NIFTY rise yesterday?", canonical_premarket_state)
    synth = EvidenceSynthesizer.synthesize(subq, packet)
    plan = AnswerPlanner.build_plan(synth, packet)

    assert "bullish structure of yesterday's session was driven by broad market participation" in plan.direct_answer_lead
    assert len(plan.primary_evidence_bullets) >= 2
    assert any("FII data is post-session" in p for p in plan.prohibited_claims)


def test_followup_grounding_validator_pass():
    """Verify GroundingValidator accepts prose numbers <= 100 without failing validation."""
    from src.live_assistant.evidence_packet import BoundedEvidencePacket
    packet = BoundedEvidencePacket(
        question="Why?",
        intents=["WHY_EXPLANATION"],
        canonical_session="PRE_MARKET",
        market_timestamp="2026-08-21 04:00:00 IST",
        freshness_status="LIVE",
        evidence={"premarket_intelligence": {"confidence": 78}},
        missing_evidence=[],
        prohibited_inference=True,
        allowed_conclusions=[]
    )

    resp_text = "ArdhaMind is waiting for 09:15 confirmation because 2 conditions are missing."
    val_res = GroundingValidator.validate(resp_text, packet)
    assert val_res.is_valid


def test_full_8_turn_acceptance_conversation(canonical_premarket_state):
    """Verify the required 8-question browser acceptance sequence."""
    c_id = "phase3_8turn_acceptance"
    LiveAssistantService.clear_history(c_id)

    queries = [
        "What happened yesterday?",
        "Why did it rise that much?",
        "Was it broad or just heavyweights?",
        "What was the biggest contributor?",
        "Did FII cause it?",
        "What are we expecting at open?",
        "Why?",
        "What could invalidate that?"
    ]

    for q in queries:
        res = LiveAssistantService.process_query(q, conversation_id=c_id, workstation_state=canonical_premarket_state)
        assert res["answer_act"] is not None
        assert res["data_sufficiency"] in ("SUFFICIENT", "PARTIAL", "INSUFFICIENT")
        assert "answer" in res and len(res["answer"]) > 10
