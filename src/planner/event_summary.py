from __future__ import annotations

from src.models.market_score import MarketScore
from src.models.opportunity_context import OpportunityContext
from src.models.market_context import MarketContext
from src.models.evening_report import EventWatchlist


def compile_event_watchlist(
    market_score: MarketScore,
    opportunity_context: OpportunityContext | None = None,
    market_context: MarketContext | None = None,
) -> EventWatchlist:
    events = []

    days_rem = 0.0
    expiry_type = "NORMAL"

    if market_score and market_score.expiry:
        # We can extract expiry type if available
        if hasattr(market_score.expiry, "expiry_type_score"):
            pass

    if market_context:
        if market_context.current_expiry:
            events.append(f"Upcoming Expiry Date: {market_context.current_expiry}")
        # Check for VIX / Volatility State
        if (
            hasattr(market_context, "volatility_state")
            and market_context.volatility_state != "NORMAL"
        ):
            events.append(
                f"Volatility Regime Alert: {market_context.volatility_state} volatility expected."
            )
        if (
            hasattr(market_context, "india_vix")
            and market_context.india_vix is not None
            and market_context.india_vix > 18.0
        ):
            events.append(
                f"High VIX Warning: India VIX is at {market_context.india_vix:.2f}. Expect wider swings."
            )

    if opportunity_context:
        # Check if there are invalidation factors or global status
        if (
            hasattr(opportunity_context, "global_ctx")
            and opportunity_context.global_ctx
            and opportunity_context.global_ctx.is_available
        ):
            g_ctx = opportunity_context.global_ctx
            if getattr(g_ctx, "vix_trend", None):
                events.append(f"Global VIX Trend: {g_ctx.vix_trend}")
            if getattr(g_ctx, "gift_nifty_status", None):
                events.append(
                    f"GIFT NIFTY Overnight Bias: {g_ctx.gift_nifty_status}"
                )
            if getattr(g_ctx, "us_markets_status", None):
                events.append(f"US Markets Session: {g_ctx.us_markets_status}")

    # Deduplicate events
    unique_events = []
    for e in events:
        if e not in unique_events:
            unique_events.append(e)

    return EventWatchlist(
        events=unique_events,
        expiry_days_remaining=days_rem,
        expiry_type=expiry_type,
    )
