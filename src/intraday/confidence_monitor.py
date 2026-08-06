from __future__ import annotations

from typing import List, Optional, Dict
from src.models import (
    EveningReport,
    ConfidenceReport,
    ConfidenceChange,
    CandidateStatus,
)


def monitor_confidence(
    evening_report: EveningReport,
    current_confidence_report: Optional[ConfidenceReport] = None,
) -> List[ConfidenceChange]:
    changes = []
    if not evening_report.top_candidates:
        return changes

    current_conf_map = {}
    if current_confidence_report and current_confidence_report.candidate_confidences:
        current_conf_map = {
            c.candidate_id: c.confidence_score
            for c in current_confidence_report.candidate_confidences
        }

    for cand in evening_report.top_candidates:
        cand_id = cand.candidate_id
        prev_conf = cand.confidence_score
        curr_conf = current_conf_map.get(cand_id, prev_conf)
        change_amt = curr_conf - prev_conf

        status = CandidateStatus.UNCHANGED
        explanation = f"Confidence is unchanged at {curr_conf:.1f}%."

        if change_amt >= 5.0:
            status = CandidateStatus.IMPROVED
            explanation = f"Confidence improved by {change_amt:+.1f} points (from {prev_conf:.1f}% to {curr_conf:.1f}%)."
        elif change_amt <= -15.0:
            status = CandidateStatus.INVALIDATED
            explanation = f"Confidence collapsed by {change_amt:.1f} points (from {prev_conf:.1f}% to {curr_conf:.1f}%)."
        elif change_amt <= -5.0:
            status = CandidateStatus.WEAKENED
            explanation = f"Confidence weakened by {change_amt:.1f} points (from {prev_conf:.1f}% to {curr_conf:.1f}%)."

        changes.append(
            ConfidenceChange(
                candidate_id=cand_id,
                previous_confidence=prev_conf,
                current_confidence=curr_conf,
                change_amt=change_amt,
                status=status,
                explanation=explanation,
            )
        )

    return changes
