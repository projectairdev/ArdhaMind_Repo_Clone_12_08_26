from __future__ import annotations

from datetime import date, datetime, timezone
import pytest

from src.analytics.snapshot.analytics_snapshot import MarketAnalyticsSnapshot
from src.decision.models.decision_models import (
    DecisionRiskLevel,
    DecisionState,
    OpportunityAssessment,
    RiskAssessment,
    SetupType,
    SignalFusionContext,
)
from src.decision.risk.no_trade_engine import NoTradeEngine
from src.decision.risk.risk_assessment_engine import RiskAssessmentEngine
from src.market_data.models.quality_enums import DataQualityStatus
from tests.unit.decision.test_signal_fusion_and_opportunity import _make_snapshot


def test_1_risk_assessment_levels():
    # 1. Normal conditions -> Low Risk
    snap_normal = _make_snapshot()
    fusion_normal = SignalFusionContext("BULLISH", 0.8, 0.0, ["Trend"], [], [])
    risk_low = RiskAssessmentEngine.assess_risk(snap_normal, fusion_normal)
    assert risk_low.risk_level == DecisionRiskLevel.LOW
    assert risk_low.is_blocked is False

    # 2. Extreme Volatility -> Blocked
    snap_high_vix = _make_snapshot()
    snap_high_vix = MarketAnalyticsSnapshot(
        session_date=snap_high_vix.session_date,
        captured_at=snap_high_vix.captured_at,
        price_structure=snap_high_vix.price_structure,
        market_breadth=snap_high_vix.market_breadth,
        options_intelligence=snap_high_vix.options_intelligence,
        market_regime=snap_high_vix.market_regime,
        vix_price=26.5,
        state_revision=1,
        quality=DataQualityStatus.VALID,
    )
    risk_blocked = RiskAssessmentEngine.assess_risk(snap_high_vix, fusion_normal)
    assert risk_blocked.risk_level == DecisionRiskLevel.BLOCKED
    assert risk_blocked.is_blocked is True


def test_2_no_trade_gating_scenarios():
    snap = _make_snapshot()
    risk_ok = RiskAssessment(DecisionRiskLevel.LOW, [], False, None)

    # 1. High Conflict (> 0.50) -> NO_TRADE
    fusion_conf = SignalFusionContext("NEUTRAL", 0.4, 0.60, [], ["Conflict"], [])
    opp_ok = OpportunityAssessment(SetupType.TREND_CONTINUATION, "WATCH", "Trend", "Trigger", [], 24450.0, "Inv")
    gated, state, reason = NoTradeEngine.evaluate_gate(snap, fusion_conf, opp_ok, risk_ok)
    assert gated is True
    assert state == DecisionState.NO_TRADE

    # 2. Missing Invalidation Level -> NO_TRADE
    fusion_ok = SignalFusionContext("BULLISH", 0.8, 0.0, [], [], [])
    opp_no_inv = OpportunityAssessment(SetupType.TREND_CONTINUATION, "WATCH", "Trend", "Trigger", [], None, "N/A")
    gated_inv, state_inv, _ = NoTradeEngine.evaluate_gate(snap, fusion_ok, opp_no_inv, risk_ok)
    assert gated_inv is True
    assert state_inv == DecisionState.NO_TRADE

    # 3. No Setup -> NO_TRADE
    opp_none = OpportunityAssessment(SetupType.NO_SETUP, "NO_OPPORTUNITY", "Chop", "N/A", [], None, "N/A")
    gated_none, state_none, _ = NoTradeEngine.evaluate_gate(snap, fusion_ok, opp_none, risk_ok)
    assert gated_none is True
    assert state_none == DecisionState.NO_TRADE
