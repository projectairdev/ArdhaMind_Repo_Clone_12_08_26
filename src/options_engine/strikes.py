from __future__ import annotations

from typing import List
import numpy as np
import pandas as pd
from src.utils import round_to_step


def get_dynamic_strike_step(
    instruments_df: pd.DataFrame,
    symbol: str,
    expiry: pd.Timestamp | str | datetime.date,
) -> int:
    rows = instruments_df[
        (instruments_df["exchange"] == "NFO")
        & (instruments_df["name"] == symbol)
        & (instruments_df["instrument_type"].isin(["CE", "PE"]))
        & (instruments_df["expiry"] == expiry)
    ].copy()

    strikes = sorted(rows["strike"].dropna().astype(float).unique().tolist())
    if len(strikes) < 2:
        return 10

    diffs = np.diff(strikes)
    diffs = [d for d in diffs if d > 0]
    if not diffs:
        return 10

    return int(round(float(np.median(diffs))))


def candidate_strikes(spot: float, step: int) -> List[int]:
    atm = round_to_step(spot, step)
    return sorted(
        {
            atm - 3 * step,
            atm - 2 * step,
            atm - step,
            atm,
            atm + step,
            atm + 2 * step,
            atm + 3 * step,
        }
    )
