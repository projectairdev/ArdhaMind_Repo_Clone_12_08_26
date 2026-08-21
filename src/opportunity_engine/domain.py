from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SetupType(str, Enum):
    BREAKOUT = "BREAKOUT"
    BREAKDOWN = "BREAKDOWN"
    PULLBACK = "PULLBACK"
    REVERSAL = "REVERSAL"
    MOMENTUM_CONTINUATION = "MOMENTUM_CONTINUATION"


class Direction(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"


class OpportunityStatus(str, Enum):
    RAW = "RAW"
    WATCHING = "WATCHING"
    QUALIFIED = "QUALIFIED"
    TRADE_READY = "TRADE_READY"
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"
    INVALIDATED = "INVALIDATED"
    EXPIRED = "EXPIRED"


@dataclass
class DetectorInputRequirements:
    required_inputs: List[str] = field(default_factory=list)
    optional_inputs: List[str] = field(default_factory=list)
    max_freshness_seconds: float = 30.0
    min_history_candles: int = 1


@dataclass
class DetectorResult:
    detector_id: str
    detector_version: str
    detected: bool
    direction: Direction
    raw_score: float  # 0 to 100
    evidence: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    blocked: bool = False
    blocking_reason: Optional[str] = None
    suggested_levels: Dict[str, Any] = field(default_factory=dict)
    validity_window_seconds: int = 900


@dataclass
class OpportunityStatusTransition:
    timestamp: str
    previous_status: str
    new_status: str
    reason: str
    state_sequence: int


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
    underlying: str = "NIFTY"
    instrument_family: str = "NIFTY CE"  # "NIFTY CE" | "NIFTY PE" | "NIFTY FUT"

    market_session: str = "OPEN"
    market_state: str = "LIVE"
    freshness_state: str = "FRESH"

    status: str = "RAW"
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

    confidence_score: float = 0.0
    quality_score: float = 0.0
    priority_score: float = 0.0

    detector_scores: Dict[str, float] = field(default_factory=dict)
    confirmation_signals: List[str] = field(default_factory=list)
    conflicting_signals: List[str] = field(default_factory=list)

    market_context_snapshot: Dict[str, Any] = field(default_factory=dict)
    options_context_snapshot: Dict[str, Any] = field(default_factory=dict)
    news_context_snapshot: Dict[str, Any] = field(default_factory=dict)
    macro_context_snapshot: Dict[str, Any] = field(default_factory=dict)

    expiry_at: str = ""
    invalidated_at: Optional[str] = None

    source_detector: str = ""
    detector_version: str = "1.0.0"
    scoring_version: str = "1.0.0"
    qualification_version: str = "1.0.0"
    config_version: str = "1.0.0"

    explanation_tokens: List[str] = field(default_factory=list)
    explanation_fields: Dict[str, Any] = field(default_factory=dict)

    data_quality: Dict[str, Any] = field(default_factory=dict)
    blocking_reasons: List[str] = field(default_factory=list)

    transition_history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "runtime_id": self.runtime_id,
            "state_sequence": self.state_sequence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "first_detected_at": self.first_detected_at,
            "last_detected_at": self.last_detected_at,
            "setup_type": self.setup_type,
            "direction": self.direction,
            "underlying": self.underlying,
            "instrument_family": self.instrument_family,
            "market_session": self.market_session,
            "market_state": self.market_state,
            "freshness_state": self.freshness_state,
            "status": self.status,
            "status_reason": self.status_reason,
            "entry_reference": self.entry_reference,
            "entry_zone_low": self.entry_zone_low,
            "entry_zone_high": self.entry_zone_high,
            "invalidation_level": self.invalidation_level,
            "target_reference": self.target_reference,
            "target_zone_1": self.target_zone_1,
            "target_zone_2": self.target_zone_2,
            "estimated_reward": self.estimated_reward,
            "estimated_risk": self.estimated_risk,
            "reward_risk_ratio": self.reward_risk_ratio,
            "confidence_score": self.confidence_score,
            "quality_score": self.quality_score,
            "priority_score": self.priority_score,
            "detector_scores": self.detector_scores,
            "confirmation_signals": self.confirmation_signals,
            "conflicting_signals": self.conflicting_signals,
            "market_context_snapshot": self.market_context_snapshot,
            "options_context_snapshot": self.options_context_snapshot,
            "news_context_snapshot": self.news_context_snapshot,
            "macro_context_snapshot": self.macro_context_snapshot,
            "expiry_at": self.expiry_at,
            "invalidated_at": self.invalidated_at,
            "source_detector": self.source_detector,
            "detector_version": self.detector_version,
            "scoring_version": self.scoring_version,
            "qualification_version": self.qualification_version,
            "config_version": self.config_version,
            "explanation_tokens": self.explanation_tokens,
            "explanation_fields": self.explanation_fields,
            "data_quality": self.data_quality,
            "blocking_reasons": self.blocking_reasons,
            "transition_history": self.transition_history,
        }


@dataclass
class DetectorHealthInfo:
    detector_id: str
    status: str  # "HEALTHY" | "DEGRADED" | "BLOCKED" | "ERROR"
    version: str
    last_evaluated: Optional[str] = None
    detections_today: int = 0
    qualified_today: int = 0
    blocked_today: int = 0
    rejected_today: int = 0
    errors: List[str] = field(default_factory=list)
    data_blockers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "detector_id": self.detector_id,
            "status": self.status,
            "version": self.version,
            "last_evaluated": self.last_evaluated,
            "detections_today": self.detections_today,
            "qualified_today": self.qualified_today,
            "blocked_today": self.blocked_today,
            "rejected_today": self.rejected_today,
            "errors": self.errors,
            "data_blockers": self.data_blockers,
        }


@dataclass
class ScanMetrics:
    scan_duration_ms: float = 0.0
    detector_duration_ms: float = 0.0
    candidates_evaluated: int = 0
    active_candidates: int = 0
    last_scan_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scan_duration_ms": round(self.scan_duration_ms, 2),
            "detector_duration_ms": round(self.detector_duration_ms, 2),
            "candidates_evaluated": self.candidates_evaluated,
            "active_candidates": self.active_candidates,
            "last_scan_at": self.last_scan_at,
        }
