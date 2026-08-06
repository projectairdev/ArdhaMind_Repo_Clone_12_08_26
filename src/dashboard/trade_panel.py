from __future__ import annotations

from typing import Any, Dict, Optional, List
from src.models import TradePlan, ConfidenceReport, DecisionReport

class TradePanel:
    """
    Stateless Trade Panel.
    Integrates TradePlan, ConfidenceReport, and DecisionReport to showcase the
    pipeline from generation, to confidence scoring, to final decision & capital allocation.
    """

    def __init__(
        self,
        trade_plan: Optional[TradePlan] = None,
        confidence_report: Optional[ConfidenceReport] = None,
        decision_report: Optional[DecisionReport] = None,
    ) -> None:
        self.trade_plan = trade_plan
        self.confidence_report = confidence_report
        self.decision_report = decision_report

    def to_dict(self) -> Dict[str, Any]:
        """
        Extracts structured data correlating TradePlan, Confidence, and Decisions.
        """
        # Dictionary of candidates by ID for correlation
        correlated: Dict[str, Dict[str, Any]] = {}

        # 1. Start with TradePlan candidates
        if self.trade_plan and self.trade_plan.accepted_candidates:
            for cand in self.trade_plan.accepted_candidates:
                correlated[cand.candidate_id] = {
                    "candidate_id": cand.candidate_id,
                    "tradingsymbol": cand.tradingsymbol,
                    "strategy_name": cand.strategy_name,
                    "strike": cand.strike,
                    "instrument_type": cand.instrument_type,
                    "expiry": cand.expiry,
                    "ranking_score": cand.ranking_score,
                    "rank": cand.rank,
                    "confidence_score": None,
                    "decision": "WATCH",
                    "priority_score": None,
                    "allocated_capital": 0.0,
                    "allocated_lots": 0,
                    "explanation": "",
                }

        # 2. Add Confidence scores
        if self.confidence_report and self.confidence_report.candidate_confidences:
            for conf in self.confidence_report.candidate_confidences:
                if conf.candidate_id not in correlated:
                    correlated[conf.candidate_id] = {
                        "candidate_id": conf.candidate_id,
                        "tradingsymbol": conf.tradingsymbol,
                        "strategy_name": conf.strategy_name,
                        "strike": 0.0,
                        "instrument_type": "",
                        "expiry": "",
                        "ranking_score": 0.0,
                        "rank": 99,
                        "confidence_score": conf.confidence_score,
                        "decision": "WATCH",
                        "priority_score": None,
                        "allocated_capital": 0.0,
                        "allocated_lots": 0,
                        "explanation": "",
                    }
                else:
                    correlated[conf.candidate_id]["confidence_score"] = conf.confidence_score

        # 3. Add Decision & capital details
        if self.decision_report and self.decision_report.candidate_decisions:
            for dec in self.decision_report.candidate_decisions:
                if dec.candidate_id not in correlated:
                    correlated[dec.candidate_id] = {
                        "candidate_id": dec.candidate_id,
                        "tradingsymbol": dec.tradingsymbol,
                        "strategy_name": dec.strategy_name,
                        "strike": 0.0,
                        "instrument_type": "",
                        "expiry": "",
                        "ranking_score": 0.0,
                        "rank": 99,
                        "confidence_score": None,
                        "decision": dec.decision,
                        "priority_score": dec.priority_score,
                        "allocated_capital": getattr(dec, "allocated_capital", 0.0),
                        "allocated_lots": getattr(dec, "allocated_lots", 0),
                        "explanation": getattr(dec, "explanation", ""),
                    }
                else:
                    correlated[dec.candidate_id]["decision"] = dec.decision
                    correlated[dec.candidate_id]["priority_score"] = dec.priority_score
                    correlated[dec.candidate_id]["allocated_capital"] = getattr(dec, "allocated_capital", 0.0)
                    correlated[dec.candidate_id]["allocated_lots"] = getattr(dec, "allocated_lots", 0)
                    correlated[dec.candidate_id]["explanation"] = getattr(dec, "explanation", "")

        # Sort correlated candidates by ranking_score descending or execution priority
        candidate_list = list(correlated.values())
        candidate_list.sort(key=lambda x: x.get("ranking_score") or 0.0, reverse=True)

        top_trade = None
        if self.trade_plan and self.trade_plan.summary and self.trade_plan.summary.best_candidate_id:
            best_id = self.trade_plan.summary.best_candidate_id
            if best_id in correlated:
                top_trade = correlated[best_id]
        if not top_trade and candidate_list:
            top_trade = candidate_list[0]

        plan_stats = {}
        if self.trade_plan and self.trade_plan.statistics:
            s = self.trade_plan.statistics
            plan_stats = {
                "generated": s.total_candidates_generated,
                "accepted": s.total_candidates_accepted,
                "rejected": s.total_candidates_rejected,
            }

        conf_stats = {}
        if self.confidence_report and self.confidence_report.summary:
            cs = self.confidence_report.summary
            conf_stats = {
                "avg_confidence": cs.average_confidence,
                "highest_id": cs.highest_confidence_candidate_id,
            }

        decision_stats = {}
        if self.decision_report and self.decision_report.stats:
            ds = self.decision_report.stats
            decision_stats = {
                "buy_count": ds.buy_count,
                "sell_count": ds.sell_count,
                "watch_count": ds.watch_count,
                "reject_count": ds.reject_count,
                "allocated_capital": ds.total_allocated_capital,
            }

        return {
            "top_trade": top_trade,
            "candidates": candidate_list,
            "statistics": {
                "planning": plan_stats,
                "confidence": conf_stats,
                "decision": decision_stats,
            },
            "overall_decision_summary": self.decision_report.summary.overall_action if self.decision_report and self.decision_report.summary else None,
            "overall_decision_message": self.decision_report.summary.portfolio_status_message if self.decision_report and self.decision_report.summary else None,
        }

    def render_cli(self) -> str:
        """
        Renders a cohesive CLI terminal visualization for trade pipeline.
        """
        data = self.to_dict()
        lines = []
        lines.append("+- TRADE PLAN, CONFIDENCE & DECISION PIPELINE ---------------------------------+")

        # Top Trade
        if data["top_trade"]:
            tt = data["top_trade"]
            lines.append(f"| TOP TRADE RECOMMENDATION: {tt['candidate_id']:<50} |")
            lines.append(f"|   Symbol: {tt['tradingsymbol']:<15} | Strategy: {tt['strategy_name']:<15} | Expiry: {tt['expiry']:<10} |")
            lines.append(f"|   Rank  : {tt['rank']:<15} | Rank Score: {tt['ranking_score'] or 0.0:<12.1f} | Decision: {tt['decision']:<10} |")
            conf_str = f"{tt['confidence_score']:.1f}%" if tt['confidence_score'] is not None else "N/A"
            prio_str = f"{tt['priority_score']:.1f}" if tt['priority_score'] is not None else "N/A"
            lines.append(f"|   Confidence: {conf_str:<11} | Priority  : {prio_str:<14} | Lots/Cap: {tt['allocated_lots']} Lots / INR {tt['allocated_capital']:.2f} |")
            if tt["explanation"]:
                lines.append(f"|   Rationale: {tt['explanation'][:65]:<66} |")
        else:
            lines.append("| TOP TRADE RECOMMENDATION: NONE                                               |")

        lines.append("| " + "="*76 + " |")

        # Statistics Summary
        stats = data["statistics"]
        plan_str = f"Plan Gen/Acc/Rej: {stats['planning'].get('generated', 0)}/{stats['planning'].get('accepted', 0)}/{stats['planning'].get('rejected', 0)}" if stats["planning"] else "Planning: N/A"
        conf_str = f"Avg Conf: {stats['confidence'].get('avg_confidence', 0.0):.1f}%" if stats["confidence"] else "Confidence: N/A"
        dec_str = f"Buy/Sell/Watch: {stats['decision'].get('buy_count', 0)}/{stats['decision'].get('sell_count', 0)}/{stats['decision'].get('watch_count', 0)}" if stats["decision"] else "Decision: N/A"
        lines.append(f"| {plan_str:<25} | {conf_str:<18} | {dec_str:<27} |")
        if stats["decision"] and stats["decision"].get("allocated_capital"):
            lines.append(f"| Total Allocated Capital: INR {stats['decision']['allocated_capital']:,.2f}                                      |")

        lines.append("| " + "-"*76 + " |")

        # Candidate details table
        lines.append("| CANDIDATE ID                       | STRATEGY | CONF % | DECISION | CAPITAL ALLOC  |")
        lines.append("| " + "-"*34 + "+" + "-"*10 + "+" + "-"*8 + "+" + "-"*10 + "+" + "-"*14 + " |")
        
        for c in data["candidates"][:5]:  # show top 5
            c_conf = f"{c['confidence_score']:.1f}%" if c['confidence_score'] is not None else "N/A"
            cap_alloc = f"INR {c['allocated_capital']:,.1f}" if c['allocated_capital'] > 0 else "0.0"
            lines.append(
                f"| {c['candidate_id'][:34]:<34} | {c['strategy_name'][:10]:<10} | {c_conf:>6} | {c['decision']:<8} | {cap_alloc:>14} |"
            )

        if len(data["candidates"]) > 5:
            lines.append(f"| ... and {len(data['candidates']) - 5} other candidates                                                    |")

        lines.append("+------------------------------------------------------------------------------+")
        return "\n".join(lines)
