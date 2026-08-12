# tests/test_sprint_d31_persistence_recovery.py
from datetime import datetime, timezone
from pathlib import Path
import json
import pytest

from src.application.workstation_state_service import WorkstationStateService
from src.models.canonical_workstation_state import FORBIDDEN_CANONICAL_KEYS


def get_base_payload(spot=24500.0, timestamp="2026-08-11T09:15:00Z"):
    return {
        "marketContext": {
            "current_spot": spot,
            "previous_close": 24550.0,
            "session_date": "2026-08-11",
            "exchange_timestamp": timestamp,
            "backend_receive_timestamp": timestamp
        },
        "technicalAnalysis": {},
        "optionContext": {"pcr": 1.05},
        "macroIntelligence": {},
        "newsSentiment": {}
    }


def setup_function():
    # Clean in-memory and test cache file before each test
    WorkstationStateService._allow_disk_cache_in_test = True
    WorkstationStateService._snapshots_history = []
    WorkstationStateService._live_event_stream = []
    WorkstationStateService._last_loaded_session_date = None
    cache_file = Path("data/cache/session_history_2026-08-11.json")
    if cache_file.exists():
        cache_file.unlink()


def teardown_function():
    WorkstationStateService._allow_disk_cache_in_test = False
    WorkstationStateService._snapshots_history = []
    WorkstationStateService._live_event_stream = []
    WorkstationStateService._last_loaded_session_date = None


def test_session_history_persists_and_restores_on_backend_restart():
    t0 = datetime(2026, 8, 11, 9, 15, 0, tzinfo=timezone.utc)
    WorkstationStateService.build_from_legacy(get_base_payload(24530.0, "2026-08-11T09:15:00Z"), market_state="OPEN", now=t0)

    t1 = datetime(2026, 8, 11, 9, 30, 0, tzinfo=timezone.utc)
    WorkstationStateService.build_from_legacy(get_base_payload(24490.0, "2026-08-11T09:30:00Z"), market_state="OPEN", now=t1)

    cache_file = Path("data/cache/session_history_2026-08-11.json")
    assert cache_file.exists()

    # Simulate backend restart (destroy process memory)
    WorkstationStateService._snapshots_history = []
    WorkstationStateService._live_event_stream = []
    WorkstationStateService._last_loaded_session_date = None

    # Now build state when market is CLOSED (e.g. 18:12 IST)
    t_closed = datetime(2026, 8, 11, 18, 12, 0, tzinfo=timezone.utc)
    closed_state = WorkstationStateService.build_from_legacy(
        get_base_payload(24490.0, "2026-08-11T18:12:00Z"), market_state="CLOSED", now=t_closed
    )

    story = closed_state.session_story
    assert story is not None
    assert story["session_status"] == "TODAYS_SESSION_REVIEW"
    assert story["session_status_classification"] in ("COMPLETE", "PARTIAL")
    assert story["session_summary"]["open"] == 24530.0
    assert len(story["timeline"]) > 0


def test_trading_date_scoping_and_wrong_date_cache_ignored():
    t0 = datetime(2026, 8, 11, 9, 15, 0, tzinfo=timezone.utc)
    WorkstationStateService.build_from_legacy(get_base_payload(24500.0), market_state="OPEN", now=t0)

    # A cache for another date should not mix into current session
    wrong_cache = Path("data/cache/session_history_2026-08-10.json")
    wrong_cache.parent.mkdir(parents=True, exist_ok=True)
    wrong_cache.write_text(json.dumps({
        "session_date": "2026-08-10",
        "snapshots": [{"timestamp": "2026-08-10T09:15:00Z", "spot": 24000.0, "session_date": "2026-08-10"}]
    }), encoding="utf-8")

    # Load 2026-08-11 session
    WorkstationStateService._snapshots_history = []
    WorkstationStateService._load_session_history("2026-08-11")

    # Ensure 2026-08-10 snapshot was NOT loaded into 2026-08-11 history
    assert not any(s.get("session_date") == "2026-08-10" for s in WorkstationStateService._snapshots_history)


def test_corrupt_cache_handled_safely_without_crash():
    cache_file = Path("data/cache/session_history_2026-08-11.json")
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text("{ malformed JSON content ...", encoding="utf-8")

    WorkstationStateService._snapshots_history = []
    WorkstationStateService._load_session_history("2026-08-11")

    assert WorkstationStateService._persistence_health == "DEGRADED"
    assert WorkstationStateService._snapshots_history == []


def test_status_classifications_complete_partial_and_unavailable():
    cache_file = Path("data/cache/session_history_2026-08-11.json")
    if cache_file.exists():
        cache_file.unlink()

    # 1. Zero history after close => UNAVAILABLE
    WorkstationStateService._snapshots_history = []
    WorkstationStateService._live_event_stream = []
    WorkstationStateService._last_loaded_session_date = "2026-08-11"
    t_closed = datetime(2026, 8, 11, 18, 12, 0, tzinfo=timezone.utc)
    state_no_hist = WorkstationStateService.build_from_legacy(
        get_base_payload(24500.0), market_state="CLOSED", now=t_closed
    )
    assert state_no_hist.session_story["session_status_classification"] == "UNAVAILABLE"
    assert "UNAVAILABLE" in state_no_hist.session_story["session_summary"]["session_verdict"]

    if cache_file.exists():
        cache_file.unlink()

    # 2. Host gap present => PARTIAL
    WorkstationStateService._snapshots_history = []
    WorkstationStateService._last_loaded_session_date = None
    t1 = datetime(2026, 8, 11, 9, 34, 47, tzinfo=timezone.utc)
    p1 = get_base_payload(24500.0, "2026-08-11T09:34:47Z")
    WorkstationStateService.build_from_legacy(p1, market_state="OPEN", now=t1)

    t2 = datetime(2026, 8, 11, 12, 12, 11, tzinfo=timezone.utc)
    p2 = get_base_payload(24450.0, "2026-08-11T12:12:11Z")
    state_gap = WorkstationStateService.build_from_legacy(p2, market_state="CLOSED", now=t2)
    assert state_gap.session_story["session_status_classification"] == "PARTIAL"

    if cache_file.exists():
        cache_file.unlink()

    # 3. Continuous history => COMPLETE
    WorkstationStateService._snapshots_history = []
    WorkstationStateService._last_loaded_session_date = None
    t_c1 = datetime(2026, 8, 11, 9, 15, 0, tzinfo=timezone.utc)
    WorkstationStateService.build_from_legacy(get_base_payload(24500.0, "2026-08-11T09:15:00Z"), market_state="OPEN", now=t_c1)
    t_c2 = datetime(2026, 8, 11, 9, 16, 0, tzinfo=timezone.utc)
    state_comp = WorkstationStateService.build_from_legacy(get_base_payload(24510.0, "2026-08-11T09:16:00Z"), market_state="CLOSED", now=t_c2)
    assert state_comp.session_story["session_status_classification"] == "COMPLETE"


def test_read_only_and_latency_truth_preserved():
    t0 = datetime(2026, 8, 11, 9, 15, 0, tzinfo=timezone.utc)
    state = WorkstationStateService.build_from_legacy(get_base_payload(24500.0), market_state="OPEN", now=t0)

    # Read-only check
    for forbidden in FORBIDDEN_CANONICAL_KEYS:
        assert forbidden not in str(state.session_story).lower()

    # Latency check
    lat = state.market_data["live_feed_latency_truth"]
    assert "source_observed_at" in lat
    assert "feed_received_at" in lat
    assert "status" in lat


def test_cache_diagnostics_and_retention_filter():
    cache_file = Path("data/cache/session_history_2026-08-11.json")
    if cache_file.exists():
        cache_file.unlink()
    WorkstationStateService._snapshots_history = []
    WorkstationStateService._live_event_stream = []
    WorkstationStateService._last_loaded_session_date = None

    t0 = datetime(2026, 8, 11, 3, 45, 0, tzinfo=timezone.utc)
    WorkstationStateService.build_from_legacy(get_base_payload(24533.85, "2026-08-11T03:45:00Z"), market_state="OPEN", now=t0)

    # Simulate 600 rapid ticks with monotonically advancing timestamps across session
    for i in range(1, 600):
        total_sec = i * 2  # tick every 2 seconds
        m = 45 + (total_sec // 60)
        s = total_sec % 60
        hh = 3 + (m // 60)
        mm = m % 60
        ts = f"2026-08-11T{hh:02d}:{mm:02d}:{s:02d}Z"
        t_tick = datetime(2026, 8, 11, hh, mm, s, tzinfo=timezone.utc)
        WorkstationStateService.build_from_legacy(get_base_payload(24500.0 + i * 0.1, ts), market_state="OPEN", now=t_tick)

    diag = WorkstationStateService.get_cache_diagnostics()
    assert diag["persistence_status"] in ("READY", "DEGRADED")
    assert diag["loaded_snapshot_count"] > 0
    assert diag["cache_session_date"] == "2026-08-11"

    # Crucial test: Ensure first 09:15 MARKET_OPEN snapshot was NOT evicted by 600 rapid ticks
    open_snaps = [
        s for s in WorkstationStateService._snapshots_history
        if s.get("market_session_phase") in ("MARKET_OPEN", "OPEN") and s.get("continuous_session_open")
    ]
    assert len(open_snaps) > 0
    assert open_snaps[0]["spot"] == 24533.85
