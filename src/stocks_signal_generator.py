#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import pandas as pd

# Add src to python path if run as script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import setup_logger
from src.pipeline import PlannerPipeline
from src.strategies import get_strategy
from src.models import StockSignal, MarketRegime

logger = setup_logger("StocksSignalGenerator")


def build_stock_signal(
    kite,
    instruments_df: pd.DataFrame,
    symbol: str,
    market_regime: MarketRegime,
    history_cache: dict,
    benchmark_history: pd.DataFrame,
    sector_vs_nifty_pct: float,
    scan_time: str,
) -> tuple[StockSignal | None, list]:
    """
    Builds stock signal by invoking the modular PlannerPipeline and the BreakoutTrendStrategy.
    """
    pipeline = PlannerPipeline()
    strategy = get_strategy("BreakoutTrendStrategy")

    signal, rejections = pipeline.run_symbol(
        kite=kite,
        instruments_df=instruments_df,
        symbol=symbol,
        market_regime=market_regime,
        history_cache=history_cache,
        benchmark_history=benchmark_history,
        sector_vs_nifty_pct=sector_vs_nifty_pct,
        scan_time=scan_time,
        strategy=strategy,
    )
    return signal, rejections
