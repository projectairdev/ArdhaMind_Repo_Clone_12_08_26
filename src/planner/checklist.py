from __future__ import annotations

from src.models.opportunity_context import OpportunityContext
from src.models.market_context import MarketContext
from src.models.evening_report import PlannerChecklist


def generate_checklist(
    opportunity_context: OpportunityContext,
    market_context: MarketContext | None = None,
    best_strategy: str = "UNKNOWN",
    has_portfolio_warnings: bool = False,
) -> PlannerChecklist:
    items = []

    # 1. Opening Gap Direction / Overnight News
    bias = (
        opportunity_context.directional_bias.value
        if opportunity_context and opportunity_context.directional_bias
        else "NEUTRAL"
    )
    items.append(f"Confirm opening gap direction aligns with {bias} bias.")

    # 2. Liquidity / Option Chain
    items.append(
        "Verify option chain liquidity remains healthy with tight bid-ask spreads."
    )
    items.append(
        "Confirm option chain PCR and MaxPain have not materially shifted overnight."
    )

    # 3. Strategy specific level checks
    if (
        market_context
        and getattr(market_context, "support_levels", None)
        and getattr(market_context, "resistance_levels", None)
    ):
        support = market_context.support_levels[0]
        resistance = market_context.resistance_levels[0]
        if best_strategy == "BREAKOUT":
            items.append(
                f"Confirm breakout level of {resistance} is cleanly breached with high volume."
            )
        elif best_strategy in ("MEAN_REVERSION", "RANGE"):
            items.append(
                f"Verify spot price remains bounded between support {support} and resistance {resistance}."
            )
        else:
            items.append(
                f"Confirm price action respects support {support} and resistance {resistance}."
            )
    else:
        if best_strategy == "BREAKOUT":
            items.append(
                "Confirm breakout level has been cleanly breached with volume confirmation."
            )
        else:
            items.append("Confirm key S/R breakout/reversal levels before entry.")

    # 4. Volatility alerts
    vix = (
        market_context.india_vix
        if (market_context and getattr(market_context, "india_vix", None) is not None)
        else 0.0
    )
    if vix > 18.0:
        items.append(
            f"India VIX is high ({vix:.2f}). Reduce position sizing to manage larger expected moves."
        )

    # 5. Portfolio Warnings check
    if has_portfolio_warnings:
        items.append(
            "Review and resolve active portfolio constraint/exposure warnings before execution."
        )

    # 6. News/Overnight events
    items.append(
        "Re-evaluate directional bias if major overnight global or macro news occurs."
    )

    return PlannerChecklist(checklist_items=items)

