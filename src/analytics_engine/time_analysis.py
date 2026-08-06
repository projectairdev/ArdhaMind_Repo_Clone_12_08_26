from __future__ import annotations

from datetime import datetime
from typing import List, Dict
from src.models import TimePerformance, TradeJournalEntry

class TimeAnalyser:
    """
    Stateless evaluator for temporal patterns in trading performance.
    """

    @staticmethod
    def parse_time(time_str: str) -> datetime | None:
        if not time_str:
            return None
        # Remove trailing Z or offsets for simplicity
        clean_str = time_str.split("+")[0].split("Z")[0].strip()
        for fmt in (
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d",
        ):
            try:
                return datetime.strptime(clean_str, fmt)
            except ValueError:
                continue
        return None

    @classmethod
    def analyze(cls, entries: List[TradeJournalEntry]) -> TimePerformance:
        if not entries:
            return TimePerformance()

        by_entry_hour: Dict[int, float] = {}
        by_day_of_week: Dict[str, float] = {}
        total_holding_time = 0.0

        for e in entries:
            total_holding_time += e.duration_seconds

            dt = cls.parse_time(e.entry_time)
            if dt is not None:
                hour = dt.hour
                day_name = dt.strftime("%A")

                by_entry_hour[hour] = by_entry_hour.get(hour, 0.0) + e.pnl
                by_day_of_week[day_name] = by_day_of_week.get(day_name, 0.0) + e.pnl
            else:
                # Fallback if unparseable
                by_entry_hour[10] = by_entry_hour.get(10, 0.0) + e.pnl
                by_day_of_week["Monday"] = by_day_of_week.get("Monday", 0.0) + e.pnl

        avg_holding_time = total_holding_time / len(entries) if entries else 0.0

        return TimePerformance(
            by_entry_hour=by_entry_hour,
            by_day_of_week=by_day_of_week,
            avg_holding_time=avg_holding_time,
        )
