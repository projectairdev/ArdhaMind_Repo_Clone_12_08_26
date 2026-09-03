from __future__ import annotations

from typing import List, Optional

from src.analytics.breadth.models import MarketBreadthContext
from src.analytics.options.models import OptionsConfirmationBias, OptionsConfirmationContext
from src.analytics.price_structure.models import BreakoutStatus, PriceStructureContext, TrendDirection
from src.analytics.regime.models import MarketRegime, RegimeContext
from src.market_data.models.quality_enums import DataQualityStatus


class MarketRegimeEngine:
    """
    Deterministic market regime classifier.
    Combines Price Structure, Volatility, Market Breadth, and Options Confirmation.
    """

    @staticmethod
    def classify_regime(
        price_structure: PriceStructureContext,
        breadth_context: Optional[MarketBreadthContext] = None,
        options_context: Optional[OptionsConfirmationContext] = None,
        vix_price: Optional[float] = None,
    ) -> RegimeContext:
        """Determines active market regime and supporting evidence."""
        if price_structure.quality == DataQualityStatus.UNAVAILABLE:
            return RegimeContext(
                regime=MarketRegime.INSUFFICIENT_DATA,
                confidence_score=0.0,
                primary_factors=["Price structure unavailable"],
                caution_factors=[],
                quality=DataQualityStatus.UNAVAILABLE,
            )

        primary: List[str] = []
        cautions: List[str] = []

        # 1. Check High Volatility
        if vix_price and vix_price >= 20.0:
            return RegimeContext(
                regime=MarketRegime.HIGH_VOLATILITY,
                confidence_score=0.85,
                primary_factors=[f"India VIX elevated ({vix_price:.2f} >= 20.0)"],
                caution_factors=["Wide price swings expected; range expansion probable"],
                quality=DataQualityStatus.VALID,
            )

        # 2. Check Compression / Squeeze
        if price_structure.compression.is_compressing:
            primary.append(f"Volatility compression active (ratio {price_structure.compression.compression_ratio:.2f} < 0.60)")
            return RegimeContext(
                regime=MarketRegime.COMPRESSION,
                confidence_score=0.80,
                primary_factors=primary,
                caution_factors=["Energy building for potential expansion/breakout"],
                quality=DataQualityStatus.VALID,
            )

        # 3. Check Breakout Attempt
        if price_structure.breakout.status in (BreakoutStatus.BREAKOUT_UP, BreakoutStatus.BREAKDOWN, BreakoutStatus.RETESTING):
            primary.append(f"Active {price_structure.breakout.status.value} from {price_structure.breakout.level_source} ({price_structure.breakout.level_price})")
            return RegimeContext(
                regime=MarketRegime.BREAKOUT_ATTEMPT,
                confidence_score=0.75,
                primary_factors=primary,
                caution_factors=["Awaiting sustained follow-through confirmation"],
                quality=DataQualityStatus.VALID,
            )

        # 4. Check Trend Up vs Trend Down
        trend = price_structure.trend
        opt_bias = options_context.bias if options_context else OptionsConfirmationBias.NEUTRAL
        breadth_score = breadth_context.breadth_summary.weighted_breadth_score if breadth_context else 0.0

        if trend == TrendDirection.BULLISH:
            primary.append("Price structure in higher highs / higher lows uptrend")
            if opt_bias == OptionsConfirmationBias.BULLISH:
                primary.append("Options positioning confirms bullish trajectory")
            elif opt_bias == OptionsConfirmationBias.BEARISH:
                cautions.append("Options positioning conflicts with price uptrend")

            if breadth_score >= 0.2:
                primary.append(f"Broad constituent participation (score: {breadth_score:+.2f})")
            elif breadth_score <= -0.2:
                cautions.append(f"Negative constituent breadth ({breadth_score:+.2f}) during index advance")

            regime = MarketRegime.TREND_UP if len(cautions) == 0 else MarketRegime.CONFLICTED
            conf = 0.85 if regime == MarketRegime.TREND_UP else 0.60
            return RegimeContext(regime, conf, primary, cautions, DataQualityStatus.VALID)

        elif trend == TrendDirection.BEARISH:
            primary.append("Price structure in lower highs / lower lows downtrend")
            if opt_bias == OptionsConfirmationBias.BEARISH:
                primary.append("Options positioning confirms bearish breakdown")
            elif opt_bias == OptionsConfirmationBias.BULLISH:
                cautions.append("Options positioning conflicts with price downtrend")

            if breadth_score <= -0.2:
                primary.append(f"Broad constituent selling (score: {breadth_score:+.2f})")
            elif breadth_score >= 0.2:
                cautions.append(f"Positive constituent breadth ({breadth_score:+.2f}) during index decline")

            regime = MarketRegime.TREND_DOWN if len(cautions) == 0 else MarketRegime.CONFLICTED
            conf = 0.85 if regime == MarketRegime.TREND_DOWN else 0.60
            return RegimeContext(regime, conf, primary, cautions, DataQualityStatus.VALID)

        else:
            primary.append("Price oscillating within intraday boundaries (No persistent directional trend)")
            return RegimeContext(
                regime=MarketRegime.RANGE,
                confidence_score=0.70,
                primary_factors=primary,
                caution_factors=["Mean reversion dominant; avoid trend-chasing"],
                quality=DataQualityStatus.VALID,
            )
