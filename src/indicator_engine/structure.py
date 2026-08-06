from __future__ import annotations

import pandas as pd
from src.models import StructureMetrics


def detect_market_structure(df: pd.DataFrame, lookback_bars: int = 8) -> StructureMetrics:
    if df.empty:
        return StructureMetrics("SIDEWAYS", 0, 0, 0, 0, "No candles available.")

    recent = df.sort_values("date").tail(max(lookback_bars, 4)).reset_index(drop=True)
    highs = recent["high"].astype(float).tolist()
    lows = recent["low"].astype(float).tolist()

    if len(highs) < 3:
        return StructureMetrics("SIDEWAYS", 0, 0, 0, 0, "Not enough candles for structure.")

    swing_highs = []
    swing_lows = []
    for idx in range(1, len(recent) - 1):
        if highs[idx] >= highs[idx - 1] and highs[idx] > highs[idx + 1]:
            swing_highs.append(highs[idx])
        if lows[idx] <= lows[idx - 1] and lows[idx] < lows[idx + 1]:
            swing_lows.append(lows[idx])

    if len(swing_highs) >= 2 and len(swing_lows) >= 2:
        hh = sum(1 for idx in range(1, len(swing_highs)) if swing_highs[idx] > swing_highs[idx - 1])
        lh = sum(1 for idx in range(1, len(swing_highs)) if swing_highs[idx] < swing_highs[idx - 1])
        hl = sum(1 for idx in range(1, len(swing_lows)) if swing_lows[idx] > swing_lows[idx - 1])
        ll = sum(1 for idx in range(1, len(swing_lows)) if swing_lows[idx] < swing_lows[idx - 1])
    else:
        hh = sum(1 for idx in range(1, len(highs)) if highs[idx] > highs[idx - 1])
        lh = sum(1 for idx in range(1, len(highs)) if highs[idx] < highs[idx - 1])
        hl = sum(1 for idx in range(1, len(lows)) if lows[idx] > lows[idx - 1])
        ll = sum(1 for idx in range(1, len(lows)) if lows[idx] < lows[idx - 1])

    threshold = 2 if len(recent) >= 6 else 1
    if hh >= threshold and hl >= threshold and hh >= lh and hl >= ll:
        trend = "BULLISH"
        rationale = f"Structure bullish with HH={hh}, HL={hl}."
    elif lh >= threshold and ll >= threshold and lh >= hh and ll >= hl:
        trend = "BEARISH"
        rationale = f"Structure bearish with LH={lh}, LL={ll}."
    else:
        trend = "SIDEWAYS"
        rationale = f"Structure mixed with HH={hh}, HL={hl}, LH={lh}, LL={ll}."

    return StructureMetrics(
        trend=trend,
        higher_highs=hh,
        higher_lows=hl,
        lower_highs=lh,
        lower_lows=ll,
        rationale=rationale,
    )
