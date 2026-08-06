from __future__ import annotations

from src.models.risk_report import RiskReport
from src.models.decision_report import DecisionReport
from src.models.evening_report import RiskWatchlist


def compile_risk_watchlist(
    risk_report: RiskReport, decision_report: DecisionReport | None = None
) -> RiskWatchlist:
    portfolio_warnings = []
    candidate_warnings = []

    if not risk_report:
        return RiskWatchlist()

    # Candidate risks in risk_report have warnings
    if risk_report.candidate_risks:
        for cand in risk_report.candidate_risks:
            for w in cand.warnings:
                msg = f"[{cand.candidate_id}] {w.message} ({w.warning_type}, Severity: {w.severity})"
                if msg not in candidate_warnings:
                    candidate_warnings.append(msg)

    # If we have decision report, append any warnings from candidate_decisions
    if decision_report and decision_report.candidate_decisions:
        for d in decision_report.candidate_decisions:
            for w in d.warnings:
                msg = f"[{d.candidate_id}] {w.message} ({w.warning_type}, Severity: {w.severity})"
                if msg not in candidate_warnings:
                    candidate_warnings.append(msg)

    # Portfolio warnings are found at RiskReport or from constraints
    violated_constraints = set()
    if risk_report.candidate_risks:
        for cand in risk_report.candidate_risks:
            for c in cand.constraints:
                if c.is_violated:
                    violated_constraints.add(
                        f"Portfolio limit '{c.constraint_type}' violated! Limit: {c.limit_value}, Current: {c.current_value}"
                    )
    portfolio_warnings.extend(list(violated_constraints))

    # Also extract any conclusions or overall status from risk report
    if (
        risk_report.summary
        and hasattr(risk_report.summary, "conclusions")
        and risk_report.summary.conclusions
    ):
        for c in risk_report.summary.conclusions:
            if c not in portfolio_warnings:
                portfolio_warnings.append(c)

    max_limit = 150000.0  # default
    allocated = 0.0
    util_pct = 0.0

    if risk_report.exposure_summary:
        allocated = risk_report.exposure_summary.total_capital_allocated
        util_pct = risk_report.exposure_summary.portfolio_utilization_pct

    # Look for max_portfolio_exposure limit in risk report config
    if hasattr(risk_report, "config") and risk_report.config:
        max_limit = getattr(
            risk_report.config, "max_portfolio_exposure", 150000.0
        )

    risk_grade = (
        risk_report.summary.portfolio_risk_grade
        if risk_report.summary and hasattr(risk_report.summary, "portfolio_risk_grade")
        else "CONSERVATIVE"
    )

    return RiskWatchlist(
        warnings=candidate_warnings,
        portfolio_warnings=portfolio_warnings,
        max_capital_limit=max_limit,
        allocated_capital=allocated,
        portfolio_utilization_pct=util_pct,
        risk_grade=risk_grade,
    )
