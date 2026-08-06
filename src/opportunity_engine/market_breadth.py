from __future__ import annotations

from typing import Optional
from src.models import MarketBreadthContext


def evaluate_market_breadth(breadth: Optional[MarketBreadthContext] = None) -> MarketBreadthContext:
    """
    Parses and validates MarketBreadthContext.
    If unavailable or not provided, degrades gracefully returning a blank disabled breadth context.
    """
    if breadth is None:
        return MarketBreadthContext(is_available=False)
    
    # If the user passed in breadth but didn't set is_available, let's derive it or preserve it
    if not breadth.is_available:
        # Check if we have some core signals to make it available
        if breadth.advance_decline_ratio is not None or breadth.sector_strength is not None:
            return MarketBreadthContext(
                advance_decline_ratio=breadth.advance_decline_ratio,
                sector_strength=breadth.sector_strength,
                bank_nifty_confirmation=breadth.bank_nifty_confirmation,
                fin_nifty_confirmation=breadth.fin_nifty_confirmation,
                large_cap_participation=breadth.large_cap_participation,
                mid_cap_participation=breadth.mid_cap_participation,
                is_available=True
            )
        return MarketBreadthContext(is_available=False)
        
    return breadth
