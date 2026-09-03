from __future__ import annotations

from typing import Optional, Tuple

from src.analytics.snapshot.analytics_snapshot import MarketAnalyticsSnapshot
from src.decision.models.decision_models import (
    DecisionRiskLevel,
    DecisionState,
    OpportunityAssessment,
    RiskAssessment,
    SetupType,
    SignalFusionContext,
)
from src.market_data.models.quality_enums import DataQualityStatus


class NoTradeEngine:
    """
    Deterministic no-trade and safety gating engine.
    Establishes when market conditions dictate an explicit NO_TRADE or BLOCKED conclusion.
    A valid NO_TRADE conclusion is treated as a primary first-class output.
    """

    @staticmethod
    def evaluate_gate(
        analytics: MarketAnalyticsSnapshot,
        fusion: SignalFusionContext,
        opportunity: OpportunityAssessment,
        risk: RiskAssessment,
    ) -> Tuple[bool, Optional[DecisionState], Optional[str]]:
        """
        Returns (is_gated, recommended_state, reason).
        If is_gated is True, the market must not proceed to review.
        """
        # 1. Critical Data Quality Blocker
        if analytics.quality == DataQualityStatus.UNAVAILABLE:
            return True, DecisionState.BLOCKED, "Market data quality is unavailable"

        # 2. Extreme Volatility / Risk Blocker
        if risk.is_blocked or risk.risk_level == DecisionRiskLevel.BLOCKED:
            return True, DecisionState.BLOCKED, risk.blocker_reason or "Risk conditions blocked"

        # 3. High Conflict Gating
        if fusion.conflict_score >= 0.50:
            return True, DecisionState.NO_TRADE, "Internal signals critically conflicted (Conflict score >= 0.50)"

        # 4. No Invalidation Level Established
        if opportunity.setup != SetupType.NO_SETUP and opportunity.invalidation_level is None:
            return True, DecisionState.NO_TRADE, "No clear structural invalidation boundary established"

        # 5. No Structural Opportunity
        if opportunity.setup == SetupType.NO_SETUP:
            return True, DecisionState.NO_TRADE, "No qualified structural setup detected"

        return False, None, None
