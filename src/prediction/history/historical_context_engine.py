from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional, Sequence

from src.market_data.models.completed_session_snapshot import CompletedSessionSnapshot


@dataclass(frozen=True)
class HistoricalRollContext:
    """Date-safe rolling session statistics."""
    sample_count: int
    rolling_5_avg_range: float
    rolling_20_avg_range: float
    rolling_20_median_range: float
    up_session_ratio: float
    down_session_ratio: float
    avg_gap_points: float


class HistoricalContextEngine:
    """
    Computes date-safe rolling historical features.
    Enforces zero lookahead bias by strictly filtering out present/future session data.
    """

    @staticmethod
    def compute_rolling_metrics(
        historical_snapshots: Sequence[CompletedSessionSnapshot],
        as_of_session_date: date,
    ) -> HistoricalRollContext:
        """Calculates rolling historical range and directional statistics strictly prior to as_of_session_date."""
        # Enforce strict historical filtering (session_date < as_of_session_date)
        prior_snapshots = [s for s in historical_snapshots if s.session_date < as_of_session_date]

        if not prior_snapshots:
            return HistoricalRollContext(
                sample_count=0,
                rolling_5_avg_range=120.0,
                rolling_20_avg_range=120.0,
                rolling_20_median_range=120.0,
                up_session_ratio=0.50,
                down_session_ratio=0.50,
                avg_gap_points=30.0,
            )

        # Sort chronologically
        sorted_snaps = sorted(prior_snapshots, key=lambda s: s.session_date)
        ranges = [s.range for s in sorted_snaps]

        # 5-session average
        r5 = ranges[-5:] if len(ranges) >= 5 else ranges
        avg_r5 = round(sum(r5) / len(r5), 1)

        # 20-session average and median
        r20 = ranges[-20:] if len(ranges) >= 20 else ranges
        avg_r20 = round(sum(r20) / len(r20), 1)
        sorted_r20 = sorted(r20)
        median_r20 = sorted_r20[len(sorted_r20) // 2]

        # Directional win rate (change > 0)
        up_count = sum(1 for s in sorted_snaps[-20:] if s.absolute_change and s.absolute_change > 0)
        down_count = sum(1 for s in sorted_snaps[-20:] if s.absolute_change and s.absolute_change < 0)
        total_dir = max(1, up_count + down_count)

        return HistoricalRollContext(
            sample_count=len(sorted_snaps),
            rolling_5_avg_range=avg_r5,
            rolling_20_avg_range=avg_r20,
            rolling_20_median_range=median_r20,
            up_session_ratio=round(up_count / total_dir, 2),
            down_session_ratio=round(down_count / total_dir, 2),
            avg_gap_points=30.0,
        )
