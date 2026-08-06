from __future__ import annotations

from src.models import TradeContext, TrendScore
from src.configuration_engine.runtime import Config


def evaluate_trend_score(context: TradeContext) -> TrendScore:
    """
    Evaluates Trend Score based on trend strength, EMA alignment, ADX, Slope, and Momentum.
    """
    market = context.market
    scoring_config = Config.SCORING
    
    weights = scoring_config.get("trend_weights", {})
    params = scoring_config.get("trend_params", {})
    
    # 1. Trend strength
    trend_strength_score = float(market.trend_strength)
    
    # 2. EMA Alignment
    if market.trend_direction != "SIDEWAYS":
        ema_score = float(params.get("base_trending_score", 90.0))
        # Add spot vs vwap alignment bonus
        if (market.trend_direction == "BULLISH" and market.current_spot >= market.vwap) or \
           (market.trend_direction == "BEARISH" and market.current_spot <= market.vwap):
            ema_score += float(params.get("spot_vwap_alignment_bonus", 10.0))
    else:
        ema_score = float(params.get("base_sideways_score", 40.0))
    ema_alignment_score = float(min(100.0, max(0.0, ema_score)))
    
    # 3. ADX Score (ADX is estimated/scaled from trend strength)
    adx_score = float(min(100.0, max(0.0, market.trend_strength * params.get("adx_multiplier", 2.0))))
    
    # 4. Slope Score (Evaluated relative to spot vs vwap and direction)
    if market.trend_direction == "BULLISH":
        if market.current_spot >= market.vwap:
            slope_score = float(params.get("slope_aligned_score", 100.0))
        else:
            slope_score = float(params.get("slope_misaligned_score", 20.0))
    elif market.trend_direction == "BEARISH":
        if market.current_spot <= market.vwap:
            slope_score = float(params.get("slope_aligned_score", 100.0))
        else:
            slope_score = float(params.get("slope_misaligned_score", 20.0))
    else:
        slope_score = float(params.get("slope_sideways_score", 50.0))
        
    # 5. Momentum Score (Evaluated relative to spot vs vwap and direction)
    if market.trend_direction == "BULLISH":
        if market.current_spot >= market.vwap:
            momentum_score = float(params.get("momentum_aligned_score", 100.0))
        else:
            momentum_score = float(params.get("momentum_misaligned_score", 30.0))
    elif market.trend_direction == "BEARISH":
        if market.current_spot <= market.vwap:
            momentum_score = float(params.get("momentum_aligned_score", 100.0))
        else:
            momentum_score = float(params.get("momentum_misaligned_score", 30.0))
    else:
        momentum_score = float(params.get("momentum_sideways_score", 50.0))
        
    # Calculate overall weighted score
    w_strength = weights.get("trend_strength", 0.30)
    w_ema = weights.get("ema_alignment", 0.20)
    w_adx = weights.get("adx", 0.20)
    w_slope = weights.get("slope", 0.15)
    w_momentum = weights.get("momentum", 0.15)
    
    total_weight = w_strength + w_ema + w_adx + w_slope + w_momentum
    weighted_sum = (
        trend_strength_score * w_strength +
        ema_alignment_score * w_ema +
        adx_score * w_adx +
        slope_score * w_slope +
        momentum_score * w_momentum
    )
    
    overall_trend_score = float(round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0)
    
    return TrendScore(
        trend_strength_score=trend_strength_score,
        ema_alignment_score=ema_alignment_score,
        adx_score=adx_score,
        slope_score=slope_score,
        momentum_score=momentum_score,
        overall_trend_score=overall_trend_score,
    )
