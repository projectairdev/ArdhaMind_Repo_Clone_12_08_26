from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.application.workstation_state_service import WorkstationStateService
from src.intelligence_engine import UnifiedNiftyIntelligenceBuilder


NOW = datetime(2026, 8, 10, 3, 0, tzinfo=timezone.utc)


def inputs():
    market = {
        "current_spot": 24700, "previous_close": 24600, "last_tick_time": "2026-08-10T03:00:00Z",
        "session_mode": "CURRENT_SESSION", "trend_direction": "BULLISH", "market_regime": "TRENDING_UP",
        "support_levels": [24650], "resistance_levels": [24750],
        "breadth": {"valid_observations": 50, "advances": 36, "declines": 13, "unchanged": 1},
        "india_vix_context": {"status": "AVAILABLE", "value": 14, "regime": "NORMAL", "freshness": "FRESH",
                               "observation_timestamp": "2026-08-10T03:00:00Z", "source": "Kite Quote API"},
    }
    technical = {"trend_direction": "BULLISH", "market_regime": "TRENDING_UP"}
    options = {
        "pcr": 1.12, "max_pain": 24700, "atm_strike": 24700, "market_option_bias": "BULLISH",
        "support_strikes": [24600], "resistance_strikes": [24800], "atm_iv": 12.5,
        "timestamp": "2026-08-10T03:00:00Z",
    }
    quotes = {key: {"change_pct": .5, "observation_timestamp": "2026-08-10T02:55:00Z"}
              for key in ("S&P 500", "NASDAQ", "DOW_JONES", "NIKKEI_225", "HANG_SENG")}
    macro = {
        "opening_gap": {"status": "READY", "classification": "POSITIVE_GAP_INDICATION", "gap_points": 100,
                        "gap_pct": .41, "source": "NSE International Exchange", "freshness": "FRESH",
                        "observation_timestamp": "2026-08-10T02:55:00Z"},
        "quotes": quotes, "workspace_context": {"current_context_quote_keys": list(quotes)},
        "institutional_context": {
            "cash": [{"dataset_type": "FII_CASH", "net_value": 1200}],
            "derivatives": {"FII_INDEX_FUTURES": {"positioning": "NET_LONG"}},
        },
        "india_vix": market["india_vix_context"],
        "economic_events": [{"event_name": "RBI policy", "status": "UPCOMING", "impact_level": "HIGH",
                             "scheduled_at": "2026-08-10T10:00:00Z"}],
    }
    news = {"freshness": "FRESH", "items": [{"canonical_eligible": True, "nifty_relevance_score": 8,
                                                 "expected_direction": "POSITIVE"}]}
    return market, technical, options, macro, news


def build(state="PRE_OPEN", mutate=None, *, market_fresh="fresh", option_fresh="fresh"):
    values = list(inputs())
    if mutate: mutate(*values)
    return UnifiedNiftyIntelligenceBuilder.build(
        market=values[0], technical=values[1], options=values[2], macro=values[3], news=values[4],
        market_state=state, market_meta={"freshness_status": market_fresh},
        option_meta={"freshness_status": option_fresh}, now=NOW,
    )


@pytest.mark.parametrize("raw,session,mode", [
    ("PRE_OPEN", "PRE_OPEN", "PRE_MARKET_INTELLIGENCE"),
    ("MARKET_OPEN", "MARKET_OPEN", "LIVE_MARKET_INTELLIGENCE"),
    ("POST_CLOSE", "POST_CLOSE", "SESSION_REVIEW"),
    ("WEEKEND", "WEEKEND", "NEXT_SESSION_CONTEXT"),
    ("HOLIDAY", "HOLIDAY", "NEXT_SESSION_CONTEXT"),
])
def test_session_specific_modes(raw, session, mode):
    result = build(raw)
    assert (result["session"], result["mode"]) == (session, mode)
    assert result["execution_authorized"] is False


def test_positive_alignment_is_rule_based():
    assert build()["alignment"] == "STRONG_BULLISH_ALIGNMENT"


def test_negative_alignment_is_rule_based():
    def negative(m, t, o, macro, news):
        t["trend_direction"] = "BEARISH"; m["trend_direction"] = "BEARISH"
        o.update(pcr=.6, market_option_bias="BEARISH")
        for q in macro["quotes"].values(): q["change_pct"] = -.6
        macro["opening_gap"]["classification"] = "NEGATIVE_GAP_INDICATION"
        macro["institutional_context"]["cash"][0]["net_value"] = -100
        macro["institutional_context"]["derivatives"]["FII_INDEX_FUTURES"]["positioning"] = "NET_SHORT"
        news["items"][0]["expected_direction"] = "NEGATIVE"
    assert build(mutate=negative)["alignment"] == "STRONG_BEARISH_ALIGNMENT"


def test_conflicted_evidence_is_not_majority_vote():
    def conflict(m, t, o, macro, news):
        o.update(pcr=.6, market_option_bias="BEARISH")
    result = build(mutate=conflict)
    assert result["alignment"] == "CONFLICTED" and "options" in result["opposing_signals"]
    assert "price" in result["confirming_signals"]


def test_insufficient_evidence_is_explicit():
    def empty(m, t, o, macro, news):
        m.clear(); t.clear(); o.clear(); macro.clear(); news.clear()
    result = build(mutate=empty)
    assert result["alignment"] == "INSUFFICIENT_EVIDENCE"
    assert result["confidence"] == "INSUFFICIENT"


def test_stale_gift_is_excluded_from_live_reasoning():
    result = build("MARKET_OPEN")
    assert not result["signals"]["opening"]["eligible"]
    assert "historical context" in result["signals"]["opening"]["ineligibility_reason"]


@pytest.mark.parametrize("coverage,eligible", [(25, False), (39, False), (40, True), (50, True)])
def test_breadth_coverage_gate(coverage, eligible):
    def mutate(m, *_): m["breadth"]["valid_observations"] = coverage
    assert build("MARKET_OPEN", mutate)["signals"]["breadth"]["eligible"] is eligible


def test_last_session_breadth_is_excluded_during_live_market():
    def mutate(m, *_): m["session_mode"] = "LAST_SESSION"
    assert not build("MARKET_OPEN", mutate)["signals"]["breadth"]["eligible"]


def test_canonical_breadth_coverage_object_is_accepted():
    def mutate(m, *_):
        m["breadth"]["coverage"] = {"valid": 50, "expected": 50, "minimum": 40}
        m["breadth"].pop("valid_observations")
    signal = build("MARKET_OPEN", mutate)["signals"]["breadth"]
    assert signal["eligible"] is True and "coverage 50/50" in signal["evidence"][0]


def test_institutional_mixed_positioning_preserves_evidence():
    def mutate(m, t, o, macro, n):
        macro["institutional_context"]["derivatives"]["FII_INDEX_FUTURES"]["positioning"] = "NET_SHORT"
    signal = build(mutate=mutate)["signals"]["institutional"]
    assert signal["state"] == "MIXED" and len(signal["evidence"]) == 2


@pytest.mark.parametrize("pcr,bias,expected", [(1.2, "BULLISH", "BULLISH"), (.6, "BEARISH", "BEARISH"),
                                                 (.6, "BULLISH", "CONFLICTED"), (.9, "NEUTRAL", "BALANCED")])
def test_option_normalization_and_conflict(pcr, bias, expected):
    def mutate(m, t, o, *_): o.update(pcr=pcr, market_option_bias=bias)
    assert build(mutate=mutate)["signals"]["options"]["state"] == expected


@pytest.mark.parametrize("regime,risk", [("NORMAL", "NORMAL"), ("ELEVATED", "ELEVATED"), ("HIGH", "HIGH")])
def test_volatility_escalates_analytical_risk(regime, risk):
    def mutate(m, t, o, macro, n):
        m["india_vix_context"]["regime"] = regime; macro["india_vix"]["regime"] = regime
        macro["economic_events"][0]["scheduled_at"] = "2026-08-12T10:00:00Z"
    assert build(mutate=mutate)["risk"]["state"] == risk


def test_imminent_event_escalates_risk():
    def mutate(m, t, o, macro, n): macro["economic_events"][0]["scheduled_at"] = "2026-08-10T04:00:00Z"
    result = build(mutate=mutate)
    assert result["signals"]["events"]["state"] == "IMMINENT" and result["risk"]["state"] == "HIGH"


def test_simultaneous_events_have_deterministic_order():
    def mutate(m, t, o, macro, n):
        macro["economic_events"] = [
            {"event_name": name, "status": "UPCOMING", "impact_level": "HIGH", "scheduled_at": "2026-08-10T04:00:00Z"}
            for name in ("Zulu release", "Alpha release")
        ]
    evidence = build(mutate=mutate)["signals"]["events"]["evidence"]
    assert evidence[0].startswith("Alpha release") and evidence[1].startswith("Zulu release")


def test_missing_calendar_is_unknown_not_zero_risk():
    def mutate(m, t, o, macro, n): macro["economic_events"] = []
    result = build(mutate=mutate)
    assert result["signals"]["events"]["state"] == "UNAVAILABLE"
    assert "event calendar unavailable" in result["risk"]["reasons"]


@pytest.mark.parametrize("gap,expected", [("POSITIVE_GAP_INDICATION", "GAP_UP_HOLD"),
                                            ("NEGATIVE_GAP_INDICATION", "GAP_DOWN_RECOVERY"),
                                            ("FLAT_OPEN_INDICATION", "FLAT_OPEN_BREAKOUT")])
def test_opening_scenarios_are_conditional_not_predictions(gap, expected):
    def mutate(m, t, o, macro, n): macro["opening_gap"]["classification"] = gap
    scenario = build(mutate=mutate)["scenarios"][0]
    assert scenario["name"] == expected and scenario["prediction"] is False
    assert scenario["confirmation_conditions"] and scenario["invalidation_conditions"]


def test_key_levels_keep_genuine_provenance_without_averaging():
    levels = build()["key_levels"]
    assert {x["origin"] for x in levels} >= {"PRICE_STRUCTURE", "OPTION_OI", "MAX_PAIN", "ATM", "PREVIOUS_SESSION"}
    assert all(x["synthetic"] is False for x in levels)
    assert not any(x["value"] == 24725 for x in levels)


def test_missing_levels_are_not_fabricated():
    def mutate(m, t, o, *_):
        m["support_levels"] = []; m["resistance_levels"] = []; m.pop("previous_close")
        o["support_strikes"] = []; o["resistance_strikes"] = []; o["max_pain"] = None; o["atm_strike"] = None
    assert build(mutate=mutate)["key_levels"] == []


def test_conflict_and_missing_critical_data_reduce_confidence():
    assert build()["confidence"] in {"MODERATE", "HIGH"}
    def conflict(m, t, o, *_): o.update(pcr=.6, market_option_bias="BEARISH")
    assert build(mutate=conflict)["confidence"] == "LOW"
    assert build("MARKET_OPEN", option_fresh="stale")["confidence"] == "LOW"


def test_explanation_is_deterministic_and_changes_with_evidence():
    first = build(); second = build()
    assert first["explanation"] == second["explanation"]
    def negative(m, t, o, macro, news):
        t["trend_direction"] = m["trend_direction"] = "BEARISH"; o.update(pcr=.6, market_option_bias="BEARISH")
    assert build(mutate=negative)["explanation"] != first["explanation"]


def test_synthesis_has_no_external_calls_or_synthetic_inputs():
    result = build()
    assert result["input_contract"]["external_fetches"] == 0
    assert result["synthetic_inputs"] == [] and result["human_decision_required"] is True


def test_canonical_state_publishes_one_synthesis_to_decision_and_explanation():
    market, technical, options, macro, news = inputs()
    state = WorkstationStateService.build_from_legacy({"marketContext": market, "technicalAnalysis": technical,
        "optionContext": options, "macroIntelligence": macro, "newsSentiment": news},
        broker_state="CONNECTED", market_state="HOLIDAY", now=NOW).to_dict()
    engine = state["unified_intelligence"]["engine"]
    assert state["decision_support"]["unified_intelligence_engine"] == engine
    assert state["explanation"]["engine"] == engine
    assert all(state["workspace_readiness"][name]["unified_intelligence_mode"] == "NEXT_SESSION_CONTEXT"
               for name in ("pre_market_planner", "todays_analysis", "live_assistant"))
    assert state["application_status"]["read_only"] is True


def test_frontend_workspaces_consume_shared_canonical_field_without_core_recomputation():
    root = Path("src/frontend/components")
    panel = (root / "UnifiedIntelligencePanel.tsx").read_text(encoding="utf-8")
    phase = (root / "PhaseOneWorkspaces.tsx").read_text(encoding="utf-8")
    pre = (root / "PreMarketPlannerWorkspace.tsx").read_text(encoding="utf-8")
    assert "canonicalState?.unified_intelligence" in panel
    assert phase.count("<UnifiedIntelligencePanel") >= 4 and "PRE_MARKET" in pre
    assert "BREADTH_MIN_COVERAGE" not in panel and "fetch(" not in panel
