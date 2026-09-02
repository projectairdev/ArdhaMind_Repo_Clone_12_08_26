from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from enum import Enum
import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Set

from src.market_data.bus.events import MarketEvent, MarketEventType
from src.market_data.bus.event_bus import MarketEventBus
from src.market_data.interfaces.historical_data_provider import IHistoricalDataProvider
from src.market_data.interfaces.market_data_provider import IMarketDataProvider
from src.market_data.interfaces.option_chain_provider import IOptionChainProvider
from src.market_data.models.canonical_candle import CanonicalCandle
from src.market_data.models.canonical_instrument import CanonicalInstrument
from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.models.quality_enums import CandleQuality, Timeframe
from src.market_data.services.candle_engine import CanonicalCandleEngine
from src.market_data.services.feed_health_engine import FeedHealthEngine, FeedHealthStatus
from src.market_data.services.historical_bootstrap_service import HistoricalBootstrapService
from src.market_data.services.instrument_master_service import InstrumentMasterService
from src.market_data.services.reconciliation_service import ReconciliationService
from src.market_data.state.live_market_state import LiveMarketState

logger = logging.getLogger(__name__)


class OrchestratorLifecycleState(str, Enum):
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    RECOVERING = "RECOVERING"
    DEGRADED = "DEGRADED"
    STOPPED = "STOPPED"


@dataclass
class SubscriptionRegistry:
    """
    Authoritative state for instrument subscriptions across connection lifetimes.
    """
    desired: Set[str]
    active: Set[str]
    pending: Set[str]
    failed: Set[str]


class MarketDataOrchestrator:
    """
    Provider-agnostic coordinator for the market data machine.
    Manages startup sequence, subscription registry, REST reconciliation,
    gap backfilling, and automatic reconnect recovery with exponential backoff.
    """

    DEFAULT_BACKOFF_STEPS = (1.0, 2.0, 4.0, 8.0, 16.0)

    def __init__(
        self,
        market_data_provider: IMarketDataProvider,
        historical_provider: Optional[IHistoricalDataProvider] = None,
        option_chain_provider: Optional[IOptionChainProvider] = None,
        instrument_master: Optional[InstrumentMasterService] = None,
        event_bus: Optional[MarketEventBus] = None,
        live_market_state: Optional[LiveMarketState] = None,
        feed_health_engine: Optional[FeedHealthEngine] = None,
        candle_engine: Optional[CanonicalCandleEngine] = None,
        historical_bootstrap: Optional[HistoricalBootstrapService] = None,
        reconciliation_service: Optional[ReconciliationService] = None,
        backoff_steps: Sequence[float] = DEFAULT_BACKOFF_STEPS,
    ) -> None:
        self.market_data_provider = market_data_provider
        self.historical_provider = historical_provider
        self.option_chain_provider = option_chain_provider

        self.instrument_master = instrument_master or InstrumentMasterService()
        self.event_bus = event_bus or MarketEventBus()
        self.live_market_state = live_market_state or LiveMarketState(self.instrument_master)
        self.feed_health_engine = feed_health_engine or FeedHealthEngine()
        self.candle_engine = candle_engine or CanonicalCandleEngine()
        self.historical_bootstrap = historical_bootstrap or HistoricalBootstrapService(historical_provider=self.historical_provider)
        self.reconciliation_service = reconciliation_service or ReconciliationService(self.live_market_state)

        self.backoff_steps = list(backoff_steps)
        self._lock = threading.RLock()
        self._state = OrchestratorLifecycleState.INITIALIZING
        self._reconnect_attempts: int = 0
        self._total_reconnects: int = 0
        self._total_backfills: int = 0

        # Authoritative Subscription Registry
        self.subscriptions = SubscriptionRegistry(
            desired=set(),
            active=set(),
            pending=set(),
            failed=set(),
        )

        # Wire EventBus to core engines
        self.live_market_state.attach(self.event_bus)
        self.feed_health_engine.attach(self.event_bus)
        self.candle_engine.attach(self.event_bus)

        # Subscribe to health events for auto-recovery trigger
        self._health_sub_id = self.event_bus.subscribe(
            MarketEventType.FEED_STALE,
            self._handle_feed_stale_event,
        )

    @property
    def lifecycle_state(self) -> OrchestratorLifecycleState:
        with self._lock:
            return self._state

    def start(self, instruments_to_subscribe: Sequence[CanonicalInstrument]) -> bool:
        """
        Executes full pipeline startup flow:
        1. Ensure EventBus is running.
        2. Register desired subscriptions.
        3. Connect provider transport.
        4. Subscribe desired instruments.
        5. Verify state and set RUNNING.
        """
        with self._lock:
            if not self.event_bus.is_running:
                self.event_bus.start()

            for inst in instruments_to_subscribe:
                if isinstance(inst, CanonicalInstrument):
                    self.subscriptions.desired.add(inst.canonical_id)
                    self.subscriptions.pending.add(inst.canonical_id)

            # Connect transport
            self.market_data_provider.connect()

            # Subscribe
            try:
                self.market_data_provider.subscribe(instruments_to_subscribe)
                for inst in instruments_to_subscribe:
                    self.subscriptions.active.add(inst.canonical_id)
                    self.subscriptions.pending.discard(inst.canonical_id)
            except Exception as e:
                logger.error(f"Subscription failed: {e}")
                for inst in instruments_to_subscribe:
                    self.subscriptions.failed.add(inst.canonical_id)
                    self.subscriptions.pending.discard(inst.canonical_id)
                self._state = OrchestratorLifecycleState.DEGRADED
                return False

            self._state = OrchestratorLifecycleState.RUNNING
            return True

    def stop(self) -> None:
        """Shuts down orchestrator cleanly."""
        with self._lock:
            self._state = OrchestratorLifecycleState.STOPPED
            try:
                self.market_data_provider.disconnect()
            except Exception:
                pass
            self.live_market_state.detach()
            self.feed_health_engine.detach()
            self.candle_engine.detach()
            if self.event_bus.is_running:
                self.event_bus.stop(drain=True)

    def _handle_feed_stale_event(self, event: MarketEvent) -> None:
        """Triggers recovery sequence when feed health degrades."""
        with self._lock:
            if self._state in (OrchestratorLifecycleState.RUNNING, OrchestratorLifecycleState.DEGRADED):
                self.trigger_recovery()

    def trigger_recovery(self) -> bool:
        """
        Executes automated recovery routine:
        1. Marks state RECOVERING.
        2. Reconnects provider with bounded exponential backoff.
        3. Restores all DESIRED subscriptions.
        4. Triggers gap detection and historical candle backfill.
        """
        with self._lock:
            self._state = OrchestratorLifecycleState.RECOVERING
            self._total_reconnects += 1

            # Bounded backoff delay
            idx = min(self._reconnect_attempts, len(self.backoff_steps) - 1)
            delay = self.backoff_steps[idx]
            self._reconnect_attempts += 1

        logger.warning(f"Orchestrator initiating recovery (attempt {self._reconnect_attempts}, backoff {delay}s)...")
        time.sleep(delay)

        with self._lock:
            try:
                self.market_data_provider.disconnect()
                self.market_data_provider.connect()

                # Rebuild subscriptions strictly from DESIRED set
                desired_cids = list(self.subscriptions.desired)
                insts_to_sub = []
                for cid in desired_cids:
                    inst = self.instrument_master.get_by_canonical_id(cid)
                    if inst:
                        insts_to_sub.append(inst)

                if insts_to_sub:
                    self.market_data_provider.subscribe(insts_to_sub)
                    self.subscriptions.active = set(self.subscriptions.desired)
                    self.subscriptions.failed.clear()

                # Backfill missing candles if historical provider exists
                self.backfill_detected_gaps()

                self._reconnect_attempts = 0
                self._state = OrchestratorLifecycleState.RUNNING
                logger.info("Orchestrator recovery completed successfully.")
                return True
            except Exception as e:
                logger.error(f"Orchestrator recovery failed: {e}")
                self._state = OrchestratorLifecycleState.DEGRADED
                return False

    def backfill_detected_gaps(self) -> int:
        """
        Queries CandleEngine for gaps, fetches missing historical candles,
        and hydrates CandleEngine with quality=BACKFILLED.
        """
        if self.historical_provider is None:
            return 0

        backfilled_count = 0
        with self._lock:
            for cid in list(self.subscriptions.active):
                gaps = self.candle_engine.detect_gaps(cid, Timeframe.M1)
                inst = self.instrument_master.get_by_canonical_id(cid)
                if not gaps or not inst:
                    continue

                for gap_start, gap_end in gaps:
                    try:
                        candles = self.historical_provider.fetch_candles(
                            instrument=inst,
                            timeframe=Timeframe.M1,
                            start=gap_start,
                            end=gap_end,
                        )
                        if candles:
                            # Re-tag quality as BACKFILLED
                            tagged = [
                                CanonicalCandle(
                                    canonical_instrument_id=c.canonical_instrument_id,
                                    provider=c.provider,
                                    session_date=c.session_date,
                                    timeframe=c.timeframe,
                                    start_timestamp=c.start_timestamp,
                                    end_timestamp=c.end_timestamp,
                                    open=c.open,
                                    high=c.high,
                                    low=c.low,
                                    close=c.close,
                                    volume=c.volume,
                                    oi=c.oi,
                                    quality=CandleQuality.BACKFILLED,
                                )
                                for c in candles
                            ]
                            self.candle_engine.hydrate_candles(tagged)
                            backfilled_count += len(tagged)
                            self._total_backfills += len(tagged)
                    except Exception as ex:
                        logger.error(f"Error backfilling gap for {cid}: {ex}")

        return backfilled_count

    def get_diagnostics(self) -> Dict[str, Any]:
        """
        Returns unified diagnostic status across all market data layers for proof mode.
        """
        with self._lock:
            nifty_state = self.live_market_state.get_nifty()
            vix_state = self.live_market_state.get_vix()

            return {
                "orchestrator_state": self._state.value,
                "provider": self.market_data_provider.provider_name(),
                "provider_connected": self.market_data_provider.is_connected(),
                "subscriptions": {
                    "desired_count": len(self.subscriptions.desired),
                    "active_count": len(self.subscriptions.active),
                    "pending_count": len(self.subscriptions.pending),
                    "failed_count": len(self.subscriptions.failed),
                },
                "feed_health": self.feed_health_engine.stats(),
                "live_market_state": self.live_market_state.stats(),
                "candle_engine": self.candle_engine.snapshot(),
                "nifty_canonical_price": nifty_state.last_price if nifty_state else None,
                "vix_canonical_price": vix_state.last_price if vix_state else None,
                "total_reconnects": self._total_reconnects,
                "total_backfills": self._total_backfills,
            }
