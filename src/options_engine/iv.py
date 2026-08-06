from __future__ import annotations

import datetime
import math
from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np
from src.options_engine.chain_builder import OptionChainContract


@dataclass
class ContractIV:
    tradingsymbol: str
    strike: float
    instrument_type: str
    iv: float  # as percentage, e.g. 15.4 for 15.4%


@dataclass
class IVAnalysisResult:
    atm_iv: float
    average_iv: float
    iv_percentile: float
    expected_move: float
    iv_classification: str  # "LOW", "NORMAL", "HIGH", "EXTREME"
    contract_ivs: List[ContractIV] = field(default_factory=list)


def normal_cdf(x: float) -> float:
    """Standard normal cumulative distribution function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def black_scholes_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: str,
) -> float:
    """Computes the Black-Scholes price of a European option."""
    if T <= 0 or sigma <= 0:
        return max(0.0, S - K) if option_type == "CE" else max(0.0, K - S)

    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    if option_type == "CE":
        return S * normal_cdf(d1) - K * math.exp(-r * T) * normal_cdf(d2)
    else:
        return K * math.exp(-r * T) * normal_cdf(-d2) - S * normal_cdf(-d1)


def calculate_implied_volatility(
    price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: str,
) -> float:
    """Computes the Implied Volatility using Bisection search."""
    # Check intrinsic value
    intrinsic = max(0.0, S - K) if option_type == "CE" else max(0.0, K - S)
    if price <= intrinsic + 0.05:
        return 0.0

    low = 0.0001
    high = 5.0  # Max 500% IV
    
    for _ in range(50):
        mid = (low + high) / 2.0
        mid_price = black_scholes_price(S, K, T, r, mid, option_type)
        if abs(mid_price - price) < 0.01:
            return mid * 100.0  # Return as percentage
        if mid_price > price:
            high = mid
        else:
            low = mid

    return ((low + high) / 2.0) * 100.0


def analyze_iv(
    chain: List[OptionChainContract],
    spot_price: float,
    atm_strike: float,
    expiry_date: datetime.date,
    today_date: Optional[datetime.date] = None,
    r: float = 0.07,
    historical_ivs: Optional[List[float]] = None,
) -> IVAnalysisResult:
    """
    Analyzes Implied Volatility (IV) across the option chain.
    Calculates ATM IV, Average IV, IV Percentile, Expected Move, and IV Classification.
    """
    if today_date is None:
        today_date = datetime.date.today()

    dte = (expiry_date - today_date).days
    # Use minimum of 0.5 days to avoid division by zero
    T = max(0.5, float(dte)) / 365.0

    if not chain or spot_price <= 0:
        return IVAnalysisResult(
            atm_iv=0.0,
            average_iv=0.0,
            iv_percentile=50.0,
            expected_move=0.0,
            iv_classification="NORMAL",
        )

    contract_ivs = []
    atm_ivs = []
    all_ivs = []

    for c in chain:
        # Resolve contract-specific T
        try:
            import pandas as pd
            if isinstance(c.expiry, str):
                c_expiry_date = pd.to_datetime(c.expiry).date()
            elif hasattr(c.expiry, "date"):
                c_expiry_date = c.expiry.date()
            else:
                c_expiry_date = c.expiry
        except Exception:
            c_expiry_date = expiry_date

        c_dte = (c_expiry_date - today_date).days
        c_T = max(0.5, float(c_dte)) / 365.0

        # Calculate implied volatility for each contract
        iv_val = calculate_implied_volatility(
            price=c.ltp,
            S=spot_price,
            K=c.strike,
            T=c_T,
            r=r,
            option_type=c.instrument_type,
        )
        
        # If the bisection failed or price is too low, we might get 0.0. Only include valid non-zero IVs
        if iv_val > 0:
            contract_ivs.append(
                ContractIV(
                    tradingsymbol=c.tradingsymbol,
                    strike=c.strike,
                    instrument_type=c.instrument_type,
                    iv=round(iv_val, 2),
                )
            )
            all_ivs.append(iv_val)
            
            # ATM IV: average IV of contracts at the ATM strike
            if abs(c.strike - atm_strike) < 0.1:
                atm_ivs.append(iv_val)

    # Resolve ATM IV
    if atm_ivs:
        atm_iv = float(np.mean(atm_ivs))
    else:
        # Fallback if ATM strike doesn't have valid IV: average of nearest strikes
        nearest_ivs = [c_iv.iv for c_iv in contract_ivs if abs(c_iv.strike - atm_strike) <= (100.0 * 2)]
        atm_iv = float(np.mean(nearest_ivs)) if nearest_ivs else 15.0

    # Resolve Average IV
    average_iv = float(np.mean(all_ivs)) if all_ivs else atm_iv

    # IV Classification
    if atm_iv < 12.0:
        iv_class = "LOW"
    elif atm_iv < 18.0:
        iv_class = "NORMAL"
    elif atm_iv < 25.0:
        iv_class = "HIGH"
    else:
        iv_class = "EXTREME"

    # IV Percentile
    if historical_ivs:
        arr = np.array(historical_ivs)
        iv_pct = float((arr <= atm_iv).mean() * 100.0)
    else:
        # If no history is provided, we calibrate relative to normal NIFTY VIX range (10.0 to 24.0)
        min_vix = 10.0
        max_vix = 24.0
        pct = ((atm_iv - min_vix) / (max_vix - min_vix)) * 100.0
        iv_pct = float(np.clip(pct, 0.0, 100.0))

    # Expected Move: Spot * IV * sqrt(T)
    expected_move = spot_price * (atm_iv / 100.0) * math.sqrt(T)

    return IVAnalysisResult(
        atm_iv=round(atm_iv, 2),
        average_iv=round(average_iv, 2),
        iv_percentile=round(iv_pct, 2),
        expected_move=round(expected_move, 2),
        iv_classification=iv_class,
        contract_ivs=contract_ivs,
    )
