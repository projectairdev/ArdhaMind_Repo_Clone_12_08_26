from __future__ import annotations

from typing import Optional, Tuple

from src.analytics.price_structure.models import BreakoutStatus, PriceStructureContext, TrendDirection
from src.analytics.snapshot.analytics_snapshot import MarketAnalyticsSnapshot
from src.decision.models.decision_models import (
    EntryReadinessStatus,
    OpportunityAssessment,
    SetupType,
    SignalFusionContext,
)
from src.market_data.models.quality_enums import DataQualityStatus


class OpportunityDetectionEngine:
    """
    Deterministic opportunity classification, trigger definition, and invalidation engine.
    Derives triggers and invalidations strictly from canonical reference levels (zero LLM-invented numbers).
    """

    @staticmethod
    def evaluate_opportunity(
        analytics: MarketAnalyticsSnapshot,
        fusion: SignalFusionContext,
    ) -> Tuple[OpportunityAssessment, EntryReadinessStatus]:
        """Classifies active structural setup, trigger conditions, and entry readiness."""
        if analytics.quality == DataQualityStatus.UNAVAILABLE or analytics.price_structure.quality == DataQualityStatus.UNAVAILABLE:
            return (
                OpportunityAssessment(
                    setup=SetupType.NO_SETUP,
                    status="BLOCKED",
                    rationale="Insufficient or unavailable market data",
                    trigger_condition="N/A",
                    confirmation_requirements=[],
                    invalidation_level=None,
                    invalidation_condition="N/A",
                ),
                EntryReadinessStatus.BLOCKED_DATA_QUALITY,
            )

        ps = analytics.price_structure
        last_price = ps.last_price
        trend = ps.trend
        or_ctx = ps.opening_range
        breakout = ps.breakout

        # 1. Retest of Broken Level (takes precedence when retest state is active)
        if breakout.status == BreakoutStatus.RETESTING and breakout.level_price:
            inv_lvl = round(breakout.level_price - 25.0, 1) if trend == TrendDirection.BULLISH else round(breakout.level_price + 25.0, 1)
            return (
                OpportunityAssessment(
                    setup=SetupType.RETEST,
                    status="FORMING",
                    rationale=f"Price retesting broken level ({breakout.level_source}: {breakout.level_price:.1f}) and holding",
                    trigger_condition=f"Rejection wick and bounce off {breakout.level_price:.1f}",
                    confirmation_requirements=["Volume confirmation on bounce", "No close below retest level"],
                    invalidation_level=inv_lvl,
                    invalidation_condition=f"Decisive break beyond {inv_lvl:.1f}",
                ),
                EntryReadinessStatus.WAITING_FOR_TRIGGER,
            )

        # 2. Opening Range Breakout (ORB)
        if or_ctx.is_established and or_ctx.high and or_ctx.low:
            if last_price > or_ctx.high and fusion.directional_alignment == "BULLISH":
                inv_lvl = or_ctx.low
                return (
                    OpportunityAssessment(
                        setup=SetupType.OPENING_RANGE_BREAKOUT,
                        status="ACTIVE",
                        rationale=f"Price ({last_price:.1f}) trading above 15m Opening Range High ({or_ctx.high:.1f}) with bullish confirmation",
                        trigger_condition=f"Sustained acceptance above OR High ({or_ctx.high:.1f})",
                        confirmation_requirements=["5m candle close above ORH", "Positive constituent breadth (ADR > 1.5)"],
                        invalidation_level=inv_lvl,
                        invalidation_condition=f"Pullback and sustained close below OR Low ({inv_lvl:.1f})",
                    ),
                    EntryReadinessStatus.READY_FOR_HUMAN_REVIEW,
                )
            elif last_price < or_ctx.low and fusion.directional_alignment == "BEARISH":
                inv_lvl = or_ctx.high
                return (
                    OpportunityAssessment(
                        setup=SetupType.BREAKDOWN,
                        status="ACTIVE",
                        rationale=f"Price ({last_price:.1f}) broke below 15m Opening Range Low ({or_ctx.low:.1f}) with bearish pressure",
                        trigger_condition=f"Sustained acceptance below OR Low ({or_ctx.low:.1f})",
                        confirmation_requirements=["5m candle close below ORL", "Constituent declines dominate"],
                        invalidation_level=inv_lvl,
                        invalidation_condition=f"Rebound and close above OR High ({inv_lvl:.1f})",
                    ),
                    EntryReadinessStatus.READY_FOR_HUMAN_REVIEW,
                )

        # 3. Trend Continuation
        if trend == TrendDirection.BULLISH and len(ps.support_levels) > 0:
            nearest_supp = ps.support_levels[0].price
            inv_lvl = nearest_supp
            return (
                OpportunityAssessment(
                    setup=SetupType.TREND_CONTINUATION,
                    status="WATCH",
                    rationale=f"Higher highs uptrend intact; nearest support cluster at {nearest_supp:.1f}",
                    trigger_condition=f"Hold above support {nearest_supp:.1f} and reclaim previous swing high",
                    confirmation_requirements=["Higher low confirmation", "Options PCR > 1.10"],
                    invalidation_level=inv_lvl,
                    invalidation_condition=f"Breakdown and close below support {nearest_supp:.1f}",
                ),
                EntryReadinessStatus.WAITING_FOR_TRIGGER,
            )
        elif trend == TrendDirection.BEARISH and len(ps.resistance_levels) > 0:
            nearest_res = ps.resistance_levels[0].price
            inv_lvl = nearest_res
            return (
                OpportunityAssessment(
                    setup=SetupType.TREND_CONTINUATION,
                    status="WATCH",
                    rationale=f"Lower lows downtrend intact; nearest resistance cluster at {nearest_res:.1f}",
                    trigger_condition=f"Rejection at resistance {nearest_res:.1f} and break of lower swing low",
                    confirmation_requirements=["Lower high confirmation", "Options PCR < 0.85"],
                    invalidation_level=inv_lvl,
                    invalidation_condition=f"Rally and close above resistance {nearest_res:.1f}",
                ),
                EntryReadinessStatus.WAITING_FOR_TRIGGER,
            )

        # 4. Default: No Structural Setup
        return (
            OpportunityAssessment(
                setup=SetupType.NO_SETUP,
                status="NO_OPPORTUNITY",
                rationale="Market oscillating without clear directional breakout or defined invalidation level",
                trigger_condition="Awaiting clear structural expansion or range test",
                confirmation_requirements=[],
                invalidation_level=None,
                invalidation_condition="N/A",
            ),
            EntryReadinessStatus.NOT_READY,
        )
