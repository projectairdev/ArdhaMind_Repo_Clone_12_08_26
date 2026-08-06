from __future__ import annotations

from typing import List
from src.models.market_context import MarketContext
from src.models.option_context import OptionContext
from src.models.trade_context import SessionContext, ExpiryContext, MarketReadiness


def evaluate_market_readiness(
    market: MarketContext,
    options: OptionContext,
    session: SessionContext,
    expiry: ExpiryContext,
) -> MarketReadiness:
    """
    Deterministically evaluates whether the market environment is suitable for trading.
    This does NOT generate buy/sell signals, but assesses overall platform/market readiness.
    """
    reasons: List[str] = []
    
    # 1. Session Suitability
    session_suitable = False
    if session.is_tradable_time:
        if session.session_type in ["MORNING", "MID_SESSION", "AFTERNOON", "HALF_DAY"]:
            session_suitable = True
            reasons.append("Active trading session with stable liquidity.")
        elif session.session_type == "MARKET_OPEN":
            reasons.append("First 15 minutes of market open features high volatility and wide spreads.")
        elif session.session_type == "CLOSING_SESSION":
            reasons.append("Closing session contains high squaring-off volatility and risk.")
    else:
        reasons.append(f"Market is closed. Session type: {session.session_type}.")

    # 2. Volatility Suitability
    volatility_suitable = True
    vix = market.india_vix
    vol_state = market.volatility_state
    
    if vol_state == "EXTREME" or options.atm_iv > 35.0 or (vix is not None and vix > 30.0):
        volatility_suitable = False
        reasons.append(f"High volatility warning: Volatility state is {vol_state}, ATM IV is {options.atm_iv}%.")
    elif options.atm_iv < 5.0:
        volatility_suitable = False
        reasons.append(f"Low volatility warning: Extremely compressed option premium IV {options.atm_iv}%.")
    else:
        reasons.append("Volatility is within standard operational range.")

    # 3. Liquidity Suitability
    liquidity_suitable = True
    liq_metrics = options.liquidity_metrics
    liq_score = liq_metrics.get("overall_liquidity_score", 100.0)
    avg_spread = liq_metrics.get("average_spread_pct", 0.0)

    if liq_score < 40.0:
        liquidity_suitable = False
        reasons.append(f"Insufficient options liquidity. Liquidity score: {liq_score:.1f}/100.")
    elif avg_spread > 3.0:
        liquidity_suitable = False
        reasons.append(f"Wide option bid-ask spreads: {avg_spread:.2f}%. Execution slippage risk.")
    else:
        reasons.append("Sufficient option chain liquidity and narrow bid-ask spreads.")

    # 4. Trend / Regime Suitability
    trend_suitable = True
    if market.market_regime == "TRENDING" and market.trend_strength < 10.0:
        trend_suitable = False
        reasons.append("Trending regime detected but trend strength is weak.")
    elif market.market_regime == "UNKNOWN":
        trend_suitable = False
        reasons.append("Market regime is undefined or erratic.")
    else:
        reasons.append(f"Stable {market.market_regime} market regime with strength {market.trend_strength:.1f}.")

    # Calculate suitability score out of 100.0
    # Each dimension contributes 25 points if fully suitable.
    score = 0.0
    if session_suitable:
        score += 25.0
    if volatility_suitable:
        score += 25.0
    if liquidity_suitable:
        score += 25.0
    if trend_suitable:
        score += 25.0

    # If the session is totally untradable (weekend, holiday, post-market), is_market_ready is False
    is_ready = (score >= 60.0) and session.is_tradable_time

    return MarketReadiness(
        is_market_ready=is_ready,
        suitability_score=score,
        reasons=reasons,
        session_suitable=session_suitable,
        volatility_suitable=volatility_suitable,
        liquidity_suitable=liquidity_suitable,
        trend_suitable=trend_suitable,
    )
