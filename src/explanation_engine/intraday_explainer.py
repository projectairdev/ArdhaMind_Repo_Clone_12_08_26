from __future__ import annotations

from typing import Optional, List
from src.models import IntradayReport, IntradayExplanation, PlanStatus, ActionRecommendation


def explain_intraday(intraday_report: Optional[IntradayReport]) -> IntradayExplanation:
    """
    Explains the live intraday changes, checking plan validity, action recommendation,
    and explaining significant changes in market metrics or candidates.
    """
    if not intraday_report:
        return IntradayExplanation(
            plan_status="N/A",
            action_recommendation="N/A",
            explanation="No active intraday report available to explain.",
            market_change_reasons=[],
            candidate_change_reasons=[],
        )

    sum_data = intraday_report.summary
    p_status = sum_data.plan_status
    a_rec = sum_data.action_recommendation

    p_status_str = p_status.value if isinstance(p_status, PlanStatus) else str(p_status)
    a_rec_str = a_rec.value if isinstance(a_rec, ActionRecommendation) else str(a_rec)

    # 1. Market changes
    m_reasons: List[str] = []
    for mc in intraday_report.market_changes:
        pct_suffix = f" ({mc.change_pct:+.2f}%)" if mc.change_pct is not None else ""
        sig_prefix = "[SIGNIFICANT] " if mc.is_significant else ""
        m_reasons.append(
            f"{sig_prefix}Metric '{mc.metric_name}' changed from {mc.previous_value} to {mc.current_value}{pct_suffix}. {mc.message}"
        )

    # 2. Candidate status reports
    c_reasons: List[str] = []
    for cc in intraday_report.candidate_changes:
        status_val = cc.status.value if hasattr(cc.status, "value") else str(cc.status)
        detail = f"Candidate '{cc.candidate_id}' status is {status_val}. Decision: {cc.previous_decision} -> {cc.suggested_decision}."
        if cc.explanation:
            detail += f" {cc.explanation}"
        c_reasons.append(detail)

    # Add confidence changes
    for cc in intraday_report.confidence_changes:
        status_val = cc.status.value if hasattr(cc.status, "value") else str(cc.status)
        c_reasons.append(
            f"Confidence for '{cc.candidate_id}' changed from {cc.previous_confidence:.1f}% to {cc.current_confidence:.1f}% (Shift: {cc.change_amt:+.1f}%, Status: {status_val}). {cc.explanation}"
        )

    # Add risk changes
    for rc in intraday_report.risk_changes:
        risk_inc_msg = "Risk increased!" if rc.is_risk_increased else "Risk stable."
        c_reasons.append(
            f"Risk grade for '{rc.candidate_id}' shifted from {rc.previous_risk_grade} to {rc.current_risk_grade}. {risk_inc_msg}"
        )

    # 3. Overall explanation
    explanation_text = (
        f"The intraday monitoring system evaluated the current market and decided the plan status is '{p_status_str}' "
        f"with an action recommendation to '{a_rec_str}'. "
        f"Total candidates monitored: {sum_data.total_candidates_monitored}. Invalidated candidates: {sum_data.invalidated_candidates_count}. "
        f"Significant market changes detected: {sum_data.significant_market_changes_count}. "
        f"Overall VIX Shift: {sum_data.overall_vix_shift:+.2f}, PCR Shift: {sum_data.overall_pcr_shift:+.2f}. "
    )

    if intraday_report.validation_reasons:
        explanation_text += "Validation checks: " + "; ".join(intraday_report.validation_reasons) + "."

    return IntradayExplanation(
        plan_status=p_status_str,
        action_recommendation=a_rec_str,
        explanation=explanation_text,
        market_change_reasons=m_reasons,
        candidate_change_reasons=c_reasons,
    )
