from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from src.analytics.breadth.models import DivergenceType, LeadershipBias
from src.analytics.options.models import OptionsConfirmationBias
from src.analytics.price_structure.models import TrendDirection
from src.analytics.regime.models import MarketRegime
from src.analytics.snapshot.analytics_snapshot import MarketAnalyticsSnapshot
from src.market_data.models.quality_enums import DataQualityStatus
from src.prediction.models.prediction_models import DirectionClass


@dataclass(frozen=True)
class FactorContribution:
    factor_name: str
    raw_weight: float
    effective_weight: float
    available: bool
    raw_score: float  # -1.0 to +1.0
    weighted_contribution: float


class DirectionPredictionEngine:
    """
    Deterministic provider-independent direction prediction engine.
    Applies strict dynamic weight normalization across available evidence factors.
    Guarantees that unavailable factors contribute zero weight without inflating probabilities.
    """

    RAW_WEIGHTS = {
        "trend": 0.35,
        "regime": 0.20,
        "breadth": 0.25,
        "leadership": 0.15,
        "options": 0.25,
    }

    @staticmethod
    def infer_direction(
        snapshot: MarketAnalyticsSnapshot,
    ) -> Tuple[DirectionClass, float, List[str], List[str], List[str]]:
        """
        Computes directional forecast, probability, features used, and explanatory factors.
        Returns (direction, probability, features_used, supporting_factors, caution_factors).
        """
        direction, probability, _, features, supporting, cautions = DirectionPredictionEngine.infer_direction_detailed(snapshot)
        return direction, probability, features, supporting, cautions

    @staticmethod
    def infer_direction_detailed(
        snapshot: MarketAnalyticsSnapshot,
    ) -> Tuple[DirectionClass, float, List[FactorContribution], List[str], List[str], List[str]]:
        """
        Detailed inference returning FactorContributions with effective normalized weights.
        """
        if snapshot.quality == DataQualityStatus.UNAVAILABLE or snapshot.price_structure.quality == DataQualityStatus.UNAVAILABLE:
            return (
                DirectionClass.INSUFFICIENT_DATA,
                0.50,
                [],
                ["price_structure_quality"],
                [],
                ["Market data unavailable or invalid"],
            )

        supporting: List[str] = []
        cautions: List[str] = []
        features_used: List[str] = []

        # Evaluate individual raw scores and availability
        factor_scores: Dict[str, Tuple[bool, float]] = {}

        # 1. Price Trend
        trend = snapshot.price_structure.trend
        if trend != TrendDirection.UNAVAILABLE:
            if trend == TrendDirection.BULLISH:
                factor_scores["trend"] = (True, 1.0)
                supporting.append("Price structure in confirmed uptrend")
            elif trend == TrendDirection.BEARISH:
                factor_scores["trend"] = (True, -1.0)
                supporting.append("Price structure in confirmed downtrend")
            else:
                factor_scores["trend"] = (True, 0.0)
                cautions.append("Price structure is sideways / non-trending")
        else:
            factor_scores["trend"] = (False, 0.0)

        # 2. Market Regime
        regime = snapshot.market_regime.regime
        if regime != MarketRegime.INSUFFICIENT_DATA:
            if regime == MarketRegime.TREND_UP:
                factor_scores["regime"] = (True, 1.0)
                supporting.append("Regime: Confirmed Trend Up")
            elif regime == MarketRegime.TREND_DOWN:
                factor_scores["regime"] = (True, -1.0)
                supporting.append("Regime: Confirmed Trend Down")
            elif regime == MarketRegime.COMPRESSION:
                factor_scores["regime"] = (True, 0.0)
                cautions.append("Regime: Volatility compression")
            elif regime == MarketRegime.CONFLICTED:
                factor_scores["regime"] = (True, 0.0)
                cautions.append("Regime: Internal signals conflicted")
            else:
                factor_scores["regime"] = (True, 0.0)
        else:
            factor_scores["regime"] = (False, 0.0)

        # 3. Market Breadth
        breadth = snapshot.market_breadth
        if breadth.quality != DataQualityStatus.UNAVAILABLE:
            b_score = breadth.breadth_summary.weighted_breadth_score
            # Divergence adjustment
            div = breadth.divergence.divergence
            if div == DivergenceType.BEARISH_DIVERGENCE:
                b_score = max(-1.0, b_score - 0.5)
                cautions.append("Bearish breadth divergence detected (Narrow advance)")
            elif div == DivergenceType.BULLISH_DIVERGENCE:
                b_score = min(1.0, b_score + 0.5)
                supporting.append("Bullish breadth divergence detected (Broad accumulation)")
            elif b_score >= 0.2:
                supporting.append(f"Positive constituent breadth participation ({b_score:+.2f})")
            elif b_score <= -0.2:
                supporting.append(f"Negative constituent breadth participation ({b_score:+.2f})")

            factor_scores["breadth"] = (True, max(-1.0, min(1.0, b_score)))
        else:
            factor_scores["breadth"] = (False, 0.0)
            cautions.append("Market breadth unavailable - breadth weighting bypassed")

        # 4. Heavyweight Leadership
        hw = snapshot.market_breadth.leadership
        if hw.quality != DataQualityStatus.UNAVAILABLE and hw.leadership_bias != LeadershipBias.UNAVAILABLE:
            if hw.leadership_bias == LeadershipBias.BULLISH:
                factor_scores["leadership"] = (True, 1.0)
                supporting.append("Heavyweight leadership positive")
            elif hw.leadership_bias == LeadershipBias.BEARISH:
                factor_scores["leadership"] = (True, -1.0)
                supporting.append("Heavyweight leadership negative")
            else:
                factor_scores["leadership"] = (True, 0.0)
        else:
            factor_scores["leadership"] = (False, 0.0)

        # 5. Options Confirmation
        options = snapshot.options_intelligence
        if options.quality != DataQualityStatus.UNAVAILABLE and options.bias != OptionsConfirmationBias.UNAVAILABLE:
            opt_score = options.confirmation_score
            if options.bias == OptionsConfirmationBias.BULLISH:
                supporting.append(f"Options positioning bullish (PCR: {options.pcr:.2f})")
            elif options.bias == OptionsConfirmationBias.BEARISH:
                supporting.append(f"Options positioning bearish (PCR: {options.pcr:.2f})")
            elif options.bias == OptionsConfirmationBias.CONFLICTED:
                cautions.append("Options positioning conflicted with price trend")

            factor_scores["options"] = (True, max(-1.0, min(1.0, opt_score)))
        else:
            factor_scores["options"] = (False, 0.0)
            cautions.append("Options chain unavailable - derivatives weighting bypassed")

        # Dynamic Normalization Calculation
        available_weights_sum = sum(
            DirectionPredictionEngine.RAW_WEIGHTS[fname]
            for fname, (is_avail, _) in factor_scores.items()
            if is_avail
        )

        if available_weights_sum < 0.35:
            return (
                DirectionClass.INSUFFICIENT_DATA,
                0.50,
                [],
                [],
                [],
                ["Insufficient eligible factor weight for direction prediction"],
            )

        contributions: List[FactorContribution] = []
        normalized_score = 0.0

        for fname, raw_w in DirectionPredictionEngine.RAW_WEIGHTS.items():
            is_avail, raw_s = factor_scores.get(fname, (False, 0.0))
            if is_avail:
                eff_w = round(raw_w / available_weights_sum, 4)
                contrib = round(raw_s * eff_w, 4)
                normalized_score += contrib
                features_used.append(fname)
            else:
                eff_w = 0.0
                contrib = 0.0

            contributions.append(
                FactorContribution(
                    factor_name=fname,
                    raw_weight=raw_w,
                    effective_weight=eff_w,
                    available=is_avail,
                    raw_score=raw_s,
                    weighted_contribution=contrib,
                )
            )

        normalized_score = max(-1.0, min(1.0, normalized_score))
        probability = round(0.50 + (normalized_score * 0.45), 3)

        if normalized_score >= 0.25:
            direction = DirectionClass.BULLISH
        elif normalized_score <= -0.25:
            direction = DirectionClass.BEARISH
        else:
            direction = DirectionClass.NEUTRAL

        return direction, probability, contributions, features_used, supporting, cautions
