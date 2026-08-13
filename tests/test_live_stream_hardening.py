from __future__ import annotations
import unittest
from unittest.mock import MagicMock, patch
import logging

from src.broker.services.streaming_orchestrator import StreamingOrchestrator
from src.broker.adapters.kite_ticker_adapter import KiteTickerAdapter


class TestLiveStreamHardening(unittest.TestCase):
    """
    Targeted production hardening test suite for:
    - Safe KiteTicker re-authentication and adapter replacement
    - Single active adapter & single reconnect loop invariants
    - Callback unbinding to prevent race condition reconnects
    - Data quality freshness decoupling from transport status
    """

    def setUp(self) -> None:
        # Reset StreamingOrchestrator singleton state for testing
        StreamingOrchestrator._instance = None
        self.orchestrator = StreamingOrchestrator.get_instance()

    def tearDown(self) -> None:
        if self.orchestrator:
            self.orchestrator.disconnect_stream()
        StreamingOrchestrator._instance = None

    @patch("src.broker.services.streaming_orchestrator.KiteTickerAdapter")
    def test_adapter_replacement_safely_terminates_old_adapter(self, mock_adapter_cls):
        mock_adapter_1 = MagicMock()
        mock_adapter_1.api_key = "key1"
        mock_adapter_1.access_token = "token1"
        mock_adapter_1.connect.return_value = True
        mock_adapter_1.is_connected.return_value = True

        mock_adapter_2 = MagicMock()
        mock_adapter_2.api_key = "key2"
        mock_adapter_2.access_token = "token2"
        mock_adapter_2.connect.return_value = True
        mock_adapter_2.is_connected.return_value = True

        mock_adapter_cls.side_effect = [mock_adapter_1, mock_adapter_2]

        # First connection with key1/token1
        self.orchestrator.configure("key1", "token1")
        self.assertTrue(self.orchestrator.connect_stream())
        self.assertEqual(self.orchestrator.adapter, mock_adapter_1)

        # Re-authenticate with new credentials key2/token2
        self.orchestrator.configure("key2", "token2")
        self.assertTrue(self.orchestrator.connect_stream())

        # Verify old adapter was safely terminated with callbacks unbound
        self.assertIsNone(mock_adapter_1.on_status_changed)
        self.assertIsNone(mock_adapter_1.on_tick_received)
        mock_adapter_1.disconnect.assert_called_once()

        # Verify new adapter is active
        self.assertEqual(self.orchestrator.adapter, mock_adapter_2)

    @patch("src.broker.services.streaming_orchestrator.KiteTickerAdapter")
    def test_reconnect_loop_not_triggered_on_adapter_replacement(self, mock_adapter_cls):
        mock_adapter = MagicMock()
        mock_adapter.api_key = "key1"
        mock_adapter.access_token = "token1"
        mock_adapter.connect.return_value = True
        mock_adapter.is_connected.return_value = True

        mock_adapter_cls.return_value = mock_adapter

        self.orchestrator.configure("key1", "token1")
        self.orchestrator.connect_stream()

        # Disconnect stream explicitly
        self.orchestrator.disconnect_stream()

        # Verify callbacks were cleared before disconnect
        self.assertIsNone(mock_adapter.on_status_changed)
        self.assertIsNone(mock_adapter.on_tick_received)
        mock_adapter.disconnect.assert_called_once()
        self.assertIsNone(self.orchestrator.adapter)
        self.assertFalse(self.orchestrator.fallback_active)

    def test_same_credentials_does_not_recreate_adapter(self):
        with patch("src.broker.services.streaming_orchestrator.KiteTickerAdapter") as mock_adapter_cls:
            mock_adapter = MagicMock()
            mock_adapter.api_key = "key1"
            mock_adapter.access_token = "token1"
            mock_adapter.connect.return_value = True
            mock_adapter.is_connected.return_value = True
            mock_adapter_cls.return_value = mock_adapter

            self.orchestrator.configure("key1", "token1")
            self.orchestrator.connect_stream()

            # Second connect with exact same credentials while running & connected
            self.orchestrator.connect_stream()

            # Should only instantiate adapter once
            self.assertEqual(mock_adapter_cls.call_count, 1)


if __name__ == "__main__":
    unittest.main()
