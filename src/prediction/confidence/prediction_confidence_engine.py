from __future__ import annotations

from typing import Tuple

from src.analytics.options.models import OptionsConfirmationBias
from src.analytics.price_structure.models import TrendDirection
from src.analytics.regime.models import MarketRegime
from src.analytics.snapshot.analytics_snapshot import MarketAnalyticsSnapshot
from src.market_data.models.quality_enums import DataQualityStatus
from src.prediction.models.prediction_models import ConfidenceBand, DirectionClass


class PredictionConfidenceEngine:
    """
    Deterministic confidence assessment engine.
    Ensures that high directional conviction cannot be assigned HIGH confidence
    when data quality is degraded, signals conflict, or inputs are incomplete.
    """

    @staticmethod
    def evaluate_confidence(
        direction: DirectionClass,
        direction_probability: float,
        snapshot: MarketAnalyticsSnapshot,
    ) -> Tuple[float, ConfidenceBand]:
        """Calculates confidence score (0.0 to 1.0) and confidence band."""
        if snapshot.quality == DataQualityStatus.UNAVAILABLE or direction == DirectionClass.INSUFFICIENT_DATA:
            return 0.0, ConfidenceBand.INSUFFICIENT

        base_score = 0.50

        # 1. Signal Agreement
        trend = snapshot.price_structure.trend
        opt_bias = snapshot.options_intelligence.bias
        regime = snapshot.market_regime.regime

        agreements = 0
        conflicts = 0

        if direction == DirectionClass.BULLISH:
            if trend == TrendDirection.BULLISH:
                agreements += 1
            if opt_bias == OptionsConfirmationBias.BULLISH:
                agreements += 1
            elif opt_bias == OptionsConfirmationBias.BEARISH:
                conflicts += 1
            if regime == MarketRegime.TREND_UP:
                agreements += 1
        elif direction == DirectionClass.BEARISH:
            if trend == TrendDirection.BEARISH:
                agreements += 1
            if opt_bias == OptionsConfirmationBias.BEARISH:
                agreements += 1
            elif opt_bias == OptionsConfirmationBias.BULLISH:
                conflicts += 1
            if regime == MarketRegime.TREND_DOWN:
                agreements += 1

        base_score += (agreements * 0.12) - (conflicts * 0.20)

        # 2. Data Completeness & Quality Penalties
        if snapshot.market_breadth.quality == DataQualityStatus.DELAYED:
            base_score -= 0.15
        elif snapshot.market_breadth.quality == DataQualityStatus.UNAVAILABLE:
            base_score -= 0.20

        if snapshot.options_intelligence.quality == DataQualityStatus.UNAVAILABLE:
            base_score -= 0.15

        if snapshot.quality == DataQualityStatus.DELAYED:
            base_score -= 0.15

        # 3. Regime Penalties
        if regime in (MarketRegime.CONFLICTED, MarketRegime.INSUFFICIENT_DATA):
            base_score -= 0.25

        score = round(max(0.05, min(0.95, base_score)), 2)

        # Guard: Degraded data cannot produce HIGH confidence band
        if snapshot.quality != DataQualityStatus.VALID and score >= 0.75:
            score = 0.65

        if score >= 0.75:
            band = ConfidenceBand.HIGH
        elif score >= 0.50:
            band = ConfidenceBand.MODERATE
        elif score >= 0.25:
            band = ConfidenceBand.LOW
        else:
            band = ConfidenceBand.INSUFFICIENT

        return score, band
