from __future__ import annotations

from typing import Any
from src.models import TrendSnapshot, MarketRegime, OptionSignal, StockSignal, TradeSignal


class BaseStrategy:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description

    def generate_signal(
        self,
        trend_snapshot: TrendSnapshot,
        market_regime: MarketRegime,
        asset_type: str = "STOCK",
        **kwargs: Any,
    ) -> TradeSignal | None:
        """
        Generates a trading signal (StockSignal or OptionSignal) based on trend and market regime.
        """
        raise NotImplementedError("Strategies must implement generate_signal")
