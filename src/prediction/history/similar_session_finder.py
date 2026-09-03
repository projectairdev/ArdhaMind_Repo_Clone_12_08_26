from __future__ import annotations

from datetime import date
from typing import List, Optional, Sequence

from src.market_data.models.completed_session_snapshot import CompletedSessionSnapshot
from src.prediction.models.prediction_models import SimilarSessionMatch


class SimilarSessionFinder:
    """
    Deterministic historical analog finder.
    Matches current session context against past completed sessions with zero lookahead bias.
    """

    @staticmethod
    def find_analogs(
        historical_snapshots: Sequence[CompletedSessionSnapshot],
        as_of_session_date: date,
        current_regime: str,
        current_range_estimate: float,
        limit: int = 5,
    ) -> List[SimilarSessionMatch]:
        """Finds closest historical sessions strictly prior to as_of_session_date."""
        priors = [s for s in historical_snapshots if s.session_date < as_of_session_date]
        if not priors:
            return []

        scored_matches: List[SimilarSessionMatch] = []
        for s in priors:
            # Range distance score
            range_diff = abs(s.range - current_range_estimate)
            range_sim = max(0.0, 1.0 - (range_diff / max(1.0, current_range_estimate)))

            sim_score = round(range_sim, 2)
            if sim_score >= 0.50:
                dir_str = "BULLISH" if s.absolute_change and s.absolute_change > 0 else "BEARISH"
                scored_matches.append(
                    SimilarSessionMatch(
                        session_date=s.session_date,
                        similarity_score=sim_score,
                        regime=current_regime,
                        observed_move_pts=s.absolute_change or 0.0,
                        observed_range_pts=s.range,
                        observed_direction=dir_str,
                    )
                )

        scored_matches.sort(key=lambda m: m.similarity_score, reverse=True)
        return scored_matches[:limit]
