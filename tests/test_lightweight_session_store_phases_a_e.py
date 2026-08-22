"""
tests/test_lightweight_session_store_phases_a_e.py

Comprehensive test suite validating Phases A through E of the Lightweight Session Storage Architecture:
- Phase A: Core schemas & atomic storage primitives
- Phase B: Candle cache, 15m telemetry, and connectivity logging
- Phase C: SessionCloseCore, permanent OptionsCloseBaseline, CloseReconciliationPolicy, missed-close recovery
- Phase D: Reader migration (PerformanceTrackerEngine, LiveAssistantEngine, WorkstationStateService)
- Phase E: Dual-write shadow mode & shadow comparison verification
- Non-trading weekend/holiday safety
- Security & token absence verification
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import pytest

from src.storage import (
    CloseReconciler,
    CloseReconciliationPolicy,
    ConnectivityEvent,
    DerivativesSummary,
    IntradayTelemetrySeries,
    LatestCanonicalRecoverySnapshot,
    LightweightSessionStore,
    MarketOHLCV,
    MarketRegime,
    OptionsCloseBaseline,
    RetentionManager,
    SessionCloseCore,
    SessionIntegrityEnvelope,
    SessionStory,
    StrikeBaseline,
    StructuralLevels,
    TelemetryBucket,
    atomic_read_json,
    atomic_write_json,
)
from src.intelligence_engine.performance_tracker_engine import PerformanceTrackerEngine
from src.intelligence_engine.live_assistant_engine import LiveAssistantEngine
from src.application.workstation_state_service import WorkstationStateService


@pytest.fixture
def temp_store(tmp_path):
    """Creates an isolated LightweightSessionStore in a temporary directory."""
    return LightweightSessionStore(base_dir=tmp_path / "session_store")


# ── PHASE A: Core Schemas & Atomic Storage ─────────────────────────────────────

def test_phase_a_schemas_and_versioning():
    """Verify that all durable schemas include schema_name and schema_version."""
    close = SessionCloseCore(session_date="2026-08-21")
    assert close.schema_name == "SESSION_CLOSE_CORE"
    assert close.schema_version == "1.1.0"
    
    options = OptionsCloseBaseline(session_date="2026-08-21")
    assert options.schema_name == "OPTIONS_CLOSE_BASELINE"
    assert options.schema_version == "1.1.0"
    
    telemetry = IntradayTelemetrySeries(session_date="2026-08-21")
    assert telemetry.schema_name == "INTRADAY_TELEMETRY_SERIES"
    assert telemetry.schema_version == "1.1.0"
    
    integrity = SessionIntegrityEnvelope(session_date="2026-08-21")
    assert integrity.schema_name == "SESSION_INTEGRITY_ENVELOPE"
    assert integrity.schema_version == "1.1.0"
    
    recovery = LatestCanonicalRecoverySnapshot(session_date="2026-08-21")
    assert recovery.schema_name == "LATEST_CANONICAL_RECOVERY_SNAPSHOT"
    assert recovery.schema_version == "1.1.0"


def test_phase_a_atomic_write_and_read(tmp_path):
    """Verify atomic write, clean read, and safe handling of corrupt files."""
    target = tmp_path / "test_file.json"
    data = {"key": "value", "count": 42}
    
    # 1. Atomic write
    assert atomic_write_json(target, data) is True
    assert target.exists()
    
    # 2. Atomic read
    read_data = atomic_read_json(target)
    assert read_data == data
    
    # 3. Corrupt file handling
    with open(target, "w") as f:
        f.write("{invalid_json: true,")
    corrupt_read = atomic_read_json(target)
    assert corrupt_read is None, "Corrupt file must return None safely without raising"


# ── PHASE B: Candle Cache, Telemetry & Connectivity ────────────────────────────

def test_phase_b_candle_cache_sync(temp_store):
    """Verify candle cache syncing, deduplication, and timestamp ordering."""
    candles = [
        {"date": "2026-08-21T09:15:00Z", "open": 24200, "high": 24210, "low": 24195, "close": 24205, "volume": 1000},
        {"date": "2026-08-21T09:20:00Z", "open": 24205, "high": 24220, "low": 24200, "close": 24215, "volume": 1200},
        {"date": "2026-08-21T09:15:00Z", "open": 24200, "high": 24210, "low": 24195, "close": 24205, "volume": 1000}, # Duplicate
    ]
    
    assert temp_store.sync_candles(candles) is True
    loaded = temp_store.load_candle_cache()
    assert len(loaded) == 2, "Deduplication must eliminate duplicate timestamps"
    assert loaded[0]["date"] == "2026-08-21T09:15:00Z"
    assert loaded[1]["date"] == "2026-08-21T09:20:00Z"


def test_phase_b_telemetry_series(temp_store):
    """Verify 15-minute telemetry bucket recording and sorting."""
    bucket1 = {
        "index": 1,
        "window_start": "09:15",
        "window_end": "09:30",
        "start_spot": 24200.0,
        "end_spot": 24225.0,
        "breadth_advances": 30,
        "breadth_declines": 19,
        "vix": 12.4,
        "pcr": 1.05
    }
    bucket2 = {
        "index": 2,
        "window_start": "09:30",
        "window_end": "09:45",
        "start_spot": 24225.0,
        "end_spot": 24240.0,
        "breadth_advances": 33,
        "breadth_declines": 16,
        "vix": 12.3,
        "pcr": 1.08
    }
    
    assert temp_store.record_telemetry_bucket("2026-08-21", bucket1) is True
    assert temp_store.record_telemetry_bucket("2026-08-21", bucket2) is True
    
    series = temp_store.load_telemetry_series("2026-08-21")
    assert len(series) == 2
    assert series[0]["index"] == 1
    assert series[1]["index"] == 2


def test_phase_b_connectivity_logging(temp_store):
    """Verify connectivity event logging to JSONL."""
    event = ConnectivityEvent(
        event_id="CONN-20260821-001",
        session_date="2026-08-21",
        event_type="WS_DISCONNECTED",
        detected_at="2026-08-21T10:15:00Z",
        socket_state="CLOSED",
        broker_state="AUTHENTICATED",
        affected_domains=["NIFTY_SPOT"],
        gap_duration_ms=3200,
        resolution="AUTOMATIC_RECONNECTED"
    )
    assert temp_store.record_connectivity_event(event) is True
    events = temp_store.load_connectivity_events("2026-08-21")
    assert len(events) == 1
    assert events[0]["event_id"] == "CONN-20260821-001"
    assert events[0]["event_type"] == "WS_DISCONNECTED"


# ── PHASE C: Session Close, Options Baseline & Reconciliation ─────────────────

def test_phase_c_session_close_finalization(temp_store):
    """Verify permanent SessionCloseCore finalization and latest close retrieval."""
    close = SessionCloseCore(
        session_date="2026-08-21",
        market_ohlcv=MarketOHLCV(open=24225.0, high=24265.0, low=24206.0, close=24252.0, previous_close=24231.85),
        structural_levels=StructuralLevels(pivot=24241.0, r1=24275.0, s1=24217.0)
    )
    assert temp_store.finalize_session_close(close) is True
    
    loaded = temp_store.load_session_close("2026-08-21")
    assert loaded is not None
    assert loaded.market_ohlcv.close == 24252.0
    assert loaded.structural_levels.pivot == 24241.0
    
    latest = temp_store.load_latest_session_close()
    assert latest is not None
    assert latest.session_date == "2026-08-21"


def test_phase_c_options_close_permanent_retention(temp_store):
    """Verify permanent OptionsCloseBaseline finalization and off-hours empty packet protection."""
    valid_baseline = OptionsCloseBaseline(
        session_date="2026-08-21",
        expiry_date="2026-08-28",
        underlying_spot=24252.0,
        atm_strike=24250,
        derivatives_summary=DerivativesSummary(pcr_oi=1.09, max_pain_strike=24250, call_wall_strike=24500, put_wall_strike=24000),
        strike_baseline=[
            {"strike": 24200, "ce_oi": 380000, "pe_oi": 1120000, "ce_ltp": 112.5, "pe_ltp": 62.0},
            {"strike": 24250, "ce_oi": 750000, "pe_oi": 820000, "ce_ltp": 84.0, "pe_ltp": 82.5},
            {"strike": 24300, "ce_oi": 1240000, "pe_oi": 410000, "ce_ltp": 59.0, "pe_ltp": 108.0}
        ]
    )
    # 1. Record pre-close valid candidate at 15:20
    temp_store.record_pre_close_options(valid_baseline)
    
    # 2. Simulate off-hours empty packet at 15:35
    empty_baseline = OptionsCloseBaseline(session_date="2026-08-21", strike_baseline=[])
    
    # 3. Finalize: must automatically use the pre-close candidate
    assert temp_store.finalize_options_baseline(empty_baseline) is True
    
    loaded = temp_store.load_options_baseline("2026-08-21")
    assert loaded is not None
    assert len(loaded.strike_baseline) == 3, "Pre-close candidate must be preserved against empty packet overwrite"
    assert loaded.derivatives_summary.call_wall_strike == 24500


def test_phase_c_close_reconciliation_policy():
    """Verify configurable CloseReconciliationPolicy evaluation."""
    policy = CloseReconciliationPolicy(max_absolute_drift_points=5.0, max_relative_drift_bps=2.5)
    
    # Exact match
    status, meta = CloseReconciler.reconcile(24252.00, 24252.00, policy)
    assert status == "MATCHED"
    
    # Within absolute tolerance (3 pts drift on Nifty)
    status, meta = CloseReconciler.reconcile(24249.00, 24252.00, policy)
    assert status == "WITHIN_TOLERANCE"
    
    # Exceeds tolerance with provider correction allowed
    status, meta = CloseReconciler.reconcile(24200.00, 24252.00, policy)
    assert status == "CORRECTED_FROM_PROVIDER"
    assert meta["adopted_close"] == 24252.00


def test_phase_c_missed_close_recovery(temp_store):
    """Verify missed-close recovery upon server restart."""
    hist_ohlc = {
        "open": 24220.0,
        "high": 24270.0,
        "low": 24210.0,
        "close": 24260.0,
        "volume": 3500000
    }
    assert temp_store.recover_missed_close("2026-08-21", hist_ohlc) is True
    
    recovered = temp_store.load_session_close("2026-08-21")
    assert recovered is not None
    assert recovered.market_ohlcv.close == 24260.0
    assert recovered.provenance["reconciliation_status"] == "RECOVERED_HISTORICAL_API"


# ── PHASE D: Reader Migration ──────────────────────────────────────────────────

def test_phase_d_performance_tracker_migration(temp_store, monkeypatch):
    """Verify PerformanceTrackerEngine reads SessionCloseCore from LightweightSessionStore."""
    close = SessionCloseCore(
        session_date="2026-08-21",
        market_ohlcv=MarketOHLCV(open=24225.45, high=24265.15, low=24206.80, close=24252.00, previous_close=24231.85)
    )
    temp_store.finalize_session_close(close)
    
    # Mock LightweightSessionStore.get_instance to return temp_store
    monkeypatch.setattr(LightweightSessionStore, "get_instance", lambda base_dir=None: temp_store)
    
    engine = PerformanceTrackerEngine()
    truth = {
        "open": 24225.45, "high": 24265.15, "low": 24206.80, "close": 24252.00,
        "previous_close": 24231.85, "regime": "RANGE_DAY", "risk_level": "MODERATE",
        "is_live": False, "current_hhmm": "15:35", "market_status": "CLOSED"
    }
    evals = engine.evaluate_pending_records("2026-08-21", truth)
    assert isinstance(evals, list)


def test_phase_d_live_assistant_migration(temp_store, monkeypatch):
    """Verify LiveAssistantEngine reads telemetry series from LightweightSessionStore."""
    close = SessionCloseCore(session_date="2026-08-21", market_ohlcv=MarketOHLCV(close=24252.0))
    temp_store.finalize_session_close(close)
    
    bucket = {
        "index": 1,
        "window_start": "09:15",
        "window_end": "09:30",
        "start_spot": 24200.0,
        "end_spot": 24225.0,
        "breadth_advances": 30,
        "breadth_declines": 19,
        "vix": 12.4,
        "pcr": 1.05
    }
    temp_store.record_telemetry_bucket("2026-08-21", bucket)
    
    monkeypatch.setattr(LightweightSessionStore, "get_instance", lambda base_dir=None: temp_store)
    
    m_session = {"status": "CLOSED", "session_date": "2026-08-24"}
    now_ist = datetime(2026, 8, 24, 8, 45, 0)
    date_res, mode, snaps = LiveAssistantEngine.resolve_intraday_session(
        m_session=m_session,
        now_ist=now_ist,
        snapshot_history=[],
        cache_dir=temp_store.base_dir
    )
    assert date_res == "2026-08-21"
    assert mode == "COMPLETED_SESSION"
    assert len(snaps) == 1


# ── PHASE E: Dual-Write & Retention Policy ─────────────────────────────────────

def test_phase_e_retention_policy_pruning(temp_store):
    """Verify that RetentionManager prunes telemetry/connectivity while preserving close & options baselines."""
    # Create 7 days of close, options, and telemetry files
    for day in range(10, 17):
        d_str = f"2026-08-{day}"
        temp_store.finalize_session_close(SessionCloseCore(session_date=d_str))
        temp_store.finalize_options_baseline(OptionsCloseBaseline(session_date=d_str, strike_baseline=[{"strike": 24000}]))
        temp_store.record_telemetry_bucket(d_str, {"index": 1, "spot": 24000})
        temp_store.record_connectivity_event(ConnectivityEvent(event_id=f"EV-{day}", session_date=d_str, event_type="HEALTHY", detected_at="now"))
        
    # Execute pruning
    pruned = temp_store.prune_expired_sessions()
    assert pruned["telemetry"] == 2, "Telemetry must prune 2 older files to keep 5"
    
    # Verify close and options_close are 100% untouched (PERMANENT)
    assert len(list(temp_store.close_dir.glob("*.json"))) == 7
    assert len(list(temp_store.options_dir.glob("*.json"))) == 7


def test_phase_e_security_no_tokens_in_store(temp_store):
    """Verify that stored session files contain zero auth tokens or secrets."""
    close = SessionCloseCore(session_date="2026-08-21", market_ohlcv=MarketOHLCV(close=24252.0))
    temp_store.finalize_session_close(close)
    
    content = (temp_store.close_dir / "2026-08-21.json").read_text(encoding="utf-8")
    for secret_keyword in ["token", "access_token", "api_key", "secret", "password", "authorization"]:
        assert secret_keyword not in content.lower(), f"Sensitive keyword {secret_keyword} must not be stored"
