from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

class EventSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass(frozen=True)
class AffectedIndex:
    index_name: str
    impact_direction: str  # "BULLISH", "BEARISH", "NEUTRAL"
    impact_score: float    # -1.0 to 1.0

@dataclass(frozen=True)
class AffectedSector:
    sector_name: str
    impact_direction: str  # "BULLISH", "BEARISH", "NEUTRAL"
    impact_score: float    # -1.0 to 1.0

@dataclass(frozen=True)
class AffectedMarket:
    market_name: str       # e.g., "INDIA", "GLOBAL"
    impact_direction: str  # "BULLISH", "BEARISH", "NEUTRAL"
    impact_score: float    # -1.0 to 1.0

@dataclass(frozen=True)
class MarketImpact:
    expected_direction: str         # "BULLISH", "BEARISH", "NEUTRAL"
    time_horizon: str               # "INTRADAY", "DAILY", "WEEKLY"
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
    event_type: str             # e.g., "Central Bank", "Inflation"
    severity: EventSeverity
    status: str                 # "CURRENT", "UPCOMING", "OVERNIGHT"
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
    sentiment_score: float = 0.0  # -1.0 to 1.0

@dataclass(frozen=True)
class NewsContext:
    scanned_at: str
    current_events: List[NewsEvent] = field(default_factory=list)
    upcoming_events: List[NewsEvent] = field(default_factory=list)
    critical_alerts: List[NewsEvent] = field(default_factory=list)
    overnight_events: List[NewsEvent] = field(default_factory=list)
    market_summary: NewsSummary = field(default_factory=NewsSummary)
    statistics: NewsStatistics = field(default_factory=NewsStatistics)
    articles: List[NewsArticle] = field(default_factory=list)
