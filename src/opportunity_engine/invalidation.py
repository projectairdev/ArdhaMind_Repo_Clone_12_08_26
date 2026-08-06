from __future__ import annotations

from src.models import TradeContext, InvalidationFactor


def evaluate_invalidation_factors(context: TradeContext, directional_bias: str) -> list[InvalidationFactor]:
    """
    Evaluates TradeContext to determine deterministic invalidation rules.
    """
    factors: list[InvalidationFactor] = []
    market = context.market
    options = context.options
    expiry = context.expiry
    session = context.session
    
    # 1. Loss of Trend Alignment
    is_trend_invalid = market.trend_direction == "SIDEWAYS" or (
        directional_bias in ["BULLISH", "BEARISH"] and market.trend_direction != directional_bias
    )
    factors.append(InvalidationFactor(
        factor_type="LOSS_OF_TREND_ALIGNMENT",
        is_invalidated=is_trend_invalid,
        reason=f"Current market trend {market.trend_direction} is not aligned with opportunity bias {directional_bias}." if is_trend_invalid else "Trend alignment is preserved."
    ))
    
    # 2. Liquidity Deterioration
    metrics = options.liquidity_metrics if isinstance(options.liquidity_metrics, dict) else {}
    overall_liq_score = float(metrics.get("overall_liquidity_score", 100.0))
    is_liq_invalid = overall_liq_score < 40.0
    factors.append(InvalidationFactor(
        factor_type="LIQUIDITY_DETERIORATION",
        is_invalidated=is_liq_invalid,
        reason=f"Option chain overall liquidity score is {overall_liq_score:.1f}, falling below critical threshold of 40.0." if is_liq_invalid else "Option chain liquidity is sufficient."
    ))
    
    # 3. Volatility Regime Change
    is_vol_invalid = market.volatility_state == "EXTREME"
    factors.append(InvalidationFactor(
        factor_type="VOLATILITY_REGIME_CHANGE",
        is_invalidated=is_vol_invalid,
        reason="Market is in an EXTREME volatility state, rendering normal technical levels invalid." if is_vol_invalid else "Volatility state is stable."
    ))
    
    # 4. Support Break (for bullish directional bias)
    is_support_broken = False
    support_reason = "No support levels broken."
    if directional_bias == "BULLISH" and market.support_levels and market.current_spot > 0:
        min_support = min(market.support_levels)
        if market.current_spot < min_support:
            is_support_broken = True
            support_reason = f"Current spot {market.current_spot} broke below critical support floor {min_support}."
    factors.append(InvalidationFactor(
        factor_type="SUPPORT_BREAK",
        is_invalidated=is_support_broken,
        reason=support_reason
    ))
    
    # 5. Resistance Break (for bearish directional bias)
    is_resistance_broken = False
    resistance_reason = "No resistance levels broken."
    if directional_bias == "BEARISH" and market.resistance_levels and market.current_spot > 0:
        max_resistance = max(market.resistance_levels)
        if market.current_spot > max_resistance:
            is_resistance_broken = True
            resistance_reason = f"Current spot {market.current_spot} broke above critical resistance ceiling {max_resistance}."
    factors.append(InvalidationFactor(
        factor_type="RESISTANCE_BREAK",
        is_invalidated=is_resistance_broken,
        reason=resistance_reason
    ))
    
    # 6. Option Structure Collapse
    is_option_collapse = options.pcr < 0.4 or options.pcr > 2.0
    factors.append(InvalidationFactor(
        factor_type="OPTION_STRUCTURE_COLLAPSE",
        is_invalidated=is_option_collapse,
        reason=f"PCR of {options.pcr:.2f} is in panic/unhealthy extreme, indicating options structure collapse." if is_option_collapse else "Options structure is intact."
    ))
    
    # 7. Session Change
    is_session_invalid = not session.is_tradable_time or session.session_type in ["POST_MARKET", "WEEKEND", "HOLIDAY"]
    factors.append(InvalidationFactor(
        factor_type="SESSION_CHANGE",
        is_invalidated=is_session_invalid,
        reason=f"Current session {session.session_type} is not suitable for active trading." if is_session_invalid else "Active trading session is open."
    ))
    
    # 8. Expiry Transition
    is_expiry_invalid = expiry.days_remaining < 0
    factors.append(InvalidationFactor(
        factor_type="EXPIRY_TRANSITION",
        is_invalidated=is_expiry_invalid,
        reason="Contracts have expired. Days remaining < 0." if is_expiry_invalid else "Contracts are prior to expiry."
    ))
    
    return factors
