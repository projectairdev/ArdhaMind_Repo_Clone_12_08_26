# src/models/news_context_v2.py
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ProviderHealth:
    provider_name: str
    status: str                  # "ready", "degraded", "stale", "unavailable", "blocked"
    last_successful_fetch: Optional[str] = None
    last_attempted_fetch: Optional[str] = None
    item_count: int = 0
    error_count: int = 0
    operational_error_reason: Optional[str] = None  # "timeout", "rate_limited", "parse_error", "connection_error"
    failure_detail: Optional[str] = None
    next_retry_at: Optional[str] = None
    is_enabled: bool = True
    raw_item_count: int = 0
    normalized_item_count: int = 0
    unique_item_count: int = 0
    event_cluster_count: int = 0
    discovery_streams: List[str] = field(default_factory=list)
    rate_limit_state: str = "READY"
    coverage_regions: List[str] = field(default_factory=list)
    scheduled_record_count: int = 0
    released_record_count: int = 0
    next_scheduled_event: Optional[str] = None
    latest_fetch_status: str = "NOT_ATTEMPTED"
    serving_mode: str = "NO_DATA"
    data_status: str = "UNAVAILABLE"
    cached_last_valid: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NewsItem:
    id: str
    headline: str
    summary_snippet: str
    source_name: str
    source_type: str            # "official", "media", "social", "unknown"
    original_url: str
    discovery_url: str
    discovered_via: str         # e.g., "google_news_rss"
    provider_id: str
    published_at: str
    received_at: str
    age_seconds: int
    freshness_status: str       # "fresh", "stale", "unavailable"
    quality_status: str         # "high", "medium", "low"
    verification_status: str    # "confirmed", "developing", "unverified", "unavailable"
    category: str
    event_type: str
    affected_symbols: List[str]
    affected_sectors: List[str]
    nifty_relevance_score: float
    expected_direction: str     # "positive", "negative", "mixed", "uncertain", "not_assessed"
    impact_strength: str        # "high", "medium", "low"
    impact_duration: str        # "intraday", "daily", "weekly"
    confidence: float
    discovery_query: str = ""
    discovery_category: str = "Other"
    why_it_matters: str = ""
    assessment_reasons: List[str] = field(default_factory=list)
    rule_version: str = ""
    duplicate_group_id: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None
    canonical_event_category: str = ""
    source_authority: str = ""
    source_reference: str = ""
    official_subcategory: str = ""
    publisher: str = ""
    source_tier: str = "TIER_D_DISCOVERY"
    discovery_stream: str = ""
    language: str = "en"
    related_countries: List[str] = field(default_factory=list)
    affected_channels: List[str] = field(default_factory=list)
    recency_state: str = "STALE"
    priority_score: float = 0.0
    updated_at: str = ""
    normalized_timestamp: str = ""
    timestamp_source: str = "published_at"
    timestamp_validity: str = "VALID"
    timestamp_confidence: str = "HIGH"
    temporal_class: str = "CURRENT"
    canonical_eligible: bool = True
    workspace_eligible: bool = True
    cache_restored: bool = False
    age_minutes: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScheduledEvent:
    id: str
    event_name: str
    description: str
    scheduled_at: str
    importance: str             # "low", "medium", "high", "critical"
    source_name: str
    verification_status: str    # "confirmed", "developing", "unverified", "unavailable"
    category: str
    expected_direction: str     # "positive", "negative", "mixed", "uncertain", "not_assessed"
    relevance_score: float
    status: str                 # "upcoming", "completed"
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CorporateAnnouncement:
    id: str
    company_symbol: str
    announcement_type: str      # "earnings", "dividend", "board_meeting", "action", "filing", "other"
    headline: str
    description: str
    published_at: str
    source_name: str
    original_url: str
    verification_status: str    # "confirmed", "developing", "unverified", "unavailable"
    nifty_relevance_score: float
    expected_direction: str     # "positive", "negative", "mixed", "uncertain", "not_assessed"
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EventCluster:
    event_cluster_id: str
    canonical_headline: str
    category: str
    first_seen: str
    last_updated: str
    article_count: int
    publishers: List[str]
    primary_sources: List[str]
    related_countries: List[str]
    related_symbols: List[str]
    verification_strength: str
    nifty_relevance: float
    impact_level: str
    expected_direction: str
    reasoning: str
    affected_channels: List[str] = field(default_factory=list)
    article_ids: List[str] = field(default_factory=list)
    discovery_streams: List[str] = field(default_factory=list)
    recency_state: str = "STALE"
    priority_score: float = 0.0
    economic_event_id: Optional[str] = None
    latest_article_published_at: str = ""
    current_article_count: int = 0
    historical_article_count: int = 0
    temporal_class: str = "CURRENT"
    canonical_eligible: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NewsContext:
    scanned_at: str
    items: List[NewsItem] = field(default_factory=list)
    top_headlines: List[NewsItem] = field(default_factory=list)
    high_impact_items: List[NewsItem] = field(default_factory=list)
    corporate_items: List[CorporateAnnouncement] = field(default_factory=list)
    event_items: List[ScheduledEvent] = field(default_factory=list)
    provider_health: Dict[str, Any] = field(default_factory=dict)
    freshness: str = "unavailable"
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    generated_at: str = ""
    usable: bool = True
    source: str = "canonical_news_service"
    event_clusters: List[EventCluster] = field(default_factory=list)
    coverage_matrix: List[Dict[str, Any]] = field(default_factory=list)
    coverage_status: str = "UNAVAILABLE"
    raw_article_count: int = 0
    normalized_article_count: int = 0
    unique_article_count: int = 0
    duplicate_article_count: int = 0
    ingestion_metrics: Dict[str, Any] = field(default_factory=dict)
    historical_items: List[NewsItem] = field(default_factory=list)
    historical_event_clusters: List[EventCluster] = field(default_factory=list)
    temporal_diagnostics: Dict[str, Any] = field(default_factory=dict)
    last_market_close_boundary: str = ""
    current_window_hours: int = 24

    @property
    def payload(self) -> dict[str, Any]:
        return {
            "section_status": "ready" if self.usable else "unavailable",
            "items": [item.to_dict() for item in self.items],
            "top_headlines": [item.to_dict() for item in self.top_headlines],
            "high_impact_items": [item.to_dict() for item in self.high_impact_items],
            "corporate_items": [item.to_dict() for item in self.corporate_items],
            "event_items": [item.to_dict() for item in self.event_items],
            "provider_health": self.provider_health,
            "freshness": self.freshness,
            "warnings": self.warnings,
            "errors": self.errors,
            "generated_at": self.generated_at or self.scanned_at,
            "event_clusters": [cluster.to_dict() if hasattr(cluster, "to_dict") else cluster for cluster in self.event_clusters],
            "coverage_matrix": self.coverage_matrix,
            "coverage_status": self.coverage_status,
            "raw_article_count": self.raw_article_count,
            "normalized_article_count": self.normalized_article_count,
            "unique_article_count": self.unique_article_count,
            "duplicate_article_count": self.duplicate_article_count,
              "ingestion_metrics": self.ingestion_metrics,
              "historical_items": [item.to_dict() if hasattr(item, "to_dict") else item for item in self.historical_items],
              "historical_event_clusters": [cluster.to_dict() if hasattr(cluster, "to_dict") else cluster for cluster in self.historical_event_clusters],
              "temporal_diagnostics": self.temporal_diagnostics,
              "last_market_close_boundary": self.last_market_close_boundary,
              "current_window_hours": self.current_window_hours,
          }

# Legacy Compatibility Definitions
from enum import Enum

class EventSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass(frozen=True)
class AffectedIndex:
    index_name: str
    impact_direction: str
    impact_score: float

@dataclass(frozen=True)
class AffectedSector:
    sector_name: str
    impact_direction: str
    impact_score: float

@dataclass(frozen=True)
class AffectedMarket:
    market_name: str
    impact_direction: str
    impact_score: float

@dataclass(frozen=True)
class MarketImpact:
    expected_direction: str
    time_horizon: str
    market_impact_description: str
    impact_score: float = 0.0
    affected_indices: List[AffectedIndex] = field(default_factory=list)
    affected_sectors: List[AffectedSector] = field(default_factory=list)
    affected_markets: List[AffectedMarket] = field(default_factory=list)

@dataclass(frozen=True)
class NewsArticle:
    article_id: str
    title: str
    content: str
    source: str
    published_at: str
    url: str
    entities: List[str] = field(default_factory=list)
    classification: str = "Macro Economy"
    severity: EventSeverity = EventSeverity.LOW
    impact: Optional[MarketImpact] = None
    confidence_score: float = 1.0

@dataclass(frozen=True)
class NewsEvent:
    event_id: str
    title: str
    description: str
    event_type: str
    severity: EventSeverity
    status: str
    scheduled_time: Optional[str] = None
    impact: Optional[MarketImpact] = None
    sources: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class NewsSummary:
    market_summary: str = ""
    key_takeaways: List[str] = field(default_factory=list)
    critical_alerts: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class NewsStatistics:
    total_articles: int = 0
    severity_distribution: Dict[str, int] = field(default_factory=dict)
    classification_distribution: Dict[str, int] = field(default_factory=dict)
    sentiment_score: float = 0.0

@dataclass
class NewsContextV2:
    scanned_at: str
    current_events: List[NewsEvent] = field(default_factory=list)
    upcoming_events: List[NewsEvent] = field(default_factory=list)
    critical_alerts: List[NewsEvent] = field(default_factory=list)
    overnight_events: List[NewsEvent] = field(default_factory=list)
    market_summary: NewsSummary = field(default_factory=NewsSummary)
    statistics: NewsStatistics = field(default_factory=NewsStatistics)
    articles: List[NewsArticle] = field(default_factory=list)
    usable: bool = True
    source: str = "news_engine_v1"
