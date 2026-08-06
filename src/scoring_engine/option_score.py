from __future__ import annotations

from src.models import TradeContext, OptionScore
from src.configuration_engine.runtime import Config


def evaluate_option_score(context: TradeContext) -> OptionScore:
    """
    Evaluates Option Score based on PCR, Max Pain distance, OI Structure, OI Build-up, Liquidity, IV, and Expected Move.
    """
    options = context.options
    market = context.market
    scoring_config = Config.SCORING
    
    weights = scoring_config.get("option_weights", {})
    params = scoring_config.get("option_params", {})
    
    # 1. PCR Score
    pcr_lower = params.get("pcr_lower_bound", 0.70)
    pcr_upper = params.get("pcr_upper_bound", 1.30)
    if pcr_lower <= options.pcr <= pcr_upper:
        pcr_score = 100.0
    else:
        target = params.get("pcr_target", 1.00)
        penalty_mult = params.get("pcr_penalty_mult", 80.0)
        pcr_score = float(max(0.0, 100.0 - abs(options.pcr - target) * penalty_mult))
        
    # 2. Max Pain Score
    if options.underlying_spot > 0:
        dist_pct = (abs(options.underlying_spot - options.max_pain) / options.underlying_spot) * 100.0
    else:
        dist_pct = 0.0
    max_pain_penalty_mult = params.get("max_pain_penalty_mult", 40.0)
    max_pain_score = float(max(0.0, 100.0 - dist_pct * max_pain_penalty_mult))
    
    # 3. OI Structure Score
    if options.market_option_bias == market.trend_direction and market.trend_direction != "SIDEWAYS":
        oi_structure_score = float(params.get("oi_aligned_score", 100.0))
    elif market.trend_direction == "SIDEWAYS":
        oi_structure_score = 80.0
    else:
        oi_structure_score = float(params.get("oi_misaligned_score", 40.0))
        
    # 4. OI Build-up Score
    if market.trend_direction == "BULLISH":
        if options.highest_put_oi_change >= options.highest_call_oi_change:
            oi_buildup_score = float(params.get("oi_buildup_aligned_score", 100.0))
        else:
            oi_buildup_score = float(params.get("oi_buildup_misaligned_score", 50.0))
    elif market.trend_direction == "BEARISH":
        if options.highest_call_oi_change >= options.highest_put_oi_change:
            oi_buildup_score = float(params.get("oi_buildup_aligned_score", 100.0))
        else:
            oi_buildup_score = float(params.get("oi_buildup_misaligned_score", 50.0))
    else:
        oi_buildup_score = 75.0
        
    # 5. Liquidity Component Score (overall score from options context)
    if isinstance(options.liquidity_metrics, dict):
        liquidity_score = float(options.liquidity_metrics.get("overall_liquidity_score", 100.0))
    else:
        liquidity_score = 100.0
        
    # 6. IV Score
    iv_min = params.get("iv_min_healthy", 10.0)
    iv_max = params.get("iv_max_healthy", 22.0)
    iv_penalty = params.get("iv_penalty_mult", 5.0)
    if iv_min <= options.atm_iv <= iv_max:
        iv_score = 100.0
    elif options.atm_iv < iv_min:
        iv_score = float(max(0.0, 100.0 - (iv_min - options.atm_iv) * iv_penalty))
    else:
        iv_score = float(max(0.0, 100.0 - (options.atm_iv - iv_max) * iv_penalty))
        
    # 7. Expected Move Score
    if options.underlying_spot > 0:
        em_pct = (options.expected_move / options.underlying_spot) * 100.0
    else:
        em_pct = 0.0
    em_min = params.get("expected_move_min_pct", 0.5)
    em_max = params.get("expected_move_max_pct", 3.5)
    em_penalty = params.get("expected_move_penalty_mult", 15.0)
    if em_min <= em_pct <= em_max:
        expected_move_score = 100.0
    elif em_pct < em_min:
        expected_move_score = float(max(0.0, 100.0 - (em_min - em_pct) * em_penalty))
    else:
        expected_move_score = float(max(0.0, 100.0 - (em_pct - em_max) * em_penalty))
        
    # Calculate overall weighted score
    w_pcr = weights.get("pcr", 0.20)
    w_max_pain = weights.get("max_pain", 0.15)
    w_oi_structure = weights.get("oi_structure", 0.20)
    w_oi_buildup = weights.get("oi_buildup", 0.15)
    w_liquidity = weights.get("liquidity", 0.15)
    w_iv = weights.get("iv", 0.05)
    w_expected_move = weights.get("expected_move", 0.10)
    
    total_weight = w_pcr + w_max_pain + w_oi_structure + w_oi_buildup + w_liquidity + w_iv + w_expected_move
    weighted_sum = (
        pcr_score * w_pcr +
        max_pain_score * w_max_pain +
        oi_structure_score * w_oi_structure +
        oi_buildup_score * w_oi_buildup +
        liquidity_score * w_liquidity +
        iv_score * w_iv +
        expected_move_score * w_expected_move
    )
    
    overall_option_score = float(round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0)
    
    return OptionScore(
        pcr_score=pcr_score,
        max_pain_score=max_pain_score,
        oi_structure_score=oi_structure_score,
        oi_buildup_score=oi_buildup_score,
        liquidity_score=liquidity_score,
        iv_score=iv_score,
        expected_move_score=expected_move_score,
        overall_option_score=overall_option_score,
    )
