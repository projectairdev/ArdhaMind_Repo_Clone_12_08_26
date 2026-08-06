from __future__ import annotations

from src.models import TradeContext, LiquidityScore
from src.configuration_engine.runtime import Config


def evaluate_liquidity_score(context: TradeContext) -> LiquidityScore:
    """
    Evaluates Liquidity Score based on Spread, Volume metrics, Open Interest, and Tradability.
    """
    options = context.options
    scoring_config = Config.SCORING
    
    weights = scoring_config.get("liquidity_weights", {})
    params = scoring_config.get("liquidity_params", {})
    
    metrics = options.liquidity_metrics if isinstance(options.liquidity_metrics, dict) else {}
    summary = options.option_chain_summary if isinstance(options.option_chain_summary, dict) else {}
    
    # 1. Spread Score (lower spread means higher score)
    spread_pct = float(metrics.get("average_spread_pct", 0.5))
    spread_penalty = float(params.get("spread_penalty_mult", 60.0))
    # If spread is 0.1% or less, it's perfect
    if spread_pct <= 0.1:
        spread_score = 100.0
    else:
        spread_score = float(max(0.0, 100.0 - (spread_pct - 0.1) * spread_penalty))
        
    # 2. Volume Score (derived from overall liquidity score)
    volume_score = float(metrics.get("overall_liquidity_score", 85.0))
    
    # 3. Open Interest Score
    total_calls_oi = float(summary.get("total_calls_oi", 500000.0))
    total_puts_oi = float(summary.get("total_puts_oi", 500000.0))
    total_oi = total_calls_oi + total_puts_oi
    
    oi_threshold = float(params.get("oi_threshold", 100000.0))
    if total_oi >= oi_threshold:
        oi_score = 100.0
    else:
        oi_penalty = float(params.get("oi_penalty_mult", 0.0001))
        oi_score = float(max(10.0, 100.0 - (oi_threshold - total_oi) * oi_penalty))
        
    # 4. Tradability Score
    min_liq = float(params.get("tradability_min_liquidity", 50.0))
    if volume_score >= min_liq and spread_score >= 50.0:
        tradability_score = 100.0
    else:
        tradability_score = float(min(volume_score, spread_score))
        
    # Calculate overall weighted score
    w_spread = weights.get("spread", 0.40)
    w_volume = weights.get("volume", 0.25)
    w_oi = weights.get("oi", 0.20)
    w_tradability = weights.get("tradability", 0.15)
    
    total_weight = w_spread + w_volume + w_oi + w_tradability
    weighted_sum = (
        spread_score * w_spread +
        volume_score * w_volume +
        oi_score * w_oi +
        tradability_score * w_tradability
    )
    
    overall_liquidity_score = float(round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0)
    
    return LiquidityScore(
        spread_score=spread_score,
        volume_score=volume_score,
        oi_score=oi_score,
        tradability_score=tradability_score,
        overall_liquidity_score=overall_liquidity_score,
    )
