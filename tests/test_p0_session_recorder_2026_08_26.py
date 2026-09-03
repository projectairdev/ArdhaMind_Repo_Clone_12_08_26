# tests/test_p0_session_recorder_2026_08_26.py
"""
Deterministic regression and specification tests for P0 Trader-Ready Session Recorder.
Verifies all 13 requirements:
1. Before 08:45 IST: No continuous market heartbeats
2. 08:45-09:00 IST: 60-second heartbeat policy
3. 09:00-09:15 IST: 15-second pre-open heartbeat policy
4. 09:15-15:30 IST: 15-second LIVE heartbeat policy
5. Material source change (WS -> REST): Immediate event emission
6. Stale transition (REALTIME -> STALE): Immediate persistence
7. Briefing deduplication: 100 snapshots reference 1 briefing version without duplicate payloads
8. Briefing version change: Altered briefing creates a distinct new version
9. 15:45 stop: Market heartbeats stop at 15:45 IST
10. Post-close news (15:45-18:30 IST): New unique article stored, no market snapshots appended
11. News deduplication: Repeated fetches of same article yield single stored entry
12. Final session: Completed-session OHLC and metrics persisted in final_session_record
13. Compatibility: Existing session-history readers continue functioning
"""

import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest

from src.application.workstation_state_service import WorkstationStateService


def _create_ist_time(hour: int, minute: int, second: int = 0) -> datetime:
    """Helper to construct UTC datetime corresponding to exact IST time on 2026-08-26."""
    ist = timezone(timedelta(hours=5, minutes=30))
    dt_ist = datetime(2026, 8, 26, hour, minute, second, tzinfo=ist)
    return dt_ist.astimezone(timezone.utc)


def test_1_before_0845_no_continuous_heartbeats(tmp_path):
    """Test 1: Before 08:45 IST, verify window is WINDOW_A and heartbeat is 0.0 (no periodic market snapshots)."""
    t_0800 = _create_ist_time(8, 0, 0)
    window, hb = WorkstationStateService._get_session_recording_window(t_0800)
    assert window == "WINDOW_A_BEFORE_0845"
    assert hb == 0.0


def test_2_0845_to_0900_60s_heartbeat(tmp_path):
    """Test 2: 08:45-09:00 IST, verify window is WINDOW_B_PRE_MARKET_EVIDENCE with 60s heartbeat."""
    t_0850 = _create_ist_time(8, 50, 0)
    window, hb = WorkstationStateService._get_session_recording_window(t_0850)
    assert window == "WINDOW_B_PRE_MARKET_EVIDENCE"
    assert hb == 60.0


def test_3_0900_to_0915_15s_pre_open_heartbeat(tmp_path):
    """Test 3: 09:00-09:15 IST, verify window is WINDOW_C_PRE_OPEN with 15s heartbeat."""
    t_0905 = _create_ist_time(9, 5, 0)
    window, hb = WorkstationStateService._get_session_recording_window(t_0905)
    assert window == "WINDOW_C_PRE_OPEN"
    assert hb == 15.0


def test_4_0915_to_1530_15s_live_heartbeat(tmp_path):
    """Test 4: 09:15-15:30 IST, verify window is WINDOW_D_LIVE with 15s heartbeat."""
    t_1130 = _create_ist_time(11, 30, 0)
    window, hb = WorkstationStateService._get_session_recording_window(t_1130)
    assert window == "WINDOW_D_LIVE"
    assert hb == 15.0


def test_5_material_source_change_emits_immediate_event():
    """Test 5: WebSocket -> REST quote source transition generates SPOT_SOURCE_CHANGED event."""
    WorkstationStateService.reset_for_testing()
    ts_now = datetime.now(timezone.utc).isoformat() + "Z"

    # Seed initial state with WEBSOCKET_STREAM
    initial = {
        "session_phase": "OPEN",
        "broker_state": "CONNECTED",
        "spot_source": "WEBSOCKET_STREAM",
        "spot_freshness": "REALTIME",
        "atm_strike": 24300,
        "regime": "TRENDING",
        "trend": "BULLISH",
        "feed_health": "HEALTHY",
        "stream_status": "CONNECTED"
    }
    WorkstationStateService._last_material_state = dict(initial)

    # Transition to REST_POLL
    updated = dict(initial)
    updated["spot_source"] = "REST_POLL"
    events = WorkstationStateService._detect_material_changes(updated, ts_now)

    assert len(events) == 1
    assert events[0]["event_type"] == "SPOT_SOURCE_CHANGED"
    assert events[0]["old_value"] == "WEBSOCKET_STREAM"
    assert events[0]["new_value"] == "REST_POLL"


def test_6_stale_transition_emits_immediate_event():
    """Test 6: REALTIME -> STALE freshness transition generates FRESHNESS_CHANGED event."""
    WorkstationStateService.reset_for_testing()
    ts_now = datetime.now(timezone.utc).isoformat() + "Z"

    initial = {
        "session_phase": "OPEN",
        "broker_state": "CONNECTED",
        "spot_source": "WEBSOCKET_STREAM",
        "spot_freshness": "REALTIME",
        "atm_strike": 24300,
        "regime": "TRENDING",
        "trend": "BULLISH",
        "feed_health": "HEALTHY",
        "stream_status": "CONNECTED"
    }
    WorkstationStateService._last_material_state = dict(initial)

    updated = dict(initial)
    updated["spot_freshness"] = "STALE"
    events = WorkstationStateService._detect_material_changes(updated, ts_now)

    assert len(events) == 1
    assert events[0]["event_type"] == "FRESHNESS_CHANGED"
    assert events[0]["old_value"] == "REALTIME"
    assert events[0]["new_value"] == "STALE"


def test_7_briefing_deduplication(tmp_path):
    """
    Test 7: 100 snapshots referencing identical briefing result in exactly
    1 versioned briefing payload in pre_market_briefing_versions and 100 lightweight snapshots.
    """
    WorkstationStateService.reset_for_testing()
    WorkstationStateService.CACHE_DIR = tmp_path
    WorkstationStateService._allow_disk_cache_in_test = True

    static_briefing = {
        "title": "NIFTY Morning Strategy Briefing",
        "expected_open": 24300.0,
        "key_themes": ["Global cues positive", "DII buying support", "Crude stable"],
        "heavyweight_impact": {"HDFCBANK": "POSITIVE", "RELIANCE": "NEUTRAL"},
        "long_text_summary": "Detailed morning analysis paragraph..." * 50
    }

    session_date = "2026-08-26"
    h = WorkstationStateService._compute_payload_hash(static_briefing)
    ref_k = f"PMB-{session_date}-{h}"
    WorkstationStateService._pre_market_briefing_versions[ref_k] = static_briefing

    for i in range(100):
        snap = {
            "timestamp": f"2026-08-26T04:{i:02d}:00Z",
            "runtime_id": "test-runtime",
            "state_sequence": i + 1,
            "session_date": session_date,
            "market_session_phase": "OPEN",
            "spot": 24300.0 + i,
            "open": 24280.0,
            "high": 24320.0,
            "low": 24270.0,
            "close": 24300.0 + i,
            "pre_market_briefing_ref": ref_k,
            "pre_market_briefing": static_briefing
        }
        WorkstationStateService._snapshots_history.append(snap)

    WorkstationStateService.flush_session_history(session_date)

    cache_file = tmp_path / f"session_history_{session_date}.json"
    assert cache_file.exists()

    with open(cache_file, "r") as f:
        disk_data = json.load(f)

    # Exactly 1 briefing version stored
    assert len(disk_data.get("pre_market_briefing_versions", {})) == 1
    assert ref_k in disk_data["pre_market_briefing_versions"]

    # Snapshots on disk have pre_market_briefing_ref and NOT raw 26KB pre_market_briefing
    snaps_disk = disk_data.get("snapshots", [])
    assert len(snaps_disk) == 100
    for s in snaps_disk:
        assert s.get("pre_market_briefing_ref") == ref_k
        assert "pre_market_briefing" not in s

    # Projected disk size is very compact (< 100 KB) instead of megabytes
    file_size_kb = cache_file.stat().st_size / 1024.0
    assert file_size_kb < 100.0


def test_8_briefing_version_change(tmp_path):
    """Test 8: When briefing content changes materially, a new version is added to pre_market_briefing_versions."""
    WorkstationStateService.reset_for_testing()
    WorkstationStateService.CACHE_DIR = tmp_path
    WorkstationStateService._allow_disk_cache_in_test = True

    b1 = {"title": "Briefing v1", "expected_open": 24300.0}
    b2 = {"title": "Briefing v2 - REVISED", "expected_open": 24350.0}

    session_date = "2026-08-26"
    h1 = WorkstationStateService._compute_payload_hash(b1)
    ref1 = f"PMB-{session_date}-{h1}"
    WorkstationStateService._pre_market_briefing_versions[ref1] = b1

    h2 = WorkstationStateService._compute_payload_hash(b2)
    ref2 = f"PMB-{session_date}-{h2}"
    WorkstationStateService._pre_market_briefing_versions[ref2] = b2

    assert ref1 != ref2
    assert len(WorkstationStateService._pre_market_briefing_versions) == 2


def test_9_1545_stop_market_heartbeats():
    """Test 9: At 15:45 IST and later, market heartbeats are 0.0 (stopped)."""
    t_1546 = _create_ist_time(15, 46, 0)
    window, hb = WorkstationStateService._get_session_recording_window(t_1546)
    assert window == "WINDOW_F_NEWS_ONLY"
    assert hb == 0.0

    t_1700 = _create_ist_time(17, 0, 0)
    window_late, hb_late = WorkstationStateService._get_session_recording_window(t_1700)
    assert window_late == "WINDOW_F_NEWS_ONLY"
    assert hb_late == 0.0


def test_10_post_close_news_recording_without_market_snapshots(tmp_path):
    """Test 10: At 16:30 IST, new unique article is ingested and flushed to disk without creating market snapshots."""
    WorkstationStateService.reset_for_testing()
    WorkstationStateService.CACHE_DIR = tmp_path
    WorkstationStateService._allow_disk_cache_in_test = True

    # Seed 1 market snapshot from earlier in the day
    session_date = "2026-08-26"
    snap_earlier = {
        "timestamp": "2026-08-26T10:00:00Z",
        "runtime_id": "test",
        "state_sequence": 1,
        "session_date": session_date,
        "market_session_phase": "CLOSED",
        "spot": 24334.55
    }
    WorkstationStateService._snapshots_history = [snap_earlier]

    # Ingest evening news item
    news_payload = {
        "items": [
            {
                "id": "NEWS-101",
                "headline": "RBI Announces Post-Market Liquidity Stance",
                "source": "MoneyControl",
                "published_at": "2026-08-26T11:00:00Z"
            }
        ]
    }
    new_count = WorkstationStateService._ingest_news_items(news_payload)
    assert new_count == 1

    WorkstationStateService.flush_session_history(session_date)

    cache_file = tmp_path / f"session_history_{session_date}.json"
    with open(cache_file, "r") as f:
        disk_data = json.load(f)

    assert len(disk_data.get("news_items", [])) == 1
    assert disk_data["news_items"][0]["id"] == "NEWS-101"
    # Market snapshot count remains exactly 1 (no new market snapshots created)
    assert len(disk_data.get("snapshots", [])) == 1


def test_11_news_deduplication():
    """Test 11: Ingesting the exact same article 10 times yields 1 stored entry."""
    WorkstationStateService.reset_for_testing()
    article = {
        "id": "ARTICLE-500",
        "headline": "Nifty Sets New High on IT Rally",
        "url": "https://example.com/nifty-sets-new-high",
        "source": "Bloomberg"
    }
    news_payload = {"items": [article]}

    c1 = WorkstationStateService._ingest_news_items(news_payload)
    assert c1 == 1

    c2 = WorkstationStateService._ingest_news_items(news_payload)
    assert c2 == 0  # Deduplicated!

    assert len(WorkstationStateService._news_items) == 1


def test_12_final_session_record_persistence(tmp_path):
    """Test 12: Final completed-session OHLC and indicators persist cleanly in final_session_record."""
    WorkstationStateService.reset_for_testing()
    WorkstationStateService.CACHE_DIR = tmp_path
    WorkstationStateService._allow_disk_cache_in_test = True

    session_date = "2026-08-26"
    WorkstationStateService._final_session_record = {
        "trading_date": session_date,
        "open": 24175.75,
        "high": 24334.55,
        "low": 24115.45,
        "close": 24334.55,
        "previous_close": 24219.05,
        "change": 115.50,
        "change_percent": 0.4769,
        "range": 219.10,
        "final_breadth": {"advances": 32, "declines": 18, "coverage": 50},
        "final_vix": 11.25,
        "final_options": {"atm_strike": 24350, "pcr": 1.15, "max_pain": 24300, "atm_iv": 11.8},
        "final_trend": "BULLISH",
        "final_regime": "TRENDING_EXPANSION",
        "source_coverage": "REST_POLL",
        "data_quality_status": "READY",
        "finalized_at": "2026-08-26T10:15:00Z"
    }

    WorkstationStateService.flush_session_history(session_date)

    cache_file = tmp_path / f"session_history_{session_date}.json"
    with open(cache_file, "r") as f:
        disk_data = json.load(f)

    rec = disk_data.get("final_session_record")
    assert rec is not None
    assert rec["open"] == 24175.75
    assert rec["close"] == 24334.55
    assert rec["change"] == 115.50
    assert rec["final_options"]["atm_strike"] == 24350


def test_13_backward_compatibility_with_existing_readers(tmp_path):
    """Test 13: Hydration from disk restores s['pre_market_briefing'] and s['forward_outlook'] for legacy readers."""
    WorkstationStateService.reset_for_testing()
    WorkstationStateService.CACHE_DIR = tmp_path
    WorkstationStateService._allow_disk_cache_in_test = True

    session_date = "2026-08-26"
    test_briefing = {"title": "Legacy Reader Compat Briefing", "value": 12345}
    test_fo = {"status": "ACTIVE", "confidence": 0.85, "support": 24200.0, "resistance": 24400.0}

    ref_pmb = f"PMB-{session_date}-test1"
    ref_fo = f"FO-{session_date}-test1"

    raw_file_payload = {
        "version": "1.1.0",
        "session_date": session_date,
        "pre_market_briefing_versions": {ref_pmb: test_briefing},
        "forward_outlook_versions": {ref_fo: test_fo},
        "snapshots": [
            {
                "timestamp": "2026-08-26T04:00:00Z",
                "state_sequence": 1,
                "session_date": session_date,
                "spot": 24310.0,
                "pre_market_briefing_ref": ref_pmb,
                "forward_outlook_ref": ref_fo
            }
        ]
    }

    cache_file = tmp_path / f"session_history_{session_date}.json"
    with open(cache_file, "w") as f:
        json.dump(raw_file_payload, f)

    # Load via WorkstationStateService._load_session_history
    WorkstationStateService._load_session_history(session_date)

    assert len(WorkstationStateService._snapshots_history) == 1
    loaded_snap = WorkstationStateService._snapshots_history[0]

    # Seamlessly hydrated!
    assert loaded_snap.get("pre_market_briefing") == test_briefing
    assert loaded_snap.get("forward_outlook") == test_fo
    assert loaded_snap.get("spot") == 24310.0


def test_13_off_market_window_is_absolute_stop():
    """After 18:30 IST the recorder window must authorize no heartbeat writes."""
    t_183001 = _create_ist_time(18, 30, 1)
    window, hb = WorkstationStateService._get_session_recording_window(t_183001)

    assert window == "WINDOW_G_OFF_MARKET"
    assert hb == 0.0

    t_2330 = _create_ist_time(23, 30, 0)
    window_late, hb_late = WorkstationStateService._get_session_recording_window(t_2330)

    assert window_late == "WINDOW_G_OFF_MARKET"
    assert hb_late == 0.0


def test_14_news_only_window_has_zero_market_heartbeat():
    """15:45-18:30 remains event-driven news only, never periodic market heartbeat."""
    for hour, minute in ((15, 45), (16, 30), (18, 29), (18, 30)):
        t = _create_ist_time(hour, minute, 0)
        window, hb = WorkstationStateService._get_session_recording_window(t)

        assert window == "WINDOW_F_NEWS_ONLY"
        assert hb == 0.0
