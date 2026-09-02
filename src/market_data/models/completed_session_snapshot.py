from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional

from src.market_data.models.canonical_provenance import CanonicalProvenance
from src.market_data.models.quality_enums import DataQualityStatus


class FinalizationStage(str, Enum):
    PRICE_FINAL = "PRICE_FINAL"                     # 15:30 IST: Continuous price finalized
    DERIVATIVES_PENDING = "DERIVATIVES_PENDING"     # Awaiting final settlement/OI sync
    INSTITUTIONAL_PENDING = "INSTITUTIONAL_PENDING" # Awaiting post-market block/FII reports
    COMPLETE = "COMPLETE"                           # Authoritative permanent session close


@dataclass(frozen=True)
class CompletedSessionSnapshot:
    """
    Authoritative, immutable snapshot of a finalized completed market session.
    Keyed by (canonical_instrument_id, session_date).
    """
    canonical_instrument_id: str
    session_date: date
    open: float
    high: float
    low: float
    close: float
    previous_close: Optional[float]
    absolute_change: Optional[float]
    percent_change: Optional[float]
    range: float
    final_candle_timestamp: datetime
    quality: DataQualityStatus = DataQualityStatus.VALID
    provenance: Optional[CanonicalProvenance] = None
    finalization_stage: FinalizationStage = FinalizationStage.PRICE_FINAL
    finalized_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.canonical_instrument_id or not str(self.canonical_instrument_id).strip():
            raise ValueError("CompletedSessionSnapshot 'canonical_instrument_id' is required.")
        if self.open <= 0 or self.high <= 0 or self.low <= 0 or self.close <= 0:
            raise ValueError("CompletedSessionSnapshot OHLC values must be positive.")
        if self.high < self.low:
            raise ValueError(f"High ({self.high}) cannot be lower than Low ({self.low}).")
        if self.final_candle_timestamp.tzinfo is None:
            raise ValueError("CompletedSessionSnapshot 'final_candle_timestamp' must be timezone-aware.")
