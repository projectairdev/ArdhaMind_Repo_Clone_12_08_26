from __future__ import annotations

from typing import Any, Dict, Optional
from src.models import IntradayReport, PlanStatus, ActionRecommendation, CandidateStatus

class IntradayPanel:
    """
    Stateless Intraday Panel.
    Displays IntradayReport contents comparing current live state to the evening plan.
    """

    def __init__(self, intraday_report: Optional[IntradayReport] = None) -> None:
        self.intraday_report = intraday_report

    def to_dict(self) -> Dict[str, Any]:
        """
        Extracts structured presentation data for intraday status tracking.
        """
        if not self.intraday_report:
            return {}

        ir = self.intraday_report

        market_changes = []
        for mc in ir.market_changes:
            market_changes.append({
                "metric_name": mc.metric_name,
                "previous_value": mc.previous_value,
                "current_value": mc.current_value,
                "change_pct": mc.change_pct,
                "is_significant": mc.is_significant,
                "message": mc.message,
            })

        candidate_changes = []
        for cc in ir.candidate_changes:
            candidate_changes.append({
                "candidate_id": cc.candidate_id,
                "tradingsymbol": cc.tradingsymbol,
                "status": cc.status.value if hasattr(cc.status, "value") else str(cc.status),
                "explanation": cc.explanation,
                "previous_decision": cc.previous_decision,
                "suggested_decision": cc.suggested_decision,
            })

        confidence_changes = []
        for conf_c in ir.confidence_changes:
            confidence_changes.append({
                "candidate_id": conf_c.candidate_id,
                "previous_confidence": conf_c.previous_confidence,
                "current_confidence": conf_c.current_confidence,
                "change_amt": conf_c.change_amt,
                "status": conf_c.status.value if hasattr(conf_c.status, "value") else str(conf_c.status),
                "explanation": conf_c.explanation,
            })

        risk_changes = []
        for rc in ir.risk_changes:
            risk_changes.append({
                "candidate_id": rc.candidate_id,
                "previous_risk_grade": rc.previous_risk_grade,
                "current_risk_grade": rc.current_risk_grade,
                "is_risk_increased": rc.is_risk_increased,
                "triggered_new_warnings": rc.triggered_new_warnings,
            })

        # Resolve plan status and action recommendation string representations
        plan_status_str = "N/A"
        if ir.summary and ir.summary.plan_status:
            if hasattr(ir.summary.plan_status, "value"):
                plan_status_str = ir.summary.plan_status.value
            else:
                plan_status_str = str(ir.summary.plan_status)

        action_rec_str = "N/A"
        if ir.summary and ir.summary.action_recommendation:
            if hasattr(ir.summary.action_recommendation, "value"):
                action_rec_str = ir.summary.action_recommendation.value
            elif hasattr(ir.summary.action_recommendation, "name"):
                action_rec_str = ir.summary.action_recommendation.name
            else:
                action_rec_str = str(ir.summary.action_recommendation)

        return {
            "report_id": ir.report_id,
            "evening_report_id": ir.evening_report_id,
            "timestamp": ir.timestamp,
            "summary": {
                "plan_status": plan_status_str,
                "action_recommendation": action_rec_str,
                "total_candidates_monitored": ir.summary.total_candidates_monitored if ir.summary else 0,
                "invalidated_candidates_count": ir.summary.invalidated_candidates_count if ir.summary else 0,
                "significant_market_changes_count": ir.summary.significant_market_changes_count if ir.summary else 0,
                "overall_pcr_shift": ir.summary.overall_pcr_shift if ir.summary else 0.0,
                "overall_vix_shift": ir.summary.overall_vix_shift if ir.summary else 0.0,
            },
            "market_changes": market_changes,
            "candidate_changes": candidate_changes,
            "confidence_changes": confidence_changes,
            "risk_changes": risk_changes,
            "validation_reasons": ir.validation_reasons,
        }

    def render_cli(self) -> str:
        """
        Renders an ASCII text-based representation of the Intraday Monitor Panel.
        """
        data = self.to_dict()
        lines = []
        lines.append("+- INTRADAY ASSISTANT MONITOR -------------------------------------------------+")

        if not data:
            lines.append("| Intraday Monitor: NOT AVAILABLE                                              |")
            lines.append("+------------------------------------------------------------------------------+")
            return "\n".join(lines)

        sum_d = data["summary"]
        lines.append(f"| Plan Validity Status: {sum_d['plan_status']:<18} | Workflow Action: {sum_d['action_recommendation']:<16} |")
        lines.append(f"| Monitored Candidates : {sum_d['total_candidates_monitored']:<3}                | Invalidated Count: {sum_d['invalidated_candidates_count']:<3}             |")
        lines.append(f"| VIX Shift            : {sum_d['overall_vix_shift']:>+5.2f}               | PCR Shift        : {sum_d['overall_pcr_shift']:>+5.2f}              |")
        lines.append("| " + "-"*76 + " |")

        # Market changes table
        if data["market_changes"]:
            lines.append("| Live Market Changes:                                                         |")
            lines.append("| METRIC             | PREV VALUE   | LIVE VALUE   | % CHANGE | SIGNIFICANT    |")
            lines.append("| " + "-"*18 + "+" + "-"*12 + "+" + "-"*12 + "+" + "-"*10 + "+" + "-"*14 + " |")
            for mc in data["market_changes"][:3]:
                pct_str = f"{mc['change_pct']:>+7.2f}%" if mc["change_pct"] is not None else "N/A"
                prev_val = str(mc["previous_value"])[:10]
                live_val = str(mc["current_value"])[:10]
                lines.append(
                    f"| {mc['metric_name']:<18} | {prev_val:>12} | {live_val:>12} | {pct_str:>10} | {str(mc['is_significant']):<14} |"
                )
            lines.append("| " + "-"*76 + " |")

        # Candidate status changes
        if data["candidate_changes"]:
            lines.append("| Live Candidate Status Tracking:                                              |")
            for cc in data["candidate_changes"][:3]:
                lines.append(f"|   * [{cc['status']}] {cc['candidate_id'][:32]:<32} Decision: {cc['previous_decision']} -> {cc['suggested_decision']} |")
                if cc["explanation"]:
                    lines.append(f"|     Reason: {cc['explanation'][:68]:<68} |")
            lines.append("| " + "-"*76 + " |")

        # Validation reasons
        if data["validation_reasons"]:
            lines.append("| Validation Assessments & Alerts:                                             |")
            for vr in data["validation_reasons"][:3]:
                lines.append(f"|   * Alert: {vr[:68]:<68} |")

        lines.append("+------------------------------------------------------------------------------+")
        return "\n".join(lines)
