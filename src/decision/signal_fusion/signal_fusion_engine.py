from __future__ import annotations

from typing import List, Tuple

from src.analytics.breadth.models import DivergenceType, LeadershipBias
from src.analytics.options.models import OptionsConfirmationBias
from src.analytics.price_structure.models import TrendDirection
from src.analytics.regime.models import MarketRegime
from src.analytics.snapshot.analytics_snapshot import MarketAnalyticsSnapshot
from src.market_data.models.quality_enums import DataQualityStatus
from src.decision.models.decision_models import SignalFusionContext
from src.prediction.models.prediction_models import DirectionClass, PredictionSnapshot


class SignalFusionEngine:
    """
    Deterministic signal fusion engine.
    Fuses technical structure, breadth, options, and predictive forecasts without double-counting.
    Calculates explicit agreement score and conflict score.
    """

    @staticmethod
    def fuse_signals(
        analytics: MarketAnalyticsSnapshot,
        prediction: PredictionSnapshot | None = None,
    ) -> SignalFusionContext:
        """Evaluates cross-signal alignment, agreement, conflict, and evidence factors."""
        supporting: List[str] = []
        contradicting: List[str] = []
        unavailable: List[str] = []

        bull_votes = 0
        bear_votes = 0
        total_eligible = 0

        # 1. Price Structure & Regime Group (Combined as 1 fundamental group to prevent double-counting)
        trend = analytics.price_structure.trend
        regime = analytics.market_regime.regime
        total_eligible += 1

        if trend == TrendDirection.BULLISH or regime == MarketRegime.TREND_UP:
            bull_votes += 1
            supporting.append("Technical price structure indicates upward momentum")
        elif trend == TrendDirection.BEARISH or regime == MarketRegime.TREND_DOWN:
            bear_votes += 1
            contradicting.append("Technical price structure indicates downward momentum")
        elif trend == TrendDirection.UNAVAILABLE:
            unavailable.append("Price structure trend unavailable")
        else:
            supporting.append("Technical structure is range-bound / sideways")

        # 2. Breadth Group
        breadth = analytics.market_breadth
        if breadth.quality != DataQualityStatus.UNAVAILABLE:
            total_eligible += 1
            b_score = breadth.breadth_summary.weighted_breadth_score
            div = breadth.divergence.divergence
            if b_score >= 0.20 or div == DivergenceType.BULLISH_DIVERGENCE:
                bull_votes += 1
                supporting.append(f"Constituent breadth confirms buying participation ({b_score:+.2f})")
            elif b_score <= -0.20 or div == DivergenceType.BEARISH_DIVERGENCE:
                bear_votes += 1
                contradicting.append(f"Constituent breadth confirms selling pressure ({b_score:+.2f})")
        else:
            unavailable.append("Constituent market breadth data unavailable")

        # 3. Options Intelligence Group
        options = analytics.options_intelligence
        if options.quality != DataQualityStatus.UNAVAILABLE and options.bias != OptionsConfirmationBias.UNAVAILABLE:
            total_eligible += 1
            if options.bias == OptionsConfirmationBias.BULLISH:
                bull_votes += 1
                supporting.append(f"Derivatives positioning bullish (PCR: {options.pcr:.2f})")
            elif options.bias == OptionsConfirmationBias.BEARISH:
                bear_votes += 1
                contradicting.append(f"Derivatives positioning bearish (PCR: {options.pcr:.2f})")
            elif options.bias == OptionsConfirmationBias.CONFLICTED:
                contradicting.append("Derivatives positioning conflicted with intraday price")
        else:
            unavailable.append("Options chain intelligence unavailable")

        # 4. Prediction Forecast Group
        if prediction and prediction.quality != DataQualityStatus.UNAVAILABLE:
            total_eligible += 1
            p_dir = prediction.prediction_record.direction_prediction
            if p_dir == DirectionClass.BULLISH:
                bull_votes += 1
                supporting.append(f"Forecast model expects upward excursion (+{prediction.prediction_record.expected_move_points:.1f} pts)")
            elif p_dir == DirectionClass.BEARISH:
                bear_votes += 1
                contradicting.append(f"Forecast model expects downward excursion ({prediction.prediction_record.expected_move_points:.1f} pts)")
        elif prediction is None:
            unavailable.append("Prediction snapshot unavailable")

        if total_eligible == 0:
            return SignalFusionContext(
                directional_alignment="INSUFFICIENT_DATA",
                agreement_score=0.0,
                conflict_score=0.0,
                supporting_factors=[],
                contradicting_factors=[],
                unavailable_factors=unavailable,
            )

        # Alignment resolution
        if bull_votes > bear_votes:
            alignment = "BULLISH"
            agreement = round(bull_votes / total_eligible, 2)
            conflict = round(bear_votes / total_eligible, 2)
        elif bear_votes > bull_votes:
            alignment = "BEARISH"
            agreement = round(bear_votes / total_eligible, 2)
            conflict = round(bull_votes / total_eligible, 2)
        else:
            alignment = "NEUTRAL"
            agreement = 0.50
            conflict = round(min(bull_votes, bear_votes) / total_eligible, 2) if total_eligible > 0 else 0.0

        return SignalFusionContext(
            directional_alignment=alignment,
            agreement_score=agreement,
            conflict_score=conflict,
            supporting_factors=supporting,
            contradicting_factors=contradicting,
            unavailable_factors=unavailable,
        )
