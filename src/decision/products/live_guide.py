from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import List, Optional

from src.analytics.snapshot.analytics_snapshot import MarketAnalyticsSnapshot
from src.decision.models.decision_models import DecisionSnapshot, StrikeCandidate
from src.market_data.models.quality_enums import DataQualityStatus


@dataclass(frozen=True)
class LiveGuideSnapshot:
    """
    Authoritative real-time intraday guide.
    Answers: 'What is happening NOW and is there a valid setup?'
    """
    session_date: date
    captured_at: datetime
    nifty_price: float
    session_phase: str
    trend: str
    structure_summary: str
    vwap_summary: Optional[str]
    twap_summary: Optional[str]
    breadth_summary: str
    options_summary: str
    regime: str
    active_setup: str
    trigger_condition: str
    confirmation_requirements: List[str]
    invalidation_condition: str
    strike_candidates: List[StrikeCandidate]
    risk_level: str
    decision_state: str
    decision_confidence: str
    data_health: str

    def __post_init__(self) -> None:
        if self.captured_at.tzinfo is None:
            raise ValueError("LiveGuideSnapshot 'captured_at' must be timezone-aware.")


class LiveGuideGenerator:
    """Generates deterministic LiveGuideSnapshot combining analytics, prediction, and decision state."""

    @staticmethod
    def generate(
        analytics: MarketAnalyticsSnapshot,
        decision: DecisionSnapshot,
        session_phase: str = "MARKET_OPEN",
    ) -> LiveGuideSnapshot:
        now_utc = datetime.now(timezone.utc)
        ps = analytics.price_structure

        vwap_str = f"VWAP: {ps.vwap_context.vwap:.1f} ({ps.vwap_context.price_position})" if ps.vwap_context else "VWAP: UNAVAILABLE (Volume missing)"
        twap_str = f"TWAP: {ps.twap_context.twap:.1f} ({ps.twap_context.price_position})" if ps.twap_context else None

        breadth = analytics.market_breadth.breadth_summary
        breadth_str = f"Adv: {breadth.advances} | Dec: {breadth.declines} | Score: {breadth.weighted_breadth_score:+.2f}"

        options = analytics.options_intelligence
        opt_str = f"PCR: {options.pcr:.2f} | Put Wall: {options.put_wall:.0f} | Call Wall: {options.call_wall:.0f}"

        return LiveGuideSnapshot(
            session_date=analytics.session_date,
            captured_at=now_utc,
            nifty_price=ps.last_price,
            session_phase=session_phase,
            trend=ps.trend.value,
            structure_summary=f"Range: {ps.opening_range.range_size or 0.0:.1f} pts | OR Status: {ps.opening_range.status}",
            vwap_summary=vwap_str,
            twap_summary=twap_str,
            breadth_summary=breadth_str,
            options_summary=opt_str,
            regime=analytics.market_regime.regime.value,
            active_setup=decision.setup.setup.value,
            trigger_condition=decision.setup.trigger_condition,
            confirmation_requirements=decision.setup.confirmation_requirements,
            invalidation_condition=decision.setup.invalidation_condition,
            strike_candidates=decision.strike_candidates,
            risk_level=decision.risk_assessment.risk_level.value,
            decision_state=decision.decision_state.value,
            decision_confidence=decision.confidence_band,
            data_health=analytics.quality.value,
        )
