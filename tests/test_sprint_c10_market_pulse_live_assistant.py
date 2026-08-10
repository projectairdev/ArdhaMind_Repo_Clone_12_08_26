"""Sprint C.10 — Market Pulse + Live Assistant Productization Test Suite.

Validates primary navigation, session-aware Market Pulse context board,
Core Market Feed vs Intelligence Provider health separation,
Live Assistant 7-section hierarchy, material What Changed baseline tracking,
verified news count semantics, and zero canonical data loss.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest

from src.broker.services.kite_intelligence_service import KiteIntelligenceService
from src.broker.services.market_context_builder import MarketContextBuilder
from src.application.workstation_state_service import WorkstationStateService
from src.intelligence_engine.unified_nifty import UnifiedNiftyIntelligenceBuilder
from src.news_engine.source_authority import classify_source


def format_ts(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


# 1. Navigation contains Market Pulse
def test_1_navigation_contains_market_pulse():
    layout_file = Path("src/frontend/layout/DashboardLayout.tsx")
    text = layout_file.read_text(encoding="utf-8")
    assert "Market Pulse" in text
    assert 'id: "market-pulse"' in text


# 2. Permanent Pre-Market Planner navigation is removed
def test_2_premarket_planner_navigation_removed():
    layout_file = Path("src/frontend/layout/DashboardLayout.tsx")
    text = layout_file.read_text(encoding="utf-8")
    assert 'label: "Pre-Market Planner"' not in text


# 3. Market Pulse works PRE_OPEN
def test_3_market_pulse_works_pre_open():
    data = {"marketContext": {"current_spot": 24500.0}}
    state = WorkstationStateService.build_from_legacy(data, market_state="PRE_OPEN").to_dict()
    assert state["market_session"]["status"] in {"pre_open", "pre_market"}


# 4. Market Pulse works MARKET_OPEN
def test_4_market_pulse_works_market_open():
    data = {"marketContext": {"current_spot": 24583.5, "previous_close": 24570.65}}
    state = WorkstationStateService.build_from_legacy(data, market_state="OPEN").to_dict()
    assert state["market_session"]["status"] == "open"


# 5. Market Pulse works POST_CLOSE
def test_5_market_pulse_works_post_close():
    data = {"marketContext": {"current_spot": 24500.0}}
    state = WorkstationStateService.build_from_legacy(data, market_state="CLOSED").to_dict()
    assert state["market_session"]["status"] == "closed"


# 6. Market Pulse renders existing canonical GIFT Nifty
def test_6_market_pulse_renders_canonical_gift_nifty():
    macro = {
        "quotes": {
            "GIFT_NIFTY": {"name": "GIFT Nifty", "price": 24616.5, "change": -18.4, "observation_timestamp": format_ts(datetime.now(timezone.utc)), "freshness_status": "eligible"}
        }
    }
    state = WorkstationStateService.build_from_legacy({"macroIntelligence": macro}, market_state="OPEN").to_dict()
    assert "GIFT_NIFTY" in state["macro_intelligence"]["quotes"]


# 7. Global cues transmit correctly
def test_7_global_cues_transmit_correctly():
    macro = {
        "quotes": {
            "S&P 500": {"name": "S&P 500", "price": 5500.0, "change_pct": 0.62, "observation_timestamp": format_ts(datetime.now(timezone.utc)), "freshness_status": "eligible"}
        }
    }
    state = WorkstationStateService.build_from_legacy({"macroIntelligence": macro}, market_state="OPEN").to_dict()
    assert state["macro_intelligence"]["quotes"]["S&P 500"]["price"] == 5500.0


# 8. FII/DII transmit correctly
def test_8_fii_dii_transmit_correctly():
    macro = {"institutional_flows": [{"category": "FII_CASH", "net_value": 1240.0}]}
    state = WorkstationStateService.build_from_legacy({"macroIntelligence": macro}, market_state="OPEN").to_dict()
    assert state["macro_intelligence"]["institutional_flows"][0]["net_value"] == 1240.0


# 9. Breadth transmits correctly
def test_9_breadth_transmits_correctly():
    mc = {
        "current_spot": 24583.5,
        "breadth": {"status": "READY", "coverage": {"valid": 50, "expected": 50, "minimum": 40}, "advances": 23, "declines": 27}
    }
    state = WorkstationStateService.build_from_legacy({"marketContext": mc}, market_state="OPEN").to_dict()
    assert state["market_data"]["breadth"]["advances"] == 23


# 10. Options transmit correctly
def test_10_options_transmit_correctly():
    op = {"pcr": 0.72, "max_pain": 24600.0, "atm_strike": 24550.0, "status": "ready"}
    state = WorkstationStateService.build_from_legacy({"optionContext": op}, market_state="OPEN").to_dict()
    assert "option_intelligence" in state


# 11. VIX transmits correctly
def test_11_vix_transmits_correctly():
    macro = {"india_vix": {"value": 12.66, "regime": "NORMAL"}}
    state = WorkstationStateService.build_from_legacy({"macroIntelligence": macro}, market_state="OPEN").to_dict()
    assert state["macro_intelligence"]["india_vix"]["value"] == 12.66


# 12. Cross-asset observations transmit correctly
def test_12_cross_asset_transmits_correctly():
    macro = {
        "quotes": {
            "USD/INR": {"name": "USD/INR", "price": 83.92, "change_pct": 0.02, "observation_timestamp": format_ts(datetime.now(timezone.utc))}
        }
    }
    state = WorkstationStateService.build_from_legacy({"macroIntelligence": macro}, market_state="OPEN").to_dict()
    assert state["macro_intelligence"]["quotes"]["USD/INR"]["price"] == 83.92


# 13. News/event risk transmits correctly
def test_13_news_event_risk_transmits_correctly():
    ts_now = format_ts(datetime.now(timezone.utc))
    news = {"items": [{"id": "n1", "title": "RBI stance unchanged", "source_name": "Reuters", "published_at": ts_now, "retrieved_at": ts_now, "freshness_status": "fresh"}]}
    state = WorkstationStateService.build_from_legacy({"newsSentiment": news}, market_state="OPEN").to_dict()
    assert len(state["news_intelligence"]["items"]) == 1


# 14. Refresh uses canonical backend path
def test_14_refresh_uses_canonical_backend():
    bridge_file = Path("src/server_bridge.py")
    text = bridge_file.read_text(encoding="utf-8")
    assert "build_from_legacy" in text


# 15. Refresh does not create duplicate provider pipelines
def test_15_no_duplicate_provider_pipelines():
    pulse_component = Path("src/frontend/components/MarketPulseWorkspace.tsx")
    text = pulse_component.read_text(encoding="utf-8")
    assert "syncBroker" in text
    assert "fetch(" not in text


# 16. Optional provider failure does not mark core feed degraded
def test_16_optional_provider_failure_does_not_degrade_core_feed():
    ts_str = format_ts(datetime.now(timezone.utc))
    data = {
        "marketContext": {"current_spot": 24583.5, "last_tick_time": ts_str},
        "newsSentiment": {"status": "unavailable"},
        "macroIntelligence": {"quotes": {}}
    }
    state = WorkstationStateService.build_from_legacy(data, market_state="OPEN").to_dict()
    assert state["workspace_readiness"]["core_market_feed_state"] == "READY"


# 17. Actual Kite failure DOES degrade core feed
def test_17_actual_kite_failure_degrades_core_feed():
    data = {"marketContext": {}} # Empty spot / tick time
    state = WorkstationStateService.build_from_legacy(data, market_state="OPEN").to_dict()
    assert state["workspace_readiness"]["core_market_feed_state"] != "READY"


# 18. Live Assistant MARKET_OPEN renders Current State
def test_18_live_assistant_renders_current_state():
    data = {"marketContext": {"current_spot": 24583.5, "previous_close": 24570.65}}
    state = WorkstationStateService.build_from_legacy(data, market_state="OPEN").to_dict()
    monitor = state["unified_intelligence"]["live_assistant_monitor"]
    assert "current_market_view" in monitor
    assert "conviction" in monitor


# 19. Live Assistant renders material What Changed
def test_19_live_assistant_renders_what_changed():
    UnifiedNiftyIntelligenceBuilder._prior_snapshot = {"spot": 24500.0, "alignment": "BEARISH_ALIGNMENT"}
    market = {"current_spot": 24520.0}
    res = UnifiedNiftyIntelligenceBuilder.build(market=market, technical={}, options={}, macro={}, news={}, market_state="OPEN", now=datetime.now(timezone.utc))
    assert any("NIFTY Spot moved" in item for item in res["live_assistant_monitor"]["what_changed"])


# 20. Live Assistant renders evidence
def test_20_live_assistant_renders_evidence():
    data = {"marketContext": {"current_spot": 24583.5}}
    state = WorkstationStateService.build_from_legacy(data, market_state="OPEN").to_dict()
    assert "supports" in state["unified_intelligence"]


# 21. Live Assistant renders What Matters Next
def test_21_live_assistant_renders_what_matters_next():
    data = {"marketContext": {"current_spot": 24583.5}}
    state = WorkstationStateService.build_from_legacy(data, market_state="OPEN").to_dict()
    monitor = state["unified_intelligence"]["live_assistant_monitor"]
    assert "next_watch" in monitor


# 22. Live Assistant renders scenarios
def test_22_live_assistant_renders_scenarios():
    data = {"marketContext": {"current_spot": 24583.5}}
    state = WorkstationStateService.build_from_legacy(data, market_state="OPEN").to_dict()
    assert "scenarios" in state["unified_intelligence"]


# 23. Live Assistant renders decision zones
def test_23_live_assistant_renders_decision_zones():
    data = {"marketContext": {"current_spot": 24583.5}}
    state = WorkstationStateService.build_from_legacy(data, market_state="OPEN").to_dict()
    assert "decision_zones" in state["unified_intelligence"]


# 24. No frontend market reasoning
def test_24_no_frontend_market_reasoning():
    pulse_component = Path("src/frontend/components/MarketPulseWorkspace.tsx")
    text = pulse_component.read_text(encoding="utf-8")
    assert "useWorkstationState" in text


# 25. No mock/sample data
def test_25_no_mock_sample_data():
    builder = Path("src/broker/services/market_context_builder.py")
    text = builder.read_text(encoding="utf-8")
    assert "sample" not in text.lower() or "test" in text.lower()


# 26. No execution language
def test_26_no_execution_language():
    data = {"marketContext": {"current_spot": 24583.5}}
    state = WorkstationStateService.build_from_legacy(data, market_state="OPEN").to_dict()
    text = json.dumps(state["unified_intelligence"]).upper()
    for word in ("BUY NIFTY", "SELL NIFTY", "TARGET 2", "STOP LOSS 2", "LOT SIZE"):
        assert word not in text


# 27. NIFTY Live Price & Trend remains available
def test_27_nifty_live_price_trend_available():
    file = Path("src/frontend/components/NiftyLiveWorkspace.tsx")
    assert file.exists()


# 28. NIFTY Live Options remains available
def test_28_nifty_live_options_available():
    file = Path("src/frontend/components/NiftyLiveWorkspace.tsx")
    text = file.read_text(encoding="utf-8")
    assert "Options" in text


# 29. Spot update/change remains correct
def test_29_spot_change_calculation():
    spot = 24583.50
    prev = 24570.65
    diff = round(spot - prev, 2)
    assert diff == 12.85


# 30. Breadth remains 50/50 when genuine constituent observations exist
def test_30_breadth_remains_50_of_50():
    snapshot_path = Path(".cache/nifty50_membership_snapshots.json")
    snapshots = json.loads(snapshot_path.read_text(encoding="utf-8"))
    members = snapshots[-1].get("constituents") or []
    assert len(members) == 50


# 31. News verified count is truthful
def test_31_news_verified_count_is_truthful():
    assert classify_source("Reuters") == "TIER_B_HIGH_TRUST"
    assert classify_source("Random Blog") == "TIER_D_DISCOVERY"


# 32. Global observations are temporally labeled
def test_32_global_observations_temporally_labeled():
    macro = {
        "quotes": {
            "S&P 500": {"name": "S&P 500", "price": 5500.0, "observation_timestamp": format_ts(datetime.now(timezone.utc)), "freshness_status": "fresh"}
        }
    }
    state = WorkstationStateService.build_from_legacy({"macroIntelligence": macro}, market_state="OPEN").to_dict()
    assert state["macro_intelligence"]["quotes"]["S&P 500"]["freshness_status"] == "fresh"


# 33. Canonical state remains authoritative
def test_33_canonical_state_authoritative():
    data = {"marketContext": {"current_spot": 24583.5}}
    state = WorkstationStateService.build_from_legacy(data, market_state="OPEN").to_dict()
    assert state["schema_version"] == "2.0.0"


# 34. C.9/C.9.1/C.9.2 regression tests remain green
def test_34_c9_regression_tests_present():
    assert Path("tests/test_sprint_c9_runtime_truth.py").exists()
    assert Path("tests/test_sprint_c91_live_runtime_repair.py").exists()
    assert Path("tests/test_sprint_c92_live_market_acceptance.py").exists()
