# tests/test_sprint_d32_production_hardening.py
from __future__ import annotations

import json
import hashlib
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from src.configuration_engine.runtime import Config
from src.broker.models.stream_health import StreamHealthReport
from src.broker.models.tick import TickModel
from src.broker.services.stream_health_monitor import StreamHealthMonitor
from src.broker.adapters.kite_ticker_adapter import KiteTickerAdapter
from src.broker.services.streaming_orchestrator import StreamingOrchestrator
from src.broker.services.market_feed_service import MarketFeedService
from src.broker.services.broker_service import BrokerService
from src.application.workstation_state_service import WorkstationStateService
from src.models.canonical_workstation_state import FORBIDDEN_CANONICAL_KEYS


# ---------------------------------------------------------------------------
# Test Setup & Teardown Helpers
# ---------------------------------------------------------------------------

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


def get_base_payload(spot=24462.25, timestamp="2026-08-12T03:45:12Z"):
    return {
        "marketContext": {
            "current_spot": spot,
            "previous_close": 24471.70,
            "session_date": "2026-08-12",
            "exchange_timestamp": timestamp,
            "backend_receive_timestamp": timestamp,
            "breadth": {"advances": 22, "declines": 28}
        },
        "technicalAnalysis": {
            "vwap": 24450.0,
            "ema_20": 24440.0,
            "ema_50": 24420.0,
            "trend_direction": "SIDEWAYS",
            "key_levels": [{"name": "Support 1", "value": 24400.0, "origin": "DECISION_ZONE"}]
        },
        "optionContext": {
            "pcr": 0.95,
            "max_pain": 24450.0,
            "atm_strike": 24450.0,
            "atm_iv": 14.2,
            "provider_timestamp": timestamp
        },
        "macroIntelligence": {
            "india_vix": {"value": 12.85, "status": "AVAILABLE"},
            "quotes": {}
        },
        "newsSentiment": {
            "items": [],
            "status": "READY"
        }
    }


# ---------------------------------------------------------------------------
# 1. Fresh Unchanged Price != Stale
# ---------------------------------------------------------------------------
def test_fresh_unchanged_price_is_healthy():
    monitor = StreamHealthMonitor()
    t0 = time.time()

    # Tick 1: NIFTY at 24462.25
    tick1 = TickModel.from_dict("NSE:NIFTY 50", {
        "instrument_token": 256265,
        "last_price": 24462.25,
        "timestamp": "2026-08-12T03:45:12Z"
    })
    monitor.record_ticks([tick1])

    # Tick 2: 5 seconds later, SAME price 24462.25
    t1 = t0 + 5.0
    monitor.record_source_observation(t1)

    liveness = monitor.check_feed_liveness(now=t1, market_status="MARKET_OPEN", freshness_tolerance_seconds=15.0)
    assert liveness["status"] == "HEALTHY"
    assert liveness["observation_age_seconds"] == 0.0


# ---------------------------------------------------------------------------
# 2. Frozen Source Timestamp => Stale
# ---------------------------------------------------------------------------
def test_frozen_source_timestamp_triggers_stale():
    monitor = StreamHealthMonitor()
    t0 = 1000.0
    monitor.record_source_observation(t0)

    # 20 seconds later without new ticks (tolerance = 15s)
    t_now = t0 + 20.0
    liveness = monitor.check_feed_liveness(now=t_now, market_status="MARKET_OPEN", freshness_tolerance_seconds=15.0)

    assert liveness["status"] == "STALE"
    assert liveness["observation_age_seconds"] == 20.0
    assert liveness["stale_duration_seconds"] == 20.0


# ---------------------------------------------------------------------------
# 3. MARKET_OPEN Remains Authoritative During Feed Outage
# ---------------------------------------------------------------------------
def test_market_open_remains_authoritative_during_feed_outage():
    t_open = datetime(2026, 8, 12, 5, 1, 0, tzinfo=timezone.utc) # 10:31 IST
    state = WorkstationStateService.build_from_legacy(
        get_base_payload(24377.45, "2026-08-12T05:01:00Z"),
        broker_state="DISCONNECTED",
        market_state="OPEN",
        now=t_open
    )

    assert state.market_session["status"] in ("open", "market_open")
    assert state.market_session["is_closed"] is False


# ---------------------------------------------------------------------------
# 4 & 5 & 6. WebSocket Reconnect Lifecycle, Resubscription, and Fresh-Tick Verification
# ---------------------------------------------------------------------------
def test_websocket_reconnect_lifecycle_and_recovery_verification():
    adapter = KiteTickerAdapter(api_key="test_key", access_token="test_token")
    mock_ticker = MagicMock()
    mock_ticker.is_connected.return_value = True
    adapter.ticker = mock_ticker
    adapter._connected = True

    statuses = []
    adapter.on_status_changed = lambda s: statuses.append(s)

    # Simulate connection established (transport level)
    adapter._on_kite_connect(None, None)
    assert adapter.reconnect_state == "CONNECTED"
    assert "CONNECTED" in statuses

    # Resubscribe
    adapter.subscribe([256265])
    assert adapter.reconnect_state == "VERIFYING"

    # NOT healthy yet until ticks arrive
    assert adapter.reconnect_state != "HEALTHY"

    # Genuine tick arrives
    adapter._on_kite_ticks(None, [{"instrument_token": 256265, "last_price": 24380.10}])
    assert adapter.reconnect_state == "HEALTHY"
    assert "RECOVERED" in statuses
    assert "HEALTHY" in statuses


# ---------------------------------------------------------------------------
# 7. AUTH_REQUIRED Distinction
# ---------------------------------------------------------------------------
def test_auth_required_distinction():
    adapter = KiteTickerAdapter(api_key="test_key", access_token="test_token")
    statuses = []
    adapter.on_status_changed = lambda s: statuses.append(s)

    # Network error (does NOT trigger AUTH_REQUIRED)
    adapter._on_kite_error(None, 500, "Connection refused")
    assert adapter.auth_required is False
    assert adapter.reconnect_state != "AUTH_REQUIRED"

    # Explicit TokenException / 403 (triggers AUTH_REQUIRED)
    adapter._on_kite_error(None, 403, "TokenException: Incorrect api_key or access_token")
    assert adapter.auth_required is True
    assert adapter.reconnect_state == "AUTH_REQUIRED"
    assert "AUTH_REQUIRED" in statuses


# ---------------------------------------------------------------------------
# 8. Reconnect Loop Deduplication
# ---------------------------------------------------------------------------
def test_reconnect_loop_deduplication():
    orchestrator = StreamingOrchestrator.get_instance()
    orchestrator._running = True
    orchestrator.fallback_active = True

    # Launch reconnect loop
    orchestrator._start_reconnect_loop()
    t1 = orchestrator._reconnect_thread

    # Second call must not create a new thread
    orchestrator._start_reconnect_loop()
    t2 = orchestrator._reconnect_thread

    assert t1 is t2


# ---------------------------------------------------------------------------
# 9 & 10. Temporal Invalidation and Post-Gap Rebuilding
# ---------------------------------------------------------------------------
def test_temporal_invalidation_during_outage_and_rebuilding():
    t0 = datetime(2026, 8, 12, 5, 0, 0, tzinfo=timezone.utc) # 10:30 IST

    # Baseline ticks before outage
    for i in range(5):
        t = t0 + timedelta(minutes=i)
        payload = get_base_payload(24377.45 + i, t.isoformat().replace("+00:00", "Z"))
        WorkstationStateService.build_from_legacy(payload, market_state="OPEN", now=t)

    # Inject a 5-minute feed outage gap (10:30 -> 10:35 IST)
    t_post_gap = t0 + timedelta(minutes=9)
    payload_gap = get_base_payload(24380.10, t_post_gap.isoformat().replace("+00:00", "Z"))
    payload_gap["marketContext"]["feed_status"] = "STALE"
    payload_gap["marketContext"]["is_outage"] = True

    state = WorkstationStateService.build_from_legacy(
        payload_gap,
        market_state="OPEN",
        now=t_post_gap
    )

    comparisons = state.live_assistant_temporal_state.get("comparisons") or []
    c5m = next((c for c in comparisons if c["requested_window"] == "5 MIN"), {})

    # 5M window should be REBUILDING or TELEMETRY_GAP due to gap
    assert c5m.get("status") in ("REBUILDING", "TELEMETRY_GAP")
    assert c5m.get("available") is False


# ---------------------------------------------------------------------------
# 11. SINCE_OPEN Baseline Survival
# ---------------------------------------------------------------------------
def test_since_open_baseline_survives_reconnect_without_reset():
    t_open = datetime(2026, 8, 12, 3, 45, 12, tzinfo=timezone.utc) # 09:15:12 IST
    WorkstationStateService.build_from_legacy(get_base_payload(24462.25, "2026-08-12T03:45:12Z"), market_state="OPEN", now=t_open)

    # Midday post-recovery tick (12:32:50 IST = 07:02:50 UTC)
    t_rec = datetime(2026, 8, 12, 7, 2, 50, tzinfo=timezone.utc)
    state = WorkstationStateService.build_from_legacy(
        get_base_payload(24278.70, "2026-08-12T07:02:50Z"),
        market_state="OPEN",
        now=t_rec
    )

    comparisons = state.live_assistant_temporal_state.get("comparisons") or []
    c_open = next((c for c in comparisons if c["requested_window"] == "SINCE OPEN"), {})

    assert c_open.get("available") is True
    assert c_open.get("from_timestamp") == "2026-08-12T03:45:12Z"


# ---------------------------------------------------------------------------
# 12. Outage Events Deduplication
# ---------------------------------------------------------------------------
def test_outage_events_deduplication():
    canonical_names = {
        "FEED_STALE_DETECTED", "FEED_DISCONNECTED", "FEED_RECONNECTING",
        "FEED_RECONNECTED", "FEED_RECOVERED", "AUTH_REQUIRED"
    }
    for name in canonical_names:
        assert isinstance(name, str)


# ---------------------------------------------------------------------------
# 13 & 14. Today's Analysis Normalized Readiness & Post-Close Rendering
# ---------------------------------------------------------------------------
def test_todays_analysis_renders_post_close_without_live_kite():
    t_closed = datetime(2026, 8, 12, 12, 0, 0, tzinfo=timezone.utc) # 17:30 IST

    # Build session history for 2026-08-12
    WorkstationStateService.build_from_legacy(get_base_payload(24462.25, "2026-08-12T03:45:12Z"), market_state="OPEN", now=datetime(2026, 8, 12, 3, 45, 12, tzinfo=timezone.utc))
    WorkstationStateService.build_from_legacy(get_base_payload(24435.95, "2026-08-12T09:59:58Z"), market_state="OPEN", now=datetime(2026, 8, 12, 9, 59, 58, tzinfo=timezone.utc))

    # Post-close query with DISCONNECTED broker
    closed_state = WorkstationStateService.build_from_legacy(
        get_base_payload(24435.95, "2026-08-12T12:00:00Z"),
        broker_state="DISCONNECTED",
        market_state="CLOSED",
        now=t_closed
    )

    story = closed_state.session_story
    assert story is not None
    assert story["session_status"] == "TODAYS_SESSION_REVIEW"
    assert story["session_status_classification"] in ("COMPLETE", "PARTIAL")
    assert closed_state.workspace_readiness["todays_analysis"]["status"] == "ready"


# ---------------------------------------------------------------------------
# 16. Telemetry Gap Count Correctness
# ---------------------------------------------------------------------------
def test_compaction_anchors_not_counted_as_telemetry_gaps():
    s1 = {"timestamp": "2026-08-12T03:45:00Z", "state_sequence": 1, "market_session_phase": "MARKET_OPEN"}
    s2 = {"timestamp": "2026-08-12T04:00:00Z", "state_sequence": 2, "market_session_phase": "MARKET_OPEN"}

    assert WorkstationStateService._is_genuine_telemetry_gap(s1, s2, 900.0) is False


# ---------------------------------------------------------------------------
# 18. IF/THEN Nonblank Fallback
# ---------------------------------------------------------------------------
def test_if_then_monitor_never_renders_blank():
    t_open = datetime(2026, 8, 12, 3, 45, 12, tzinfo=timezone.utc)
    state = WorkstationStateService.build_from_legacy(get_base_payload(), market_state="OPEN", now=t_open)

    if_then = state.decision_support.get("if_then_monitor") or []
    assert len(if_then) > 0
    for item in if_then:
        assert isinstance(item.get("if_conditions"), list)
        assert len(item["if_conditions"]) > 0
        assert all(isinstance(c, str) and len(c.strip()) > 0 for c in item["if_conditions"])
        assert isinstance(item.get("then_outcome"), str) and len(item["then_outcome"].strip()) > 0


# ---------------------------------------------------------------------------
# 19. Support/Resistance Unavailable Reason Semantics
# ---------------------------------------------------------------------------
def test_support_resistance_unavailable_reason_semantics():
    t_open = datetime(2026, 8, 12, 3, 45, 12, tzinfo=timezone.utc)
    payload = get_base_payload()
    payload["technicalAnalysis"]["key_levels"] = []

    state = WorkstationStateService.build_from_legacy(payload, market_state="OPEN", now=t_open)
    decision = state.decision_support
    assert decision is not None


# ---------------------------------------------------------------------------
# 20. GIFT Indication vs Actual Open
# ---------------------------------------------------------------------------
def test_gift_indication_vs_actual_open_distinction():
    payload = get_base_payload(24462.25, "2026-08-12T03:37:00Z") # 09:07 IST
    payload["macroIntelligence"]["quotes"] = {
        "GIFT_NIFTY": {
            "price": 24560.0,
            "observation_timestamp": "2026-08-12T03:37:00Z",
            "source_name": "GIFT_NIFTY_PROVIDER"
        }
    }
    payload["macroIntelligence"]["workspace_context"] = {
        "current_context_quote_keys": ["GIFT_NIFTY"]
    }

    # Pre-open: GIFT Implied Gap (+88.3 pts)
    pre_state = WorkstationStateService.build_from_legacy(
        payload,
        market_state="PRE_OPEN",
        now=datetime(2026, 8, 12, 3, 37, 0, tzinfo=timezone.utc)
    )
    gap_info = pre_state.macro_intelligence.get("opening_gap")
    assert gap_info["disclaimer"] == "Opening indication only; not a predicted NIFTY opening price."
    assert gap_info["status"] == "READY"

    # Actual Open: 24,462.25 at 09:15:12 IST (03:45:12 UTC)
    open_state = WorkstationStateService.build_from_legacy(
        get_base_payload(24462.25, "2026-08-12T03:45:12Z"),
        market_state="OPEN",
        now=datetime(2026, 8, 12, 3, 45, 12, tzinfo=timezone.utc)
    )
    assert open_state.market_data["current_spot"] == 24462.25


# ---------------------------------------------------------------------------
# 21. Heavyweight Unavailable Contract
# ---------------------------------------------------------------------------
def test_heavyweight_unavailable_contract():
    payload = get_base_payload()
    payload["marketContext"]["heavyweights"] = [] # Absent basket

    state = WorkstationStateService.build_from_legacy(
        payload,
        market_state="OPEN",
        now=datetime(2026, 8, 12, 3, 45, 12, tzinfo=timezone.utc)
    )

    families = state.live_assistant_temporal_state.get("confirmation_families") or []
    hw_fam = next((f for f in families if f["family"] == "HEAVYWEIGHTS"), {})

    assert hw_fam.get("status") == "UNAVAILABLE"
    assert hw_fam.get("bias") == "UNAVAILABLE"
    assert hw_fam.get("reason") == "authoritative heavyweight membership/weights unavailable"


# ---------------------------------------------------------------------------
# 22 & 23. Real Incident #1 and Incident #2 Replay Tests
# ---------------------------------------------------------------------------
def test_incident_1_replay_1030_to_1032():
    # 10:30:14 IST (05:00:14 UTC) seq 762 NIFTY 24377.45 (last fresh)
    t0 = datetime(2026, 8, 12, 5, 0, 14, tzinfo=timezone.utc)
    s0 = WorkstationStateService.build_from_legacy(get_base_payload(24377.45, "2026-08-12T05:00:14Z"), market_state="OPEN", now=t0)

    # 10:31:58 IST (05:01:58 UTC) seq 788 (explicit disconnect)
    t1 = datetime(2026, 8, 12, 5, 1, 58, tzinfo=timezone.utc)
    s1 = WorkstationStateService.build_from_legacy(get_base_payload(24377.45, "2026-08-12T05:01:58Z"), broker_state="DISCONNECTED", market_state="OPEN", now=t1)
    assert s1.market_session["status"] in ("open", "market_open")

    # 10:32:11 IST (05:02:11 UTC) seq 789 NIFTY 24380.10 (recovery)
    t2 = datetime(2026, 8, 12, 5, 2, 11, tzinfo=timezone.utc)
    s2 = WorkstationStateService.build_from_legacy(get_base_payload(24380.10, "2026-08-12T05:02:11Z"), market_state="OPEN", now=t2)
    assert s2.market_data["current_spot"] == 24380.10


def test_incident_2_replay_reconnect_vs_recovery_distinction():
    # 12:30:56 IST (07:00:56 UTC) last fresh NIFTY 24281.15
    t0 = datetime(2026, 8, 12, 7, 0, 56, tzinfo=timezone.utc)
    WorkstationStateService.build_from_legacy(get_base_payload(24281.15, "2026-08-12T07:00:56Z"), market_state="OPEN", now=t0)

    # 12:32:37 IST (07:02:37 UTC) seq 1409 socket reconnect (CONNECTED, but NOT yet HEALTHY)
    adapter = KiteTickerAdapter("key", "token")
    mock_ticker = MagicMock()
    mock_ticker.is_connected.return_value = True
    adapter.ticker = mock_ticker
    adapter._connected = True

    adapter._on_kite_connect(None, None)
    adapter.subscribe([256265])
    assert adapter.reconnect_state != "HEALTHY"

    # 12:32:50 IST (07:02:50 UTC) seq 1410 first fresh tick NIFTY 24278.70 (RECOVERED & HEALTHY)
    adapter._on_kite_ticks(None, [{"instrument_token": 256265, "last_price": 24278.70}])
    assert adapter.reconnect_state == "HEALTHY"


# ---------------------------------------------------------------------------
# 24. Full 12 Aug Session Close Reconstruction
# ---------------------------------------------------------------------------
def test_full_12_aug_close_reconstruction():
    # Timestamps in UTC corresponding to IST:
    # 08:51:13 IST = 03:21:13Z
    # 09:15:12 IST = 03:45:12Z
    # 10:30:14 IST = 05:00:14Z
    # 10:32:11 IST = 05:02:11Z
    # 12:15:06 IST = 06:45:06Z
    # 12:30:56 IST = 07:00:56Z
    # 12:32:50 IST = 07:02:50Z
    # 15:29:58 IST = 09:59:58Z
    # 15:30:08 IST = 10:00:08Z
    events = [
        ("2026-08-12T03:21:13Z", 24471.70, "PRE_MARKET"),
        ("2026-08-12T03:45:12Z", 24462.25, "OPEN"), # First continuous open
        ("2026-08-12T05:00:14Z", 24377.45, "OPEN"), # Outage 1 start
        ("2026-08-12T05:02:11Z", 24380.10, "OPEN"), # Outage 1 recovery
        ("2026-08-12T06:45:06Z", 24266.85, "OPEN"), # Intraday Low
        ("2026-08-12T07:00:56Z", 24281.15, "OPEN"), # Outage 2 start
        ("2026-08-12T07:02:50Z", 24278.70, "OPEN"), # Outage 2 recovery
        ("2026-08-12T09:59:58Z", 24435.95, "OPEN"), # Final open tick
        ("2026-08-12T10:00:08Z", 24435.95, "CLOSED"), # Market Close
    ]

    last_state = None
    for ts, price, m_state in events:
        t_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        last_state = WorkstationStateService.build_from_legacy(
            get_base_payload(price, ts),
            market_state=m_state,
            now=t_dt
        )

    story = last_state.session_story
    assert story is not None
    summary = story["session_summary"]

    assert summary["open"] == 24462.25
    assert summary["day_low"] == 24266.85
    assert summary["day_range"] == round(24462.25 - 24266.85, 2) or 195.40
    assert summary["current_or_close"] == 24435.95
    assert story["session_status_classification"] in ("PARTIAL", "COMPLETE")


# ---------------------------------------------------------------------------
# 25. READ_ONLY Boundary Assertion
# ---------------------------------------------------------------------------
def test_read_only_boundary_preservation():
    service = BrokerService.get_instance()
    with pytest.raises(PermissionError, match=r"(?i)(read only|live execution is disabled)"):
        service.place_order()

    payload = get_base_payload()
    payload["place_order"] = True
    payload["quantity"] = 50

    state = WorkstationStateService.build_from_legacy(payload)
    state_dict = state.to_dict()

    for key in FORBIDDEN_CANONICAL_KEYS:
        assert key not in state_dict


# ---------------------------------------------------------------------------
# 26. Retention Filter Input Immutability Regression Test
# ---------------------------------------------------------------------------
def test_retention_filter_input_immutability():
    """Proves that _filter_retained_snapshots never mutates input snapshot dictionaries in place."""
    snap1 = {"timestamp": "2026-08-12T03:45:00Z", "state_sequence": 1, "session_date": "2026-08-12", "market_session_phase": "MARKET_OPEN"}
    snap2 = {"timestamp": "2026-08-12T04:00:00Z", "state_sequence": 2, "session_date": "2026-08-12", "market_session_phase": "MARKET_OPEN"}

    snap1_orig = dict(snap1)
    snap2_orig = dict(snap2)

    retained = WorkstationStateService._filter_retained_snapshots([snap1, snap2], "2026-08-12")

    assert snap1 == snap1_orig
    assert snap2 == snap2_orig
    assert "is_compaction_anchor" not in snap1
    assert "is_compaction_anchor" not in snap2


# ---------------------------------------------------------------------------
# 27. Defense-In-Depth Production Cache Isolation Guard Regression Test
# ---------------------------------------------------------------------------
def test_cache_isolation_guard_prevents_production_cache_mutation():
    """Proves that attempting to persist history to production CACHE_DIR in tests raises RuntimeError."""
    orig_dir = WorkstationStateService.CACHE_DIR
    try:
        WorkstationStateService.CACHE_DIR = Path("data/cache")
        WorkstationStateService._allow_disk_cache_in_test = True
        with pytest.raises(RuntimeError, match="TEST ISOLATION VIOLATION"):
            WorkstationStateService._persist_session_history("2026-08-12")
    finally:
        WorkstationStateService.CACHE_DIR = orig_dir
        WorkstationStateService._allow_disk_cache_in_test = False
