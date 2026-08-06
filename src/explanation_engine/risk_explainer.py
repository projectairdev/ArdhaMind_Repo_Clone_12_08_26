from __future__ import annotations

from typing import Optional, List
from src.models import RiskReport, RiskExplanation


def explain_risk(risk_report: Optional[RiskReport]) -> RiskExplanation:
    """
    Explains the risk grade, portfolio exposure levels, utilization,
    and individual candidate risk profiles.
    """
    if not risk_report:
        return RiskExplanation(
            portfolio_risk_grade="N/A",
            total_capital_allocated=0.0,
            portfolio_utilization_pct=0.0,
            portfolio_risk_reasoning="No active risk report available to generate risk explanations.",
            warnings_explanations=[],
        )

    sum_data = risk_report.summary
    exp_summary = risk_report.exposure_summary

    risk_grade = sum_data.portfolio_risk_grade
    allocated_cap = exp_summary.total_capital_allocated
    util_pct = exp_summary.portfolio_utilization_pct
    highest_risk_cid = sum_data.highest_risk_candidate_id
    lowest_risk_cid = sum_data.lowest_risk_candidate_id
    conclusions = sum_data.conclusions

    reasoning = (
        f"The risk management engine evaluated the portfolio and designated a overall risk grade of '{risk_grade}'. "
        f"A total capital of INR {allocated_cap:,.2f} has been allocated, representing {util_pct:.1f}% portfolio utilization. "
    )

    if highest_risk_cid and highest_risk_cid != "NONE":
        reasoning += f"The candidate carrying the highest risk exposure is '{highest_risk_cid}'. "
    if lowest_risk_cid and lowest_risk_cid != "NONE" and lowest_risk_cid != highest_risk_cid:
        reasoning += f"The candidate with the lowest risk profile is '{lowest_risk_cid}'. "

    if conclusions:
        reasoning += " Risk conclusions: " + " ".join(conclusions)

    # Gather warnings explanations
    warn_exps: List[str] = []
    for cr in risk_report.candidate_risks:
        for w in cr.warnings:
            warn_exps.append(
                f"Candidate {cr.candidate_id}: Triggered {w.warning_type} ({w.severity}) - {w.message}"
            )
        for c in cr.constraints:
            if c.is_violated:
                warn_exps.append(
                    f"Candidate {cr.candidate_id}: Violated portfolio constraint {c.constraint_type} (Limit: {c.limit_value:.1f}, Current: {c.current_value:.1f})"
                )

    return RiskExplanation(
        portfolio_risk_grade=risk_grade,
        total_capital_allocated=allocated_cap,
        portfolio_utilization_pct=util_pct,
        portfolio_risk_reasoning=reasoning,
        warnings_explanations=warn_exps,
    )
