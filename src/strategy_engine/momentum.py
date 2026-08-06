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


def evaluate_momentum(
    trade_context: TradeContext,
    market_score: MarketScore,
    opportunity_context: OpportunityContext,
) -> StrategyScore:
    """
    Evaluates momentum strategy suitability for the current market environment.
    """
    market = trade_context.market
    options = trade_context.options
    session = trade_context.session
    expiry = trade_context.expiry
    
    reasons: list[StrategyReason] = []
    warnings: list[StrategyWarning] = []
    constraints: list[StrategyConstraint] = []
    required_conditions: list[str] = []
    rejected_conditions: list[str] = []
    
    # Base suitability calculation
    score = 50.0  # Start neutral
    
    # 1. Evaluate Trend Strength
    trend_strength = float(market.trend_strength)
    if trend_strength >= 60.0:
        score += 20.0
        required_conditions.append("High trend strength (trend_strength >= 60.0)")
        reasons.append(StrategyReason(
            reason_type="STRONG_TREND",
            message=f"Trend strength is elevated at {trend_strength:.1f}, favoring continuation."
        ))
    elif trend_strength < 40.0:
        score -= 20.0
        rejected_conditions.append("Low trend strength (trend_strength < 40.0)")
        reasons.append(StrategyReason(
            reason_type="WEAK_TREND",
            message=f"Trend strength is low at {trend_strength:.1f}, momentum plays are risky."
        ))
    else:
        reasons.append(StrategyReason(
            reason_type="NEUTRAL_TREND",
            message=f"Trend strength is moderate ({trend_strength:.1f})."
        ))
        
    # 2. Evaluate Regime
    if market.market_regime == "TRENDING":
        score += 15.0
        required_conditions.append("Regime is TRENDING")
        reasons.append(StrategyReason(
            reason_type="TRENDING_REGIME",
            message="Market is categorized in a TRENDING regime, ideal for momentum."
        ))
    elif market.market_regime == "SIDEWAYS":
        score -= 30.0
        rejected_conditions.append("Regime is SIDEWAYS")
        reasons.append(StrategyReason(
            reason_type="SIDEWAYS_REGIME",
            message="Market is in a SIDEWAYS consolidation regime. Mean reversion is preferred over momentum."
        ))
        
    # 3. Directional Bias check
    bias = opportunity_context.directional_bias.value
    if bias in ["BULLISH", "BEARISH"]:
        score += 10.0
        required_conditions.append("Directional bias is active and directional")
        reasons.append(StrategyReason(
            reason_type="ALIGNED_BIAS",
            message=f"Active directional bias of {bias} supports momentum implementation."
        ))
    else:
        score -= 15.0
        rejected_conditions.append("Directional bias is neutral/sideways")
        reasons.append(StrategyReason(
            reason_type="NO_BIAS",
            message="Neutral or sideways bias prevents clear directional momentum entry."
        ))
        
    # 4. Volatility state check
    if market.volatility_state == "COMPRESSED":
        score += 10.0
        reasons.append(StrategyReason(
            reason_type="COMPRESSED_VOLATILITY",
            message="Compressed volatility provides high coiling potential for a momentum expansion."
        ))
    elif market.volatility_state == "EXTREME":
        score -= 25.0
        rejected_conditions.append("Volatility state is EXTREME")
        reasons.append(StrategyReason(
            reason_type="EXTREME_VOLATILITY",
            message="Extreme market volatility poses high whipsaw risk for momentum trades."
        ))
        warnings.append(StrategyWarning(
            warning_type="HIGH_WHIPSAW_RISK",
            message="Extreme volatility increases likelihood of stop-outs prior to momentum realization.",
            severity="HIGH"
        ))
        
    # 5. Expiry & Decay considerations
    if expiry.days_remaining == 0:
        score -= 20.0
        rejected_conditions.append("Expiry is today")
        reasons.append(StrategyReason(
            reason_type="EXPIRY_DAY_DECAY",
            message="Today is expiry day. High theta decay and gamma sensitivity degrade standard momentum structures."
        ))
        warnings.append(StrategyWarning(
            warning_type="GAMMA_RISK",
            message="High gamma risks on expiry day might amplify option price fluctuations excessively.",
            severity="HIGH"
        ))
        
    # 6. Session constraints
    is_trading_disabled = not session.is_tradable_time or session.session_type in ["WEEKEND", "HOLIDAY", "POST_MARKET"]
    constraints.append(StrategyConstraint(
        constraint_type="TRADABLE_SESSION",
        message="Active market session must be open and tradable.",
        is_violated=is_trading_disabled
    ))
    
    # 7. Liquidity constraints
    metrics = options.liquidity_metrics if isinstance(options.liquidity_metrics, dict) else {}
    overall_liq = float(metrics.get("overall_liquidity_score", 100.0))
    is_liq_bad = overall_liq < 50.0
    constraints.append(StrategyConstraint(
        constraint_type="OPTION_LIQUIDITY",
        message="Option chain liquidity must be sufficient to support fast executions.",
        is_violated=is_liq_bad
    ))
    if is_liq_bad:
        score -= 30.0
        warnings.append(StrategyWarning(
            warning_type="LIQUIDITY_HAZARD",
            message="Slippage on fast-moving momentum trades is elevated due to wide bid-ask spreads.",
            severity="HIGH"
        ))

    # Clamp the suitability score between 0.0 and 100.0
    final_score = float(round(min(100.0, max(0.0, score)), 2))
    
    # Determine suitability level
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
        strategy_name="MOMENTUM",
        suitability_score=final_score,
        suitability_level=suitability_level,
        reasons=reasons,
        warnings=warnings,
        constraints=constraints,
        required_conditions_met=required_conditions,
        rejected_conditions_met=rejected_conditions,
    )
