from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence
from uuid import uuid4

from src.market_data.models.canonical_candle import CanonicalCandle
from src.market_data.models.canonical_option_chain import CanonicalOptionChainSnapshot
from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.models.quality_enums import DataQualityStatus


class ReplaySpeed(str, Enum):
    SPEED_1X = "1X"
    SPEED_10X = "10X"
    SPEED_100X = "100X"
    SPEED_MAX = "MAX"


class ReplayState(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ReplayEvent:
    """Canonical replay event envelope."""
    sequence: int
    event_timestamp: datetime
    event_type: str  # TICK, CANDLE, OPTION_CHAIN, EXTERNAL
    canonical_instrument_id: str
    payload: Any  # CanonicalTick, CanonicalCandle, or CanonicalOptionChainSnapshot
    provider: str = "CANONICAL_REPLAY"
    session_date: Optional[date] = None
    quality: DataQualityStatus = DataQualityStatus.VALID

    def __post_init__(self) -> None:
        if self.event_timestamp.tzinfo is None:
            raise ValueError("ReplayEvent 'event_timestamp' must be timezone-aware.")


@dataclass(frozen=True)
class ReplayConfig:
    """Replay execution parameters."""
    session_date: date
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    speed: ReplaySpeed = ReplaySpeed.SPEED_MAX
    step_interval_ms: int = 0
    replay_id: str = field(default_factory=lambda: f"rep_{uuid4().hex[:8]}")


@dataclass(frozen=True)
class ReplayReport:
    """Summary of completed replay execution."""
    replay_id: str
    session_date: date
    total_events: int
    processed_events: int
    elapsed_simulated_seconds: float
    elapsed_wallclock_seconds: float
    reproducibility_hash: str
    final_state_revision: int
    final_nifty_price: Optional[float]
    final_decision_state: str
    quality: DataQualityStatus
