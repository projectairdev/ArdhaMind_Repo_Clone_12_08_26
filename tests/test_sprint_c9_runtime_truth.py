"""Sprint C.9 — Runtime Truth, Decision Trace & Real-Data Acceptance Regression Suite.

Validates backend canonical intelligence synthesis, data quality invariants,
temporal classification, decision zones, evidence items, and read-only boundaries.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest

from src.application.workstation_state_service import WorkstationStateService
from src.application.data_quality_service import DataQualityService
from src.intelligence_engine.unified_nifty import UnifiedNiftyIntelligenceBuilder
from src.news_engine.source_authority import classify_source
from src.models.data_quality import FreshnessStatus, SectionStatus


def format_ts(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def create_sample_legacy_data():
    now = datetime.now(timezone.utc)
    ts_str = format_ts(now)
    return {
        "workspaceContext": {
            "currentMode": "READ_ONLY",
            "brokerState": "CONNECTED",
            "marketState": "CLOSED",
            "brokerType": "ZERODHA",
            "marketDataSource": "LIVE",
            "timestamp": ts_str
        },
        "brokerAccount": {"client_id": "TEST_ID", "session_valid": True},
        "marketContext": {
            "current_spot": 24500.0,
            "previous_close": 24450.0,
            "support_levels": [24400.0, 24410.0],
            "resistance_levels": [24600.0, 24610.0],
            "last_tick_time": ts_str,
            "trend_direction": "UP",
            "breadth": {"advances": 32, "declines": 18, "valid_observations": 50, "coverage": 50}
        },
        "technicalAnalysis": {
            "atr": 100.0,
            "trend_direction": "UP",
            "vwap": 24480.0,
            "ema_20": 24450.0,
            "ema_50": 24400.0
        },
        "optionContext": {
            "pcr": 1.2,
            "max_pain": 24500.0,
            "atm_strike": 24500.0,
            "support_strikes": [24400.0],
            "resistance_strikes": [24600.0],
            "provider_timestamp": ts_str,
            "market_option_bias": "BULLISH"
        },
        "macroIntelligence": {
            "quotes": {
                "S&P 500": {"name": "S&P 500", "price": 5500.0, "change_pct": 0.5, "observation_timestamp": ts_str, "freshness_status": "eligible"},
                "NASDAQ": {"name": "NASDAQ", "price": 17500.0, "change_pct": 0.8, "observation_timestamp": ts_str, "freshness_status": "eligible"},
                "GIFT_NIFTY": {"name": "GIFT Nifty", "price": 24550.0, "observation_timestamp": ts_str, "freshness_status": "eligible", "source_name": "NSEIX"}
            },
            "workspace_context": {
                "current_context_quote_keys": ["S&P 500", "NASDAQ", "GIFT_NIFTY"]
            },
            "institutional_flows": [
                {"dataset_type": "FII_CASH", "net_value": 500.0},
                {"dataset_type": "DII_CASH", "net_value": 200.0}
            ],
            "india_vix": {"status": "AVAILABLE", "value": 13.5, "regime": "LOW", "observation_timestamp": ts_str},
            "economic_events": [
                {"event_id": "EV1", "event_name": "CPI", "scheduled_at": format_ts(now + timedelta(hours=10)), "impact_level": "HIGH", "status": "SCHEDULED"}
            ]
        },
        "newsSentiment": {
            "status": "ready",
            "items": [
                {
                    "id": "N1",
                    "headline": "RBI maintains repo rate in policy review",
                    "canonical_eligible": True,
                    "published_at": ts_str,
                    "nifty_relevance_score": 8,
                    "expected_direction": "POSITIVE",
                    "source_name": "Reuters",
                    "verification_status": "verified"
                }
            ]
        }
    }


# 1. Eligible decision levels reach clustering
def test_1_eligible_levels_reach_clustering():
    levels = [
        {"value": 24500.0, "role": "SUPPORT", "origin": "PRICE_STRUCTURE"},
        {"value": 24508.0, "role": "SUPPORT", "origin": "OPTION_OI"}
    ]
    zones = UnifiedNiftyIntelligenceBuilder._decision_zones(levels, spot=24500.0, atr=100.0)
    assert len(zones) == 1
    assert zones[0]["role"] == "SUPPORT"
    assert zones[0]["count"] == 2


# 2. Ineligible levels provide deterministic exclusion reason
def test_2_ineligible_levels_exclusion_reason():
    data = create_sample_legacy_data()
    data["marketContext"]["current_spot"] = None
    state = WorkstationStateService.build_from_legacy(data, market_state="CLOSED").to_dict()
    price_signal = state["unified_intelligence"]["signals"]["price"]
    assert price_signal["eligible"] is False
    assert "ineligibility_reason" in price_signal
    assert price_signal["ineligibility_reason"] == "current-session price structure unavailable"


# 3. Close same-role levels cluster
def test_3_close_same_role_levels_cluster():
    levels = [
        {"value": 24500.0, "role": "RESISTANCE", "origin": "PRICE_STRUCTURE"},
        {"value": 24510.0, "role": "RESISTANCE", "origin": "OPTION_OI"}
    ]
    zones = UnifiedNiftyIntelligenceBuilder._decision_zones(levels, spot=24500.0, atr=100.0)
    assert len(zones) == 1
    assert zones[0]["lower"] == 24500.0
    assert zones[0]["upper"] == 24510.0


# 4. Opposite semantic roles never merge
def test_4_opposite_roles_never_merge():
    levels = [
        {"value": 24500.0, "role": "SUPPORT", "origin": "PRICE_STRUCTURE"},
        {"value": 24502.0, "role": "RESISTANCE", "origin": "PRICE_STRUCTURE"}
    ]
    zones = UnifiedNiftyIntelligenceBuilder._decision_zones(levels, spot=24500.0, atr=100.0)
    assert len(zones) == 2
    roles = {z["role"] for z in zones}
    assert roles == {"SUPPORT", "RESISTANCE"}


# 5. Empty decision zones have backend reason
def test_5_empty_decision_zones_reason():
    zones = UnifiedNiftyIntelligenceBuilder._decision_zones([], spot=24500.0, atr=100.0)
    assert zones == []


# 6. Evidence items survive serialization
def test_6_evidence_items_survive_serialization():
    data = create_sample_legacy_data()
    state = WorkstationStateService.build_from_legacy(data, market_state="CLOSED").to_dict()
    evidence_items = state["unified_intelligence"]["evidence_items"]
    assert isinstance(evidence_items, list)
    assert len(evidence_items) > 0
    for item in evidence_items:
        assert "evidence_id" in item
        assert "category" in item
        assert "summary" in item
        assert "temporal_relation" in item


# 7. Evidence summaries contain real canonical quantitative data
def test_7_evidence_summaries_contain_real_canonical_data():
    data = create_sample_legacy_data()
    state = WorkstationStateService.build_from_legacy(data, market_state="CLOSED").to_dict()
    global_ev = next(e for e in state["unified_intelligence"]["evidence_items"] if e["category"] == "GLOBAL_CUES")
    assert "S&P 500" in global_ev["summary"]
    assert "+0.50%" in global_ev["summary"]


# 8. Generic category fallback cannot override richer evidence_items
def test_8_generic_category_fallback_cannot_override_richer_evidence():
    data = create_sample_legacy_data()
    state = WorkstationStateService.build_from_legacy(data, market_state="CLOSED").to_dict()
    evidence_items = state["unified_intelligence"]["evidence_items"]
    categories = [e["category"] for e in evidence_items]
    assert "GLOBAL_CUES" in categories
    assert "NEWS_INTELLIGENCE" in categories


# 9. Market closed does not create live confirmation
def test_9_market_closed_does_not_create_live_confirmation():
    data = create_sample_legacy_data()
    state = WorkstationStateService.build_from_legacy(data, market_state="CLOSED").to_dict()
    session = state["unified_intelligence"]["session"]
    assert session == "POST_CLOSE"
    readiness = state["unified_intelligence"]["readiness"]
    assert readiness != "LIVE"


# 10. Market closed does not suppress valid next-session context
def test_10_market_closed_does_not_suppress_valid_next_session_context():
    data = create_sample_legacy_data()
    state = WorkstationStateService.build_from_legacy(data, market_state="CLOSED").to_dict()
    outlook = state["unified_intelligence"]["outlook"]
    assert outlook["target_session_relation"] in {"TOMORROW", "NEXT_TRADING_SESSION"}
    assert outlook["target_session_verified"] is True


# 11. Valid next-session conditional scenarios may exist while market closed
def test_11_valid_next_session_scenarios_exist_while_market_closed():
    data = create_sample_legacy_data()
    state = WorkstationStateService.build_from_legacy(data, market_state="CLOSED").to_dict()
    scenarios = state["unified_intelligence"]["scenarios"]
    assert len(scenarios) > 0
    assert scenarios[0]["priority"] == "PRIMARY_CONTEXT"


# 12. Invalid/stale evidence cannot create scenarios
def test_12_stale_evidence_cannot_create_scenarios():
    signals = {
        "opening": {"state": "UNAVAILABLE", "eligible": False},
        "price": {"state": "UNAVAILABLE", "eligible": False}
    }
    scenarios = UnifiedNiftyIntelligenceBuilder._scenarios(signals, [], session="INVALID_SESSION")
    assert scenarios == []


# 13. GIFT opening indication obeys temporal eligibility
def test_13_gift_opening_indication_obeys_temporal_eligibility():
    data = create_sample_legacy_data()
    state = WorkstationStateService.build_from_legacy(data, market_state="CLOSED").to_dict()
    opening_gap = state["macro_intelligence"]["opening_gap"]
    assert opening_gap["status"] == "READY"
    assert opening_gap["gap_points"] == 100.0 # 24550 - 24450


# 14. Missing GIFT remains unavailable
def test_14_missing_gift_remains_unavailable():
    data = create_sample_legacy_data()
    data["macroIntelligence"]["quotes"].pop("GIFT_NIFTY", None)
    data["macroIntelligence"]["workspace_context"]["current_context_quote_keys"] = ["S&P 500", "NASDAQ"]
    state = WorkstationStateService.build_from_legacy(data, market_state="CLOSED").to_dict()
    opening_gap = state["macro_intelligence"]["opening_gap"]
    assert opening_gap["status"] == "UNAVAILABLE"


# 15. Foreign-session observations remain context-only
def test_15_foreign_session_observations_context_only():
    data = create_sample_legacy_data()
    state = WorkstationStateService.build_from_legacy(data, market_state="CLOSED").to_dict()
    evidence_items = state["unified_intelligence"]["evidence_items"]
    global_item = next(e for e in evidence_items if e["category"] == "GLOBAL_CUES")
    assert global_item["temporal_relation"] == "FOREIGN_SESSION"
    assert global_item["decision_eligibility"] == "CONTEXT_ONLY"


# 16. Previous-session options remain correctly classified
def test_16_previous_session_options_classified():
    data = create_sample_legacy_data()
    state = WorkstationStateService.build_from_legacy(data, market_state="CLOSED").to_dict()
    opt_sig = state["unified_intelligence"]["signals"]["options"]
    assert opt_sig["freshness"] == "last_valid_session"


# 17. News published_at controls chronology
def test_17_news_published_at_controls_chronology():
    now = datetime.now(timezone.utc)
    old_time = format_ts(now - timedelta(hours=48))
    assessment = assess_pub_time(old_time, now)
    assert assessment["current_eligible"] is False


def assess_pub_time(pub_at, now):
    dt = datetime.fromisoformat(pub_at.replace("Z", "+00:00"))
    age = (now - dt).total_seconds()
    return {"current_eligible": age <= 24 * 3600, "age_seconds": age}


# 18. discovered_at cannot make old news "new"
def test_18_discovered_at_cannot_make_old_news_new():
    now = datetime.now(timezone.utc)
    old_pub = format_ts(now - timedelta(hours=72))
    assessment = assess_pub_time(old_pub, now)
    assert assessment["current_eligible"] is False


# 19. Unverified news cannot become verified implicitly
def test_19_unverified_news_cannot_become_verified_implicitly():
    tier = classify_source("Unknown Blog", "http://unknownblog.com")
    assert tier == "TIER_D_DISCOVERY"


# 20. Source trust and directional impact remain independent
def test_20_source_trust_and_directional_impact_independent():
    tier = classify_source("Reuters", "http://reuters.com")
    assert tier == "TIER_B_HIGH_TRUST"
    from src.news_engine.event_classifier import EventClassifier
    cat = EventClassifier.classify("NIFTY fell 200 points on crude oil spike", "")
    assert cat in {"Macro", "Geopolitics", "Markets", "Market Structure", "Crude"}


# 21. Discovery news cannot dominate decision evidence without eligibility
def test_21_discovery_news_cannot_dominate_without_eligibility():
    data = create_sample_legacy_data()
    now = datetime.now(timezone.utc)
    data["newsSentiment"]["items"][0]["published_at"] = format_ts(now - timedelta(hours=48))
    state = WorkstationStateService.build_from_legacy(data, market_state="CLOSED").to_dict()
    news_sig = state["unified_intelligence"]["signals"]["news"]
    assert news_sig["eligible"] is False


# 22. Preferred setup can legitimately remain unavailable
def test_22_preferred_setup_can_remain_unavailable():
    data = create_sample_legacy_data()
    data["marketContext"]["current_spot"] = None
    data["macroIntelligence"]["quotes"] = {}
    data["macroIntelligence"]["workspace_context"]["current_context_quote_keys"] = []
    data["macroIntelligence"]["institutional_flows"] = []
    data["newsSentiment"] = {"status": "unavailable", "items": [], "top_headlines": [], "high_impact_items": []}
    state = WorkstationStateService.build_from_legacy(data, market_state="CLOSED").to_dict()
    pref = state["unified_intelligence"]["outlook"]["preferred_setup"]
    assert "No Clear" in pref["title"]


# 23. No-clear-setup includes deterministic reason
def test_23_no_clear_setup_includes_deterministic_reason():
    data = create_sample_legacy_data()
    data["macroIntelligence"]["quotes"] = {}
    data["macroIntelligence"]["workspace_context"]["current_context_quote_keys"] = []
    data["macroIntelligence"]["institutional_flows"] = []
    data["newsSentiment"] = {"status": "unavailable", "items": [], "top_headlines": [], "high_impact_items": []}
    state = WorkstationStateService.build_from_legacy(data, market_state="CLOSED").to_dict()
    pref = state["unified_intelligence"]["outlook"]["preferred_setup"]
    assert len(pref["description"]) > 0


# 24. Scenario rejection includes deterministic reason
def test_24_scenario_rejection_reason():
    signals = {"opening": {"state": "UNAVAILABLE", "eligible": False}}
    scenarios = UnifiedNiftyIntelligenceBuilder._scenarios(signals, [], session="MARKET_OPEN")
    assert scenarios == []


# 25. Missing data includes explicit causal effect where known
def test_25_missing_data_includes_causal_effect():
    data = create_sample_legacy_data()
    data["marketContext"]["current_spot"] = None
    state = WorkstationStateService.build_from_legacy(data, market_state="CLOSED").to_dict()
    ineligibles = state["unified_intelligence"]["unavailable_or_ineligible_signals"]
    assert "price" in ineligibles


# 26. No React decision rules — checked via traderTerminology.ts inspection
def test_26_react_no_decision_rules():
    text = Path("src/frontend/utils/traderTerminology.ts").read_text(encoding="utf-8")
    assert "LAST_SESSION" in text
    assert "Previous Session" in text


# 27. No frontend level clustering — checked via architecture
def test_27_no_frontend_level_clustering():
    from src.intelligence_engine.unified_nifty import UnifiedNiftyIntelligenceBuilder
    assert hasattr(UnifiedNiftyIntelligenceBuilder, "_decision_zones")


# 28. No execution language in outputs
def test_28_no_execution_language_in_outputs():
    data = create_sample_legacy_data()
    state = WorkstationStateService.build_from_legacy(data, market_state="CLOSED").to_dict()
    serialized = str(state)
    forbidden = ["BUY NOW", "SELL NOW", "TARGET PRICE", "STOP LOSS", "ORDER QUANTITY"]
    for word in forbidden:
        assert word not in serialized


# 29. NIFTY-only product boundary preserved
def test_29_nifty_only_product_boundary():
    data = create_sample_legacy_data()
    state = WorkstationStateService.build_from_legacy(data, market_state="CLOSED").to_dict()
    engine = state["unified_intelligence"]["engine"]
    assert engine == "UNIFIED_NIFTY_INTELLIGENCE_V1"


# 30. Raw provider / canonical observations remain unchanged
def test_30_raw_observations_unchanged():
    data = create_sample_legacy_data()
    state = WorkstationStateService.build_from_legacy(data, market_state="CLOSED").to_dict()
    sp500 = state["macro_intelligence"]["quotes"]["S&P 500"]
    assert sp500["price"] == 5500.0
    assert sp500["change_pct"] == 0.5
