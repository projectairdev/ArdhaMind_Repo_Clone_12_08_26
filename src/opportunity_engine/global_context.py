from __future__ import annotations

from typing import Optional
from src.models import GlobalContext


def evaluate_global_context(global_ctx: Optional[GlobalContext] = None) -> GlobalContext:
    """
    Parses and validates GlobalContext.
    If unavailable or not provided, degrades gracefully returning a blank disabled global context.
    """
    if global_ctx is None:
        return GlobalContext(is_available=False)
        
    if not global_ctx.is_available:
        if global_ctx.gift_nifty_status is not None or global_ctx.us_markets_status is not None:
            return GlobalContext(
                gift_nifty_status=global_ctx.gift_nifty_status,
                us_markets_status=global_ctx.us_markets_status,
                european_markets_status=global_ctx.european_markets_status,
                asian_markets_status=global_ctx.asian_markets_status,
                vix_trend=global_ctx.vix_trend,
                usdinr_trend=global_ctx.usdinr_trend,
                crude_oil_trend=global_ctx.crude_oil_trend,
                is_available=True
            )
        return GlobalContext(is_available=False)
        
    return global_ctx
