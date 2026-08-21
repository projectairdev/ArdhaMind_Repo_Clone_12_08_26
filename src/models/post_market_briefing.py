# src/models/post_market_briefing.py
"""
Post-Market Briefing Domain Model for AIR ArdhaMind.

Represents a canonical 15:20 IST post-market briefing artifact that bridges
today's session reality with tomorrow's preparation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class NiftySnapshot:
    price_at_snapshot: float
    open: float
    high_so_far: float
    low_so_far: float
    previous_close: float
    change_points: float
    change_pct: float
    session_range_so_far: float
    official_close_value: Optional[float] = None
    official_close_available: bool = False
    reconciled_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> NiftySnapshot:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class SessionCharacter:
    directional_bias: str  # BULLISH | BEARISH | NEUTRAL | MIXED
    market_regime: str     # TREND_DAY | RANGE_DAY | REVERSAL_DAY | FAILED_BREAKOUT | FAILED_BREAKDOWN | VOLATILE_TWO_WAY | LOW_PARTICIPATION_DRIFT | SIDEWAYS
    volatility_regime: str  # COMPRESSED | NORMAL | ELEVATED | EXTREME
    trend_quality: str
    breadth_state: str
    participation_quality: str
    intraday_structure: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> SessionCharacter:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class KeyLevels:
    immediate_support: str
    immediate_resistance: str
    major_support: str
    major_resistance: str
    decision_zone: str
    day_high: float
    day_low: float
    opening_range_high: float
    opening_range_low: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> KeyLevels:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class OptionsContext:
    atm_strike: Optional[float] = None
    expiry: str = "UNAVAILABLE"
    pcr_oi: Optional[float] = None
    pcr_volume: Optional[float] = None
    max_pain: Optional[float] = None
    call_wall: Optional[float] = None
    put_wall: Optional[float] = None
    atm_iv: Optional[float] = None
    options_bias: str = "UNAVAILABLE"
    call_oi_shift: str = "UNAVAILABLE"
    put_oi_shift: str = "UNAVAILABLE"
    late_session_positioning: str = "UNAVAILABLE"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> OptionsContext:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class BreadthContext:
    advances: int = 0
    declines: int = 0
    unchanged: int = 0
    breadth_bias: str = "NEUTRAL"
    breadth_strength: str = "MODERATE"
    heavyweight_participation: str = "BALANCED"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> BreadthContext:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class SectorContext:
    strongest_sectors: List[str] = field(default_factory=list)
    weakest_sectors: List[str] = field(default_factory=list)
    sectors_improving_into_close: List[str] = field(default_factory=list)
    sectors_weakening_into_close: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> SectorContext:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class InstitutionalContext:
    fii_net_crores: Optional[float] = None
    dii_net_crores: Optional[float] = None
    net_crores: Optional[float] = None
    source_date: str = "UNAVAILABLE"
    freshness: str = "PREVIOUS_TRADING_SESSION"
    provenance: str = "Published EOD Data"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> InstitutionalContext:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class MacroContext:
    gift_nifty: Optional[float] = None
    usd_inr: Optional[float] = None
    dxy: Optional[float] = None
    brent: Optional[float] = None
    gold: Optional[float] = None
    india_vix: Optional[float] = None
    global_index_tone: str = "NEUTRAL"
    overnight_risk_flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> MacroContext:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class NewsContext:
    major_session_drivers: List[Dict[str, Any]] = field(default_factory=list)
    late_session_news: List[Dict[str, Any]] = field(default_factory=list)
    tomorrow_known_events: List[Dict[str, Any]] = field(default_factory=list)
    event_risk_level: str = "MODERATE"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> NewsContext:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class PreMarketVsActual:
    expected_open: str = "UNAVAILABLE"
    actual_open: str = "UNAVAILABLE"
    open_result: str = "PENDING"
    opening_bias: str = "UNAVAILABLE"
    observed_opening_bias: str = "UNAVAILABLE"
    bias_result: str = "PENDING"
    expected_range: str = "UNAVAILABLE"
    actual_range: str = "UNAVAILABLE"
    range_result: str = "PENDING"
    expected_high_zone: str = "UNAVAILABLE"
    actual_high: str = "UNAVAILABLE"
    high_result: str = "PENDING"
    expected_low_zone: str = "UNAVAILABLE"
    actual_low: str = "UNAVAILABLE"
    low_result: str = "PENDING"
    primary_scenario: str = "UNAVAILABLE"
    observed_outcome: str = "UNAVAILABLE"
    scenario_result: str = "PENDING"
    hits_count: int = 0
    near_count: int = 0
    misses_count: int = 0
    pending_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> PreMarketVsActual:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class SessionStoryTimelineItem:
    time_hhmm: str
    title: str
    observation: str
    price_level: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> SessionStoryTimelineItem:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class SessionStory:
    timeline: List[SessionStoryTimelineItem] = field(default_factory=list)
    narrative_summary: str = "Session story constructed from intraday observations."
    coverage_status: str = "COMPLETE"  # COMPLETE | PARTIAL

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["timeline"] = [t.to_dict() if hasattr(t, "to_dict") else t for t in self.timeline]
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> SessionStory:
        items = []
        for raw in d.get("timeline", []):
            if isinstance(raw, dict):
                items.append(SessionStoryTimelineItem.from_dict(raw))
            elif isinstance(raw, SessionStoryTimelineItem):
                items.append(raw)
        return cls(
            timeline=items,
            narrative_summary=d.get("narrative_summary", ""),
            coverage_status=d.get("coverage_status", "COMPLETE")
        )


@dataclass
class Phase3ExecutionSummary:
    proposals_generated: int = 0
    proposals_rejected: int = 0
    proposals_approved: int = 0
    orders_submitted: int = 0
    orders_filled: int = 0
    trades_closed: int = 0
    open_positions_at_15_20: int = 0
    realized_trade_pnl_analytics: float = 0.0
    unresolved_operations: int = 0
    status_label: str = "NO EXECUTED TRADES"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Phase3ExecutionSummary:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class ScenarioDetail:
    title: str
    trigger: str
    confirmation: str
    expected_behavior: str
    invalidation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> ScenarioDetail:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class NextSessionOutlook:
    target_trading_date: str
    baseline_bias: str  # BULLISH | BEARISH | NEUTRAL | MIXED
    confidence: str    # scalar percentage or UNAVAILABLE
    expected_regime: str  # TREND | RANGE | VOLATILE | MIXED | UNAVAILABLE
    overnight_risk: str  # LOW | MODERATE | HIGH
    carry_forward_levels: Dict[str, Any] = field(default_factory=dict)
    scenario_base: Optional[ScenarioDetail] = None
    scenario_bullish: Optional[ScenarioDetail] = None
    scenario_bearish: Optional[ScenarioDetail] = None
    scenario_range: Optional[ScenarioDetail] = None
    watchlist: Dict[str, List[Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        for k in ["scenario_base", "scenario_bullish", "scenario_bearish", "scenario_range"]:
            v = getattr(self, k)
            if v and hasattr(v, "to_dict"):
                d[k] = v.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> NextSessionOutlook:
        kwargs: Dict[str, Any] = {
            "target_trading_date": d.get("target_trading_date", ""),
            "baseline_bias": d.get("baseline_bias", "NEUTRAL"),
            "confidence": d.get("confidence", "UNAVAILABLE"),
            "expected_regime": d.get("expected_regime", "UNAVAILABLE"),
            "overnight_risk": d.get("overnight_risk", "MODERATE"),
            "carry_forward_levels": d.get("carry_forward_levels", {}),
            "watchlist": d.get("watchlist", {}),
        }
        for k in ["scenario_base", "scenario_bullish", "scenario_bearish", "scenario_range"]:
            raw = d.get(k)
            if isinstance(raw, dict):
                kwargs[k] = ScenarioDetail.from_dict(raw)
            elif isinstance(raw, ScenarioDetail):
                kwargs[k] = raw
        return cls(**kwargs)


@dataclass
class PostMarketBriefingReport:
    report_id: str
    trading_session_date: str
    generated_at: str
    schema_version: int = 1
    snapshot_time_ist: str = "15:20 IST"
    snapshot_type: str = "PRE_CLOSE_1520"  # PRE_CLOSE_1520 | POST_CLOSE_FINAL
    lifecycle_status: str = "SNAPSHOT_FROZEN"  # PREPARING | SNAPSHOT_FROZEN | AWAITING_OFFICIAL_CLOSE | FINAL_RECONCILED | DEGRADED | MISSED_SNAPSHOT
    nifty_snapshot: Optional[NiftySnapshot] = None
    session_character: Optional[SessionCharacter] = None
    key_levels: Optional[KeyLevels] = None
    options_context: Optional[OptionsContext] = None
    breadth_context: Optional[BreadthContext] = None
    sector_context: Optional[SectorContext] = None
    institutional_context: Optional[InstitutionalContext] = None
    macro_context: Optional[MacroContext] = None
    news_context: Optional[NewsContext] = None
    pre_market_vs_actual: Optional[PreMarketVsActual] = None
    session_story: Optional[SessionStory] = None
    phase3_execution: Optional[Phase3ExecutionSummary] = None
    next_session_outlook: Optional[NextSessionOutlook] = None
    snapshot_1520_payload: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        for k in [
            "nifty_snapshot",
            "session_character",
            "key_levels",
            "options_context",
            "breadth_context",
            "sector_context",
            "institutional_context",
            "macro_context",
            "news_context",
            "pre_market_vs_actual",
            "session_story",
            "phase3_execution",
            "next_session_outlook",
        ]:
            val = getattr(self, k)
            if val and hasattr(val, "to_dict"):
                d[k] = val.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> PostMarketBriefingReport:
        kwargs: Dict[str, Any] = {
            "report_id": d.get("report_id", ""),
            "trading_session_date": d.get("trading_session_date", ""),
            "generated_at": d.get("generated_at", ""),
            "schema_version": d.get("schema_version", 1),
            "snapshot_time_ist": d.get("snapshot_time_ist", "15:20 IST"),
            "snapshot_type": d.get("snapshot_type", "PRE_CLOSE_1520"),
            "lifecycle_status": d.get("lifecycle_status", "SNAPSHOT_FROZEN"),
            "snapshot_1520_payload": d.get("snapshot_1520_payload"),
        }

        mappers = {
            "nifty_snapshot": NiftySnapshot,
            "session_character": SessionCharacter,
            "key_levels": KeyLevels,
            "options_context": OptionsContext,
            "breadth_context": BreadthContext,
            "sector_context": SectorContext,
            "institutional_context": InstitutionalContext,
            "macro_context": MacroContext,
            "news_context": NewsContext,
            "pre_market_vs_actual": PreMarketVsActual,
            "session_story": SessionStory,
            "phase3_execution": Phase3ExecutionSummary,
            "next_session_outlook": NextSessionOutlook,
        }

        for field_name, cls_target in mappers.items():
            raw = d.get(field_name)
            if isinstance(raw, dict):
                kwargs[field_name] = cls_target.from_dict(raw)
            elif isinstance(raw, cls_target):
                kwargs[field_name] = raw

        return cls(**kwargs)
