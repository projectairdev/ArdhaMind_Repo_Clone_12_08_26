from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional, Dict, List
import uuid
from datetime import datetime, timezone


class OpportunityStatus(str, Enum):
    RAW = "RAW"
    WATCHING = "WATCHING"
    QUALIFIED = "QUALIFIED"
    TRADE_READY = "TRADE_READY"
    REJECTED = "REJECTED"
    INVALIDATED = "INVALIDATED"
    EXPIRED = "EXPIRED"


class SetupType(str, Enum):
    BREAKOUT = "BREAKOUT"
    BREAKDOWN = "BREAKDOWN"
    PULLBACK = "PULLBACK"
    REVERSAL = "REVERSAL"
    MOMENTUM_CONTINUATION = "MOMENTUM_CONTINUATION"


class Direction(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"


@dataclass
class DetectorResult:
    detector_id: str
    detector_version: str
    detected: bool
    direction: str  # BULLISH | BEARISH
    setup_type: str  # SetupType value
    raw_score: float  # 0.0 - 100.0
    evidence: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    blocking_reason: Optional[str] = None
    suggested_levels: dict[str, float] = field(default_factory=dict)
    validity_window_seconds: int = 1800
    provisional_strike: Optional[int] = None
    option_type: Optional[str] = None  # "CE" or "PE"


@dataclass
class ScoreBreakdown:
    setup_quality: float = 0.0
    trend_alignment: float = 0.0
    momentum_strength: float = 0.0
    structure_quality: float = 0.0
    options_confirmation: float = 0.0
    breadth_confirmation: float = 0.0
    volatility_suitability: float = 0.0
    news_risk: float = 0.0
    macro_risk: float = 0.0
    data_quality: float = 0.0
    reward_risk_quality: float = 0.0
    extension_penalty: float = 0.0
    conflict_penalty: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass
class LifecycleTransition:
    timestamp: str
    previous_status: str
    new_status: str
    reason: str
    state_sequence: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CanonicalOpportunity:
    opportunity_id: str
    runtime_id: str
    state_sequence: int
    created_at: str
    updated_at: str
    first_detected_at: str
    last_detected_at: str

    setup_type: str
    direction: str
    underlying: str = "NIFTY 50"
    instrument_family: str = "NIFTY SPOT"

    market_session: str = "LIVE"
    market_state: str = "OPEN"
    freshness_state: str = "FRESH"

    status: str = OpportunityStatus.RAW.value
    status_reason: str = "Initial detection"

    entry_reference: float = 0.0
    entry_zone_low: float = 0.0
    entry_zone_high: float = 0.0

    invalidation_level: float = 0.0
    target_reference: float = 0.0
    target_zone_1: float = 0.0
    target_zone_2: float = 0.0

    estimated_reward: float = 0.0
    estimated_risk: float = 0.0
    reward_risk_ratio: float = 0.0

    confidence_score: int = 0
    quality_score: int = 0
    priority_score: int = 0

    detector_scores: dict[str, Any] = field(default_factory=dict)
    confirmation_signals: list[str] = field(default_factory=list)
    conflicting_signals: list[str] = field(default_factory=list)

    market_context_snapshot: dict[str, Any] = field(default_factory=dict)
    options_context_snapshot: dict[str, Any] = field(default_factory=dict)
    news_context_snapshot: dict[str, Any] = field(default_factory=dict)
    macro_context_snapshot: dict[str, Any] = field(default_factory=dict)

    expiry_at: str = ""
    invalidated_at: Optional[str] = None

    source_detector: str = ""
    detector_version: str = "1.0.0"

    explanation_tokens: list[str] = field(default_factory=list)
    explanation_fields: dict[str, Any] = field(default_factory=dict)

    data_quality: dict[str, Any] = field(default_factory=dict)
    blocking_reasons: list[str] = field(default_factory=list)
    lifecycle_history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CanonicalOpportunity:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
