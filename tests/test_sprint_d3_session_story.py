from datetime import datetime, timezone
from pathlib import Path
import pytest
from src.application.workstation_state_service import WorkstationStateService
from src.models.canonical_workstation_state import CanonicalWorkstationState, FORBIDDEN_CANONICAL_KEYS


def setup_function():
    WorkstationStateService._snapshots_history = []
    WorkstationStateService._live_event_stream = []
    WorkstationStateService._last_loaded_session_date = None
    cache_file = Path("data/cache/session_history_2026-08-11.json")
    if cache_file.exists():
        cache_file.unlink()


def get_base_legacy_payload():
    return {
        "marketContext": {
            "current_spot": 24533.85,
            "previous_close": 24583.80,
            "candles": [],
            "exchange_timestamp": "2026-08-11T09:15:23Z",
            "backend_receive_timestamp": "2026-08-11T09:15:23.050Z"
        },
        "technicalAnalysis": {
            "vwap": 24510.0,
            "ema_20": 24520.0,
            "ema_50": 24540.0,
            "trend_direction": "BEARISH"
        },
        "optionContext": {
            "pcr": 1.04,
            "max_pain": 24550.0,
            "atm_strike": 24500.0,
            "atm_iv": 12.25,
            "provider_timestamp": "2026-08-11T09:17:47Z"
        },
        "macroIntelligence": {
            "india_vix": {"status": "AVAILABLE", "value": 12.25},
            "quotes": {}
        },
        "newsSentiment": {
            "status": "ready",
            "items": [
                {
                    "id": "news-101",
                    "headline": "Crude Oil Fluctuation Impact",
                    "published_at": "2026-08-11T09:20:00Z",
                    "nifty_relevance_score": 75,
                    "canonical_event_category": "INDIA_MACRO"
                }
            ]
        }
    }


def test_session_story_structure_and_read_only():
    payload = get_base_legacy_payload()
    state = WorkstationStateService.build_from_legacy(
        payload, broker_state="CONNECTED", market_state="OPEN"
    )

    d = state.to_dict()
    assert "session_story" in d
    story = d["session_story"]
    assert story is not None
    assert story["session_status"] == "TODAY_SO_FAR"
    assert "session_summary" in story
    assert "timeline" in story
    assert "major_turning_points" in story
    assert "session_phases" in story
    assert "session_verdict" in story
    assert "data_quality" in story

    # Verify read-only contract
    for forbidden in FORBIDDEN_CANONICAL_KEYS:
        assert forbidden not in str(story).lower()


def test_pre_market_and_market_open_timeline_events():
    payload = get_base_legacy_payload()
    now_dt = datetime(2026, 8, 11, 9, 15, 23, tzinfo=timezone.utc)
    state = WorkstationStateService.build_from_legacy(
        payload, broker_state="CONNECTED", market_state="OPEN", now=now_dt
    )

    story = state.session_story
    assert story is not None
    timeline = story["timeline"]
    assert len(timeline) > 0

    pre_mkt = next((t for t in timeline if t["phase"] == "PRE_MARKET"), None)
    assert pre_mkt is not None
    assert pre_mkt["event_type"] == "PRE_MARKET_CONTEXT"

    mkt_open = next((t for t in timeline if t["phase"] == "MARKET_OPEN"), None)
    assert mkt_open is not None
    assert mkt_open["event_type"] == "MARKET_OPEN"
    assert mkt_open["market_snapshot"]["nifty"] == 24533.85


def test_telemetry_gap_timeline_event():
    # Build two snapshots separated by > 120s
    t1 = datetime(2026, 8, 11, 9, 34, 47, tzinfo=timezone.utc)
    p1 = get_base_legacy_payload()
    p1["marketContext"]["current_spot"] = 24488.70
    p1["marketContext"]["exchange_timestamp"] = "2026-08-11T09:34:47Z"
    WorkstationStateService.build_from_legacy(p1, broker_state="CONNECTED", market_state="OPEN", now=t1)

    t2 = datetime(2026, 8, 11, 12, 12, 11, tzinfo=timezone.utc)
    p2 = get_base_legacy_payload()
    p2["marketContext"]["current_spot"] = 24488.70
    p2["marketContext"]["exchange_timestamp"] = "2026-08-11T12:12:11Z"
    state2 = WorkstationStateService.build_from_legacy(p2, broker_state="CONNECTED", market_state="OPEN", now=t2)

    story = state2.session_story
    assert story is not None
    gap_evt = next((t for t in story["timeline"] if t["phase"] == "TELEMETRY_GAP"), None)
    assert gap_evt is not None
    assert gap_evt["event_type"] == "TELEMETRY_GAP"
    assert "OBSERVATION GAP" in gap_evt["headline"]
    assert gap_evt["data_quality"] == "DEGRADED"


def test_news_attribution_conservative_contract():
    payload = get_base_legacy_payload()
    now_dt = datetime(2026, 8, 11, 9, 30, 0, tzinfo=timezone.utc)
    state = WorkstationStateService.build_from_legacy(
        payload, broker_state="CONNECTED", market_state="OPEN", now=now_dt
    )

    story = state.session_story
    assert story is not None
    m930 = next((t for t in story["timeline"] if t["timestamp"] == "09:30"), None)
    assert m930 is not None
    news_ctx = m930["news_context"]
    assert len(news_ctx) > 0
    # Provenance note: temporal proximity alone is never CONFIRMED_DRIVER
    for n in news_ctx:
        assert n.get("attribution") != "CONFIRMED_DRIVER"
        if n.get("attribution") == "POSSIBLE_CATALYST":
            assert "Temporal proximity alone does not establish causality" in n["attribution_note"]


def test_live_vs_closed_session_semantics():
    p1 = get_base_legacy_payload()
    live_state = WorkstationStateService.build_from_legacy(p1, broker_state="CONNECTED", market_state="OPEN")
    assert live_state.session_story["session_status"] == "TODAY_SO_FAR"

    p2 = get_base_legacy_payload()
    closed_state = WorkstationStateService.build_from_legacy(p2, broker_state="CONNECTED", market_state="CLOSED")
    assert closed_state.session_story["session_status"] == "TODAYS_SESSION_REVIEW"
