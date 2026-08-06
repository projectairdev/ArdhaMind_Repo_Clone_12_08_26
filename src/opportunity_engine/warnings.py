from __future__ import annotations

from src.models import TradeContext, OpportunityWarning


def evaluate_warnings(context: TradeContext) -> list[OpportunityWarning]:
    """
    Evaluates market and option parameters to identify structured warnings.
    """
    warnings: list[OpportunityWarning] = []
    market = context.market
    options = context.options
    expiry = context.expiry
    session = context.session
    
    # 1. Resistance Proximity
    if market.trend_direction == "BULLISH" and market.current_spot > 0:
        resistance_levels = market.resistance_levels or []
        for level in resistance_levels:
            dist_pct = (level - market.current_spot) / market.current_spot * 100.0
            if 0.0 < dist_pct <= 0.4:
                warnings.append(OpportunityWarning(
                    warning_type="RESISTANCE_PROXIMITY",
                    message=f"Spot is extremely close to major resistance level {level} ({dist_pct:.2f}% distance). Bullish extension room is limited.",
                    severity="HIGH"
                ))
                break
                
    # 2. Support Proximity
    if market.trend_direction == "BEARISH" and market.current_spot > 0:
        support_levels = market.support_levels or []
        for level in support_levels:
            dist_pct = (market.current_spot - level) / market.current_spot * 100.0
            if 0.0 < dist_pct <= 0.4:
                warnings.append(OpportunityWarning(
                    warning_type="SUPPORT_PROXIMITY",
                    message=f"Spot is extremely close to major support level {level} ({dist_pct:.2f}% distance). Bearish downside room is limited.",
                    severity="HIGH"
                ))
                break
                
    # 3. Low Liquidity
    metrics = options.liquidity_metrics if isinstance(options.liquidity_metrics, dict) else {}
    overall_liq_score = float(metrics.get("overall_liquidity_score", 100.0))
    spread_pct = float(metrics.get("average_spread_pct", 0.15))
    if overall_liq_score < 60.0 or spread_pct > 0.40:
        severity = "HIGH" if overall_liq_score < 45.0 else "MEDIUM"
        warnings.append(OpportunityWarning(
            warning_type="LOW_LIQUIDITY",
            message=f"Option chain liquidity is suboptimal. Average spread is {spread_pct:.2f}% and liquidity score is {overall_liq_score:.1f}.",
            severity=severity
        ))
        
    # 4. High IV
    if options.atm_iv > 22.0:
        warnings.append(OpportunityWarning(
            warning_type="HIGH_IV",
            message=f"ATM IV is high ({options.atm_iv:.1f}%), implying expensive options premium and susceptibility to IV crush.",
            severity="MEDIUM"
        ))
        
    # 5. Extreme Volatility
    if market.volatility_state == "EXTREME":
        warnings.append(OpportunityWarning(
            warning_type="EXTREME_VOLATILITY",
            message="Market is exhibiting extreme/unstable volatility. Normal technical structures may fail.",
            severity="HIGH"
        ))
        
    # 6. Expiry Risk
    if expiry.days_remaining == 0:
        warnings.append(OpportunityWarning(
            warning_type="EXPIRY_RISK",
            message="Today is Expiry Day. Extreme theta decay and gamma risk are present.",
            severity="HIGH"
        ))
    elif expiry.days_remaining == 1:
        warnings.append(OpportunityWarning(
            warning_type="EXPIRY_RISK",
            message="Tomorrow is Expiry Day (Expiry Eve). Accelerated premium decay is in progress.",
            severity="MEDIUM"
        ))
        
    # 7. Gap Risk
    if session.session_type == "CLOSING_SESSION":
        warnings.append(OpportunityWarning(
            warning_type="GAP_RISK",
            message="Current session is CLOSING_SESSION. Over-night holding exposes the trade to next-day open gaps.",
            severity="MEDIUM"
        ))
        
    # 8. Weak Option Confirmation
    if market.trend_direction != "SIDEWAYS" and options.market_option_bias != market.trend_direction:
        warnings.append(OpportunityWarning(
            warning_type="WEAK_OPTION_CONFIRMATION",
            message=f"Market trend is {market.trend_direction} but option chain bias is {options.market_option_bias}. Alignment is missing.",
            severity="HIGH"
        ))
        
    # 9. Conflicting Market Structure
    if market.market_regime == "SIDEWAYS" and market.trend_strength > 65.0:
        warnings.append(OpportunityWarning(
            warning_type="CONFLICTING_MARKET_STRUCTURE",
            message=f"Market regime is classified as SIDEWAYS but trend strength is high ({market.trend_strength:.1f}). Possible regime transition.",
            severity="LOW"
        ))
        
    return warnings
