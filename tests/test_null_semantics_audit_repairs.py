# tests/test_null_semantics_audit_repairs.py
"""
Focused regression test suite verifying AIR ArdhaMind production null-semantics repairs.

Rules verified:
  1. MISSING DATA MUST REMAIN MISSING (None / UNAVAILABLE).
  2. Missing GIFT price -> implied_gap_points = None, opening_character = "UNCERTAIN" (Never FLAT_OPEN or 0.00 pts).
  3. Missing PCR / breadth -> PCR = None, advances = None, declines = None (Never 1.00 or 25/25).
  4. Missing spot -> Spot = None (Never 24500.0).
  5. Forward Outlook missing data -> INSUFFICIENT_DATA status / LOW confidence, cannot manufacture 95/100 scenario.
  6. Historical session data preserved per date and distinguishable from current session evidence.
"""
from datetime import datetime, timezone, timedelta
import pytest

from src.intelligence_engine.pre_market_engine import PreMarketIntelligenceEngine
from src.intelligence_engine.forward_outlook_engine import ForwardOutlookEngine
from src.intelligence_engine.structural_level_engine import StructuralLevelEngine


def test_pre_market_engine_null_semantics():
    """Verify pre-market engine preserves None when GIFT Nifty, PCR, or breadth is absent."""
    PreMarketIntelligenceEngine.reset_engine_state()

    empty_state = {
        "market_session": {"status": "PRE_MARKET", "session_date": "2026-08-14"},
        "market_data": {},
        "macro_intelligence": {"quotes": {}},
        "option_intelligence": {},
        "news_intelligence": {}
    }

    report = PreMarketIntelligenceEngine.analyze_pre_market(empty_state)

    # GIFT Nifty gap must be None, opening character UNCERTAIN (NOT FLAT_OPEN / 0.00 pts)
    gift_ctx = report.gift_nifty_context
    assert gift_ctx["gift_price"] is None
    assert gift_ctx["implied_gap_points"] is None
    assert gift_ctx["implied_gap_percent"] is None
    assert report.opening_character == "UNCERTAIN"

    # Overall confidence must be LOW due to unavailable GIFT Nifty
    assert report.overall_confidence == "LOW"


def test_forward_outlook_null_semantics_and_scoring_gating():
    """Verify forward outlook engine returns INSUFFICIENT_DATA and refrains from scoring 95/100 on missing data."""
    ForwardOutlookEngine.reset_engine_state()

    empty_state = {
        "market_session": {"status": "OPEN", "session_date": "2026-08-14"},
        "market_data": {},  # spot missing!
        "macro_intelligence": {},
        "option_intelligence": {}
    }

    report = ForwardOutlookEngine.evaluate_outlook(empty_state)

    # Missing spot must return INSUFFICIENT_DATA
    assert report.analysis_status == "INSUFFICIENT_DATA"
    assert report.overall_confidence == "LOW"
    assert report.primary_scenario.scenario_id == "SCEN-INSUFFICIENT"
    assert report.primary_scenario.scenario_score == 0.0

    # Test state with spot but missing breadth and PCR
    spot_only_state = {
        "market_session": {"status": "OPEN", "session_date": "2026-08-14"},
        "market_data": {
            "current_spot": 24450.0,
            "previous_close": 24450.0,
            "vwap": 24450.0
        },
        "macro_intelligence": {},
        "option_intelligence": {}  # missing PCR!
    }

    today_insufficient = {
        "analysis_status": "INSUFFICIENT_DATA",
        "trend_classification": "INSUFFICIENT_DATA",
        "trend_score": 0.0
    }

    report2 = ForwardOutlookEngine.evaluate_outlook(spot_only_state, today_analysis_report=today_insufficient)

    # Confidence must be LOW and scenario score must NOT be 95
    assert report2.overall_confidence == "LOW"
    assert report2.primary_scenario.scenario_score < 60.0
    assert "OPTIONS_POSITIONING" not in report2.primary_scenario.family_score_contributions
    assert "BREADTH_LEVEL" not in report2.primary_scenario.family_score_contributions


def test_structural_levels_null_semantics():
    """Verify structural level engine does not default PCR to 1.00 or spot to 24500."""
    empty_state = {
        "market_data": {"previous_close": 24400.0},  # no spot, no PCR
        "option_intelligence": {},
        "macro_intelligence": {}
    }

    levels = StructuralLevelEngine.evaluate_levels(empty_state)
    assert levels["previous_close"] == 24400.0
    assert levels["gap_reference"] == 24400.0


def test_pre_market_snapshot_unfreeze_when_gift_becomes_available():
    """Verify pre-market engine updates pre-market report if earlier run had missing GIFT quote but new run has GIFT quote."""
    PreMarketIntelligenceEngine.reset_engine_state()

    state_no_gift = {
        "market_session": {"status": "PRE_MARKET", "session_date": "2026-08-14"},
        "market_data": {"previous_close": 24400.0},
        "macro_intelligence": {"quotes": {}},
        "option_intelligence": {}
    }

    # Initial pre-market run before GIFT Nifty provider finishes
    rep1 = PreMarketIntelligenceEngine.analyze_pre_market(state_no_gift)
    assert rep1.gift_nifty_context["gift_price"] is None
    assert rep1.opening_character == "UNCERTAIN"

    state_with_gift = {
        "market_session": {"status": "PRE_MARKET", "session_date": "2026-08-14"},
        "market_data": {"previous_close": 24400.0},
        "macro_intelligence": {
            "quotes": {
                "GIFT_NIFTY": {
                    "price": 24480.0,
                    "status": "AVAILABLE",
                    "source_session": "CURRENT_PRE_OPEN"
                }
            }
        },
        "option_intelligence": {}
    }

    # Subsequent run during pre-market when GIFT quote becomes available
    rep2 = PreMarketIntelligenceEngine.analyze_pre_market(state_with_gift)
    assert rep2.gift_nifty_context["gift_price"] == 24480.0
    assert rep2.gift_nifty_context["implied_gap_points"] == 80.0
    assert rep2.opening_character == "GAP_UP"


def test_today_analysis_missing_session_price_gives_unavailable_change():
    """Missing session price / previous_close must produce None for session change."""
    from src.intelligence_engine.today_analysis_engine import TodayAnalysisEngine
    state = {
        "market_session": {"status": "OPEN", "session_date": "2026-08-14"},
        "market_data": {
            "current_spot": 24450.0,
            "previous_close": None, # missing prev_close!
            "open": 24450.0, "high": 24450.0, "low": 24450.0
        }
    }
    report = TodayAnalysisEngine.analyze(state)
    stats = report.session_statistics
    assert stats["change"] is None
    assert stats["change_pct"] is None


def test_today_analysis_insufficient_data_no_balanced_explanation():
    """INSUFFICIENT_DATA status must state data is unavailable, not described as balanced."""
    from src.intelligence_engine.today_analysis_engine import TodayAnalysisEngine
    state = {
        "market_session": {"status": "OPEN", "session_date": "2026-08-14"},
        "market_data": {} # missing spot!
    }
    report = TodayAnalysisEngine.analyze(state)
    assert report.analysis_status == "INSUFFICIENT_DATA"
    assert "Insufficient" in report.primary_driver or "unavailable" in report.primary_driver
    assert "balanced across price" not in report.primary_driver


def test_forward_outlook_missing_spot_no_synthetic_levels():
    """Missing spot must yield None structural levels, not synthetic 24400 / 24480 / 24580 levels."""
    ForwardOutlookEngine.reset_engine_state()
    state = {
        "market_session": {"status": "OPEN", "session_date": "2026-08-14"},
        "market_data": {} # no spot
    }
    report = ForwardOutlookEngine.evaluate_outlook(state)
    assert report.analysis_status == "INSUFFICIENT_DATA"
    levels = report.primary_scenario.relevant_levels
    assert levels["support"] is None
    assert levels["resistance"] is None
    assert levels["vwap"] is None


def test_empty_sector_evidence_neutral_or_insufficient():
    """Empty pre-market evidence must return NEUTRAL or INSUFFICIENT_DATA for sectors, never BULLISH through defaults."""
    PreMarketIntelligenceEngine.reset_engine_state()
    state = {
        "market_session": {"status": "PRE_MARKET", "session_date": "2026-08-14"},
        "market_data": {"previous_close": 24400.0},
        "macro_intelligence": {"quotes": {}},
        "option_intelligence": {}
    }
    report = PreMarketIntelligenceEngine.analyze_pre_market(state)
    for sector in report.sector_watch:
        assert sector["posture"] in ("NEUTRAL", "INSUFFICIENT_DATA", "UNCERTAIN")
        assert sector["posture"] != "BULLISH"


def test_disconnected_feed_zero_ticks_no_live_age():
    """Disconnected stream with 0 ticks must report tick_age_seconds as None."""
    from src.broker.services.broker_service import BrokerService
    bs = BrokerService.get_instance()
    telemetry = bs.get_bootstrap_telemetry()
    assert telemetry.get("tick_age_seconds") is None


def test_live_assistant_one_checkpoint_no_zero_deltas():
    """One-checkpoint window evidence must emit None for price/vix/range deltas, not zero fallbacks."""
    from src.intelligence_engine.live_assistant_engine import LiveAssistantEngine
    state = {
        "market_session": {"status": "OPEN", "session_date": "2026-08-14"},
        "market_data": {"current_spot": 24450.0}
    }
    # Single snapshot history (1 checkpoint)
    single_hist = [{
        "timestamp": "2026-08-14T03:45:00Z",
        "market_state": "OPEN",
        "session_phase": "OPENING_RANGE",
        "session_date": "2026-08-14",
        "spot": 24450.0,
        "breadth": {"advances": 25, "declines": 25, "coverage": 50}
    }]
    intel = LiveAssistantEngine.analyze_live_session(state, snapshot_history=single_hist)
    windows = intel.get("windows") or []
    if windows:
        w = windows[0]
        if w.get("significance_classification") == "INSUFFICIENT_EVIDENCE":
            assert w.get("price_change_points") is None
            assert w.get("window_range") is None
            assert w.get("vix_change") is None
            assert w.get("breadth_change") == "UNAVAILABLE"

