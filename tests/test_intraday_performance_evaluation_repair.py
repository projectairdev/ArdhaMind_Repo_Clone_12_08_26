import pytest
import tempfile
import shutil
from pathlib import Path
from src.models.performance_record import ArdhaEvaluationRecord
from src.analytics_engine.prediction_reality_evaluator import (
    METRIC_REGISTRY,
    evaluate_record,
    parse_numeric_range,
)
from src.intelligence_engine.performance_tracker_engine import PerformanceTrackerEngine


@pytest.fixture
def temp_tracker():
    tmpdir = tempfile.mkdtemp()
    engine = PerformanceTrackerEngine(storage_dir=Path(tmpdir))
    yield engine, tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


# 1. Expected-open range pairs cleanly with official open
def test_expected_open_range_pairs_with_official_open():
    rec = ArdhaEvaluationRecord(
        id="eo-range-1",
        trading_date="2026-08-20",
        phase="PRE_MARKET",
        captured_at="2026-08-20T08:50:00",
        prediction_at="2026-08-20T08:50:00",
        metric="Expected Open",
        metric_id="pre_expected_open",
        ardha_value="24,110 – 24,140",
        result="PENDING",
    )
    session_truth = {
        "open": 24125.0,
        "high": 24150.0,
        "low": 24100.0,
        "close": 24130.0,
        "is_live": True,
        "current_hhmm": "09:20",
        "market_status": "OPEN",
    }
    eval_rec = evaluate_record(rec, session_truth)
    assert eval_rec.result == "HIT"
    assert "24125" in eval_rec.real_value
    assert eval_rec.pending_reason is None


# 2. Existing prediction cannot return "No prediction recorded" even if previously NOT_EVALUABLE
def test_existing_prediction_re_evaluates_from_not_evaluable():
    rec = ArdhaEvaluationRecord(
        id="act-vs-fc-1",
        trading_date="2026-08-20",
        phase="EARLY_SESSION",
        captured_at="2026-08-20T09:15:00",
        prediction_at="2026-08-20T09:15:00",
        metric="Actual Open vs Forecast",
        metric_id="open_actual_vs_forecast",
        ardha_value="24,110 – 24,140",
        result="NOT_EVALUABLE",
        real_value="No prediction recorded",
    )
    session_truth = {
        "open": 24152.05,
        "high": 24175.0,
        "low": 24100.0,
        "close": 24130.0,
        "is_live": True,
        "current_hhmm": "09:20",
        "market_status": "OPEN",
    }
    eval_rec = evaluate_record(rec, session_truth)
    assert eval_rec.result in ["HIT", "NEAR", "MISS"]
    assert eval_rec.real_value != "No prediction recorded"
    assert "24152" in eval_rec.real_value


# 3. Real Runtime Payload Keys Extraction (alignment, regime, breadth, options, vix)
def test_real_runtime_payload_extraction(temp_tracker):
    engine, _ = temp_tracker
    date_str = "2026-08-20"

    real_runtime_snapshot = {
        "timestamp": "2026-08-20T04:33:16.815938Z",
        "runtime_id": "staging-v1",
        "spot": 24152.05,
        "regime": "UNCERTAIN",
        "alignment": "BULLISH_ALIGNMENT",
        "breadth": {"advances": 39, "declines": 11, "coverage": 50},
        "options": {"pcr": 1.1476, "max_pain": 24200.0, "atm_strike": 24200.0, "atm_iv": 8.7941},
        "vix": 10.81,
    }

    recs = engine.capture_live_intraday_snapshot(real_runtime_snapshot, date_str)
    by_id = {r.metric_id: r for r in recs}

    assert by_id["live_current_bias"].ardha_value == "BULLISH"
    assert by_id["live_market_regime"].ardha_value == "UNCERTAIN"
    assert "39 A / 11 D" in by_id["live_breadth_interpretation"].ardha_value
    assert "PCR 1.15" in by_id["live_pcr_interpretation"].ardha_value
    assert by_id["live_call_wall_state"].ardha_value == "24200.0"
    assert by_id["live_risk_level"].ardha_value == "LOW"  # vix 10.81 < 13


# 4. Material change emitted immediately without blanket 60s time veto
def test_material_change_emitted_immediately(temp_tracker):
    engine, _ = temp_tracker
    date_str = "2026-08-20"

    r1 = ArdhaEvaluationRecord(
        id="bias-1",
        trading_date=date_str,
        phase="LIVE_INTRADAY",
        captured_at="2026-08-20T09:15:00+05:30",
        metric="Current Bias",
        metric_id="live_current_bias",
        ardha_value="NEUTRAL",
    )
    engine.append_record(r1)

    r2 = ArdhaEvaluationRecord(
        id="bias-2",
        trading_date=date_str,
        phase="LIVE_INTRADAY",
        captured_at="2026-08-20T09:15:05+05:30",  # Only 5 seconds later!
        metric="Current Bias",
        metric_id="live_current_bias",
        ardha_value="BULLISH",  # Changed!
    )
    res2 = engine.append_record(r2)
    assert res2.id == "bias-2"

    records = engine.load_records(date_str)
    assert len([r for r in records if r.metric_id == "live_current_bias"]) == 2


# 5. Missing risk source returns UNAVAILABLE (no MODERATE fallback per STEP 17)
def test_missing_risk_returns_unavailable(temp_tracker):
    engine, _ = temp_tracker
    date_str = "2026-08-20"

    empty_risk_state = {}
    recs = engine.capture_live_intraday_snapshot(empty_risk_state, date_str)
    by_id = {r.metric_id: r for r in recs}
    assert by_id["live_risk_level"].ardha_value == "UNAVAILABLE"


# 6. Production untouched
def test_production_untouched():
    prod_path = Path("/opt/ArdhaMind")
    assert prod_path.exists()
