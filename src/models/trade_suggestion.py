# src/models/trade_suggestion.py
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SuggestionState(str, Enum):
    WATCHING = "WATCHING"
    ARMED = "ARMED"
    ARMED_FOR_NEXT_SESSION = "ARMED_FOR_NEXT_SESSION"
    PRE_OPEN_WATCH = "PRE_OPEN_WATCH"
    ARMED_FOR_OPEN = "ARMED_FOR_OPEN"
    QUALIFIED = "QUALIFIED"
    EXECUTION_BLOCKED = "EXECUTION_BLOCKED"
    INVALIDATED = "INVALIDATED"
    EXPIRED = "EXPIRED"
    NO_TRADE = "NO_TRADE"


@dataclass
class TradeSuggestion:
    """
    Trader-grade actionable trade suggestion synthesized by ArdhaMind Intelligence Engine.
    Represents either ONE primary actionable trade or a structured NO_TRADE explaining next triggers.
    Includes full parameter provenance for auditability and session-aware actionability states.
    """
    suggestion_id: str
    candidate_id: str
    state: str  # WATCHING / ARMED / ARMED_FOR_NEXT_SESSION / PRE_OPEN_WATCH / ARMED_FOR_OPEN / QUALIFIED / etc.
    strategy: str  # BREAKOUT / BREAKOUT_RETEST / TREND_CONTINUATION / PULLBACK_TO_SUPPORT / etc.
    direction: str  # BULLISH / BEARISH / NEUTRAL
    underlying: str = "NIFTY"
    expiry: Optional[str] = "WEEKLY"
    strike: Optional[int] = None
    option_type: Optional[str] = None  # CE / PE / NONE
    contract_symbol: str = "TO_BE_RESOLVED"

    # Executable Premium Parameters (Optional / Nullable when Market Closed or Pre-Open)
    entry_zone: Optional[str] = None
    stop_loss: Optional[float] = None
    target_1: Optional[float] = None
    target_2: Optional[float] = None

    underlying_trigger: str = ""
    underlying_invalidation: str = ""

    risk_reward_ratio: Optional[float] = None
    confidence: float = 0.0
    conviction: float = 0.0
    evidence_quality: float = 0.0

    lots: Optional[int] = None
    quantity: Optional[int] = None
    estimated_max_loss: Optional[float] = None

    liquidity_status: str = "REQUIRES_LIVE_REVALIDATION"
    spread_pct: Optional[float] = None
    premium_ltp: Optional[float] = None

    rationale: List[str] = field(default_factory=list)
    opposing_evidence: List[str] = field(default_factory=list)
    invalidation_condition: str = ""

    qualification_reason: str = ""
    next_trigger: str = ""

    # Parameter Provenance Metadata
    provenance: Dict[str, Any] = field(default_factory=dict)

    source_runtime_id: str = "rt-staging-1"
    source_state_sequence: int = 1
    generated_at: str = ""
    expires_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
