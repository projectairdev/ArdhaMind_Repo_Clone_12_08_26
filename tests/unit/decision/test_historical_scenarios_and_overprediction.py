from __future__ import annotations

from datetime import date, datetime, timezone
import inspect
import pytest

from src.analytics.breadth.models import DivergenceType
from src.analytics.options.models import OptionLiquidityLevel, OptionsConfirmationBias, StrikeIntelligence
from src.analytics.price_structure.models import BreakoutStatus, TrendDirection
from src.analytics.regime.models import MarketRegime
from src.analytics.snapshot.analytics_snapshot import MarketAnalyticsSnapshot
from src.decision.decision.decision_engine import DecisionEngine
from src.decision.models.decision_models import DecisionRiskLevel, DecisionState, SetupType
from src.market_data.models.quality_enums import DataQualityStatus, OptionType
from src.prediction.models.prediction_models import (
    ConfidenceBand,
    DirectionClass,
    MagnitudeDistribution,
    PredictionPhase,
    PredictionRecord,
    PredictionSnapshot,
)
from tests.unit.decision.test_decision_engine_and_products import _make_dummy_pred
from tests.unit.decision.test_signal_fusion_and_opportunity import _make_snapshot


def test_1_historical_scenario_fixtures_matrix():
    # Scenario 1: Strong trend-up day
    s1 = _make_snapshot(last_price=24550.0, or_high=24520.0, or_low=24480.0)
    d1 = DecisionEngine.evaluate_decision(s1, _make_dummy_pred(s1.session_date))
    assert d1.decision_state == DecisionState.READY_FOR_HUMAN_REVIEW
    assert d1.setup.setup == SetupType.OPENING_RANGE_BREAKOUT

    # Scenario 2: Strong trend-down day
    s2 = _make_snapshot(last_price=24450.0, trend=TrendDirection.BEARISH, regime=MarketRegime.TREND_DOWN, breadth_score=-0.40, or_high=24520.0, or_low=24480.0, opt_bias=OptionsConfirmationBias.BEARISH)
    d2 = DecisionEngine.evaluate_decision(s2)
    assert d2.decision_state == DecisionState.READY_FOR_HUMAN_REVIEW
    assert d2.setup.setup == SetupType.BREAKDOWN

    # Scenario 3: Range day (price inside OR, sideways trend)
    s3 = _make_snapshot(last_price=24500.0, trend=TrendDirection.SIDEWAYS, or_high=24520.0, or_low=24480.0)
    d3 = DecisionEngine.evaluate_decision(s3)
    assert d3.decision_state == DecisionState.NO_TRADE

    # Scenario 4: False breakout / Retest forming
    s4 = _make_snapshot(last_price=24520.0, breakout_status=BreakoutStatus.RETESTING)
    d4 = DecisionEngine.evaluate_decision(s4)
    assert d4.decision_state == DecisionState.WAIT
    assert d4.setup.setup == SetupType.RETEST

    # Scenario 5: Extreme Volatility
    s5 = _make_snapshot()
    object.__setattr__(s5, "vix_price", 27.5)
    d5 = DecisionEngine.evaluate_decision(s5)
    assert d5.decision_state == DecisionState.BLOCKED

    # Scenario 6: Stale feed / Unavailable data
    s6 = _make_snapshot(quality=DataQualityStatus.UNAVAILABLE)
    d6 = DecisionEngine.evaluate_decision(s6)
    assert d6.decision_state == DecisionState.BLOCKED


def test_2_overprediction_safety_behavior():
    """
    CRITICAL OVERPREDICTION SAFETY TEST:
    Pre-market prediction forecast: Bullish, expected move +140 points, High confidence.
    Live intraday market evidence: Narrow range, sideways chop within opening range (24500 inside 24480-24520).

    The DecisionEngine MUST NOT blindly issue a BUY / READY signal simply because
    the pre-market prediction expected a huge move. Live structural evidence must strictly govern!
    """
    s_live_chop = _make_snapshot(last_price=24500.0, trend=TrendDirection.SIDEWAYS, or_high=24520.0, or_low=24480.0)

    # Bullish large forecast
    pred_large = _make_dummy_pred(s_live_chop.session_date)

    dec = DecisionEngine.evaluate_decision(s_live_chop, pred_large)

    # Must be NO_TRADE or WAIT; NEVER READY_FOR_HUMAN_REVIEW
    assert dec.decision_state in (DecisionState.NO_TRADE, DecisionState.WAIT)
    assert dec.decision_state != DecisionState.READY_FOR_HUMAN_REVIEW


def test_3_read_only_architectural_inspection():
    """Verifies that src/decision contains zero execution/trading API calls."""
    import src.decision.decision.decision_engine as de_mod
    import src.decision.opportunity.opportunity_detection_engine as opp_mod
    import src.decision.risk.risk_assessment_engine as rsk_mod
    import src.decision.strategy.strategy_suitability_engine as str_mod
    import src.decision.products.product_coordinator as prod_mod

    for mod in (de_mod, opp_mod, rsk_mod, str_mod, prod_mod):
        source = inspect.getsource(mod)
        forbidden = [
            "place_order",
            "modify_order",
            "cancel_order",
            "exit_order",
            "buy(",
            "sell(",
            "order_id",
            "execute_trade",
            "portfolio.mutate",
        ]
        for f in forbidden:
            assert f not in source
