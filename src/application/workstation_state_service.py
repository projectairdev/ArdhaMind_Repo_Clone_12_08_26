from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any

from src.application.data_quality_service import DataQualityService
from src.models.canonical_workstation_state import CanonicalWorkstationState, sanitize_read_only
from src.models.data_quality import FreshnessStatus, SectionStatus, ValueClassification
from src.models.decision_support import DecisionSupportReport


class WorkstationStateService:
    SCHEMA_VERSION = "2.0.0"
    _sequence = 0
    _lock = Lock()

    @classmethod
    def _next_sequence(cls) -> int:
        with cls._lock:
            cls._sequence += 1
            return cls._sequence

    @classmethod
    def build_from_legacy(cls, payload: dict[str, Any], *, broker_state: str = "DISCONNECTED",
                          market_state: str = "UNKNOWN", now: datetime | None = None) -> CanonicalWorkstationState:
        current = now or datetime.now(timezone.utc)
        generated = current.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        market_closed = str(market_state).upper() in {"CLOSED", "MARKET_CLOSED", "POST_MARKET"}
        expired = str(broker_state).upper() in {"SESSION_EXPIRED", "TOKEN_EXPIRED", "EXPIRED"}
        market = sanitize_read_only(payload.get("marketContext") or {})
        options = sanitize_read_only(payload.get("optionContext") or {})
        market_observed = cls._timestamp(market)
        option_observed = cls._timestamp(options)
        market_available = bool(market) and not expired
        option_available = bool(options) and not expired
        market_meta = DataQualityService.metadata("nifty_spot", "kite_market_feed", market_observed,
            instrument="NIFTY 50", generated_at=current, market_closed=market_closed,
            available=market_available,
            classification=ValueClassification.LIVE, now=current)
        option_meta = DataQualityService.metadata("option_aggregate", "kite_option_chain", option_observed,
            instrument="NIFTY options", generated_at=current, market_closed=market_closed,
            available=option_available, classification=ValueClassification.CALCULATED, now=current)
        market_status = cls._section(market_meta.freshness_status)
        option_status = cls._section(option_meta.freshness_status)
        news = sanitize_read_only(payload.get("newsSentiment") or {})
        news_status = SectionStatus.READY if news and news.get("status") != "UNAVAILABLE" else SectionStatus.UNAVAILABLE
        analytics_status = cls._dependent(market_status, [option_status, news_status])
        assistant_status = cls._dependent(market_status, [option_status])
        readiness = {
            "nifty_live": cls._ready("NIFTY Live", SectionStatus.READY, []),
            "pre_market_planner": cls._ready("Pre-Market Planner", market_status,
                [] if market_status in {SectionStatus.READY, SectionStatus.MARKET_CLOSED} else ["validated market snapshot"]),
            "todays_analysis": cls._ready("Today's Analysis", analytics_status,
                cls._reasons(market_status, option_status, news_status)),
            "news_updates": cls._ready("NEWS & UPDATES", news_status,
                [] if news_status == SectionStatus.READY else ["real news provider"]),
            "live_assistant": cls._ready("Live Assistant", assistant_status,
                cls._reasons(market_status, option_status)),
            "settings": cls._ready("Settings", SectionStatus.READY, []),
        }
        blockers = cls._reasons(market_status, option_status)
        support = DecisionSupportReport(
            market_interpretation="Validated analytical context" if not blockers else "Analytical context incomplete",
            current_scenario_status="market_closed" if market_closed else ("blocked" if blockers else "monitor"),
            required_confirmations=["validated NIFTY spot", "validated option aggregate"],
            missing_confirmations=blockers, blockers=blockers,
            warnings=["Live broker session requires reconnect"] if expired else [],
        )
        def section(name: str, status: SectionStatus, fallback: Any = None) -> dict[str, Any]:
            value = sanitize_read_only(payload.get(name) or fallback or {})
            if isinstance(value, dict):
                return {**value, "status": status.value}
            return {"status": status.value, "value": value}
        return CanonicalWorkstationState(
            cls.SCHEMA_VERSION, cls._next_sequence(), generated,
            {"status": "closed" if market_closed else str(market_state).lower(), "is_closed": market_closed},
            {"status": "degraded" if expired else "ready", "read_only": True},
            {"status": "session_expired" if expired else str(broker_state).lower(),
             "reconnect_required": expired, "last_successful_update": market_observed},
            {"status": market_status.value, "source": "kite_market_feed"},
            section("marketContext", market_status), section("technicalAnalysis", market_status),
            section("optionContext", option_status), section("marketScore", market_status),
            section("opportunityContext", market_status), section("strategyEvaluation", assistant_status),
            sanitize_read_only(payload.get("tradeScenarios") or []),
            section("confidenceReport", assistant_status), section("riskReport", market_status),
            sanitize_read_only(payload.get("decisionReport") or support.to_dict()), section("explanationReport", assistant_status),
            section("newsSentiment", news_status), None, section("operationsReport", SectionStatus.READY),
            readiness, {"market_data": market_meta.to_dict(), "option_intelligence": option_meta.to_dict()},
            warnings=support.warnings, errors=[],
        )

    @staticmethod
    def _timestamp(section: dict[str, Any]) -> Any:
        for key in ("observed_at", "observedAt", "timestamp", "lastUpdated", "generated_at", "generatedAt"):
            if section.get(key):
                return section[key]
        return None

    @staticmethod
    def _section(freshness: FreshnessStatus) -> SectionStatus:
        return {FreshnessStatus.FRESH: SectionStatus.READY, FreshnessStatus.STALE: SectionStatus.DEGRADED,
                FreshnessStatus.BLOCKED: SectionStatus.BLOCKED,
                FreshnessStatus.UNAVAILABLE: SectionStatus.UNAVAILABLE,
                FreshnessStatus.MARKET_CLOSED: SectionStatus.MARKET_CLOSED}[freshness]

    @staticmethod
    def _dependent(required: SectionStatus, optional: list[SectionStatus]) -> SectionStatus:
        if required in {SectionStatus.BLOCKED, SectionStatus.UNAVAILABLE}:
            return SectionStatus.BLOCKED
        if required == SectionStatus.MARKET_CLOSED:
            return SectionStatus.MARKET_CLOSED
        return SectionStatus.DEGRADED if any(x != SectionStatus.READY for x in optional) else SectionStatus.READY

    @staticmethod
    def _reasons(*statuses: SectionStatus) -> list[str]:
        names = ("validated market context", "option-chain aggregate", "real news provider")
        return [names[i] for i, status in enumerate(statuses)
                if status in {SectionStatus.BLOCKED, SectionStatus.UNAVAILABLE}]

    @staticmethod
    def _ready(name: str, status: SectionStatus, reasons: list[str]) -> dict[str, Any]:
        return {"workspace": name, "status": status.value,
                "accessible": name in {"NIFTY Live", "Settings"} or status not in {SectionStatus.BLOCKED, SectionStatus.UNAVAILABLE},
                "dependency_reasons": reasons}
