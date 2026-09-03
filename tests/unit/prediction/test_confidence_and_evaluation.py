from __future__ import annotations

from datetime import date, datetime, timezone
import pytest

from src.market_data.models.completed_session_snapshot import CompletedSessionSnapshot
from src.market_data.models.quality_enums import DataQualityStatus
from src.prediction.confidence.prediction_confidence_engine import PredictionConfidenceEngine
from src.prediction.evaluation.prediction_evaluator import PredictionEvaluator
from src.prediction.models.prediction_models import (
    ConfidenceBand,
    DirectionClass,
    MagnitudeBias,
    MagnitudeDistribution,
    PredictionOutcome,
    PredictionPhase,
    PredictionRecord,
)
from tests.unit.prediction.test_direction_and_magnitude import _make_dummy_snapshot


def test_1_confidence_evaluation_and_quality_cap():
    # 1. Valid high conviction
    snap_valid = _make_dummy_snapshot(quality=DataQualityStatus.VALID)
    score_v, band_v = PredictionConfidenceEngine.evaluate_confidence(
        direction=DirectionClass.BULLISH,
        direction_probability=0.85,
        snapshot=snap_valid,
    )
    assert score_v >= 0.70
    assert band_v in (ConfidenceBand.HIGH, ConfidenceBand.MODERATE)

    # 2. Degraded data cannot get HIGH band
    snap_delayed = _make_dummy_snapshot(quality=DataQualityStatus.DELAYED)
    score_d, band_d = PredictionConfidenceEngine.evaluate_confidence(
        direction=DirectionClass.BULLISH,
        direction_probability=0.85,
        snapshot=snap_delayed,
    )
    assert band_d != ConfidenceBand.HIGH


def test_2_prediction_evaluator_outcome_separation():
    now_utc = datetime.now(timezone.utc)
    t_sess = date(2026, 8, 28)

    mag_dist = MagnitudeDistribution(
        p_0_50=0.10,
        p_50_100=0.20,
        p_100_150=0.40,
        p_150_200=0.20,
        p_200_plus=0.10,
        expected_magnitude=120.0,
        median_magnitude=120.0,
        lower_band_pts=80.0,
        upper_band_pts=160.0,
    )

    pred = PredictionRecord(
        prediction_id="p1",
        model_version="v1.0.0",
        feature_schema_version="v1.0.0",
        calibration_version="v1.0.0",
        created_at=now_utc,
        target_session_date=t_sess,
        prediction_phase=PredictionPhase.PRE_MARKET,
        reference_price=24500.0,
        reference_timestamp=now_utc,
        direction_prediction=DirectionClass.BULLISH,
        direction_probability=0.75,
        expected_move_points=120.0,
        magnitude_distribution=mag_dist,
        confidence_score=0.80,
        confidence_band=ConfidenceBand.HIGH,
        input_state_revision=1,
        input_quality=DataQualityStatus.VALID,
        market_regime="TREND_UP",
        volatility_context=14.0,
        features_used=["trend"],
        supporting_factors=["Strong trend"],
        caution_factors=[],
    )

    # Completed session with small move: actual_close = 24520 (+20 pts), range = 60 pts
    comp_sess = CompletedSessionSnapshot(
        canonical_instrument_id="IDX:NSE:NIFTY_50",
        session_date=t_sess,
        open=24510.0,
        high=24550.0,
        low=24490.0,
        close=24520.0,
        previous_close=24500.0,
        absolute_change=20.0,
        percent_change=0.08,
        range=60.0,
        final_candle_timestamp=now_utc,
        quality=DataQualityStatus.VALID,
    )

    outcome = PredictionEvaluator.evaluate(pred, comp_sess)

    # Assert direction was correct (+20 pts >= 15 pts Bullish), but magnitude was OVERPREDICTED
    assert outcome.actual_direction == DirectionClass.BULLISH
    assert outcome.direction_correct is True
    assert outcome.magnitude_bias == MagnitudeBias.OVERPREDICTED
    assert outcome.range_hit is False  # 60 pts is outside 80-160 pts band
