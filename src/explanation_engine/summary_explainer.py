from __future__ import annotations

from typing import Optional, List
from src.models import (
    DecisionReport,
    IntradayReport,
    StrategyEvaluation,
    MarketScore,
    ExplanationSummary,
)


def explain_summary(
    decision_report: Optional[DecisionReport],
    intraday_report: Optional[IntradayReport],
    strategy_evaluation: Optional[StrategyEvaluation],
    market_score: Optional[MarketScore],
) -> ExplanationSummary:
    """
    Compiles a high-level title, brief overview, and key findings for the workstation state.
    References existing fields to build human-readable highlights.
    """
    title = "Trading Workstation Explanation Report"

    # 1. Brief overview
    m_grade = market_score.letter_grade if market_score else "N/A"
    m_val = market_score.overall_score if market_score else 0.0
    best_strat = strategy_evaluation.overall_best_strategy if strategy_evaluation else "N/A"

    overview = (
        f"This explanation report clarifies current workstation recommendations. "
        f"The current market environment is rated with an overall score of {m_val:.1f} (Grade {m_grade}), "
        f"with '{best_strat}' identified as the primary trading strategy suitability choice. "
    )

    if decision_report:
        overview += (
            f"The decision pipeline has resolved to '{decision_report.summary.overall_action}' status "
            f"for immediate action. "
        )

    # 2. Key findings
    findings: List[str] = []
    
    if market_score:
        findings.append(f"Market health is grade {m_grade} with an overall quality score of {m_val:.1f} out of 100.")

    if strategy_evaluation:
        findings.append(f"Primary recommended strategy: '{best_strat}' based on suitability assessments.")

    if decision_report:
        stats = decision_report.stats
        findings.append(
            f"Decision summary resolved to overall action '{decision_report.summary.overall_action}'. "
            f"Total candidates: {stats.total_candidates_evaluated} (BUY: {stats.buy_count}, "
            f"SELL: {stats.sell_count}, WATCH: {stats.watch_count}, REJECT: {stats.reject_count}, "
            f"NO TRADE: {stats.no_trade_count}). Allocated capital: INR {stats.total_allocated_capital:,.2f}."
        )
        if decision_report.summary.highest_priority_candidate_id != "NONE":
            findings.append(f"Highest priority execution candidate is '{decision_report.summary.highest_priority_candidate_id}'.")

    if intraday_report:
        sum_data = intraday_report.summary
        findings.append(
            f"Intraday monitor validates plan as '{sum_data.plan_status.value if hasattr(sum_data.plan_status, 'value') else str(sum_data.plan_status)}' "
            f"recommending workflow action '{sum_data.action_recommendation.value if hasattr(sum_data.action_recommendation, 'value') else str(sum_data.action_recommendation)}'."
        )

    return ExplanationSummary(
        title=title,
        brief_overview=overview,
        key_findings=findings,
    )
