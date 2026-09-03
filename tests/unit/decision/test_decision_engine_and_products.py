from __future__ import annotations

from datetime import date, datetime, timezone
import pytest

from src.decision.decision.decision_engine import DecisionEngine
from src.decision.models.decision_models import DecisionSnapshot, DecisionState
from src.decision.products.live_guide import LiveGuideGenerator, LiveGuideSnapshot
from src.decision.products.market_intelligence import MarketIntelligenceSummary, MarketIntelligenceSummaryGenerator
from src.decision.products.morning_plan import MorningPlanGenerator, MorningPlanSnapshot
from src.decision.products.product_coordinator import ProductCoordinator
from src.decision.products.tomorrow_plan import TomorrowPlanGenerator, TomorrowPlanSnapshot
from src.market_data.models.completed_session_snapshot import CompletedSessionSnapshot
from src.market_data.models.quality_enums import DataQualityStatus
from src.market_data.session.session_authority import CanonicalSessionAuthority
from src.prediction.models.prediction_models import (
    ConfidenceBand,
    DirectionClass,
    MagnitudeDistribution,
    PredictionOutcome,
    PredictionPhase,
    PredictionRecord,
    PredictionSnapshot,
)
from tests.unit.decision.test_signal_fusion_and_opportunity import _make_snapshot


def _make_dummy_pred(session_d: date) -> PredictionSnapshot:
    now_utc = datetime.now(timezone.utc)
    dist = MagnitudeDistribution(0.1, 0.4, 0.3, 0.15, 0.05, 95.0, 90.0, 60.0, 140.0)
    rec = PredictionRecord(
        prediction_id="p_test",
        model_version="v1.0.0",
        feature_schema_version="v1.0.0",
        calibration_version="v1.0.0",
        created_at=now_utc,
        target_session_date=session_d,
        prediction_phase=PredictionPhase.PRE_MARKET,
        reference_price=24500.0,
        reference_timestamp=now_utc,
        direction_prediction=DirectionClass.BULLISH,
        direction_probability=0.78,
        expected_move_points=95.0,
        magnitude_distribution=dist,
        confidence_score=0.80,
        confidence_band=ConfidenceBand.HIGH,
        input_state_revision=1,
        input_quality=DataQualityStatus.VALID,
        market_regime="TREND_UP",
        volatility_context=13.5,
        features_used=["trend", "breadth"],
        supporting_factors=["Uptrend"],
        caution_factors=[],
    )
    return PredictionSnapshot(rec, [], DataQualityStatus.VALID, "CALIBRATED")


def test_1_decision_snapshot_lifecycle_and_confidence():
    snap = _make_snapshot(last_price=24550.0, or_high=24520.0, or_low=24480.0)
    pred = _make_dummy_pred(snap.session_date)

    dec_snap = DecisionEngine.evaluate_decision(snap, pred)

    assert isinstance(dec_snap, DecisionSnapshot)
    assert dec_snap.decision_state == DecisionState.READY_FOR_HUMAN_REVIEW
    assert dec_snap.confidence_band == "HIGH"
    assert "OR Low" in dec_snap.explanation.what_invalidates_it


def test_2_product_layer_snapshots():
    snap = _make_snapshot()
    pred = _make_dummy_pred(snap.session_date)
    dec = DecisionEngine.evaluate_decision(snap, pred)

    # 1. Morning Plan
    mp = MorningPlanGenerator.generate(snap, pred)
    assert isinstance(mp, MorningPlanSnapshot)
    assert mp.opening_bias == "BULLISH"
    assert len(mp.opening_checklist) == 4

    # 2. Live Guide
    lg = LiveGuideGenerator.generate(snap, dec)
    assert isinstance(lg, LiveGuideSnapshot)
    assert lg.decision_state == dec.decision_state.value

    # 3. Tomorrow Plan
    comp = CompletedSessionSnapshot(
        canonical_instrument_id="IDX:NSE:NIFTY_50",
        session_date=snap.session_date,
        open=24500.0,
        high=24600.0,
        low=24480.0,
        close=24580.0,
        previous_close=24450.0,
        absolute_change=130.0,
        percent_change=0.53,
        range=120.0,
        final_candle_timestamp=datetime.now(timezone.utc),
        quality=DataQualityStatus.VALID,
    )
    tp = TomorrowPlanGenerator.generate(comp, next_trading_date=date(2026, 8, 31))
    assert isinstance(tp, TomorrowPlanSnapshot)
    assert tp.session_range == 120.0

    # 4. Market Intelligence Summary
    summary = MarketIntelligenceSummaryGenerator.generate(dec)
    assert isinstance(summary, MarketIntelligenceSummary)
    assert summary.nifty_bias == "BULLISH"


def test_3_product_coordinator_phase_routing():
    snap = _make_snapshot()
    pred = _make_dummy_pred(snap.session_date)
    dec = DecisionEngine.evaluate_decision(snap, pred)

    coord = ProductCoordinator()
    res = coord.get_primary_product(snap, pred, dec)
    assert "primary_product" in res
    assert "market_intelligence_summary" in res
