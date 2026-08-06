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


def evaluate_expiry(
    trade_context: TradeContext,
    market_score: MarketScore,
    opportunity_context: OpportunityContext,
) -> StrategyScore:
    """
    Evaluates expiry play strategy suitability for the current market environment.
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
    
    score = 0.0  # Start very low; default is unsuitable unless near expiry
    
    # 1. Evaluate proximity to Expiry (The absolute gatekeeper for this strategy)
    days = expiry.days_remaining
    if days == 0:
        score += 85.0
        required_conditions.append("Expiry Day (days_remaining == 0)")
        reasons.append(StrategyReason(
            reason_type="EXPIRY_DAY",
            message="Today is the contract expiry day. High theta decay and rapid option pricing convergence are active."
        ))
    elif days == 1:
        score += 65.0
        required_conditions.append("Expiry Eve (days_remaining == 1)")
        reasons.append(StrategyReason(
            reason_type="EXPIRY_EVE",
            message="Tomorrow is expiry day. Premium decay curve is accelerating rapidly."
        ))
    elif days <= 3:
        score += 35.0
        reasons.append(StrategyReason(
            reason_type="NEAR_EXPIRY",
            message=f"Contract is within {days} days of expiry, starting to exhibit expiry-eve dynamics."
        ))
    else:
        score -= 20.0
        rejected_conditions.append("Far from expiry (days_remaining > 3)")
        reasons.append(StrategyReason(
            reason_type="FAR_EXPIRY",
            message=f"Contract is far from expiry ({days} days remaining). Expiry strategies are invalid."
        ))
        
    # 2. Option liquidity check (Absolute must for expiry pin trading)
    metrics = options.liquidity_metrics if isinstance(options.liquidity_metrics, dict) else {}
    overall_liq = float(metrics.get("overall_liquidity_score", 100.0))
    if overall_liq >= 75.0:
        score += 15.0
        required_conditions.append("Excellent option chain liquidity (liquidity_score >= 75.0)")
        reasons.append(StrategyReason(
            reason_type="HIGH_LIQUIDITY_CONFIRMATION",
            message=f"Strong liquidity score of {overall_liq:.1f} facilitates tight spread capture on zero-day contracts."
        ))
    else:
        score -= 30.0
        rejected_conditions.append("Poor option chain liquidity")
        reasons.append(StrategyReason(
            reason_type="LOW_LIQUIDITY_HAZARD",
            message=f"Low option liquidity score ({overall_liq:.1f}) represents fatal execution hazard on zero-day contracts."
        ))
        warnings.append(StrategyWarning(
            warning_type="EXPIRY_SPREAD_HAZARD",
            message="Wide bid-ask spreads on expiry day will absorb a large fraction of the option premium.",
            severity="HIGH"
        ))
        
    # 3. Volatility considerations on Expiry day
    if market.volatility_state == "EXTREME":
        score -= 20.0
        reasons.append(StrategyReason(
            reason_type="EXTREME_VOLATILITY_EXPIRY",
            message="Extreme volatility increases gamma whip risks dramatically on expiry day."
        ))
        warnings.append(StrategyWarning(
            warning_type="GAMMA_WHIP_HAZARD",
            message="Extreme volatility triggers severe gamma risk, exposing option sellers to unlimited tail risk.",
            severity="HIGH"
        ))
    elif market.volatility_state == "COMPRESSED":
        score += 10.0
        reasons.append(StrategyReason(
            reason_type="COMPRESSED_VOLATILITY_EXPIRY",
            message="Compressed volatility on expiry day supports safe range/pin trading."
        ))
        
    # 4. Session constraints
    is_trading_disabled = not session.is_tradable_time or session.session_type in ["WEEKEND", "HOLIDAY", "POST_MARKET"]
    constraints.append(StrategyConstraint(
        constraint_type="TRADABLE_SESSION",
        message="Active market session must be open and tradable.",
        is_violated=is_trading_disabled
    ))
    
    # 5. Expiry invalidation factor (e.g. past expiry)
    is_past_expiry = days < 0
    constraints.append(StrategyConstraint(
        constraint_type="ACTIVE_CONTRACTS",
        message="Contracts must be currently active and not expired.",
        is_violated=is_past_expiry
    ))
    if is_past_expiry:
        score = 0.0

    final_score = float(round(min(100.0, max(0.0, score)), 2))
    
    if is_trading_disabled or is_past_expiry or overall_liq < 50.0:
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
        strategy_name="EXPIRY",
        suitability_score=final_score,
        suitability_level=suitability_level,
        reasons=reasons,
        warnings=warnings,
        constraints=constraints,
        required_conditions_met=required_conditions,
        rejected_conditions_met=rejected_conditions,
    )
