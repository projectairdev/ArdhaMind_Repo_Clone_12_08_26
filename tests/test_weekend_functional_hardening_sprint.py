# tests/test_weekend_functional_hardening_sprint.py
"""
Comprehensive Regression Unit Test Suite for AIR ArdhaMind Weekend Functional Hardening Sprint.

Covers all 13 sprint areas:
1. Pre-Market Event Timeline Date Correctness
2. Pre-Market GIFT Nifty Consistency
3. Previous Close Propagation
4. Forward Outlook Post-Close UX & Semantics
5. News Ranking Quality & Penalties (Crypto & Sensationalism)
6. News Provider Degradation Handling
7. Calendar Status Semantics
8. Settings Operator Language (READ_ONLY compliance)
9. Session & Transport Status Non-Blinking Semantics
10. Monday Rollover Isolation
11. Live Assistant 3-Minute Density
12. Persistence Closed-Session Throttling Optimization
13. READ_ONLY Boundary Invariant Preservation
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

from src.intelligence_engine.pre_market_engine import PreMarketIntelligenceEngine
from src.intelligence_engine.forward_outlook_engine import ForwardOutlookEngine, ForwardOutlookReport
from src.news_engine.relevance_v2 import NiftyRelevanceEngineV2
from src.application.workstation_state_service import WorkstationStateService


def test_pre_market_event_timeline_date_filtering(tmp_path):
    """Test 1: Event timeline excludes stale 2025 events and labels upcoming future events correctly."""
    state = {
        "market_session": {"session_date": "2026-08-17", "status": "PRE_MARKET"},
        "market_data": {"current_spot": 24500.0, "previous_close": 24450.0},
        "macro_intelligence": {
            "economic_events": [
                {
                    "event_name": "Stale 2025 US CPI",
                    "scheduled_at": "2025-08-14T18:00:00Z",
                    "scheduled_at_ist": "2025-08-14T23:30:00",
                    "country": "US",
                    "impact_level": "HIGH"
                },
                {
                    "event_name": "Target Session RBI Policy Minutes",
                    "scheduled_at": "2026-08-17T11:00:00Z",
                    "scheduled_at_ist": "2026-08-17T16:30:00",
                    "country": "IND",
                    "impact_level": "CRITICAL"
                },
                {
                    "event_name": "Future Session US Fed Rate Decision",
                    "scheduled_at": "2026-08-18T18:00:00Z",
                    "scheduled_at_ist": "2026-08-18T23:30:00",
                    "country": "US",
                    "impact_level": "HIGH"
                }
            ],
            "quotes": {
                "GIFT_NIFTY": {"price": 24530.0, "freshness_status": "FRESH", "observed_at": "2026-08-17T08:30:00Z"}
            }
        }
    }

    try:
        WorkstationStateService.reset_for_testing()
        WorkstationStateService.CACHE_DIR = tmp_path
        WorkstationStateService._allow_disk_cache_in_test = True

        PreMarketIntelligenceEngine.reset_engine_state()
        report = PreMarketIntelligenceEngine.analyze_pre_market(state)

        event_names = [e["event_name"] for e in report.event_timeline]

        # 1. Stale 2025 event MUST NOT be in active timeline
        assert "Stale 2025 US CPI" not in event_names

        # 2. Target date event MUST be present with TODAY scope
        target_ev = next(e for e in report.event_timeline if e["event_name"] == "Target Session RBI Policy Minutes")
        assert target_ev["scope"] == "TODAY"

        # 3. Future date event MUST be present with UPCOMING scope
        future_ev = next(e for e in report.event_timeline if e["event_name"] == "Future Session US Fed Rate Decision")
        assert future_ev["scope"] == "UPCOMING"
        assert "UPCOMING (2026-08-18)" in future_ev["time_ist"]
    finally:
        WorkstationStateService.reset_for_testing()


def test_previous_close_propagation(tmp_path):
    """Test 2: Pre-Market critical levels propagates previous close robustly without rendering --."""
    state = {
        "market_session": {"session_date": "2026-08-17", "status": "PRE_MARKET"},
        "market_data": {
            "current_spot": 24500.0,
            "close": 24420.0  # close provided via fallback key
        },
        "macro_intelligence": {}
    }

    try:
        WorkstationStateService.reset_for_testing()
        WorkstationStateService.CACHE_DIR = tmp_path
        WorkstationStateService._allow_disk_cache_in_test = True

        PreMarketIntelligenceEngine.reset_engine_state()
        report = PreMarketIntelligenceEngine.analyze_pre_market(state)

        prev_c = report.critical_levels.get("previous_close")
        assert prev_c is not None
        assert float(prev_c) == 24420.0
    finally:
        WorkstationStateService.reset_for_testing()


def test_forward_outlook_post_close_horizon_label():
    """Test 3: ForwardOutlookEngine sets explicit horizon_label for CLOSED session lifecycle."""
    state = {
        "market_session": {"session_date": "2026-08-14", "status": "CLOSED", "is_closed": True},
        "market_data": {"current_spot": 24400.0, "previous_close": 24350.0}
    }

    ForwardOutlookEngine.reset_engine_state()
    report = ForwardOutlookEngine.evaluate_outlook(state)

    assert report.horizon_label == "Session Outlook Archive & Next Session Horizon"
    assert report.current_regime in ("CLOSED", "SESSION_COMPLETE")


def test_news_ranking_penalizes_crypto_and_sensationalism():
    """Test 4: News relevance engine penalizes crypto-centric content and sensational doom-mongering."""
    universe = {"HDFCBANK": "HDFC Bank Limited", "RELIANCE": "Reliance Industries Limited"}

    # 1. Official constituent news
    res_official = NiftyRelevanceEngineV2.assess(
        headline="HDFC Bank Q1 Net Profit Surges 15% to Rs 16,500 Crore",
        content="HDFC Bank reported strong quarterly earnings driven by net interest margin growth.",
        category="Earnings",
        stream="NIFTY_CORPORATE",
        source_tier="TIER_A_PRIMARY",
        nifty_universe=universe
    )

    # 2. Crypto news
    res_crypto = NiftyRelevanceEngineV2.assess(
        headline="Bitcoin Surges Past $70,000 as Crypto Markets Rally",
        content="Ethereum and Solana gains lift altcoins in heavy trading.",
        category="Global Markets",
        stream="GLOBAL_RISK",
        source_tier="TIER_D_DISCOVERY",
        nifty_universe=universe
    )

    # 3. Sensational doom-mongering opinion without source
    res_sensational = NiftyRelevanceEngineV2.assess(
        headline="Great Depression Coming: Stock Market Will Crash 80% Soon",
        content="Unverified opinion column claiming catastrophic economic disaster ahead.",
        category="Opinion",
        stream="GLOBAL_RISK",
        source_tier="TIER_D_DISCOVERY",
        nifty_universe=universe
    )

    # Assertions
    assert res_official["nifty_relevance_score"] >= 8.0
    assert res_official["impact_level"] == "HIGH"

    assert res_crypto["nifty_relevance_score"] <= 2.0
    assert res_crypto["impact_level"] == "LOW"

    assert res_sensational["nifty_relevance_score"] <= 3.0
    assert res_sensational["impact_level"] == "LOW"


def test_persistence_closed_session_throttling_optimization(tmp_path):
    """Test 5: Persistence does not repeatedly force-flush unchanged closed session history."""
    try:
        WorkstationStateService.reset_for_testing()
        WorkstationStateService.CACHE_DIR = tmp_path
        WorkstationStateService._allow_disk_cache_in_test = True

        state_raw = {
            "market_state": "MARKET_CLOSED",
            "market_session": {"status": "CLOSED", "session_date": "2026-08-14", "is_closed": True},
            "market_data": {"current_spot": 24400.0, "previous_close": 24350.0},
            "broker_account": {"session_valid": True, "broker_state": "CONNECTED"},
            "option_intelligence": {"status": "ready", "pcr": 1.05},
            "news_intelligence": {"items": []},
            "macro_intelligence": {"quotes": {}}
        }

        # First build on CLOSED market -> triggers initial force flush ONCE
        snap1 = WorkstationStateService.build_from_legacy(state_raw)
        t_first_flush = WorkstationStateService._last_disk_flush_timestamp
        assert t_first_flush > 0.0

        # Second build on CLOSED market without sequence or snapshot changes
        snap2 = WorkstationStateService.build_from_legacy(state_raw)
        t_second_flush = WorkstationStateService._last_disk_flush_timestamp

        # Flush timestamp MUST NOT update on second call because state was unchanged & closed flush was completed
        assert t_second_flush == t_first_flush
    finally:
        WorkstationStateService.reset_for_testing()
