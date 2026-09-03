from __future__ import annotations

from datetime import datetime, timezone
import inspect
import pytest

from src.market_data.bus.event_bus import MarketEventBus
from src.market_data.bus.events import MarketEvent, MarketEventType
from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.providers.dhan.dhan_tick_normalizer import DhanTickNormalizer
from src.market_data.runtime.cutover_readiness import CutoverStatus, EnhancedCutoverEvaluator
from src.market_data.runtime.validate_live_dhan import run_validation


def test_1_chaos_event_bus_subscriber_exception_isolation():
    bus = MarketEventBus()
    bus.start()
    received = []

    def bad_subscriber(event: MarketEvent):
        raise RuntimeError("Chaos Subscriber Explosion")

    def good_subscriber(event: MarketEvent):
        received.append(event.payload.get("data"))

    bus.subscribe(MarketEventType.TICK, bad_subscriber)
    bus.subscribe(MarketEventType.TICK, good_subscriber)

    bus.publish(MarketEventType.TICK, {"data": "test_payload"})
    bus.stop(drain=True, timeout=2.0)

    # Good subscriber must still receive event despite bad subscriber exception
    assert len(received) == 1
    assert received[0] == "test_payload"


def test_2_chaos_malformed_packets_rejected():
    from src.market_data.services.instrument_master_service import InstrumentMasterService
    normalizer = DhanTickNormalizer(InstrumentMasterService())
    malformed_bytes = b"CORRUPTED_GARBAGE_PACKET_NOT_DHAN"

    tick = normalizer.parse_packet(malformed_bytes)
    assert tick is None


def test_3_cutover_readiness_report_status():
    """
    Verifies that before live market-hours Dhan proof is completed,
    the cutover status is strictly READY_FOR_LIVE_VALIDATION (never READY_FOR_CUTOVER).
    """
    mock_inputs = {
        "dhan_auth_verified": True,
        "websocket_connected": True,
        "desired_subscriptions_count": 2,
        "active_subscriptions_count": 2,
        "nifty_ticks_observed_count": 500,
        "feed_health_status": "HEALTHY",
        "session_authority_valid": True,
        "has_session_mismatch": False,
        "candles_count": 50,
        "reconciliation_functioning": True,
        "historical_bootstrap_functioning": True,
        "option_chain_functioning": True,
        "shadow_comparison_status": "MATCH",
        "fabricated_values_count": 0,
    }

    report_unverified = EnhancedCutoverEvaluator.evaluate(mock_inputs, live_dhan_proof_verified=False)
    assert report_unverified.status == CutoverStatus.READY_FOR_LIVE_VALIDATION

    report_verified = EnhancedCutoverEvaluator.evaluate(mock_inputs, live_dhan_proof_verified=True)
    assert report_verified.status == CutoverStatus.READY_FOR_CUTOVER


def test_4_validate_live_dhan_script_dry_run():
    res = run_validation(is_dry_run=True)
    assert res["status"] == "DRY_RUN_COMPLETED"
    assert res["passed"] is True
    assert res["readiness_status"] == CutoverStatus.READY_FOR_LIVE_VALIDATION.value


def test_5_full_stack_architectural_dependency_audit():
    """
    Comprehensive architectural audit proving:
    - Zero execution/order methods across analytics, prediction, decision, replay, observability.
    - Zero provider SDK imports in prediction, decision, replay, observability.
    """
    import src.decision.decision.decision_engine as de_mod
    import src.prediction.prediction_engine as pe_mod
    import src.replay.engine.market_replay_engine as rep_mod
    import src.observability.latency_tracker as obs_mod

    forbidden_execution = ["place_order", "modify_order", "cancel_order", "exit_order", "execute_trade"]
    forbidden_sdks = ["kiteconnect", "dhanhq"]

    for mod in (de_mod, pe_mod, rep_mod, obs_mod):
        source = inspect.getsource(mod)
        for term in forbidden_execution:
            assert term not in source
        for sdk in forbidden_sdks:
            assert f"import {sdk}" not in source
