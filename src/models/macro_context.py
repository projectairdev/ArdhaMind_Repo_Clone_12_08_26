# src/models/macro_context.py
"""
Canonical Domain Models for Macro & External Market Intelligence.

Covers:
  - Global Indices (GIFT Nifty, S&P 500, Nasdaq, Dow Jones, Nikkei 225, Hang Seng)
  - Commodities & Forex (Brent Crude, Gold, USD/INR, DXY, US 10Y Yield)
  - Institutional Flows (FII/DII Cash, Futures, Options)
  - Calendars (Economic Events, Corporate Actions, Earnings, IPOs)
  - Versioned NIFTY 50 Constituent Metadata & Weights
  - Domain-specific Freshness & Provider Health
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MarketQuote:
    """Canonical model for global indices, commodities, forex, and yields."""
    symbol: str
    name: str
    category: str  # GLOBAL_INDEX | COMMODITY | FOREX | YIELD
    price: float
    change: float
    change_pct: float
    currency: str
    source_name: str
    source_attribution: str
    retrieved_at: str
    published_at: str
    freshness_status: str  # fresh | stale | unavailable
    source_symbol: str = ""
    provider_symbol: str = ""
    observation_timestamp: str = ""
    exchange: str = "UNKNOWN"
    exchange_timezone: str = "UTC"
    instrument_type: str = "UNKNOWN"
    source_session: str = "UNKNOWN"
    reference_value: Optional[float] = None
    reference_type: str = ""
    reference_timestamp: str = ""
    change_source: str = ""
    observation_mode: str = "LAST_VALID_SOURCE_OBSERVATION"
    cache_restored: bool = False
    status: str = "UNAVAILABLE"
    current_eligible: bool = False
    age_seconds: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result.update({
            "display_name": self.name,
            "value": self.price,
            "unit": self.currency,
            "source": self.source_name,
            "provider": self.source_name,
            "freshness": self.freshness_status,
        })
        return result


@dataclass
class InstitutionalFlowItem:
    """Canonical model for FII/DII daily cash, futures, and options activity."""
    dataset_type: str  # FII_CASH | DII_CASH | FII_FUTURES | FII_OPTIONS
    date: str
    buy_value: float
    sell_value: float
    net_value: float
    currency: str
    source_name: str
    source_attribution: str
    retrieved_at: str
    freshness_status: str
    source_authority: str = "PRIMARY"
    source_url: str = ""
    observation_mode: str = "LATEST_AVAILABLE_TRADING_SESSION"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ParticipantDerivativeRecord:
    """One official participant/category derivatives observation in contracts."""
    dataset_type: str
    trade_date: str
    participant_type: str
    instrument_category: str
    long_contracts: int
    short_contracts: int
    net_position: int
    unit: str
    source: str
    source_authority: str
    source_url: str
    retrieved_at: str
    record_timestamp: str
    freshness: str
    status: str
    observation_mode: str = "LATEST_AVAILABLE_TRADING_SESSION"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RiskFreeRateRecord:
    """Verified INR risk-free-rate observation used by the IV engine."""
    status: str
    rate: Optional[float]
    rate_pct: Optional[float]
    tenor: str
    source: str
    source_authority: str
    source_url: str
    observation_date: Optional[str]
    retrieved_at: str
    freshness: str
    observation_mode: str = "LATEST_RBI_PUBLISHED_RATE"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EconomicCalendarEvent:
    """Canonical model for macroeconomic calendar announcements."""
    event_id: str
    country: str
    event_name: str
    actual: Optional[str]
    forecast: Optional[str]
    previous: Optional[str]
    scheduled_at: str
    impact_level: str  # high | medium | low
    source_name: str
    source_attribution: str
    retrieved_at: str
    freshness_status: str
    provider_event_id: str = ""
    canonical_event_name: str = ""
    region: str = ""
    currency: str = ""
    category: str = ""
    scheduled_at_original: str = ""
    source_timezone: str = "UTC"
    scheduled_at_ist: str = ""
    unit: Optional[str] = None
    source: str = ""
    source_authority: str = "DISCOVERY"
    source_url: str = ""
    status: str = "SCHEDULED"
    last_updated: str = ""
    nifty_relevance: float = 0.0
    affected_channels: List[str] = field(default_factory=list)
    reasoning: str = ""
    release_period: str = ""
    provider_provenance: List[Dict[str, Any]] = field(default_factory=list)
    surprise_direction: str = "NOT_APPLICABLE"
    surprise_absolute: Optional[float] = None
    surprise_percentage: Optional[float] = None
    market_interpretation: str = "UNCERTAIN"
    refresh_window: str = "NORMAL"
    session_timing: str = "AFTER_CLOSE"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CorporateActionRecord:
    """Canonical model for corporate actions (dividends, splits, bonuses)."""
    id: str
    symbol: str
    company_name: str
    action_type: str  # DIVIDEND | SPLIT | BONUS | RIGHTS
    ex_date: str
    record_date: str
    details: str
    source_name: str
    source_attribution: str
    retrieved_at: str
    freshness_status: str
    source_authority: str = "PRIMARY"
    source_url: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EarningsRecord:
    """Canonical model for corporate earnings announcements."""
    id: str
    symbol: str
    company_name: str
    period: str
    announcement_date: str
    status: str  # UPCOMING | ANNOUNCED
    source_name: str
    source_attribution: str
    retrieved_at: str
    freshness_status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IpoRecord:
    """Canonical model for initial public offerings."""
    id: str
    company_name: str
    symbol: str
    issue_start: str
    issue_close: str
    price_band: str
    lot_size: int
    status: str  # UPCOMING | OPEN | CLOSED
    source_name: str
    source_attribution: str
    retrieved_at: str
    freshness_status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NiftyConstituentItem:
    """Canonical model for a single NIFTY constituent stock."""
    symbol: str
    company_name: str
    sector: str
    weight_pct: Optional[float] = None
    isin: str = ""
    effective_from: str = ""
    effective_to: str = ""
    metadata_version: str = ""
    source: str = ""
    retrieved_at: str = ""
    resolution_status: str = "UNAVAILABLE"
    kite_trading_symbol: str = ""
    kite_instrument_token: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NiftyConstituentMetadata:
    """Versioned NIFTY 50 constituent metadata & weights container."""
    metadata_version: str
    effective_from: str
    retrieved_at: str
    verified_source: str
    source_attribution: str
    is_available: bool
    constituents: List[NiftyConstituentItem] = field(default_factory=list)
    weights_status: str = "UNAVAILABLE"
    weights_reason: str = ""
    effective_date_status: str = "UNAVAILABLE"
    source_url: str = ""
    source_authority: str = "PRIMARY"
    resolution_count: int = 0
    effective_snapshot_date: str = ""
    reconstitution: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["constituents"] = [c.to_dict() if hasattr(c, "to_dict") else c for c in self.constituents]
        return res


@dataclass
class MacroContext:
    """
    Unified Macro Intelligence Context.
    Combines global market quotes, commodities, forex, yields, institutional flows,
    calendars, and NIFTY constituent metadata into a validated atomic snapshot.
    """
    scanned_at: str
    generated_at: str
    quotes: Dict[str, MarketQuote] = field(default_factory=dict)
    institutional_flows: List[InstitutionalFlowItem] = field(default_factory=list)
    economic_events: List[EconomicCalendarEvent] = field(default_factory=list)
    corporate_actions: List[CorporateActionRecord] = field(default_factory=list)
    earnings_events: List[EarningsRecord] = field(default_factory=list)
    ipo_events: List[IpoRecord] = field(default_factory=list)
    constituent_metadata: Optional[NiftyConstituentMetadata] = None
    corporate_announcements: List[Dict[str, Any]] = field(default_factory=list)
    board_meetings: List[Dict[str, Any]] = field(default_factory=list)
    official_india_events: List[Dict[str, Any]] = field(default_factory=list)
    additional_institutional_flows: List[Dict[str, Any]] = field(default_factory=list)
    dataset_health: List[Dict[str, Any]] = field(default_factory=list)
    provider_health: Dict[str, Any] = field(default_factory=dict)
    calendar_provider_health: Dict[str, Any] = field(default_factory=dict)
    calendar_coverage: str = "UNAVAILABLE"
    calendar_metrics: Dict[str, Any] = field(default_factory=dict)
    domain_freshness: Dict[str, str] = field(default_factory=dict)
    quote_status: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    ingestion_metrics: Dict[str, Any] = field(default_factory=dict)
    workspace_context: Dict[str, Any] = field(default_factory=dict)
    institutional_derivatives: Dict[str, Any] = field(default_factory=dict)
    india_vix: Dict[str, Any] = field(default_factory=dict)
    risk_free_rate: Optional[Dict[str, Any]] = None
    provider_contracts: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    usable: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scanned_at": self.scanned_at,
            "generated_at": self.generated_at,
            "quotes": {k: v.to_dict() if hasattr(v, "to_dict") else v for k, v in self.quotes.items()},
            "institutional_flows": [f.to_dict() if hasattr(f, "to_dict") else f for f in self.institutional_flows],
            "economic_events": [e.to_dict() if hasattr(e, "to_dict") else e for e in self.economic_events],
            "corporate_actions": [c.to_dict() if hasattr(c, "to_dict") else c for c in self.corporate_actions],
            "earnings_events": [e.to_dict() if hasattr(e, "to_dict") else e for e in self.earnings_events],
            "ipo_events": [i.to_dict() if hasattr(i, "to_dict") else i for i in self.ipo_events],
            "constituent_metadata": self.constituent_metadata.to_dict() if self.constituent_metadata and hasattr(self.constituent_metadata, "to_dict") else None,
            "corporate_announcements": self.corporate_announcements,
            "board_meetings": self.board_meetings,
            "official_india_events": self.official_india_events,
            "additional_institutional_flows": self.additional_institutional_flows,
            "dataset_health": self.dataset_health,
            "provider_health": self.provider_health,
            "calendar_provider_health": self.calendar_provider_health,
            "calendar_coverage": self.calendar_coverage,
            "calendar_metrics": self.calendar_metrics,
            "domain_freshness": self.domain_freshness,
            "quote_status": self.quote_status,
            "ingestion_metrics": self.ingestion_metrics,
            "workspace_context": self.workspace_context,
            "institutional_derivatives": self.institutional_derivatives,
            "india_vix": self.india_vix,
            "risk_free_rate": self.risk_free_rate,
            "provider_contracts": self.provider_contracts,
            "errors": self.errors,
            "warnings": self.warnings,
            "usable": self.usable,
        }
