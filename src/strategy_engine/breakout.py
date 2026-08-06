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


def evaluate_breakout(
    trade_context: TradeContext,
    market_score: MarketScore,
    opportunity_context: OpportunityContext,
) -> StrategyScore:
    """
    Evaluates breakout strategy suitability for the current market environment.
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
    
    # 1. Volatility compression evaluation (Crucial for Breakout)
    if market.volatility_state == "COMPRESSED":
        score += 25.0
        required_conditions.append("Volatility compression (volatility_state == 'COMPRESSED')")
        reasons.append(StrategyReason(
            reason_type="VOLATILITY_COILING",
            message="Volatility is compressed, indicating coiled price energy ready to break out."
        ))
    elif market.volatility_state == "NORMAL":
        score += 5.0
        reasons.append(StrategyReason(
            reason_type="VOLATILITY_NORMAL",
            message="Volatility is in a normal state, supportable for structural breakouts."
        ))
    elif market.volatility_state == "EXPANDED":
        score -= 10.0
        reasons.append(StrategyReason(
            reason_type="VOLATILITY_EXPANDED",
            message="Volatility is already expanded, breakout moves may be late/exhausted."
        ))
    elif market.volatility_state == "EXTREME":
        score -= 30.0
        rejected_conditions.append("Volatility state is EXTREME")
        reasons.append(StrategyReason(
            reason_type="VOLATILITY_EXTREME",
            message="Extreme volatility increases the likelihood of whipsaws and false breakouts."
        ))
        warnings.append(StrategyWarning(
            warning_type="FAKEOUT_RISK",
            message="Extreme volatility triggers false breakout signals frequently.",
            severity="HIGH"
        ))
        
    # 2. Check spot proximity to S/R levels
    spot = market.current_spot
    levels = (market.resistance_levels or []) + (market.support_levels or [])
    if spot > 0 and levels:
        closest_dist_pct = min(abs(lvl - spot) / spot * 100.0 for lvl in levels)
        if closest_dist_pct <= 0.5:
            score += 20.0
            required_conditions.append("Spot close to major structure levels (distance <= 0.5%)")
            reasons.append(StrategyReason(
                reason_type="LEVEL_PROXIMITY",
                message=f"Spot is extremely close to a major technical level ({closest_dist_pct:.2f}% distance), priming a potential breakout."
            ))
        elif closest_dist_pct <= 1.0:
            score += 10.0
            reasons.append(StrategyReason(
                reason_type="LEVEL_NEARBY",
                message=f"Spot is approaching a major level ({closest_dist_pct:.2f}% distance)."
            ))
        else:
            score -= 10.0
            reasons.append(StrategyReason(
                reason_type="LEVEL_FAR",
                message=f"Spot is in open space far from S/R levels ({closest_dist_pct:.2f}% distance). Breakout trigger is distant."
            ))
            
    # 3. Trend Force & Confluence confirmation
    if market_score.trend.overall_trend_score >= 70.0:
        score += 10.0
        reasons.append(StrategyReason(
            reason_type="STRONG_TREND_BIAS",
            message=f"High trend score of {market_score.trend.overall_trend_score:.1f} supports breakout direction."
        ))
        
    if trade_context.confluence.sr_alignment:
        score += 5.0
        reasons.append(StrategyReason(
            reason_type="SR_ALIGNMENT",
            message="Support/Resistance alignment is validated across timeframes."
        ))
        
    # 4. Expiry / Decay warnings
    if trade_context.expiry.days_remaining == 0:
        warnings.append(StrategyWarning(
            warning_type="GAMMA_PIN_RISK",
            message="On expiry day, option prices around the breakout strike exhibit hyper-sensitivity (Gamma risk).",
            severity="MEDIUM"
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
        message="Option chain liquidity must be high to exit breakouts quickly on failure.",
        is_violated=is_liq_bad
    ))
    if is_liq_bad:
        score -= 25.0
        warnings.append(StrategyWarning(
            warning_type="LIQUIDITY_HAZARD",
            message="Suboptimal options liquidity could cause massive slippage if a breakout fails and triggers exit.",
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
        strategy_name="BREAKOUT",
        suitability_score=final_score,
        suitability_level=suitability_level,
        reasons=reasons,
        warnings=warnings,
        constraints=constraints,
        required_conditions_met=required_conditions,
        rejected_conditions_met=rejected_conditions,
    )
