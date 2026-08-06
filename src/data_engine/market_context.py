from __future__ import annotations

import datetime
import pandas as pd
from typing import Any
from src.utils import setup_logger
from src.data_engine.instruments import get_index_row, InstrumentManager
from src.data_engine.historical import get_multi_timeframe_history
from src.data_engine.quotes import get_quote_map, get_ltp_map

logger = setup_logger("MarketContextBuilder")


def fetch_nifty_spot(kite: Any) -> float:
    """
    Fetches the current NIFTY 50 spot price from Kite API.
    """
    try:
        quotes = get_quote_map(kite, ["NSE:NIFTY 50"])
        if "NSE:NIFTY 50" in quotes:
            return float(quotes["NSE:NIFTY 50"]["last_price"])
    except Exception as exc:
        logger.warning(f"Failed to fetch NIFTY spot from quote API: {exc}. Trying LTP API.")
    
    try:
        ltp_map = get_ltp_map(kite, ["NSE:NIFTY 50"])
        if "NSE:NIFTY 50" in ltp_map:
            return float(ltp_map["NSE:NIFTY 50"]["last_price"])
    except Exception as exc:
        logger.error(f"Failed to fetch NIFTY spot from LTP API: {exc}")
    
    raise RuntimeError("Unable to fetch NIFTY spot price from Kite API.")


def fetch_india_vix(kite: Any) -> float | None:
    """
    Fetches the India VIX index value if available.
    """
    try:
        quotes = get_quote_map(kite, ["NSE:INDIA VIX"])
        if "NSE:INDIA VIX" in quotes:
            return float(quotes["NSE:INDIA VIX"]["last_price"])
    except Exception:
        try:
            ltp_map = get_ltp_map(kite, ["NSE:INDIA VIX"])
            if "NSE:INDIA VIX" in ltp_map:
                return float(ltp_map["NSE:INDIA VIX"]["last_price"])
        except Exception:
            pass
    return None


def resolve_current_expiry(instruments_df: pd.DataFrame) -> str:
    """
    Resolves the nearest NIFTY option expiry date.
    """
    expiry = InstrumentManager.resolve_nearest_expiry(instruments_df, "NIFTY")
    if expiry is None:
        # Fallback to next Thursday
        today = datetime.date.today()
        days_to_thursday = (3 - today.weekday()) % 7
        if days_to_thursday == 0:
            days_to_thursday = 7
        expiry = today + datetime.timedelta(days=days_to_thursday)
    return expiry.strftime("%Y-%m-%d")


def load_nifty_candles(kite: Any, instruments_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Loads multi-timeframe daily and intraday candles for NIFTY 50 index.
    """
    index_row = get_index_row(instruments_df, "NIFTY 50")
    token = int(index_row["instrument_token"])
    return get_multi_timeframe_history(kite, token)


def load_nifty_quotes(kite: Any) -> dict:
    """
    Loads latest quotes for NIFTY 50 index.
    """
    try:
        return get_quote_map(kite, ["NSE:NIFTY 50"])
    except Exception as exc:
        logger.error(f"Failed loading NIFTY quotes: {exc}")
        return {}


def determine_trading_session() -> str:
    """
    Determines whether the market is in PRE, LIVE, or POST session.
    Standard Indian market hours: 09:15 to 15:30.
    """
    now = datetime.datetime.now()
    t = now.time()
    if t < datetime.time(9, 15):
        return "PRE"
    elif t <= datetime.time(15, 30):
        return "LIVE"
    else:
        return "POST"
