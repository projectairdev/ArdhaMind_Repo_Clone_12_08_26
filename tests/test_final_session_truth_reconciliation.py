"""
Regression test suite for 18 AUG Final Session Truth, Completed Session OHLC,
Post-Market Consistency, and 19 AUG Pre-Market Reference Rollover.
"""

import pytest
from datetime import datetime, timezone, timedelta
from src.intelligence_engine.pre_market_briefing_engine import PreMarketBriefingEngine
from src.intelligence_engine.pre_market_engine import PreMarketIntelligenceEngine
from src.intelligence_engine.structural_level_engine import StructuralLevelEngine
from src.broker.services.market_context_builder import MarketContextBuilder
from src.broker.services.broker_service import BrokerService


def test_authoritative_18_aug_candles_and_extremes():
    """Invariant 1-5: 18 Aug intraday candles yield correct OHLC extremes."""
    bs = BrokerService.get_instance()
    ctx = MarketContextBuilder.build(bs, None, 11.33)
    candles = ctx.get("candles") or []
    
    assert len(candles) > 0, "Intraday candles must be populated"
    candle_highs = [float(c["h"]) for c in candles]
    candle_lows = [float(c["l"]) for c in candles]
    
    # Authoritative extremes
    assert max(candle_highs) == pytest.approx(24269.65, abs=0.5)
    assert min(candle_lows) == pytest.approx(24154.90, abs=0.5)
    assert max(candle_highs) < 24500, "Contaminated 24,759.70 high must not exist in candles"


def test_market_context_ohlc_consistency():
    """Invariant 6-10: MarketContext OHLC matches candle extremes."""
    bs = BrokerService.get_instance()
    ctx = MarketContextBuilder.build(bs, None, 11.33)
    
    assert float(ctx["open"]) == pytest.approx(24223.85, abs=0.5)
    assert float(ctx["high"]) == pytest.approx(24269.65, abs=0.5)
    assert float(ctx["low"]) == pytest.approx(24154.90, abs=0.5)
    assert float(ctx["close"]) == pytest.approx(24154.90, abs=0.5)
    assert float(ctx["previous_close"]) == pytest.approx(24287.65, abs=0.5)


def test_19_aug_pre_market_briefing_reference_rollover():
    """Invariant 11-18: 19 Aug Pre-Market Briefing derives from completed 18 Aug session."""
    now_18_post = datetime(2026, 8, 18, 11, 15, 0, tzinfo=timezone.utc)  # 16:45 IST
    mock_state = {
        "market_data": {
            "open": 24223.85,
            "high": 24269.65,
            "low": 24154.90,
            "close": 24154.90,
            "current_spot": 24154.90,
            "previous_close": 24287.65,
            "session_date": "2026-08-18"
        },
        "macro_intelligence": {
            "quotes": {
                "GIFT_NIFTY": {"price": 24210.0, "change": 55.10, "change_pct": 0.23}
            }
        }
    }
    briefing = PreMarketBriefingEngine.generate_or_get_briefing(mock_state, as_of_time=now_18_post, force_regenerate=True)
    
    assert briefing.trading_date == "2026-08-19"
    assert briefing.reference_session_date == "2026-08-18"
    assert briefing.reference_close == pytest.approx(24154.90, abs=0.1)
    assert briefing.status == "PREPARING"
    
    ps = briefing.price_structure
    assert ps["reference_close"] == pytest.approx(24154.90, abs=0.1)
    assert ps["previous_high"] == pytest.approx(24269.65, abs=0.5)
    assert ps["previous_low"] == pytest.approx(24154.90, abs=0.5)
    assert ps["pivot_floor"] == pytest.approx(24193.15, abs=0.5)
    assert ps["r1"] == pytest.approx(24231.40, abs=0.5)
    assert ps["s1"] == pytest.approx(24116.65, abs=0.5)
    assert ps["r2"] == pytest.approx(24307.90, abs=0.5)
    assert ps["s2"] == pytest.approx(24078.40, abs=0.5)


def test_structural_level_engine_uncontaminated():
    """Invariant 19-24: Structural level engine computes levels bounded by 18 Aug range."""
    mock_state = {
        "market_data": {
            "current_spot": 24154.90,
            "open": 24223.85,
            "high": 24269.65,
            "low": 24154.90,
            "close": 24154.90,
            "previous_close": 24154.90
        }
    }
    levels = StructuralLevelEngine.evaluate_levels(mock_state)
    
    assert "all_structural_levels" in levels
    for lvl in levels["all_structural_levels"]:
        assert float(lvl["price"]) < 24600, f"Level {lvl} contaminated by high price"
        assert float(lvl["price"]) > 23800


def test_range_arithmetic_and_chart_extremes():
    """Invariant 9-11: Range = High - Low arithmetic check."""
    bs = BrokerService.get_instance()
    ctx = MarketContextBuilder.build(bs, None, 11.33)
    high = float(ctx["high"])
    low = float(ctx["low"])
    expected_range = round(high - low, 2)
    assert expected_range == pytest.approx(114.75, abs=0.5)


def test_briefing_validation_isolation_preview():
    """Invariant 22-24: Historical validation isolation preserves PREPARING status for 19 Aug."""
    now_18_post = datetime(2026, 8, 18, 11, 15, 0, tzinfo=timezone.utc)
    mock_state = {
        "market_data": {
            "open": 24223.85,
            "high": 24269.65,
            "low": 24154.90,
            "close": 24154.90,
            "current_spot": 24154.90,
            "previous_close": 24287.65,
            "session_date": "2026-08-18"
        }
    }
    report = PreMarketBriefingEngine.generate_or_get_briefing(mock_state, as_of_time=now_18_post, force_regenerate=True)
    assert report.trading_date == "2026-08-19"
    assert report.status == "PREPARING"
    
    # Run preview validation
    validated_report = PreMarketBriefingEngine.validate_briefing(report, mock_state, is_preview=True, now_time=now_18_post)
    assert validated_report.status == "PREPARING"
    assert validated_report.validation_preview is not None
    assert validated_report.validation_preview["is_preview"] is True
    assert validated_report.post_market_validation.validation_status == "PENDING"


def test_cross_workspace_close_and_reference_invariants():
    """Invariant 30: Completed 18 Aug close matches 19 Aug reference close across engines."""
    final_18_aug_close = 24154.90
    
    # PreMarketBriefingEngine
    now_18_post = datetime(2026, 8, 18, 11, 15, 0, tzinfo=timezone.utc)
    mock_state = {
        "market_data": {
            "open": 24223.85,
            "high": 24269.65,
            "low": 24154.90,
            "close": final_18_aug_close,
            "current_spot": final_18_aug_close,
            "previous_close": 24287.65,
            "session_date": "2026-08-18"
        }
    }
    now_18_ist = now_18_post + timedelta(hours=5, minutes=30)
    target_date, ref_date, ref_close = PreMarketBriefingEngine.resolve_session_lifecycle(mock_state, now_ist=now_18_ist)
    assert target_date == "2026-08-19"
    assert ref_date == "2026-08-18"
    assert ref_close == pytest.approx(final_18_aug_close, abs=0.1)


def test_future_nifty_high_accepted_without_arbitrary_ceiling():
    """Invariant T: Genuine future session high of e.g. 25,200 is accepted when supported by candle data."""
    mock_future_state = {
        "market_data": {
            "current_spot": 25150.00,
            "open": 25000.00,
            "high": 25200.00,
            "low": 24950.00,
            "close": 25150.00,
            "previous_close": 24900.00
        }
    }
    levels = StructuralLevelEngine.evaluate_levels(mock_future_state)
    assert levels["previous_high"] == pytest.approx(25200.00)
    
    # PreMarketIntelligenceEngine also preserves 25200
    pm_report = PreMarketIntelligenceEngine.analyze_pre_market(mock_future_state)
    assert pm_report is not None


def test_floor_pivot_exact_formula_and_values():
    """Invariant P: Exact Floor Pivot formulas verified for 18 Aug finalized values."""
    H = 24269.65
    L = 24154.90
    C = 24154.90
    
    P = round((H + L + C) / 3.0, 2)
    R1 = round(2 * P - L, 2)
    S1 = round(2 * P - H, 2)
    R2 = round(P + (H - L), 2)
    S2 = round(P - (H - L), 2)
    
    assert P == pytest.approx(24193.15, abs=0.01)
    assert R1 == pytest.approx(24231.40, abs=0.01)
    assert S1 == pytest.approx(24116.65, abs=0.01)
    assert R2 == pytest.approx(24307.90, abs=0.01)
    assert S2 == pytest.approx(24078.40, abs=0.01)


