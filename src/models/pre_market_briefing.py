# src/models/pre_market_briefing.py
"""
Pre-Market Briefing Domain Model for AIR ArdhaMind.

Represents an immutable 08:50 AM IST pre-market briefing artifact that permanently
preserves morning forecast telemetry, evidence, trade playbooks, and post-market validation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class GiftSnapshot:
    value: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    observed_at: str = "Unavailable"
    checked_at: str = "Unavailable"
    freshness: str = "UNAVAILABLE"  # FRESH | RECENT | LAST_VALID | PENDING | UNAVAILABLE | STALE
    provider: str = "NSE International Exchange"
    session: str = "Current Pre-Open Session"
    availability_status: str = "UNAVAILABLE"  # FRESH | RECENT | LAST_VALID | PENDING | UNAVAILABLE | STALE
    methodology: str = "GIFT_ANCHORED"  # GIFT_ANCHORED | EVIDENCE_SCORE_FALLBACK


@dataclass
class MarketCommandCenter:
    nifty_reference_close: Optional[float]
    gift_nifty_price: Optional[float]
    implied_gap_points: Optional[float]
    implied_gap_percent: Optional[float]
    expected_open_low: Optional[float]
    expected_open_high: Optional[float]
    expected_open_str: str
    expected_gap_str: str
    opening_bias: str
    setup_score: float
    confidence_pct: int
    confidence_label: str
    risk_level: str
    india_vix: Optional[float]
    vix_change_pct: Optional[float]
    institutional_tone: str
    global_market_tone: str
    bank_nifty_ref: Optional[float]
    bank_nifty_tone: str
    finnifty_ref: Optional[float]
    finnifty_tone: str
    sensex_ref: Optional[float]
    sensex_tone: str
    overall_summary_why: List[str]
    gift_freshness: str = "FRESH"
    gift_observed_at: str = "08:45 IST"
    gift_availability_status: str = "FRESH"
    gap_methodology: str = "GIFT_ANCHORED"


@dataclass
class TrafficLightItem:
    category: str  # GLOBAL | GIFT_NIFTY | INSTITUTIONAL | VOLATILITY | OPTIONS | BREADTH_CARRY | NEWS_RISK | OVERALL
    status: str    # GREEN | AMBER | RED
    label: str
    reason: str
    source: str


@dataclass
class GlobalMarketItem:
    symbol: str
    name: str
    category: str
    price: Optional[float]
    change: Optional[float]
    change_pct: Optional[float]
    session_status: str
    observed_at: str
    freshness: str
    provider: str
    directional_implication: str  # POSITIVE | NEGATIVE | NEUTRAL


@dataclass
class SectorOutlookItem:
    sector: str
    previous_change_pct: Optional[float]
    morning_outlook: str  # BULLISH | CAUTIOUS | NEUTRAL | BEARISH
    catalyst: str
    reason: str


@dataclass
class HeavyweightItem:
    symbol: str
    weight_pct: float
    sector: str
    previous_close: Optional[float]
    previous_change_pct: Optional[float]
    morning_cue: str  # POSITIVE | CAUTIOUS | NEUTRAL | NEGATIVE
    catalyst: str
    reason: str


@dataclass
class StockToWatchItem:
    symbol: str
    sector: str
    catalyst_type: str  # NEWS | EARNINGS | TECHNICAL | INSTITUTIONAL | CORPORATE
    headline_or_reason: str
    bias: str  # POSITIVE | NEGATIVE | WATCH
    source: str


@dataclass
class NewsBriefingItem:
    id: str
    headline: str
    publisher: str
    published_at: str
    source_url: str
    relevance_score: float
    affected_sectors: List[str]
    impact_level: str  # HIGH | MEDIUM | LOW
    expected_direction: str  # POSITIVE | NEGATIVE | NEUTRAL


@dataclass
class CalendarEventItem:
    time_ist: str
    event_name: str
    country: str
    importance: str  # HIGH | MEDIUM | LOW
    expected_impact: str
    affected_sector: str
    source: str


@dataclass
class OpeningScenarioItem:
    name: str  # BULLISH | BEARISH | RANGE
    title: str
    condition_if: List[str]
    outcome_then: str
    entry_condition: str
    confirmation_rules: List[str]
    target_levels: List[str]
    invalidation_level: str
    risk_note: str


@dataclass
class TradePlaybookSetup:
    setup_code: str  # SETUP_A | SETUP_B | SETUP_C
    name: str
    bias: str
    why_today: str
    entry_trigger: str
    confirmation_required: str
    stop_invalidation: str
    profit_targets: str
    risk_grade: str


@dataclass
class OnePageTradeCard:
    morning_view: str
    expected_open: str
    expected_gap: str
    key_resistance: str
    key_support: str
    decision_corridor: str
    vix_summary: str
    pcr_summary: str
    max_pain: str
    call_wall: str
    put_wall: str
    fii_net: str
    dii_net: str
    global_tone: str
    primary_sector_focus: str
    primary_risk: str
    first_thing_to_watch: str
    best_action_at_open: str


@dataclass
class ActualSessionCapture:
    actual_open: Optional[float] = None
    actual_open_time: Optional[str] = None
    actual_gap_points: Optional[float] = None
    actual_gap_percent: Optional[float] = None
    open_inside_expected_range: Optional[bool] = None
    actual_high: Optional[float] = None
    actual_low: Optional[float] = None
    actual_close: Optional[float] = None
    actual_session_change: Optional[float] = None
    actual_session_change_pct: Optional[float] = None
    actual_session_range: Optional[float] = None
    actual_breadth_adv: Optional[int] = None
    actual_breadth_dec: Optional[int] = None
    actual_breadth_unch: Optional[int] = None
    actual_vix_close: Optional[float] = None
    actual_sector_leaders: List[str] = field(default_factory=list)
    actual_sector_laggards: List[str] = field(default_factory=list)


@dataclass
class ValidationCriterion:
    criterion_name: str
    forecast_value: str
    actual_value: str
    status: str  # HIT | NEAR_HIT | PARTIAL | MISS | NOT_TESTED | UNVERIFIABLE
    points_awarded: float
    max_points: float
    explanation: str


@dataclass
class PostMarketValidation:
    validation_status: str = "PENDING"  # PENDING | IN_PROGRESS | VALIDATED
    validated_at: Optional[str] = None
    overall_accuracy_score_pct: Optional[float] = None
    criteria: List[ValidationCriterion] = field(default_factory=list)
    summary_verdict: str = ""


@dataclass
class PreMarketBriefingReport:
    report_id: str
    report_version: str
    trading_date: str
    generated_at: str
    frozen_at: str
    evidence_cutoff_at: str
    status: str  # PREPARING | READY | FROZEN | MARKET_OPEN | VALIDATING | SESSION_COMPLETE | VALIDATED
    reference_session_date: str
    reference_close: float
    source_state_sequence: int
    runtime_id: str
    generated_late: bool

    command_center: MarketCommandCenter
    traffic_lights: List[TrafficLightItem]
    global_snapshot: List[GlobalMarketItem]
    global_cue_interpretation: Dict[str, Any]
    gift_dashboard: Dict[str, Any]
    price_structure: Dict[str, Any]
    options_intelligence: Dict[str, Any]
    institutional_positioning: Dict[str, Any]
    volatility_and_risk: Dict[str, Any]
    breadth_carry: Dict[str, Any]
    sector_scoreboard: List[SectorOutlookItem]
    heavyweights: List[HeavyweightItem]
    stocks_to_watch: List[StockToWatchItem]
    news_highlights: List[NewsBriefingItem]
    event_calendar: List[CalendarEventItem]
    overnight_risk: List[Dict[str, Any]]
    opening_bias_analysis: Dict[str, Any]
    opening_scenarios: List[OpeningScenarioItem]
    first_30m_plan: Dict[str, Any]
    trade_playbook: List[TradePlaybookSetup]
    one_page_trade_card: OnePageTradeCard
    provenance: Dict[str, Any]

    actual_session: ActualSessionCapture = field(default_factory=ActualSessionCapture)
    post_market_validation: PostMarketValidation = field(default_factory=PostMarketValidation)
    validation_preview: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
