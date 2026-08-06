from __future__ import annotations

import datetime
from dataclasses import dataclass
import numpy as np
import pandas as pd
from kiteconnect import KiteConnect

from src.utils import setup_logger, is_market_hours
from src.data_engine.instruments import InstrumentManager
from src.data_engine.quotes import get_quote_map

logger = setup_logger("ChainBuilder")


@dataclass
class OptionChainContract:
    tradingsymbol: str
    strike: float
    expiry: str
    instrument_type: str  # "CE" or "PE"
    ltp: float
    bid: float
    ask: float
    spread: float
    spread_pct: float
    volume: int
    oi: int
    oi_change: int
    itm_otm: str  # "ITM", "ATM", "OTM"
    is_liquid: bool
    price_change: float = 0.0
    price_change_pct: float = 0.0


def build_option_chain(
    kite: KiteConnect,
    instruments_df: pd.DataFrame,
    symbol: str,
    expiry: datetime.date | str | list[datetime.date | str],
    spot_price: float,
    range_steps: int = 15,
) -> list[OptionChainContract]:
    """
    Fetches the NIFTY option chain, normalizes contracts, removes illiquid ones,
    and identifies ATM/ITM/OTM states.
    """
    # 1. Resolve expiry and strike step
    step = InstrumentManager.resolve_strike_step(instruments_df, symbol)
    if step is None:
        step = 50.0  # Fallback for NIFTY

    atm_strike = InstrumentManager.resolve_atm_strike(instruments_df, symbol, spot_price)
    if atm_strike is None:
        atm_strike = round(spot_price / step) * step

    expiries_list = expiry if isinstance(expiry, list) else [expiry]
    all_filtered_rows = []

    for exp_val in expiries_list:
        if isinstance(exp_val, str):
            exp_date = pd.to_datetime(exp_val).date()
        elif hasattr(exp_val, "date"):
            exp_date = exp_val.date()
        else:
            exp_date = exp_val

        # 2. Get active contracts for symbol and expiry
        contracts_df = InstrumentManager.resolve_tradable_contracts(instruments_df, symbol, exp_date)
        if contracts_df.empty:
            continue

        # 3. Filter contracts to range of strikes around ATM to optimize API usage
        current_range = 5 if len(expiries_list) > 1 else range_steps
        min_strike = atm_strike - (current_range * step)
        max_strike = atm_strike + (current_range * step)
        
        filtered_df = contracts_df[
            (contracts_df["strike"].astype(float) >= min_strike)
            & (contracts_df["strike"].astype(float) <= max_strike)
        ].copy()

        if filtered_df.empty:
            filtered_df = contracts_df.copy()

        all_filtered_rows.append(filtered_df)

    if not all_filtered_rows:
        logger.warning(f"No option contracts found for {symbol} on expiries {expiries_list}")
        return []

    combined_df = pd.concat(all_filtered_rows).drop_duplicates(subset=["tradingsymbol"])

    # 4. Fetch quotes from Kite API
    trading_symbols = combined_df["tradingsymbol"].tolist()
    quote_keys = [f"NFO:{ts}" for ts in trading_symbols]
    
    logger.info(f"Fetching quotes for {len(quote_keys)} contracts for {symbol} option chain...")
    quote_map = get_quote_map(kite, quote_keys)
    allow_after_hours = not is_market_hours()

    # 5. Normalize and build chain
    chain_contracts = []
    for _, row in combined_df.iterrows():
        ts = row["tradingsymbol"]
        key = f"NFO:{ts}"
        q = quote_map.get(key, {})

        # Extract quote fields
        ltp = q.get("last_price")
        if ltp in (None, ""):
            ltp = (q.get("ohlc") or {}).get("close")
        ltp = float(ltp) if ltp not in (None, "") else 0.0

        ohlc_close = (q.get("ohlc") or {}).get("close")
        prev_close = float(ohlc_close) if ohlc_close not in (None, "") else 0.0
        price_change = ltp - prev_close if prev_close > 0 else 0.0
        price_change_pct = (price_change / prev_close) * 100.0 if prev_close > 0 else 0.0

        depth = q.get("depth") or {}
        buy_depth = depth.get("buy") or []
        sell_depth = depth.get("sell") or []
        bid = float(buy_depth[0].get("price", 0.0)) if buy_depth else 0.0
        ask = float(sell_depth[0].get("price", 0.0)) if sell_depth else 0.0

        volume = int(q.get("volume", 0) or 0)
        oi = int(q.get("oi", q.get("open_interest", 0)) or 0)
        oi_change = int(q.get("oi_change", 0) or 0)

        # Spread calculation
        spread = ask - bid
        if ltp > 0:
            spread_pct = (spread / ltp) * 100.0
        else:
            spread_pct = 99.0

        if allow_after_hours and ltp > 0 and (bid == 0.0 or ask == 0.0):
            bid = ltp
            ask = ltp
            spread = 0.0
            spread_pct = 0.0

        # Determine ITM / ATM / OTM
        strike = float(row["strike"])
        opt_type = row["instrument_type"]

        if abs(strike - atm_strike) < 0.1:
            itm_otm = "ATM"
        else:
            if opt_type == "CE":
                itm_otm = "ITM" if strike < atm_strike else "OTM"
            else:
                itm_otm = "ITM" if strike > atm_strike else "OTM"

        # Determine Liquidity
        # A contract is considered liquid if it has valid bid/ask or is within a reasonable spread limit
        is_liquid = True
        if ltp <= 0:
            is_liquid = False
        elif volume == 0 and oi < 50:
            is_liquid = False
        elif spread_pct > 20.0 and not (allow_after_hours and spread_pct == 0.0):
            is_liquid = False
        elif bid <= 0 or ask <= 0:
            # Under live conditions, having no bid or ask is highly illiquid
            if not allow_after_hours:
                is_liquid = False

        # Resolve the expiry date for this specific contract row
        row_expiry = row.get("expiry")
        if isinstance(row_expiry, str):
            row_expiry_date = pd.to_datetime(row_expiry).date()
        elif hasattr(row_expiry, "date"):
            row_expiry_date = row_expiry.date()
        else:
            row_expiry_date = row_expiry
        row_expiry_str = row_expiry_date.strftime("%Y-%m-%d") if row_expiry_date else ""

        contract = OptionChainContract(
            tradingsymbol=ts,
            strike=strike,
            expiry=row_expiry_str,
            instrument_type=opt_type,
            ltp=round(ltp, 2),
            bid=round(bid, 2),
            ask=round(ask, 2),
            spread=round(spread, 2),
            spread_pct=round(spread_pct, 2),
            volume=volume,
            oi=oi,
            oi_change=oi_change,
            itm_otm=itm_otm,
            is_liquid=is_liquid,
            price_change=round(price_change, 2),
            price_change_pct=round(price_change_pct, 2),
        )
        chain_contracts.append(contract)

    # Sort chain by strike and then instrument type (CE first then PE, or vice versa)
    chain_contracts = sorted(chain_contracts, key=lambda x: (x.strike, 0 if x.instrument_type == "CE" else 1))
    return chain_contracts
