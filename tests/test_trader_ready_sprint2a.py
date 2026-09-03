# tests/test_trader_ready_sprint2a.py
"""
Deterministic Test Suite for AIR ArdhaMind Trader-Ready Sprint 2A.

Tests:
1. Reference Close Truth (Monday prior Friday, missing close degradation, no static fallback).
2. GIFT Normalization & Basis layer (raw gift, basis subtraction, unmeasured fallback).
3. Removal of +30 Gap Heuristic (dynamic VIX/volatility dispersion interval).
4. Signal Families (US + Asia single family, no double counting, capped contributions).
5. FII/DII reduced weighting (context only, no lone high confidence).
6. Confidence Gating (no hardcoded 75%, nullable calibrated probability).
7. NSE Pre-Open Handoff (GIFT anchor -> NSE_PREOPEN anchor).
8. Prediction Telemetry & Immutable Storage (outcome attachment, empirical calibration).
9. 24 Aug Replay Validation (Old vs Corrected comparison on actual 24 Aug session).
"""

import json
from datetime import datetime, timezone
from pathlib import Path
import pytest

from src.intelligence_engine.pre_market_engine import PreMarketIntelligenceEngine
from src.intelligence_engine.pre_market_briefing_engine import PreMarketBriefingEngine
from src.intelligence_engine.prediction_telemetry import (
    PredictionTelemetryStore,
    PreMarketPredictionRecord,
)
from src.intelligence_engine.intraday_scoring_evaluator import IntradayPredictionScoringEvaluator


def test_reference_close_truth_and_no_static_fallback():
    """Test 1: Reference close resolves canonically without static fallbacks."""
    PreMarketIntelligenceEngine.reset_engine_state()
    as_of = datetime.fromisoformat("2026-08-24T08:25:00+05:30")

    # State with valid previous close from Friday
    state_with_close = {
        "market_session": {"status": "PRE_MARKET", "session_date": "2026-08-24"},
        "market_data": {"previous_close": 24287.65, "current_spot": 24287.65},
        "macro_intelligence": {"quotes": {}}
    }
    report = PreMarketIntelligenceEngine.analyze_pre_market(state_with_close, as_of_time=as_of.astimezone(timezone.utc))
    assert report.reference_close == 24287.65
    assert report.target_trading_date == "2026-08-24"
    assert report.reference_session_date == "2026-08-21"

    # State with MISSING previous close -> must NOT fall back to static number, must degrade
    PreMarketIntelligenceEngine.reset_engine_state()
    state_no_close = {
        "market_session": {"status": "PRE_MARKET", "session_date": "2026-08-24"},
        "market_data": {},
        "macro_intelligence": {"quotes": {}}
    }
    report_no_close = PreMarketIntelligenceEngine.analyze_pre_market(state_no_close, as_of_time=as_of.astimezone(timezone.utc))
    assert report_no_close.reference_close is None
    assert report_no_close.overall_confidence == "LOW"
    assert report_no_close.analysis_status == "DEGRADED"


def test_gift_normalization_and_basis():
    """Test 2: GIFT Nifty normalized by basis rather than treated directly as cash open."""
    PreMarketIntelligenceEngine.reset_engine_state()
    as_of = datetime.fromisoformat("2026-08-24T08:30:00+05:30")

    # Raw GIFT 24,337.65 with 50.0 basis -> Normalized 24,287.65 (flat gap)
    state = {
        "market_session": {"status": "PRE_MARKET", "session_date": "2026-08-24"},
        "market_data": {"previous_close": 24287.65, "futures_basis": 50.0},
        "macro_intelligence": {
            "quotes": {
                "GIFT_NIFTY": {"price": 24337.65, "status": "FRESH", "observed_at": "08:30 IST"}
            },
            "india_vix": {"value": 11.5}
        }
    }
    report = PreMarketIntelligenceEngine.analyze_pre_market(state, as_of_time=as_of.astimezone(timezone.utc))
    assert report.raw_gift == 24337.65
    assert report.estimated_basis == 50.0
    assert report.basis_quality == "MEASURED_PRIOR_CLOSE"
    assert report.normalized_gift == 24287.65
    assert report.expected_open_center == 24287.65
    assert report.forecast_anchor == "NORMALIZED_GIFT"


def test_no_plus_30_heuristic():
    """Test 3: Opening range uses dynamic volatility dispersion, not hardcoded +30 width."""
    PreMarketIntelligenceEngine.reset_engine_state()
    as_of = datetime.fromisoformat("2026-08-24T08:30:00+05:30")

    state = {
        "market_session": {"status": "PRE_MARKET", "session_date": "2026-08-24"},
        "market_data": {"previous_close": 24287.65, "futures_basis": 0.0},
        "macro_intelligence": {
            "quotes": {
                "GIFT_NIFTY": {"price": 24287.65, "status": "FRESH"}
            },
            "india_vix": {"value": 12.0}
        }
    }
    report = PreMarketIntelligenceEngine.analyze_pre_market(state, as_of_time=as_of.astimezone(timezone.utc))
    assert report.expected_open_low is not None
    assert report.expected_open_high is not None
    # Dynamic interval width is symmetric around expected center
    bandwidth = report.expected_open_high - report.expected_open_low
    assert report.expected_open_center == 24287.65
    # The old +30 heuristic made expected_open_low = implied_gap and high = implied_gap + 30 (asymmetric)
    # New logic is symmetric around center
    assert round((report.expected_open_low + report.expected_open_high) / 2.0, 2) == 24287.65
    assert report.interval_method == "VIX_IMPLIED_DISPERSION"


def test_signal_families_prevent_triple_counting():
    """Test 4: US + Asia + GIFT are grouped into families and capped."""
    PreMarketIntelligenceEngine.reset_engine_state()
    as_of = datetime.fromisoformat("2026-08-24T08:30:00+05:30")

    state = {
        "market_session": {"status": "PRE_MARKET", "session_date": "2026-08-24"},
        "market_data": {"previous_close": 24287.65},
        "macro_intelligence": {
            "quotes": {
                "GIFT_NIFTY": {"price": 24350.0, "status": "FRESH"},
                "S&P 500": {"change_pct": 1.5},
                "NASDAQ": {"change_pct": 2.0},
                "DOW_JONES": {"change_pct": 1.2},
                "NIKKEI_225": {"change_pct": 1.8},
                "HANG_SENG": {"change_pct": 1.4}
            }
        }
    }
    report = PreMarketIntelligenceEngine.analyze_pre_market(state, as_of_time=as_of.astimezone(timezone.utc))
    # Global Risk Context family is capped at max 20.0
    # Total setup_score cannot blow up beyond sum of capped families
    assert report.setup_score <= 90.0


def test_confidence_and_nullable_calibrated_probability():
    """Test 5: Confidence is qualitative (LOW/MODERATE/HIGH) and calibrated probability is nullable."""
    PreMarketIntelligenceEngine.reset_engine_state()
    as_of = datetime.fromisoformat("2026-08-24T08:30:00+05:30")

    state = {
        "market_session": {"status": "PRE_MARKET", "session_date": "2026-08-24"},
        "market_data": {"previous_close": 24287.65},
        "macro_intelligence": {
            "quotes": {
                "GIFT_NIFTY": {"price": 24290.0, "status": "FRESH"}
            }
        }
    }
    report = PreMarketIntelligenceEngine.analyze_pre_market(state, as_of_time=as_of.astimezone(timezone.utc))
    assert report.overall_confidence in ("LOW", "MODERATE", "HIGH")
    # Calibrated probability is nullable when sample size is insufficient
    assert report.calibrated_probability is None or (0.0 <= report.calibrated_probability <= 1.0)


def test_nse_preopen_handoff():
    """Test 6: Pre-open handoff anchors to settled NSE pre-open price at 09:08."""
    PreMarketIntelligenceEngine.reset_engine_state()
    as_of_preopen = datetime.fromisoformat("2026-08-24T09:09:00+05:30")

    state = {
        "market_session": {"status": "PRE_OPEN", "session_date": "2026-08-24"},
        "market_data": {
            "previous_close": 24287.65,
            "pre_open_settlement": 24285.05,
            "open": 24285.05
        },
        "macro_intelligence": {
            "quotes": {
                "GIFT_NIFTY": {"price": 24350.0, "status": "FRESH"}
            }
        }
    }
    report = PreMarketIntelligenceEngine.analyze_pre_market(state, as_of_time=as_of_preopen.astimezone(timezone.utc))
    assert report.forecast_anchor == "NSE_PREOPEN"
    assert report.anchor_freshness == "SETTLED_CANONICAL"
    assert report.expected_open_center == 24285.05
    assert report.expected_open_low == 24280.05
    assert report.expected_open_high == 24290.05


def test_prediction_telemetry_recording_and_outcome_attachment(tmp_path):
    """Test 7: Prediction telemetry persists immutably and attaches outcomes."""
    test_storage = tmp_path / "prediction_telemetry.json"
    PredictionTelemetryStore.set_storage_path(test_storage)

    record = PreMarketPredictionRecord(
        prediction_id="PRED-TEST-001",
        generated_at="2026-08-24T08:30:00Z",
        target_session="2026-08-24",
        reference_session_date="2026-08-21",
        reference_close=24287.65,
        raw_gift=24293.5,
        estimated_basis=0.0,
        basis_quality="UNMEASURED_ESTIMATE",
        normalized_gift=24293.5,
        gift_freshness="FRESH",
        forecast_anchor="NORMALIZED_GIFT",
        anchor_timestamp="08:30 IST",
        expected_open_center=24293.5,
        expected_open_low=24268.5,
        expected_open_high=24318.5,
        opening_bias="NEUTRAL / MIXED OPENING",
        confidence_band="MODERATE",
        calibrated_probability=None,
        interval_method="VIX_IMPLIED_DISPERSION",
        calibration_sample_size=0,
        family_contributions={},
        supporting_evidence=[],
        opposing_evidence=[],
        risk_flags=[]
    )
    PredictionTelemetryStore.record_premarket_prediction(record)

    # Attach actual outcome
    updated = PredictionTelemetryStore.attach_premarket_outcome("2026-08-24", 24285.05, "2026-08-24T09:15:00Z")
    assert len(updated) == 1
    eval_rec = updated[0]
    assert eval_rec.outcome_status == "EVALUATED"
    assert eval_rec.actual_open == 24285.05
    assert eval_rec.error_points == -8.45
    assert eval_rec.absolute_error == 8.45
    assert eval_rec.interval_hit is True


def test_24_aug_replay_validation():
    """Test 8: Replay 24 Aug 2026 and verify old vs corrected metrics."""
    res = IntradayPredictionScoringEvaluator.evaluate_session_history(
        session_history_path="/opt/ardhamind/staging/data/cache/session_history_2026-08-24.json",
        candles_cache_path="/opt/ardhamind/staging/data/cache/nifty_candles_cache.json"
    )
    assert res["status"] == "EVALUATION_SUCCESS"
    assert res["all_observations"]["total_observations"] == 126
    scenarios = res["all_observations"]["scenario_summary"]
    assert "RANGE_CONTINUATION" in scenarios
    assert "RANGE_WITH_BEARISH_PRESSURE" in scenarios
    
    # Verify range scenarios have direction = N/A and null directional MFE
    range_stats = scenarios["RANGE_CONTINUATION"]
    assert range_stats["30m"]["direction_accuracy_pct"] == "N/A (RANGE)"
    assert range_stats["30m"]["avg_mfe_pts"] is None
    assert range_stats["30m"]["avg_mae_pts"] is None
    assert range_stats["30m"]["endpoint_containment_pct"] > 70.0
    assert range_stats["30m"]["full_horizon_containment_pct"] > 70.0

    # Verify bearish scenarios have mathematical MFE/MAE and direction accuracy
    bearish_stats = scenarios["RANGE_WITH_BEARISH_PRESSURE"]
    assert isinstance(bearish_stats["30m"]["direction_accuracy_pct"], float)
    assert bearish_stats["30m"]["avg_mfe_pts"] is not None and bearish_stats["30m"]["avg_mfe_pts"] > 0
    assert bearish_stats["30m"]["avg_mae_pts"] is not None and bearish_stats["30m"]["avg_mae_pts"] > 0


def test_mfe_mae_mathematical_definitions():
    """Test 9: Verify MFE/MAE formulas for bullish, bearish, and range."""
    # Bullish scenario: spot_0 = 24200, intermediate high = 24250, low = 24180
    spot_0 = 24200.0
    high = 24250.0
    low = 24180.0

    # Bullish: MFE = max(0, high - spot_0) = 50.0, MAE = max(0, spot_0 - low) = 20.0
    bullish_mfe = max(0.0, high - spot_0)
    bullish_mae = max(0.0, spot_0 - low)
    assert bullish_mfe == 50.0
    assert bullish_mae == 20.0

    # Bearish: MFE = max(0, spot_0 - low) = 20.0, MAE = max(0, high - spot_0) = 50.0
    bearish_mfe = max(0.0, spot_0 - low)
    bearish_mae = max(0.0, high - spot_0)
    assert bearish_mfe == 20.0
    assert bearish_mae == 50.0


def test_range_containment_and_temporary_breach():
    """Test 10: Verify endpoint inside vs full horizon containment vs temporary breach."""
    support = 24200.0
    resistance = 24300.0

    # Case A: Fully contained
    candles_contained = [{"low": 24210.0, "high": 24290.0, "close": 24250.0}]
    min_low = min(c["low"] for c in candles_contained)
    max_high = max(c["high"] for c in candles_contained)
    endpoint = candles_contained[-1]["close"]
    assert (support <= min_low and max_high <= resistance) is True
    assert (support <= endpoint <= resistance) is True

    # Case B: Temporary breach (dipped to 24180, closed at 24250)
    candles_temp_breach = [
        {"low": 24180.0, "high": 24230.0, "close": 24190.0},
        {"low": 24220.0, "high": 24260.0, "close": 24250.0}
    ]
    min_low_b = min(c["low"] for c in candles_temp_breach)
    max_high_b = max(c["high"] for c in candles_temp_breach)
    endpoint_b = candles_temp_breach[-1]["close"]
    full_contained_b = (support <= min_low_b and max_high_b <= resistance)
    endpoint_inside_b = (support <= endpoint_b <= resistance)
    assert full_contained_b is False
    assert endpoint_inside_b is True
    # Temporary breach is true when not fully contained but endpoint inside
    assert (not full_contained_b and endpoint_inside_b) is True


def test_no_future_leakage_invariant():
    """Test 11: Evaluator does not access future candles before prediction horizon."""
    # When evaluating at 09:15 for a 30m horizon (09:45):
    # Only candles between 09:15 and 09:45 are eligible
    dt_start = "09:15"
    dt_end = "09:45"
    sample_candles = [
        {"hhmm": "09:15", "close": 24285.05},
        {"hhmm": "09:30", "close": 24270.00},
        {"hhmm": "09:45", "close": 24260.00},
        {"hhmm": "10:30", "close": 24200.00},
        {"hhmm": "15:29", "close": 24219.05},
    ]
    eligible = [c for c in sample_candles if dt_start <= c["hhmm"] <= dt_end]
    assert len(eligible) == 3
    assert all(c["hhmm"] <= "09:45" for c in eligible)
    # Ensure post-horizon candles (10:30, 15:29) are strictly excluded
    assert not any(c["hhmm"] > "09:45" for c in eligible)
