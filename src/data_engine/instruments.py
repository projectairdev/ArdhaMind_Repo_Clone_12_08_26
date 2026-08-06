from __future__ import annotations

import pandas as pd
from kiteconnect import KiteConnect
from src.config_engine import Config
from typing import Any
from src.utils import call_with_retry, setup_logger

logger = setup_logger("Instruments")


def load_instruments_df(kite: Any) -> pd.DataFrame:
    logger.info("Loading instrument master list from Kite API...")
    if hasattr(kite, "get_instruments"):
        instruments = call_with_retry(kite.get_instruments)
    else:
        instruments = call_with_retry(kite.instruments)
    df = pd.DataFrame(instruments)
    if df.empty:
        raise RuntimeError("Instrument master is empty.")
    if "expiry" in df.columns:
        df["expiry"] = pd.to_datetime(df["expiry"], errors="coerce").dt.date
    return df


def get_equity_row(instruments_df: pd.DataFrame, symbol: str) -> pd.Series:
    rows = instruments_df[
        (instruments_df["exchange"] == "NSE")
        & (instruments_df["segment"] == "NSE")
        & (instruments_df["tradingsymbol"] == symbol)
    ]
    if rows.empty:
        raise ValueError(f"NSE equity instrument not found for {symbol}")
    return rows.iloc[0]


def get_index_row(instruments_df: pd.DataFrame, symbol: str) -> pd.Series:
    rows = instruments_df[
        (instruments_df["segment"] == "INDICES")
        & (instruments_df["tradingsymbol"] == symbol)
    ]
    if rows.empty:
        raise ValueError(f"Index instrument not found for {symbol}")
    return rows.iloc[0]


def get_fo_underlying_symbols(instruments_df: pd.DataFrame) -> list[str]:
    nfo_symbols = instruments_df[
        (instruments_df["exchange"] == "NFO")
        & (instruments_df["instrument_type"].isin(["CE", "PE"]))
        & (instruments_df["name"].notna())
        & (instruments_df["name"] != "")
    ]["name"].dropna().unique().tolist()

    nse_cash_symbols = set(
        instruments_df[
            (instruments_df["exchange"] == "NSE")
            & (instruments_df["segment"] == "NSE")
        ]["tradingsymbol"].dropna().unique().tolist()
    )
    return sorted(set(nfo_symbols).intersection(nse_cash_symbols))


def get_symbol_sector(symbol: str) -> str:
    return Config.SYMBOL_SECTOR_MAP.get(symbol, "UNKNOWN")


class InstrumentManager:
    _cache: pd.DataFrame | None = None
    _last_loaded: pd.Timestamp | None = None

    @classmethod
    def get_instruments(cls, kite: KiteConnect) -> pd.DataFrame:
        """
        Retrieves the instruments master list, utilizing class-level caching.
        Refreshes once daily if date changes.
        """
        today = pd.Timestamp.now().normalize()
        if cls._cache is None or cls._last_loaded is None or cls._last_loaded < today:
            cls._cache = load_instruments_df(kite)
            cls._last_loaded = today
        return cls._cache

    @classmethod
    def clear_cache(cls):
        cls._cache = None
        cls._last_loaded = None

    @staticmethod
    def get_option_expiries(instruments_df: pd.DataFrame, symbol: str) -> list[pd.Timestamp.date]:
        """
        Returns a sorted list of unique option expiries for a given symbol, equal to or after today.
        """
        import datetime
        today = datetime.date.today()
        # Filter NFO options for the underlying symbol
        df_opts = instruments_df[
            (instruments_df["exchange"] == "NFO")
            & (instruments_df["name"] == symbol)
            & (instruments_df["instrument_type"].isin(["CE", "PE"]))
        ]
        if df_opts.empty:
            return []
        
        # Ensure expiries are dates and filter for future/today
        expiries = df_opts["expiry"].dropna().unique()
        exp_unique = sorted(list(expiries))
        return [exp for exp in exp_unique if exp >= today]

    @classmethod
    def resolve_nearest_expiry(cls, instruments_df: pd.DataFrame, symbol: str) -> pd.Timestamp.date | None:
        """
        Returns the nearest option expiry.
        """
        expiries = cls.get_option_expiries(instruments_df, symbol)
        return expiries[0] if expiries else None

    @classmethod
    def resolve_weekly_expiry(cls, instruments_df: pd.DataFrame, symbol: str) -> pd.Timestamp.date | None:
        """
        Returns the nearest weekly expiry. An expiry is weekly if it is NOT the last expiry of that calendar month.
        """
        expiries = cls.get_option_expiries(instruments_df, symbol)
        for exp in expiries:
            same_month = [e for e in expiries if e.year == exp.year and e.month == exp.month]
            if exp != max(same_month):
                return exp
        # If no weekly expiry found, return the nearest one
        return expiries[0] if expiries else None

    @classmethod
    def resolve_monthly_expiry(cls, instruments_df: pd.DataFrame, symbol: str) -> pd.Timestamp.date | None:
        """
        Returns the nearest monthly expiry (last expiry of the calendar month).
        """
        expiries = cls.get_option_expiries(instruments_df, symbol)
        for exp in expiries:
            same_month = [e for e in expiries if e.year == exp.year and e.month == exp.month]
            if exp == max(same_month):
                return exp
        return None

    @classmethod
    def resolve_next_weekly_expiry(cls, instruments_df: pd.DataFrame, symbol: str) -> pd.Timestamp.date | None:
        """
        Returns the second nearest weekly expiry.
        """
        expiries = cls.get_option_expiries(instruments_df, symbol)
        if len(expiries) > 1:
            return expiries[1]
        return expiries[0] if expiries else None

    @classmethod
    def resolve_next_monthly_expiry(cls, instruments_df: pd.DataFrame, symbol: str) -> pd.Timestamp.date | None:
        """
        Returns the monthly expiry for the next calendar month.
        """
        expiries = cls.get_option_expiries(instruments_df, symbol)
        current_monthly = cls.resolve_monthly_expiry(instruments_df, symbol)
        if not current_monthly:
            return None
        next_month = (current_monthly.month % 12) + 1
        next_year = current_monthly.year + (1 if current_monthly.month == 12 else 0)
        next_month_expiries = [e for e in expiries if e.year == next_year and e.month == next_month]
        if next_month_expiries:
            return max(next_month_expiries)
        return None

    @staticmethod
    def resolve_atm_strike(instruments_df: pd.DataFrame, symbol: str, spot_price: float) -> float | None:
        """
        Resolves the At-The-Money (ATM) strike price closest to the spot price.
        """
        df_opts = instruments_df[
            (instruments_df["exchange"] == "NFO")
            & (instruments_df["name"] == symbol)
            & (instruments_df["instrument_type"].isin(["CE", "PE"]))
        ]
        if df_opts.empty:
            return None
        
        strikes = sorted(df_opts["strike"].unique())
        if not strikes:
            return None
        
        return min(strikes, key=lambda s: abs(s - spot_price))

    @staticmethod
    def resolve_strike_step(instruments_df: pd.DataFrame, symbol: str) -> float | None:
        """
        Resolves the strike step (difference between consecutive strikes).
        """
        from collections import Counter
        df_opts = instruments_df[
            (instruments_df["exchange"] == "NFO")
            & (instruments_df["name"] == symbol)
            & (instruments_df["instrument_type"].isin(["CE", "PE"]))
        ]
        if df_opts.empty:
            return None
        
        strikes = sorted(df_opts["strike"].unique())
        if len(strikes) < 2:
            return None
        
        diffs = [strikes[i+1] - strikes[i] for i in range(len(strikes)-1)]
        if not diffs:
            return None
        return Counter(diffs).most_common(1)[0][0]

    @staticmethod
    def resolve_tradable_contracts(
        instruments_df: pd.DataFrame,
        symbol: str,
        expiry: pd.Timestamp.date,
        option_type: str | None = None
    ) -> pd.DataFrame:
        """
        Returns a DataFrame of tradable contracts matching the symbol and expiry.
        """
        import datetime
        # Ensure expiry matches datetime.date
        if isinstance(expiry, str):
            expiry = pd.to_datetime(expiry).date()
        elif hasattr(expiry, "date"):
            expiry = expiry.date()
        
        df_opts = instruments_df[
            (instruments_df["exchange"] == "NFO")
            & (instruments_df["name"] == symbol)
            & (instruments_df["expiry"] == expiry)
        ]
        if option_type:
            df_opts = df_opts[df_opts["instrument_type"] == option_type]
        return df_opts

