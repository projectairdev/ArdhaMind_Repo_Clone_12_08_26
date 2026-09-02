from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import time
from typing import Any, Dict, List, Optional

from src.analytics.market_analytics_engine import MarketAnalyticsEngine
from src.decision.decision.decision_engine import DecisionEngine
from src.decision.products.product_coordinator import ProductCoordinator
from src.market_data.bus.event_bus import MarketEventBus
from src.market_data.bus.events import MarketEventType
from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.models.quality_enums import DataQualityStatus
from src.market_data.providers.dhan.dhan_instrument_mapper import DhanInstrumentMapper
from src.market_data.services.candle_engine import CanonicalCandleEngine
from src.market_data.services.feed_health_engine import FeedHealthEngine
from src.market_data.services.instrument_master_service import InstrumentMasterService
from src.market_data.session.exchange_calendar import ExchangeCalendar
from src.market_data.session.session_authority import CanonicalSessionAuthority
from src.market_data.state.live_market_state import LiveMarketState
from src.prediction.prediction_engine import PredictionEngine, PredictionPhase
from src.replay.clock.replay_clock import ReplayClock
from src.replay.models.replay_models import ReplayConfig, ReplayEvent, ReplayReport, ReplaySpeed
from src.replay.source.replay_source import ReplaySource


class MarketReplayEngine:
    """
    Deterministic full-pipeline market replay coordinator.
    Replays canonical market events through standard pipeline components with injected clock.
    """

    def __init__(
        self,
        clock: Optional[ReplayClock] = None,
        instrument_master: Optional[InstrumentMasterService] = None,
    ) -> None:
        self.clock = clock or ReplayClock()
        self.instrument_master = instrument_master or InstrumentMasterService()
        DhanInstrumentMapper(self.instrument_master).register_default_universe()

        self.calendar = ExchangeCalendar()
        self.session_authority = CanonicalSessionAuthority(self.calendar)

        # Canonical Stack
        self.event_bus = MarketEventBus()
        self.event_bus.start()
        self.state_store = LiveMarketState(self.instrument_master)
        self.state_store.attach(self.event_bus)
        self.feed_health = FeedHealthEngine(
            healthy_threshold_seconds=3.0,
            delayed_threshold_seconds=7.0,
        )
        self.feed_health.attach(self.event_bus)
        self.feed_health.on_socket_connected()
        self.candle_engine = CanonicalCandleEngine()
        self.analytics_engine = MarketAnalyticsEngine(
            self.state_store,
            self.candle_engine,
            self.session_authority,
        )
        self.product_coordinator = ProductCoordinator(self.session_authority)

    def run_replay(self, source: ReplaySource, config: ReplayConfig) -> ReplayReport:
        """Executes replay to completion and generates comprehensive ReplayReport."""
        events = source.get_events(config)
        wall_start = time.perf_counter()

        if not events:
            return ReplayReport(
                replay_id=config.replay_id,
                session_date=config.session_date,
                total_events=0,
                processed_events=0,
                elapsed_simulated_seconds=0.0,
                elapsed_wallclock_seconds=0.0,
                reproducibility_hash=hashlib.sha256(b"EMPTY").hexdigest(),
                final_state_revision=0,
                final_nifty_price=None,
                final_decision_state="BLOCKED",
                quality=DataQualityStatus.UNAVAILABLE,
            )

        sim_start = events[0].event_timestamp
        sim_end = events[-1].event_timestamp
        self.clock.start(sim_start, config.speed)

        processed = 0

        for e in events:
            # Advance clock deterministically
            self.clock.advance_to(e.event_timestamp)

            if e.event_type == "TICK" and isinstance(e.payload, CanonicalTick):
                tick: CanonicalTick = e.payload
                # 1. Publish into EventBus
                self.event_bus.publish(
                    event_type=MarketEventType.TICK,
                    payload=tick,
                    canonical_instrument_id=tick.canonical_instrument_id,
                )
                self.candle_engine.apply_tick(tick)
                self.feed_health.on_tick(tick)
                processed += 1

        # Stop and drain event bus to ensure all events were processed into LiveMarketState
        self.event_bus.stop(drain=True, timeout=5.0)

        # Run end-of-replay full pipeline evaluation
        analytics_snap = self.analytics_engine.generate_snapshot()
        pred_snap = PredictionEngine.generate_prediction(
            snapshot=analytics_snap,
            target_session_date=config.session_date,
            phase=PredictionPhase.INTRADAY,
        )
        dec_snap = DecisionEngine.evaluate_decision(analytics_snap, pred_snap)

        wall_elapsed = time.perf_counter() - wall_start
        sim_elapsed = (sim_end - sim_start).total_seconds()
        self.clock.complete()

        # Compute deterministic reproducibility fingerprint
        canon_fingerprint = f"{self.state_store.state_revision}_{analytics_snap.price_structure.last_price}_{dec_snap.decision_state.value}_{dec_snap.confidence_band}"
        rep_hash = hashlib.sha256(canon_fingerprint.encode("utf-8")).hexdigest()

        nifty_state = self.state_store.get_nifty()
        nifty_price = nifty_state.last_price if nifty_state else None

        return ReplayReport(
            replay_id=config.replay_id,
            session_date=config.session_date,
            total_events=len(events),
            processed_events=processed,
            elapsed_simulated_seconds=sim_elapsed,
            elapsed_wallclock_seconds=round(wall_elapsed, 4),
            reproducibility_hash=rep_hash,
            final_state_revision=self.state_store.state_revision,
            final_nifty_price=nifty_price,
            final_decision_state=dec_snap.decision_state.value,
            quality=dec_snap.quality,
        )
