from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from src.models import (
    EveningReport,
    MarketContext,
    OptionContext,
    MarketScore,
    OpportunityContext,
    ConfidenceReport,
    RiskReport,
    DecisionReport,
    IntradayReport,
    IntradaySummary,
    PlanStatus,
    ActionRecommendation,
)

from src.intraday.market_comparator import compare_market
from src.intraday.candidate_monitor import monitor_candidates
from src.intraday.confidence_monitor import monitor_confidence
from src.intraday.risk_monitor import monitor_risk
from src.intraday.plan_validator import validate_plan


class IntradayAssistant:
    @staticmethod
    def generate_report(
        evening_report: EveningReport,
        current_market_context: MarketContext,
        current_option_context: Optional[OptionContext] = None,
        current_market_score: Optional[MarketScore] = None,
        current_opportunity_context: Optional[OpportunityContext] = None,
        current_confidence_report: Optional[ConfidenceReport] = None,
        current_risk_report: Optional[RiskReport] = None,
        current_decision_report: Optional[DecisionReport] = None,
        previous_option_context: Optional[OptionContext] = None,
    ) -> IntradayReport:
        """
        Orchestrates real-time comparison, monitoring, risk appraisal, and plan validation.
        Produces a single unified, immutable IntradayReport.
        """
        # 1. Compare Market Contexts
        market_changes = compare_market(
            evening_report=evening_report,
            current_market_context=current_market_context,
            current_option_context=current_option_context,
            current_market_score=current_market_score,
            previous_option_context=previous_option_context,
        )

        # 2. Monitor Candidates
        candidate_changes = monitor_candidates(
            evening_report=evening_report,
            current_confidence_report=current_confidence_report,
            current_risk_report=current_risk_report,
            current_decision_report=current_decision_report,
        )

        # 3. Monitor Confidence Changes
        confidence_changes = monitor_confidence(
            evening_report=evening_report,
            current_confidence_report=current_confidence_report,
        )

        # 4. Monitor Risk Changes
        risk_changes = monitor_risk(
            evening_report=evening_report,
            current_risk_report=current_risk_report,
            current_decision_report=current_decision_report,
        )

        # 5. Validate the overall plan
        plan_status, validation_reasons = validate_plan(
            market_changes=market_changes,
            candidate_changes=candidate_changes,
        )

        # 6. Action Recommendation
        if plan_status == PlanStatus.INVALIDATED:
            action_rec = ActionRecommendation.CANCEL
        elif plan_status == PlanStatus.NEEDS_REVIEW:
            action_rec = ActionRecommendation.REVIEW
        else:
            # Let's say if there are any warnings, wait, otherwise proceed
            has_warnings = any(
                rc.triggered_new_warnings for rc in risk_changes
            ) or any(
                mc.metric_name in ("SUPPORT_BREACH", "RESISTANCE_BREACH") for mc in market_changes
            )
            action_rec = ActionRecommendation.WAIT if has_warnings else ActionRecommendation.PROCEED

        # 7. Compile Intraday Summary Metrics
        sig_market_changes = sum(1 for mc in market_changes if mc.is_significant)
        invalidated_count = sum(1 for cc in candidate_changes if cc.status.name == "INVALIDATED")

        prev_pcr = 1.0
        curr_pcr = 1.0
        if current_option_context:
            curr_pcr = current_option_context.pcr
            if previous_option_context:
                prev_pcr = previous_option_context.pcr

        prev_vix = evening_report.market_summary.vix_price
        curr_vix = current_market_context.india_vix if current_market_context.india_vix is not None else 0.0

        pcr_shift = curr_pcr - prev_pcr
        vix_shift = curr_vix - prev_vix

        summary = IntradaySummary(
            plan_status=plan_status,
            action_recommendation=action_rec,
            total_candidates_monitored=len(candidate_changes),
            invalidated_candidates_count=invalidated_count,
            significant_market_changes_count=sig_market_changes,
            overall_pcr_shift=pcr_shift,
            overall_vix_shift=vix_shift,
        )

        report_id = f"INTRADAY_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return IntradayReport(
            report_id=report_id,
            evening_report_id=evening_report.report_id,
            summary=summary,
            market_changes=market_changes,
            candidate_changes=candidate_changes,
            confidence_changes=confidence_changes,
            risk_changes=risk_changes,
            validation_reasons=validation_reasons,
            timestamp=datetime.now().isoformat(),
        )


def format_intraday_report_cli(report: IntradayReport) -> str:
    """
    Produce a concise terminal report for the Intraday Assistant.
    """
    lines = []
    lines.append("=" * 80)
    lines.append(f"               INTRADAY ASSISTANT MONITOR: {report.report_id}")
    lines.append(f"               Associated Plan:            {report.evening_report_id}")
    lines.append(f"               Timestamp:                  {report.timestamp}")
    lines.append("=" * 80)

    # Plan Status and Action Recommendation
    s = report.summary
    status_emoji = "✅" if s.plan_status == PlanStatus.VALID else ("⚠️" if s.plan_status == PlanStatus.NEEDS_REVIEW else "❌")
    action_color = s.action_recommendation.name

    lines.append("\n[ PLAN STATUS & ACTION RECOMMENDATION ]")
    lines.append("-" * 40)
    lines.append(f"  Plan Validity Status:  {status_emoji} {s.plan_status.value}")
    lines.append(f"  Workflow Action:       👉 {action_color} 👈")
    lines.append(f"  Overall PCR Shift:     {s.overall_pcr_shift:+.2f}")
    lines.append(f"  Overall India VIX Shift: {s.overall_vix_shift:+.2f}")

    # Validation Reasons
    if report.validation_reasons:
        lines.append("\n  Key Validation Details:")
        for r in report.validation_reasons:
            lines.append(f"    - {r}")

    # Market Changes
    lines.append("\n[ MARKET CHANGES ]")
    lines.append("-" * 40)
    sig_changes = [m for m in report.market_changes if m.is_significant]
    if sig_changes:
        for mc in sig_changes:
            lines.append(f"  [SIGNIFICANT] {mc.metric_name}: {mc.message}")
    else:
        lines.append("  No significant or critical market parameter changes detected.")

    other_changes = [m for m in report.market_changes if not m.is_significant]
    if other_changes:
        lines.append("\n  Minor Market Metrics:")
        for mc in other_changes:
            lines.append(f"    * {mc.metric_name}: {mc.message}")

    # Candidate Status Changes
    lines.append("\n[ CANDIDATE CHANGES ]")
    lines.append("-" * 40)
    if not report.candidate_changes:
        lines.append("  No monitored trade candidates found.")
    else:
        for cc in report.candidate_changes:
            lines.append(
                f"  * {cc.candidate_id} ({cc.tradingsymbol}): {cc.status.value}"
            )
            lines.append(f"    Explanation:      {cc.explanation}")
            lines.append(f"    Decision:         {cc.previous_decision} ➔ {cc.suggested_decision}")

    # Confidence Changes
    lines.append("\n[ CONFIDENCE CHANGES ]")
    lines.append("-" * 40)
    if not report.confidence_changes:
        lines.append("  No confidence tracking data.")
    else:
        for c_chg in report.confidence_changes:
            lines.append(
                f"  * {c_chg.candidate_id}: {c_chg.previous_confidence:.1f}% ➔ {c_chg.current_confidence:.1f}% ({c_chg.change_amt:+.1f} points)"
            )
            if c_chg.explanation:
                lines.append(f"    Detail: {c_chg.explanation}")

    # Risk Changes
    lines.append("\n[ RISK CHANGES ]")
    lines.append("-" * 40)
    if not report.risk_changes:
        lines.append("  No risk changes detected.")
    else:
        for r_chg in report.risk_changes:
            lines.append(
                f"  * {r_chg.candidate_id}: Risk Grade {r_chg.previous_risk_grade} ➔ {r_chg.current_risk_grade} (Increased: {r_chg.is_risk_increased})"
            )
            if r_chg.triggered_new_warnings:
                lines.append("    Triggered Warnings:")
                for w in r_chg.triggered_new_warnings:
                    lines.append(f"      [!] {w}")

    lines.append("=" * 80)
    return "\n".join(lines)
