# tests/test_live_assistant_news_parity.py
"""
Unit and integration tests for Canonical News Runtime Parity & Multi-Turn Cleanliness.
Verifies server-authoritative state hydration, absence of MARKET_SUMMARY intent pollution,
sector exposure derived from news, and scheduled event calendar retrieval.
"""
import os
import pytest
from typing import Dict, Any

from src.live_assistant.intent_taxonomy import (
    UserIntent, AnswerAct, classify_user_query_with_temporal, resolve_answer_act
)
from src.live_assistant.evidence_router import EvidenceRouter
from src.live_assistant.evidence_synthesis import EvidenceSynthesizer
from src.live_assistant.answer_planner import AnswerPlanner
from src.live_assistant.assistant_service import LiveAssistantService


@pytest.fixture
def real_canonical_news_state() -> Dict[str, Any]:
    return {
        "market_session": {"status": "closed", "is_closed": True},
        "market_insights_phase": "PRE_MARKET",
        "news_intelligence": {
            "status": "ready",
            "section_status": "ready",
            "market_tone": "NEUTRAL",
            "provider_health": {"rss_feed": "READY", "official_sources": "READY"},
            "items": [
                {
                    "id": "real-news-001",
                    "headline": "SEBI Updates Margin Requirements for Derivative Contracts",
                    "summary_snippet": "New regulatory framework issued for institutional traders.",
                    "source_name": "SEBI Circular",
                    "published_at": "2026-08-21 04:15:00 IST",
                    "impact_strength": "HIGH",
                    "expected_direction": "UNCLEAR",
                    "affected_sectors": ["BANKING", "FINANCIALS"],
                    "nifty_relevance_score": 0.96,
                    "confidence": 0.92,
                },
                {
                    "id": "real-news-002",
                    "headline": "Crude Oil Surge Spikes Inflation Concerns for Asia",
                    "summary_snippet": "Brent crude breaks $88 on energy supply tightness.",
                    "source_name": "Bloomberg",
                    "published_at": "2026-08-21 04:30:00 IST",
                    "impact_strength": "HIGH",
                    "expected_direction": "UNCLEAR",
                    "affected_sectors": ["ENERGY", "AUTO", "PAINT"],
                    "nifty_relevance_score": 0.89,
                    "confidence": 0.85,
                }
            ],
            "event_items": [
                {
                    "id": "real-evt-001",
                    "headline": "India Trade Balance Data Release",
                    "scheduled_time": "17:30 IST",
                    "impact_level": "HIGH",
                    "event_category": "MACRO_EVENT"
                }
            ]
        },
        "is_stale": False,
    }


def test_pure_news_query_intent_cleanliness():
    """Verify 'what are the top news that might affect market today?' does NOT include MARKET_SUMMARY."""
    intents, temporal = classify_user_query_with_temporal("what are the top news that might affect market today?")
    assert UserIntent.NEWS_EVENTS in intents
    assert UserIntent.MARKET_SUMMARY not in intents


def test_news_sector_exposure_planning(real_canonical_news_state):
    """Verify 'Which sector is most exposed?' returns news sector exposure (NOT yesterday's session performance)."""
    packet = EvidenceRouter.route_query("Which sector is most exposed to today's news?", real_canonical_news_state)
    synth = EvidenceSynthesizer.synthesize([], packet)
    plan = AnswerPlanner.build_plan(synth, packet)

    assert any("news_sector_exposures" in c for c in synth.contributions if isinstance(c, dict))
    sec_map = [c["news_sector_exposures"] for c in synth.contributions if isinstance(c, dict) and "news_sector_exposures" in c][0]
    assert "BANKING" in sec_map or "ENERGY" in sec_map
    assert "BANK NIFTY (+0.85%)" not in plan.direct_answer_lead


def test_event_calendar_planning(real_canonical_news_state):
    """Verify 'What time is the next major event?' returns scheduled event calendar items with IST timing."""
    packet = EvidenceRouter.route_query("What time is the next major event today?", real_canonical_news_state)
    synth = EvidenceSynthesizer.synthesize([], packet)
    plan = AnswerPlanner.build_plan(synth, packet)

    assert "India Trade Balance Data Release" in plan.direct_answer_lead or any("17:30 IST" in b for b in plan.primary_evidence_bullets)


def test_multi_turn_intent_accumulation_cleanliness(real_canonical_news_state):
    """Verify multi-turn queries do NOT accumulate bloated intent clutter."""
    c_id = "clean_intent_seq_test"
    LiveAssistantService.clear_history(c_id)

    res1 = LiveAssistantService.process_query("What are the top news today?", conversation_id=c_id, workstation_state=real_canonical_news_state)
    assert res1["intent"] == ["NEWS_EVENTS"] or res1["intent"] == ["NEWS_EVENTS", "FOLLOW_UP"]

    res2 = LiveAssistantService.process_query("Which sector is most exposed?", conversation_id=c_id, workstation_state=real_canonical_news_state)
    assert "BREADTH_SECTORS_HEAVYWEIGHTS" not in res2["intent"]
    assert "SESSION_HISTORY" not in res2["intent"]
    assert "NEWS_EVENTS" in res2["intent"]

    res3 = LiveAssistantService.process_query("What time is the next major event?", conversation_id=c_id, workstation_state=real_canonical_news_state)
    assert res3["answer_act"] == AnswerAct.EVENT_CALENDAR.value
    assert "SESSION_HISTORY" not in res3["intent"]
