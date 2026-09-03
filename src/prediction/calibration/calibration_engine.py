from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Dict, List, Sequence, Tuple

from src.prediction.models.prediction_models import (
    CalibrationMaturity,
    CalibrationRecommendation,
    MagnitudeBias,
    PredictionOutcome,
    PredictionRecord,
    RegimeCalibrationMetrics,
)


class PredictionCalibrationEngine:
    """
    Deterministic calibration analysis engine.
    Calculates calibration metrics overall and per-regime, generating non-mutating feedback.
    Enforces sample maturity: immature samples (<20) are labeled OBSERVATIONAL / INSUFFICIENT.
    """

    MIN_ACTIONABLE_SAMPLE_SIZE = 20
    MIN_OBSERVATIONAL_SAMPLE_SIZE = 5

    @staticmethod
    def calculate_metrics(
        evaluated_pairs: Sequence[Tuple[PredictionRecord, PredictionOutcome]],
        regime_filter: str | None = None,
    ) -> RegimeCalibrationMetrics:
        """Computes comprehensive accuracy, error, and calibration metrics for evaluated pairs."""
        pairs = evaluated_pairs
        if regime_filter:
            pairs = [p for p in pairs if p[0].market_regime == regime_filter]

        n = len(pairs)
        if n < PredictionCalibrationEngine.MIN_OBSERVATIONAL_SAMPLE_SIZE:
            maturity = CalibrationMaturity.INSUFFICIENT_SAMPLE
        elif n < PredictionCalibrationEngine.MIN_ACTIONABLE_SAMPLE_SIZE:
            maturity = CalibrationMaturity.OBSERVATIONAL
        else:
            maturity = CalibrationMaturity.ACTIONABLE

        if n == 0:
            return RegimeCalibrationMetrics(
                regime=regime_filter or "ALL",
                sample_count=0,
                minimum_required_for_actionable=PredictionCalibrationEngine.MIN_ACTIONABLE_SAMPLE_SIZE,
                maturity=CalibrationMaturity.INSUFFICIENT_SAMPLE,
                direction_accuracy=0.0,
                brier_score=0.25,
                mean_absolute_error=0.0,
                root_mean_squared_error=0.0,
                median_absolute_error=0.0,
                range_hit_rate=0.0,
                bucket_hit_rate=0.0,
                overshoot_rate=0.0,
                undershoot_rate=0.0,
            )

        dir_correct_count = sum(1 for p in pairs if p[1].direction_correct)
        dir_accuracy = round(dir_correct_count / n, 4)

        brier_sum = 0.0
        for p in pairs:
            actual_binary = 1.0 if p[1].direction_correct else 0.0
            prob = p[0].direction_probability
            brier_sum += (prob - actual_binary) ** 2
        brier_score = round(brier_sum / n, 4)

        abs_errors = [p[1].absolute_error for p in pairs]
        mae = round(sum(abs_errors) / n, 2)
        sq_errors = [p[1].magnitude_error ** 2 for p in pairs]
        rmse = round(math.sqrt(sum(sq_errors) / n), 2)
        sorted_abs = sorted(abs_errors)
        med_ae = sorted_abs[n // 2]

        range_hits = sum(1 for p in pairs if p[1].range_hit)
        bucket_hits = sum(1 for p in pairs if p[1].bucket_hit)
        overshoots = sum(1 for p in pairs if p[1].magnitude_bias == MagnitudeBias.OVERPREDICTED)
        undershoots = sum(1 for p in pairs if p[1].magnitude_bias == MagnitudeBias.UNDERPREDICTED)

        return RegimeCalibrationMetrics(
            regime=regime_filter or "ALL",
            sample_count=n,
            minimum_required_for_actionable=PredictionCalibrationEngine.MIN_ACTIONABLE_SAMPLE_SIZE,
            maturity=maturity,
            direction_accuracy=dir_accuracy,
            brier_score=brier_score,
            mean_absolute_error=mae,
            root_mean_squared_error=rmse,
            median_absolute_error=med_ae,
            range_hit_rate=round(range_hits / n, 4),
            bucket_hit_rate=round(bucket_hits / n, 4),
            overshoot_rate=round(overshoots / n, 4),
            undershoot_rate=round(undershoots / n, 4),
        )

    @staticmethod
    def generate_recommendations(
        metrics: RegimeCalibrationMetrics,
        current_magnitude_scale: float = 1.0,
    ) -> List[CalibrationRecommendation]:
        """Produces non-mutating diagnostic adjustments with explicit maturity rating."""
        recs: List[CalibrationRecommendation] = []
        now_utc = datetime.now(timezone.utc)

        if metrics.sample_count < PredictionCalibrationEngine.MIN_OBSERVATIONAL_SAMPLE_SIZE:
            return recs

        # Systematic overprediction adjustment recommendation
        if metrics.overshoot_rate >= 0.40:
            rec_scale = round(current_magnitude_scale * 0.85, 2)
            recs.append(
                CalibrationRecommendation(
                    metric="magnitude_scale",
                    current_calibration_factor=current_magnitude_scale,
                    observed_error=metrics.mean_absolute_error,
                    recommended_adjustment=rec_scale,
                    sample_size=metrics.sample_count,
                    minimum_required=PredictionCalibrationEngine.MIN_ACTIONABLE_SAMPLE_SIZE,
                    maturity=metrics.maturity,
                    regime=metrics.regime,
                    evaluation_period="LAST_N_SESSIONS",
                    generated_at=now_utc,
                )
            )
        elif metrics.undershoot_rate >= 0.40:
            rec_scale = round(current_magnitude_scale * 1.15, 2)
            recs.append(
                CalibrationRecommendation(
                    metric="magnitude_scale",
                    current_calibration_factor=current_magnitude_scale,
                    observed_error=metrics.mean_absolute_error,
                    recommended_adjustment=rec_scale,
                    sample_size=metrics.sample_count,
                    minimum_required=PredictionCalibrationEngine.MIN_ACTIONABLE_SAMPLE_SIZE,
                    maturity=metrics.maturity,
                    regime=metrics.regime,
                    evaluation_period="LAST_N_SESSIONS",
                    generated_at=now_utc,
                )
            )

        return recs
