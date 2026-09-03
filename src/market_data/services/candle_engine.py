from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time as dtime, timedelta, timezone
import threading
from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.market_data.bus.events import MarketEvent, MarketEventType
from src.market_data.bus.event_bus import MarketEventBus
from src.market_data.models.canonical_candle import CanonicalCandle
from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.models.quality_enums import CandleQuality, Timeframe


def _floor_timestamp_anchored(
    dt: datetime,
    tf: Timeframe | str,
    session_anchor_time: dtime = dtime(9, 15),
) -> Tuple[datetime, datetime]:
    """
    Calculates start and end timestamps for a candle bucket anchored to session start.
    For 60m with 09:15 anchor: buckets are 09:15-10:15, 10:15-11:15, etc.
    """
    tf_str = tf.value if hasattr(tf, "value") else str(tf)
    base = dt.replace(microsecond=0)

    if tf_str == "1s":
        start = base
        end = start + timedelta(seconds=1)
    elif tf_str == "1m":
        start = base.replace(second=0)
        end = start + timedelta(minutes=1)
    elif tf_str in ("5m", "15m", "60m"):
        # Anchor calculation based on minutes elapsed since midnight
        anchor_min = session_anchor_time.hour * 60 + session_anchor_time.minute
        current_min = base.hour * 60 + base.minute

        interval_min = 5 if tf_str == "5m" else (15 if tf_str == "15m" else 60)
        diff = current_min - anchor_min
        bucket_index = diff // interval_min
        bucket_start_min = anchor_min + (bucket_index * interval_min)

        start_hour = (bucket_start_min // 60) % 24
        start_minute = bucket_start_min % 60
        start = base.replace(hour=start_hour, minute=start_minute, second=0)
        end = start + timedelta(minutes=interval_min)
    elif tf_str == "1D":
        start = base.replace(hour=0, minute=0, second=0)
        end = start + timedelta(days=1)
    else:
        start = base.replace(second=0)
        end = start + timedelta(minutes=1)

    return start, end


@dataclass
class _LiveCandleBuilder:
    canonical_instrument_id: str
    provider: str
    session_date: date
    timeframe: Timeframe
    start_timestamp: datetime
    end_timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    start_cumulative_volume: Optional[int] = None
    volume: Optional[int] = None
    oi: Optional[int] = None

    def to_canonical(self, quality: CandleQuality = CandleQuality.VALID) -> CanonicalCandle:
        return CanonicalCandle(
            canonical_instrument_id=self.canonical_instrument_id,
            provider=self.provider,
            session_date=self.session_date,
            timeframe=self.timeframe,
            start_timestamp=self.start_timestamp,
            end_timestamp=self.end_timestamp,
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume,
            oi=self.oi,
            quality=quality,
        )


class CanonicalCandleEngine:
    """
    Deterministically constructs 1-minute canonical candles from raw accepted ticks
    and aggregates session-anchored higher timeframes (5m, 15m, 60m, 1D).
    Calculates incremental volume from cumulative feeds without index volume fabrication.
    """

    SUPPORTED_TIMEFRAMES = [Timeframe.M1, Timeframe.M5, Timeframe.M15, Timeframe.M60, Timeframe.D1]

    def __init__(
        self,
        session_anchor_time: dtime = dtime(9, 15),
    ) -> None:
        self.session_anchor_time = session_anchor_time
        self._lock = threading.RLock()
        self._event_bus: Optional[MarketEventBus] = None
        self._subscription_id: Optional[str] = None

        self._live_1m_candles: Dict[str, _LiveCandleBuilder] = {}
        self._finalized_candles: Dict[str, Dict[str, List[CanonicalCandle]]] = {}
        self._live_htf_candles: Dict[str, Dict[str, _LiveCandleBuilder]] = {}
        self._detected_gaps: Dict[str, List[Tuple[datetime, datetime]]] = {}

    def attach(self, event_bus: MarketEventBus) -> None:
        """Attaches to MarketEventBus to consume ticks and publish candle updates."""
        with self._lock:
            if self._event_bus is event_bus and self._subscription_id is not None:
                return
            if self._event_bus is not None and self._subscription_id is not None:
                self.detach()

            self._event_bus = event_bus
            self._subscription_id = event_bus.subscribe(
                MarketEventType.TICK,
                self._handle_tick_event,
            )

    def detach(self) -> None:
        """Detaches from MarketEventBus."""
        with self._lock:
            if self._event_bus and self._subscription_id:
                self._event_bus.unsubscribe(self._subscription_id)
            self._event_bus = None
            self._subscription_id = None

    def apply_tick(self, tick: CanonicalTick) -> None:
        """Convenience alias for on_tick."""
        self.on_tick(tick)

    def on_tick(self, tick: CanonicalTick) -> None:
        """Ingests a CanonicalTick, rolls 1m candles, finalizes closed buckets, and updates higher timeframes."""
        if not isinstance(tick, CanonicalTick):
            return

        cid = tick.canonical_instrument_id
        ts = tick.exchange_timestamp
        price = tick.last_price

        with self._lock:
            if cid not in self._finalized_candles:
                self._finalized_candles[cid] = {tf.value: [] for tf in self.SUPPORTED_TIMEFRAMES}
                self._live_htf_candles[cid] = {}

            live_1m = self._live_1m_candles.get(cid)

            if live_1m is None:
                start, end = _floor_timestamp_anchored(ts, Timeframe.M1, self.session_anchor_time)
                # Volume semantics: start cumulative volume is recorded
                init_vol = 0 if tick.volume is not None else None
                live_1m = _LiveCandleBuilder(
                    canonical_instrument_id=cid,
                    provider=tick.provider,
                    session_date=tick.session_date,
                    timeframe=Timeframe.M1,
                    start_timestamp=start,
                    end_timestamp=end,
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                    start_cumulative_volume=tick.volume,
                    volume=init_vol,
                    oi=tick.oi,
                )
                self._live_1m_candles[cid] = live_1m
                self._update_htf_live(tick)
                self._publish_candle_updated(live_1m.to_canonical())
                return

            if ts >= live_1m.end_timestamp:
                # 1. Finalize previous 1m candle
                closed_candle = live_1m.to_canonical(quality=CandleQuality.VALID)
                self._finalized_candles[cid][Timeframe.M1.value].append(closed_candle)
                self._publish_candle_closed(closed_candle)

                # 2. Gap detection
                start_next, end_next = _floor_timestamp_anchored(ts, Timeframe.M1, self.session_anchor_time)
                expected_next_start = live_1m.end_timestamp
                if start_next > expected_next_start and tick.session_date == live_1m.session_date:
                    gaps = self._detected_gaps.setdefault(cid, [])
                    gaps.append((expected_next_start, start_next))

                # 3. Aggregate into HTF
                self._process_1m_into_htf(closed_candle)

                # 4. Start fresh 1m live candle
                init_vol = 0 if tick.volume is not None else None
                live_1m = _LiveCandleBuilder(
                    canonical_instrument_id=cid,
                    provider=tick.provider,
                    session_date=tick.session_date,
                    timeframe=Timeframe.M1,
                    start_timestamp=start_next,
                    end_timestamp=end_next,
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                    start_cumulative_volume=tick.volume,
                    volume=init_vol,
                    oi=tick.oi,
                )
                self._live_1m_candles[cid] = live_1m
                self._update_htf_live(tick)
                self._publish_candle_updated(live_1m.to_canonical())
            elif ts >= live_1m.start_timestamp:
                live_1m.high = max(live_1m.high, price)
                live_1m.low = min(live_1m.low, price)
                live_1m.close = price

                # Incremental volume calculation from cumulative ticks
                if tick.volume is not None:
                    if live_1m.start_cumulative_volume is not None and tick.volume >= live_1m.start_cumulative_volume:
                        live_1m.volume = tick.volume - live_1m.start_cumulative_volume
                    else:
                        live_1m.volume = (live_1m.volume or 0)

                if tick.oi is not None:
                    live_1m.oi = tick.oi

                self._update_htf_live(tick)
                self._publish_candle_updated(live_1m.to_canonical())

    def _update_htf_live(self, tick: CanonicalTick) -> None:
        cid = tick.canonical_instrument_id
        ts = tick.exchange_timestamp
        price = tick.last_price

        for tf in [Timeframe.M5, Timeframe.M15, Timeframe.M60, Timeframe.D1]:
            tf_key = tf.value
            start, end = _floor_timestamp_anchored(ts, tf, self.session_anchor_time)
            htf_live = self._live_htf_candles[cid].get(tf_key)

            if htf_live is None or ts >= htf_live.end_timestamp:
                init_vol = 0 if tick.volume is not None else None
                htf_live = _LiveCandleBuilder(
                    canonical_instrument_id=cid,
                    provider=tick.provider,
                    session_date=tick.session_date,
                    timeframe=tf,
                    start_timestamp=start,
                    end_timestamp=end,
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                    start_cumulative_volume=tick.volume,
                    volume=init_vol,
                    oi=tick.oi,
                )
                self._live_htf_candles[cid][tf_key] = htf_live
            else:
                htf_live.high = max(htf_live.high, price)
                htf_live.low = min(htf_live.low, price)
                htf_live.close = price
                if tick.volume is not None and htf_live.start_cumulative_volume is not None:
                    if tick.volume >= htf_live.start_cumulative_volume:
                        htf_live.volume = tick.volume - htf_live.start_cumulative_volume
                if tick.oi is not None:
                    htf_live.oi = tick.oi

    def _process_1m_into_htf(self, candle_1m: CanonicalCandle) -> None:
        cid = candle_1m.canonical_instrument_id

        for tf in [Timeframe.M5, Timeframe.M15, Timeframe.M60, Timeframe.D1]:
            tf_key = tf.value
            start, end = _floor_timestamp_anchored(candle_1m.start_timestamp, tf, self.session_anchor_time)
            finalized_list = self._finalized_candles[cid][tf_key]

            if candle_1m.end_timestamp == end:
                m1_candles = [
                    c for c in self._finalized_candles[cid][Timeframe.M1.value]
                    if start <= c.start_timestamp < end
                ]
                if m1_candles:
                    has_volume = any(c.volume is not None for c in m1_candles)
                    total_vol = sum(c.volume for c in m1_candles if c.volume is not None) if has_volume else None
                    htf_candle = CanonicalCandle(
                        canonical_instrument_id=cid,
                        provider=candle_1m.provider,
                        session_date=candle_1m.session_date,
                        timeframe=tf,
                        start_timestamp=start,
                        end_timestamp=end,
                        open=m1_candles[0].open,
                        high=max(c.high for c in m1_candles),
                        low=min(c.low for c in m1_candles),
                        close=m1_candles[-1].close,
                        volume=total_vol,
                        oi=m1_candles[-1].oi,
                        quality=CandleQuality.VALID,
                    )
                    if not finalized_list or finalized_list[-1].start_timestamp < start:
                        finalized_list.append(htf_candle)
                        self._publish_candle_closed(htf_candle)

    def _handle_tick_event(self, event: MarketEvent) -> None:
        if isinstance(event.payload, CanonicalTick):
            self.on_tick(event.payload)

    def _publish_candle_updated(self, candle: CanonicalCandle) -> None:
        if self._event_bus and self._event_bus.is_running and self._event_bus.has_subscribers(MarketEventType.CANDLE_UPDATED):
            self._event_bus.publish(
                MarketEventType.CANDLE_UPDATED,
                candle,
                canonical_instrument_id=candle.canonical_instrument_id,
            )

    def _publish_candle_closed(self, candle: CanonicalCandle) -> None:
        if self._event_bus and self._event_bus.is_running and self._event_bus.has_subscribers(MarketEventType.CANDLE_CLOSED):
            self._event_bus.publish(
                MarketEventType.CANDLE_CLOSED,
                candle,
                canonical_instrument_id=candle.canonical_instrument_id,
            )

    def get_live_candle(
        self,
        canonical_instrument_id: str,
        timeframe: Timeframe | str = Timeframe.M1,
    ) -> Optional[CanonicalCandle]:
        """Returns the currently accumulating live unfinalized candle."""
        tf_str = timeframe.value if hasattr(timeframe, "value") else str(timeframe)
        with self._lock:
            cid = canonical_instrument_id.strip()
            if tf_str == "1m":
                b = self._live_1m_candles.get(cid)
                return b.to_canonical() if b else None
            else:
                b = self._live_htf_candles.get(cid, {}).get(tf_str)
                return b.to_canonical() if b else None

    def get_candles(
        self,
        canonical_instrument_id: str,
        timeframe: Timeframe | str = Timeframe.M1,
        limit: Optional[int] = None,
    ) -> List[CanonicalCandle]:
        """Returns a snapshot list of finalized historical candles for an instrument."""
        tf_str = timeframe.value if hasattr(timeframe, "value") else str(timeframe)
        with self._lock:
            cid = canonical_instrument_id.strip()
            candles = self._finalized_candles.get(cid, {}).get(tf_str, [])
            if limit is not None and limit > 0:
                return list(candles[-limit:])
            return list(candles)

    def hydrate_candles(self, candles: Sequence[CanonicalCandle]) -> None:
        """Hydrates historical candles from bootstrap without duplication."""
        with self._lock:
            for candle in candles:
                if not isinstance(candle, CanonicalCandle):
                    continue
                cid = candle.canonical_instrument_id
                tf_str = candle.timeframe.value if hasattr(candle.timeframe, "value") else str(candle.timeframe)

                if cid not in self._finalized_candles:
                    self._finalized_candles[cid] = {tf.value: [] for tf in self.SUPPORTED_TIMEFRAMES}
                    self._live_htf_candles[cid] = {}

                existing_list = self._finalized_candles[cid].setdefault(tf_str, [])
                if not any(c.start_timestamp == candle.start_timestamp for c in existing_list):
                    existing_list.append(candle)

            for cid_key in self._finalized_candles:
                for tf_k in self._finalized_candles[cid_key]:
                    self._finalized_candles[cid_key][tf_k].sort(key=lambda c: c.start_timestamp)

    def detect_gaps(
        self,
        canonical_instrument_id: str,
        timeframe: Timeframe | str = Timeframe.M1,
    ) -> List[Tuple[datetime, datetime]]:
        """Returns detected missing intervals for the instrument."""
        with self._lock:
            cid = canonical_instrument_id.strip()
            return list(self._detected_gaps.get(cid, []))

    def snapshot(self) -> Dict[str, Any]:
        """Returns copy-safe diagnostic snapshot of engine state."""
        with self._lock:
            return {
                "instruments_count": len(self._finalized_candles),
                "live_1m_count": len(self._live_1m_candles),
                "session_anchor_time": self.session_anchor_time.isoformat(),
                "finalized_1m_total": sum(len(v.get("1m", [])) for v in self._finalized_candles.values()),
                "finalized_5m_total": sum(len(v.get("5m", [])) for v in self._finalized_candles.values()),
                "finalized_15m_total": sum(len(v.get("15m", [])) for v in self._finalized_candles.values()),
                "finalized_60m_total": sum(len(v.get("60m", [])) for v in self._finalized_candles.values()),
                "finalized_1D_total": sum(len(v.get("1D", [])) for v in self._finalized_candles.values()),
                "total_detected_gaps": sum(len(g) for g in self._detected_gaps.values()),
            }
