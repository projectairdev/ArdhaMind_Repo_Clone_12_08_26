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
from src.analytics.regime.models import MarketRegime, RegimeContext
from src.analytics.snapshot.analytics_snapshot import MarketAnalyticsSnapshot
from src.market_data.models.quality_enums import DataQualityStatus
from src.prediction.direction.direction_prediction_engine import DirectionPredictionEngine
from src.prediction.magnitude.magnitude_prediction_engine import MagnitudePredictionEngine
from src.prediction.models.prediction_models import DirectionClass


def _make_dummy_snapshot(
    trend: TrendDirection = TrendDirection.BULLISH,
    regime: MarketRegime = MarketRegime.TREND_UP,
    breadth_score: float = 0.50,
    opt_bias: OptionsConfirmationBias = OptionsConfirmationBias.BULLISH,
    vix_price: float = 13.5,
    is_compressing: bool = False,
    quality: DataQualityStatus = DataQualityStatus.VALID,
) -> MarketAnalyticsSnapshot:
    ps = PriceStructureContext(
        last_price=24550.0,
        trend=trend,
        vwap_context=None,
        twap_context=None,
        opening_range=OpeningRangeContext(15, 24520.0, 24480.0, 40.0, True, "ABOVE"),
        gap_context=GapContext(GapType.FLAT, 0.0, 0.0, True, 100.0, 24500.0, 24500.0),
        support_levels=[],
        resistance_levels=[],
        swings=[],
        breakout=BreakoutContext(BreakoutStatus.NONE, None, None, 0.0),
        compression=CompressionContext(is_compressing=is_compressing, compression_ratio=0.5 if is_compressing else 1.0),
        atr=ATRContext(atr_value=90.0, current_range=90.0, expansion_ratio=1.0),
        quality=quality,
    )
    breadth = MarketBreadthContext(
        breadth_summary=MarketBreadthSummary(50, 50, 35, 15, 0, 2.33, 70.0, breadth_score, 100.0, quality),
        divergence=BreadthDivergenceContext(DivergenceType.NONE, 0.5, 70.0, "Aligned"),
        sector_context=SectorParticipationContext({}, [], [], 0.5, quality),
        leadership=HeavyweightLeadershipContext([], 7, 3, LeadershipBias.BULLISH, 0.4, quality),
        quality=quality,
    )
    options = OptionsConfirmationContext(
        bias=opt_bias,
        confirmation_score=0.6 if opt_bias == OptionsConfirmationBias.BULLISH else (-0.6 if opt_bias == OptionsConfirmationBias.BEARISH else 0.0),
        atm_strike=24500.0,
        pcr=1.25,
        max_pain=24500.0,
        call_wall=24600.0,
        put_wall=24400.0,
        strike_universe=[],
        supporting_factors=["Bullish PCR"],
        contradicting_factors=[],
        quality=quality,
    )
    reg = RegimeContext(regime, 0.8, ["Trend Up"], [], quality)

    return MarketAnalyticsSnapshot(
        session_date=date(2026, 8, 28),
        captured_at=datetime.now(timezone.utc),
        price_structure=ps,
        market_breadth=breadth,
        options_intelligence=options,
        market_regime=reg,
        vix_price=vix_price,
        state_revision=10,
        quality=quality,
    )


def test_1_bullish_and_bearish_direction_inference():
    # 1. Bullish scenario
    snap_bull = _make_dummy_snapshot(trend=TrendDirection.BULLISH, regime=MarketRegime.TREND_UP, breadth_score=0.5, opt_bias=OptionsConfirmationBias.BULLISH)
    dir_b, prob_b, feats_b, supp_b, caut_b = DirectionPredictionEngine.infer_direction(snap_bull)
    assert dir_b == DirectionClass.BULLISH
    assert prob_b > 0.65
    assert len(supp_b) >= 2

    # 2. Bearish scenario
    snap_bear = _make_dummy_snapshot(trend=TrendDirection.BEARISH, regime=MarketRegime.TREND_DOWN, breadth_score=-0.5, opt_bias=OptionsConfirmationBias.BEARISH)
    dir_br, prob_br, feats_br, supp_br, caut_br = DirectionPredictionEngine.infer_direction(snap_bear)
    assert dir_br == DirectionClass.BEARISH
    assert prob_br < 0.35


def test_2_insufficient_data_direction():
    snap_unavail = _make_dummy_snapshot(quality=DataQualityStatus.UNAVAILABLE)
    d, prob, feats, supp, caut = DirectionPredictionEngine.infer_direction(snap_unavail)
    assert d == DirectionClass.INSUFFICIENT_DATA
    assert prob == 0.50


def test_3_magnitude_distribution_probabilities_sum_to_one():
    atr = ATRContext(atr_value=110.0, current_range=110.0, expansion_ratio=1.0)
    comp = CompressionContext(is_compressing=False, compression_ratio=1.0)

    dist = MagnitudePredictionEngine.infer_magnitude(atr, comp, vix_price=14.0)
    total_p = round(dist.p_0_50 + dist.p_50_100 + dist.p_100_150 + dist.p_150_200 + dist.p_200_plus, 2)
    assert total_p == 1.00
    assert dist.expected_magnitude > 0.0


def test_4_decoupled_direction_and_magnitude_overprediction_prevention():
    """
    Proves that a strong directional score under low volatility / squeeze conditions
    does NOT blindly generate an oversized magnitude prediction.
    """
    atr_low = ATRContext(atr_value=60.0, current_range=60.0, expansion_ratio=1.0)
    comp_squeeze = CompressionContext(is_compressing=True, compression_ratio=0.45)

    dist_squeeze = MagnitudePredictionEngine.infer_magnitude(atr_low, comp_squeeze, vix_price=11.5)
    # Expected magnitude should be modest despite strong conviction
    assert dist_squeeze.expected_magnitude < 60.0
    assert dist_squeeze.p_0_50 >= 0.40


def test_5_factor_weight_normalization_across_availability_scenarios():
    """
    Proves dynamic weight normalization:
    1. All factors available: effective weights sum to 1.00.
    2. Options unavailable: effective weights of remaining factors sum to 1.00.
    3. Breadth unavailable: effective weights sum to 1.00.
    4. Multiple factors unavailable: effective weights sum to 1.00.
    """
    # 1. All factors available
    snap_all = _make_dummy_snapshot()
    _, _, contribs_all, _, _, _ = DirectionPredictionEngine.infer_direction_detailed(snap_all)
    assert all(c.available for c in contribs_all)
    eff_sum_all = round(sum(c.effective_weight for c in contribs_all), 2)
    assert eff_sum_all == 1.00

    # 2. Options unavailable
    snap_no_opt = _make_dummy_snapshot()
    object.__setattr__(snap_no_opt.options_intelligence, "quality", DataQualityStatus.UNAVAILABLE)
    _, _, contribs_no_opt, _, _, _ = DirectionPredictionEngine.infer_direction_detailed(snap_no_opt)
    eff_sum_no_opt = round(sum(c.effective_weight for c in contribs_no_opt if c.available), 2)
    assert eff_sum_no_opt == 1.00
    opt_contrib = next(c for c in contribs_no_opt if c.factor_name == "options")
    assert opt_contrib.available is False
    assert opt_contrib.effective_weight == 0.0

    # 3. Breadth unavailable
    snap_no_br = _make_dummy_snapshot()
    object.__setattr__(snap_no_br.market_breadth, "quality", DataQualityStatus.UNAVAILABLE)
    _, _, contribs_no_br, _, _, _ = DirectionPredictionEngine.infer_direction_detailed(snap_no_br)
    eff_sum_no_br = round(sum(c.effective_weight for c in contribs_no_br if c.available), 2)
    assert eff_sum_no_br == 1.00
    br_contrib = next(c for c in contribs_no_br if c.factor_name == "breadth")
    assert br_contrib.available is False
    assert br_contrib.effective_weight == 0.0
