from __future__ import annotations

from typing import Mapping
import pandas as pd
from src.models import TimeframeMetrics
from src.indicator_engine.indicators import atr


def compute_volatility_score(timeframe_metrics: Mapping[str, TimeframeMetrics]) -> float:
    five = timeframe_metrics.get("5minute")
    fifteen = timeframe_metrics.get("15minute")
    daily = timeframe_metrics.get("day")

    vol_candidates = []
    for metrics in [five, fifteen, daily]:
        if metrics is None or metrics.close <= 0:
            continue
        vol_candidates.append((metrics.atr / metrics.close) * 100.0)
    return round(max(vol_candidates) if vol_candidates else 0.0, 2)
