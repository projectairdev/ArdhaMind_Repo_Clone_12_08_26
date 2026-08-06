from __future__ import annotations

from typing import List
from src.models import (
    TradeCandidate,
    MarketScore,
    OpportunityContext,
    ConfidenceBonus,
)


class BonusCalculator:
    """
    Stateless calculator for identifying and evaluating candidate confidence bonuses.
    """

    @staticmethod
    def calculate_bonuses(
        cand: TradeCandidate,
        market_score: MarketScore,
        opportunity_ctx: OpportunityContext,
    ) -> List[ConfidenceBonus]:
        bonuses: List[ConfidenceBonus] = []

        # 1. Ultra Tight Spread Bonus
        if cand.spread_pct <= 0.10:
            bonuses.append(
                ConfidenceBonus(
                    bonus_type="ULTRA_TIGHT_SPREAD",
                    message=f"Bid-ask spread is exceptionally tight ({cand.spread_pct:.2f}%), reducing slippage risk.",
                    value=5.0,
                )
            )

        # 2. Deep OI Support Bonus
        if cand.oi >= 50000:
            bonuses.append(
                ConfidenceBonus(
                    bonus_type="DEEP_OI_SUPPORT",
                    message=f"Thick open interest ({cand.oi:,} contracts) provides highly liquid execution support.",
                    value=5.0,
                )
            )

        # 3. High Suitability Bonus
        if cand.suitability_score >= 85.0:
            bonuses.append(
                ConfidenceBonus(
                    bonus_type="HIGH_STRATEGY_SUITABILITY",
                    message=f"Outstanding alignment ({cand.suitability_score:.1f}%) with current market conditions.",
                    value=5.0,
                )
            )

        # 4. Strong Trend Alignment Bonus
        bias = opportunity_ctx.directional_bias.value if opportunity_ctx.directional_bias else "NEUTRAL"
        trend_score = market_score.trend.overall_trend_score
        if trend_score >= 75.0:
            if (bias == "BULLISH" and cand.instrument_type == "CE") or \
               (bias == "BEARISH" and cand.instrument_type == "PE"):
                bonuses.append(
                    ConfidenceBonus(
                        bonus_type="STRONG_TREND_CONFLUENCE",
                        message=f"Candidate aligns directly with a robust {bias} market trend (trend score: {trend_score:.1f}%).",
                        value=5.0,
                    )
                )

        return bonuses
