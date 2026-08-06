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


def evaluate_scalping(
    trade_context: TradeContext,
    market_score: MarketScore,
    opportunity_context: OpportunityContext,
) -> StrategyScore:
    """
    Evaluates scalping strategy suitability for the current market environment.
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
    
    # 1. Option Chain spreads & overall liquidity (absolutely critical for scalping)
    metrics = options.liquidity_metrics if isinstance(options.liquidity_metrics, dict) else {}
    overall_liq = float(metrics.get("overall_liquidity_score", 100.0))
    spread_pct = float(metrics.get("average_spread_pct", 0.15))
    
    if overall_liq >= 80.0 and spread_pct <= 0.15:
        score += 25.0
        required_conditions.append(f"Excellent liquidity and tight spread (spread={spread_pct:.2f}% <= 0.15%)")
        reasons.append(StrategyReason(
            reason_type="HIGH_LIQUIDITY_LOW_SPREAD",
            message=f"Outstanding option chain liquidity ({overall_liq:.1f}) and tight spreads ({spread_pct:.2f}%) enable ultra-low slippage entry/exits."
        ))
    elif spread_pct > 0.30:
        score -= 30.0
        rejected_conditions.append("Wide option spread (average_spread_pct > 0.30%)")
        reasons.append(StrategyReason(
            reason_type="WIDE_SPREAD_HAZARD",
            message=f"Bid-ask spread ({spread_pct:.2f}%) is too wide for scalping. High frictional cost."
        ))
        warnings.append(StrategyWarning(
            warning_type="HIGH_FRICTION_COST",
            message="Wide option spreads will erode quick scalp profits immediately.",
            severity="HIGH"
        ))
    else:
        reasons.append(StrategyReason(
            reason_type="NORMAL_LIQUIDITY",
            message=f"Option chain liquidity is moderate (spread: {spread_pct:.2f}%)."
        ))
        
    # 2. Session Type check (scalpers thrive in active morning or afternoon blocks, avoid closing)
    if session.session_type in ["MORNING", "AFTERNOON"]:
        score += 15.0
        required_conditions.append("Active regular session")
        reasons.append(StrategyReason(
            reason_type="ACTIVE_SESSION",
            message=f"Active {session.session_type} session exhibits strong continuous volume flow."
        ))
    elif session.session_type == "CLOSING_SESSION":
        score -= 20.0
        rejected_conditions.append("Session is CLOSING_SESSION")
        reasons.append(StrategyReason(
            reason_type="CLOSING_SESSION_HAZARD",
            message="Closing session exhibits erratic auction flows and widening spreads, unsafe for scalps."
        ))
        warnings.append(StrategyWarning(
            warning_type="CLOSING_AUCTION_HAZARD",
            message="Erratic price fluctuations during the closing session could disrupt scalping targets.",
            severity="MEDIUM"
        ))
        
    # 3. Volatility state check
    if market.volatility_state == "EXTREME":
        score -= 15.0
        reasons.append(StrategyReason(
            reason_type="EXTREME_VOL_SCALPING",
            message="Extreme market volatility creates rapid price skips and unsafe fills."
        ))
        warnings.append(StrategyWarning(
            warning_type="SLIPPAGE_RISK",
            message="High volatility causes sudden order book gaps and severe slippage on execution.",
            severity="HIGH"
        ))
    elif market.volatility_state == "NORMAL":
        score += 10.0
        reasons.append(StrategyReason(
            reason_type="NORMAL_VOL_SCALPING",
            message="Normal volatility supports stable order books and predictable fill prices."
        ))
        
    # 4. Session constraints
    is_trading_disabled = not session.is_tradable_time or session.session_type in ["WEEKEND", "HOLIDAY", "POST_MARKET"]
    constraints.append(StrategyConstraint(
        constraint_type="TRADABLE_SESSION",
        message="Active market session must be open and tradable.",
        is_violated=is_trading_disabled
    ))
    
    # 5. Extreme low liquidity constraint
    is_liq_unusable = overall_liq < 45.0
    constraints.append(StrategyConstraint(
        constraint_type="MINIMUM_LIQUIDITY",
        message="Option chain liquidity must be at least 45.0 to scalp safely.",
        is_violated=is_liq_unusable
    ))
    if is_liq_unusable:
        score = 0.0

    final_score = float(round(min(100.0, max(0.0, score)), 2))
    
    if is_trading_disabled or is_liq_unusable or spread_pct > 0.40:
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
        strategy_name="SCALPING",
        suitability_score=final_score,
        suitability_level=suitability_level,
        reasons=reasons,
        warnings=warnings,
        constraints=constraints,
        required_conditions_met=required_conditions,
        rejected_conditions_met=rejected_conditions,
    )
