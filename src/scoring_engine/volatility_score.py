from __future__ import annotations

from src.models import TradeContext, VolatilityScore
from src.configuration_engine.runtime import Config


def evaluate_volatility_score(context: TradeContext) -> VolatilityScore:
    """
    Evaluates Volatility Score based on ATR, Volatility state compression/expansion, IV environment (VIX), and Expected Move.
    """
    market = context.market
    options = context.options
    scoring_config = Config.SCORING
    
    weights = scoring_config.get("volatility_weights", {})
    params = scoring_config.get("volatility_params", {})
    
    # 1. ATR Score (relative to spot)
    if market.current_spot > 0:
        atr_pct = (market.atr / market.current_spot) * 100.0
    else:
        atr_pct = 0.0
    atr_min = params.get("atr_min_pct", 0.4)
    atr_max = params.get("atr_max_pct", 2.0)
    atr_penalty = params.get("atr_penalty_mult", 25.0)
    if atr_min <= atr_pct <= atr_max:
        atr_score = 100.0
    elif atr_pct < atr_min:
        atr_score = float(max(0.0, 100.0 - (atr_min - atr_pct) * atr_penalty))
    else:
        atr_score = float(max(0.0, 100.0 - (atr_pct - atr_max) * atr_penalty))
        
    # 2. Compression Score (high is good for breakout trade set-ups)
    vol_state = getattr(market, "volatility_state", "NORMAL")
    if vol_state == "COMPRESSED":
        compression_score = float(params.get("vol_state_compressed_score", 100.0))
    elif vol_state == "NORMAL":
        compression_score = float(params.get("vol_state_normal_score", 90.0))
    elif vol_state == "EXPANDED":
        compression_score = float(params.get("vol_state_expanded_score", 75.0))
    else:  # EXTREME
        compression_score = float(params.get("vol_state_extreme_score", 40.0))
        
    # 3. Expansion Score (high is good for trend continuation)
    if vol_state == "EXPANDED":
        expansion_score = 100.0
    elif vol_state == "NORMAL":
        expansion_score = 85.0
    elif vol_state == "COMPRESSED":
        expansion_score = 70.0
    else:  # EXTREME
        expansion_score = 30.0
        
    # 4. IV Environment Score (VIX/IV range check)
    vix = market.india_vix if market.india_vix is not None else options.atm_iv
    vix_min = params.get("vix_min_healthy", 11.0)
    vix_max = params.get("vix_max_healthy", 19.0)
    vix_penalty = params.get("vix_penalty_mult", 6.0)
    if vix_min <= vix <= vix_max:
        iv_env_score = 100.0
    elif vix < vix_min:
        iv_env_score = float(max(0.0, 100.0 - (vix_min - vix) * vix_penalty))
    else:
        iv_env_score = float(max(0.0, 100.0 - (vix - vix_max) * vix_penalty))
        
    # 5. Expected Move Score (relative to spot)
    if options.underlying_spot > 0:
        em_pct = (options.expected_move / options.underlying_spot) * 100.0
    else:
        em_pct = 0.0
    em_min = 0.5
    em_max = 3.5
    em_penalty = 15.0
    if em_min <= em_pct <= em_max:
        expected_move_score = 100.0
    elif em_pct < em_min:
        expected_move_score = float(max(0.0, 100.0 - (em_min - em_pct) * em_penalty))
    else:
        expected_move_score = float(max(0.0, 100.0 - (em_pct - em_max) * em_penalty))
        
    # Calculate overall weighted score
    w_atr = weights.get("atr", 0.25)
    w_compression = weights.get("compression", 0.20)
    w_expansion = weights.get("expansion", 0.15)
    w_iv_env = weights.get("iv_env", 0.20)
    w_expected_move = weights.get("expected_move", 0.20)
    
    total_weight = w_atr + w_compression + w_expansion + w_iv_env + w_expected_move
    weighted_sum = (
        atr_score * w_atr +
        compression_score * w_compression +
        expansion_score * w_expansion +
        iv_env_score * w_iv_env +
        expected_move_score * w_expected_move
    )
    
    overall_volatility_score = float(round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0)
    
    return VolatilityScore(
        atr_score=atr_score,
        compression_score=compression_score,
        expansion_score=expansion_score,
        iv_env_score=iv_env_score,
        expected_move_score=expected_move_score,
        overall_volatility_score=overall_volatility_score,
    )
