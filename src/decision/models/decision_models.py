from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.market_data.models.quality_enums import DataQualityStatus, OptionType


class DecisionState(str, Enum):
    BLOCKED = "BLOCKED"                          # Missing data, stale feed, high conflict
    NO_TRADE = "NO_TRADE"                        # Choppy conditions, no structural edge
    WATCH = "WATCH"                              # Catalyst or level forming
    WAIT = "WAIT"                                # Setup identified, awaiting trigger level confirmation
    READY_FOR_HUMAN_REVIEW = "READY_FOR_HUMAN_REVIEW"  # All confirmation criteria met, invalidation fixed
    INVALIDATED = "INVALIDATED"                  # Setup boundary violated


class SetupType(str, Enum):
    TREND_CONTINUATION = "TREND_CONTINUATION"
    BREAKOUT = "BREAKOUT"
    BREAKDOWN = "BREAKDOWN"
    RETEST = "RETEST"
    RANGE_REVERSAL = "RANGE_REVERSAL"
    OPENING_RANGE_BREAKOUT = "OPENING_RANGE_BREAKOUT"
    OPENING_RANGE_FAILURE = "OPENING_RANGE_FAILURE"
    NO_SETUP = "NO_SETUP"


class EntryReadinessStatus(str, Enum):
    NOT_READY = "NOT_READY"
    WAITING_FOR_TRIGGER = "WAITING_FOR_TRIGGER"
    READY_FOR_HUMAN_REVIEW = "READY_FOR_HUMAN_REVIEW"
    INVALIDATED = "INVALIDATED"
    BLOCKED_DATA_QUALITY = "BLOCKED_DATA_QUALITY"


class DecisionRiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    BLOCKED = "BLOCKED"


class StrategySuitability(str, Enum):
    LONG_CALL = "LONG_CALL"
    LONG_PUT = "LONG_PUT"
    BULL_CALL_SPREAD = "BULL_CALL_SPREAD"
    BEAR_PUT_SPREAD = "BEAR_PUT_SPREAD"
    DEFINED_RISK_ONLY = "DEFINED_RISK_ONLY"
    NO_OPTIONS_STRATEGY = "NO_OPTIONS_STRATEGY"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class StrikeCandidate:
    """Human-review strike recommendation (read-only intelligence)."""
    strike: float
    option_type: OptionType
    strength: str
    liquidity: str
    oi_context: str
    iv: Optional[float]
    spread: Optional[float]
    distance_from_spot: float
    supporting_reasons: List[str]
    risks: List[str]


@dataclass(frozen=True)
class SignalFusionContext:
    """Multi-layer signal synthesis."""
    directional_alignment: str
    agreement_score: float  # 0.0 to 1.0
    conflict_score: float   # 0.0 to 1.0
    supporting_factors: List[str]
    contradicting_factors: List[str]
    unavailable_factors: List[str]


@dataclass(frozen=True)
class OpportunityAssessment:
    """Identified structural market setup."""
    setup: SetupType
    status: str
    rationale: str
    trigger_condition: str
    confirmation_requirements: List[str]
    invalidation_level: Optional[float]
    invalidation_condition: str


@dataclass(frozen=True)
class RiskAssessment:
    """Risk evaluation for decision support."""
    risk_level: DecisionRiskLevel
    risk_factors: List[str]
    is_blocked: bool
    blocker_reason: Optional[str] = None


@dataclass(frozen=True)
class DecisionExplanation:
    """Deterministic natural explanation."""
    what_market_is_doing: str
    why_setup_exists: str
    what_confirms_it: str
    what_invalidates_it: str
    what_options_are_saying: str
    main_risks: List[str]
    why_waiting_or_ready: str
    missing_information: List[str]


@dataclass(frozen=True)
class DecisionSnapshot:
    """
    Authoritative, immutable decision intelligence snapshot.
    Combines signal fusion, opportunity assessment, risk gating, and candidate options.
    """
    decision_id: str
    session_date: date
    captured_at: datetime
    decision_state: DecisionState
    confidence_score: float  # 0.0 to 1.0
    confidence_band: str     # HIGH, MODERATE, LOW, INSUFFICIENT
    setup: OpportunityAssessment
    entry_readiness: EntryReadinessStatus
    risk_assessment: RiskAssessment
    strategy_suitability: StrategySuitability
    strike_candidates: List[StrikeCandidate]
    signal_fusion: SignalFusionContext
    explanation: DecisionExplanation
    quality: DataQualityStatus
    state_revision: int

    def __post_init__(self) -> None:
        if self.captured_at.tzinfo is None:
            raise ValueError("DecisionSnapshot 'captured_at' must be timezone-aware.")


@dataclass(frozen=True)
class DecisionAuditRecord:
    """Immutable audit record for regulatory traceability."""
    decision_id: str
    created_at: datetime
    session_date: date
    decision_state: DecisionState
    setup_type: SetupType
    confidence_score: float
    risk_level: DecisionRiskLevel
    trigger: str
    invalidation: str
    factors_summary: str
