from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass(frozen=True)
class DataProvenance:
    """
    Metadata tracking the authoritative origin, arrival time, and session
    for any market-data payload.
    """
    provider: str
    source_timestamp: datetime
    received_at: datetime
    session_date: date
    source_type: Optional[str] = None
    request_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.provider or not isinstance(self.provider, str) or not self.provider.strip():
            raise ValueError("DataProvenance 'provider' must be a non-empty string.")
        if not isinstance(self.source_timestamp, datetime):
            raise TypeError("DataProvenance 'source_timestamp' must be a datetime instance.")
        if self.source_timestamp.tzinfo is None:
            raise ValueError("DataProvenance 'source_timestamp' must be timezone-aware.")
        if not isinstance(self.received_at, datetime):
            raise TypeError("DataProvenance 'received_at' must be a datetime instance.")
        if self.received_at.tzinfo is None:
            raise ValueError("DataProvenance 'received_at' must be timezone-aware.")
        if not isinstance(self.session_date, date):
            raise TypeError("DataProvenance 'session_date' must be a date instance.")
