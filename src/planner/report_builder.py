from __future__ import annotations

from datetime import datetime
from src.models.decision_report import DecisionReport
from src.models.risk_report import RiskReport
from src.models.confidence_report import ConfidenceReport
from src.models.trade_plan import TradePlan
from src.models.strategy_evaluation import StrategyEvaluation
from src.models.opportunity_context import OpportunityContext
from src.models.market_score import MarketScore
from src.models.optimization_report import OptimizationReport
from src.models.market_context import MarketContext
from src.models.evening_report import EveningReport, ReportSummary

from src.planner.market_summary import compile_market_summary, compile_tomorrow_outlook
from src.planner.strategy_summary import compile_strategy_summary
from src.planner.candidate_summary import compile_recommended_candidates, compile_rejected_candidates
from src.planner.risk_summary import compile_risk_watchlist
from src.planner.event_summary import compile_event_watchlist
from src.planner.checklist import generate_checklist


class EveningPlanner:
    @staticmethod
    def generate_report(
        decision_report: DecisionReport,
        risk_report: RiskReport,
        confidence_report: ConfidenceReport,
        trade_plan: TradePlan,
        strategy_evaluation: StrategyEvaluation,
        opportunity_context: OpportunityContext,
        market_score: MarketScore,
        optimization_report: OptimizationReport | None = None,
        market_context: MarketContext | None = None,
    ) -> EveningReport:
        """
        Main orchestration function to consume the completed trading engine outputs
        and assemble them into a cohesive, immutable EveningReport.
        """
        # Build each section using its specialized component
        m_summary = compile_market_summary(
            market_score, opportunity_context, market_context
        )
        outlook = compile_tomorrow_outlook(opportunity_context, market_context)
        strategies = compile_strategy_summary(strategy_evaluation)

        recommended = compile_recommended_candidates(
            decision_report, confidence_report, trade_plan
        )
        rejected = compile_rejected_candidates(trade_plan, decision_report)

        risk_wl = compile_risk_watchlist(risk_report, decision_report)
        event_wl = compile_event_watchlist(
            market_score, opportunity_context, market_context
        )

        best_strategy = (
            strategy_evaluation.overall_best_strategy
            if strategy_evaluation
            else "UNKNOWN"
        )
        checklist = generate_checklist(
            opportunity_context,
            market_context,
            best_strategy=best_strategy,
            has_portfolio_warnings=len(risk_wl.portfolio_warnings) > 0,
        )

        # Extract optimization notes if optimization report is provided
        opt_notes = []
        if optimization_report:
            if hasattr(optimization_report, "recommendations") and optimization_report.recommendations:
                for rec in optimization_report.recommendations:
                    opt_notes.append(
                        f"[{rec.category}] {rec.title}: {rec.description} (Recommended: {rec.recommended_value})"
                    )
            if hasattr(optimization_report, "strategy_optimizations") and optimization_report.strategy_optimizations:
                for st_opt in optimization_report.strategy_optimizations:
                    opt_notes.append(
                        f"[STRATEGY] {st_opt.strategy_name}: {st_opt.recommended_action} - {st_opt.rationale}"
                    )
            if hasattr(optimization_report, "threshold_recommendations") and optimization_report.threshold_recommendations:
                for th_opt in optimization_report.threshold_recommendations:
                    opt_notes.append(
                        f"[THRESHOLD] {th_opt.parameter_name}: {th_opt.direction} to {th_opt.suggested_value} - {th_opt.impact}"
                    )
            if hasattr(optimization_report, "weight_recommendations") and optimization_report.weight_recommendations:
                for wt_opt in optimization_report.weight_recommendations:
                    opt_notes.append(
                        f"[WEIGHT] {wt_opt.strategy_or_factor}: suggested weight {wt_opt.suggested_weight} (current: {wt_opt.current_weight})"
                    )

        # Report ID and summary compilation
        report_id = "EVENING_REPORT_PLAN"
        if decision_report and decision_report.report_id:
            report_id = (
                f"EVENING_REPORT_{decision_report.report_id.split('_')[-1]}"
                if "_" in decision_report.report_id
                else f"EVENING_REPORT_{decision_report.report_id}"
            )

        best_candidate_id = (
            decision_report.summary.highest_priority_candidate_id
            if decision_report and decision_report.summary
            else "NONE"
        )
        action_type = (
            decision_report.summary.overall_action
            if decision_report and decision_report.summary
            else "HOLD"
        )

        total_accepted = (
            len(trade_plan.accepted_candidates)
            if trade_plan and trade_plan.accepted_candidates
            else 0
        )
        total_rejected = (
            len(trade_plan.rejected_candidates)
            if trade_plan and trade_plan.rejected_candidates
            else 0
        )

        summary = ReportSummary(
            best_candidate_id=best_candidate_id,
            best_strategy=best_strategy,
            total_accepted_candidates=total_accepted,
            total_rejected_candidates=total_rejected,
            action_type=action_type,
        )

        timestamp = (
            decision_report.timestamp
            if decision_report and decision_report.timestamp
            else datetime.now().isoformat()
        )

        return EveningReport(
            report_id=report_id,
            market_summary=m_summary,
            tomorrow_outlook=outlook,
            recommended_strategies=strategies,
            top_candidates=recommended,
            rejected_candidates=rejected,
            risk_watchlist=risk_wl,
            event_watchlist=event_wl,
            checklist=checklist,
            summary=summary,
            timestamp=timestamp,
            optimization_notes=opt_notes,
        )


def format_evening_report_cli(report: EveningReport) -> str:
    """
    Format an EveningReport object into a highly polished, clean CLI terminal report.
    """
    lines = []
    lines.append("=" * 80)
    lines.append(f"                    EVENING PLANNER REPORT: {report.report_id}")
    lines.append(f"                    Timestamp: {report.timestamp}")
    lines.append("=" * 80)

    # Market Summary
    ms = report.market_summary
    lines.append("\n[ MARKET SUMMARY ]")
    lines.append("-" * 40)
    lines.append(f"  Spot Price:     {ms.spot_price:,.2f}")
    lines.append(f"  India VIX:      {ms.vix_price:,.2f}")
    lines.append(f"  Market Regime:  {ms.regime}")
    lines.append(f"  Trend:          {ms.trend_direction}")
    lines.append(
        f"  Market Score:   {ms.market_score:.2f} ({ms.market_grade} - {ms.session_type})"
    )

    # Tomorrow Outlook
    out = report.tomorrow_outlook
    lines.append("\n[ TOMORROW OUTLOOK ]")
    lines.append("-" * 40)
    lines.append(f"  Directional Bias:      {out.directional_bias}")
    lines.append(f"  Outlook Classification: {out.outlook_classification}")
    lines.append(f"  Opportunity Strength:   {out.opportunity_strength:.2f}%")
    if out.key_support_levels:
        lines.append(
            f"  Key Support Levels:     {', '.join(map(str, out.key_support_levels))}"
        )
    if out.key_resistance_levels:
        lines.append(
            f"  Key Resistance Levels:  {', '.join(map(str, out.key_resistance_levels))}"
        )
    if out.description:
        lines.append(f"  Description:            {out.description}")

    # Recommended Strategies
    lines.append("\n[ RECOMMENDED STRATEGIES ]")
    lines.append("-" * 40)
    if not report.recommended_strategies:
        lines.append("  No recommended strategies with MEDIUM/HIGH suitability.")
    else:
        for strat in report.recommended_strategies:
            lines.append(
                f"  * {strat.strategy_name} (Suitability Score: {strat.suitability_score:.2f}, Level: {strat.suitability_level})"
            )
            for rat in strat.rationale:
                lines.append(f"    - {rat}")

    # Top Candidates
    lines.append("\n[ TOP CANDIDATES ]")
    lines.append("-" * 40)
    if not report.top_candidates:
        lines.append("  No active recommended candidates.")
    else:
        header = f"  {'Candidate ID':<30} | {'Decision':<8} | {'Conf':<6} | {'Priority':<8} | {'Capital':<10}"
        lines.append(header)
        lines.append("  " + "-" * 70)
        for c in report.top_candidates:
            row = f"  {c.candidate_id:<30} | {c.decision:<8} | {c.confidence_score:5.1f} | {c.priority_score:8.2f} | Rs.{c.allocated_capital:,.2f}"
            lines.append(row)
            if c.strike or c.instrument_type:
                lines.append(
                    f"    Details: Strike: {c.strike}, Type: {c.instrument_type}, Expiry: {c.expiry}, Lots: {c.allocated_lots}"
                )

    # Rejected Candidates
    lines.append("\n[ REJECTED CANDIDATES ]")
    lines.append("-" * 40)
    if not report.rejected_candidates:
        lines.append("  No rejected candidates.")
    else:
        for rj in report.rejected_candidates[:10]:  # Limit to 10 for readability
            lines.append(
                f"  - {rj.strategy_name} @ {rj.tradingsymbol}: {rj.message} ({rj.reason_type})"
            )
        if len(report.rejected_candidates) > 10:
            lines.append(
                f"  ... and {len(report.rejected_candidates) - 10} more rejected candidates."
            )

    # Risk Watchlist
    lines.append("\n[ RISK WATCHLIST ]")
    lines.append("-" * 40)
    rw = report.risk_watchlist
    lines.append(f"  Portfolio Risk Grade:   {rw.risk_grade}")
    lines.append(
        f"  Allocated Capital:      Rs.{rw.allocated_capital:,.2f} / Rs.{rw.max_capital_limit:,.2f} ({rw.portfolio_utilization_pct:.2f}%)"
    )

    if rw.portfolio_warnings:
        lines.append("  Portfolio Warnings:")
        for pw in rw.portfolio_warnings:
            lines.append(f"    [!] {pw}")
    if rw.warnings:
        lines.append("  Candidate Warnings:")
        for cw in rw.warnings[:5]:  # Limit to 5
            lines.append(f"    [!] {cw}")
        if len(rw.warnings) > 5:
            lines.append(
                f"    ... and {len(rw.warnings) - 5} more candidate warnings."
            )

    # Event Watchlist
    if report.event_watchlist and report.event_watchlist.events:
        lines.append("\n[ EVENT WATCHLIST ]")
        lines.append("-" * 40)
        for ev in report.event_watchlist.events:
            lines.append(f"  * {ev}")

    # Morning Checklist
    lines.append("\n[ MORNING CHECKLIST ]")
    lines.append("-" * 40)
    if report.checklist and report.checklist.checklist_items:
        for item in report.checklist.checklist_items:
            lines.append(f"  [ ] {item}")
    else:
        lines.append("  No checklist generated.")

    # Optimization Notes
    if report.optimization_notes:
        lines.append("\n[ OPTIMIZATION NOTES ]")
        lines.append("-" * 40)
        for note in report.optimization_notes:
            lines.append(f"  * {note}")

    # Summary
    lines.append("\n[ SUMMARY ]")
    lines.append("-" * 40)
    s = report.summary
    lines.append(f"  Best Strategy:              {s.best_strategy}")
    lines.append(f"  Highest Priority Candidate: {s.best_candidate_id}")
    lines.append(f"  Overall Session Action:     {s.action_type}")
    lines.append(
        f"  Total Candidates Evaluated: {s.total_accepted_candidates + s.total_rejected_candidates} (Accepted: {s.total_accepted_candidates}, Rejected: {s.total_rejected_candidates})"
    )

    lines.append("=" * 80)
    return "\n".join(lines)
