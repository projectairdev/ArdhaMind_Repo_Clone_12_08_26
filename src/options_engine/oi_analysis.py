from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from src.options_engine.chain_builder import OptionChainContract


@dataclass
class OIStrikeMetrics:
    strike: float
    ce_oi: int = 0
    pe_oi: int = 0
    ce_oi_change: int = 0
    pe_oi_change: int = 0
    ce_volume: int = 0
    pe_volume: int = 0


@dataclass
class OIBuildUp:
    long_buildup: List[float] = field(default_factory=list)
    short_buildup: List[float] = field(default_factory=list)
    long_unwinding: List[float] = field(default_factory=list)
    short_covering: List[float] = field(default_factory=list)


@dataclass
class OIAnalysisResult:
    pcr_oi: float
    pcr_volume: float
    highest_ce_oi_strike: float
    highest_ce_oi_value: int
    highest_pe_oi_strike: float
    highest_pe_oi_value: int
    highest_ce_oi_change_strike: float
    highest_ce_oi_change_value: int
    highest_pe_oi_change_strike: float
    highest_pe_oi_change_value: int
    call_writing_strikes: List[float] = field(default_factory=list)
    put_writing_strikes: List[float] = field(default_factory=list)
    ce_build_ups: OIBuildUp = field(default_factory=OIBuildUp)
    pe_build_ups: OIBuildUp = field(default_factory=OIBuildUp)
    oi_distribution: List[OIStrikeMetrics] = field(default_factory=list)
    oi_concentration_ce: List[float] = field(default_factory=list)
    oi_concentration_pe: List[float] = field(default_factory=list)
    oi_shift_description: str = ""


def analyze_oi(chain: List[OptionChainContract]) -> OIAnalysisResult:
    """
    Performs pure open interest (OI) calculations and analyzes distribution,
    concentration, shift, writing activity, and build-up behaviors.
    """
    if not chain:
        return OIAnalysisResult(
            pcr_oi=0.0,
            pcr_volume=0.0,
            highest_ce_oi_strike=0.0,
            highest_ce_oi_value=0,
            highest_pe_oi_strike=0.0,
            highest_pe_oi_value=0,
            highest_ce_oi_change_strike=0.0,
            highest_ce_oi_change_value=0,
            highest_pe_oi_change_strike=0.0,
            highest_pe_oi_change_value=0,
        )

    # 1. Group by strike for distribution and totals
    strikes_map: Dict[float, OIStrikeMetrics] = {}
    total_ce_oi = 0
    total_pe_oi = 0
    total_ce_vol = 0
    total_pe_vol = 0

    highest_ce_oi_val = -1
    highest_ce_oi_strk = 0.0
    highest_pe_oi_val = -1
    highest_pe_oi_strk = 0.0

    highest_ce_oi_chg_val = -999999999
    highest_ce_oi_chg_strk = 0.0
    highest_pe_oi_chg_val = -999999999
    highest_pe_oi_chg_strk = 0.0

    ce_contracts: List[OptionChainContract] = []
    pe_contracts: List[OptionChainContract] = []

    for c in chain:
        strike = c.strike
        if strike not in strikes_map:
            strikes_map[strike] = OIStrikeMetrics(strike=strike)
        
        metrics = strikes_map[strike]
        if c.instrument_type == "CE":
            ce_contracts.append(c)
            metrics.ce_oi = c.oi
            metrics.ce_oi_change = c.oi_change
            metrics.ce_volume = c.volume
            total_ce_oi += c.oi
            total_ce_vol += c.volume

            if c.oi > highest_ce_oi_val:
                highest_ce_oi_val = c.oi
                highest_ce_oi_strk = strike
            
            if c.oi_change > highest_ce_oi_chg_val:
                highest_ce_oi_chg_val = c.oi_change
                highest_ce_oi_chg_strk = strike
        else:
            pe_contracts.append(c)
            metrics.pe_oi = c.oi
            metrics.pe_oi_change = c.oi_change
            metrics.pe_volume = c.volume
            total_pe_oi += c.oi
            total_pe_vol += c.volume

            if c.oi > highest_pe_oi_val:
                highest_pe_oi_val = c.oi
                highest_pe_oi_strk = strike

            if c.oi_change > highest_pe_oi_chg_val:
                highest_pe_oi_chg_val = c.oi_change
                highest_pe_oi_chg_strk = strike

    # 2. PCR Calculations
    pcr_oi = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 0.0
    pcr_vol = total_pe_vol / total_ce_vol if total_ce_vol > 0 else 0.0

    # 3. OI Concentration (Top 5 CE and PE strikes by OI)
    sorted_ce_by_oi = sorted(ce_contracts, key=lambda x: x.oi, reverse=True)
    sorted_pe_by_oi = sorted(pe_contracts, key=lambda x: x.oi, reverse=True)
    
    oi_concentration_ce = [c.strike for c in sorted_ce_by_oi[:5]]
    oi_concentration_pe = [c.strike for c in sorted_pe_by_oi[:5]]

    # 4. Build-ups Analysis
    ce_buildup = OIBuildUp()
    pe_buildup = OIBuildUp()

    def categorize_buildup(c: OptionChainContract, buildup_obj: OIBuildUp):
        # We classify based on change in open interest and price change
        if c.oi_change > 0:
            if c.price_change > 0:
                buildup_obj.long_buildup.append(c.strike)
            elif c.price_change < 0:
                buildup_obj.short_buildup.append(c.strike)
        elif c.oi_change < 0:
            if c.price_change < 0:
                buildup_obj.long_unwinding.append(c.strike)
            elif c.price_change > 0:
                buildup_obj.short_covering.append(c.strike)

    for c in ce_contracts:
        categorize_buildup(c, ce_buildup)
    for c in pe_contracts:
        categorize_buildup(c, pe_buildup)

    # 5. Call & Put Writing (Positive OI change & Price decrease, i.e., Short Build-up, sorted by OI change desc)
    ce_writing = [c for c in ce_contracts if c.oi_change > 0 and c.price_change <= 0]
    ce_writing_sorted = sorted(ce_writing, key=lambda x: x.oi_change, reverse=True)
    call_writing_strikes = [c.strike for c in ce_writing_sorted[:5]]

    pe_writing = [c for c in pe_contracts if c.oi_change > 0 and c.price_change <= 0]
    pe_writing_sorted = sorted(pe_writing, key=lambda x: x.oi_change, reverse=True)
    put_writing_strikes = [c.strike for c in pe_writing_sorted[:5]]

    # 6. OI Shift description
    # Highlight where the highest positive OI change occurred
    oi_shift_desc = f"Call OI build-up concentrated at {highest_ce_oi_chg_strk} (Chg: {highest_ce_oi_chg_val}). " \
                    f"Put OI build-up concentrated at {highest_pe_oi_chg_strk} (Chg: {highest_pe_oi_chg_val})."

    # Sorted list of strike metrics
    oi_distribution = [strikes_map[s] for s in sorted(strikes_map.keys())]

    return OIAnalysisResult(
        pcr_oi=round(pcr_oi, 3),
        pcr_volume=round(pcr_vol, 3),
        highest_ce_oi_strike=highest_ce_oi_strk,
        highest_ce_oi_value=max(0, highest_ce_oi_val),
        highest_pe_oi_strike=highest_pe_oi_strk,
        highest_pe_oi_value=max(0, highest_pe_oi_val),
        highest_ce_oi_change_strike=highest_ce_oi_chg_strk,
        highest_ce_oi_change_value=max(0, highest_ce_oi_chg_val),
        highest_pe_oi_change_strike=highest_pe_oi_chg_strk,
        highest_pe_oi_change_value=max(0, highest_pe_oi_chg_val),
        call_writing_strikes=call_writing_strikes,
        put_writing_strikes=put_writing_strikes,
        ce_build_ups=ce_buildup,
        pe_build_ups=pe_buildup,
        oi_distribution=oi_distribution,
        oi_concentration_ce=oi_concentration_ce,
        oi_concentration_pe=oi_concentration_pe,
        oi_shift_description=oi_shift_desc,
    )
