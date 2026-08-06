from __future__ import annotations

from typing import List
from src.models import ConfidenceBonus, ConfidencePenalty


class ScoreNormalizer:
    """
    Stateless scorer to handle raw weighted score aggregation,
    applying bonuses/penalties and strictly bounding the output score to 0-100.
    """

    @staticmethod
    def normalize_score(
        raw_score: float,
        bonuses: List[ConfidenceBonus],
        penalties: List[ConfidencePenalty],
    ) -> float:
        total_bonus = sum(b.value for b in bonuses)
        total_penalty = sum(p.value for p in penalties)
        
        final_score = raw_score + total_bonus - total_penalty
        # Ensure result is bounded strictly within [0.0, 100.0]
        return float(round(min(100.0, max(0.0, final_score)), 2))
