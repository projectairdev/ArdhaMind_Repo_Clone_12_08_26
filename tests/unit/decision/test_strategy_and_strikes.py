from __future__ import annotations

from datetime import date, datetime, timezone
import pytest

from src.analytics.options.models import (
    BuildupType,
    GreeksContext,
    OptionLiquidityLevel,
    OptionsConfirmationBias,
    OptionsConfirmationContext,
    StrikeIntelligence,
    StrikeStrengthClass,
)
from src.decision.models.decision_models import (
    DecisionRiskLevel,
    RiskAssessment,
    SignalFusionContext,
    StrategySuitability,
)
from src.decision.strategy.strategy_suitability_engine import StrategySuitabilityEngine
from src.market_data.models.quality_enums import DataQualityStatus, OptionType
from tests.unit.decision.test_signal_fusion_and_opportunity import _make_snapshot


def test_1_strategy_suitability_classification():
    # 1. Bullish with normal vix -> LONG_CALL
    snap_bull = _make_snapshot()
    fusion_bull = SignalFusionContext("BULLISH", 0.8, 0.0, ["Bullish"], [], [])
    risk_low = RiskAssessment(DecisionRiskLevel.LOW, [], False, None)

    # Populate strike universe
    strikes = [
        StrikeIntelligence(
            strike=24500.0,
            call_buildup=BuildupType.LONG_BUILDUP,
            put_buildup=BuildupType.SHORT_BUILDUP,
            call_oi=15000,
            put_oi=12000,
            call_oi_change=500,
            put_oi_change=200,
            call_volume=8000,
            put_volume=6000,
            call_greeks=GreeksContext(14.0, 0.50, 0.002, -15.0, 10.0),
            put_greeks=GreeksContext(14.5, -0.50, 0.002, -15.0, 10.0),
            strike_bias=StrikeStrengthClass.BULLISH_STRIKE_CONFIRMATION,
            liquidity=OptionLiquidityLevel.HIGH,
            strength_score=0.8,
        )
    ]
    snap_bull.options_intelligence.strike_universe.extend(strikes)

    strat_bull, cands_bull = StrategySuitabilityEngine.evaluate_strategy(snap_bull, fusion_bull, risk_low)
    assert strat_bull == StrategySuitability.LONG_CALL
    assert len(cands_bull) == 1
    assert cands_bull[0].strike == 24500.0
    assert cands_bull[0].option_type == OptionType.CE

    # 2. Elevated VIX -> DEFINED_RISK_ONLY
    snap_high_vix = _make_snapshot()
    snap_high_vix = snap_bull
    object.__setattr__(snap_high_vix, "vix_price", 19.5)

    strat_high_vix, _ = StrategySuitabilityEngine.evaluate_strategy(snap_high_vix, fusion_bull, risk_low)
    assert strat_high_vix == StrategySuitability.DEFINED_RISK_ONLY
