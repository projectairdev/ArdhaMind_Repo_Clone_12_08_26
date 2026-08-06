from __future__ import annotations

from typing import Optional
from src.models import ConfidenceReport, ConfidenceExplanation


def explain_confidence(confidence_report: Optional[ConfidenceReport]) -> ConfidenceExplanation:
    """
    Explains the confidence levels, highlighting the highest confidence choices
    and aggregating general confidence levels and conclusions.
    """
    if not confidence_report or not confidence_report.candidate_confidences:
        return ConfidenceExplanation(
            highest_confidence_candidate_id="NONE",
            confidence_reasoning="No active confidence report available to explain.",
        )

    sum_data = confidence_report.summary
    highest_cid = sum_data.highest_confidence_candidate_id
    lowest_cid = sum_data.lowest_confidence_candidate_id
    avg_conf = sum_data.average_confidence
    total_eval = sum_data.total_evaluated
    conclusions = sum_data.conclusions

    reasoning = (
        f"A total of {total_eval} trade candidates were evaluated for execution confidence. "
        f"The average candidate confidence is {avg_conf:.1f}%. "
    )

    # Find highest candidate details
    highest_candidate = None
    for cc in confidence_report.candidate_confidences:
        if cc.candidate_id == highest_cid:
            highest_candidate = cc
            break

    if highest_candidate:
        reasoning += (
            f"The candidate with the highest conviction is '{highest_cid}' with a score of {highest_candidate.confidence_score:.1f}% "
            f"(raw score: {highest_candidate.raw_score:.1f}%). "
        )
        pos_reasons = [f.message for f in highest_candidate.positive_factors]
        if pos_reasons:
            reasoning += "This top score is supported by: " + "; ".join(pos_reasons) + ". "

    if lowest_cid and lowest_cid != "NONE" and lowest_cid != highest_cid:
        reasoning += f"The lowest conviction score was observed on candidate '{lowest_cid}'. "

    if conclusions:
        reasoning += "Key confidence conclusions: " + " ".join(conclusions)

    return ConfidenceExplanation(
        highest_confidence_candidate_id=highest_cid,
        confidence_reasoning=reasoning,
    )
