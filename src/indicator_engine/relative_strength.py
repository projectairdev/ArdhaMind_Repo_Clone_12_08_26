from __future__ import annotations

from typing import Optional
import numpy as np
import pandas as pd

from src.models import RelativeStrengthMetrics


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def compute_return_pct(df: pd.DataFrame, lookback_bars: int = 5) -> float:
    if df.empty or len(df) < 2:
        return 0.0
    sorted_df = df.sort_values("date")
    start_idx = max(0, len(sorted_df) - lookback_bars - 1)
    start_price = _safe_float(sorted_df.iloc[start_idx]["close"])
    end_price = _safe_float(sorted_df.iloc[-1]["close"])
    if start_price <= 0:
        return 0.0
    return round(((end_price - start_price) / start_price) * 100.0, 2)


def compute_relative_strength(
    stock_daily_df: pd.DataFrame,
    benchmark_daily_df: Optional[pd.DataFrame],
    sector_vs_nifty_pct: float = 0.0,
    lookback_bars: int = 5,
) -> RelativeStrengthMetrics:
    stock_return_pct = compute_return_pct(stock_daily_df, lookback_bars=lookback_bars)
    benchmark_return_pct = (
        compute_return_pct(benchmark_daily_df, lookback_bars=lookback_bars)
        if benchmark_daily_df is not None
        else 0.0
    )
    stock_vs_nifty_pct = round(stock_return_pct - benchmark_return_pct, 2)
    sector_vs_nifty_pct = round(float(sector_vs_nifty_pct), 2)

    stock_score = float(np.clip(stock_vs_nifty_pct / 6.0, -0.10, 0.10))
    sector_score = float(np.clip(sector_vs_nifty_pct / 8.0, -0.08, 0.08))
    score = round(stock_score + sector_score, 2)

    if stock_vs_nifty_pct > 1.0 and sector_vs_nifty_pct >= 0:
        rationale = f"Stock outperforming Nifty by {stock_vs_nifty_pct:+.2f}% with sector support {sector_vs_nifty_pct:+.2f}%."
    elif stock_vs_nifty_pct < -1.0 and sector_vs_nifty_pct <= 0:
        rationale = f"Stock underperforming Nifty by {stock_vs_nifty_pct:+.2f}% with weak sector {sector_vs_nifty_pct:+.2f}%."
    else:
        rationale = f"Relative strength mixed at stock {stock_vs_nifty_pct:+.2f}% vs sector {sector_vs_nifty_pct:+.2f}%."

    return RelativeStrengthMetrics(
        stock_return_pct=stock_return_pct,
        benchmark_return_pct=benchmark_return_pct,
        stock_vs_nifty_pct=stock_vs_nifty_pct,
        sector_vs_nifty_pct=sector_vs_nifty_pct,
        score=score,
        rationale=rationale,
    )
