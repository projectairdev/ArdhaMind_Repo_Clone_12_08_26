from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.market_data.models.quality_enums import DataQualityStatus


class PredictionPhase(str, Enum):
    PRE_MARKET = "PRE_MARKET"  # Before 09:00 IST
    PRE_OPEN = "PRE_OPEN"      # 09:00 - 09:15 IST
    OPENING = "OPENING"        # 09:15 - 09:30 IST
    INTRADAY = "INTRADAY"      # 09:30 - 15:30 IST


class DirectionClass(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class ConfidenceBand(str, Enum):
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    INSUFFICIENT = "INSUFFICIENT"


class MagnitudeBias(str, Enum):
    ACCURATE = "ACCURATE"
    OVERPREDICTED = "OVERPREDICTED"
    UNDERPREDICTED = "UNDERPREDICTED"


class CalibrationMaturity(str, Enum):
    INSUFFICIENT_SAMPLE = "INSUFFICIENT_SAMPLE"  # N < 5
    OBSERVATIONAL = "OBSERVATIONAL"              # 5 <= N < 20
    ACTIONABLE = "ACTIONABLE"                    # N >= 20


@dataclass(frozen=True)
class MagnitudeDistribution:
    """
    Discrete probability distribution over move magnitude buckets (in points).
    Probabilities sum to 1.0.
    """
    p_0_50: float
    p_50_100: float
    p_100_150: float
    p_150_200: float
    p_200_plus: float
    expected_magnitude: float
    median_magnitude: float
    lower_band_pts: float
    upper_band_pts: float

    def __post_init__(self) -> None:
        total_p = round(self.p_0_50 + self.p_50_100 + self.p_100_150 + self.p_150_200 + self.p_200_plus, 2)
        if total_p != 1.00:
            raise ValueError(f"MagnitudeDistribution probabilities must sum to 1.0, got {total_p}")


@dataclass(frozen=True)
class SimilarSessionMatch:
    """Historical session analog."""
    session_date: date
    similarity_score: float  # 0.0 to 1.0
    regime: str
    observed_move_pts: float
    observed_range_pts: float
    observed_direction: str


@dataclass(frozen=True)
class PredictionRecord:
    """
    Authoritative, immutable forecast record.
    Captures exact forecast parameters before outcome is observed.
    """
    prediction_id: str
    model_version: str
    feature_schema_version: str
    calibration_version: str
    created_at: datetime
    target_session_date: date
    prediction_phase: PredictionPhase
    reference_price: float
    reference_timestamp: datetime
    direction_prediction: DirectionClass
    direction_probability: float  # 0.0 to 1.0
    expected_move_points: float  # signed points (+ for up, - for down)
    magnitude_distribution: MagnitudeDistribution
    confidence_score: float  # 0.0 to 1.0
    confidence_band: ConfidenceBand
    input_state_revision: int
    input_quality: DataQualityStatus
    market_regime: str
    volatility_context: float  # ATR or VIX
    features_used: List[str]
    supporting_factors: List[str]
    caution_factors: List[str]
    expected_open_low: Optional[float] = None
    expected_open_high: Optional[float] = None

    def __post_init__(self) -> None:
        if self.created_at.tzinfo is None or self.reference_timestamp.tzinfo is None:
            raise ValueError("PredictionRecord timestamps must be timezone-aware.")


@dataclass(frozen=True)
class PredictionOutcome:
    """
    Immutable evaluation record comparing a PredictionRecord to canonical completed session truth.
    Separates directional correctness from magnitude accuracy.
    """
    prediction_id: str
    target_session_date: date
    actual_open: float
    actual_high: float
    actual_low: float
    actual_close: float
    actual_open_move: float
    actual_session_move: float
    actual_range: float
    actual_direction: DirectionClass
    direction_correct: bool
    magnitude_error: float  # predicted_move - actual_move
    absolute_error: float   # abs(magnitude_error)
    range_hit: bool         # actual_range within predicted lower/upper band
    bucket_hit: bool        # actual_magnitude falls in highest probability bucket
    magnitude_bias: MagnitudeBias
    evaluated_at: datetime

    def __post_init__(self) -> None:
        if self.evaluated_at.tzinfo is None:
            raise ValueError("PredictionOutcome 'evaluated_at' must be timezone-aware.")


@dataclass(frozen=True)
class CalibrationRecommendation:
    """Non-mutating diagnostic calibration feedback."""
    metric: str
    current_calibration_factor: float
    observed_error: float
    recommended_adjustment: float
    sample_size: int
    minimum_required: int
    maturity: CalibrationMaturity
    regime: str
    evaluation_period: str
    generated_at: datetime


@dataclass(frozen=True)
class RegimeCalibrationMetrics:
    """Performance metrics aggregated per market regime."""
    regime: str
    sample_count: int
    minimum_required_for_actionable: int
    maturity: CalibrationMaturity
    direction_accuracy: float
    brier_score: float
    mean_absolute_error: float
    root_mean_squared_error: float
    median_absolute_error: float
    range_hit_rate: float
    bucket_hit_rate: float
    overshoot_rate: float
    undershoot_rate: float


@dataclass(frozen=True)
class PredictionSnapshot:
    """Master prediction container combining forecast, analogs, and diagnostic metadata."""
    prediction_record: PredictionRecord
    similar_sessions: List[SimilarSessionMatch]
    quality: DataQualityStatus
    calibration_status: str
