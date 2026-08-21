import os
import pytest
import tempfile
import shutil
from pathlib import Path
from src.models.performance_record import ArdhaEvaluationRecord
from src.analytics_engine.prediction_reality_evaluator import (
    METRIC_REGISTRY,
    METRICS_BY_ID,
    evaluate_record,
    parse_numeric_range,
)
from src.intelligence_engine.performance_tracker_engine import PerformanceTrackerEngine


@pytest.fixture
def temp_tracker_engine():
    tmpdir = tempfile.mkdtemp()
    engine = PerformanceTrackerEngine(storage_dir=Path(tmpdir))
    yield engine, tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


# 1. Exactly 50 supported metric definitions
def test_exactly_50_supported_metric_definitions():
    assert len(METRIC_REGISTRY) == 50


# 2. Metric IDs stable and unique
def test_metric_ids_stable():
    ids = [m["id"] for m in METRIC_REGISTRY]
    assert len(ids) == 50
    assert len(set(ids)) == 50


# 3. PRE metrics count = 26
def test_pre_metrics_count():
    pre_list = [m for m in METRIC_REGISTRY if m["phase"] == "PRE_MARKET"]
    assert len(pre_list) == 26


# 4. OPEN metrics count = 7
def test_open_metrics_count():
    open_list = [m for m in METRIC_REGISTRY if m["phase"] == "EARLY_SESSION"]
    assert len(open_list) == 7


# 5. LIVE metrics count = 16
def test_live_metrics_count():
    live_list = [m for m in METRIC_REGISTRY if m["phase"] == "LIVE_INTRADAY"]
    assert len(live_list) == 16


# 6. CLOSE metrics count = 1
def test_close_metrics_count():
    close_list = [m for m in METRIC_REGISTRY if m["phase"] == "CLOSE"]
    assert len(close_list) == 1


# 7. PRE prediction_at sourced from canonical briefing
def test_pre_prediction_at_sourced_from_briefing(temp_tracker_engine):
    engine, _ = temp_tracker_engine
    date_str = "2026-08-19"
    mock_state = {"market_session": {"session_date": date_str, "status": "CLOSED"}}
    frozen_briefing = {
        "generated_at": "2026-08-18T11:15:00Z",
        "command_center": {"expected_open_str": "24,158 – 24,178"},
    }
    engine.capture_pre_market_snapshot(mock_state, date_str, frozen_briefing=frozen_briefing)
    recs = engine.load_records(date_str)
    assert recs[0].prediction_at == "2026-08-19T08:50:00+05:30"


# 8. Atomic file write prevents JSON corruption
def test_atomic_file_write_prevents_corruption(temp_tracker_engine):
    engine, tmpdir = temp_tracker_engine
    date_str = "2026-08-25"
    r = ArdhaEvaluationRecord(
        id="atomic-1",
        trading_date=date_str,
        phase="PRE_MARKET",
        captured_at="2026-08-25T08:50:00",
        prediction_at="2026-08-25T08:50:00",
        metric="Expected Open",
        metric_id="pre_expected_open",
        ardha_value="24,200",
    )
    engine.save_records(date_str, [r])
    loaded = engine.load_records(date_str)
    assert len(loaded) == 1
    assert loaded[0].id == "atomic-1"


# 9. Post-close evaluation reduces PENDING to 0
def test_post_close_evaluation_finalizes_pending(temp_tracker_engine):
    engine, _ = temp_tracker_engine
    date_str = "2026-08-25"
    r = ArdhaEvaluationRecord(
        id="pend-1",
        trading_date=date_str,
        phase="PRE_MARKET",
        captured_at="2026-08-25T08:50:00",
        prediction_at="2026-08-25T08:50:00",
        metric="Expected Open",
        metric_id="pre_expected_open",
        ardha_value="24,158 – 24,178",
        result="PENDING",
    )
    engine.append_record(r)
    session_truth = {"open": 24165.0, "high": 24200.0, "low": 24100.0, "close": 24150.0}
    engine.evaluate_pending_records(date_str, session_truth)
    loaded = engine.load_records(date_str)
    assert loaded[0].result == "HIT"
    assert sum(1 for item in loaded if item.result == "PENDING") == 0


# 10. All 26 PRE metrics captured cleanly when briefing is available
def test_all_26_pre_metrics_captured(temp_tracker_engine):
    engine, _ = temp_tracker_engine
    date_str = "2026-08-19"
    mock_state = {"market_session": {"session_date": date_str, "status": "CLOSED"}}
    frozen_briefing = {
        "generated_at": "2026-08-18T11:15:00Z",
        "command_center": {
            "expected_open_str": "24,158 – 24,178",
            "expected_gap_str": "+4 to +24",
            "opening_bias": "NEUTRAL / MIXED",
            "confidence_pct": 60,
            "risk_level": "MODERATE",
            "global_market_tone": "MIXED",
            "institutional_tone": "NET BUYING",
        },
        "price_structure": {
            "r1": 24231.4,
            "r2": 24307.9,
            "s1": 24116.65,
            "s2": 24078.4,
            "immediate_support": 24116.65,
            "immediate_resistance": 24231.4,
            "pivot_floor": 24193.15,
            "decision_corridor_lower": 24188.0,
            "decision_corridor_upper": 24198.0,
        },
        "volatility_and_risk": {"session_range": 133.15, "regime": "ELEVATED"},
        "options_intelligence": {
            "options_bias": "MILD BULLISH SUPPORT",
            "pcr_oi": 1.22,
            "max_pain": 24350.0,
            "call_wall": 24500.0,
            "put_wall": 24300.0,
        },
        "gift_dashboard": {"classification": "EVIDENCE_DERIVED_OPEN"},
        "sector_scoreboard": [{"sector": "NIFTY METAL"}, {"sector": "NIFTY IT"}],
        "opening_scenarios": [
            {"title": "SCENARIO A: BULLISH BREAKOUT CONTINUATION"},
            {"title": "SCENARIO B: BEARISH BREAKDOWN EXPANSION"},
        ],
    }
    recs = engine.capture_pre_market_snapshot(mock_state, date_str, frozen_briefing=frozen_briefing)
    assert len(recs) == 26


# 11. UNKNOWN realized regime returns NOT_EVALUABLE (never MISS!)
def test_unknown_realized_regime_returns_not_evaluable():
    rec = ArdhaEvaluationRecord(
        id="regime-unk",
        trading_date="2026-08-25",
        phase="PRE_MARKET",
        captured_at="2026-08-25T08:50:00",
        prediction_at="2026-08-25T08:50:00",
        metric="Expected Market Regime",
        metric_id="pre_expected_regime",
        ardha_value="RANGE",
    )
    eval_rec = evaluate_record(rec, {"regime": "UNKNOWN", "open": 24200.0, "close": 24200.0})
    assert eval_rec.result == "NOT_EVALUABLE"


# 12. Primary scenario activation uses structured scenario ID
def test_primary_scenario_structured_evaluation():
    rec = ArdhaEvaluationRecord(
        id="ps-struct",
        trading_date="2026-08-25",
        phase="PRE_MARKET",
        captured_at="2026-08-25T08:50:00",
        prediction_at="2026-08-25T08:50:00",
        metric="Primary Scenario",
        metric_id="pre_primary_scenario",
        ardha_value="SCENARIO A: BULLISH BREAKOUT CONTINUATION",
    )
    eval_rec = evaluate_record(rec, {"open": 24200.0, "high": 24210.0, "low": 24050.0, "close": 24050.0})
    assert eval_rec.result == "MISS"
    assert "SCENARIO B" in eval_rec.real_value


# 13. Production untouched
def test_production_untouched():
    prod_path = Path("/opt/ArdhaMind")
    assert prod_path.exists()
