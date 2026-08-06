from __future__ import annotations

from typing import List, Tuple
from src.models import (
    TradeCandidate,
    CandidateRisk,
    DecisionReason,
    DecisionWarning,
)


def generate_explanations(
    candidate: TradeCandidate,
    confidence_score: float,
    risk_cand: CandidateRisk,
    decision: str,
) -> Tuple[str, List[DecisionReason], List[DecisionReason], List[DecisionWarning]]:
    """
    Generates structured supporting evidence, blocking factors, warnings, and a readable explanation.
    """
    supporting_evidence: List[DecisionReason] = []
    blocking_factors: List[DecisionReason] = []
    warnings: List[DecisionWarning] = []

    # 1. Evaluate Confidence
    if confidence_score >= 70.0:
        supporting_evidence.append(
            DecisionReason(
                reason_type="HIGH_CONFIDENCE",
                message=f"Candidate has strong confidence score of {confidence_score:.1f}%",
                metric_name="confidence_score",
                metric_value=confidence_score,
            )
        )
    elif confidence_score >= 50.0:
        supporting_evidence.append(
            DecisionReason(
                reason_type="MODERATE_CONFIDENCE",
                message=f"Candidate has moderate confidence score of {confidence_score:.1f}%",
                metric_name="confidence_score",
                metric_value=confidence_score,
            )
        )
    else:
        blocking_factors.append(
            DecisionReason(
                reason_type="LOW_CONFIDENCE",
                message=f"Candidate confidence score of {confidence_score:.1f}% is below watch threshold.",
                metric_name="confidence_score",
                metric_value=confidence_score,
            )
        )

    # 2. Evaluate Risk and Allocation
    if risk_cand is not None:
        if not risk_cand.is_approved:
            blocking_factors.append(
                DecisionReason(
                    reason_type="RISK_ENGINE_REJECTED",
                    message=f"Risk engine rejected candidate. Grade: {risk_cand.risk_grade}",
                    metric_name="risk_approved",
                    metric_value=0.0,
                )
            )
            for constr in risk_cand.constraints:
                if constr.is_violated:
                    blocking_factors.append(
                        DecisionReason(
                            reason_type=f"VIOLATED_{constr.constraint_type}",
                            message=f"Constraint {constr.constraint_type} violated: Limit {constr.limit_value:.2f}, Current {constr.current_value:.2f}",
                            metric_name=constr.constraint_type,
                            metric_value=constr.current_value,
                        )
                    )
        else:
            supporting_evidence.append(
                DecisionReason(
                    reason_type="RISK_ENGINE_APPROVED",
                    message=f"Risk engine approved candidate. Grade: {risk_cand.risk_grade}",
                    metric_name="risk_approved",
                    metric_value=1.0,
                )
            )
            supporting_evidence.append(
                DecisionReason(
                    reason_type="CAPITAL_ALLOCATED",
                    message=f"Capital allocation: {risk_cand.capital_allocation.allocated_capital:.2f} across {risk_cand.capital_allocation.allocated_lots} lots.",
                    metric_name="allocated_capital",
                    metric_value=risk_cand.capital_allocation.allocated_capital,
                )
            )

        # Propagate warnings from risk
        for w in risk_cand.warnings:
            warnings.append(
                DecisionWarning(
                    warning_type=w.warning_type,
                    message=w.message,
                    severity=w.severity,
                )
            )
    else:
        blocking_factors.append(
            DecisionReason(
                reason_type="NO_RISK_DATA",
                message="No risk analysis record found for this candidate.",
                metric_name="risk_data_exists",
                metric_value=0.0,
            )
        )

    # 3. Evaluate Candidate-specific Attributes
    if candidate.spread_pct > 0.5:
        warnings.append(
            DecisionWarning(
                warning_type="HIGH_SPREAD",
                message=f"Candidate has higher bid-ask spread of {candidate.spread_pct:.2f}%",
                severity="MEDIUM",
            )
        )
    if candidate.iv > 25.0:
        warnings.append(
            DecisionWarning(
                warning_type="HIGH_IV_WARNING",
                message=f"High implied volatility of {candidate.iv:.1f}% increases option price decay risk.",
                severity="LOW",
            )
        )

    # 4. Formulate overall explanation
    if decision == "BUY":
        explanation = f"Approved BUY decision based on high confidence ({confidence_score:.1f}%) and solid risk engine authorization with capital allocation."
    elif decision == "SELL":
        explanation = f"Approved SELL decision (bearish setup/PE option) based on high confidence ({confidence_score:.1f}%) and risk engine authorization."
    elif decision == "WATCH":
        explanation = f"Set to WATCH. Candidate is approved but confidence is moderate ({confidence_score:.1f}%) or portfolio limits were exceeded."
    elif decision == "REJECT":
        reasons_list = [f.message for f in blocking_factors]
        explanation = f"REJECTED: " + "; ".join(reasons_list)
    else:  # NO TRADE
        explanation = "NO TRADE: Capital allocation or execution criteria were not satisfied."

    return explanation, supporting_evidence, blocking_factors, warnings
