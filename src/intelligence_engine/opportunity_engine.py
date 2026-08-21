# src/intelligence_engine/opportunity_engine.py
from __future__ import annotations

from typing import Any, Dict, Optional
from src.utils import setup_logger

logger = setup_logger("RollingOpportunityEngine")


class RollingOpportunityEngine:
    """
    Dynamic Rolling Decision Corridor Engine for ArdhaMind.
    
    Recalculates active decision corridors when NIFTY expands beyond pre-market ranges,
    avoiding static lock-in to obsolete morning corridors.
    """

    @classmethod
    def calculate_rolling_corridor(
        cls,
        spot: float,
        open_price: float,
        high_price: float,
        low_price: float,
        vwap: float = 0.0,
        pre_market_corridor: Optional[Dict[str, float]] = None,
        candles_beyond_count: int = 0,
    ) -> Dict[str, Any]:
        open_ref = open_price if open_price > 0 else spot
        vwap_ref = vwap if vwap > 0 else open_ref

        # Initial pre-market corridor bounds
        base_low = pre_market_corridor.get("low") if pre_market_corridor else (open_ref - 20.0)
        base_high = pre_market_corridor.get("high") if pre_market_corridor else (open_ref + 20.0)

        # Expansion check: Spot moved > 0.25% beyond previous corridor
        corridor_width = max(20.0, base_high - base_low)
        expansion_up = spot > (base_high + 5.0)
        expansion_down = spot < (base_low - 5.0)

        if expansion_up and (candles_beyond_count >= 2 or spot > open_ref * 1.003):
            # Roll corridor upward around trailing VWAP / recent swing
            corridor_low = round(max(base_low, vwap_ref - 10.0), 1)
            corridor_high = round(max(high_price, spot + 15.0), 1)
            is_rolled = True
        elif expansion_down and (candles_beyond_count >= 2 or spot < open_ref * 0.997):
            # Roll corridor downward around trailing VWAP / recent swing
            corridor_low = round(min(low_price, spot - 15.0), 1)
            corridor_high = round(min(base_high, vwap_ref + 10.0), 1)
            is_rolled = True
        else:
            corridor_low = round(base_low, 1)
            corridor_high = round(base_high, 1)
            is_rolled = False

        decision_zone_str = f"{corridor_low:.0f} – {corridor_high:.0f}"

        return {
            "corridor_low": corridor_low,
            "corridor_high": corridor_high,
            "decision_zone": decision_zone_str,
            "is_rolled": is_rolled,
            "corridor_midpoint": round((corridor_low + corridor_high) / 2.0, 1),
        }
