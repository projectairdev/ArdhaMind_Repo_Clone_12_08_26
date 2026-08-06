from __future__ import annotations

from typing import List, Optional, Dict
from src.models import (
    EveningReport,
    ConfidenceReport,
    RiskReport,
    DecisionReport,
    CandidateStatusReport,
    CandidateStatus,
)


def monitor_candidates(
    evening_report: EveningReport,
    current_confidence_report: Optional[ConfidenceReport] = None,
    current_risk_report: Optional[RiskReport] = None,
    current_decision_report: Optional[DecisionReport] = None,
) -> List[CandidateStatusReport]:
    reports = []
    if not evening_report.top_candidates:
        return reports

    # Build confidence map
    current_conf_map = {}
    if current_confidence_report and current_confidence_report.candidate_confidences:
        current_conf_map = {
            c.candidate_id: c.confidence_score
            for c in current_confidence_report.candidate_confidences
        }

    # Build risk map
    current_risk_map = {}
    if current_risk_report and current_risk_report.candidate_risks:
        current_risk_map = {
            r.candidate_id: r for r in current_risk_report.candidate_risks
        }

    # Build decision map
    current_dec_map = {}
    if current_decision_report and current_decision_report.candidate_decisions:
        current_dec_map = {
            d.candidate_id: d for d in current_decision_report.candidate_decisions
        }

    for cand in evening_report.top_candidates:
        cand_id = cand.candidate_id
        prev_conf = cand.confidence_score
        prev_decision = cand.decision

        curr_conf = current_conf_map.get(cand_id, prev_conf)
        curr_decision_obj = current_dec_map.get(cand_id)
        curr_decision = curr_decision_obj.decision if curr_decision_obj else prev_decision
        curr_risk_obj = current_risk_map.get(cand_id)

        # Start with default status
        status = CandidateStatus.UNCHANGED
        explanation = "Candidate parameters remain within planned thresholds."

        # Check for invalidation first
        is_rejected_by_risk = curr_risk_obj is not None and not curr_risk_obj.is_approved
        is_rejected_by_decision = curr_decision == "REJECT"

        if is_rejected_by_risk or is_rejected_by_decision:
            status = CandidateStatus.INVALIDATED
            explanation = "Rejected by real-time risk/decision engine."
            if curr_decision_obj and curr_decision_obj.explanation:
                explanation = f"Rejected: {curr_decision_obj.explanation}"
            elif curr_risk_obj and curr_risk_obj.summary:
                explanation = "Rejected due to active risk/exposure violations."
        elif curr_conf < 50.0:
            status = CandidateStatus.INVALIDATED
            explanation = f"Confidence collapsed to {curr_conf:.1f}% (below critical 50% threshold)."
        elif prev_conf - curr_conf >= 15.0:
            status = CandidateStatus.INVALIDATED
            explanation = f"Severe confidence drop from {prev_conf:.1f}% to {curr_conf:.1f}%."
        # Check for weakened
        elif prev_decision in ("BUY", "SELL") and curr_decision in ("WATCH", "NO TRADE"):
            status = CandidateStatus.WEAKENED
            explanation = f"Decision downgraded from {prev_decision} to {curr_decision}."
        elif prev_conf - curr_conf >= 5.0:
            status = CandidateStatus.WEAKENED
            explanation = f"Confidence weakened from {prev_conf:.1f}% to {curr_conf:.1f}%."
        # Check for improved
        elif prev_decision in ("WATCH", "NO TRADE") and curr_decision in ("BUY", "SELL"):
            status = CandidateStatus.IMPROVED
            explanation = f"Decision upgraded from {prev_decision} to {curr_decision}."
        elif curr_conf - prev_conf >= 5.0:
            status = CandidateStatus.IMPROVED
            explanation = f"Confidence improved from {prev_conf:.1f}% to {curr_conf:.1f}%."

        reports.append(
            CandidateStatusReport(
                candidate_id=cand_id,
                tradingsymbol=cand.tradingsymbol,
                status=status,
                explanation=explanation,
                previous_decision=prev_decision,
                suggested_decision=curr_decision,
            )
        )

    return reports
