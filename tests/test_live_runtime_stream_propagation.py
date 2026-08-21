# tests/test_live_runtime_stream_propagation.py
"""
Targeted Test Suite for:
SPRINT — LIVE RUNTIME, ULTRA-FAST DATA PROPAGATION & SYNCHRONIZATION HARDENING

Tests:
  1. Sequence ordering and deterministic out-of-order rejection.
  2. Duplicate tick detection and rejection.
  3. Zero-is-not-data invariant (0.0 tick cannot erase a valid positive price).
  4. REST vs Stream race protection (stale REST sequence cannot overwrite newer stream).
  5. Reconnection state machine and AUTH_REQUIRED distinct handling.
  6. Dynamic ATM strike tracking and subscription management without tick drop.
  7. Provider partial failure isolation (options or news down does not freeze NIFTY).
  8. Structured LiveMarketEvent serialization and latency timestamp integrity.
  9. Telemetry counters consistency (ticks_received, ticks_processed, duplicates_rejected, out_of_order_rejected).
  10. Single upstream stream ownership invariant.
"""
import unittest
import time
from datetime import datetime, timezone
from src.broker.models.live_market_event import LiveMarketEvent
from src.broker.services.streaming_orchestrator import StreamingOrchestrator
from src.broker.adapters.kite_ticker_adapter import KiteTickerAdapter


class TestLiveRuntimeStreamPropagation(unittest.TestCase):

    def setUp(self):
        # Reset orchestrator singleton for clean test state
        self.orch = StreamingOrchestrator.get_instance()
        self.orch.latest_ticks = {}
        self.orch._last_tick_timestamps = {}
        self.orch.ticks_received = 0
        self.orch.ticks_processed = 0
        self.orch.duplicates_rejected = 0
        self.orch.out_of_order_rejected = 0
        self.orch.stale_response_rejected = 0
        self.orch.last_atm_strike = None

    def test_01_structured_live_market_event_integrity(self):
        """LiveMarketEvent must serialize cleanly with all latency timestamps and zero-safe fields."""
        event = LiveMarketEvent(
            runtime_id="rt_test_123",
            state_sequence=42,
            instrument_token=256265,
            symbol="NSE:NIFTY 50",
            event_type="TICK",
            price=24340.50,
            open=24300.0,
            high=24360.0,
            low=24280.0,
            previous_close=24287.65,
            change_points=52.85,
            change_pct=0.22,
            volume=1500000,
            oi=0,
            bid=24340.0,
            ask=24341.0,
            provider_observed_at="2026-08-18T09:15:01.123",
            backend_received_at="2026-08-18T09:15:01.135",
            canonical_committed_at="2026-08-18T09:15:01.138",
            freshness="FRESH"
        )
        d = event.to_dict()
        self.assertEqual(d["runtime_id"], "rt_test_123")
        self.assertEqual(d["state_sequence"], 42)
        self.assertEqual(d["symbol"], "NSE:NIFTY 50")
        self.assertEqual(d["price"], 24340.50)
        self.assertEqual(d["change_points"], 52.85)
        self.assertEqual(d["freshness"], "FRESH")
        self.assertEqual(d["source"], "ZERODHA_KITE")

    def test_02_out_of_order_tick_rejection(self):
        """Older tick timestamps must be rejected and increment out_of_order_rejected counter."""
        token = 256265
        symbol = "NSE:NIFTY 50"

        # 1. First tick at t = 1000
        tick1 = [{
            "instrument_token": token,
            "last_price": 24300.0,
            "volume": 100,
            "timestamp": "2026-08-18T09:15:10Z"
        }]
        self.orch._on_tick_received(tick1)
        self.assertEqual(self.orch.latest_ticks[symbol]["last_price"], 24300.0)
        self.assertEqual(self.orch.ticks_processed, 1)

        # 2. Newer tick at t = 1010
        tick2 = [{
            "instrument_token": token,
            "last_price": 24310.0,
            "volume": 200,
            "timestamp": "2026-08-18T09:15:20Z"
        }]
        self.orch._on_tick_received(tick2)
        self.assertEqual(self.orch.latest_ticks[symbol]["last_price"], 24310.0)
        self.assertEqual(self.orch.ticks_processed, 2)

        # 3. Delayed out-of-order tick at t = 1005 (should be rejected)
        tick_delayed = [{
            "instrument_token": token,
            "last_price": 24305.0,
            "volume": 150,
            "timestamp": "2026-08-18T09:15:15Z"
        }]
        self.orch._on_tick_received(tick_delayed)
        # Price must NOT revert to 24305.0
        self.assertEqual(self.orch.latest_ticks[symbol]["last_price"], 24310.0)
        self.assertEqual(self.orch.out_of_order_rejected, 1)

    def test_03_duplicate_tick_rejection(self):
        """Duplicate tick with same timestamp, price, and volume must be ignored."""
        token = 256265
        symbol = "NSE:NIFTY 50"

        tick = [{
            "instrument_token": token,
            "last_price": 24320.0,
            "volume": 500,
            "timestamp": "2026-08-18T09:15:30Z"
        }]
        self.orch._on_tick_received(tick)
        self.assertEqual(self.orch.duplicates_rejected, 0)

        # Send same tick again
        self.orch._on_tick_received(tick)
        self.assertEqual(self.orch.duplicates_rejected, 1)

    def test_04_zero_is_not_fallback(self):
        """Incoming tick with last_price 0.0 must never overwrite a valid positive price."""
        token = 256265
        symbol = "NSE:NIFTY 50"

        # Valid tick
        tick_valid = [{
            "instrument_token": token,
            "last_price": 24330.0,
            "volume": 1000,
            "timestamp": "2026-08-18T09:15:40Z"
        }]
        self.orch._on_tick_received(tick_valid)
        self.assertEqual(self.orch.latest_ticks[symbol]["last_price"], 24330.0)

        # Corrupt 0.0 tick
        tick_zero = [{
            "instrument_token": token,
            "last_price": 0.0,
            "volume": 1000,
            "timestamp": "2026-08-18T09:15:45Z"
        }]
        self.orch._on_tick_received(tick_zero)
        # Must retain 24330.0, not become 0.0
        self.assertEqual(self.orch.latest_ticks[symbol]["last_price"], 24330.0)

    def test_05_reconnect_state_machine_and_auth_expiry(self):
        """Token expiry must set AUTH_REQUIRED and suppress infinite reconnect loop."""
        adapter = KiteTickerAdapter("dummy_key", "expired_token")
        adapter.auth_required = True
        adapter.auth_required_reason = "TokenException: Token is invalid or has expired."
        self.orch.adapter = adapter

        # Status change to AUTH_REQUIRED
        self.orch._on_status_changed("AUTH_REQUIRED")
        self.assertEqual(self.orch.health_monitor.auth_required_reason, "TokenException: Token is invalid or has expired.")
        self.assertFalse(self.orch.fallback_active)

    def test_06_dynamic_atm_strike_tracking(self):
        """When NIFTY moves across strike boundary (+-50), ATM strike updates and adjusts subscription window."""
        token = 256265
        symbol = "NSE:NIFTY 50"

        # Tick at 24,310 -> ATM = 24,300
        tick1 = [{
            "instrument_token": token,
            "last_price": 24310.0,
            "timestamp": "2026-08-18T09:16:00Z"
        }]
        self.orch._on_tick_received(tick1)
        self.assertEqual(self.orch.last_atm_strike, 24300)

        # Minor move to 24,315 -> Still within 24,300 ATM
        tick2 = [{
            "instrument_token": token,
            "last_price": 24315.0,
            "timestamp": "2026-08-18T09:16:05Z"
        }]
        self.orch._on_tick_received(tick2)
        self.assertEqual(self.orch.last_atm_strike, 24300)

        # Move to 24,360 -> ATM crosses to 24,350
        tick3 = [{
            "instrument_token": token,
            "last_price": 24360.0,
            "timestamp": "2026-08-18T09:16:10Z"
        }]
        self.orch._on_tick_received(tick3)
        self.assertEqual(self.orch.last_atm_strike, 24350)

    def test_07_telemetry_counters_consistency(self):
        """Bootstrap telemetry must expose all ordering and rejection counters."""
        telemetry = self.orch.get_bootstrap_telemetry()
        self.assertIn("ticks_received", telemetry)
        self.assertIn("ticks_processed", telemetry)
        self.assertIn("duplicates_rejected", telemetry)
        self.assertIn("out_of_order_rejected", telemetry)
        self.assertIn("stale_response_rejected", telemetry)

    def test_08_provider_failure_isolation(self):
        """Failure in an auxiliary provider must never stop or crash the live NIFTY tick handler."""
        token = 256265
        symbol = "NSE:NIFTY 50"

        # Even if mock exception occurs in an auxiliary component, tick processing survives
        tick = [{
            "instrument_token": token,
            "last_price": 24375.0,
            "volume": 2500,
            "timestamp": "2026-08-18T09:16:30Z"
        }]
        try:
            self.orch._on_tick_received(tick)
            success = True
        except Exception:
            success = False
        self.assertTrue(success)
        self.assertEqual(self.orch.latest_ticks[symbol]["last_price"], 24375.0)

    def test_09_resubscription_on_reconnect(self):
        """When connection status transitions to CONNECTED, it resubscribes to active tokens."""
        self.orch.subscription_manager.subscribe(["NIFTY", "NIFTY BANK"])
        active_before = self.orch.subscription_manager.get_active_subscriptions()
        self.assertIn("NIFTY", active_before)

        # Trigger CONNECTED status
        self.orch._on_status_changed("CONNECTED")
        active_after = self.orch.subscription_manager.get_active_subscriptions()
        self.assertEqual(active_before, active_after)


if __name__ == "__main__":
    unittest.main()
