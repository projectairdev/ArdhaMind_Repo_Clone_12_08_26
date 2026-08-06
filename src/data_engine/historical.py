from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
import pandas as pd
from kiteconnect import KiteConnect
from src.config_engine import Config
from src.utils import call_with_retry, setup_logger

logger = setup_logger("HistoricalData")

TIMEFRAME_DAYS: Dict[str, int] = {
    "day": 90,
    "60minute": 30,
    "15minute": 20,
    "5minute": Config.LOOKBACK_DAYS,
}


def get_historical_df(
    kite: Any,
    instrument_token: int,
    interval: str,
    days: int,
) -> pd.DataFrame:
    now = datetime.now()
    frm = now - timedelta(days=days)
    
    from src.broker.interfaces.broker_interface import IBrokerGateway
    from src.broker.services.broker_service import BrokerService
    if isinstance(kite, (IBrokerGateway, BrokerService)):
        func = kite.get_historical_data
    else:
        func = kite.historical_data

    candles = call_with_retry(
        func,
        instrument_token=instrument_token,
        from_date=frm,
        to_date=now,
        interval=interval,
        continuous=False,
        oi=False,
    )
    df = pd.DataFrame(candles)
    if df.empty:
        raise RuntimeError(f"No historical data for token {instrument_token}")
    df["date"] = pd.to_datetime(df["date"])
    return df


def get_historical_df_cached(
    kite: Any,
    instrument_token: int,
    interval: str,
    days: int,
    history_cache: Optional[Dict[Tuple[int, str, int], pd.DataFrame]] = None,
) -> pd.DataFrame:
    if history_cache is None:
        return get_historical_df(kite, instrument_token, interval, days)

    cache_key = (instrument_token, interval, days)
    if cache_key not in history_cache:
        history_cache[cache_key] = get_historical_df(kite, instrument_token, interval, days)
    return history_cache[cache_key]


def get_multi_timeframe_history(
    kite: Any,
    instrument_token: int,
    history_cache: Optional[Dict[Tuple[int, str, int], pd.DataFrame]] = None,
) -> Dict[str, pd.DataFrame]:
    return {
        interval: get_historical_df_cached(
            kite=kite,
            instrument_token=instrument_token,
            interval=interval,
            days=days,
            history_cache=history_cache,
        )
        for interval, days in TIMEFRAME_DAYS.items()
    }
