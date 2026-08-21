"""
test_live_assistant_null_safety.py

Targeted regression tests for LiveAssistantEngine null-safety, canonical state resilience,
data truth invariants, and broker readiness propagation.
"""
from datetime import datetime, timezone
import pytest
from src.intelligence_engine.live_assistant_engine import LiveAssistantEngine, MarketWindowAnalysis
from src.application.workstation_state_service import WorkstationStateService


def create_sample_state(market_session_status="OPEN", spot=24500.0, broker_state="CONNECTED"):
    now_str = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "workspaceContext": {
            "currentMode": "READ_ONLY",
            "brokerState": broker_state,
            "marketState": market_session_status,
            "brokerType": "ZERODHA",
            "marketDataSource": "LIVE",
            "timestamp": now_str
        },
        "market_session": {
            "status": market_session_status,
            "is_closed": market_session_status in ("CLOSED", "HOLIDAY", "POST_CLOSE"),
            "session_date": "2026-08-16"
        },
        "marketContext": {
            "current_spot": spot,
            "previous_close": 24450.0 if spot else None,
            "last_tick_time": now_str,
            "breadth": {"advances": 30, "declines": 20, "valid_observations": 50} if spot else {}
        },
        "macroIntelligence": {
            "india_vix": {"value": 13.5, "regime": "LOW"}
        },
        "newsSentiment": {"status": "ready", "items": []}
    }


def get_broker_status_str(canonical_dict):
    bs = canonical_dict.get("broker_status") or {}
    if isinstance(bs, dict):
        return str(bs.get("status") or "").upper()
    return str(bs).upper()


def test_live_assistant_normal_numeric_end_spot():
    state = create_sample_state(spot=24500.0)
    snaps = [
        {"session_date": "2026-08-16", "timestamp": "2026-08-16T09:16:00Z", "spot": 24480.0, "breadth": {"advances": 25, "declines": 25}},
        {"session_date": "2026-08-16", "timestamp": "2026-08-16T09:29:00Z", "spot": 24500.0, "breadth": {"advances": 30, "declines": 20}}
    ]
    res = LiveAssistantEngine.analyze_live_session(state, snaps)
    assert res["session_status"] in ("LIVE_MONITORING", "SESSION_COMPLETE")
    assert isinstance(res["windows"], list)


def test_live_assistant_end_spot_none_session_complete():
    state = create_sample_state(market_session_status="CLOSED", spot=None)
    snaps = []
    res = LiveAssistantEngine.analyze_live_session(state, snaps)
    assert res["session_status"] == "SESSION_COMPLETE"
    for w in res["windows"]:
        assert w["end_spot"] is None
        for txt in w["watch_next"]:
            assert "None" not in txt
            assert "0.00" not in txt or "span" in txt


def test_live_assistant_holiday_session():
    state = create_sample_state(market_session_status="HOLIDAY", spot=None, broker_state="DISCONNECTED")
    snaps = []
    res = LiveAssistantEngine.analyze_live_session(state, snaps)
    assert res["session_status"] == "SESSION_COMPLETE"
    for w in res["windows"]:
        assert w["start_spot"] is None
        assert w["end_spot"] is None


def test_live_assistant_disconnected_broker():
    state = create_sample_state(market_session_status="CLOSED", spot=None, broker_state="DISCONNECTED")
    canonical = WorkstationStateService.build_from_legacy(state, broker_state="DISCONNECTED", market_state="CLOSED")
    d = canonical.to_dict()
    assert get_broker_status_str(d) == "DISCONNECTED"
    assert d["unified_intelligence"]["live_assistant_intelligence"]["session_status"] == "SESSION_COMPLETE"


def test_live_assistant_no_valid_session_observations():
    state = create_sample_state(market_session_status="CLOSED", spot=None)
    snaps = []
    analysis = LiveAssistantEngine._build_window_analysis(
        "09:15", "09:30", snaps, is_completed=True, is_session_closed=True, session_date="2026-08-16"
    )
    assert analysis.end_spot is None
    assert analysis.price_change_points is None
    assert "spot unavailable" in analysis.watch_next[0].lower()


def test_completed_session_with_valid_final_observation():
    state = create_sample_state(market_session_status="CLOSED", spot=24520.0)
    snaps = [
        {"session_date": "2026-08-16", "timestamp": "2026-08-16T15:29:00Z", "spot": 24520.0, "breadth": {"advances": 32, "declines": 18}}
    ]
    res = LiveAssistantEngine.analyze_live_session(state, snaps)
    assert res["session_status"] == "SESSION_COMPLETE"


def test_missing_nifty_spot_cannot_become_zero():
    state = create_sample_state(spot=None)
    canonical = WorkstationStateService.build_from_legacy(state, broker_state="DISCONNECTED", market_state="CLOSED")
    d = canonical.to_dict()
    spot_val = d["market_data"].get("current_spot")
    assert spot_val is None or spot_val == "Unavailable"


def test_missing_fii_dii_cannot_become_fabricated():
    state = create_sample_state()
    state["macroIntelligence"]["institutional_flows"] = []
    canonical = WorkstationStateService.build_from_legacy(state, broker_state="DISCONNECTED", market_state="CLOSED")
    d = canonical.to_dict()
    flows = d["macro_intelligence"].get("institutional_flows") or []
    assert len(flows) == 0 or all(f.get("net_value") is None for f in flows)


def test_missing_trend_evidence_cannot_become_bullish():
    state = create_sample_state(spot=None)
    state["marketContext"]["trend"] = None
    state["marketContext"]["trend_direction"] = None
    canonical = WorkstationStateService.build_from_legacy(state, broker_state="DISCONNECTED", market_state="CLOSED")
    d = canonical.to_dict()
    trend = d["market_data"].get("trend") or d["market_data"].get("trend_direction")
    assert trend in (None, "UNAVAILABLE", "INSUFFICIENT_EVIDENCE", "Unavailable")


def test_successful_kite_profile_validation_propagates_broker_readiness():
    state = create_sample_state(broker_state="CONNECTED")
    canonical = WorkstationStateService.build_from_legacy(state, broker_state="CONNECTED", market_state="OPEN")
    d = canonical.to_dict()
    assert get_broker_status_str(d) == "CONNECTED"
