from __future__ import annotations

from typing import Any
import pandas as pd


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or pd.isna(value):
            return default
        return int(value)
    except Exception:
        return default


def round_to_step(price: float, step: int) -> int:
    if step <= 0:
        return int(price)
    return int(round(price / step) * step)
