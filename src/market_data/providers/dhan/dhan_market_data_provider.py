from __future__ import annotations

import logging
import threading
from typing import Any, Callable, Dict, List, Optional, Sequence, Set

from src.market_data.bus.events import MarketEventType
from src.market_data.bus.event_bus import MarketEventBus
from src.market_data.interfaces.market_data_provider import IMarketDataProvider
from src.market_data.models.canonical_instrument import CanonicalInstrument
from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.providers.dhan.dhan_tick_normalizer import DhanTickNormalizer
from src.market_data.services.instrument_master_service import InstrumentMasterService

logger = logging.getLogger(__name__)


class DhanMarketDataProvider(IMarketDataProvider):
    """
    Real-time DhanHQ market data provider adapter.
    Translates raw WebSocket frames into CanonicalTicks and publishes them to the MarketEventBus.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        access_token: Optional[str] = None,
        instrument_master: Optional[InstrumentMasterService] = None,
        event_bus: Optional[MarketEventBus] = None,
        on_tick_callback: Optional[Callable[[CanonicalTick], None]] = None,
    ) -> None:
        self.client_id = client_id or ""
        self._access_token = access_token or ""
        self.instrument_master = instrument_master or InstrumentMasterService()
        self.event_bus = event_bus
        self.on_tick_callback = on_tick_callback

        self.normalizer = DhanTickNormalizer(self.instrument_master)
        self._lock = threading.RLock()
        self._connected: bool = False
        self._subscribed_instruments: Set[str] = set()

        # Connection telemetry
        self.packets_received_count: int = 0
        self.ticks_emitted_count: int = 0

    def provider_name(self) -> str:
        return "DHAN"

    def set_tick_handler(self, handler: Callable[[CanonicalTick], None]) -> None:
        """Registers a callback for incoming normalized CanonicalTicks."""
        with self._lock:
            self.on_tick_callback = handler

    def is_connected(self) -> bool:
        with self._lock:
            return self._connected

    def connect(self) -> None:
        """Establishes real-time feed transport connection."""
        with self._lock:
            if self._connected:
                return
            # Note: For production execution, socket connection to Dhan Feed API would open here.
            self._connected = True
            if self.event_bus and self.event_bus.is_running and self.event_bus.has_subscribers(MarketEventType.FEED_CONNECTED):
                self.event_bus.publish(
                    MarketEventType.FEED_CONNECTED,
                    {"provider": "DHAN", "connected": True},
                )
            logger.info("DhanMarketDataProvider connected.")

    def disconnect(self) -> None:
        """Closes real-time feed transport connection."""
        with self._lock:
            if not self._connected:
                return
            self._connected = False
            if self.event_bus and self.event_bus.is_running and self.event_bus.has_subscribers(MarketEventType.FEED_DISCONNECTED):
                self.event_bus.publish(
                    MarketEventType.FEED_DISCONNECTED,
                    {"provider": "DHAN", "connected": False},
                )
            logger.info("DhanMarketDataProvider disconnected.")

    def subscribe(self, instruments: Sequence[CanonicalInstrument]) -> None:
        """Registers instruments for real-time market data streaming."""
        with self._lock:
            for inst in instruments:
                if not isinstance(inst, CanonicalInstrument):
                    continue
                sec_id = inst.provider_ids.get("DHAN")
                if sec_id:
                    self._subscribed_instruments.add(inst.canonical_id)
            logger.info(f"DhanMarketDataProvider subscribed to {len(instruments)} instruments.")

    def unsubscribe(self, instruments: Sequence[CanonicalInstrument]) -> None:
        """Removes instruments from real-time streaming."""
        with self._lock:
            for inst in instruments:
                if isinstance(inst, CanonicalInstrument):
                    self._subscribed_instruments.discard(inst.canonical_id)

    def handle_raw_packet(self, raw_data: Any) -> Optional[CanonicalTick]:
        """
        Processes a single raw incoming binary or dictionary packet from the Dhan transport.
        Normalizes to CanonicalTick and routes to EventBus / callback.
        """
        with self._lock:
            self.packets_received_count += 1

        tick = self.normalizer.parse_packet(raw_data)
        if tick is None:
            return None

        with self._lock:
            self.ticks_emitted_count += 1

        # Dispatch
        if self.on_tick_callback:
            try:
                self.on_tick_callback(tick)
            except Exception as e:
                logger.error(f"Error in on_tick_callback: {e}")

        if self.event_bus and self.event_bus.is_running:
            self.event_bus.publish(
                MarketEventType.TICK,
                tick,
                canonical_instrument_id=tick.canonical_instrument_id,
            )

        return tick

    def stats(self) -> Dict[str, Any]:
        """Returns provider telemetry."""
        with self._lock:
            return {
                "provider": "DHAN",
                "connected": self._connected,
                "subscribed_count": len(self._subscribed_instruments),
                "packets_received": self.packets_received_count,
                "ticks_emitted": self.ticks_emitted_count,
                "malformed_packets": self.normalizer.malformed_packets_count,
                "unmapped_security_ids": self.normalizer.unmapped_security_ids_count,
            }
