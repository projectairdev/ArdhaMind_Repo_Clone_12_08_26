from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Optional

from src.decision.models.decision_models import DecisionSnapshot


@dataclass(frozen=True)
class MarketIntelligenceSummary:
    """
    High-level trader-facing unified intelligence summary.
    Backed directly by canonical decision structures (zero independent recalculation).
    """
    session_date: date
    captured_at: datetime
    nifty_bias: str
    setup_name: str
    top_strike_candidate: Optional[str]
    entry_condition: str
    confidence_band: str
    liquidity_level: str
    data_quality: str
    risk_level: str
    decision_status: str

    def __post_init__(self) -> None:
        if self.captured_at.tzinfo is None:
            raise ValueError("MarketIntelligenceSummary 'captured_at' must be timezone-aware.")


class MarketIntelligenceSummaryGenerator:
    """Generates the unified MarketIntelligenceSummary from an authoritative DecisionSnapshot."""

    @staticmethod
    def generate(decision: DecisionSnapshot) -> MarketIntelligenceSummary:
        top_strike = None
        top_liq = "UNAVAILABLE"
        if decision.strike_candidates:
            cand = decision.strike_candidates[0]
            top_strike = f"{cand.strike:.0f} {cand.option_type.value}"
            top_liq = cand.liquidity

        return MarketIntelligenceSummary(
            session_date=decision.session_date,
            captured_at=decision.captured_at,
            nifty_bias=decision.signal_fusion.directional_alignment,
            setup_name=decision.setup.setup.value,
            top_strike_candidate=top_strike,
            entry_condition=decision.setup.trigger_condition,
            confidence_band=decision.confidence_band,
            liquidity_level=top_liq,
            data_quality=decision.quality.value,
            risk_level=decision.risk_assessment.risk_level.value,
            decision_status=decision.decision_state.value,
        )
