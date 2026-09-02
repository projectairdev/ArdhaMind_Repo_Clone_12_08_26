from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import threading
from typing import Any, Dict, List, Optional

from src.market_data.bus.events import MarketEvent, MarketEventType
from src.market_data.bus.event_bus import MarketEventBus
from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.models.quality_enums import DataQualityStatus
from src.market_data.services.instrument_master_service import InstrumentMasterService


@dataclass(frozen=True)
class InstrumentState:
    """
    Immutable, authoritative in-memory snapshot of the latest accepted market state
    for a single canonical instrument.
    Timestamps (exchange_timestamp and received_at) are strictly required and timezone-aware.
    """
    canonical_instrument_id: str
    symbol: Optional[str]
    session_date: date
    last_price: float
    exchange_timestamp: datetime
    received_at: datetime
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    previous_close: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    volume: Optional[int] = None
    oi: Optional[int] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    spread: Optional[float] = None
    provider: str = "UNKNOWN"
    last_event_sequence: int = 0
    last_tick_internal_sequence: Optional[int] = None
    update_count: int = 1
    quality: DataQualityStatus = DataQualityStatus.VALID

    def __post_init__(self) -> None:
        if not self.canonical_instrument_id or not isinstance(self.canonical_instrument_id, str) or not self.canonical_instrument_id.strip():
            raise ValueError("InstrumentState 'canonical_instrument_id' must be a non-empty string.")
        if not isinstance(self.session_date, date):
            raise TypeError("InstrumentState 'session_date' must be a date instance.")
        if not isinstance(self.last_price, (int, float)) or self.last_price <= 0.0:
            raise ValueError(f"InstrumentState 'last_price' must be a positive number, got {self.last_price}.")
        if not isinstance(self.exchange_timestamp, datetime) or self.exchange_timestamp.tzinfo is None:
            raise ValueError("InstrumentState 'exchange_timestamp' must be a timezone-aware datetime.")
        if not isinstance(self.received_at, datetime) or self.received_at.tzinfo is None:
            raise ValueError("InstrumentState 'received_at' must be a timezone-aware datetime.")


class LiveMarketState:
    """
    Thread-safe, authoritative in-memory state store holding the latest accepted
    InstrumentState for each canonical instrument.
    Enforces strict chronological update ordering, monotonic same-session OHLC merging,
    stale crossed-quote prevention, and clean new-session resets.
    """

    def __init__(self, instrument_master: Optional[InstrumentMasterService] = None) -> None:
        self._lock = threading.RLock()
        self._states: Dict[str, InstrumentState] = {}
        self._instrument_master = instrument_master
        self._event_bus: Optional[MarketEventBus] = None
        self._subscription_id: Optional[str] = None

        # State Revision & Metrics
        self._state_revision: int = 0
        self._accepted_updates: int = 0
        self._rejected_updates: int = 0
        self._rejected_older_session: int = 0
        self._rejected_out_of_order: int = 0
        self._rejected_invalid_event: int = 0
        self._last_applied_event_sequence: Optional[int] = None
        self._last_updated_at: Optional[str] = None

    @property
    def state_revision(self) -> int:
        with self._lock:
            return self._state_revision

    def attach(self, event_bus: MarketEventBus) -> None:
        """Subscribes to MarketEventType.TICK on the provided MarketEventBus. Idempotent."""
        with self._lock:
            if self._event_bus is event_bus and self._subscription_id is not None:
                return
            if self._event_bus is not None and self._subscription_id is not None:
                self.detach()

            self._event_bus = event_bus
            self._subscription_id = event_bus.subscribe(
                MarketEventType.TICK,
                self.apply_tick_event,
            )

    def detach(self) -> None:
        """Unsubscribes from the attached MarketEventBus. Idempotent."""
        with self._lock:
            if self._event_bus and self._subscription_id:
                self._event_bus.unsubscribe(self._subscription_id)
            self._event_bus = None
            self._subscription_id = None

    def apply_tick_event(self, event: MarketEvent) -> bool:
        """
        Processes an incoming MarketEvent containing a CanonicalTick.
        Validates event structure, enforces temporal ordering invariants,
        merges valid same-session fields with OHLC and quote monotonicity,
        and increments state_revision atomically.
        Returns True if accepted and applied, False if rejected.
        """
        if not isinstance(event, MarketEvent) or event.event_type != MarketEventType.TICK:
            with self._lock:
                self._rejected_updates += 1
                self._rejected_invalid_event += 1
            return False

        tick = event.payload
        if not isinstance(tick, CanonicalTick):
            with self._lock:
                self._rejected_updates += 1
                self._rejected_invalid_event += 1
            return False

        cid = tick.canonical_instrument_id
        if event.canonical_instrument_id and event.canonical_instrument_id != cid:
            with self._lock:
                self._rejected_updates += 1
                self._rejected_invalid_event += 1
            return False

        with self._lock:
            # Validate with InstrumentMaster if supplied
            resolved_symbol: Optional[str] = None
            if self._instrument_master is not None:
                master_inst = self._instrument_master.get_by_canonical_id(cid)
                if master_inst is None:
                    self._rejected_updates += 1
                    self._rejected_invalid_event += 1
                    return False
                resolved_symbol = master_inst.symbol
            else:
                resolved_symbol = cid.split(":")[-1] if ":" in cid else cid

            existing = self._states.get(cid)

            # Ordering guards
            if existing is not None:
                # Rule A: Reject older session date
                if tick.session_date < existing.session_date:
                    self._rejected_updates += 1
                    self._rejected_older_session += 1
                    return False

                # Rule B: Same session ordering checks
                if tick.session_date == existing.session_date:
                    if tick.exchange_timestamp < existing.exchange_timestamp:
                        self._rejected_updates += 1
                        self._rejected_out_of_order += 1
                        return False
                    elif tick.exchange_timestamp == existing.exchange_timestamp:
                        if event.sequence <= existing.last_event_sequence:
                            self._rejected_updates += 1
                            self._rejected_out_of_order += 1
                            return False

            # Compute new InstrumentState
            is_new_session = existing is None or tick.session_date > existing.session_date

            if is_new_session:
                # New session transition: fresh state from tick only (zero prior-session intraday leakage)
                open_val = tick.open
                high_val = tick.high
                low_val = tick.low
                prev_close_val = tick.previous_close
                vol_val = tick.volume
                oi_val = tick.oi
                bid_val = tick.bid
                ask_val = tick.ask
                update_cnt = 1
            else:
                # Same session: merge with strict OHLC monotonicity and bid/ask crossing prevention
                # 1. Open: first known valid open remains authoritative
                if existing.open is not None:
                    open_val = existing.open
                else:
                    open_val = tick.open

                # 2. High: monotonic expansion
                if existing.high is not None and tick.high is not None:
                    high_val = max(existing.high, tick.high)
                else:
                    high_val = tick.high if tick.high is not None else existing.high

                # 3. Low: monotonic contraction
                if existing.low is not None and tick.low is not None:
                    low_val = min(existing.low, tick.low)
                else:
                    low_val = tick.low if tick.low is not None else existing.low

                # 4. Previous Close
                prev_close_val = tick.previous_close if tick.previous_close is not None else existing.previous_close

                # 5. Volume and OI
                vol_val = tick.volume if tick.volume is not None else existing.volume
                oi_val = tick.oi if tick.oi is not None else existing.oi

                # 6. Bid / Ask merge safety (crossing prevention)
                if tick.bid is not None and tick.ask is not None:
                    bid_val = tick.bid
                    ask_val = tick.ask
                elif tick.bid is not None and tick.ask is None:
                    bid_val = tick.bid
                    # Preserve existing ask only if it does not cross with the new bid
                    if existing.ask is not None and existing.ask >= tick.bid:
                        ask_val = existing.ask
                    else:
                        ask_val = None
                elif tick.ask is not None and tick.bid is None:
                    ask_val = tick.ask
                    # Preserve existing bid only if it does not cross with the new ask
                    if existing.bid is not None and tick.ask >= existing.bid:
                        bid_val = existing.bid
                    else:
                        bid_val = None
                else:
                    # Neither supplied, preserve existing quote
                    bid_val = existing.bid
                    ask_val = existing.ask

                update_cnt = existing.update_count + 1

            # Derived mathematical calculations (Zero fabrication)
            change_val: Optional[float] = None
            change_pct_val: Optional[float] = None
            if prev_close_val is not None and prev_close_val > 0.0:
                change_val = round(tick.last_price - prev_close_val, 4)
                change_pct_val = round((change_val / prev_close_val) * 100.0, 4)

            spread_val: Optional[float] = None
            if bid_val is not None and ask_val is not None:
                spread_val = round(ask_val - bid_val, 4)

            new_state = InstrumentState(
                canonical_instrument_id=cid,
                symbol=resolved_symbol,
                session_date=tick.session_date,
                last_price=tick.last_price,
                exchange_timestamp=tick.exchange_timestamp,
                received_at=tick.received_at,
                open=open_val,
                high=high_val,
                low=low_val,
                previous_close=prev_close_val,
                change=change_val,
                change_pct=change_pct_val,
                volume=vol_val,
                oi=oi_val,
                bid=bid_val,
                ask=ask_val,
                spread=spread_val,
                provider=tick.provider,
                last_event_sequence=event.sequence,
                last_tick_internal_sequence=tick.internal_sequence,
                update_count=update_cnt,
                quality=DataQualityStatus.VALID,
            )

            # Store update and advance revision
            self._states[cid] = new_state
            self._state_revision += 1
            self._accepted_updates += 1
            self._last_applied_event_sequence = event.sequence
            self._last_updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            return True

    def get(self, canonical_instrument_id: str) -> Optional[InstrumentState]:
        """Retrieves the latest InstrumentState for the specified canonical ID."""
        if not canonical_instrument_id:
            return None
        with self._lock:
            return self._states.get(canonical_instrument_id.strip())

    def get_instrument_state(self, canonical_instrument_id: str) -> Optional[InstrumentState]:
        """Convenience alias for get()."""
        return self.get(canonical_instrument_id)

    def get_nifty(self) -> Optional[InstrumentState]:
        """Convenience accessor for NIFTY 50 spot state."""
        return self.get("IDX:NSE:NIFTY_50")

    def get_vix(self) -> Optional[InstrumentState]:
        """Convenience accessor for INDIA VIX state."""
        return self.get("IDX:NSE:INDIA_VIX")

    def get_options(
        self,
        underlying: str = "NIFTY",
        expiry: Optional[str] = None,
    ) -> List[InstrumentState]:
        """Returns all registered option states matching the underlying and optional expiry."""
        u_key = underlying.upper().strip()
        exp_str = str(expiry)[:10] if expiry else None

        with self._lock:
            results = []
            for cid, state in self._states.items():
                if cid.startswith("OPT:"):
                    parts = cid.split(":")
                    opt_und = parts[2] if len(parts) > 2 else ""
                    opt_exp = parts[3] if len(parts) > 3 else ""

                    if opt_und.upper() == u_key:
                        if exp_str is None or opt_exp == exp_str:
                            results.append(state)

            return sorted(results, key=lambda s: s.canonical_instrument_id)

    def list_states(self) -> List[InstrumentState]:
        """Returns a snapshot list of all tracked InstrumentStates."""
        with self._lock:
            return list(self._states.values())

    def snapshot(self) -> Dict[str, InstrumentState]:
        """Returns an immutable / copy-safe dictionary mapping canonical IDs to their states."""
        with self._lock:
            return dict(self._states)

    def stats(self) -> Dict[str, Any]:
        """Returns a copy-safe diagnostic dictionary of store telemetry."""
        with self._lock:
            return {
                "instrument_count": len(self._states),
                "state_revision": self._state_revision,
                "accepted_updates": self._accepted_updates,
                "rejected_updates": self._rejected_updates,
                "rejected_older_session": self._rejected_older_session,
                "rejected_out_of_order": self._rejected_out_of_order,
                "rejected_invalid_event": self._rejected_invalid_event,
                "last_applied_event_sequence": self._last_applied_event_sequence,
                "last_updated_at": self._last_updated_at,
                "attached_to_event_bus": self._event_bus is not None,
            }
