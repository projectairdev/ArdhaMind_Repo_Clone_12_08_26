from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any
import numpy as np
from src.options_engine.chain_builder import OptionChainContract
from src.configuration_engine.runtime import Config


@dataclass
class ContractLiquidity:
    tradingsymbol: str
    strike: float
    instrument_type: str
    bid_ask_spread: float
    bid_ask_spread_pct: float
    volume_score: float
    oi_score: float
    liquidity_score: float
    tradability_score: float
    is_suitable: bool


@dataclass
class LiquiditySummary:
    average_spread_pct: float
    total_volume: int
    total_oi: int
    liquid_contracts_count: int
    unsuitable_contracts_count: int
    overall_liquidity_score: float
    contract_metrics: List[ContractLiquidity] = field(default_factory=list)


def analyze_liquidity(
    chain: List[OptionChainContract],
    atm_strike: float,
    strike_step: float,
) -> LiquiditySummary:
    """
    Computes liquidity and tradability metrics for each contract in the chain,
    filters unsuitable contracts, and returns a detailed summary.
    """
    if not chain:
        return LiquiditySummary(
            average_spread_pct=0.0,
            total_volume=0,
            total_oi=0,
            liquid_contracts_count=0,
            unsuitable_contracts_count=0,
            overall_liquidity_score=0.0,
        )

    contract_metrics = []
    total_spread_pct = 0.0
    valid_spread_count = 0
    total_vol = 0
    total_oi = 0
    liquid_count = 0
    unsuitable_count = 0

    # Calculate individual metrics
    for c in chain:
        bid_ask_spread = max(0.0, c.ask - c.bid)
        bid_ask_spread_pct = c.spread_pct

        if c.ltp > 0:
            total_spread_pct += bid_ask_spread_pct
            valid_spread_count += 1

        total_vol += c.volume
        total_oi += c.oi

        # Log scale volume score (0 - 100)
        # reference: log(100,000) is approx 11.5
        volume_score = min(100.0, float(np.log1p(c.volume) / np.log1p(100000)) * 100.0)

        # Log scale OI score (0 - 100)
        # reference: log(500,000) is approx 13.1
        oi_score = min(100.0, float(np.log1p(c.oi) / np.log1p(500000)) * 100.0)

        # Spread score (0 - 100)
        # 0% spread = 100 score, 10% spread = 0 score
        spread_score = max(0.0, 100.0 - (bid_ask_spread_pct * 10.0))

        # Overall liquidity score is weighted: 50% Spread, 30% Volume, 20% OI
        liquidity_score = (spread_score * 0.5) + (volume_score * 0.3) + (oi_score * 0.2)

        # Tradability score penalizes strikes far from ATM
        distance_steps = abs(c.strike - atm_strike) / (strike_step if strike_step > 0 else 50.0)
        # Penalty: 5 points per strike step away from ATM, max penalty of 50 points
        distance_penalty = min(50.0, distance_steps * 5.0)
        tradability_score = max(0.0, liquidity_score - distance_penalty)

        # Suitability Filter
        is_suitable = True
        if not c.is_liquid:
            is_suitable = False
        elif c.ltp < Config.MIN_OPTION_LTP or c.ltp > Config.MAX_OPTION_LTP:
            is_suitable = False
        elif bid_ask_spread_pct > 20.0:
            is_suitable = False
        elif liquidity_score < 25.0:
            is_suitable = False

        if c.is_liquid:
            liquid_count += 1
        if not is_suitable:
            unsuitable_count += 1

        metric = ContractLiquidity(
            tradingsymbol=c.tradingsymbol,
            strike=c.strike,
            instrument_type=c.instrument_type,
            bid_ask_spread=round(bid_ask_spread, 2),
            bid_ask_spread_pct=round(bid_ask_spread_pct, 2),
            volume_score=round(volume_score, 2),
            oi_score=round(oi_score, 2),
            liquidity_score=round(liquidity_score, 2),
            tradability_score=round(tradability_score, 2),
            is_suitable=is_suitable,
        )
        contract_metrics.append(metric)

    # Compute aggregate metrics
    avg_spread_pct = total_spread_pct / valid_spread_count if valid_spread_count > 0 else 0.0
    overall_liq = np.mean([m.liquidity_score for m in contract_metrics]) if contract_metrics else 0.0

    return LiquiditySummary(
        average_spread_pct=round(avg_spread_pct, 2),
        total_volume=total_vol,
        total_oi=total_oi,
        liquid_contracts_count=liquid_count,
        unsuitable_contracts_count=unsuitable_count,
        overall_liquidity_score=round(float(overall_liq), 2),
        contract_metrics=contract_metrics,
    )
