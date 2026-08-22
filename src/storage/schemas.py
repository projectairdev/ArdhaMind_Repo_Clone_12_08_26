"""
src/storage/schemas.py

Typed data models and schema definitions for AIR Ardha Lightweight Session Storage Subsystem.
All durable schemas contain schema_name and schema_version.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class MarketOHLCV:
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None
    previous_close: Optional[float] = None
    change_points: Optional[float] = None
    change_percent: Optional[float] = None
    session_range_points: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StructuralLevels:
    pivot: Optional[float] = None
    r1: Optional[float] = None
    r2: Optional[float] = None
    r3: Optional[float] = None
    s1: Optional[float] = None
    s2: Optional[float] = None
    s3: Optional[float] = None
    local_atr_upper: Optional[float] = None
    local_atr_lower: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MarketRegime:
    regime: str = "UNKNOWN"
    day_character: str = "UNKNOWN"
    momentum: str = "NEUTRAL"
    volatility_regime: str = "UNKNOWN"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ClosingVIX:
    vix_close: Optional[float] = None
    vix_change_points: Optional[float] = None
    vix_change_pct: Optional[float] = None
    volatility_state: str = "UNKNOWN"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ClosingBreadth:
    advances: Optional[int] = None
    declines: Optional[int] = None
    unchanged: Optional[int] = None
    ad_ratio: Optional[float] = None
    breadth_bias: str = "UNKNOWN"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InstitutionalFlows:
    fii_net_crores: Optional[float] = None
    dii_net_crores: Optional[float] = None
    combined_net_crores: Optional[float] = None
    stance: str = "NEUTRAL"
    as_of_date: Optional[str] = None
    source: str = "NSE_EOD_SETTLEMENT"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SessionStory:
    headline: str = ""
    primary_driver: str = ""
    carry_forward_thesis: str = ""
    key_takeaways: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SessionCloseCore:
    schema_name: str = "SESSION_CLOSE_CORE"
    schema_version: str = "1.1.0"
    session_date: str = ""
    session_type: str = "REGULAR_TRADING"
    finalized_at: str = ""
    finalization_generation: int = 1
    idempotency_key: str = ""
    market_ohlcv: MarketOHLCV = field(default_factory=MarketOHLCV)
    structural_levels: StructuralLevels = field(default_factory=StructuralLevels)
    market_regime: MarketRegime = field(default_factory=MarketRegime)
    closing_vix: ClosingVIX = field(default_factory=ClosingVIX)
    closing_breadth: ClosingBreadth = field(default_factory=ClosingBreadth)
    institutional_flows: InstitutionalFlows = field(default_factory=InstitutionalFlows)
    session_story: SessionStory = field(default_factory=SessionStory)
    provenance: Dict[str, Any] = field(default_factory=lambda: {
        "provider": "ZERODHA_KITE_RECONCILED",
        "reconciliation_policy": "v1.0-standard",
        "reconciliation_status": "OFFICIAL_RECONCILED",
        "runtime_id": ""
    })

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionCloseCore":
        if not data:
            return cls()
        return cls(
            schema_name=data.get("schema_name", "SESSION_CLOSE_CORE"),
            schema_version=data.get("schema_version", "1.1.0"),
            session_date=data.get("session_date", ""),
            session_type=data.get("session_type", "REGULAR_TRADING"),
            finalized_at=data.get("finalized_at", ""),
            finalization_generation=data.get("finalization_generation", 1),
            idempotency_key=data.get("idempotency_key", ""),
            market_ohlcv=MarketOHLCV(**(data.get("market_ohlcv") or {})),
            structural_levels=StructuralLevels(**(data.get("structural_levels") or {})),
            market_regime=MarketRegime(**(data.get("market_regime") or {})),
            closing_vix=ClosingVIX(**(data.get("closing_vix") or {})),
            closing_breadth=ClosingBreadth(**(data.get("closing_breadth") or {})),
            institutional_flows=InstitutionalFlows(**(data.get("institutional_flows") or {})),
            session_story=SessionStory(**(data.get("session_story") or {})),
            provenance=data.get("provenance") or {}
        )


@dataclass
class StrikeBaseline:
    strike: float
    ce_oi: int = 0
    pe_oi: int = 0
    ce_ltp: Optional[float] = None
    pe_ltp: Optional[float] = None
    ce_iv: Optional[float] = None
    pe_iv: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DerivativesSummary:
    pcr_oi: Optional[float] = None
    pcr_volume: Optional[float] = None
    max_pain_strike: Optional[float] = None
    call_wall_strike: Optional[float] = None
    put_wall_strike: Optional[float] = None
    atm_iv_pct: Optional[float] = None
    total_call_oi_crores: Optional[float] = None
    total_put_oi_crores: Optional[float] = None
    oi_skew_bias: str = "BALANCED"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OptionsCloseBaseline:
    schema_name: str = "OPTIONS_CLOSE_BASELINE"
    schema_version: str = "1.1.0"
    session_date: str = ""
    expiry_date: str = ""
    captured_at: str = ""
    underlying_spot: Optional[float] = None
    atm_strike: Optional[float] = None
    derivatives_summary: DerivativesSummary = field(default_factory=DerivativesSummary)
    strike_baseline: List[Dict[str, Any]] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=lambda: {
        "provider": "ZERODHA_KITE_NFO",
        "last_valid_options_at": "",
        "finalization_quality": "COMPLETE_FINALIZED",
        "retention_tier": "PERMANENT"
    })

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OptionsCloseBaseline":
        if not data:
            return cls()
        return cls(
            schema_name=data.get("schema_name", "OPTIONS_CLOSE_BASELINE"),
            schema_version=data.get("schema_version", "1.1.0"),
            session_date=data.get("session_date", ""),
            expiry_date=data.get("expiry_date", ""),
            captured_at=data.get("captured_at", ""),
            underlying_spot=data.get("underlying_spot"),
            atm_strike=data.get("atm_strike"),
            derivatives_summary=DerivativesSummary(**(data.get("derivatives_summary") or {})),
            strike_baseline=data.get("strike_baseline") or [],
            provenance=data.get("provenance") or {}
        )


@dataclass
class TelemetryBucket:
    index: int
    window_start: str
    window_end: str
    start_spot: Optional[float] = None
    end_spot: Optional[float] = None
    high_spot: Optional[float] = None
    low_spot: Optional[float] = None
    change_pts: Optional[float] = None
    breadth_advances: Optional[int] = None
    breadth_declines: Optional[int] = None
    vix: Optional[float] = None
    pcr: Optional[float] = None
    max_pain: Optional[float] = None
    session_phase: str = "CONTINUOUS_TRADING"
    evidence_quality: str = "SUFFICIENT"
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IntradayTelemetrySeries:
    schema_name: str = "INTRADAY_TELEMETRY_SERIES"
    schema_version: str = "1.1.0"
    session_date: str = ""
    bucket_interval_minutes: int = 15
    total_buckets: int = 0
    buckets: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntradayTelemetrySeries":
        if not data:
            return cls()
        return cls(
            schema_name=data.get("schema_name", "INTRADAY_TELEMETRY_SERIES"),
            schema_version=data.get("schema_version", "1.1.0"),
            session_date=data.get("session_date", ""),
            bucket_interval_minutes=data.get("bucket_interval_minutes", 15),
            total_buckets=data.get("total_buckets", 0),
            buckets=data.get("buckets") or []
        )


@dataclass
class ConnectivityEvent:
    event_id: str
    session_date: str
    event_type: str
    detected_at: str
    last_valid_tick_at: Optional[str] = None
    socket_state: str = "UNKNOWN"
    broker_state: str = "UNKNOWN"
    affected_domains: List[str] = field(default_factory=list)
    reconnect_attempt: int = 0
    reconnect_started_at: Optional[str] = None
    socket_restored_at: Optional[str] = None
    subscriptions_restored_at: Optional[str] = None
    first_valid_tick_at: Optional[str] = None
    canonical_healthy_at: Optional[str] = None
    reconciliation_completed_at: Optional[str] = None
    gap_duration_ms: Optional[int] = None
    resolution: str = "UNRESOLVED"
    error_details: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CloseReconciliationPolicy:
    policy_version: str = "v1.0-standard"
    comparison_source: str = "KITE_HISTORICAL_DAY_CANDLE"
    max_absolute_drift_points: float = 5.0
    max_relative_drift_bps: float = 2.5
    source_priority: List[str] = field(default_factory=lambda: [
        "LIVE_CANONICAL_OBSERVED",
        "OFFICIAL_DAY_CANDLE",
        "NSE_SETTLEMENT",
        "LAST_VALID_FALLBACK"
    ])
    allow_provider_correction: bool = True
    market_state_required: str = "CLOSED"
    validation_window_seconds: int = 300

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SessionIntegrityEnvelope:
    schema_name: str = "SESSION_INTEGRITY_ENVELOPE"
    schema_version: str = "1.1.0"
    session_date: str = ""
    session_type: str = "REGULAR_TRADING"
    finalization_status: str = "PENDING"
    completeness_status: str = "FULL_SESSION"
    broker_auth_state_at_close: str = "AUTHENTICATED"
    websocket_state_at_close: str = "CONNECTED"
    market_feed_state_at_close: str = "HEALTHY"
    last_valid_nifty_tick_at: Optional[str] = None
    last_valid_options_at: Optional[str] = None
    last_valid_breadth_at: Optional[str] = None
    last_valid_vix_at: Optional[str] = None
    feed_gap_count: int = 0
    total_feed_gap_seconds: float = 0.0
    longest_feed_gap_seconds: float = 0.0
    degraded_intervals: List[Dict[str, Any]] = field(default_factory=list)
    unrecoverable_intervals: List[Dict[str, Any]] = field(default_factory=list)
    reconciliation: Dict[str, Any] = field(default_factory=lambda: {
        "reconciliation_status": "PENDING",
        "reconciliation_policy_version": "v1.0-standard",
        "reconciliation_completed_at": "",
        "sources_used": [],
        "observed_close": None,
        "provider_settled_close": None,
        "drift_points": 0.0
    })
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionIntegrityEnvelope":
        if not data:
            return cls()
        return cls(
            schema_name=data.get("schema_name", "SESSION_INTEGRITY_ENVELOPE"),
            schema_version=data.get("schema_version", "1.1.0"),
            session_date=data.get("session_date", ""),
            session_type=data.get("session_type", "REGULAR_TRADING"),
            finalization_status=data.get("finalization_status", "PENDING"),
            completeness_status=data.get("completeness_status", "FULL_SESSION"),
            broker_auth_state_at_close=data.get("broker_auth_state_at_close", "AUTHENTICATED"),
            websocket_state_at_close=data.get("websocket_state_at_close", "CONNECTED"),
            market_feed_state_at_close=data.get("market_feed_state_at_close", "HEALTHY"),
            last_valid_nifty_tick_at=data.get("last_valid_nifty_tick_at"),
            last_valid_options_at=data.get("last_valid_options_at"),
            last_valid_breadth_at=data.get("last_valid_breadth_at"),
            last_valid_vix_at=data.get("last_valid_vix_at"),
            feed_gap_count=data.get("feed_gap_count", 0),
            total_feed_gap_seconds=data.get("total_feed_gap_seconds", 0.0),
            longest_feed_gap_seconds=data.get("longest_feed_gap_seconds", 0.0),
            degraded_intervals=data.get("degraded_intervals") or [],
            unrecoverable_intervals=data.get("unrecoverable_intervals") or [],
            reconciliation=data.get("reconciliation") or {},
            warnings=data.get("warnings") or []
        )


@dataclass
class LatestCanonicalRecoverySnapshot:
    schema_name: str = "LATEST_CANONICAL_RECOVERY_SNAPSHOT"
    schema_version: str = "1.1.0"
    runtime_id: str = ""
    state_sequence: int = 0
    generated_at: str = ""
    session_date: str = ""
    market_session_phase: str = ""
    state: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LatestCanonicalRecoverySnapshot":
        if not data:
            return cls()
        return cls(
            schema_name=data.get("schema_name", "LATEST_CANONICAL_RECOVERY_SNAPSHOT"),
            schema_version=data.get("schema_version", "1.1.0"),
            runtime_id=data.get("runtime_id", ""),
            state_sequence=data.get("state_sequence", 0),
            generated_at=data.get("generated_at", ""),
            session_date=data.get("session_date", ""),
            market_session_phase=data.get("market_session_phase", ""),
            state=data.get("state") or {}
        )
