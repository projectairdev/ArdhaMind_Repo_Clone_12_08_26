from __future__ import annotations

from src.models.market_context import MarketContext
from src.models.option_context import OptionContext
from src.models.trade_context import ConfluenceContext


def analyze_confluence(
    market: MarketContext,
    options: OptionContext,
) -> ConfluenceContext:
    """
    Computes structural agreement between MarketContext (technical charts) and OptionContext (derivatives data).
    Strictly describes alignment only, with NO scoring or confidence metrics.
    """
    # 1. Trend Confluence
    trend_confluence = (market.trend_direction == options.market_option_bias)

    # 2. Option Confluence
    option_confluence = False
    pcr = options.pcr
    bias = options.market_option_bias
    if bias == "BULLISH" and pcr >= 1.0:
        option_confluence = True
    elif bias == "BEARISH" and pcr <= 1.0:
        option_confluence = True
    elif bias == "NEUTRAL" and (0.8 <= pcr <= 1.2):
        option_confluence = True

    # 3. Support & Resistance Alignment
    # We define alignment if a technical S/R level is within 100 points of an options S/R level
    sr_alignment = False
    aligned_s = False
    aligned_r = False
    
    threshold = 100.0  # 100 points for NIFTY is standard
    
    for tech_s in market.support_levels:
        for opt_s in options.support_strikes:
            if abs(tech_s - opt_s) <= threshold:
                aligned_s = True
                break
        if aligned_s:
            break
            
    for tech_r in market.resistance_levels:
        for opt_r in options.resistance_strikes:
            if abs(tech_r - opt_r) <= threshold:
                aligned_r = True
                break
        if aligned_r:
            break
            
    sr_alignment = aligned_s or aligned_r

    # 4. Volatility Alignment
    volatility_alignment = False
    tech_vol = market.volatility_state
    
    # Classify Options IV
    iv = options.atm_iv
    if iv <= 12.0:
        opt_vol_state = "LOW"
    elif iv <= 20.0:
        opt_vol_state = "NORMAL"
    elif iv <= 30.0:
        opt_vol_state = "HIGH"
    else:
        opt_vol_state = "EXTREME"
        
    volatility_alignment = (tech_vol == opt_vol_state)

    # 5. Liquidity Alignment
    liquidity_alignment = False
    liq_metrics = options.liquidity_metrics
    liq_score = liq_metrics.get("overall_liquidity_score", 100.0)
    avg_spread = liq_metrics.get("average_spread_pct", 0.0)
    
    if liq_score >= 50.0 and avg_spread <= 2.0:
        liquidity_alignment = True

    # 6. Overall Confluence
    alignments_count = sum([
        trend_confluence,
        option_confluence,
        sr_alignment,
        volatility_alignment,
        liquidity_alignment
    ])
    overall_confluence = (alignments_count >= 3)

    # Descriptive summary
    desc_parts = []
    if trend_confluence:
        desc_parts.append("Technical trend matches derivative bias.")
    if option_confluence:
        desc_parts.append("PCR aligns with options market bias.")
    if sr_alignment:
        desc_parts.append("Technical S/R aligns with derivative OI concentrations.")
    if volatility_alignment:
        desc_parts.append("Technical volatility matches options implied volatility state.")
    if liquidity_alignment:
        desc_parts.append("Option chain exhibits high liquidity with narrow spreads.")
        
    if not desc_parts:
        description = "No structural alignments observed between technical and option metrics."
    else:
        description = " ".join(desc_parts)

    return ConfluenceContext(
        trend_confluence=trend_confluence,
        option_confluence=option_confluence,
        sr_alignment=sr_alignment,
        volatility_alignment=volatility_alignment,
        liquidity_alignment=liquidity_alignment,
        overall_confluence=overall_confluence,
        description=description,
    )
