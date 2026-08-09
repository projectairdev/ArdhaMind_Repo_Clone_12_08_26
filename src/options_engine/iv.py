from __future__ import annotations

import datetime
import math
from dataclasses import dataclass, field
from typing import List, Optional

from src.options_engine.chain_builder import OptionChainContract


@dataclass
class IVSolverResult:
    iv: Optional[float]
    solver_status: str
    iterations: int
    convergence_error: Optional[float]
    reason: Optional[str] = None


@dataclass
class ContractIV:
    tradingsymbol: str
    strike: float
    instrument_type: str
    iv: float
    solver_status: str = "CONVERGED"
    iterations: int = 0
    convergence_error: Optional[float] = None


@dataclass
class IVAnalysisResult:
    atm_iv: Optional[float]
    average_iv: Optional[float]
    iv_percentile: Optional[float]
    expected_move: Optional[float]
    iv_classification: str
    contract_ivs: List[ContractIV] = field(default_factory=list)
    status: str = "UNAVAILABLE"
    reason: Optional[str] = None


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def black_scholes_price(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    kind = str(option_type).upper()
    if S <= 0 or K <= 0 or T <= 0 or sigma <= 0 or kind not in {"CE", "PE"}:
        raise ValueError("Black-Scholes inputs must be positive and option type must be CE or PE")
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    if kind == "CE":
        return S * normal_cdf(d1) - K * math.exp(-r * T) * normal_cdf(d2)
    return K * math.exp(-r * T) * normal_cdf(-d2) - S * normal_cdf(-d1)


def solve_implied_volatility(
    price: float,
    S: float,
    K: float,
    T: float,
    r: Optional[float],
    option_type: str,
    tolerance: float = 0.005,
    max_iterations: int = 100,
    lower_sigma: float = 0.0001,
    upper_sigma: float = 5.0,
) -> IVSolverResult:
    """Bounded bisection solver with explicit rejection and convergence state."""
    kind = str(option_type).upper()
    values = (price, S, K, T)
    if r is None:
        return IVSolverResult(None, "UNAVAILABLE", 0, None, "MISSING_RISK_FREE_RATE")
    if any(not isinstance(value, (int, float)) or not math.isfinite(float(value)) for value in values):
        return IVSolverResult(None, "INVALID_INPUT", 0, None, "NON_FINITE_INPUT")
    if price <= 0 or S <= 0 or K <= 0:
        return IVSolverResult(None, "INVALID_INPUT", 0, None, "NON_POSITIVE_PRICE_SPOT_OR_STRIKE")
    if T <= 0:
        return IVSolverResult(None, "EXPIRED", 0, None, "EXPIRED_CONTRACT")
    if kind not in {"CE", "PE"}:
        return IVSolverResult(None, "INVALID_INPUT", 0, None, "INVALID_OPTION_TYPE")
    discounted_strike = K * math.exp(-float(r) * T)
    lower_bound = max(0.0, S - discounted_strike) if kind == "CE" else max(0.0, discounted_strike - S)
    upper_bound = S if kind == "CE" else discounted_strike
    if price < lower_bound - tolerance or price > upper_bound + tolerance:
        return IVSolverResult(None, "INVALID_INPUT", 0, None, "IMPOSSIBLE_OPTION_PRICE")
    low, high = lower_sigma, upper_sigma
    low_price = black_scholes_price(S, K, T, float(r), low, kind)
    high_price = black_scholes_price(S, K, T, float(r), high, kind)
    if price < low_price - tolerance or price > high_price + tolerance:
        return IVSolverResult(None, "NON_CONVERGENCE", 0, min(abs(price - low_price), abs(price - high_price)), "PRICE_OUTSIDE_SOLVER_BOUNDS")
    error: Optional[float] = None
    for iteration in range(1, max_iterations + 1):
        mid = (low + high) / 2.0
        calculated = black_scholes_price(S, K, T, float(r), mid, kind)
        error = abs(calculated - price)
        if error <= tolerance:
            return IVSolverResult(round(mid * 100.0, 4), "CONVERGED", iteration, error)
        if calculated > price:
            high = mid
        else:
            low = mid
    return IVSolverResult(None, "NON_CONVERGENCE", max_iterations, error, "ITERATION_LIMIT_REACHED")


def calculate_implied_volatility(price: float, S: float, K: float, T: float, r: float, option_type: str) -> float:
    """Backward-compatible numeric wrapper; invalid inputs return 0, never a guessed IV."""
    result = solve_implied_volatility(price, S, K, T, r, option_type)
    return float(result.iv) if result.iv is not None else 0.0


def analyze_iv(
    chain: List[OptionChainContract],
    spot_price: float,
    atm_strike: float,
    expiry_date: datetime.date,
    today_date: Optional[datetime.date] = None,
    r: Optional[float] = None,
    historical_ivs: Optional[List[float]] = None,
) -> IVAnalysisResult:
    if r is None:
        return IVAnalysisResult(None, None, None, None, "UNAVAILABLE", status="UNAVAILABLE", reason="MISSING_RISK_FREE_RATE")
    if today_date is None:
        today_date = datetime.date.today()
    if not chain or spot_price <= 0:
        return IVAnalysisResult(None, None, None, None, "UNAVAILABLE", status="UNAVAILABLE", reason="MISSING_CHAIN_OR_SPOT")
    contract_ivs: List[ContractIV] = []
    atm_ivs: List[float] = []
    all_ivs: List[float] = []
    for contract in chain:
        try:
            expiry = datetime.date.fromisoformat(str(contract.expiry)[:10])
        except (TypeError, ValueError):
            expiry = expiry_date
        T = (expiry - today_date).days / 365.0
        solved = solve_implied_volatility(contract.ltp, spot_price, contract.strike, T, r, contract.instrument_type)
        if solved.iv is None:
            continue
        contract_ivs.append(ContractIV(
            tradingsymbol=contract.tradingsymbol, strike=contract.strike,
            instrument_type=contract.instrument_type, iv=solved.iv,
            solver_status=solved.solver_status, iterations=solved.iterations,
            convergence_error=solved.convergence_error,
        ))
        all_ivs.append(solved.iv)
        if abs(contract.strike - atm_strike) < 0.1:
            atm_ivs.append(solved.iv)
    if not all_ivs:
        return IVAnalysisResult(None, None, None, None, "UNAVAILABLE", status="UNAVAILABLE", reason="NO_CONVERGED_CONTRACT_IV")
    atm_iv = sum(atm_ivs) / len(atm_ivs) if atm_ivs else None
    average_iv = sum(all_ivs) / len(all_ivs)
    if atm_iv is None:
        classification = "UNAVAILABLE"
        expected_move = None
    else:
        classification = "LOW" if atm_iv < 12.0 else "NORMAL" if atm_iv < 18.0 else "ELEVATED" if atm_iv < 25.0 else "HIGH"
        T = max((expiry_date - today_date).days / 365.0, 0.0)
        expected_move = spot_price * (atm_iv / 100.0) * math.sqrt(T) if T > 0 else None
    percentile = None
    if historical_ivs:
        valid_history = [value for value in historical_ivs if isinstance(value, (int, float)) and math.isfinite(value)]
        if valid_history and atm_iv is not None:
            percentile = sum(value <= atm_iv for value in valid_history) / len(valid_history) * 100.0
    return IVAnalysisResult(
        round(atm_iv, 4) if atm_iv is not None else None,
        round(average_iv, 4), round(percentile, 2) if percentile is not None else None,
        round(expected_move, 2) if expected_move is not None else None,
        classification, contract_ivs=contract_ivs, status="AVAILABLE",
    )
