# src/models/intelligence_snapshot.py
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WhatChangedEvent:
    event_type: str  # BREADTH_IMPROVED / RESISTANCE_BROKEN / REGIME_CHANGED / OPPORTUNITY_ARMED / etc.
    summary: str
    previous_value: Any
    current_value: Any
    timestamp: str
    significance: str = "HIGH"  # HIGH / MEDIUM / LOW

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IntelligenceSnapshot:
    """
    Unified Intelligence-domain synthesis snapshot derived from authoritative state.
    """
    session_date: str
    timestamp: str
    runtime_id: str = "rt-staging-1"
    state_sequence: int = 1

    spot: float = 0.0
    spot_change: float = 0.0
    spot_change_pct: float = 0.0

    directional_bias: str = "NEUTRAL"
    regime: str = "RANGE_DAY"
    trend_strength: float = 50.0
    volatility_regime: str = "COMPRESSED"

    breadth_summary: Dict[str, Any] = field(default_factory=dict)
    sector_participation: Dict[str, Any] = field(default_factory=dict)

    key_levels: Dict[str, Any] = field(default_factory=dict)
    options_summary: Dict[str, Any] = field(default_factory=dict)
    institutional_context: Dict[str, Any] = field(default_factory=dict)
    news_context: Dict[str, Any] = field(default_factory=dict)

    confidence: float = 0.0
    evidence_quality: float = 0.0

    primary_suggestion: Optional[Dict[str, Any]] = None
    watchlist_candidates: List[Dict[str, Any]] = field(default_factory=list)
    what_changed: List[Dict[str, Any]] = field(default_factory=list)
    qualification_diagnostics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
