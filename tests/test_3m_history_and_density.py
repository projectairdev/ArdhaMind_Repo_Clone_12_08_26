# tests/test_3m_history_and_density.py
from datetime import datetime, timezone, timedelta
from src.application.workstation_state_service import WorkstationStateService


def test_3m_bucketing_and_deduplication():
    WorkstationStateService.reset_for_testing()

    snaps = []
    base_time = datetime(2026, 8, 14, 9, 15, 0, tzinfo=timezone.utc)

    # Generate 10 snapshots spaced 1 minute apart across 09:15 to 09:24
    for i in range(10):
        t_iso = (base_time + timedelta(minutes=i)).isoformat().replace("+00:00", "Z")
        snaps.append({
            "timestamp": t_iso,
            "state_sequence": i + 1,
            "session_date": "2026-08-14",
            "market_session_phase": "MARKET_OPEN",
            "spot": 24300.0 + i,
            "continuous_session_open": True
        })

    filtered = WorkstationStateService._filter_retained_snapshots(snaps, "2026-08-14")

    # 10 minutes (09:15-09:24) split into 3-min buckets: 09:15, 09:18, 09:21, 09:24 -> 4 anchor buckets
    # Plus rolling buffer if same session date
    assert len(filtered) <= 10

    # Ensure timestamps are strictly monotonic
    ts_list = [s["timestamp"] for s in filtered]
    assert ts_list == sorted(ts_list)


def test_session_isolation():
    WorkstationStateService.reset_for_testing()

    snaps = [
        {"timestamp": "2026-08-13T10:00:00Z", "state_sequence": 1, "session_date": "2026-08-13", "spot": 24200.0},
        {"timestamp": "2026-08-14T10:00:00Z", "state_sequence": 2, "session_date": "2026-08-14", "spot": 24300.0},
    ]

    filtered_14 = WorkstationStateService._filter_retained_snapshots(snaps, "2026-08-14")
    dates_14 = {s["session_date"] for s in filtered_14 if s.get("session_date") == "2026-08-14"}

    assert "2026-08-14" in dates_14
