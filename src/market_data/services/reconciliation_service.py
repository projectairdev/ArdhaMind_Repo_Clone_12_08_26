from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
from typing import Any, Dict, Optional

from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.state.live_market_state import InstrumentState, LiveMarketState

logger = logging.getLogger(__name__)


class ReconciliationStatus(str, Enum):
    IN_SYNC = "IN_SYNC"
    WS_NEWER = "WS_NEWER"
    REST_NEWER = "REST_NEWER"
    DIVERGED = "DIVERGED"
    INSUFFICIENT_TIMESTAMP = "INSUFFICIENT_TIMESTAMP"


@dataclass(frozen=True)
class ReconciliationReport:
    canonical_instrument_id: str
    status: ReconciliationStatus
    ws_price: Optional[float]
    rest_price: Optional[float]
    price_diff: Optional[float]
    ws_timestamp: Optional[datetime]
    rest_timestamp: Optional[datetime]
    applied_to_state: bool
    reconciled_at: datetime


class ReconciliationService:
    """
    Reconciles streaming WebSocket LiveMarketState with REST reference snapshots.
    Guarantees that REST quotes only update canonical state when REST is conclusively newer.
    """

    def __init__(
        self,
        live_market_state: LiveMarketState,
        divergence_threshold_pct: float = 0.5,
    ) -> None:
        self.live_market_state = live_market_state
        self.divergence_threshold_pct = divergence_threshold_pct
        self.total_reconciliations: int = 0
        self.rest_applied_count: int = 0

    def reconcile_instrument(
        self,
        rest_tick: CanonicalTick,
    ) -> ReconciliationReport:
        """
        Compares a REST snapshot tick against the current LiveMarketState for an instrument.
        """
        self.total_reconciliations += 1
        cid = rest_tick.canonical_instrument_id
        ws_state = self.live_market_state.get(cid)
        now_dt = datetime.now(rest_tick.exchange_timestamp.tzinfo)

        if ws_state is None:
            # No WS state exists yet, REST tick is authoritative
            return ReconciliationReport(
                canonical_instrument_id=cid,
                status=ReconciliationStatus.REST_NEWER,
                ws_price=None,
                rest_price=rest_tick.last_price,
                price_diff=None,
                ws_timestamp=None,
                rest_timestamp=rest_tick.exchange_timestamp,
                applied_to_state=False,
                reconciled_at=now_dt,
            )

        ws_price = ws_state.last_price
        rest_price = rest_tick.last_price
        diff = round(abs(ws_price - rest_price), 4)
        pct_diff = (diff / ws_price) * 100.0 if ws_price > 0 else 0.0

        ws_ts = ws_state.exchange_timestamp
        rest_ts = rest_tick.exchange_timestamp

        # Temporal classification
        applied = False
        if ws_ts is None or rest_ts is None:
            status = ReconciliationStatus.INSUFFICIENT_TIMESTAMP
        elif ws_ts == rest_ts:
            if pct_diff <= self.divergence_threshold_pct:
                status = ReconciliationStatus.IN_SYNC
            else:
                status = ReconciliationStatus.DIVERGED
        elif rest_ts > ws_ts:
            status = ReconciliationStatus.REST_NEWER
            applied = True
            self.rest_applied_count += 1
        else:
            # ws_ts > rest_ts
            status = ReconciliationStatus.WS_NEWER

        return ReconciliationReport(
            canonical_instrument_id=cid,
            status=status,
            ws_price=ws_price,
            rest_price=rest_price,
            price_diff=diff,
            ws_timestamp=ws_ts,
            rest_timestamp=rest_ts,
            applied_to_state=applied,
            reconciled_at=now_dt,
        )
