from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import List, Optional

from src.analytics.snapshot.analytics_snapshot import MarketAnalyticsSnapshot
from src.market_data.models.quality_enums import DataQualityStatus
from src.prediction.models.prediction_models import MagnitudeDistribution, PredictionSnapshot


@dataclass(frozen=True)
class MorningPlanSnapshot:
    """
    Authoritative pre-market intelligence briefing.
    Answers: 'What should I watch at today's open?'
    """
    session_date: date
    captured_at: datetime
    reference_close: float
    opening_bias: str
    direction_probability: float
    expected_magnitude: MagnitudeDistribution
    important_levels: List[float]
    gap_context_summary: str
    regime_expectation: str
    options_summary: str
    bullish_scenario: str
    bearish_scenario: str
    no_trade_scenario: str
    opening_checklist: List[str]
    quality: DataQualityStatus

    def __post_init__(self) -> None:
        if self.captured_at.tzinfo is None:
            raise ValueError("MorningPlanSnapshot 'captured_at' must be timezone-aware.")


class MorningPlanGenerator:
    """Generates deterministic MorningPlanSnapshot from pre-market analytics and prediction."""

    @staticmethod
    def generate(
        analytics: MarketAnalyticsSnapshot,
        prediction: PredictionSnapshot,
    ) -> MorningPlanSnapshot:
        now_utc = datetime.now(timezone.utc)
        rec = prediction.prediction_record
        ps = analytics.price_structure

        levels = [l.price for l in ps.support_levels] + [l.price for l in ps.resistance_levels]
        levels.sort()

        bias = rec.direction_prediction.value
        prob = rec.direction_probability
        mag = rec.magnitude_distribution

        bullish_scen = f"Sustained opening above {ps.last_price:.1f} with breadth confirmation targets +{mag.expected_magnitude:.0f} pts."
        bearish_scen = f"Breakdown below nearest support cluster ({levels[0] if levels else ps.last_price:.1f}) targets -{mag.expected_magnitude:.0f} pts."
        no_trade_scen = "Choppy opening within first 15m range without volume confirmation."

        checklist = [
            "Observe 15m Opening Range (09:15-09:30 IST) boundaries",
            "Verify constituent advance/decline ratio (>1.5 for long, <0.7 for short)",
            "Check Options PCR alignment with intraday price trajectory",
            "Confirm clear invalidation level before acting",
        ]

        return MorningPlanSnapshot(
            session_date=analytics.session_date,
            captured_at=now_utc,
            reference_close=ps.last_price,
            opening_bias=bias,
            direction_probability=prob,
            expected_magnitude=mag,
            important_levels=levels[:6],
            gap_context_summary=f"{ps.gap_context.gap_type.value} ({ps.gap_context.gap_points:+.1f} pts)",
            regime_expectation=analytics.market_regime.regime.value,
            options_summary=f"PCR {analytics.options_intelligence.pcr:.2f} | Put Wall {analytics.options_intelligence.put_wall:.0f} | Call Wall {analytics.options_intelligence.call_wall:.0f}",
            bullish_scenario=bullish_scen,
            bearish_scenario=bearish_scen,
            no_trade_scenario=no_trade_scen,
            opening_checklist=checklist,
            quality=analytics.quality,
        )
