from __future__ import annotations

from datetime import date, datetime, timezone
import pytest

from src.analytics.breadth.models import (
    BreadthDivergenceContext,
    DivergenceType,
    HeavyweightLeadershipContext,
    LeadershipBias,
    MarketBreadthContext,
    MarketBreadthSummary,
    SectorParticipationContext,
)
from src.analytics.options.models import (
    OptionsConfirmationBias,
    OptionsConfirmationContext,
)
from src.analytics.price_structure.models import (
    ATRContext,
    BreakoutContext,
    BreakoutStatus,
    CompressionContext,
    GapContext,
    GapType,
    OpeningRangeContext,
    PriceStructureContext,
    TrendDirection,
)
from src.analytics.regime.market_regime_engine import MarketRegimeEngine
from src.analytics.regime.models import MarketRegime
from src.market_data.models.quality_enums import DataQualityStatus


def _dummy_ps(
    trend: TrendDirection = TrendDirection.BULLISH,
    is_compressing: bool = False,
    breakout_status: BreakoutStatus = BreakoutStatus.NONE,
) -> PriceStructureContext:
    return PriceStructureContext(
        last_price=24550.0,
        trend=trend,
        vwap_context=None,
        twap_context=None,
        opening_range=OpeningRangeContext(15, 24520.0, 24480.0, 40.0, True, "ABOVE"),
        gap_context=GapContext(GapType.FLAT, 0.0, 0.0, True, 100.0, 24500.0, 24500.0),
        support_levels=[],
        resistance_levels=[],
        swings=[],
        breakout=BreakoutContext(breakout_status, 24520.0 if breakout_status != BreakoutStatus.NONE else None, "ORH", 0.1),
        compression=CompressionContext(is_compressing=is_compressing, compression_ratio=0.5 if is_compressing else 1.0),
        atr=ATRContext(20.0, 20.0, 1.0),
        quality=DataQualityStatus.VALID,
    )


def test_1_high_volatility_regime():
    ps = _dummy_ps()
    regime = MarketRegimeEngine.classify_regime(ps, vix_price=22.5)
    assert regime.regime == MarketRegime.HIGH_VOLATILITY


def test_2_compression_regime():
    ps = _dummy_ps(is_compressing=True)
    regime = MarketRegimeEngine.classify_regime(ps, vix_price=13.0)
    assert regime.regime == MarketRegime.COMPRESSION


def test_3_trend_up_regime():
    ps = _dummy_ps(trend=TrendDirection.BULLISH)
    opt_ctx = OptionsConfirmationContext(
        bias=OptionsConfirmationBias.BULLISH,
        confirmation_score=0.7,
        atm_strike=24500.0,
        pcr=1.25,
        max_pain=24500.0,
        call_wall=24600.0,
        put_wall=24400.0,
        strike_universe=[],
        supporting_factors=["Bullish PCR"],
        contradicting_factors=[],
        quality=DataQualityStatus.VALID,
    )
    regime = MarketRegimeEngine.classify_regime(ps, options_context=opt_ctx, vix_price=13.0)
    assert regime.regime == MarketRegime.TREND_UP
    assert regime.confidence_score >= 0.8


def test_4_range_regime():
    ps = _dummy_ps(trend=TrendDirection.SIDEWAYS)
    regime = MarketRegimeEngine.classify_regime(ps, vix_price=13.0)
    assert regime.regime == MarketRegime.RANGE
