from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional, Sequence
from uuid import uuid4

from src.analytics.snapshot.analytics_snapshot import MarketAnalyticsSnapshot
from src.market_data.models.completed_session_snapshot import CompletedSessionSnapshot
from src.market_data.models.quality_enums import DataQualityStatus
from src.prediction.confidence.prediction_confidence_engine import PredictionConfidenceEngine
from src.prediction.direction.direction_prediction_engine import DirectionPredictionEngine
from src.prediction.history.historical_context_engine import HistoricalContextEngine
from src.prediction.history.similar_session_finder import SimilarSessionFinder
from src.prediction.magnitude.magnitude_prediction_engine import MagnitudePredictionEngine
from src.prediction.models.prediction_models import (
    DirectionClass,
    PredictionPhase,
    PredictionRecord,
    PredictionSnapshot,
)


class PredictionEngine:
    """
    Authoritative provider-independent prediction coordinator.
    Composes Direction, Magnitude, Confidence, and Historical Analogs into an immutable PredictionSnapshot.
    """

    MODEL_VERSION = "v1.0.0"
    FEATURE_SCHEMA_VERSION = "v1.0.0"
    CALIBRATION_VERSION = "v1.0.0"

    @staticmethod
    def generate_prediction(
        snapshot: MarketAnalyticsSnapshot,
        target_session_date: date,
        phase: PredictionPhase = PredictionPhase.PRE_MARKET,
        historical_sessions: Optional[Sequence[CompletedSessionSnapshot]] = None,
    ) -> PredictionSnapshot:
        """Generates comprehensive, immutable forecast snapshot from analytics and historical context."""
        now_utc = datetime.now(timezone.utc)
        ref_price = snapshot.price_structure.last_price
        history = historical_sessions or []

        # 1. Infer Direction
        direction, dir_prob, features, supporting, cautions = DirectionPredictionEngine.infer_direction(snapshot)

        # 2. Infer Magnitude (Separate from direction)
        mag_dist = MagnitudePredictionEngine.infer_magnitude(
            atr_context=snapshot.price_structure.atr,
            compression_context=snapshot.price_structure.compression,
            vix_price=snapshot.vix_price,
        )

        # Signed expected move in points
        if direction == DirectionClass.BULLISH:
            signed_move = mag_dist.expected_magnitude
        elif direction == DirectionClass.BEARISH:
            signed_move = -mag_dist.expected_magnitude
        else:
            signed_move = 0.0

        # 3. Infer Confidence
        conf_score, conf_band = PredictionConfidenceEngine.evaluate_confidence(
            direction=direction,
            direction_probability=dir_prob,
            snapshot=snapshot,
        )

        # 4. Find Similar Session Analogs (Date-safe)
        analogs = SimilarSessionFinder.find_analogs(
            historical_snapshots=history,
            as_of_session_date=target_session_date,
            current_regime=snapshot.market_regime.regime.value,
            current_range_estimate=mag_dist.expected_magnitude,
        )

        # 5. Build Immutable PredictionRecord
        rec = PredictionRecord(
            prediction_id=f"pred_{uuid4().hex[:12]}",
            model_version=PredictionEngine.MODEL_VERSION,
            feature_schema_version=PredictionEngine.FEATURE_SCHEMA_VERSION,
            calibration_version=PredictionEngine.CALIBRATION_VERSION,
            created_at=now_utc,
            target_session_date=target_session_date,
            prediction_phase=phase,
            reference_price=ref_price,
            reference_timestamp=snapshot.captured_at,
            direction_prediction=direction,
            direction_probability=dir_prob,
            expected_move_points=signed_move,
            magnitude_distribution=mag_dist,
            confidence_score=conf_score,
            confidence_band=conf_band,
            input_state_revision=snapshot.state_revision,
            input_quality=snapshot.quality,
            market_regime=snapshot.market_regime.regime.value,
            volatility_context=snapshot.vix_price or snapshot.price_structure.atr.atr_value,
            features_used=features,
            supporting_factors=supporting,
            caution_factors=cautions,
        )

        return PredictionSnapshot(
            prediction_record=rec,
            similar_sessions=analogs,
            quality=snapshot.quality,
            calibration_status="CALIBRATED",
        )
