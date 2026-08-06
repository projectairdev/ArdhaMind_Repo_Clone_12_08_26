from __future__ import annotations

from typing import List, Optional, Dict
from src.models import (
    EveningReport,
    RiskReport,
    DecisionReport,
    RiskChange,
)


def get_risk_score(grade: str) -> int:
    g = grade.upper()
    if "LOW" in g or "CONSERVATIVE" in g:
        return 1
    if "MODERATE" in g or "MEDIUM" in g:
        return 2
    if "HIGH" in g or "AGGRESSIVE" in g:
        return 3
    if "CRITICAL" in g:
        return 4
    return 1


def monitor_risk(
    evening_report: EveningReport,
    current_risk_report: Optional[RiskReport] = None,
    current_decision_report: Optional[DecisionReport] = None,
) -> List[RiskChange]:
    changes = []
    if not evening_report.top_candidates:
        return changes

    # Parse previous warnings on candidates
    prev_warnings_map: Dict[str, List[str]] = {}
    for pw in evening_report.risk_watchlist.warnings:
        # e.g., "[CANDIDATE_ID] message"
        if "]" in pw:
            parts = pw.split("]", 1)
            cand_id = parts[0].replace("[", "").strip()
            msg = parts[1].strip()
            prev_warnings_map.setdefault(cand_id, []).append(msg)

    # Parse current risk report
    current_risk_map = {}
    if current_risk_report and current_risk_report.candidate_risks:
        current_risk_map = {
            r.candidate_id: r for r in current_risk_report.candidate_risks
        }

    # Parse current decision report warnings
    current_dec_map = {}
    if current_decision_report and current_decision_report.candidate_decisions:
        current_dec_map = {
            d.candidate_id: d for d in current_decision_report.candidate_decisions
        }

    for cand in evening_report.top_candidates:
        cand_id = cand.candidate_id
        prev_grade = "LOW_RISK"  # default if not found

        curr_risk_obj = current_risk_map.get(cand_id)
        curr_dec_obj = current_dec_map.get(cand_id)

        # Retrieve previous grade if possible by matching cand_id in current or default
        if curr_risk_obj:
            curr_grade = curr_risk_obj.risk_grade
        else:
            curr_grade = "LOW_RISK"

        # Determine if risk increased
        prev_score = get_risk_score(prev_grade)
        curr_score = get_risk_score(curr_grade)
        is_risk_increased = curr_score > prev_score

        # Find new warnings
        new_warnings = []
        prev_msgs = prev_warnings_map.get(cand_id, [])

        if curr_risk_obj and curr_risk_obj.warnings:
            for w in curr_risk_obj.warnings:
                # Check if this warning message was already registered
                is_new = True
                for pm in prev_msgs:
                    if w.message in pm or pm in w.message:
                        is_new = False
                        break
                if is_new:
                    new_warnings.append(f"Risk Warning: {w.message} ({w.warning_type})")

        if curr_dec_obj and curr_dec_obj.warnings:
            for w in curr_dec_obj.warnings:
                is_new = True
                for pm in prev_msgs:
                    if w.message in pm or pm in w.message:
                        is_new = False
                        break
                if is_new:
                    new_warnings.append(f"Decision Warning: {w.message} ({w.warning_type})")

        changes.append(
            RiskChange(
                candidate_id=cand_id,
                previous_risk_grade=prev_grade,
                current_risk_grade=curr_grade,
                is_risk_increased=is_risk_increased,
                triggered_new_warnings=new_warnings,
            )
        )

    return changes
