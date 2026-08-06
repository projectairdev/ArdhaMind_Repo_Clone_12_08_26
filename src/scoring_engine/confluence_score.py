from __future__ import annotations

from src.models import TradeContext, ConfluenceScore
from src.config_engine import Config


def evaluate_confluence_score(context: TradeContext) -> ConfluenceScore:
    """
    Evaluates Confluence Score based on boolean alignments across trend, S/R, options, volatility, and liquidity.
    """
    confluence = context.confluence
    scoring_config = Config.SCORING
    
    weights = scoring_config.get("confluence_weights", {})
    
    # 1. Trend alignment
    trend_confluence_score = 100.0 if confluence.trend_confluence else 0.0
    
    # 2. Support/Resistance alignment
    support_resistance_score = 100.0 if confluence.sr_alignment else 0.0
    
    # 3. Option Bias alignment
    option_bias_score = 100.0 if confluence.option_confluence else 0.0
    
    # 4. Volatility alignment
    volatility_score = 100.0 if confluence.volatility_alignment else 0.0
    
    # 5. Liquidity alignment
    liquidity_score = 100.0 if confluence.liquidity_alignment else 0.0
    
    # Calculate overall weighted score
    w_trend = weights.get("trend_confluence", 0.25)
    w_sr = weights.get("support_resistance", 0.20)
    w_option = weights.get("option_bias", 0.20)
    w_vol = weights.get("volatility", 0.15)
    w_liq = weights.get("liquidity", 0.20)
    
    total_weight = w_trend + w_sr + w_option + w_vol + w_liq
    weighted_sum = (
        trend_confluence_score * w_trend +
        support_resistance_score * w_sr +
        option_bias_score * w_option +
        volatility_score * w_vol +
        liquidity_score * w_liq
    )
    
    overall_confluence_score = float(round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0)
    
    return ConfluenceScore(
        trend_confluence_score=trend_confluence_score,
        support_resistance_score=support_resistance_score,
        option_bias_score=option_bias_score,
        volatility_score=volatility_score,
        liquidity_score=liquidity_score,
        overall_confluence_score=overall_confluence_score,
    )
