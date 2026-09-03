from __future__ import annotations

from typing import List, Optional

from src.analytics.snapshot.analytics_snapshot import MarketAnalyticsSnapshot
from src.decision.models.decision_models import DecisionRiskLevel, RiskAssessment, SignalFusionContext
from src.market_data.models.quality_enums import DataQualityStatus


class RiskAssessmentEngine:
    """
    Deterministic decision risk assessment engine.
    Evaluates market conditions, volatility, conflict, and data quality to establish risk levels.
    """

    @staticmethod
    def assess_risk(
        analytics: MarketAnalyticsSnapshot,
        fusion: SignalFusionContext,
    ) -> RiskAssessment:
        """Evaluates aggregate decision risk level and risk factors."""
        factors: List[str] = []
        is_blocked = False
        blocker_msg: Optional[str] = None

        # 1. Data Quality Blocker
        if analytics.quality == DataQualityStatus.UNAVAILABLE:
            return RiskAssessment(
                risk_level=DecisionRiskLevel.BLOCKED,
                risk_factors=["Market analytics data is unavailable or invalid"],
                is_blocked=True,
                blocker_reason="Data Quality Unavailable",
            )

        # 2. Volatility Assessment
        vix = analytics.vix_price
        if vix:
            if vix >= 24.0:
                factors.append(f"Extreme volatility environment (India VIX: {vix:.2f} >= 24.0)")
                is_blocked = True
                blocker_msg = "Extreme Market Volatility"
            elif vix >= 18.0:
                factors.append(f"Elevated volatility environment (India VIX: {vix:.2f} >= 18.0)")

        # 3. Conflict Assessment
        if fusion.conflict_score >= 0.40:
            factors.append(f"High multi-signal conflict score ({fusion.conflict_score:.2f} >= 0.40)")

        # 4. Compression / Expansion
        if analytics.price_structure.compression.is_compressing:
            factors.append("Volatility compression active - false breakout hazard")

        # Risk level determination
        if is_blocked:
            level = DecisionRiskLevel.BLOCKED
        elif len(factors) >= 2 or (vix and vix >= 18.0) or fusion.conflict_score >= 0.40:
            level = DecisionRiskLevel.HIGH
        elif len(factors) == 1:
            level = DecisionRiskLevel.MODERATE
        else:
            level = DecisionRiskLevel.LOW

        return RiskAssessment(
            risk_level=level,
            risk_factors=factors,
            is_blocked=is_blocked,
            blocker_reason=blocker_msg,
        )
