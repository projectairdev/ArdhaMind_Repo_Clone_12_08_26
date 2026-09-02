# tests/integration/test_e2e_market_pipeline_rehearsal.py
"""
End-to-End Market Pipeline Integration Rehearsal.
Simulates real live market flow through the actual production code paths:
Raw Tick -> Callback (setup_real_ticks_callback) -> Orchestrator (latest_ticks)
         -> MarketContextBuilder -> WorkstationStateService (Canonical State)
         -> Node Transport / API Serialization -> Frontend ViewModel Transformer -> Session Recorder P0
"""

import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from src.server_bridge import setup_real_ticks_callback
from src.broker.services.market_context_builder import MarketContextBuilder
from src.application.workstation_state_service import WorkstationStateService


class MockStreamingGateway:
    def __init__(self):
        self.subscribed_tokens = set()

    def subscribe(self, tokens):
        self.subscribed_tokens.update(tokens)
        return True


class RealFlowBrokerService:
    """Mock broker providing authentic live interfaces for end-to-end rehearsal."""
    def __init__(self, connected=True, stream_connected=True):
        self._connected = connected
        self._stream_connected = stream_connected
        self._gateway = MockStreamingGateway()
        
        # Real Orchestrator mock structure matching StreamingOrchestrator
        self._orchestrator = MagicMock()
        self._orchestrator.is_connected.return_value = stream_connected
        self._orchestrator._real_ticks_callback_set = False
        self._orchestrator.latest_ticks = {}
        self._orchestrator._last_tick_timestamps = {}
        self._orchestrator.get_feed_health_metrics.return_value = {
            "status": "HEALTHY",
            "latency_ms": 14.5
        }

        # Authentic default handler on orchestrator
        def _default_on_ticks(raw_ticks):
            for t in raw_ticks:
                tok = t.get("instrument_token")
                sym = "NSE:NIFTY 50" if tok == 256265 else ("NSE:INDIA VIX" if tok == 264969 else f"TOKEN:{tok}")
                self._orchestrator.latest_ticks[sym] = t
                self._orchestrator._last_tick_timestamps[tok] = t.get("timestamp") or time.time()

        self._orchestrator._on_tick_received = _default_on_ticks

        self.quote_data = {
            "NSE:NIFTY 50": {
                "last_price": 24320.00,
                "ohlc": {"open": 24175.75, "high": 24320.00, "low": 24115.00, "close": 24219.05},
                "volume": 2500000,
                "oi": 600000
            }
        }

    def is_connected(self):
        return self._connected

    def is_stream_connected(self):
        return self._stream_connected

    def _get_orchestrator(self):
        return self._orchestrator

    def get_gateway(self):
        return self._gateway

    def get_quote(self, symbols):
        return self.quote_data

    def get_instruments(self):
        return [
            {"instrument_token": 256265, "exchange_token": "256265", "tradingsymbol": "NIFTY 50", "name": "NIFTY 50", "exchange": "NSE", "segment": "INDICES"}
        ]


def transform_to_frontend_viewmodel(canonical_state: dict) -> dict:
    """Python mirror of frontend NiftyLiveWorkspace ViewModel resolution."""
    market = canonical_state.get("market_data") or canonical_state.get("marketContext") or {}
    spot = market.get("current_spot") or market.get("spot")
    previous_close = market.get("previous_close", 24219.05)
    change = round(spot - previous_close, 2) if (spot is not None and previous_close) else None
    change_pct = round((change / previous_close) * 100.0, 4) if (change is not None and previous_close) else None
    
    options = canonical_state.get("options") or canonical_state.get("optionContext") or {}
    atm_strike = options.get("atm_strike")
    if atm_strike is None and spot is not None:
        atm_strike = int(round(spot / 50.0) * 50)

    return {
        "displaySpot": float(spot) if spot is not None else None,
        "displayChange": change,
        "displayChangePct": change_pct,
        "atmStrike": atm_strike,
        "sourceType": market.get("source_type", "WEBSOCKET_STREAM"),
        "isPositive": change >= 0 if change is not None else False
    }


def test_1_e2e_successive_tick_pipeline_rehearsal(tmp_path):
    """
    Primary Integration Rehearsal:
    Injects 6 successive advancing ticks through real registered callback:
    [24320.00, 24325.40, 24331.80, 24328.15, 24342.60, 24351.10]
    Verifies that every observation travels completely from raw tick to Session Recorder.
    """
    WorkstationStateService.reset_for_testing()
    WorkstationStateService.CACHE_DIR = tmp_path
    WorkstationStateService._allow_disk_cache_in_test = True

    bs = RealFlowBrokerService(connected=True, stream_connected=True)
    setup_real_ticks_callback(bs)
    orch = bs._get_orchestrator()

    assert orch._real_ticks_callback_set is True
    assert callable(orch._on_tick_received)

    test_prices = [24320.00, 24325.40, 24331.80, 24328.15, 24342.60, 24351.10]
    previous_close = 24219.05
    session_date = "2026-08-26"

    observation_matrix = []

    for idx, price in enumerate(test_prices):
        tick_time = time.time()
        
        # 1. INPUT TICK at boundary
        raw_tick_packet = [{
            "instrument_token": 256265,
            "last_price": price,
            "volume": 1000000 + idx * 50000,
            "oi": 500000,
            "timestamp": tick_time,
            "ohlc": {
                "open": 24175.75,
                "high": max(24320.00, price),
                "low": 24115.00,
                "close": previous_close
            }
        }]

        # 2. TRIGGER REAL CALLBACK
        orch._on_tick_received(raw_tick_packet)

        # 3. VERIFY ORCHESTRATOR LATEST TICKS
        stored_tick = orch.latest_ticks.get("NSE:NIFTY 50")
        assert stored_tick is not None
        assert stored_tick["last_price"] == price
        assert orch._last_tick_timestamps[256265] == tick_time

        # 4. RUN MARKET CONTEXT BUILDER
        market_ctx = MarketContextBuilder.build(bs, orch, india_vix=11.20)
        market_ctx["session_date"] = session_date
        assert market_ctx["current_spot"] == price
        assert market_ctx["source_type"] == "WEBSOCKET_STREAM"
        assert market_ctx["spot_change"] == round(price - previous_close, 2)

        # 5. RUN CANONICAL WORKSTATION STATE BUILDER
        raw_payload = {
            "marketContext": market_ctx,
            "optionContext": {
                "atm_strike": int(round(price / 50.0) * 50),
                "pcr": 1.15,
                "max_pain": 24300,
                "atm_iv": 11.4
            },
            "newsSentiment": {"items": []},
            "macro": {},
            "nifty_previous_close": previous_close,
            "market_feed_status": {"stream_status": "CONNECTED", "health": "HEALTHY"}
        }

        canonical_state = WorkstationStateService.build_from_legacy(
            raw_payload,
            broker_state="CONNECTED",
            market_state="OPEN",
            now=datetime.fromtimestamp(tick_time, timezone.utc)
        )

        canonical_spot = (canonical_state.market_data.get("current_spot")
                          if isinstance(canonical_state.market_data, dict)
                          else getattr(canonical_state.market_data, "current_spot", None))
        assert canonical_spot == price

        # 6. SIMULATE NODE TRANSPORT & API RESPONSE
        api_workspace_spot = canonical_state.to_dict()["market_data"]["current_spot"]
        assert api_workspace_spot == price

        # 7. TRANSFORM TO FRONTEND VIEWMODEL
        vm = transform_to_frontend_viewmodel(canonical_state.to_dict())
        assert vm["displaySpot"] == price
        assert vm["displayChange"] == round(price - previous_close, 2)
        assert vm["sourceType"] == "WEBSOCKET_STREAM"

        # 8. VERIFY SESSION RECORDER
        snaps = WorkstationStateService._snapshots_history
        assert len(snaps) > 0
        latest_snap = snaps[-1]
        assert latest_snap["spot"] == price
        assert latest_snap["provenance"]["source_type"] == "WEBSOCKET_STREAM"

        observation_matrix.append({
            "step": idx + 1,
            "input": price,
            "callback": stored_tick["last_price"],
            "orch": stored_tick["last_price"],
            "builder": market_ctx["current_spot"],
            "canonical": canonical_spot,
            "api": api_workspace_spot,
            "frontend": vm["displaySpot"],
            "recorder": latest_snap["spot"],
            "change": vm["displayChange"],
            "atm": vm["atmStrike"]
        })

    # Flush session history to disk
    WorkstationStateService.flush_session_history(session_date)
    cache_file = tmp_path / f"session_history_{session_date}.json"
    assert cache_file.exists()

    with open(cache_file, "r") as f:
        disk_data = json.load(f)

    assert len(disk_data["snapshots"]) >= 6
    assert disk_data["snapshots"][-1]["spot"] == 24351.10

    # Verify no stale state survived across observations
    for row in observation_matrix:
        assert row["input"] == row["callback"] == row["orch"] == row["builder"] == row["canonical"] == row["api"] == row["frontend"] == row["recorder"]


def test_2_day_range_and_ohlc_propagation():
    """Test 2: Demonstrates that rising spot dynamically updates High while Low is preserved."""
    WorkstationStateService.reset_for_testing()
    bs = RealFlowBrokerService(connected=True, stream_connected=True)
    setup_real_ticks_callback(bs)
    orch = bs._get_orchestrator()

    open_p = 24175.75
    low_p = 24115.00
    prev_close = 24219.05

    # Step 1: Moderate high (24320.00)
    orch._on_tick_received([{
        "instrument_token": 256265,
        "last_price": 24320.00,
        "timestamp": time.time(),
        "ohlc": {"open": open_p, "high": 24320.00, "low": low_p, "close": prev_close}
    }])
    ctx1 = MarketContextBuilder.build(bs, orch, india_vix=11.20)
    assert ctx1["high"] == 24320.00
    assert ctx1["low"] == low_p

    # Step 2: Higher high (24351.10)
    orch._on_tick_received([{
        "instrument_token": 256265,
        "last_price": 24351.10,
        "timestamp": time.time(),
        "ohlc": {"open": open_p, "high": 24351.10, "low": low_p, "close": prev_close}
    }])
    ctx2 = MarketContextBuilder.build(bs, orch, india_vix=11.20)
    assert ctx2["high"] == 24351.10
    assert ctx2["low"] == low_p


def test_3_atm_strike_boundary_transition():
    """
    Test 3: Strike rounding rule around 50-point boundary:
    24324.00 -> ATM Strike 24300
    24326.00 -> ATM Strike 24350
    """
    WorkstationStateService.reset_for_testing()
    bs = RealFlowBrokerService(connected=True, stream_connected=True)
    setup_real_ticks_callback(bs)
    orch = bs._get_orchestrator()

    # 1. Below midpoint: 24324.00 -> round to 24300
    orch._on_tick_received([{
        "instrument_token": 256265,
        "last_price": 24324.00,
        "timestamp": time.time(),
        "ohlc": {"open": 24175.75, "high": 24324.00, "low": 24115.00, "close": 24219.05}
    }])
    ctx1 = MarketContextBuilder.build(bs, orch, india_vix=11.20)
    state1 = WorkstationStateService.build_from_legacy({"marketContext": ctx1}, broker_state="CONNECTED", market_state="OPEN")
    vm1 = transform_to_frontend_viewmodel(state1.to_dict())
    assert vm1["atmStrike"] == 24300

    # 2. Above midpoint: 24326.00 -> round to 24350
    orch._on_tick_received([{
        "instrument_token": 256265,
        "last_price": 24326.00,
        "timestamp": time.time(),
        "ohlc": {"open": 24175.75, "high": 24326.00, "low": 24115.00, "close": 24219.05}
    }])
    ctx2 = MarketContextBuilder.build(bs, orch, india_vix=11.20)
    state2 = WorkstationStateService.build_from_legacy({"marketContext": ctx2}, broker_state="CONNECTED", market_state="OPEN")
    vm2 = transform_to_frontend_viewmodel(state2.to_dict())
    assert vm2["atmStrike"] == 24350


def test_4_stale_positive_value_protection_exact_25_aug_guard():
    """
    Test 4: Stale Positive Value Protection (25-Aug failure class).
    Seed an old positive pre-market tick (24219.05, age > 2h).
    Send fresh live-style tick (24351.10, age = 0s).
    Expected: Fresh observation (24351.10) MUST win.
    """
    WorkstationStateService.reset_for_testing()
    bs = RealFlowBrokerService(connected=True, stream_connected=True)
    setup_real_ticks_callback(bs)
    orch = bs._get_orchestrator()

    # Seed old pre-market tick from 07:06 AM
    stale_ts = time.time() - 7200
    orch.latest_ticks["NSE:NIFTY 50"] = {
        "instrument_token": 256265,
        "last_price": 24219.05,
        "timestamp": stale_ts,
        "ohlc": {"open": 24175.75, "high": 24219.05, "low": 24115.45, "close": 24219.05}
    }
    orch._last_tick_timestamps[256265] = stale_ts

    # Send fresh live tick
    orch._on_tick_received([{
        "instrument_token": 256265,
        "last_price": 24351.10,
        "timestamp": time.time(),
        "ohlc": {"open": 24175.75, "high": 24351.10, "low": 24115.45, "close": 24219.05}
    }])

    ctx = MarketContextBuilder.build(bs, orch, india_vix=11.20)
    assert ctx["current_spot"] == 24351.10
    assert ctx["current_spot"] != 24219.05
    assert ctx["source_type"] == "WEBSOCKET_STREAM"
    assert ctx["spot_change"] == round(24351.10 - 24219.05, 2)


def test_5_sequence_and_runtime_invariants(tmp_path):
    """Test 5: Across multiple ticks, runtime_id remains stable, sequence increases monotonically."""
    WorkstationStateService.reset_for_testing()
    WorkstationStateService.CACHE_DIR = tmp_path
    WorkstationStateService._allow_disk_cache_in_test = True

    bs = RealFlowBrokerService(connected=True, stream_connected=True)
    setup_real_ticks_callback(bs)
    orch = bs._get_orchestrator()

    runtime_id = None
    last_seq = 0

    for i in range(5):
        orch._on_tick_received([{
            "instrument_token": 256265,
            "last_price": 24320.00 + i,
            "timestamp": time.time(),
            "ohlc": {"open": 24175.75, "high": 24330.00, "low": 24115.00, "close": 24219.05}
        }])
        ctx = MarketContextBuilder.build(bs, orch, india_vix=11.20)
        state = WorkstationStateService.build_from_legacy(
            {"marketContext": ctx}, broker_state="CONNECTED", market_state="OPEN"
        )
        if runtime_id is None:
            runtime_id = state.runtime_id
        else:
            assert state.runtime_id == runtime_id, "runtime_id must remain stable across ticks"

        assert state.state_sequence > last_seq, "state_sequence must increase monotonically"
        last_seq = state.state_sequence
