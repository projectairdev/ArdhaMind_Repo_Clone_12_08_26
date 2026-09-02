from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional

from src.market_data.models.quality_enums import DataQualityStatus


class SourceType(str, Enum):
    WEBSOCKET = "WEBSOCKET"
    REST_QUOTE = "REST_QUOTE"
    REST_HISTORICAL = "REST_HISTORICAL"
    OPTION_CHAIN_REST = "OPTION_CHAIN_REST"
    CALCULATED = "CALCULATED"


@dataclass(frozen=True)
class CanonicalProvenance:
    """
    Complete audit trail and metadata origin for canonical market data.
    Guarantees no anonymous or unverified data in the new architecture.
    """
    provider: str
    source_type: SourceType | str
    source_timestamp: datetime
    received_at: datetime
    session_date: date
    requested_session_date: Optional[date] = None
    quality: DataQualityStatus = DataQualityStatus.VALID
    fallback_reason: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.provider or not str(self.provider).strip():
            raise ValueError("CanonicalProvenance 'provider' is required.")
        if self.source_timestamp.tzinfo is None:
            raise ValueError("CanonicalProvenance 'source_timestamp' must be timezone-aware.")
        if self.received_at.tzinfo is None:
            raise ValueError("CanonicalProvenance 'received_at' must be timezone-aware.")
