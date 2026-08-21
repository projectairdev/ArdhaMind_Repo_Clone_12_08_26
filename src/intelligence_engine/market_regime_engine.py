# src/intelligence_engine/market_regime_engine.py
from __future__ import annotations

from typing import Any, Dict, Optional
from src.utils import setup_logger

logger = setup_logger("MarketRegimeEngine")


class MarketRegimeEngine:
    """
    Real-Time Dynamic Market Regime Engine for ArdhaMind.
    
    Classifies session structure based on intraday displacement, market breadth,
    and VWAP/EMA separation into actionable regime states:
    - TRENDING_EXPANSION_BULL: Spot >= +0.40% from open with Advances >= 65%
    - TRENDING_EXPANSION_BEAR: Spot <= -0.40% from open with Declines >= 65%
    - RANGE_COMPRESSED: Low displacement (< 0.25%) with split breadth / chop
    - RANGE_DAY: Default two-way rotational range
    """

    @classmethod
    def detect_regime(
        cls,
        spot: float,
        open_price: float,
        advances: int = 25,
        declines: int = 25,
        vwap: float = 0.0,
        ema_20: float = 0.0,
        high_price: float = 0.0,
        low_price: float = 0.0,
        vix: float = 12.5,
    ) -> Dict[str, Any]:
        open_ref = open_price if open_price > 0 else spot
        displacement_pts = spot - open_ref
        displacement_pct = (displacement_pts / open_ref) * 100.0 if open_ref > 0 else 0.0

        total_stocks = max(1, advances + declines)
        advance_ratio_pct = (advances / total_stocks) * 100.0
        decline_ratio_pct = (declines / total_stocks) * 100.0

        # Primary Regime Classification
        if displacement_pct >= 0.40 and advance_ratio_pct >= 65.0:
            regime = "TRENDING_EXPANSION_BULL"
        elif displacement_pct <= -0.40 and decline_ratio_pct >= 65.0:
            regime = "TRENDING_EXPANSION_BEAR"
        elif abs(displacement_pct) < 0.25 and 40.0 <= advance_ratio_pct <= 60.0:
            regime = "RANGE_COMPRESSED"
        else:
            regime = "RANGE_DAY"

        # Trend Strength Calculation (0 - 100)
        base_strength = min(50.0, abs(displacement_pct) * 75.0)
        breadth_boost = min(30.0, abs(advance_ratio_pct - 50.0) * 1.2)
        
        vwap_ref = vwap if vwap > 0 else open_ref
        vwap_separation = abs(spot - vwap_ref) / vwap_ref * 100.0 if vwap_ref > 0 else 0.0
        vwap_boost = min(20.0, vwap_separation * 40.0)

        trend_strength = round(min(100.0, base_strength + breadth_boost + vwap_boost), 1)

        # Volatility Status
        if vix < 12.0:
            volatility_regime = "COMPRESSED"
        elif vix <= 16.0:
            volatility_regime = "NORMAL"
        else:
            volatility_regime = "ELEVATED"

        return {
            "regime": regime,
            "trend_strength": trend_strength,
            "displacement_pts": round(displacement_pts, 2),
            "displacement_pct": round(displacement_pct, 2),
            "advance_ratio_pct": round(advance_ratio_pct, 1),
            "decline_ratio_pct": round(decline_ratio_pct, 1),
            "volatility_regime": volatility_regime,
            "vwap_separation_pct": round(vwap_separation, 2),
        }
