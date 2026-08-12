# tests/test_sprint_d3_latency.py
from datetime import datetime, timezone
import pytest
from src.application.workstation_state_service import WorkstationStateService


def test_quote_freshness_and_latency_diagnostics():
    now_dt = datetime(2026, 8, 11, 10, 0, 0, tzinfo=timezone.utc)
    payload = {
        "marketContext": {
            "current_spot": 24500.0,
            "previous_close": 24550.0,
            "exchange_timestamp": "2026-08-11T09:59:59.800Z",
            "backend_receive_timestamp": "2026-08-11T09:59:59.850Z"
        },
        "technicalAnalysis": {},
        "optionContext": {},
        "macroIntelligence": {},
        "newsSentiment": {}
    }

    state = WorkstationStateService.build_from_legacy(
        payload, broker_state="CONNECTED", market_state="OPEN", now=now_dt
    )

    d = state.to_dict()
    assert "live_feed_latency_truth" in d["market_data"]
    lat = d["market_data"]["live_feed_latency_truth"]

    assert lat["source_observed_at"] == "2026-08-11T09:59:59.800Z"
    assert lat["feed_received_at"] == "2026-08-11T09:59:59.850Z"
    assert lat["source_to_feed_ms"] == 50.0
    assert lat["status"] == "HEALTHY"
    assert lat["end_to_end_age_ms"] is not None
    assert lat["end_to_end_age_ms"] >= 0.0


def test_stale_source_quote_detection():
    now_dt = datetime(2026, 8, 11, 10, 0, 0, tzinfo=timezone.utc)
    # Source quote timestamp is 10 seconds old
    payload = {
        "marketContext": {
            "current_spot": 24500.0,
            "previous_close": 24550.0,
            "exchange_timestamp": "2026-08-11T09:59:50.000Z",
            "backend_receive_timestamp": "2026-08-11T09:59:50.050Z"
        },
        "technicalAnalysis": {},
        "optionContext": {},
        "macroIntelligence": {},
        "newsSentiment": {}
    }

    state = WorkstationStateService.build_from_legacy(
        payload, broker_state="CONNECTED", market_state="OPEN", now=now_dt
    )

    lat = state.market_data["live_feed_latency_truth"]
    assert lat["status"] == "SOURCE_STALE"
    assert "stale or unavailable" in lat["explanation"]


def test_missing_source_timestamp_remains_unavailable():
    now_dt = datetime(2026, 8, 11, 10, 0, 0, tzinfo=timezone.utc)
    payload = {
        "marketContext": {
            "current_spot": 24500.0,
            "previous_close": 24550.0
        },
        "technicalAnalysis": {},
        "optionContext": {},
        "macroIntelligence": {},
        "newsSentiment": {}
    }

    state = WorkstationStateService.build_from_legacy(
        payload, broker_state="CONNECTED", market_state="OPEN", now=now_dt
    )

    lat = state.market_data["live_feed_latency_truth"]
    assert lat["source_observed_at"] == "UNAVAILABLE"
    assert lat["status"] == "SOURCE_STALE"
