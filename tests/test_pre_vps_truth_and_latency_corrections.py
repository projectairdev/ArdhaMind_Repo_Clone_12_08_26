# tests/test_pre_vps_truth_and_latency_corrections.py
from __future__ import annotations

import json
import hashlib
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest

from src.application.workstation_state_service import WorkstationStateService
from src.broker.services.broker_service import BrokerService
from src.broker.models.tick import TickModel
from src.broker.services.stream_health_monitor import StreamHealthMonitor
from src.models.canonical_workstation_state import FORBIDDEN_CANONICAL_KEYS


@pytest.fixture(autouse=True)
def reset_services(tmp_path):
    """Reset singletons and isolate CACHE_DIR to tmp_path before each test."""
    WorkstationStateService.reset_for_testing()
    orig_cache_dir = WorkstationStateService.CACHE_DIR
    WorkstationStateService.CACHE_DIR = tmp_path
    yield
    WorkstationStateService.CACHE_DIR = orig_cache_dir
    WorkstationStateService._allow_disk_cache_in_test = False
    WorkstationStateService.reset_for_testing()


def get_12_aug_session_data():
    """Loads authoritative 12 Aug historical session data for testing."""
    hist_file = Path("data/cache/session_history_2026-08-12.json")
    assert hist_file.exists(), "Authoritative 12 Aug session history file must exist"
    with open(hist_file, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 1. 09:15 Checkpoint uses 24,462.25, not 24,435.95
# ---------------------------------------------------------------------------
def test_0915_checkpoint_uses_authoritative_open():
    data = get_12_aug_session_data()
    WorkstationStateService._snapshots_history = data["snapshots"]
    WorkstationStateService._live_event_stream = data.get("material_events", [])

    snap = data["snapshots"][-1]
    story = WorkstationStateService._derive_session_story(
        generated="2026-08-12T10:00:00Z",
        now=datetime(2026, 8, 12, 18, 0, 0, tzinfo=timezone.utc),
        snap=snap,
        unified={"previous_close": 24583.80},
        live_decision={},
        primary_temporal=None,
        news={},
        market_session_phase="CLOSED",
        market_closed=True
    )

    timeline = story["timeline"]
    open_ckpt = next((item for item in timeline if item["timestamp"] == "09:15"), None)
    assert open_ckpt is not None
    assert open_ckpt["market_snapshot"]["nifty"] == 24462.25
    assert open_ckpt["market_snapshot"]["nifty"] != 24435.95


# ---------------------------------------------------------------------------
# 2. 09:15 Opening Change is calculated from authoritative open and prev_close
# ---------------------------------------------------------------------------
def test_0915_opening_change_calculation():
    data = get_12_aug_session_data()
    WorkstationStateService._snapshots_history = data["snapshots"]
    WorkstationStateService._live_event_stream = data.get("material_events", [])

    snap = data["snapshots"][-1]
    story = WorkstationStateService._derive_session_story(
        generated="2026-08-12T10:00:00Z",
        now=datetime(2026, 8, 12, 18, 0, 0, tzinfo=timezone.utc),
        snap=snap,
        unified={"previous_close": 24583.80},
        live_decision={},
        primary_temporal=None,
        news={},
        market_session_phase="CLOSED",
        market_closed=True
    )

    open_ckpt = next((item for item in story["timeline"] if item["timestamp"] == "09:15"), None)
    assert open_ckpt is not None
    # 24462.25 - 24583.80 = -121.55 pts
    assert open_ckpt["market_snapshot"]["change_points"] == -121.55


# ---------------------------------------------------------------------------
# 3. Missing open can never serialize/render as 0.00
# ---------------------------------------------------------------------------
def test_missing_open_never_serializes_as_zero():
    story = WorkstationStateService._derive_session_story(
        generated="2026-08-12T10:00:00Z",
        now=datetime(2026, 8, 12, 18, 0, 0, tzinfo=timezone.utc),
        snap={"session_date": "2026-08-12"},
        unified={"previous_close": 24583.80},
        live_decision={},
        primary_temporal=None,
        news={},
        market_session_phase="CLOSED",
        market_closed=True
    )
    assert story["session_summary"]["open"] is None or story["session_summary"]["open"] > 0
    assert story["session_summary"]["open"] != 0.0


# ---------------------------------------------------------------------------
# 4 & 5. Session low includes 24,266.85 at 12:15:06 and range is 195.40
# ---------------------------------------------------------------------------
def test_session_low_and_range_reconstruction():
    data = get_12_aug_session_data()
    WorkstationStateService._snapshots_history = data["snapshots"]
    WorkstationStateService._live_event_stream = data.get("material_events", [])

    snap = data["snapshots"][-1]
    story = WorkstationStateService._derive_session_story(
        generated="2026-08-12T10:00:00Z",
        now=datetime(2026, 8, 12, 18, 0, 0, tzinfo=timezone.utc),
        snap=snap,
        unified={"previous_close": 24583.80},
        live_decision={},
        primary_temporal=None,
        news={},
        market_session_phase="CLOSED",
        market_closed=True
    )

    summary = story["session_summary"]
    assert summary["day_low"] == 24266.85
    assert summary["day_high"] == 24462.25
    assert summary["day_range"] == 195.40

    low_ckpt = next((item for item in story["timeline"] if item.get("event_type") == "SESSION_LOW"), None)
    assert low_ckpt is not None
    assert low_ckpt["timestamp"] == "12:15"
    assert low_ckpt["market_snapshot"]["nifty"] == 24266.85


# ---------------------------------------------------------------------------
# 6. Final settlement remains 24,435.95
# ---------------------------------------------------------------------------
def test_final_settlement_remains_24435_95():
    data = get_12_aug_session_data()
    WorkstationStateService._snapshots_history = data["snapshots"]
    snap = data["snapshots"][-1]
    story = WorkstationStateService._derive_session_story(
        generated="2026-08-12T10:00:00Z",
        now=datetime(2026, 8, 12, 18, 0, 0, tzinfo=timezone.utc),
        snap=snap,
        unified={"previous_close": 24583.80},
        live_decision={},
        primary_temporal=None,
        news={},
        market_session_phase="CLOSED",
        market_closed=True
    )
    assert story["session_summary"]["current_or_close"] == 24435.95


# ---------------------------------------------------------------------------
# 7 & 8. As-Of-Time Checkpoint Semantics (No Backward Leakage)
# ---------------------------------------------------------------------------
def test_as_of_time_checkpoint_semantics():
    data = get_12_aug_session_data()
    WorkstationStateService._snapshots_history = data["snapshots"]
    snap = data["snapshots"][-1]
    story = WorkstationStateService._derive_session_story(
        generated="2026-08-12T10:00:00Z",
        now=datetime(2026, 8, 12, 18, 0, 0, tzinfo=timezone.utc),
        snap=snap,
        unified={"previous_close": 24583.80},
        live_decision={},
        primary_temporal=None,
        news={},
        market_session_phase="CLOSED",
        market_closed=True
    )

    pre_market = next((item for item in story["timeline"] if item["timestamp"] == "08:50"), None)
    pre_open = next((item for item in story["timeline"] if item["timestamp"] == "09:07"), None)

    # 08:50 & 09:07 must NOT inherit 15:30 close spot (24,435.95)
    if pre_market and pre_market["market_snapshot"]["nifty"] is not None:
        assert pre_market["market_snapshot"]["nifty"] != 24435.95
    if pre_open and pre_open["market_snapshot"]["nifty"] is not None:
        assert pre_open["market_snapshot"]["nifty"] != 24435.95


# ---------------------------------------------------------------------------
# 10. Historical review does not report live SOURCE_STALE solely because session is old
# ---------------------------------------------------------------------------
def test_historical_review_does_not_report_live_source_stale():
    data = get_12_aug_session_data()
    WorkstationStateService._snapshots_history = data["snapshots"]
    snap = data["snapshots"][-1]
    story = WorkstationStateService._derive_session_story(
        generated="2026-08-12T10:00:00Z",
        now=datetime(2026, 8, 12, 18, 0, 0, tzinfo=timezone.utc),
        snap=snap,
        unified={"previous_close": 24583.80},
        live_decision={},
        primary_temporal=None,
        news={},
        market_session_phase="CLOSED",
        market_closed=True
    )
    assert story["session_status"] == "TODAYS_SESSION_REVIEW"
    assert story["session_status_classification"] in ("COMPLETE", "PARTIAL")


# ---------------------------------------------------------------------------
# 11. News Context Filtered by Session Date
# ---------------------------------------------------------------------------
def test_news_context_filtered_by_session_date():
    data = get_12_aug_session_data()
    WorkstationStateService._snapshots_history = data["snapshots"]
    snap = data["snapshots"][-1]

    # News test suite: stale news (2026-08-10), overnight pre-market news (2026-08-11T16:00:00Z), and future news (2026-08-13)
    scoped_news = {
        "items": [
            {
                "id": "stale-1",
                "headline": "Old Earnings Report",
                "published_at": "2026-08-10T09:15:00Z",
                "nifty_relevance_score": 85
            },
            {
                "id": "overnight-1",
                "headline": "US Fed Signals Rate Pause Overnight",
                "published_at": "2026-08-11T16:00:00Z",
                "nifty_relevance_score": 85
            },
            {
                "id": "future-1",
                "headline": "Future RBI Policy Announcement",
                "published_at": "2026-08-13T09:15:00Z",
                "nifty_relevance_score": 85
            }
        ]
    }

    story = WorkstationStateService._derive_session_story(
        generated="2026-08-12T10:00:00Z",
        now=datetime(2026, 8, 12, 18, 0, 0, tzinfo=timezone.utc),
        snap=snap,
        unified={"previous_close": 24583.80},
        live_decision={},
        primary_temporal=None,
        news=scoped_news,
        market_session_phase="CLOSED",
        market_closed=True
    )

    # Stale news (2026-08-10) and Future news (2026-08-13) MUST be excluded from 12 Aug timeline
    for item in story["timeline"]:
        for n in item.get("news_context", []):
            assert n.get("id") != "future-1"
            assert n.get("id") != "stale-1"


# ---------------------------------------------------------------------------
# 13. Authoritative Historical SHA-256 Remains Immutable
# ---------------------------------------------------------------------------
def test_authoritative_historical_sha256_unmodified():
    hist_file = Path("data/cache/session_history_2026-08-12.json")
    with open(hist_file, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest().upper()
    assert sha == "7A1679C69E3A90BCE302F3CA3107DFE3795AC3EB26506FAB01B236A65C03AA8C"


# ---------------------------------------------------------------------------
# 14 & 15. Live First-Observation Propagation Latency
# ---------------------------------------------------------------------------
def test_live_first_observation_propagation_latency():
    monitor = StreamHealthMonitor()
    t0 = time.time()
    tick = TickModel(
        instrument_token=256265,
        symbol="NSE:NIFTY 50",
        last_price=24462.25,
        volume=100,
        oi=0,
        open=24462.25,
        high=24462.25,
        low=24266.85,
        close=24435.95,
        change=0.0,
        timestamp="2026-08-12T03:45:12Z"
    )
    monitor.record_ticks([tick])
    t1 = time.time()
    report = monitor.generate_report(connection_status="CONNECTED", active_subscriptions=["NSE:NIFTY 50"])
    t2 = time.time()

    assert report.feed_liveness_status == "HEALTHY"
    assert (t2 - t0) < 0.100  # Must process observation in under 100ms
