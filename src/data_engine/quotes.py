from __future__ import annotations

from typing import Dict, List, Optional, Any
import pandas as pd
from kiteconnect import KiteConnect
from src.config_engine import Config
from src.utils import call_with_retry, setup_logger
from src.data_engine.instruments import get_fo_underlying_symbols, get_symbol_sector

logger = setup_logger("Quotes")


def get_quote_map(kite: Any, keys: List[str]) -> Dict[str, dict]:
    if not keys:
        return {}
    from src.broker.interfaces.broker_interface import IBrokerGateway
    from src.broker.services.broker_service import BrokerService
    if isinstance(kite, (IBrokerGateway, BrokerService)):
        return call_with_retry(kite.get_quote, keys)
    return call_with_retry(kite.quote, keys)


def get_ltp_map(kite: Any, keys: List[str]) -> Dict[str, dict]:
    if not keys:
        return {}
    from src.broker.interfaces.broker_interface import IBrokerGateway
    from src.broker.services.broker_service import BrokerService
    if isinstance(kite, (IBrokerGateway, BrokerService)):
        return call_with_retry(kite.get_ltp, keys)
    return call_with_retry(kite.ltp, keys)


def build_market_snapshot(
    kite: KiteConnect,
    instruments_df: pd.DataFrame,
    symbols: Optional[List[str]] = None,
) -> pd.DataFrame:
    valid_symbols = symbols or get_fo_underlying_symbols(instruments_df)
    if not valid_symbols:
        return pd.DataFrame()

    quote_keys = [f"NSE:{s}" for s in valid_symbols]
    rows = []
    chunk_size = 200

    for i in range(0, len(quote_keys), chunk_size):
        chunk = quote_keys[i:i + chunk_size]
        try:
            quotes = get_quote_map(kite, chunk)
        except Exception as exc:
            logger.warning(f"Market snapshot chunk failed ({i}:{i + chunk_size}): {exc}")
            continue

        for key, q in quotes.items():
            try:
                symbol = key.split(":")[1]
                ltp = q.get("last_price")
                prev_close = q.get("ohlc", {}).get("close")
                volume = q.get("volume", 0)

                if ltp is None or prev_close is None or prev_close == 0:
                    continue

                rows.append(
                    {
                        "symbol": symbol,
                        "sector": get_symbol_sector(symbol),
                        "pct_change": ((float(ltp) - float(prev_close)) / float(prev_close)) * 100.0,
                        "volume": int(volume) if volume is not None else 0,
                        "ltp": float(ltp),
                    }
                )
            except Exception as exc:
                logger.warning(f"Bad market snapshot row for {key}: {exc}")

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    return df[
        (df["ltp"] > Config.MIN_STOCK_LTP)
        & (df["volume"] > (Config.MIN_STOCK_VOLUME_OPTIONS // 2))
    ].copy()
