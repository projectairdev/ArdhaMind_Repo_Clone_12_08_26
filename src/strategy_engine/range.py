from __future__ import annotations

from src.models import (
    TradeContext,
    MarketScore,
    OpportunityContext,
    StrategyScore,
    StrategyReason,
    StrategyWarning,
    StrategyConstraint,
)


def evaluate_range(
    trade_context: TradeContext,
    market_score: MarketScore,
    opportunity_context: OpportunityContext,
) -> StrategyScore:
    """
    Evaluates range trading strategy suitability for the current market environment.
    """
    market = trade_context.market
    options = trade_context.options
    session = trade_context.session
    
    reasons: list[StrategyReason] = []
    warnings: list[StrategyWarning] = []
    constraints: list[StrategyConstraint] = []
    required_conditions: list[str] = []
    rejected_conditions: list[str] = []
    
    score = 50.0  # Start neutral
    
    # 1. Regime Check (Sideways is highly favorable)
    if market.market_regime == "SIDEWAYS":
        score += 30.0
        required_conditions.append("Market regime is SIDEWAYS")
        reasons.append(StrategyReason(
            reason_type="SIDEWAYS_REGIME",
            message="Market is officially classified as SIDEWAYS, favoring range channel plays."
        ))
    elif market.market_regime == "TRENDING":
        score -= 35.0
        rejected_conditions.append("Market regime is TRENDING")
        reasons.append(StrategyReason(
            reason_type="TRENDING_REGIME",
            message="Market is TRENDING; Range-bound strategies face high break-out risks."
        ))
        
    # 2. Trend strength check
    trend_strength = float(market.trend_strength)
    if trend_strength < 35.0:
        score += 15.0
        required_conditions.append("Trend strength is extremely low (trend_strength < 35.0)")
        reasons.append(StrategyReason(
            reason_type="VERY_WEAK_TREND",
            message=f"Minimal trend strength ({trend_strength:.1f}) confirms lack of directional drive."
        ))
    elif trend_strength >= 60.0:
        score -= 20.0
        rejected_conditions.append("Trend strength is high (trend_strength >= 60.0)")
        reasons.append(StrategyReason(
            reason_type="STRONG_TREND_DRIVE",
            message=f"High trend strength ({trend_strength:.1f}) threatens range limits."
        ))
        
    # 3. Volatility state check
    if market.volatility_state == "COMPRESSED":
        score += 10.0
        reasons.append(StrategyReason(
            reason_type="STABLE_VOLATILITY",
            message="Compressed volatility represents tight range boundaries."
        ))
    elif market.volatility_state == "EXTREME":
        score -= 25.0
        rejected_conditions.append("Volatility state is EXTREME")
        reasons.append(StrategyReason(
            reason_type="UNSTABLE_VOLATILITY",
            message="Extreme volatility invalidates reliable support and resistance boundaries."
        ))
        warnings.append(StrategyWarning(
            warning_type="LEVELS_SHATTER_RISK",
            message="Support and Resistance levels are prone to piercing under extreme volatility.",
            severity="HIGH"
        ))
        
    # 4. Spot location relative to range boundaries
    spot = market.current_spot
    supports = market.support_levels or []
    resistances = market.resistance_levels or []
    if spot > 0 and supports and resistances:
        max_support = max(supports)
        min_resistance = min(resistances)
        if max_support < spot < min_resistance:
            score += 10.0
            required_conditions.append("Spot located within major support and resistance limits")
            reasons.append(StrategyReason(
                reason_type="WITHIN_LIMITS",
                message=f"Spot ({spot}) is well framed within support {max_support} and resistance {min_resistance}."
            ))
        else:
            score -= 15.0
            reasons.append(StrategyReason(
                reason_type="OUTSIDE_LIMITS",
                message=f"Spot ({spot}) has breached or is outside core range bounds ({max_support} - {min_resistance})."
            ))
            
    # 5. Session constraints
    is_trading_disabled = not session.is_tradable_time or session.session_type in ["WEEKEND", "HOLIDAY", "POST_MARKET"]
    constraints.append(StrategyConstraint(
        constraint_type="TRADABLE_SESSION",
        message="Active market session must be open and tradable.",
        is_violated=is_trading_disabled
    ))
    
    # 6. Option liquidity constraints
    metrics = options.liquidity_metrics if isinstance(options.liquidity_metrics, dict) else {}
    overall_liq = float(metrics.get("overall_liquidity_score", 100.0))
    is_liq_bad = overall_liq < 50.0
    constraints.append(StrategyConstraint(
        constraint_type="OPTION_LIQUIDITY",
        message="Option chain liquidity must be robust to facilitate range-bound premium collection.",
        is_violated=is_liq_bad
    ))
    if is_liq_bad:
        score -= 20.0
        warnings.append(StrategyWarning(
            warning_type="LIQUIDITY_HAZARD",
            message="Range strategies like iron condors require tight bid-ask spreads to avoid exit slippage.",
            severity="HIGH"
        ))

    final_score = float(round(min(100.0, max(0.0, score)), 2))
    
    if is_trading_disabled or is_liq_bad:
        suitability_level = "NONE"
    elif final_score >= 80.0:
        suitability_level = "HIGH"
    elif final_score >= 50.0:
        suitability_level = "MEDIUM"
    elif final_score >= 20.0:
        suitability_level = "LOW"
    else:
        suitability_level = "NONE"
        
    return StrategyScore(
        strategy_name="RANGE",
        suitability_score=final_score,
        suitability_level=suitability_level,
        reasons=reasons,
        warnings=warnings,
        constraints=constraints,
        required_conditions_met=required_conditions,
        rejected_conditions_met=rejected_conditions,
    )
