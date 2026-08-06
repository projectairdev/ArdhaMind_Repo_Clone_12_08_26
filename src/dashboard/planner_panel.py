from __future__ import annotations

from typing import Any, Dict, Optional
from src.models import EveningReport

class PlannerPanel:
    """
    Stateless Planner Panel.
    Displays EveningReport contents including tomorrow's outlook, candidates, watchlist, and checklist.
    """

    def __init__(self, evening_report: Optional[EveningReport] = None) -> None:
        self.evening_report = evening_report

    def to_dict(self) -> Dict[str, Any]:
        """
        Extracts structured presentation data for tomorrow's plan.
        """
        if not self.evening_report:
            return {}

        er = self.evening_report

        candidates = []
        for c in er.top_candidates:
            candidates.append({
                "candidate_id": c.candidate_id,
                "tradingsymbol": c.tradingsymbol,
                "strategy_name": c.strategy_name,
                "decision": c.decision,
                "confidence_score": c.confidence_score,
                "priority_score": c.priority_score,
                "allocated_capital": c.allocated_capital,
                "allocated_lots": c.allocated_lots,
                "strike": c.strike,
                "instrument_type": c.instrument_type,
                "expiry": c.expiry,
            })

        strategies = []
        for s in er.recommended_strategies:
            strategies.append({
                "strategy_name": s.strategy_name,
                "suitability_score": s.suitability_score,
                "suitability_level": s.suitability_level,
                "rationale": s.rationale,
            })

        checklist_items = list(er.checklist.checklist_items) if er.checklist else []

        return {
            "report_id": er.report_id,
            "timestamp": er.timestamp,
            "tomorrow_outlook": {
                "directional_bias": er.tomorrow_outlook.directional_bias,
                "outlook_classification": er.tomorrow_outlook.outlook_classification,
                "opportunity_strength": er.tomorrow_outlook.opportunity_strength,
                "key_support_levels": er.tomorrow_outlook.key_support_levels,
                "key_resistance_levels": er.tomorrow_outlook.key_resistance_levels,
                "description": er.tomorrow_outlook.description,
            } if er.tomorrow_outlook else None,
            "market_summary": {
                "spot_price": er.market_summary.spot_price,
                "vix_price": er.market_summary.vix_price,
                "regime": er.market_summary.regime,
                "trend_direction": er.market_summary.trend_direction,
                "market_score": er.market_summary.market_score,
                "market_grade": er.market_summary.market_grade,
                "session_type": er.market_summary.session_type,
            } if er.market_summary else None,
            "summary": {
                "best_candidate_id": er.summary.best_candidate_id,
                "best_strategy": er.summary.best_strategy,
                "total_accepted_candidates": er.summary.total_accepted_candidates,
                "total_rejected_candidates": er.summary.total_rejected_candidates,
                "action_type": er.summary.action_type,
            } if er.summary else None,
            "top_candidates": candidates,
            "recommended_strategies": strategies,
            "risk_watchlist": {
                "warnings": er.risk_watchlist.warnings,
                "portfolio_warnings": er.risk_watchlist.portfolio_warnings,
                "max_capital_limit": er.risk_watchlist.max_capital_limit,
                "allocated_capital": er.risk_watchlist.allocated_capital,
                "portfolio_utilization_pct": er.risk_watchlist.portfolio_utilization_pct,
                "risk_grade": er.risk_watchlist.risk_grade,
            } if er.risk_watchlist else None,
            "event_watchlist": {
                "events": er.event_watchlist.events,
                "expiry_days_remaining": er.event_watchlist.expiry_days_remaining,
                "expiry_type": er.event_watchlist.expiry_type,
            } if er.event_watchlist else None,
            "checklist": checklist_items,
        }

    def render_cli(self) -> str:
        """
        Renders an ASCII text-based representation of the Planner Panel.
        """
        data = self.to_dict()
        lines = []
        lines.append("+- EVENING PLANNER & TOMORROW OUTLOOK -----------------------------------------+")

        if not data:
            lines.append("| Evening Plan: NOT AVAILABLE                                                  |")
            lines.append("+------------------------------------------------------------------------------+")
            return "\n".join(lines)

        # Outlook Section
        out = data["tomorrow_outlook"]
        if out:
            lines.append(f"| Tomorrow Bias: {out['directional_bias']:<14} | Strength: {out['opportunity_strength']:>5.1f}% | Classification: {out['outlook_classification']:<11} |")
            lines.append(f"| S/R Levels   : Supp: {str(out['key_support_levels'][:3]):<18} | Res: {str(out['key_resistance_levels'][:3])} |")
            lines.append(f"| Outlook Desc : {out['description'][:70]:<70} |")
        else:
            lines.append("| Tomorrow Outlook: N/A                                                        |")

        lines.append("| " + "-"*76 + " |")

        # Top Candidates
        if data["top_candidates"]:
            lines.append("| Recommended Trade Candidates:                                                |")
            lines.append("| CANDIDATE ID                       | STRATEGY   | DECISION | CONF % | LOTS |")
            lines.append("| " + "-"*34 + "+" + "-"*12 + "+" + "-"*10 + "+" + "-"*8 + "+" + "-"*6 + " |")
            for tc in data["top_candidates"][:3]:
                lines.append(
                    f"| {tc['candidate_id'][:34]:<34} | {tc['strategy_name'][:12]:<12} | {tc['decision']:<10} | {tc['confidence_score']:>5.1f}% | {tc['allocated_lots']:>4} |"
                )
            if len(data["top_candidates"]) > 3:
                lines.append(f"| ... and {len(data['top_candidates']) - 3} other candidate recommendations                                  |")
        else:
            lines.append("| Candidates: NONE APPROVED                                                    |")

        lines.append("| " + "-"*76 + " |")

        # Checklist and Event/Risk Watches
        checklist = data["checklist"]
        chk_str = ", ".join(checklist[:5]) if checklist else "None"
        lines.append(f"| Checklist Items: {chk_str[:60]:<60} |")

        risk_w = data["risk_watchlist"]
        if risk_w and (risk_w["warnings"] or risk_w["portfolio_warnings"]):
            lines.append("| " + "-"*76 + " |")
            lines.append("| Risk/Event Warnings:                                                         |")
            for w in (risk_w["warnings"] + risk_w["portfolio_warnings"])[:2]:
                lines.append(f"|   * Risk Alert: {w[:68]:<68} |")

        lines.append("+------------------------------------------------------------------------------+")
        return "\n".join(lines)
