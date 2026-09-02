from __future__ import annotations

from datetime import date, datetime, timezone
import pytest

from src.market_data.models.completed_session_snapshot import CompletedSessionSnapshot
from src.market_data.models.quality_enums import DataQualityStatus
from src.prediction.calibration.calibration_engine import PredictionCalibrationEngine
from src.prediction.evaluation.prediction_evaluator import PredictionEvaluator
from src.prediction.models.prediction_models import (
    ConfidenceBand,
    DirectionClass,
    MagnitudeBias,
    MagnitudeDistribution,
    PredictionPhase,
    PredictionRecord,
)


def test_1_historical_overprediction_failure_regression():
    """
    CRITICAL HISTORICAL REGRESSION TEST:
    Forecast: Bullish, expected move +110 points, High confidence.
    Actual: Modest +15 points opening/session move.

    The engine must NOT mark the overall forecast as merely "accurate".
    It must explicitly flag:
    - direction_correct = True
    - magnitude_bias = OVERPREDICTED
    - calibration reflects overshoot
    """
    now_utc = datetime.now(timezone.utc)
    t_sess = date(2026, 8, 28)

    mag_dist = MagnitudeDistribution(
        p_0_50=0.10,
        p_50_100=0.25,
        p_100_150=0.45,
        p_150_200=0.15,
        p_200_plus=0.05,
        expected_magnitude=110.0,
        median_magnitude=110.0,
        lower_band_pts=80.0,
        upper_band_pts=150.0,
    )

    pred = PredictionRecord(
        prediction_id="p_hist_fail",
        model_version="v1.0.0",
        feature_schema_version="v1.0.0",
        calibration_version="v1.0.0",
        created_at=now_utc,
        target_session_date=t_sess,
        prediction_phase=PredictionPhase.PRE_MARKET,
        reference_price=24500.0,
        reference_timestamp=now_utc,
        direction_prediction=DirectionClass.BULLISH,
        direction_probability=0.82,
        expected_move_points=110.0,
        magnitude_distribution=mag_dist,
        confidence_score=0.85,
        confidence_band=ConfidenceBand.HIGH,
        input_state_revision=1,
        input_quality=DataQualityStatus.VALID,
        market_regime="TREND_UP",
        volatility_context=13.0,
        features_used=["trend", "options"],
        supporting_factors=["Strong trend"],
        caution_factors=[],
    )

    actual_snap = CompletedSessionSnapshot(
        canonical_instrument_id="IDX:NSE:NIFTY_50",
        session_date=t_sess,
        open=24510.0,
        high=24530.0,
        low=24495.0,
        close=24515.0,
        previous_close=24500.0,
        absolute_change=15.0,
        percent_change=0.06,
        range=35.0,
        final_candle_timestamp=now_utc,
        quality=DataQualityStatus.VALID,
    )

    outcome = PredictionEvaluator.evaluate(pred, actual_snap)

    assert outcome.direction_correct is True
    assert outcome.magnitude_bias == MagnitudeBias.OVERPREDICTED
    assert outcome.magnitude_error == 95.0  # 110 - 15 = 95 pts overpredicted!

    # Calibration calculation on a single overpredicted session (Sample size = 1)
    metrics_1 = PredictionCalibrationEngine.calculate_metrics([(pred, outcome)])
    assert metrics_1.direction_accuracy == 1.0
    assert metrics_1.overshoot_rate == 1.0
    assert metrics_1.maturity.value == "INSUFFICIENT_SAMPLE"

    # Sample size = 1 must NEVER generate actionable scaling recommendations
    recs_1 = PredictionCalibrationEngine.generate_recommendations(metrics_1, current_magnitude_scale=1.0)
    assert len(recs_1) == 0

    # 5 simulated pairs -> OBSERVATIONAL
    pairs_5 = [(pred, outcome) for _ in range(5)]
    metrics_5 = PredictionCalibrationEngine.calculate_metrics(pairs_5)
    assert metrics_5.maturity.value == "OBSERVATIONAL"
    recs_5 = PredictionCalibrationEngine.generate_recommendations(metrics_5, current_magnitude_scale=1.0)
    assert len(recs_5) == 1
    assert recs_5[0].maturity.value == "OBSERVATIONAL"

    # 20 simulated pairs -> ACTIONABLE
    pairs_20 = [(pred, outcome) for _ in range(20)]
    metrics_20 = PredictionCalibrationEngine.calculate_metrics(pairs_20)
    assert metrics_20.maturity.value == "ACTIONABLE"
    recs_20 = PredictionCalibrationEngine.generate_recommendations(metrics_20, current_magnitude_scale=1.0)
    assert len(recs_20) == 1
    assert recs_20[0].maturity.value == "ACTIONABLE"
    assert recs_20[0].recommended_adjustment < 1.0  # Scales magnitude downward (e.g. 0.85)
