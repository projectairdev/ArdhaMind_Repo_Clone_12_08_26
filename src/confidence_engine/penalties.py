from __future__ import annotations

from typing import List
from src.models import (
    TradeCandidate,
    MarketScore,
    OpportunityContext,
    ConfidencePenalty,
)


class PenaltyCalculator:
    """
    Stateless calculator for identifying and evaluating candidate confidence penalties.
    """

    @staticmethod
    def calculate_penalties(
        cand: TradeCandidate,
        market_score: MarketScore,
        opportunity_ctx: OpportunityContext,
    ) -> List[ConfidencePenalty]:
        penalties: List[ConfidencePenalty] = []

        # 1. Elevated IV Penalty
        if cand.iv >= 30.0:
            penalties.append(
                ConfidencePenalty(
                    penalty_type="ELEVATED_IV_PREMIUM",
                    message=f"Implied volatility is dangerously high ({cand.iv:.1f}%), elevating position crash risk.",
                    value=5.0,
                )
            )

        # 2. Far OTM Strike Penalty
        # If the option strike is far from ATM (e.g. 2 steps or more, or class other/ATM_PLUS_2/ATM_MINUS_2/etc.)
        if cand.distance_from_atm >= 100 or cand.atm_distance_class in ("OTHER", "ATM_PLUS_2", "ATM_MINUS_2"):
            penalties.append(
                ConfidencePenalty(
                    penalty_type="FAR_OTM_STRIKE",
                    message=f"Strike is located far from ATM ({cand.distance_from_atm} points away), increasing decay exposure.",
                    value=5.0,
                )
            )

        # 3. Wide Spread Penalty
        if cand.spread_pct >= 0.25:
            penalties.append(
                ConfidencePenalty(
                    penalty_type="WIDE_SPREAD_FRICTION",
                    message=f"Bid-ask spread is wide ({cand.spread_pct:.2f}%), raising entry/exit friction costs.",
                    value=5.0,
                )
            )

        # 4. Low OI Penalty
        if cand.oi < 5000:
            penalties.append(
                ConfidencePenalty(
                    penalty_type="LOW_OI_LIQUIDITY_RISK",
                    message=f"Thin open interest ({cand.oi:,} contracts) increases slippage and liquidity risk.",
                    value=5.0,
                )
            )

        return penalties
