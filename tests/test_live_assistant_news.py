# tests/test_live_assistant_news.py
"""
Unit and integration tests for Live Assistant News & Events Grounding.
Verifies canonical news Sentiment extraction, AnswerAct.PRIORITIZATION classification,
absence of evidence vs zero news distinction, deterministic story ranking,
news-domain fallback preservation, and multi-turn news follow-up context.
"""
import pytest
from typing import Dict, Any

from src.live_assistant.intent_taxonomy import (
    UserIntent, AnswerAct, TemporalTarget, classify_user_query_with_temporal, resolve_answer_act
)
from src.live_assistant.evidence_router import EvidenceRouter
from src.live_assistant.evidence_synthesis import EvidenceSynthesizer
from src.live_assistant.answer_planner import AnswerPlanner
from src.live_assistant.deterministic_fallback import DeterministicFallback
from src.live_assistant.assistant_service import LiveAssistantService


@pytest.fixture
def canonical_news_state() -> Dict[str, Any]:
    return {
        "market_session": {"status": "closed", "is_closed": True},
        "market_insights_phase": "PRE_MARKET",
        "newsSentiment": {
            "status": "ready",
            "section_status": "ready",
            "market_tone": "NEUTRAL",
            "provider_health": {"rss_feed": "READY", "calendar": "READY"},
            "items": [
                {
                    "id": "news-101",
                    "headline": "RBI Policy Stance Review Ahead of Policy Committee",
                    "summary_snippet": "MPC members meet to review liquidity conditions.",
                    "source_name": "Financial Express",
                    "published_at": "2026-08-21 02:30:00 IST",
                    "impact_strength": "HIGH",
                    "expected_direction": "UNCLEAR",
                    "affected_sectors": ["BANKING", "FINANCIALS"],
                    "nifty_relevance_score": 0.92,
                    "confidence": 0.88,
                },
                {
                    "id": "news-102",
                    "headline": "US Tech Rally Drives Asian Markets Higher",
                    "summary_snippet": "Semiconductor strength lifts broad indices.",
                    "source_name": "Reuters",
                    "published_at": "2026-08-21 03:00:00 IST",
                    "impact_strength": "MEDIUM",
                    "expected_direction": "POSITIVE",
                    "affected_sectors": ["IT", "GLOBAL"],
                    "nifty_relevance_score": 0.75,
                    "confidence": 0.82,
                }
            ],
            "event_items": [
                {
                    "id": "evt-201",
                    "headline": "India Trade Balance Data Release",
                    "scheduled_time": "17:30 IST",
                    "impact_level": "HIGH",
                    "event_category": "MACRO_EVENT",
                    "source_authority": "PRIMARY",
                }
            ]
        },
        "market_data": {"current_spot": 24231.85},
        "options": {"vix": 13.85},
        "intelligence": {"regime": "TREND EXPANSION"},
        "is_stale": False,
    }


def test_news_intent_and_act_classification():
    """Verify 'what are the top news that might affect market today?' resolves to NEWS_EVENTS + PRIORITIZATION."""
    intents, temporal = classify_user_query_with_temporal("what are the top news that might affect market today?")
    assert UserIntent.NEWS_EVENTS in intents
    assert temporal in (TemporalTarget.LIVE_CURRENT, TemporalTarget.CURRENT_PRE_MARKET)

    act = resolve_answer_act("what are the top news that might affect market today?", intents)
    assert act == AnswerAct.PRIORITIZATION


def test_news_evidence_router_extraction(canonical_news_state):
    """Verify EvidenceRouter extracts canonical newsSentiment items and scheduled events."""
    packet = EvidenceRouter.route_query("what are the top news that might affect market today?", canonical_news_state)
    assert "news_intelligence" in packet.evidence

    ni = packet.evidence["news_intelligence"]
    assert ni["provider_available"] is True
    assert len(ni["news_items"]) == 2
    assert ni["news_items"][0]["headline"] == "RBI Policy Stance Review Ahead of Policy Committee"
    assert len(ni["scheduled_events"]) == 1
    assert ni["scheduled_events"][0]["scheduled_time"] == "17:30 IST"


def test_absence_of_evidence_not_no_news():
    """Verify degraded/unavailable feed states provider status (never says 'no important news')."""
    degraded_state = {
        "market_session": {"status": "closed"},
        "newsSentiment": {"status": "UNAVAILABLE", "section_status": "UNAVAILABLE", "items": []}
    }
    packet = EvidenceRouter.route_query("What are the top news today?", degraded_state)
    synth = EvidenceSynthesizer.synthesize([], packet)
    plan = AnswerPlanner.build_plan(synth, packet)

    assert "unavailable or degraded" in plan.direct_answer_lead
    assert "no significant news" not in plan.direct_answer_lead.lower()


def test_news_ranking_and_unclear_direction_preservation(canonical_news_state):
    """Verify EvidenceSynthesizer ranks RBI news #1 and preserves UNCLEAR direction."""
    packet = EvidenceRouter.route_query("What are the top news today?", canonical_news_state)
    synth = EvidenceSynthesizer.synthesize([], packet)
    plan = AnswerPlanner.build_plan(synth, packet)

    assert len(plan.primary_evidence_bullets) >= 2
    assert "RBI Policy Stance Review" in plan.primary_evidence_bullets[0]
    assert "Direction: UNCLEAR" in plan.primary_evidence_bullets[0]
    assert any("Do NOT invent direction" in p for p in plan.prohibited_claims)


def test_news_domain_fallback_preservation(canonical_news_state):
    """Verify DeterministicFallback for NEWS_EVENTS outputs news headlines rather than NIFTY spot summary."""
    packet = EvidenceRouter.route_query("What are the top news today?", canonical_news_state)
    fb = DeterministicFallback.generate_fallback(packet, reason="TEST_FALLBACK")

    assert "answer" in fb
    ans = fb["answer"]
    assert "tracking 2 news items" in ans
    assert "RBI Policy Stance Review" in ans
    assert "NIFTY is currently at" not in ans


def test_multi_turn_news_followup_sequence(canonical_news_state):
    """Verify multi-turn news follow-up sequence preserves news context."""
    c_id = "news_5turn_sequence_test"
    LiveAssistantService.clear_history(c_id)

    queries = [
        "What are the top news that might affect the market today?",
        "Which one matters most?",
        "Why?",
        "Which sector is most exposed?",
        "What time is the next major event?"
    ]

    for q in queries:
        res = LiveAssistantService.process_query(q, conversation_id=c_id, workstation_state=canonical_news_state)
        assert res["answer_act"] in (
            AnswerAct.PRIORITIZATION.value, AnswerAct.CAUSE.value,
            AnswerAct.EVENT_CALENDAR.value, AnswerAct.SUMMARY.value,
            AnswerAct.CURRENT_STATE.value
        )
        assert res["data_sufficiency"] in ("SUFFICIENT", "PARTIAL")
        assert "answer" in res and len(res["answer"]) > 10
        assert "NIFTY Close:" not in res["answer"]
