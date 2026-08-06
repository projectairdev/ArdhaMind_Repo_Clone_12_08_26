from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.application.analytical_pipeline_service import AnalyticalPipelineService
from src.application.compatibility_serializer import CompatibilitySerializer
from src.application.runtime_input_builder import RuntimeInputBuilder
from src.application.workstation_state_service import WorkstationStateService


NOW = datetime.now(timezone.utc)
EXPIRY = (NOW.date() + timedelta(days=7)).isoformat()


def stamp(age=0): return (NOW - timedelta(seconds=age)).isoformat().replace("+00:00", "Z")


def market(age=0):
    return {"current_spot": 24500.0, "timestamp": stamp(age), "trading_session": "MARKET_OPEN",
            "current_expiry": EXPIRY, "market_regime": "TRENDING", "trend_direction": "BULLISH",
            "trend_strength": 70.0, "support_levels": [24400.0], "resistance_levels": [24600.0],
            "vwap": 24480.0, "atr": 120.0, "india_vix": 14.0, "volatility_state": "NORMAL"}


def options(age=0, chain_length=10):
    return {"underlying_spot": 24500.0, "atm_strike": 24500.0, "strike_step": 50.0,
            "current_weekly_expiry": EXPIRY, "current_monthly_expiry": EXPIRY,
            "time_to_expiry": 7.0, "atm_iv": 14.0, "expected_move": 300.0, "pcr": 1.1,
            "max_pain": 24500.0, "highest_call_oi": 100000.0, "highest_put_oi": 110000.0,
            "highest_call_oi_change": 5000.0, "highest_put_oi_change": 6000.0,
            "support_strikes": [24400.0], "resistance_strikes": [24600.0],
            "liquidity_metrics": {"overall_liquidity_score": 80, "average_spread_pct": 1},
            "option_chain_summary": {"chain_length": chain_length}, "top_candidate_strikes": [],
            "market_option_bias": "BULLISH", "timestamp": stamp(age)}


def run(m=None, o=None, market_state="OPEN", broker_state="CONNECTED"):
    snapshot = RuntimeInputBuilder.from_daemon(m, o, market_state=market_state,
                                                broker_state=broker_state, generated_at=NOW)
    return snapshot, AnalyticalPipelineService().run(snapshot)


def test_complete_snapshot_runs_defined_canonical_sequence():
    snapshot, result = run(market(), options())
    assert tuple(result.stages) == AnalyticalPipelineService.STAGE_ORDER
    assert all(result.stages[name].status == "ready" for name in
               ("market", "options", "trade_context", "score", "opportunity", "strategy",
                "scenarios", "confidence", "risk", "decision_support", "explanation"))
    assert result.snapshot_id == snapshot.snapshot_id
    assert result.errors == []


def test_market_only_preserves_market_and_blocks_option_dependents():
    _, result = run(market(), None)
    assert result.stages["market"].status == "ready"
    assert result.stages["options"].status == "unavailable"
    assert result.stages["score"].status == "blocked"
    assert result.stages["explanation"].status == "degraded"


def test_partial_and_stale_options_degrade_confidence():
    _, partial = run(market(), options(chain_length=1))
    assert partial.stages["options"].status == "degraded"
    assert partial.stages["confidence"].status == "degraded"
    _, stale = run(market(), options(age=20))
    assert stale.stages["options"].status == "degraded"
    assert stale.stages["decision_support"].status == "degraded"


def test_stale_spot_blocks_authoritative_downstream():
    _, result = run(market(age=8), options())
    assert result.stages["market"].status == "blocked"
    assert result.stages["opportunity"].status == "blocked"


def test_invalid_market_and_inconsistent_options_are_rejected():
    bad_market = market(); bad_market["current_spot"] = 0
    snapshot, result = run(bad_market, options())
    assert snapshot.nifty_market.errors
    assert result.stages["market"].status == "blocked"
    bad_options = options(); bad_options["underlying_spot"] = 25000
    snapshot, result = run(market(), bad_options)
    assert "inconsistent" in snapshot.option_quotes.errors[0]
    assert result.stages["options"].status == "blocked"


def test_market_closed_is_historical_and_uses_planning_language():
    snapshot, result = run(market(age=1000), options(age=1000), market_state="CLOSED")
    assert snapshot.nifty_market.classification.value == "historical"
    assert result.stages["market"].status == "market_closed"
    assert result.stages["decision_support"].value["current_scenario_status"] == "next_session_planning"


def test_expired_session_blocks_new_live_pipeline_run():
    snapshot, result = run(market(), options(), broker_state="TOKEN_EXPIRED")
    assert snapshot.broker_session.payload["reconnect_required"] is True
    assert result.stages["market"].status == "blocked"


def test_pipeline_to_state_to_compatibility_is_one_coherent_snapshot():
    _, result = run(market(), options())
    values = result.compatibility_values()
    state = WorkstationStateService.build_from_legacy(values, market_state="OPEN")
    payload = CompatibilitySerializer.to_phase1_payload(state, values)
    assert payload["canonicalMetadata"]["stateSequence"] == state.state_sequence
    assert payload["marketContext"]["current_spot"] == 24500.0
    rendered = repr(state.to_dict()).lower()
    assert "quantity" not in rendered and "place_order" not in rendered and "order_payload" not in rendered


def test_decision_support_and_explanation_are_deterministic_and_read_only():
    _, result = run(market(), options())
    decision = result.stages["decision_support"].value
    explanation = result.stages["explanation"].value
    assert decision["human_decision_required"] is True
    assert explanation["ai_provider"] is None
    assert "execute" not in repr(explanation).lower()


def test_bridge_uses_single_application_pipeline_producer():
    bridge = (Path(__file__).parents[1] / "src/server_bridge.py").read_text(encoding="utf-8")
    assert "AnalyticalPipelineService.run_daemon_snapshot(" in bridge
    assert "legacy_data.update(pipeline_result.compatibility_values())" in bridge
    assert "generate_dynamic_workspace_data" not in bridge
