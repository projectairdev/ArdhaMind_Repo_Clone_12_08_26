from __future__ import annotations

from typing import Optional, List
from src.models import (
    DecisionReport,
    RiskReport,
    ConfidenceReport,
    TradePlan,
    CandidateDecision,
    CandidateExplanation,
    DecisionExplanation,
)


def explain_decisions(
    decision_report: Optional[DecisionReport],
    risk_report: Optional[RiskReport],
    confidence_report: Optional[ConfidenceReport],
    trade_plan: Optional[TradePlan],
) -> DecisionExplanation:
    """
    Explains the decisions made for each candidate in the workstation pipeline.
    Identifies supporting and blocking factors, lot allocations, and overall priority logic.
    """
    if not decision_report:
        return DecisionExplanation(
            overall_action="HOLD",
            highest_priority_candidate_id="NONE",
            portfolio_status_message="No active decision report available.",
            overall_decision_reasoning="No decision data is loaded to generate workstation explanations.",
            candidate_explanations=[],
        )

    cand_exps: List[CandidateExplanation] = []

    # Map reports for easy lookup
    conf_map = {}
    if confidence_report:
        for cc in confidence_report.candidate_confidences:
            conf_map[cc.candidate_id] = cc

    risk_map = {}
    if risk_report:
        for cr in risk_report.candidate_risks:
            risk_map[cr.candidate_id] = cr

    for dec in decision_report.candidate_decisions:
        cid = dec.candidate_id
        sym = dec.tradingsymbol
        strat = dec.strategy_name
        decision_val = dec.decision

        # 1. Decide Decision Reasoning
        sup_reasons = [r.message for r in dec.supporting_evidence] if dec.supporting_evidence else []
        blk_reasons = [r.message for r in dec.blocking_factors] if dec.blocking_factors else []
        warns = [w.message for w in dec.warnings] if dec.warnings else []

        reasons_text = ""
        if decision_val == "BUY":
            reasons_text = f"Recommended for BUY execution. Priority score is {dec.priority_score:.1f} (Rank {dec.execution_priority})."
            if sup_reasons:
                reasons_text += " Supporting factors: " + "; ".join(sup_reasons) + "."
            if warns:
                reasons_text += " Warnings noted: " + "; ".join(warns) + "."
        elif decision_val == "SELL":
            reasons_text = f"Recommended for SELL execution. Priority score is {dec.priority_score:.1f} (Rank {dec.execution_priority})."
            if sup_reasons:
                reasons_text += " Supporting factors: " + "; ".join(sup_reasons) + "."
            if warns:
                reasons_text += " Warnings noted: " + "; ".join(warns) + "."
        elif decision_val == "WATCH":
            reasons_text = f"Marked as WATCH status. Priority score is {dec.priority_score:.1f}."
            if blk_reasons:
                reasons_text += " Prevented from full execution by: " + "; ".join(blk_reasons) + "."
            elif dec.explanation:
                reasons_text += f" Detail: {dec.explanation}."
            else:
                reasons_text += " Kept on watchlist due to low priority slots or medium suitability."
        elif decision_val == "REJECT":
            reasons_text = "REJECTED from immediate execution."
            if blk_reasons:
                reasons_text += " Blocking constraints: " + "; ".join(blk_reasons) + "."
            elif dec.explanation:
                reasons_text += f" Reason: {dec.explanation}."
            else:
                reasons_text += " Fails critical validation filters."
        else:  # "NO TRADE"
            reasons_text = "Marked as NO TRADE."
            if dec.explanation:
                reasons_text += f" Context: {dec.explanation}."
            elif blk_reasons:
                reasons_text += " Factors: " + "; ".join(blk_reasons) + "."
            else:
                reasons_text += " Did not satisfy minimal baseline criteria."

        # 2. Capital and lot allocation reasoning
        lots_text = "No lot allocation determined."
        if risk_map.get(cid):
            crisk = risk_map[cid]
            cap_alloc = crisk.capital_allocation
            if cap_alloc and cap_alloc.allocated_lots > 0:
                lots_text = (
                    f"Allocated {cap_alloc.allocated_lots} lots with capital INR {cap_alloc.allocated_capital:,.2f}. "
                    f"Derived from a risk multiplier of {cap_alloc.risk_multiplier:.2f} and portfolio utilization of {cap_alloc.utilization_pct:.1f}% "
                    f"based on candidate confidence score of {cap_alloc.confidence_score:.1f}%."
                )
            elif crisk.risk_grade == "REJECTED" or not crisk.is_approved:
                lots_text = f"Zero lots allocated because candidate is not approved or risk grade is {crisk.risk_grade}."
        elif dec.allocated_lots > 0:
            lots_text = f"Allocated {dec.allocated_lots} lots with capital INR {dec.allocated_capital:,.2f}."

        # 3. Confidence reasoning
        conf_text = "No confidence assessment available."
        if conf_map.get(cid):
            cconf = conf_map[cid]
            conf_text = f"Confidence score is {cconf.confidence_score:.1f}% (raw: {cconf.raw_score:.1f}%)."
            pos_f = [f.message for f in cconf.positive_factors] if cconf.positive_factors else []
            neg_f = [f.message for f in cconf.negative_factors] if cconf.negative_factors else []
            bonuses = [b.message for b in cconf.bonuses] if cconf.bonuses else []
            penalties = [p.message for p in cconf.penalties] if cconf.penalties else []

            factors_desc = []
            if pos_f:
                factors_desc.append("Positive factors: " + ", ".join(pos_f))
            if neg_f:
                factors_desc.append("Negative factors: " + ", ".join(neg_f))
            if bonuses:
                factors_desc.append("Bonuses applied: " + ", ".join(bonuses))
            if penalties:
                factors_desc.append("Penalties applied: " + ", ".join(penalties))

            if factors_desc:
                conf_text += " " + ". ".join(factors_desc) + "."
        
        # 4. Risk reasoning
        risk_text = "No risk assessment available."
        if risk_map.get(cid):
            crisk = risk_map[cid]
            risk_text = f"Risk grade is {crisk.risk_grade}. Is approved: {crisk.is_approved}."
            cwarns = [w.message for w in crisk.warnings] if crisk.warnings else []
            cconsts = [f"{c.constraint_type} limit: {c.limit_value} current: {c.current_value}" for c in crisk.constraints] if crisk.constraints else []
            if cwarns:
                risk_text += " Risk alerts: " + ", ".join(cwarns) + "."
            if cconsts:
                risk_text += " Portfolio limits: " + ", ".join(cconsts) + "."

        cand_exps.append(
            CandidateExplanation(
                candidate_id=cid,
                tradingsymbol=sym,
                strategy_name=strat,
                decision=decision_val,
                decision_reasoning=reasons_text,
                lots_reasoning=lots_text,
                confidence_reasoning=conf_text,
                risk_reasoning=risk_text,
            )
        )

    # Calculate overall reasoning
    overall_action = decision_report.summary.overall_action
    highest_candidate = decision_report.summary.highest_priority_candidate_id
    status_msg = decision_report.summary.portfolio_status_message
    concls = decision_report.summary.conclusions

    overall_reasoning = f"The trading system recommends an overall action of '{overall_action}'. "
    if highest_candidate != "NONE" and highest_candidate != "":
        overall_reasoning += f"The highest priority candidate is {highest_candidate}. "
    overall_reasoning += f"Portfolio status: {status_msg}."
    if concls:
        overall_reasoning += " Conclusions: " + " ".join(concls)

    return DecisionExplanation(
        overall_action=overall_action,
        highest_priority_candidate_id=highest_candidate,
        portfolio_status_message=status_msg,
        overall_decision_reasoning=overall_reasoning,
        candidate_explanations=cand_exps,
    )
