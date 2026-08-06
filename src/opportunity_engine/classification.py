from __future__ import annotations

from src.models import (
    TradeContext,
    MarketScore,
    OpportunityClassification,
    OpportunityProfile,
    DirectionalBias,
    OpportunityWarning,
)


def evaluate_directional_bias(context: TradeContext) -> DirectionalBias:
    """
    Determines direction bias cleanly from market trend and option alignments.
    """
    market = context.market
    options = context.options
    
    bias_value = "NEUTRAL"
    description = "Market exhibits neutral directional bias."
    
    if market.trend_direction == "BULLISH" and options.market_option_bias == "BULLISH":
        bias_value = "BULLISH"
        description = "Market and Option Chain exhibit aligned bullish orientation."
    elif market.trend_direction == "BEARISH" and options.market_option_bias == "BEARISH":
        bias_value = "BEARISH"
        description = "Market and Option Chain exhibit aligned bearish orientation."
    elif market.trend_direction == "SIDEWAYS" or options.market_option_bias == "SIDEWAYS":
        bias_value = "SIDEWAYS"
        description = "Sideways congestion detected on spot or option bias."
    elif market.trend_direction != "SIDEWAYS" and options.market_option_bias != "SIDEWAYS":
        # Disaligned but directional
        bias_value = "NEUTRAL"
        description = f"Conflicting signals. Spot trend is {market.trend_direction}, Option bias is {options.market_option_bias}."
        
    return DirectionalBias(value=bias_value, description=description)


def evaluate_strategy_suitability(context: TradeContext, score: MarketScore) -> OpportunityProfile:
    """
    Implements the Strategy Suitability Matrix. Determines the suitability (SUITABLE, UNSUITABLE, NEUTRAL)
    for Momentum, Breakout, Mean Reversion, Range Trading, Scalping, Trend Following, and Expiry Day plays.
    """
    market = context.market
    options = context.options
    expiry = context.expiry
    session = context.session
    confluence = context.confluence
    
    reasons: list[str] = []
    
    # 1. Momentum Strategy
    if market.trend_strength >= 60.0 and market.market_regime == "TRENDING" and market.trend_direction != "SIDEWAYS":
        momentum_suitability = "SUITABLE"
        reasons.append("Momentum: High trend strength & trending regime favor momentum continuation.")
    elif market.market_regime == "SIDEWAYS" or market.trend_strength < 35.0:
        momentum_suitability = "UNSUITABLE"
        reasons.append("Momentum: Sideways regime or low trend strength inhibits momentum plays.")
    else:
        momentum_suitability = "NEUTRAL"
        
    # 2. Breakout Strategy
    if market.volatility_state == "COMPRESSED" or (market.trend_strength >= 65.0 and market.volatility_state == "NORMAL"):
        breakout_suitability = "SUITABLE"
        reasons.append("Breakout: Compressed volatility state indicates a potential high-velocity break.")
    elif market.volatility_state == "EXTREME":
        breakout_suitability = "UNSUITABLE"
        reasons.append("Breakout: Extreme volatility invalidates structured breakout setups.")
    else:
        breakout_suitability = "NEUTRAL"
        
    # 3. Mean Reversion
    if market.market_regime == "SIDEWAYS" or market.volatility_state in ["EXPANDED", "EXTREME"]:
        # Only suitable if spot is far from VWAP or close to outer S/R limits
        mean_reversion_suitability = "SUITABLE"
        reasons.append("Mean Reversion: Sideways regime or expanded volatility structure suggests high reversion probability.")
    elif market.trend_strength >= 70.0 and market.market_regime == "TRENDING":
        mean_reversion_suitability = "UNSUITABLE"
        reasons.append("Mean Reversion: Strong runaway trend makes counter-trend reversion trades highly dangerous.")
    else:
        mean_reversion_suitability = "NEUTRAL"
        
    # 4. Range Trading
    if market.market_regime == "SIDEWAYS" and market.trend_strength < 40.0:
        range_suitability = "SUITABLE"
        reasons.append("Range Trading: Clean sideways channel structure with low trend force detected.")
    elif market.market_regime == "TRENDING" or market.volatility_state == "EXTREME":
        range_suitability = "UNSUITABLE"
        reasons.append("Range Trading: Strong trend structure or extreme volatility makes range bounds unreliable.")
    else:
        range_suitability = "NEUTRAL"
        
    # 5. Scalping
    metrics = options.liquidity_metrics if isinstance(options.liquidity_metrics, dict) else {}
    overall_liq = float(metrics.get("overall_liquidity_score", 100.0))
    spread_pct = float(metrics.get("average_spread_pct", 0.15))
    if overall_liq >= 80.0 and spread_pct <= 0.15 and session.session_type in ["MORNING", "AFTERNOON"]:
        scalping_suitability = "SUITABLE"
        reasons.append("Scalping: Excellent option chain liquidity and tight spreads favor high-frequency scalps.")
    elif spread_pct > 0.40 or not session.is_tradable_time:
        scalping_suitability = "UNSUITABLE"
        reasons.append("Scalping: Wide option spreads or off-hours prohibit scalping.")
    else:
        scalping_suitability = "NEUTRAL"
        
    # 6. Trend Following
    if market.trend_strength >= 55.0 and market.market_regime == "TRENDING" and confluence.overall_confluence:
        trend_following_suitability = "SUITABLE"
        reasons.append("Trend Following: Aligned spot trend and high confluence support trend continuation.")
    elif market.market_regime == "SIDEWAYS" or market.trend_strength < 40.0:
        trend_following_suitability = "UNSUITABLE"
        reasons.append("Trend Following: No distinct trend exists to ride.")
    else:
        trend_following_suitability = "NEUTRAL"
        
    # 7. Expiry Day Play
    if expiry.classification in ["EXPIRY_DAY", "EXPIRY_EVE"] and overall_liq >= 75.0:
        expiry_suitability = "SUITABLE"
        reasons.append("Expiry Play: Close proximity to expiry matches structured premium decay strategies.")
    elif expiry.days_remaining > 5:
        expiry_suitability = "UNSUITABLE"
        reasons.append("Expiry Play: Too many days remaining to exploit rapid expiry decay curves.")
    else:
        expiry_suitability = "NEUTRAL"
        
    # Determine the primary structural opportunity type
    opportunity_type = "NONE"
    if trend_following_suitability == "SUITABLE":
        opportunity_type = "TREND_CONTINUATION"
    elif breakout_suitability == "SUITABLE":
        opportunity_type = "BREAKOUT"
    elif range_suitability == "SUITABLE":
        opportunity_type = "RANGE_BOUND"
    elif mean_reversion_suitability == "SUITABLE":
        opportunity_type = "MEAN_REVERSION"
    elif scalping_suitability == "SUITABLE":
        opportunity_type = "SCALPING"
    elif expiry_suitability == "SUITABLE":
        opportunity_type = "EXPIRY_DAY_PLAY"
        
    return OpportunityProfile(
        opportunity_type=opportunity_type,
        momentum_suitability=momentum_suitability,
        breakout_suitability=breakout_suitability,
        reversal_suitability=mean_reversion_suitability,
        range_suitability=range_suitability,
        scalping_suitability=scalping_suitability,
        trend_following_suitability=trend_following_suitability,
        expiry_suitability=expiry_suitability,
        suitability_reasons=reasons
    )


def evaluate_opportunity_classification(
    context: TradeContext, 
    score: MarketScore, 
    warnings: list[OpportunityWarning]
) -> OpportunityClassification:
    """
    Classifies the present opportunity into EXCELLENT, GOOD, WATCHLIST, WAIT, POOR, or AVOID.
    Contains zero recommendation for trade actions.
    """
    market = context.market
    options = context.options
    session = context.session
    expiry = context.expiry
    confluence = context.confluence
    
    metrics = options.liquidity_metrics if isinstance(options.liquidity_metrics, dict) else {}
    overall_liq = float(metrics.get("overall_liquidity_score", 100.0))
    
    # Pre-checks for critical limits
    high_warnings = [w for w in warnings if w.severity == "HIGH"]
    
    if not session.is_tradable_time or session.session_type in ["WEEKEND", "HOLIDAY"]:
        return OpportunityClassification(
            value="AVOID",
            description="Trading is disabled during non-tradable or holiday sessions."
        )
        
    if overall_liq < 45.0:
        return OpportunityClassification(
            value="AVOID",
            description="Extremely poor option chain liquidity makes trading highly hazardous."
        )
        
    if market.volatility_state == "EXTREME":
        return OpportunityClassification(
            value="AVOID",
            description="Extreme market volatility invalidates structured pricing setups."
        )
        
    if session.session_type == "POST_MARKET" or expiry.days_remaining < 0:
        return OpportunityClassification(
            value="WAIT",
            description="Waiting for active session open or contract rollover."
        )
        
    # Evaluate Quality Tier based on MarketScore and Confluence
    if score.overall_score >= 85.0 and confluence.overall_confluence and len(high_warnings) == 0:
        return OpportunityClassification(
            value="EXCELLENT",
            description="High market score and clean confluences indicate a top-tier market structure."
        )
        
    if score.overall_score >= 70.0 and confluence.overall_confluence:
        return OpportunityClassification(
            value="GOOD",
            description="A highly favorable environment with solid technical and options-chain alignment."
        )
        
    if score.overall_score >= 55.0:
        return OpportunityClassification(
            value="WATCHLIST",
            description="Favorable structure present but incomplete alignment. Keep under watch."
        )
        
    if score.overall_score >= 40.0:
        return OpportunityClassification(
            value="POOR",
            description="Suboptimal environment with significant warnings or technical misalignment."
        )
        
    return OpportunityClassification(
        value="AVOID",
        description="Low market score and excessive risks present. Avoid active setups."
    )
