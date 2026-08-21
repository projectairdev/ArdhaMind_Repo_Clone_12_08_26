from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict
import numpy as np
from src.options_engine.chain_builder import OptionChainContract


@dataclass
class StrikePain:
    strike: float
    call_pain: float
    put_pain: float
    total_pain: float


@dataclass
class MaxPainResult:
    max_pain_strike: float
    pain_distribution: List[StrikePain]
    expected_pin_zone: List[float]


def calculate_max_pain(chain: List[Any]) -> MaxPainResult:
    """
    Computes the Option Max Pain Strike, the distribution of pain across strikes,
    and identifies the expected pin zone where writer pain is minimized.
    """
    if not chain:
        return MaxPainResult(
            max_pain_strike=0.0,
            pain_distribution=[],
            expected_pin_zone=[],
        )

    # Get unique strike prices
    def _strike(c: Any) -> float:
        return float(getattr(c, "strike", None) if hasattr(c, "strike") else c.get("strike", 0))

    def _itype(c: Any) -> str:
        return str(getattr(c, "instrument_type", None) if hasattr(c, "instrument_type") else (c.get("instrument_type") or c.get("option_type", ""))).upper()

    def _oi(c: Any) -> float:
        return float(getattr(c, "oi", None) if hasattr(c, "oi") else c.get("oi", 0))

    strikes = sorted(list({_strike(c) for c in chain if _strike(c) > 0}))
    if not strikes:
        return MaxPainResult(
            max_pain_strike=0.0,
            pain_distribution=[],
            expected_pin_zone=[],
        )

    # Compute pain for each potential expiry strike S
    pain_distribution: List[StrikePain] = []
    min_pain = float("inf")
    max_pain_strike = strikes[0]

    for s in strikes:
        call_pain = 0.0
        put_pain = 0.0
        
        for c in chain:
            c_strike = _strike(c)
            c_type = _itype(c)
            c_oi = _oi(c)
            # Pain is only experienced by writers when the contract is ITM at expiry S
            if c_type == "CE":
                if s > c_strike:
                    call_pain += (s - c_strike) * c_oi
            else:
                if s < c_strike:
                    put_pain += (c_strike - s) * c_oi

        total_pain = call_pain + put_pain
        pain_distribution.append(
            StrikePain(
                strike=s,
                call_pain=round(call_pain, 2),
                put_pain=round(put_pain, 2),
                total_pain=round(total_pain, 2),
            )
        )

        if total_pain < min_pain:
            min_pain = total_pain
            max_pain_strike = s

    # Expected pin zone: strikes with total pain within 15% of the minimum pain,
    # or the max pain strike and its immediate neighboring strikes
    # Let's include the max pain strike and any strike with total pain close to min_pain (within 15%)
    pin_zone_strikes = []
    threshold = min_pain * 1.15 if min_pain > 0 else 0.0
    for p in pain_distribution:
        if p.total_pain <= threshold or p.strike == max_pain_strike:
            pin_zone_strikes.append(p.strike)

    # If the threshold is too tight or wide, make sure we at least return the max pain strike
    if max_pain_strike not in pin_zone_strikes:
        pin_zone_strikes.append(max_pain_strike)

    return MaxPainResult(
        max_pain_strike=max_pain_strike,
        pain_distribution=sorted(pain_distribution, key=lambda x: x.strike),
        expected_pin_zone=sorted(list(set(pin_zone_strikes))),
    )
