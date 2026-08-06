from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from src.models.data_quality import FreshnessStatus, QualityStatus, ValueClassification


@dataclass(frozen=True)
class RuntimeInput:
    source: str
    instrument: str
    observed_at: Optional[str]
    received_at: Optional[str]
    freshness: FreshnessStatus
    quality: QualityStatus
    classification: ValueClassification
    payload: Any
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def usable(self) -> bool:
        return (self.payload is not None and not self.errors and
                self.freshness not in {FreshnessStatus.BLOCKED, FreshnessStatus.UNAVAILABLE} and
                self.quality not in {QualityStatus.INVALID})


@dataclass(frozen=True)
class RuntimeSnapshot:
    snapshot_id: str
    generated_at: str
    market_session: RuntimeInput
    broker_session: RuntimeInput
    nifty_market: RuntimeInput
    historical_candles: RuntimeInput
    india_vix: RuntimeInput
    option_instruments: RuntimeInput
    option_quotes: RuntimeInput
    expiry_metadata: RuntimeInput
    news_context: RuntimeInput
    account_summary: Optional[RuntimeInput] = None
