from __future__ import annotations
import pytest
import time
from unittest.mock import MagicMock

from src.broker.adapters.kite_ticker_adapter import KiteTickerAdapter
from src.broker.services.streaming_service import StreamingService
from src.broker.services.subscription_manager import SubscriptionManager
from src.broker.services.stream_health_monitor import StreamHealthMonitor
from src.broker.services.streaming_orchestrator import StreamingOrchestrator
from src.broker.models.tick import TickModel
from src.broker.models.stream_health import StreamHealthReport
from tests.support.fake_kiteconnect import FakeKiteTicker


@pytest.fixture(autouse=True)
def explicit_test_ticker(monkeypatch):
    monkeypatch.setattr("src.broker.adapters.kite_ticker_adapter.KiteTicker", FakeKiteTicker)


def test_kite_ticker_adapter_lifecycle():
    """Test KiteTickerAdapter connect/disconnect and callbacks."""
    adapter = KiteTickerAdapter(api_key="mock_key", access_token="mock_token")
    assert adapter.is_connected() is False

    # Mock callbacks
    on_tick = MagicMock()
    on_status = MagicMock()
    adapter.on_tick_received = on_tick
    adapter.on_status_changed = on_status

    success = adapter.connect()
    assert success is True
    assert adapter.is_connected() is True
    on_status.assert_called_with("CONNECTED")

    # Simulate ticks callback
    adapter._on_kite_ticks(None, [{"instrument_token": 256265, "last_price": 22000.0}])
    on_tick.assert_called_once()

    # Simulate close
    adapter._on_kite_close(None, 1000, "Normal Close")
    assert adapter.is_connected() is False
    on_status.assert_called_with("DISCONNECTED")


def test_streaming_service_ingestion():
    """Test StreamingService tick parsing, symbol mapping, and routing."""
    raw_ticks = [
        {"instrument_token": 256265, "last_price": 22000.0, "volume": 150000, "ohlc": {"open": 21900.0, "high": 22050.0, "low": 21850.0, "close": 21950.0}},
        {"instrument_token": 260105, "last_price": 47500.0, "volume": 80000, "ohlc": {"open": 47400.0, "high": 47600.0, "low": 47300.0, "close": 47450.0}},
        {"instrument_token": 999999, "last_price": 105.5, "volume": 1200} # Unmapped token fallback
    ]

    ticks = StreamingService.ingest_ticks(raw_ticks)
    assert len(ticks) == 3

    assert ticks[0].symbol == "NIFTY 50"
    assert ticks[0].last_price == 22000.0
    assert ticks[0].volume == 150000
    assert ticks[0].high == 22050.0

    assert ticks[1].symbol == "NIFTY BANK"
    assert ticks[1].last_price == 47500.0

    assert ticks[2].symbol == "TOKEN_999999"
    assert ticks[2].last_price == 105.5

    # Routing
    routed = StreamingService.route_ticks_by_symbol(ticks)
    assert "NIFTY 50" in routed
    assert "NIFTY BANK" in routed
    assert "TOKEN_999999" in routed
    assert len(routed["NIFTY 50"]) == 1


def test_subscription_manager():
    """Test SubscriptionManager dynamic subscription tracking and duplicate filtering."""
    manager = SubscriptionManager()
    assert len(manager.get_active_subscriptions()) == 0

    # Mock Ticker Adapter
    mock_ticker = MagicMock()
    manager.set_ticker_adapter(mock_ticker)

    # First subscribe
    tokens = manager.subscribe(["NIFTY", "BANKNIFTY"])
    assert 256265 in tokens
    assert 260105 in tokens
    assert len(manager.get_active_subscriptions()) == 2
    mock_ticker.subscribe.assert_called_with([256265, 260105])

    # Subscribe again (duplicates should be filtered out)
    tokens2 = manager.subscribe(["NIFTY", "FINNIFTY"])
    assert 257801 in tokens2
    assert 256265 not in tokens2 # already subscribed
    assert len(manager.get_active_subscriptions()) == 3

    # Unsubscribe
    unsub_tokens = manager.unsubscribe(["NIFTY"])
    assert 256265 in unsub_tokens
    assert len(manager.get_active_subscriptions()) == 2
    mock_ticker.unsubscribe.assert_called_with([256265])


def test_stream_health_monitor():
    """Test StreamHealthMonitor metrics aggregation."""
    monitor = StreamHealthMonitor()
    assert monitor.total_messages_received == 0

    ticks = [
        TickModel(instrument_token=256265, symbol="NIFTY 50", last_price=22000.0, volume=1000, oi=0, open=21900, high=22100, low=21800, close=21900, change=0.5, timestamp=time.strftime("%Y-%m-%dT%H:%M:%S")),
        TickModel(instrument_token=260105, symbol="NIFTY BANK", last_price=47500.0, volume=2000, oi=0, open=47400, high=47600, low=47300, close=47400, change=-0.2, timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"))
    ]

    monitor.record_ticks(ticks)
    assert monitor.total_messages_received == 2

    # Verify Report structure and generation
    report = monitor.generate_report(
        connection_status="CONNECTED",
        active_subscriptions=["NIFTY 50", "NIFTY BANK"],
        fallback_active=False
    )
    assert isinstance(report, StreamHealthReport)
    assert report.connection_status == "CONNECTED"
    assert report.message_throughput == 2
    assert report.fallback_active is False
    assert "NIFTY 50" in report.active_subscriptions


def test_streaming_orchestrator_fallback_and_reconnection():
    """Test StreamingOrchestrator integration, fallback activation, and retry loop."""
    mock_gateway = MagicMock()
    orchestrator = StreamingOrchestrator(mock_gateway)
    orchestrator.broker_gateway = mock_gateway
    orchestrator.configure("MOCK_API_KEY", "access_token")

    # Connect
    success = orchestrator.connect_stream()
    assert success is True
    assert orchestrator.is_connected() is True
    assert orchestrator.is_fallback_active() is False

    # Force a close event to trigger fallback and reconnection loop (simulating open market)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("src.broker.services.market_status_service.MarketStatusService.get_market_status", lambda self: {"status": "open"})
        orchestrator._on_status_changed("DISCONNECTED")
        assert orchestrator.is_fallback_active() is True

    # Test latest quote retrieval falls back to HTTP gateway under fallback mode
    mock_gateway.get_quote.return_value = {"NIFTY 50": {"last_price": 22005.0}}
    quote = orchestrator.get_latest_quote("NIFTY 50")
    assert quote is not None
    assert quote["last_price"] == 22005.0
    mock_gateway.get_quote.assert_called_with(["NIFTY 50"])

    # Clean up
    orchestrator.disconnect_stream()
    assert orchestrator.is_fallback_active() is False
