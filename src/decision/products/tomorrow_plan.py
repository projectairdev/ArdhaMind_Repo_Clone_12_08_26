from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import List, Optional

from src.market_data.models.completed_session_snapshot import CompletedSessionSnapshot
from src.market_data.models.quality_enums import DataQualityStatus
from src.prediction.models.prediction_models import PredictionOutcome


@dataclass(frozen=True)
class TomorrowPlanSnapshot:
    """
    Authoritative post-market review and next-session planning document.
    Uses canonical completed-session truth and prediction outcome evaluation.
    """
    completed_session_date: date
    next_trading_date: date
    captured_at: datetime
    session_ohlc: str
    session_range: float
    session_change: float
    day_type_regime: str
    prediction_accuracy_summary: str
    signals_worked: List[str]
    signals_failed: List[str]
    key_levels_for_tomorrow: List[float]
    preliminary_next_session_bias: str
    quality: DataQualityStatus

    def __post_init__(self) -> None:
        if self.captured_at.tzinfo is None:
            raise ValueError("TomorrowPlanSnapshot 'captured_at' must be timezone-aware.")


class TomorrowPlanGenerator:
    """Generates TomorrowPlanSnapshot from completed session truth and outcome evaluation."""

    @staticmethod
    def generate(
        completed_session: CompletedSessionSnapshot,
        next_trading_date: date,
        outcome: Optional[PredictionOutcome] = None,
        day_regime: str = "TREND_UP",
    ) -> TomorrowPlanSnapshot:
        now_utc = datetime.now(timezone.utc)
        ohlc = f"O: {completed_session.open:.1f} | H: {completed_session.high:.1f} | L: {completed_session.low:.1f} | C: {completed_session.close:.1f}"

        worked: List[str] = []
        failed: List[str] = []

        if outcome:
            if outcome.direction_correct:
                worked.append(f"Directional forecast ({outcome.actual_direction.value}) confirmed by session move ({outcome.actual_session_move:+.1f} pts)")
            else:
                failed.append("Directional forecast contradicted by session close")

            if outcome.range_hit:
                worked.append(f"Session range ({outcome.actual_range:.1f} pts) captured within predicted volatility band")
            else:
                failed.append(f"Magnitude bias: {outcome.magnitude_bias.value} (Error: {outcome.magnitude_error:+.1f} pts)")

            pred_summary = f"Direction: {'CORRECT' if outcome.direction_correct else 'INCORRECT'} | Range Hit: {'YES' if outcome.range_hit else 'NO'} | Magnitude Error: {outcome.magnitude_error:+.1f} pts"
        else:
            pred_summary = "Prediction outcome evaluation not supplied"

        # Key levels for tomorrow: PDH, PDL, PDC, and midpoint pivot
        pivot = round((completed_session.high + completed_session.low + completed_session.close) / 3.0, 1)
        levels = [completed_session.low, pivot, completed_session.close, completed_session.high]
        levels.sort()

        bias = "BULLISH" if (completed_session.absolute_change and completed_session.absolute_change > 0) else "BEARISH"

        return TomorrowPlanSnapshot(
            completed_session_date=completed_session.session_date,
            next_trading_date=next_trading_date,
            captured_at=now_utc,
            session_ohlc=ohlc,
            session_range=completed_session.range,
            session_change=completed_session.absolute_change or 0.0,
            day_type_regime=day_regime,
            prediction_accuracy_summary=pred_summary,
            signals_worked=worked,
            signals_failed=failed,
            key_levels_for_tomorrow=levels,
            preliminary_next_session_bias=bias,
            quality=completed_session.quality,
        )
