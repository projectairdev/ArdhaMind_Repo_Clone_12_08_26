from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class MarketContext:
    current_spot: float
    timestamp: str
    trading_session: str
    current_expiry: str
    market_regime: str
    trend_direction: str
    trend_strength: float
    support_levels: List[float] = field(default_factory=list)
    resistance_levels: List[float] = field(default_factory=list)
    vwap: float = 0.0
    atr: float = 0.0
    india_vix: Optional[float] = None
    volatility_state: str = "NORMAL"
