from __future__ import annotations

import math
from src.models import TradeContext, OpportunityStrength


def evaluate_opportunity_strength(context: TradeContext) -> OpportunityStrength:
    """
    Computes a physical measure of opportunity strength based on market and option imbalances.
    """
    market = context.market
    options = context.options
    
    # 1. Trend Force: based on trend strength, direction and spot relationship with VWAP
    base_trend_strength = float(market.trend_strength)
    trend_direction_multiplier = 1.0
    if market.trend_direction == "SIDEWAYS":
        trend_direction_multiplier = 0.3
    else:
        # Check alignment of spot and VWAP
        if market.trend_direction == "BULLISH":
            if market.current_spot >= market.vwap:
                trend_direction_multiplier = 1.1
            else:
                trend_direction_multiplier = 0.7
        elif market.trend_direction == "BEARISH":
            if market.current_spot <= market.vwap:
                trend_direction_multiplier = 1.1
            else:
                trend_direction_multiplier = 0.7
                
    trend_force = float(min(100.0, max(0.0, base_trend_strength * trend_direction_multiplier)))
    
    # 2. Option Force: physical buying/selling pressure imbalance
    # Skew from Put-Call Ratio
    pcr_val = float(options.pcr)
    if market.trend_direction == "BULLISH":
        pcr_force = min(100.0, max(0.0, (pcr_val - 0.7) * 100.0)) if pcr_val >= 0.7 else 20.0
    elif market.trend_direction == "BEARISH":
        pcr_force = min(100.0, max(0.0, (1.3 - pcr_val) * 100.0)) if pcr_val <= 1.3 else 20.0
    else:
        pcr_force = 50.0
        
    # Skew from OI Change
    highest_call_change = float(options.highest_call_oi_change)
    highest_put_change = float(options.highest_put_oi_change)
    total_change = highest_call_change + highest_put_change
    if total_change > 0:
        oi_change_force = (highest_put_change / total_change) * 100.0 if market.trend_direction == "BULLISH" else (highest_call_change / total_change) * 100.0
    else:
        oi_change_force = 50.0
        
    option_force = float(round((pcr_force * 0.4) + (oi_change_force * 0.6), 2))
    
    # 3. Liquidity Force: derived from options spread and score
    metrics = options.liquidity_metrics if isinstance(options.liquidity_metrics, dict) else {}
    base_liq_score = float(metrics.get("overall_liquidity_score", 85.0))
    spread_pct = float(metrics.get("average_spread_pct", 0.15))
    
    # Spread penalty
    spread_force_multiplier = 1.0
    if spread_pct > 0.5:
        spread_force_multiplier = 0.5
    elif spread_pct > 0.2:
        spread_force_multiplier = 0.8
        
    liquidity_force = float(min(100.0, max(0.0, base_liq_score * spread_force_multiplier)))
    
    # 4. Imbalance Magnitude: relative spot displacement from major support/resistance or VWAP
    if market.current_spot > 0:
        vwap_deviation_pct = (abs(market.current_spot - market.vwap) / market.current_spot) * 100.0
    else:
        vwap_deviation_pct = 0.0
        
    # Scale displacement to 0-100 scale (typically deviation is 0.1% to 1.5% for intraday)
    imbalance_magnitude = float(min(100.0, max(0.0, vwap_deviation_pct * 100.0)))
    
    # 5. Combined Overall Strength
    # Weightings: Trend 40%, Option Imbalance 40%, Liquidity stability 20%
    overall_strength = float(round((trend_force * 0.40) + (option_force * 0.40) + (liquidity_force * 0.20), 2))
    
    return OpportunityStrength(
        imbalance_magnitude=imbalance_magnitude,
        trend_force=trend_force,
        option_force=option_force,
        liquidity_force=liquidity_force,
        overall_strength=overall_strength
    )
