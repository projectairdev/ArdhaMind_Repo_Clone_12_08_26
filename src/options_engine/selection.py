from __future__ import annotations

from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
from kiteconnect import KiteConnect
from src.configuration_engine.runtime import Config
from src.utils import setup_logger, is_market_hours
from src.data_engine.quotes import get_quote_map
from src.options_engine.scoring import compute_option_quality_score

logger = setup_logger("OptionSelection")


def filter_option_candidates(
    instruments_df: pd.DataFrame,
    symbol: str,
    expiry: pd.Timestamp | str | datetime.date,
    opt_type: str,
    strikes: List[int],
) -> pd.DataFrame:
    rows = instruments_df[
        (instruments_df["exchange"] == "NFO")
        & (instruments_df["name"] == symbol)
        & (instruments_df["instrument_type"] == opt_type)
        & (instruments_df["expiry"] == expiry)
        & (instruments_df["strike"].astype(float).isin([float(s) for s in strikes]))
    ].copy()
    return rows.sort_values(["strike"])


def choose_best_option(
    kite: KiteConnect,
    options_df: pd.DataFrame,
) -> Tuple[Optional[pd.Series], Optional[str]]:
    if options_df.empty:
        return None, None

    keys = [f"NFO:{ts}" for ts in options_df["tradingsymbol"].tolist()]
    quote_fetch_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    quote_map = get_quote_map(kite, keys)
    allow_after_hours_fallback = not is_market_hours()

    metrics = []
    for _, row in options_df.iterrows():
        key = f"NFO:{row['tradingsymbol']}"
        q = quote_map.get(key, {})
        depth = q.get("depth") or {}
        buy_depth = depth.get("buy") or []
        sell_depth = depth.get("sell") or []
        bid_price = float(buy_depth[0].get("price", 0.0)) if buy_depth else 0.0
        ask_price = float(sell_depth[0].get("price", 0.0)) if sell_depth else 0.0
        ltp = q.get("last_price")
        if ltp in (None, ""):
            ltp = (q.get("ohlc") or {}).get("close")
        ltp = float(ltp) if ltp not in (None, "") else np.nan

        if not np.isnan(ltp) and bid_price > 0 and ask_price > 0:
            spread_pct = ((ask_price - bid_price) / ltp) * 100.0
        elif allow_after_hours_fallback and not np.isnan(ltp):
            bid_price = ltp
            ask_price = ltp
            spread_pct = 0.0
        else:
            spread_pct = 99.0

        oi_val = q.get("oi", q.get("open_interest", 0)) or 0
        metrics.append(
            {
                "option_ltp": ltp,
                "option_volume": int(q.get("volume", 0) or 0),
                "option_oi": int(oi_val),
                "bid_price": round(bid_price, 2),
                "ask_price": round(ask_price, 2),
                "spread_pct": round(spread_pct, 2),
            }
        )

    tmp = options_df.copy().reset_index(drop=True)
    metric_df = pd.DataFrame(metrics)
    tmp = pd.concat([tmp, metric_df], axis=1)
    tmp = tmp[tmp["option_ltp"].notna()]
    tmp = tmp[
        (tmp["option_ltp"] >= Config.MIN_OPTION_LTP)
        & (tmp["option_ltp"] <= Config.MAX_OPTION_LTP)
    ]
    tmp = tmp[tmp["spread_pct"] <= 20.0]

    if tmp.empty:
        return None, quote_fetch_time

    tmp["cost"] = tmp["option_ltp"] * tmp["lot_size"]
    tmp = tmp[tmp["cost"] <= Config.MAX_CAPITAL_PER_TRADE_OPTIONS]

    if tmp.empty:
        return None, quote_fetch_time

    atm_strike = tmp["strike"].astype(float).median()
    tmp["option_quality_score"] = tmp.apply(
        lambda row: compute_option_quality_score(
            strike=float(row["strike"]),
            atm_strike=atm_strike,
            cost=float(row["cost"]),
            option_ltp=float(row["option_ltp"]),
            option_oi=int(row["option_oi"]),
            option_volume=int(row["option_volume"]),
            spread_pct=float(row["spread_pct"]),
        ),
        axis=1,
    )

    best_row = tmp.sort_values("option_quality_score", ascending=False).iloc[0]
    return best_row, quote_fetch_time
