import pytest
import threading
from unittest.mock import MagicMock, patch
from src.broker.services.streaming_orchestrator import StreamingOrchestrator
from src.broker.adapters.kite_ticker_adapter import KiteTickerAdapter

def test_streaming_orchestrator_single_instance_guard():
    orch = StreamingOrchestrator.get_instance()
    orch.api_key = "test_key"
    orch.access_token = "test_token"

    mock_connect = MagicMock(return_value=True)
    with patch.object(KiteTickerAdapter, "connect", mock_connect):
        # First call
        res1 = orch.connect_stream(force_reconnect=True)
        adapter1 = orch.adapter
        assert res1 is True
        assert adapter1 is not None

        # Second call without force_reconnect when already connected
        with patch.object(orch, "is_connected", return_value=True):
            res2 = orch.connect_stream(force_reconnect=False)
            assert res2 is True
            assert orch.adapter is adapter1  # Same adapter instance preserved

        # Force reconnect safely terminates old adapter and creates new single adapter
        with patch.object(adapter1, "disconnect") as mock_disc:
            res3 = orch.connect_stream(force_reconnect=True)
            mock_disc.assert_called_once()
            assert orch.adapter is not None
            assert orch.adapter is not adapter1

def test_concurrent_connect_stream():
    orch = StreamingOrchestrator.get_instance()
    orch.api_key = "test_key"
    orch.access_token = "test_token"

    results = []
    def runner():
        with patch.object(KiteTickerAdapter, "connect", return_value=True):
            res = orch.connect_stream()
            results.append(res)

    threads = [threading.Thread(target=runner) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 10
    assert all(r is True for r in results)
    assert orch.adapter is not None
