from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any
from src.options_engine.chain_builder import OptionChainContract
from src.options_engine.liquidity import LiquiditySummary, ContractLiquidity
from src.options_engine.iv import IVAnalysisResult, ContractIV


@dataclass
class RankedStrike:
    tradingsymbol: str
    strike: float
    instrument_type: str
    distance_from_atm: float
    oi: int
    volume: int
    spread_pct: float
    iv: float
    tradability_score: float
    ranking_score: float
    expiry: str = ""
    rank: int = 0


def rank_strikes(
    chain: List[OptionChainContract],
    liquidity_summary: LiquiditySummary,
    iv_analysis: IVAnalysisResult,
    atm_strike: float,
) -> List[RankedStrike]:
    """
    Ranks nearby option strikes by integrating liquidity metrics, spread, volume, OI, IV,
    and distance from the ATM. Returns RankedStrike dataclass objects.
    """
    # Create fast lookup maps by trading symbol
    liq_map: Dict[str, ContractLiquidity] = {m.tradingsymbol: m for m in liquidity_summary.contract_metrics}
    iv_map: Dict[str, ContractIV] = {m.tradingsymbol: m for m in iv_analysis.contract_ivs}

    ranked_list: List[RankedStrike] = []

    for c in chain:
        ts = c.tradingsymbol
        liq_metrics = liq_map.get(ts)
        iv_metrics = iv_map.get(ts)

        # Skip if we don't have basic liquidity data or the contract is totally illiquid
        if not liq_metrics:
            continue

        distance = abs(c.strike - atm_strike)
        iv_val = iv_metrics.iv if iv_metrics else 0.0

        # We base our ranking score primarily on the tradability score from the liquidity module,
        # but we can also adjust it. Let's make the ranking score equal to the tradability score.
        ranking_score = liq_metrics.tradability_score

        # Only rank suitable contracts (or those with positive tradability)
        if liq_metrics.is_suitable and ranking_score > 0:
            ranked_list.append(
                RankedStrike(
                    tradingsymbol=ts,
                    strike=c.strike,
                    instrument_type=c.instrument_type,
                    distance_from_atm=distance,
                    oi=c.oi,
                    volume=c.volume,
                    spread_pct=c.spread_pct,
                    iv=iv_val,
                    tradability_score=liq_metrics.tradability_score,
                    ranking_score=round(ranking_score, 2),
                    expiry=c.expiry,
                )
            )

    # Sort descending by ranking score
    ranked_list = sorted(ranked_list, key=lambda x: x.ranking_score, reverse=True)

    # Assign ranks
    for idx, item in enumerate(ranked_list):
        item.rank = idx + 1

    return ranked_list
