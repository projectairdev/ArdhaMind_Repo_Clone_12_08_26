"""
Real-time Black-Scholes European Options Greeks Analytics Engine.
Calculates Delta (Δ), Gamma (Γ), Theta (Θ), and Vega (V) for European options on NIFTY index.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class OptionGreeks:
    delta: float
    gamma: float
    theta: float
    vega: float
    iv: float


def normal_cdf(x: float) -> float:
    """Standard normal cumulative distribution function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def normal_pdf(x: float) -> float:
    """Standard normal probability density function."""
    return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x * x)


def calculate_black_scholes_greeks(
    spot: float,
    strike: float,
    time_to_expiry_years: float,
    volatility: float,
    risk_free_rate: float = 0.065,
    option_type: str = "CE",
) -> Optional[OptionGreeks]:
    """
    Computes analytical Black-Scholes Greeks for European options.

    :param spot: Current underlying price (S)
    :param strike: Option strike price (K)
    :param time_to_expiry_years: Time to expiration in years (T)
    :param volatility: Implied volatility as annual decimal (sigma, e.g. 0.13 for 13%)
    :param risk_free_rate: Annual risk-free interest rate (r, default 0.065 / 6.5%)
    :param option_type: 'CE' for Call or 'PE' for Put
    :return: OptionGreeks dataclass or None if inputs invalid
    """
    if spot <= 0 or strike <= 0:
        return None

    S = float(spot)
    K = float(strike)
    # Enforce strict 10^-6 floor on time-to-expiry to prevent zero-DTE expiry afternoon division-by-zero crashes
    T = max(float(time_to_expiry_years), 1e-6)
    # Enforce strict 10^-4 floor on volatility
    sigma = max(float(volatility), 1e-4)
    r = float(risk_free_rate)
    is_call = str(option_type).upper() in ("CE", "CALL", "C")

    try:
        sqrt_T = math.sqrt(T)
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt_T)
        d2 = d1 - sigma * sqrt_T

        nd1 = normal_cdf(d1)
        nd2 = normal_cdf(d2)
        n_prime_d1 = normal_pdf(d1)
        discount = math.exp(-r * T)

        # 1. Delta (Δ)
        if is_call:
            delta = nd1
        else:
            delta = nd1 - 1.0

        # 2. Gamma (Γ)
        gamma = n_prime_d1 / (S * sigma * sqrt_T)

        # 3. Theta (Θ) - scaled to 1 calendar day (divide by 365)
        if is_call:
            theta_annual = -(S * n_prime_d1 * sigma) / (2.0 * sqrt_T) - r * K * discount * nd2
        else:
            theta_annual = -(S * n_prime_d1 * sigma) / (2.0 * sqrt_T) + r * K * discount * (1.0 - nd2)
        theta_daily = theta_annual / 365.0

        # 4. Vega (V) - scaled to 1% change in IV (divide by 100)
        vega_annual = S * sqrt_T * n_prime_d1
        vega_1pct = vega_annual / 100.0

        return OptionGreeks(
            delta=round(delta, 4),
            gamma=round(gamma, 6),
            theta=round(theta_daily, 2),
            vega=round(vega_1pct, 2),
            iv=round(sigma * 100.0, 2),
        )
    except Exception:
        return None
