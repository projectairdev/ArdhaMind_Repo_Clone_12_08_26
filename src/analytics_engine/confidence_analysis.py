from __future__ import annotations

from typing import List, Dict
from src.models import ConfidencePerformance, TradeJournalEntry

class ConfidenceAnalyser:
    """
    Stateless evaluator for confidence score correlation with performance.
    """

    @staticmethod
    def get_band(score: float) -> str:
        if 50.0 <= score < 60.0:
            return "50–60"
        elif 60.0 <= score < 70.0:
            return "60–70"
        elif 70.0 <= score < 80.0:
            return "70–80"
        elif 80.0 <= score < 90.0:
            return "80–90"
        elif 90.0 <= score <= 100.0:
            return "90–100"
        elif score < 50.0:
            return "Under 50"
        else:
            return "Over 100"

    @classmethod
    def analyze(cls, entries: List[TradeJournalEntry]) -> List[ConfidencePerformance]:
        if not entries:
            return []

        grouped: Dict[str, List[TradeJournalEntry]] = {}

        for e in entries:
            b = cls.get_band(e.confidence_score)
            grouped.setdefault(b, []).append(e)

        results: List[ConfidencePerformance] = []
        for band in sorted(grouped.keys()):
            band_entries = grouped[band]
            total = len(band_entries)
            if total == 0:
                continue

            wins = [x for x in band_entries if x.pnl > 0]
            win_rate = (len(wins) / total) * 100.0
            average_return = sum(x.pnl for x in band_entries) / total

            results.append(
                ConfidencePerformance(
                    confidence_band=band,
                    total_trades=total,
                    win_rate=win_rate,
                    average_return=average_return,
                )
            )

        return results
