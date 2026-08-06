from __future__ import annotations

from typing import List
from src.models.market_score import MarketScore
from src.models.opportunity_context import OpportunityContext
from src.models.market_context import MarketContext
from src.models.evening_report import MarketSummary, TomorrowOutlook


def compile_market_summary(
    market_score: MarketScore,
    opportunity_context: OpportunityContext,
    market_context: MarketContext | None = None,
) -> MarketSummary:
    spot_price = market_context.current_spot if market_context else 0.0
    vix_price = (
        market_context.india_vix
        if (market_context and market_context.india_vix is not None)
        else 0.0
    )
    regime = market_context.market_regime if market_context else "UNKNOWN"
    trend_direction = market_context.trend_direction if market_context else "UNKNOWN"

    return MarketSummary(
        spot_price=spot_price,
        vix_price=vix_price,
        regime=regime,
        trend_direction=trend_direction,
        market_score=market_score.overall_score if market_score else 0.0,
        market_grade=market_score.letter_grade if market_score else "N/A",
        session_type=market_context.trading_session if market_context else "NORMAL",
    )


def compile_tomorrow_outlook(
    opportunity_context: OpportunityContext,
    market_context: MarketContext | None = None,
) -> TomorrowOutlook:
    directional_bias = (
        opportunity_context.directional_bias.value
        if opportunity_context and opportunity_context.directional_bias
        else "NEUTRAL"
    )
    outlook_classification = (
        opportunity_context.classification.value
        if opportunity_context and opportunity_context.classification
        else "WAIT"
    )
    opportunity_strength = (
        opportunity_context.strength.overall_strength
        if opportunity_context and opportunity_context.strength
        else 0.0
    )
    key_support_levels = market_context.support_levels if market_context else []
    key_resistance_levels = (
        market_context.resistance_levels if market_context else []
    )
    description = (
        opportunity_context.classification.description
        if opportunity_context and opportunity_context.classification
        else ""
    )

    return TomorrowOutlook(
        directional_bias=directional_bias,
        outlook_classification=outlook_classification,
        opportunity_strength=opportunity_strength,
        key_support_levels=key_support_levels,
        key_resistance_levels=key_resistance_levels,
        description=description,
    )
