from __future__ import annotations

from typing import Optional
from src.models import EveningReport, PlannerExplanation


def explain_planner(evening_report: Optional[EveningReport]) -> PlannerExplanation:
    """
    Explains the evening plan and tomorrow's outlook, highlighting support/resistance levels,
    market conditions, watchlist, and checklist.
    """
    if not evening_report or not evening_report.tomorrow_outlook:
        return PlannerExplanation(
            directional_bias="N/A",
            outlook_classification="N/A",
            explanation="No evening report or outlook is available to generate tomorrow planning explanations.",
        )

    out = evening_report.tomorrow_outlook
    bias = out.directional_bias
    classif = out.outlook_classification
    strength = out.opportunity_strength
    supports = out.key_support_levels
    resistances = out.key_resistance_levels
    desc = out.description

    reasoning = (
        f"The evening plan projects a '{bias}' directional bias with a tomorrow outlook classification of '{classif}' "
        f"(opportunity strength is {strength:.1f}%). "
    )

    if desc:
        reasoning += f"Outlook details: {desc}. "

    if supports or resistances:
        supp_str = ", ".join(map(str, supports)) if supports else "None"
        res_str = ", ".join(map(str, resistances)) if resistances else "None"
        reasoning += f"Key support levels are identified at: [{supp_str}] and resistance levels at: [{res_str}]. "

    # Integrate Market Summary if available
    ms = evening_report.market_summary
    if ms:
        reasoning += (
            f"These outlook levels are framed within a '{ms.regime}' market regime and '{ms.trend_direction}' trend direction, "
            f"having a Spot price of {ms.spot_price:.1f} and VIX price of {ms.vix_price:.1f}. "
        )

    # Integrate watchlists/checklists if available
    rw = evening_report.risk_watchlist
    if rw:
        if rw.warnings or rw.portfolio_warnings:
            all_w = rw.warnings + rw.portfolio_warnings
            reasoning += f"Risk warnings to monitor: {'; '.join(all_w)}. "

    chk = evening_report.checklist
    if chk and chk.checklist_items:
        reasoning += f"Required planner checklist items: {', '.join(chk.checklist_items)}. "

    return PlannerExplanation(
        directional_bias=bias,
        outlook_classification=classif,
        explanation=reasoning,
    )
