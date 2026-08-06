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


def evaluate_trend_following(
    trade_context: TradeContext,
    market_score: MarketScore,
    opportunity_context: OpportunityContext,
) -> StrategyScore:
    """
    Evaluates trend following strategy suitability for the current market environment.
    """
    market = trade_context.market
    options = trade_context.options
    session = trade_context.session
    confluence = trade_context.confluence
    
    reasons: list[StrategyReason] = []
    warnings: list[StrategyWarning] = []
    constraints: list[StrategyConstraint] = []
    required_conditions: list[str] = []
    rejected_conditions: list[str] = []
    
    score = 50.0  # Start neutral
    
    # 1. Trend strength evaluation
    trend_strength = float(market.trend_strength)
    if trend_strength >= 55.0:
        score += 20.0
        required_conditions.append("Established trend (trend_strength >= 55.0)")
        reasons.append(StrategyReason(
            reason_type="ESTABLISHED_TREND",
            message=f"Market has a well-established trend with a strength of {trend_strength:.1f}."
        ))
    elif trend_strength < 40.0:
        score -= 25.0
        rejected_conditions.append("Low trend strength (trend_strength < 40.0)")
        reasons.append(StrategyReason(
            reason_type="WEAK_TREND",
            message=f"Trend strength is too low ({trend_strength:.1f}) to support trend following."
        ))
    else:
        reasons.append(StrategyReason(
            reason_type="MODERATE_TREND",
            message=f"Trend strength is moderate at {trend_strength:.1f}."
        ))
        
    # 2. Market Regime & Confluence
    if market.market_regime == "TRENDING":
        score += 15.0
        required_conditions.append("Regime is TRENDING")
        reasons.append(StrategyReason(
            reason_type="TRENDING_REGIME",
            message="Market is officially classified as TRENDING regime."
        ))
    elif market.market_regime == "SIDEWAYS":
        score -= 30.0
        rejected_conditions.append("Regime is SIDEWAYS")
        reasons.append(StrategyReason(
            reason_type="SIDEWAYS_REGIME",
            message="Market is in SIDEWAYS consolidation. Trend-following is unsuitable here."
        ))
        
    if confluence.trend_confluence:
        score += 10.0
        required_conditions.append("Trend Confluence is active")
        reasons.append(StrategyReason(
            reason_type="TREND_CONFLUENCE",
            message="Technical trend confluence is confirmed across multiple metrics."
        ))
        
    # 3. Volatility environment
    if market.volatility_state == "EXTREME":
        score -= 20.0
        rejected_conditions.append("Volatility is EXTREME")
        reasons.append(StrategyReason(
            reason_type="EXTREME_VOLATILITY",
            message="Extreme volatility corrupts structural trend lines and increases stop risk."
        ))
        warnings.append(StrategyWarning(
            warning_type="TREND_DEGRADATION",
            message="Trend structure may break prematurely under high/extreme volatility regimes.",
            severity="MEDIUM"
        ))
    elif market.volatility_state in ["NORMAL", "COMPRESSED"]:
        score += 5.0
        reasons.append(StrategyReason(
            reason_type="STABLE_VOLATILITY",
            message="Stable or compressed volatility supports steady, reliable trend extensions."
        ))
        
    # 4. Check option alignment
    if options.market_option_bias == market.trend_direction and market.trend_direction != "SIDEWAYS":
        score += 10.0
        reasons.append(StrategyReason(
            reason_type="OPTION_BIAS_ALIGNMENT",
            message=f"Options chain bias ({options.market_option_bias}) is perfectly aligned with spot trend."
        ))
    elif options.market_option_bias != "SIDEWAYS" and market.trend_direction != "SIDEWAYS":
        score -= 15.0
        reasons.append(StrategyReason(
            reason_type="OPTION_BIAS_MISALIGNMENT",
            message=f"Options chain bias ({options.market_option_bias}) diverges from spot trend ({market.trend_direction})."
        ))
        warnings.append(StrategyWarning(
            warning_type="DIVERGING_OPTIONS_STRUCTURE",
            message="Smart money option positioning is not confirming the spot trend direction.",
            severity="HIGH"
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
        message="Option chain liquidity must support larger, longer-term positions without wide spreads.",
        is_violated=is_liq_bad
    ))
    if is_liq_bad:
        score -= 20.0
        warnings.append(StrategyWarning(
            warning_type="LIQUIDITY_HAZARD",
            message="Suboptimal options liquidity restricts high-conviction trend-following structures.",
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
        strategy_name="TREND_FOLLOWING",
        suitability_score=final_score,
        suitability_level=suitability_level,
        reasons=reasons,
        warnings=warnings,
        constraints=constraints,
        required_conditions_met=required_conditions,
        rejected_conditions_met=rejected_conditions,
    )
