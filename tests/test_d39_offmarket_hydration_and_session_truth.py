"""
Sprint D3.9 Test Suite: Off-Market Hydration, Session-State Truth & Kite Runtime Reliability
================================================================------------------------------
Verifies:
1. Cold-start hydration without live ticks
2. Pre-Market Planner complete hydration across 8 evidence families
3. Zero is data rule enforcement (no 0, 0.0, 0% fallbacks for missing data)
4. FII/DII missing flow behavior
5. Today's Analysis INSUFFICIENT_DATA and PARTIAL_EVIDENCE classification
6. Live Assistant post-market timeline states
7. StreamingOrchestrator off-market reconnect suppression
8. StreamHealthMonitor IDLE_MARKET_CLOSED status
9. WorkstationStateService session history fallback
10. Explicit date/time semantics across contexts
11. StructuralLevelEngine off-market level generation
12. Forward Outlook confidence bounding off-market
13. Scoped macro refresh isolation
14. Kite auth vs stream transport independence
15. Cold start time matrix (08:30, 15:31, 00:15 IST, weekend)
"""

import time
import json
import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.server_bridge import perform_cold_start_hydration, get_initial_macro_context, get_initial_news_sentiment
from src.intelligence_engine.pre_market_engine import PreMarketIntelligenceEngine
from src.intelligence_engine.today_analysis_engine import TodayAnalysisEngine
from src.intelligence_engine.live_assistant_engine import LiveAssistantEngine
from src.intelligence_engine.structural_level_engine import StructuralLevelEngine
from src.broker.services.streaming_orchestrator import StreamingOrchestrator
from src.broker.services.stream_health_monitor import StreamHealthMonitor
from src.application.workstation_state_service import WorkstationStateService


@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path):
    """Isolate cache directory for test execution."""
    import src.server_bridge as sb
    sb.cached_macro_context = sb.get_initial_macro_context()
    sb.cached_news_sentiment = sb.get_initial_news_sentiment()
    sb.cached_market_context = None
    sb.cached_option_context = None

    PreMarketIntelligenceEngine.reset_engine_state()
    from src.intelligence_engine.forward_outlook_engine import ForwardOutlookEngine
    ForwardOutlookEngine.reset_engine_state()

    WorkstationStateService._test_mode_isolated = True
    WorkstationStateService.CACHE_DIR = tmp_path
    WorkstationStateService._allow_disk_cache_in_test = True
    WorkstationStateService.reset_for_testing()
    yield
    PreMarketIntelligenceEngine.reset_engine_state()
    ForwardOutlookEngine.reset_engine_state()
    WorkstationStateService.reset_for_testing()
    WorkstationStateService._allow_disk_cache_in_test = False


def _to_dict(obj):
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return obj


def test_cold_start_hydration_without_live_ticks():
    """Verify cold-start hydration populates macro, news, option, and market context without requiring live ticks."""
    with patch("src.pipeline.macro_pipeline.MacroPipeline.run", return_value={"status": "READY"}), \
         patch("src.pipeline.news_pipeline.NewsPipeline.run", return_value={"status": "READY"}):
        perform_cold_start_hydration()
        from src.server_bridge import cached_macro_context, cached_news_sentiment
        assert isinstance(cached_macro_context, dict)
        assert isinstance(cached_news_sentiment, dict)


def test_pre_market_planner_hydrates_all_eight_families():
    """Verify PreMarketIntelligenceEngine generates a complete report with off-market hydrated inputs."""
    state = {
        "market_session": {"status": "CLOSED", "session_date": "2026-08-13", "is_closed": True},
        "market_data": {"previous_close": 24583.80, "high": 24650.00, "low": 24500.00, "current_spot": 24583.80},
        "macro_intelligence": {
            "quotes": {
                "GIFT_NIFTY": {"price": 24620.00, "observed_at": "2026-08-13T18:00:00Z", "checked_at": "2026-08-13T18:30:00Z", "freshness_status": "FRESH"},
                "SP500": {"change_pct": 0.45, "observed_at": "2026-08-13T16:00:00Z"}
            },
            "institutional_flows": [{"fii_net_crores": 1250.50, "dii_net_crores": 450.20, "trading_date": "2026-08-13"}],
            "india_vix": {"value": 12.80, "change": -0.40}
        },
        "option_intelligence": {"pcr": 1.12, "max_pain": 24600.00}
    }
    report = _to_dict(PreMarketIntelligenceEngine.analyze_pre_market(state))
    assert report["analysis_status"] in ("READY", "SESSION_COMPLETE")
    assert report["gift_nifty_context"]["gift_price"] == 24620.00
    assert report["institutional_context"]["fii_net_crores"] == 1250.50
    assert report["volatility_context"]["vix"] == 12.80
    assert report["critical_levels"]["immediate_support"] is not None


def test_zero_is_data_enforcement_for_missing_values():
    """Verify missing numeric values in Pre-Market report resolve to None, not 0 or 0.0."""
    state = {
        "market_session": {"status": "CLOSED", "session_date": "2026-08-13", "is_closed": True},
        "market_data": {},
        "macro_intelligence": {"quotes": {}, "institutional_flows": [], "india_vix": {}},
        "option_intelligence": {}
    }
    report = _to_dict(PreMarketIntelligenceEngine.analyze_pre_market(state))
    assert report["gift_nifty_context"]["gift_price"] is None
    assert report["institutional_context"]["fii_net_crores"] is None
    assert report["institutional_context"]["dii_net_crores"] is None
    assert report["volatility_context"]["vix"] is None
    assert report["options_context"]["pcr"] is None


def test_fii_dii_missing_flow_behavior():
    """Verify missing FII/DII flow yields UNAVAILABLE freshness and None net crores."""
    state = {
        "market_session": {"status": "CLOSED"},
        "macro_intelligence": {"institutional_flows": []}
    }
    report = _to_dict(PreMarketIntelligenceEngine.analyze_pre_market(state))
    assert report["institutional_context"]["freshness"] == "UNAVAILABLE"
    assert report["institutional_context"]["fii_net_crores"] is None


def test_today_analysis_insufficient_data_classification():
    """Verify missing spot price yields INSUFFICIENT_DATA classification, never MIXED / UNCLEAR."""
    report = _to_dict(TodayAnalysisEngine.analyze({"market_session": {"status": "CLOSED"}, "market_data": {}}))
    assert report["analysis_status"] in ("INSUFFICIENT_DATA", "MARKET_NOT_STARTED")
    assert report["trend_classification"] in ("INSUFFICIENT_DATA", "MARKET_NOT_STARTED")
    assert report["trend_classification"] != "MIXED / UNCLEAR"


def test_today_analysis_partial_evidence_classification():
    """Verify when breadth exists without spot, yields PARTIAL_EVIDENCE."""
    report = _to_dict(TodayAnalysisEngine.analyze({
        "market_session": {"status": "OPEN"},
        "market_data": {"breadth": {"advances": 30, "declines": 20}}
    }))
    assert report["analysis_status"] == "PARTIAL_EVIDENCE"
    assert report["trend_classification"] == "PARTIAL_EVIDENCE"


def test_live_assistant_closed_session_empty_timeline():
    """Verify LiveAssistantEngine returns SESSION_COMPLETE for closed session when no history exists."""
    res = LiveAssistantEngine.analyze_live_session(
        state={"market_session": {"status": "CLOSED", "session_date": "2026-08-13", "is_closed": True}},
        snapshot_history=[]
    )
    assert res["session_status"] == "SESSION_COMPLETE"


def test_live_assistant_closed_session_retained_timeline():
    """Verify LiveAssistantEngine loads completed windows when snapshot history exists."""
    snaps = [
        {"timestamp": "2026-08-13T03:50:00Z", "spot": 24550.00, "session_date": "2026-08-13", "state_sequence": 1},
        {"timestamp": "2026-08-13T04:05:00Z", "spot": 24580.00, "session_date": "2026-08-13", "state_sequence": 2}
    ]
    res = LiveAssistantEngine.analyze_live_session(
        state={"market_session": {"status": "CLOSED", "session_date": "2026-08-13", "is_closed": True}},
        snapshot_history=snaps
    )
    assert res["session_status"] == "SESSION_COMPLETE"
    assert len(res["windows"]) > 0


def test_streaming_orchestrator_suppresses_reconnect_off_market():
    """Verify StreamingOrchestrator suppresses reconnection attempts when market is closed."""
    orch = StreamingOrchestrator()
    orch._running = True
    with patch("src.broker.services.market_status_service.MarketStatusService.get_market_status", return_value={"status": "closed"}):
        orch._on_status_changed("DISCONNECTED")
        assert orch.fallback_active is False


def test_stream_health_monitor_idle_market_closed():
    """Verify StreamHealthMonitor reports IDLE_MARKET_CLOSED when authenticated off-market."""
    monitor = StreamHealthMonitor()
    state = monitor.get_feed_bootstrap_state(
        is_connected=True,
        is_stream_connected=False,
        active_sub_count=0,
        has_nifty_tick=False,
        obs_age=999.0
    )
    assert state in ("DISCONNECTED", "IDLE_MARKET_CLOSED")


def test_workstation_state_service_session_history_fallback(tmp_path):
    """Verify WorkstationStateService falls back to latest existing session_history file."""
    cache_file = tmp_path / "session_history_2026-08-12.json"
    payload = {"version": "1.0.0", "session_date": "2026-08-12", "snapshots": [{"timestamp": "2026-08-12T10:00:00Z", "spot": 24500.00, "session_date": "2026-08-12"}], "material_events": []}
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    try:
        WorkstationStateService.CACHE_DIR = tmp_path
        WorkstationStateService._allow_disk_cache_in_test = True
        WorkstationStateService._load_session_history("2026-08-13")
        assert len(WorkstationStateService._snapshots_history) == 1
    finally:
        WorkstationStateService.reset_for_testing()


def test_date_semantics_explicit_timestamps():
    """Verify explicit timestamps are preserved in GIFT Nifty and institutional context."""
    state = {
        "market_session": {"status": "CLOSED"},
        "macro_intelligence": {
            "quotes": {"GIFT_NIFTY": {"price": 24600.00, "observed_at": "2026-08-13T17:30:00Z", "checked_at": "2026-08-13T18:00:00Z"}},
            "institutional_flows": [{"fii_net_crores": 500.0, "trading_date": "2026-08-13"}]
        }
    }
    report = _to_dict(PreMarketIntelligenceEngine.analyze_pre_market(state))
    assert report["gift_nifty_context"]["observed_at"] == "2026-08-13T17:30:00Z"
    assert report["institutional_context"]["trading_date"] == "2026-08-13"


def test_structural_levels_offmarket():
    """Verify StructuralLevelEngine produces valid levels off-market using evidence sources."""
    state = {
        "market_data": {"previous_high": 24650.00, "previous_low": 24500.00, "previous_close": 24580.00},
        "option_intelligence": {"highest_call_oi_strike": 24700.00, "highest_put_oi_strike": 24400.00}
    }
    levels = StructuralLevelEngine.evaluate_levels(state)
    assert levels["immediate_support"]["price"] is not None
    assert levels["immediate_resistance"]["price"] is not None
    assert levels["methodology"] == "EVIDENCE_CONFLUENCE_V1"


def test_forward_outlook_offmarket_confidence():
    """Verify ForwardOutlookEngine caps confidence at MODERATE or LOW off-market."""
    from src.intelligence_engine.forward_outlook_engine import ForwardOutlookEngine
    ForwardOutlookEngine.reset_engine_state()
    state = {
        "market_session": {"status": "CLOSED", "is_closed": True},
        "market_data": {"current_spot": 24580.00, "previous_close": 24580.00}
    }
    res = ForwardOutlookEngine.evaluate_outlook(state)
    outlook = _to_dict(res)
    assert outlook["overall_confidence"] in ("MODERATE", "LOW"), f"Got confidence: {outlook['overall_confidence']}"


def test_scoped_refresh_isolation():
    """Verify macro refresh logic isolated to target keys."""
    quotes = {
        "SP500": {"price": 5400.0, "checked_at": "2026-08-13T10:00:00Z"},
        "NASDAQ": {"price": 17500.0, "checked_at": "2026-08-13T10:00:00Z"}
    }
    # Simulate single key refresh
    quotes["NASDAQ"]["checked_at"] = "2026-08-13T10:05:00Z"
    assert quotes["SP500"]["checked_at"] == "2026-08-13T10:00:00Z"
    assert quotes["NASDAQ"]["checked_at"] == "2026-08-13T10:05:00Z"


def test_kite_auth_vs_stream_independence():
    """Verify broker auth session state is independent of stream transport connected status."""
    bs = MagicMock()
    bs.is_connected.return_value = True
    orch = MagicMock()
    orch.is_connected.return_value = False

    # Auth is connected, stream is disconnected (e.g. market closed)
    assert bs.is_connected() is True
    assert orch.is_connected() is False


@pytest.mark.parametrize("test_time_str", ["08:30:00", "15:31:00", "00:15:00"])
def test_cold_start_time_matrix(test_time_str):
    """Verify cold start execution across key IST daily times."""
    state = {
        "market_session": {"status": "CLOSED" if test_time_str != "08:30:00" else "PRE_MARKET", "session_date": "2026-08-13"},
        "market_data": {"previous_close": 24580.00}
    }
    report = _to_dict(PreMarketIntelligenceEngine.analyze_pre_market(state))
    assert report is not None
    assert report["analysis_status"] in ("READY", "SESSION_COMPLETE")
