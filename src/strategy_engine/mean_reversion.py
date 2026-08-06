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


def evaluate_mean_reversion(
    trade_context: TradeContext,
    market_score: MarketScore,
    opportunity_context: OpportunityContext,
) -> StrategyScore:
    """
    Evaluates mean reversion strategy suitability for the current market environment.
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
    
    # 1. Spot vs VWAP deviation / Imbalance magnitude
    spot = market.current_spot
    vwap = market.vwap
    if spot > 0 and vwap > 0:
        deviation_pct = abs(spot - vwap) / spot * 100.0
        if deviation_pct >= 0.6:
            score += 20.0
            required_conditions.append(f"Spot significantly stretched from VWAP (deviation={deviation_pct:.2f}% >= 0.6%)")
            reasons.append(StrategyReason(
                reason_type="HIGH_VWAP_DEVIATION",
                message=f"Spot price is significantly stretched from VWAP by {deviation_pct:.2f}%, raising probability of a reversion callback."
            ))
        elif deviation_pct <= 0.2:
            score -= 15.0
            reasons.append(StrategyReason(
                reason_type="LOW_VWAP_DEVIATION",
                message=f"Spot is extremely close to VWAP ({deviation_pct:.2f}%). No stretch is present to trade reversion."
            ))
        else:
            reasons.append(StrategyReason(
                reason_type="NORMAL_VWAP_DEVIATION",
                message=f"Spot is at a normal deviation from VWAP ({deviation_pct:.2f}%)."
            ))
            
    # 2. Volatility state (Mean reversion likes high/expanded volatility for premium selling or elastic recoil)
    if market.volatility_state in ["EXPANDED", "EXTREME"]:
        score += 15.0
        required_conditions.append("Volatility is expanded or extreme")
        reasons.append(StrategyReason(
            reason_type="EXPANDED_VOLATILITY",
            message="Expanded volatility indicates panic or overshoot, providing premium-rich mean reversion opportunities."
        ))
    elif market.volatility_state == "COMPRESSED":
        score -= 20.0
        rejected_conditions.append("Volatility is COMPRESSED")
        reasons.append(StrategyReason(
            reason_type="COMPRESSED_VOLATILITY",
            message="Compressed volatility represents a potential breakout starter; mean reversion is highly risky here."
        ))
        
    # 3. Trend strength (Strong trend is a heavy penalty for mean reversion/fading)
    trend_strength = float(market.trend_strength)
    if trend_strength >= 70.0 and market.market_regime == "TRENDING":
        score -= 35.0
        rejected_conditions.append("Strong trending regime (trend_strength >= 70.0)")
        reasons.append(StrategyReason(
            reason_type="STRONG_RUNAWAY_TREND",
            message=f"Fading a runaway trend (strength: {trend_strength:.1f}) is highly hazardous. Reversion carries extreme risk."
        ))
        warnings.append(StrategyWarning(
            warning_type="RUNAWAY_TREND_HAZARD",
            message="Fading a high-strength momentum trend often leads to severe losses prior to reversion.",
            severity="HIGH"
        ))
    elif trend_strength < 40.0:
        score += 15.0
        required_conditions.append("Trend strength is weak")
        reasons.append(StrategyReason(
            reason_type="WEAK_TREND",
            message=f"Weak trend strength of {trend_strength:.1f} increases viability of range-bound mean reversion."
        ))
        
    # 4. Option PCR extreme checks (indicator of overbought/oversold status)
    pcr = float(options.pcr)
    if pcr <= 0.65:
        score += 10.0
        reasons.append(StrategyReason(
            reason_type="OVERSOLD_PCR",
            message=f"Put-Call Ratio is extremely low ({pcr:.2f}), suggesting an oversold structure primed for a short squeeze bounce."
        ))
    elif pcr >= 1.4:
        score += 10.0
        reasons.append(StrategyReason(
            reason_type="OVERBOUGHT_PCR",
            message=f"Put-Call Ratio is high ({pcr:.2f}), suggesting an overbought structure primed for profit taking."
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
        message="Option chain liquidity must be robust to facilitate fading setups.",
        is_violated=is_liq_bad
    ))
    if is_liq_bad:
        score -= 20.0
        warnings.append(StrategyWarning(
            warning_type="LIQUIDITY_HAZARD",
            message="Fading trades require precise exits. Suboptimal options liquidity may inflate exit slippage.",
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
        strategy_name="MEAN_REVERSION",
        suitability_score=final_score,
        suitability_level=suitability_level,
        reasons=reasons,
        warnings=warnings,
        constraints=constraints,
        required_conditions_met=required_conditions,
        rejected_conditions_met=rejected_conditions,
    )
