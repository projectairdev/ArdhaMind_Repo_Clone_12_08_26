"""
tests/test_market_decision_summary_composer.py

Comprehensive test suite for the Market Decision Summary Composer, validating:
- Field-by-field source mappings (Bias, Setup, Strike, Entry, Confidence, Liquidity, DQ, Risk)
- Configurable DecisionLiquidityPolicy (Mandatory Correction #1)
- Broker Auth independence preserving analytical intelligence (Mandatory Correction #2)
- Stable Decision Identity preventing card churn (Mandatory Correction #3)
- Degraded and closed market safety scenarios
"""
import pytest
from src.intelligence_engine.decision_summary_composer import (
    DecisionLiquidityPolicy,
    FieldStatus,
    MarketDecisionSummary,
    MarketDecisionSummaryComposer,
)


@pytest.fixture
def base_context():
    return {
        "session_date": "2026-08-21",
        "market_state": "LIVE",
        "market_closed": False,
        "freshness_state": "FRESH",
        "broker_auth_state": "AUTHENTICATED",
        "data_quality_status": "HIGH",
        "overall_risk": "MODERATE",
        "active_subtab": "LIVE_GUIDE",
        "sequence": 10420,
        "runtime_id": "test-runtime-1",
        "market_context": {
            "current_spot": 24275.50,
            "trend": "BULLISH",
            "vwap": 24250.00,
            "india_vix": 12.45
        },
        "option_context": {
            "status": "AVAILABLE",
            "put_wall": 24200,
            "call_wall": 24500
        },
        "breadth": {
            "advances": 32,
            "declines": 17,
            "status": "AVAILABLE"
        },
        "unified_intelligence": {
            "market_bias": "BULLISH",
            "decision_zones": {
                "invalidation": "24240.00"
            }
        },
        "opportunities": [
            {
                "opportunity_id": "OPP-20260821-001",
                "strategy_id": "PULLBACK_CONTINUATION",
                "strategy_name": "PULLBACK CONTINUATION",
                "target_strike": "24,300 CE",
                "contract": {
                    "symbol": "24300CE",
                    "bid_ask_spread_bps": 85.0,
                    "volume": 15000,
                    "oi": 120000
                },
                "entry_trigger_statement": "Break above 24,310 with Breadth >30",
                "invalidation_statement": "Close below 24,240",
                "confirmation_conditions": ["Breadth > 30", "5m candle close"],
                "scores": {
                    "confidence_score": 78
                },
                "risk_grade": "MODERATE",
                "status": "ACTIVE"
            }
        ]
    }


def test_composer_ready_bullish_scenario(base_context):
    """Verify that a fully qualified bullish opportunity evaluates to READY_FOR_APPROVAL."""
    summary = MarketDecisionSummaryComposer.compose(base_context)
    
    assert summary.status == "READY_FOR_APPROVAL"
    assert summary.bias.value == "BULLISH"
    assert summary.bias.status == "AVAILABLE"
    assert summary.setup.value == "PULLBACK CONTINUATION"
    assert summary.strike.value == "24300CE"
    assert summary.strike.status == "AVAILABLE"
    assert summary.confidence.value == 78
    assert summary.liquidity.value == "EXCELLENT"
    assert summary.data_quality.value == "HIGH"
    assert summary.risk.value == "MODERATE"
    assert summary.invalidation == "Close below 24,240"
    assert len(summary.supporting_evidence) >= 3
    assert len(summary.blocking_reasons) == 0


def test_mandatory_correction_1_configurable_liquidity_policy(base_context):
    """Verify that DecisionLiquidityPolicy thresholds are configurable and not hardcoded."""
    # Strict policy: max spread 50 bps (our contract has 85 bps)
    strict_policy = DecisionLiquidityPolicy(
        policy_version="2.0.0-strict",
        max_spread_bps=50.0,
        min_volume=50000
    )
    summary = MarketDecisionSummaryComposer.compose(base_context, liquidity_policy=strict_policy)
    
    assert summary.liquidity.value == "FAIR"  # fails spread and volume, passes OI
    assert summary.provenance["liquidity_policy_version"] == "2.0.0-strict"


def test_mandatory_correction_2_broker_disconnected_preserves_intelligence(base_context):
    """
    Mandatory Safety Test: When broker is disconnected but market feeds are fresh,
    all analytical intelligence must remain fully visible, status set to QUALIFYING,
    and BROKER_AUTH_REQUIRED surfaced in blocking reasons.
    """
    base_context["broker_auth_state"] = "DISCONNECTED"
    summary = MarketDecisionSummaryComposer.compose(base_context)
    
    # Intelligence must NOT disappear!
    assert summary.bias.value == "BULLISH"
    assert summary.setup.value == "PULLBACK CONTINUATION"
    assert summary.strike.value == "24300CE"
    assert summary.entry_condition.value["formatted_statement"] == "Break above 24,310 with Breadth >30"
    assert summary.confidence.value == 78
    assert summary.liquidity.value == "EXCELLENT"
    assert summary.data_quality.value == "HIGH"
    assert summary.risk.value == "MODERATE"
    
    # Status cannot be READY_FOR_APPROVAL without broker auth
    assert summary.status == "QUALIFYING"
    assert "BROKER_AUTH_REQUIRED" in summary.blocking_reasons


def test_safety_options_stale_degradation(base_context):
    """Verify field-level degradation when options data is stale."""
    base_context["option_context"]["status"] = "STALE"
    summary = MarketDecisionSummaryComposer.compose(base_context)
    
    # Spot trend and setup remain visible
    assert summary.bias.value == "BULLISH"
    assert summary.setup.value == "PULLBACK CONTINUATION"
    
    # Options-dependent fields degrade safely
    assert summary.strike.status == "WAITING_FOR_OPTIONS_CONFIRMATION"
    assert summary.liquidity.status == "STALE"
    assert summary.status == "BLOCKED"
    assert "OPTIONS_FEED_STALE" in summary.blocking_reasons


def test_safety_market_closed_behavior(base_context):
    """Verify behavior outside live hours and on weekends."""
    base_context["market_closed"] = True
    base_context["market_state"] = "CLOSED"
    base_context["active_subtab"] = "TOMORROW_PLAN"
    
    summary = MarketDecisionSummaryComposer.compose(base_context)
    
    assert summary.status == "MARKET_CLOSED"
    assert summary.bias.value == "BULLISH"
    assert summary.strike.status == "REQUIRES_LIVE_OPTIONS"
    assert summary.liquidity.status == "UNAVAILABLE"


def test_mandatory_correction_3_stable_decision_identity(base_context):
    """Verify that minor spot price ticks or confidence changes do not cause decision ID churn."""
    summary1 = MarketDecisionSummaryComposer.compose(base_context)
    
    # Minor spot tick (e.g. +2 points)
    base_context["market_context"]["current_spot"] = 24277.10
    base_context["opportunities"][0]["scores"]["confidence_score"] = 79
    summary2 = MarketDecisionSummaryComposer.compose(base_context)
    
    # Same decision ID!
    assert summary1.decision_id == summary2.decision_id == "DEC-OPP-20260821-001"


def test_no_opportunity_fallback_to_waiting(base_context):
    """Verify that when no qualified opportunity exists, status becomes WAITING."""
    base_context["opportunities"] = []
    summary = MarketDecisionSummaryComposer.compose(base_context)
    
    assert summary.status == "WAITING"
    assert summary.setup.status == "NOT_QUALIFIED"
    assert summary.setup.value == "NO_VALID_SETUP"
    assert summary.strike.status == "NOT_QUALIFIED"
