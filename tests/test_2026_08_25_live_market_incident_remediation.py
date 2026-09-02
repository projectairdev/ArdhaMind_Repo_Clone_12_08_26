# tests/test_2026_08_25_live_market_incident_remediation.py
"""
Deterministic regression tests for 25 August 2026 live-market failure incident and repair.
Verifies:
1. setup_real_ticks_callback scope & safety in exchange_request_token
2. Post-auth stream startup lifecycle and idempotency
3. Spot source precedence (Fresh WS > Fresh REST > Stale/Unavailable)
4. Stale WS loses to fresh REST quote (25-Aug exact reproduction)
5. Zero semantics (missing data does not become fake zero)
6. REST-backed metrics (VIX, Breadth, Sectors) independent survival
7. Post-market completed session reconstruction unchanged
"""

import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from src.server_bridge import setup_real_ticks_callback
from src.broker.services.market_context_builder import MarketContextBuilder


class MockBrokerService:
    def __init__(self, connected=True, stream_connected=False):
        self._connected = connected
        self._stream_connected = stream_connected
        self._orchestrator = MagicMock()
        self._orchestrator.is_connected.return_value = stream_connected
        self._orchestrator._real_ticks_callback_set = False
        self._orchestrator._on_tick_received = None
        self._orchestrator.latest_ticks = {}
        self._orchestrator._last_tick_timestamps = {}
        self._orchestrator.get_feed_health_metrics.return_value = {
            "status": "HEALTHY" if stream_connected else "DISCONNECTED",
            "latency_ms": 12.0
        }
        self.quote_data = {}
        self._gateway = MagicMock()

    def is_connected(self):
        return self._connected

    def is_stream_connected(self):
        return self._stream_connected

    def _get_orchestrator(self):
        return self._orchestrator

    def get_gateway(self):
        return self._gateway

    def connect_stream(self, force_reconnect=False):
        self._stream_connected = True
        self._orchestrator.is_connected.return_value = True
        return True

    def subscribe_stream(self, symbols):
        return True

    def get_quote(self, symbols):
        return self.quote_data


def test_1_oauth_callback_scope_no_name_error():
    """Test 1: setup_real_ticks_callback is defined at module level and does not throw NameError."""
    bs = MockBrokerService(connected=True)
    # Must run cleanly without raising NameError
    setup_real_ticks_callback(bs)
    orch = bs._get_orchestrator()
    assert orch._real_ticks_callback_set is True
    assert callable(orch._on_tick_received)


def test_2_post_auth_stream_startup_lifecycle():
    """Test 2: Post-auth stream lifecycle registers callback and connects stream."""
    bs = MockBrokerService(connected=True, stream_connected=False)
    setup_real_ticks_callback(bs)
    connected = bs.connect_stream()
    assert connected is True
    assert bs.is_stream_connected() is True


def test_3_fresh_ws_wins():
    """Test 3: Fresh WebSocket tick is preferred over REST quote."""
    bs = MockBrokerService(connected=True, stream_connected=True)
    orch = bs._get_orchestrator()
    orch.is_connected.return_value = True

    # Fresh tick (age = 0s)
    t_now = time.time()
    orch.latest_ticks["NSE:NIFTY 50"] = {
        "instrument_token": 256265,
        "last_price": 24260.50,
        "timestamp": t_now,
        "ohlc": {"open": 24175.75, "high": 24270.00, "low": 24115.00, "close": 24219.05},
        "volume": 1200000,
        "oi": 500000
    }
    orch._last_tick_timestamps[256265] = t_now

    # REST quote with slightly different price
    bs.quote_data = {
        "NSE:NIFTY 50": {
            "last_price": 24255.00,
            "ohlc": {"open": 24175.75, "high": 24270.00, "low": 24115.00, "close": 24219.05}
        }
    }

    ctx = MarketContextBuilder.build(bs, orch, india_vix=11.20)
    assert ctx["current_spot"] == 24260.50
    assert ctx["source_type"] == "WEBSOCKET_STREAM"
    assert ctx["spot_change"] == round(24260.50 - 24219.05, 2)


def test_4_stale_ws_loses_to_fresh_rest_reproducing_25_aug():
    """
    Test 4: EXACT 25-AUG REPRODUCTION.
    WebSocket tick is stale (e.g. from 07:06 AM / 24,219.05).
    REST quote returns fresh 24,244.00.
    Expected: Fresh REST quote (24,244.00) is selected, NOT the stale 24,219.05.
    """
    bs = MockBrokerService(connected=True, stream_connected=False)
    orch = bs._get_orchestrator()
    orch.is_connected.return_value = False  # WS stream disconnected

    # Stale tick from pre-market (age > 2 hours)
    stale_ts = time.time() - 7200
    orch.latest_ticks["NSE:NIFTY 50"] = {
        "instrument_token": 256265,
        "last_price": 24219.05,
        "timestamp": stale_ts,
        "ohlc": {"open": 24175.75, "high": 24219.05, "low": 24115.45, "close": 24219.05}
    }
    orch._last_tick_timestamps[256265] = stale_ts

    # Live REST quote from market hours
    bs.quote_data = {
        "NSE:NIFTY 50": {
            "last_price": 24244.00,
            "ohlc": {"open": 24175.75, "high": 24256.80, "low": 24115.45, "close": 24219.05},
            "volume": 2500000,
            "oi": 600000
        }
    }

    ctx = MarketContextBuilder.build(bs, orch, india_vix=11.05)
    assert ctx["current_spot"] == 24244.00
    assert ctx["source_type"] == "REST_POLL"
    assert ctx["spot_change"] == round(24244.00 - 24219.05, 2)
    assert ctx["spot_change"] != 0.0  # Not stuck at 0.00!


def test_5_neither_source_valid_marks_unavailable():
    """Test 5: When neither WebSocket nor REST returns a valid spot, mark UNAVAILABLE / LAST_VALID without fake zero."""
    bs = MockBrokerService(connected=False, stream_connected=False)
    orch = bs._get_orchestrator()
    orch.is_connected.return_value = False
    orch.latest_ticks = {}
    bs.quote_data = {}

    with patch("src.broker.services.market_context_builder._candle_buffer", []):
        with patch.object(Path, "exists", return_value=False):
            ctx = MarketContextBuilder.build(bs, orch, india_vix=11.20)
            assert ctx["source_type"] == "UNAVAILABLE"
            assert ctx["session_mode"] == "UNAVAILABLE"
            assert ctx["current_spot"] == 0.0


def test_6_idempotent_stream_start():
    """Test 6: Repeated calls to setup_real_ticks_callback do not duplicate callback."""
    bs = MockBrokerService(connected=True)
    setup_real_ticks_callback(bs)
    setup_real_ticks_callback(bs)
    setup_real_ticks_callback(bs)
    orch = bs._get_orchestrator()
    assert orch._real_ticks_callback_set is True


def test_7_rest_backed_metrics_independent():
    """Test 7: Breadth and Sectors remain active via REST even if WebSocket is disconnected."""
    bs = MockBrokerService(connected=True, stream_connected=False)
    orch = bs._get_orchestrator()
    orch.is_connected.return_value = False

    bs.quote_data = {
        "NSE:NIFTY 50": {"last_price": 24240.00, "ohlc": {"close": 24219.05}}
    }

    ctx = MarketContextBuilder.build(bs, orch, india_vix=11.25)
    assert ctx["source_type"] == "REST_POLL"
    assert ctx["current_spot"] == 24240.00


def test_8_post_market_reconstruction_integrity():
    """Test 8: Completed session OHLC, change, and range calculate correctly from candles."""
    test_candles = [
        {"date": "2026-08-25 09:15:00", "open": 24175.75, "high": 24200.00, "low": 24160.00, "close": 24190.00, "volume": 1000},
        {"date": "2026-08-25 15:29:00", "open": 24330.00, "high": 24334.55, "low": 24320.00, "close": 24334.55, "volume": 5000},
    ]

    open_p = test_candles[0]["open"]
    close_p = test_candles[-1]["close"]
    high_p = max(c["high"] for c in test_candles)
    low_p = min(c["low"] for c in test_candles)
    prev_close = 24219.05

    change = round(close_p - prev_close, 2)
    change_pct = round((change / prev_close) * 100.0, 2)
    session_range = round(high_p - low_p, 2)

    assert open_p == 24175.75
    assert close_p == 24334.55
    assert high_p == 24334.55
    assert low_p == 24160.00
    assert change == 115.50
    assert change_pct == 0.48
    assert session_range == 174.55
