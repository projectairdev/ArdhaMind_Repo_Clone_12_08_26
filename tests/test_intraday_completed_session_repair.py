# tests/test_intraday_completed_session_repair.py
"""
Regression and unit test suite for Intraday Intelligence Completed-Session Resolver Repair.
"""
import pytest
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

from src.intelligence_engine.live_assistant_engine import LiveAssistantEngine
from src.application.workstation_state_service import WorkstationStateService


def test_1_active_live_session_selection(tmp_path):
    """Active LIVE session uses ONLY current session_date without historical contamination."""
    dt_mon = datetime(2026, 8, 17, 9, 30, tzinfo=timezone.utc)
    m_session = {"session_date": "2026-08-17", "status": "OPEN"}

    history = [
        {"session_date": "2026-08-13", "market_session_phase": "CONTINUOUS_TRADING", "spot": 24390.0, "timestamp": "2026-08-13T09:30:00Z"},
        {"session_date": "2026-08-17", "market_session_phase": "MARKET_OPEN", "spot": 24500.0, "timestamp": "2026-08-17T03:45:00Z"}
    ]

    intel_date, intel_mode, snaps = LiveAssistantEngine.resolve_intraday_session(m_session, dt_mon + timedelta(hours=5, minutes=30), history, cache_dir=tmp_path)

    assert intel_date == "2026-08-17"
    assert intel_mode == "LIVE"
    assert len(snaps) == 1
    assert snaps[0]["session_date"] == "2026-08-17"


def test_2_3_weekend_fallback_and_empty_history_skipping(tmp_path):
    """Weekend runtime skips empty history file (snapshots=[]) and selects newest valid trading session."""
    # Write empty 14-Aug file
    p14 = tmp_path / "session_history_2026-08-14.json"
    p14.write_text(json.dumps({"version": "1.0.0", "session_date": "2026-08-14", "snapshots": []}))

    # Write valid 13-Aug file
    p13 = tmp_path / "session_history_2026-08-13.json"
    p13.write_text(json.dumps({
        "version": "1.0.0", "session_date": "2026-08-13",
        "snapshots": [
            {"session_date": "2026-08-13", "market_session_phase": "CONTINUOUS_TRADING", "spot": 24395.85, "timestamp": "2026-08-13T05:00:00Z"}
        ]
    }))

    dt_sat = datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc)
    m_session = {"session_date": "2026-08-15", "status": "CLOSED"}

    intel_date, intel_mode, snaps = LiveAssistantEngine.resolve_intraday_session(m_session, dt_sat + timedelta(hours=5, minutes=30), [], cache_dir=tmp_path)

    assert intel_date == "2026-08-13"
    assert intel_mode == "COMPLETED_SESSION"
    assert len(snaps) == 1
    assert snaps[0]["spot"] == 24395.85


def test_4_no_historical_data_no_synthetic_fabrication(tmp_path):
    """Weekend with no historical session history returns current date with empty snaps and zero synthetic backfill."""
    dt_sat = datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc)
    m_session = {"session_date": "2026-08-15", "status": "HOLIDAY"}

    intel_date, intel_mode, snaps = LiveAssistantEngine.resolve_intraday_session(m_session, dt_sat + timedelta(hours=5, minutes=30), [], cache_dir=tmp_path)

    assert intel_date == "2026-08-15"
    assert intel_mode == "COMPLETED_SESSION"
    assert len(snaps) == 0


def test_5_monday_isolation_prevents_thursday_contamination(tmp_path):
    """Monday live session MUST NOT contain Thursday observations in Monday windows."""
    dt_mon = datetime(2026, 8, 17, 4, 0, tzinfo=timezone.utc)  # 09:30 IST
    m_session = {"session_date": "2026-08-17", "status": "OPEN"}

    history = [
        {"session_date": "2026-08-13", "market_session_phase": "CONTINUOUS_TRADING", "spot": 24390.0, "timestamp": "2026-08-13T04:00:00Z"},
        {"session_date": "2026-08-17", "market_session_phase": "MARKET_OPEN", "spot": 24510.0, "timestamp": "2026-08-17T03:45:00Z"}
    ]

    report = LiveAssistantEngine.analyze_live_session(
        {"market_session": m_session},
        history,
        as_of_time=dt_mon
    )

    assert report["intelligence_session_date"] == "2026-08-17"
    assert report["intelligence_mode"] == "LIVE"

    w_first = report["windows"][0]  # 09:15-09:30
    assert w_first["window_start"] == "09:15"
    # Spot in first window should be Monday spot 24510.0, NOT Thursday 24390.0
    assert w_first["end_spot"] == 24510.0


def test_6_utc_to_ist_bucketing():
    """UTC ISO timestamps convert accurately to IST time for window and 3m bucket matching."""
    # 03:45 UTC = 09:15 IST
    ts_utc = "2026-08-13T03:45:00Z"
    hm = LiveAssistantEngine._parse_ist_hm(ts_utc)
    assert hm == "09:15"

    snap = {"timestamp": ts_utc, "session_date": "2026-08-13"}
    assert LiveAssistantEngine._snap_in_window(snap, "09:15", "09:30", target_date="2026-08-13") is True
    assert LiveAssistantEngine._snap_in_window(snap, "09:15", "09:30", target_date="2026-08-14") is False


def test_7_8_restart_persistence_and_partial_metric_availability(tmp_path):
    """Persisted session with valid price but missing VIX remains a valid session."""
    p13 = tmp_path / "session_history_2026-08-13.json"
    p13.write_text(json.dumps({
        "version": "1.0.0", "session_date": "2026-08-13",
        "snapshots": [
            {"session_date": "2026-08-13", "market_session_phase": "CONTINUOUS_TRADING", "spot": 24395.85, "vix": None, "timestamp": "2026-08-13T05:00:00Z"}
        ]
    }))

    dt_sat = datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc)
    m_session = {"session_date": "2026-08-15", "status": "CLOSED"}

    intel_date, intel_mode, snaps = LiveAssistantEngine.resolve_intraday_session(m_session, dt_sat + timedelta(hours=5, minutes=30), [], cache_dir=tmp_path)

    assert intel_date == "2026-08-13"
    assert len(snaps) == 1
    assert snaps[0]["vix"] is None


def test_9_test_isolation_prevents_prod_cache_mutation():
    """Verify Pytest cannot mutate production data/cache directory."""
    orig_dir = WorkstationStateService.CACHE_DIR
    try:
        WorkstationStateService.CACHE_DIR = Path("data/cache")
        WorkstationStateService._allow_disk_cache_in_test = True
        with pytest.raises(RuntimeError, match="TEST ISOLATION VIOLATION"):
            WorkstationStateService._persist_session_history("2026-08-12", force=True)
    finally:
        WorkstationStateService.CACHE_DIR = orig_dir
        WorkstationStateService._allow_disk_cache_in_test = False
