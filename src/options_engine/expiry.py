from __future__ import annotations

from datetime import date
from typing import Optional
import pandas as pd


def nearest_expiry_for_symbol(
    instruments_df: pd.DataFrame,
    symbol: str,
    today: Optional[date] = None,
) -> Optional[date]:
    if today is None:
        today = date.today()

    rows = instruments_df[
        (instruments_df["exchange"] == "NFO")
        & (instruments_df["name"] == symbol)
        & (instruments_df["instrument_type"].isin(["CE", "PE"]))
        & (instruments_df["expiry"].notna())
    ].copy()

    if rows.empty:
        return None

    rows["dte"] = (rows["expiry"] - today).apply(lambda x: x.days)

    # Filter with reasonable days to expiry (DTE) constraints
    min_dte = 2
    max_dte = 10
    valid = rows[
        (rows["dte"] >= min_dte) &
        (rows["dte"] <= max_dte)
    ]

    if valid.empty:
        valid = rows[rows["dte"] >= min_dte]

    if valid.empty:
        return None

    return sorted(valid["expiry"].unique())[0]


def nearest_expiry_for_nifty(
    instruments_df: pd.DataFrame,
    min_expiry: Optional[date] = None,
) -> Optional[date]:
    if min_expiry is None:
        min_expiry = date.today()

    rows = instruments_df[
        (instruments_df["exchange"] == "NFO")
        & (instruments_df["name"] == "NIFTY")
        & (instruments_df["instrument_type"].isin(["CE", "PE"]))
        & (instruments_df["expiry"].notna())
        & (instruments_df["expiry"] >= min_expiry)
    ]
    if rows.empty:
        return None
    return sorted(rows["expiry"].unique())[0]
