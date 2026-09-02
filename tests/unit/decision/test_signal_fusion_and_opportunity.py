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
    LevelInfo,
    OpeningRangeContext,
    PriceStructureContext,
    TrendDirection,
)
from src.analytics.regime.models import MarketRegime, RegimeContext
from src.analytics.snapshot.analytics_snapshot import MarketAnalyticsSnapshot
from src.decision.models.decision_models import (
    EntryReadinessStatus,
    SetupType,
    SignalFusionContext,
)
from src.decision.opportunity.opportunity_detection_engine import OpportunityDetectionEngine
from src.decision.signal_fusion.signal_fusion_engine import SignalFusionEngine
from src.market_data.models.quality_enums import DataQualityStatus
from src.prediction.models.prediction_models import (
    ConfidenceBand,
    DirectionClass,
    MagnitudeDistribution,
    PredictionPhase,
    PredictionRecord,
    PredictionSnapshot,
)


def _make_snapshot(
    last_price: float = 24550.0,
    trend: TrendDirection = TrendDirection.BULLISH,
    regime: MarketRegime = MarketRegime.TREND_UP,
    breadth_score: float = 0.40,
    opt_bias: OptionsConfirmationBias = OptionsConfirmationBias.BULLISH,
    breakout_status: BreakoutStatus = BreakoutStatus.NONE,
    or_high: float = 24520.0,
    or_low: float = 24480.0,
    quality: DataQualityStatus = DataQualityStatus.VALID,
) -> MarketAnalyticsSnapshot:
    ps = PriceStructureContext(
        last_price=last_price,
        trend=trend,
        vwap_context=None,
        twap_context=None,
        opening_range=OpeningRangeContext(15, or_high, or_low, or_high - or_low, True, "ABOVE" if last_price > or_high else "INSIDE"),
        gap_context=GapContext(GapType.FLAT, 0.0, 0.0, True, 100.0, 24500.0, 24500.0),
        support_levels=[LevelInfo(price=24500.0, level_type="SUPPORT", source="ROUND_NUMBER", strength=0.8)],
        resistance_levels=[LevelInfo(price=24600.0, level_type="RESISTANCE", source="ROUND_NUMBER", strength=0.8)],
        swings=[],
        breakout=BreakoutContext(breakout_status, or_high if breakout_status != BreakoutStatus.NONE else None, "ORH", 0.1),
        compression=CompressionContext(False, 1.0),
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
        vix_price=13.5,
        state_revision=10,
        quality=quality,
    )


def test_1_signal_fusion_alignment_and_conflict():
    # 1. Aligned Bullish
    snap_bull = _make_snapshot(trend=TrendDirection.BULLISH, opt_bias=OptionsConfirmationBias.BULLISH)
    fusion_bull = SignalFusionEngine.fuse_signals(snap_bull)
    assert fusion_bull.directional_alignment == "BULLISH"
    assert fusion_bull.agreement_score >= 0.70
    assert fusion_bull.conflict_score == 0.0

    # 2. Conflicted: Trend Bullish but Options Bearish
    snap_conf = _make_snapshot(trend=TrendDirection.BULLISH, opt_bias=OptionsConfirmationBias.BEARISH)
    fusion_conf = SignalFusionEngine.fuse_signals(snap_conf)
    assert fusion_conf.conflict_score > 0.0


def test_2_opening_range_breakout_opportunity_classification():
    # Price trading at 24550 above OR High 24520 with bullish alignment
    snap = _make_snapshot(last_price=24550.0, or_high=24520.0, or_low=24480.0)
    fusion = SignalFusionEngine.fuse_signals(snap)

    opp, readiness = OpportunityDetectionEngine.evaluate_opportunity(snap, fusion)

    assert opp.setup == SetupType.OPENING_RANGE_BREAKOUT
    assert readiness == EntryReadinessStatus.READY_FOR_HUMAN_REVIEW
    assert opp.invalidation_level == 24480.0
    assert "OR Low" in opp.invalidation_condition


def test_3_retest_and_trend_continuation_setups():
    # Retest of broken ORH
    snap_retest = _make_snapshot(breakout_status=BreakoutStatus.RETESTING)
    fusion = SignalFusionEngine.fuse_signals(snap_retest)

    opp, readiness = OpportunityDetectionEngine.evaluate_opportunity(snap_retest, fusion)
    assert opp.setup == SetupType.RETEST
    assert readiness == EntryReadinessStatus.WAITING_FOR_TRIGGER
    assert opp.invalidation_level is not None
