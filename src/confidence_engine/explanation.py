from __future__ import annotations

from typing import List, Dict, Tuple
from src.models import (
    TradeCandidate,
    MarketScore,
    OpportunityContext,
    ConfidenceReason,
)


class ExplanationGenerator:
    """
    Formulates structured lists of positive and negative factors/reasons
    explaining why a candidate receives its confidence scores.
    """

    @staticmethod
    def generate_explanation(
        cand: TradeCandidate,
        market_score: MarketScore,
        opportunity_ctx: OpportunityContext,
        sub_scores: Dict[str, float],
        weights: Dict[str, float],
    ) -> Tuple[List[ConfidenceReason], List[ConfidenceReason]]:
        positive_factors: List[ConfidenceReason] = []
        negative_factors: List[ConfidenceReason] = []

        # 1. Strategy Suitability
        suit_score = sub_scores.get("strategy_suitability", 0.0)
        suit_weight = weights.get("strategy_suitability", 0.0)
        suit_impact = suit_score * suit_weight
        if suit_score >= 70.0:
            positive_factors.append(
                ConfidenceReason(
                    reason_type="HIGH_STRATEGY_SUITABILITY",
                    message=f"Strategy suitability is high at {cand.suitability_score:.1f}% (subscore: {suit_score:.1f}).",
                    impact=float(round(suit_impact, 2)),
                )
            )
        elif suit_score < 60.0:
            negative_factors.append(
                ConfidenceReason(
                    reason_type="LOW_STRATEGY_SUITABILITY",
                    message=f"Strategy suitability is weak at {cand.suitability_score:.1f}% (subscore: {suit_score:.1f}).",
                    impact=float(round(-suit_impact, 2)),
                )
            )

        # 2. Opportunity Quality
        opp_score = sub_scores.get("opportunity_quality", 0.0)
        opp_weight = weights.get("opportunity_quality", 0.0)
        opp_impact = opp_score * opp_weight
        if opp_score >= 70.0:
            positive_factors.append(
                ConfidenceReason(
                    reason_type="EXCELLENT_OPPORTUNITY_REGIME",
                    message=f"Strong active market opportunity setup (subscore: {opp_score:.1f}).",
                    impact=float(round(opp_impact, 2)),
                )
            )
        elif opp_score < 50.0:
            negative_factors.append(
                ConfidenceReason(
                    reason_type="WEAK_OPPORTUNITY_REGIME",
                    message=f"Thin or questionable active market opportunity (subscore: {opp_score:.1f}).",
                    impact=float(round(-opp_impact, 2)),
                )
            )

        # 3. Market Score
        mkt_score = sub_scores.get("market_score", 0.0)
        mkt_weight = weights.get("market_score", 0.0)
        mkt_impact = mkt_score * mkt_weight
        if mkt_score >= 75.0:
            positive_factors.append(
                ConfidenceReason(
                    reason_type="FAVORABLE_MARKET_ENVIRONMENT",
                    message=f"Favorable background market climate (overall score: {market_score.overall_score:.1f}%).",
                    impact=float(round(mkt_impact, 2)),
                )
            )
        elif mkt_score < 55.0:
            negative_factors.append(
                ConfidenceReason(
                    reason_type="UNFAVORABLE_MARKET_ENVIRONMENT",
                    message=f"Challenging background market climate (overall score: {market_score.overall_score:.1f}%).",
                    impact=float(round(-mkt_impact, 2)),
                )
            )

        # 4. Liquidity & Spread
        liq_score = sub_scores.get("liquidity", 0.0)
        liq_weight = weights.get("liquidity", 0.0)
        liq_impact = liq_score * liq_weight
        if liq_score >= 80.0:
            positive_factors.append(
                ConfidenceReason(
                    reason_type="ROBUST_CONTRACT_LIQUIDITY",
                    message=f"Contract exhibits strong liquidity metrics (tradability: {cand.tradability_score:.1f}).",
                    impact=float(round(liq_impact, 2)),
                )
            )
        elif liq_score < 60.0:
            negative_factors.append(
                ConfidenceReason(
                    reason_type="THIN_CONTRACT_LIQUIDITY",
                    message=f"Contract tradability is weak ({cand.tradability_score:.1f}), posing minor exit risk.",
                    impact=float(round(-liq_impact, 2)),
                )
            )

        # 5. Trend Agreement
        trend_score = sub_scores.get("trend_agreement", 0.0)
        trend_weight = weights.get("trend_agreement", 0.0)
        trend_impact = trend_score * trend_weight
        if trend_score >= 80.0:
            positive_factors.append(
                ConfidenceReason(
                    reason_type="ALIGNMENT_WITH_BIAS",
                    message=f"Option instrument aligns well with current directional bias ({opportunity_ctx.directional_bias.value}).",
                    impact=float(round(trend_impact, 2)),
                )
            )
        elif trend_score < 50.0:
            negative_factors.append(
                ConfidenceReason(
                    reason_type="DIRECTIONAL_FRICTION",
                    message="Instrument is out of sync or misaligned with active market bias.",
                    impact=float(round(-trend_impact, 2)),
                )
            )

        return positive_factors, negative_factors
