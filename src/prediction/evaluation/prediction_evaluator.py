from __future__ import annotations

from datetime import datetime, timezone
import math

from src.market_data.models.completed_session_snapshot import CompletedSessionSnapshot
from src.prediction.models.prediction_models import (
    DirectionClass,
    MagnitudeBias,
    PredictionOutcome,
    PredictionRecord,
)


class PredictionEvaluator:
    """
    Deterministic outcome evaluation engine.
    Evaluates an immutable PredictionRecord against canonical CompletedSessionSnapshot truth.
    Separates direction correctness from magnitude error and overprediction bias.
    """

    @staticmethod
    def evaluate(
        prediction: PredictionRecord,
        completed_session: CompletedSessionSnapshot,
        evaluation_timestamp: datetime | None = None,
    ) -> PredictionOutcome:
        """Evaluates forecast accuracy and captures outcome metrics."""
        now_utc = evaluation_timestamp or datetime.now(timezone.utc)
        if completed_session.session_date != prediction.target_session_date:
            raise ValueError(
                f"Session date mismatch: prediction targets {prediction.target_session_date}, "
                f"snapshot is for {completed_session.session_date}."
            )

        ref_p = prediction.reference_price
        act_open = completed_session.open
        act_high = completed_session.high
        act_low = completed_session.low
        act_close = completed_session.close

        open_move = round(act_open - ref_p, 2)
        session_move = round(act_close - ref_p, 2)
        act_range = round(act_high - act_low, 2)

        # Actual Direction
        if session_move >= 15.0:
            act_dir = DirectionClass.BULLISH
        elif session_move <= -15.0:
            act_dir = DirectionClass.BEARISH
        else:
            act_dir = DirectionClass.NEUTRAL

        # Directional Correctness
        dir_correct = (prediction.direction_prediction == act_dir)

        # Magnitude Error
        pred_move = prediction.expected_move_points
        mag_error = round(pred_move - session_move, 2)
        abs_error = round(abs(mag_error), 2)

        # Range Hit Check (actual range falls in predicted band)
        dist = prediction.magnitude_distribution
        range_hit = (dist.lower_band_pts <= act_range <= dist.upper_band_pts)

        # Bucket Hit Check
        act_abs_move = abs(session_move)
        # Find dominant predicted bucket
        buckets = [
            (0, 50, dist.p_0_50),
            (50, 100, dist.p_50_100),
            (100, 150, dist.p_100_150),
            (150, 200, dist.p_150_200),
            (200, float("inf"), dist.p_200_plus),
        ]
        top_bucket = max(buckets, key=lambda b: b[2])
        bucket_hit = (top_bucket[0] <= act_abs_move < top_bucket[1])

        # Overprediction vs Underprediction bias
        pred_abs_move = abs(pred_move)
        if abs_error <= 30.0:
            bias = MagnitudeBias.ACCURATE
        elif pred_abs_move > (act_abs_move + 30.0):
            bias = MagnitudeBias.OVERPREDICTED
        else:
            bias = MagnitudeBias.UNDERPREDICTED

        return PredictionOutcome(
            prediction_id=prediction.prediction_id,
            target_session_date=prediction.target_session_date,
            actual_open=act_open,
            actual_high=act_high,
            actual_low=act_low,
            actual_close=act_close,
            actual_open_move=open_move,
            actual_session_move=session_move,
            actual_range=act_range,
            actual_direction=act_dir,
            direction_correct=dir_correct,
            magnitude_error=mag_error,
            absolute_error=abs_error,
            range_hit=range_hit,
            bucket_hit=bucket_hit,
            magnitude_bias=bias,
            evaluated_at=now_utc,
        )
