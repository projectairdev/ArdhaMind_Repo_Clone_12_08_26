"""Canonical E3 economic-calendar compilation and persistence.

The pipeline is intentionally separate from corporate calendars.  It accepts
only timezone-aware release times, merges discovery rows into official anchors,
and never treats a passed schedule as proof that a release occurred.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo

from src.models.macro_context import EconomicCalendarEvent
from src.news_engine.economic_calendar_provider import (
    BaseEconomicCalendarProvider,
    BojReleaseCalendarProvider,
    EcbWeeklyCalendarProvider,
    FederalReserveCalendarProvider,
    MospiReleaseCalendarProvider,
    OfficialIcsCalendarProvider,
    TradingEconomicsCalendarProvider,
    TradingViewCalendarProvider,
)


CACHE_FILE_PATH = Path(".cache") / "economic_calendar_cache.json"
IST = ZoneInfo("Asia/Kolkata")


CANONICAL_RULES: Sequence[Tuple[Tuple[str, ...], str, str]] = (
    (("core consumer price", "core cpi"), "CORE_CPI", "INFLATION"),
    (("consumer price", "cpi"), "CPI", "INFLATION"),
    (("producer price", "ppi", "wholesale price", "wpi"), "PPI", "INFLATION"),
    (("core pce",), "CORE_PCE", "INFLATION"),
    (("personal income and outlays", "pce price"), "PCE", "INFLATION"),
    (("employment situation", "nonfarm payroll", "non-farm payroll"), "NONFARM_PAYROLLS", "LABOUR"),
    (("unemployment rate",), "UNEMPLOYMENT_RATE", "LABOUR"),
    (("jobless claims",), "INITIAL_JOBLESS_CLAIMS", "LABOUR"),
    (("gross domestic product", "gdp"), "GDP", "GROWTH"),
    (("industrial production", "iip"), "INDUSTRIAL_PRODUCTION", "GROWTH"),
    (("retail sales",), "RETAIL_SALES", "GROWTH"),
    (("manufacturing pmi",), "MANUFACTURING_PMI", "SURVEY"),
    (("services pmi",), "SERVICES_PMI", "SURVEY"),
    (("pmi", "ism"), "PMI", "SURVEY"),
    (("trade balance", "international trade"), "TRADE_BALANCE", "EXTERNAL"),
    (("forex reserves", "foreign exchange reserves"), "FOREX_RESERVES", "EXTERNAL"),
    (("fiscal deficit",), "FISCAL_DEFICIT", "FISCAL"),
    (("core industries",), "CORE_INDUSTRIES", "GROWTH"),
    (("summary of opinions",), "BOJ_SUMMARY_OF_OPINIONS", "CENTRAL_BANK"),
    (("fomc", "federal reserve rate", "fed interest rate"), "FOMC_RATE_DECISION", "CENTRAL_BANK"),
    (("ecb", "european central bank rate"), "ECB_RATE_DECISION", "CENTRAL_BANK"),
    (("bank of england", "boe rate"), "BOE_RATE_DECISION", "CENTRAL_BANK"),
    (("bank of japan", "boj rate"), "BOJ_RATE_DECISION", "CENTRAL_BANK"),
    (("reserve bank of india", "rbi monetary policy", "repo rate"), "RBI_RATE_DECISION", "CENTRAL_BANK"),
    (("press conference",), "CENTRAL_BANK_PRESS_CONFERENCE", "CENTRAL_BANK"),
    (("bank lending",), "BANK_LENDING", "LIQUIDITY"),
    (("current account",), "CURRENT_ACCOUNT", "EXTERNAL"),
)


def _now(value: Optional[str | datetime]) -> datetime:
    if isinstance(value, datetime):
        result = value
    elif value:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    else:
        result = datetime.now(timezone.utc)
    return result if result.tzinfo else result.replace(tzinfo=timezone.utc)


def _parse_datetime(value: Any) -> Optional[datetime]:
    if not value or not isinstance(value, str) or "T" not in value:
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return result if result.tzinfo else None


def canonicalize_event_name(name: str, country: str = "") -> Tuple[str, str]:
    lowered = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
    for terms, canonical, category in CANONICAL_RULES:
        if any((re.search(rf"\b{re.escape(term)}\b", lowered) if len(term) <= 4 else term in lowered) for term in terms):
            # Generic policy wording is disambiguated with country provenance.
            if canonical == "CENTRAL_BANK_PRESS_CONFERENCE":
                prefix = {"India": "RBI", "United States": "FOMC", "Euro Area": "ECB",
                          "United Kingdom": "BOE", "Japan": "BOJ"}.get(country, "CENTRAL_BANK")
                canonical = f"{prefix}_PRESS_CONFERENCE"
            return canonical, category
    normalized = re.sub(r"[^A-Z0-9]+", "_", name.upper()).strip("_")[:80]
    return normalized or "UNCLASSIFIED_EVENT", "OTHER"


def classify_event(canonical: str, country: str, provider_importance: Any = None) -> Tuple[str, float, List[str], str]:
    region_direct = country == "India"
    critical = {"RBI_RATE_DECISION", "FOMC_RATE_DECISION"}
    high = {
        "CPI", "CORE_CPI", "PCE", "CORE_PCE", "NONFARM_PAYROLLS", "GDP",
        "ECB_RATE_DECISION", "BOE_RATE_DECISION", "BOJ_RATE_DECISION",
        "UNEMPLOYMENT_RATE", "INDUSTRIAL_PRODUCTION", "RETAIL_SALES",
    }
    medium = {"PPI", "INITIAL_JOBLESS_CLAIMS", "MANUFACTURING_PMI", "SERVICES_PMI", "PMI",
              "TRADE_BALANCE", "FOREX_RESERVES", "FISCAL_DEFICIT", "CORE_INDUSTRIES",
              "BOJ_SUMMARY_OF_OPINIONS", "BANK_LENDING", "CURRENT_ACCOUNT"}
    if canonical in critical:
        impact = "CRITICAL"
    elif canonical in high:
        impact = "HIGH"
    elif canonical in medium:
        impact = "MEDIUM"
    else:
        score = int(provider_importance or 0) if str(provider_importance or "").isdigit() else 0
        impact = "HIGH" if score >= 3 else "MEDIUM" if score == 2 else "LOW"
    if canonical == "RETAIL_SALES" and country not in {"India", "United States", "China"}:
        impact = "MEDIUM"

    channels: List[str] = []
    if canonical in {"RBI_RATE_DECISION", "FOMC_RATE_DECISION", "ECB_RATE_DECISION", "BOE_RATE_DECISION", "BOJ_RATE_DECISION"}:
        channels = ["RATES", "YIELDS", "LIQUIDITY", "GLOBAL_EQUITIES"]
    elif canonical in {"CPI", "CORE_CPI", "PPI", "PCE", "CORE_PCE"}:
        channels = ["INFLATION", "RATES", "YIELDS", "GLOBAL_EQUITIES"]
    elif canonical in {"GDP", "INDUSTRIAL_PRODUCTION", "RETAIL_SALES", "PMI", "MANUFACTURING_PMI", "SERVICES_PMI"}:
        channels = ["GROWTH", "GLOBAL_EQUITIES", "FOREIGN_FLOWS"]
    elif canonical in {"NONFARM_PAYROLLS", "UNEMPLOYMENT_RATE", "INITIAL_JOBLESS_CLAIMS"}:
        channels = ["RATES", "YIELDS", "GLOBAL_EQUITIES", "FOREIGN_FLOWS"]
    elif canonical in {"TRADE_BALANCE", "CURRENT_ACCOUNT", "FOREX_RESERVES"}:
        channels = ["INR", "FOREIGN_FLOWS"]
    else:
        channels = ["GLOBAL_EQUITIES"]
    if region_direct:
        for channel in ("INR", "BANKS"):
            if channel not in channels:
                channels.append(channel)
    relevance = {"CRITICAL": 9.5, "HIGH": 8.0, "MEDIUM": 5.5, "LOW": 3.0}[impact]
    if region_direct:
        relevance = min(10.0, relevance + 0.5)
    reasoning = f"{impact.title()} {canonical.replace('_', ' ').lower()}; NIFTY transmission through {', '.join(channels).lower()}."
    return impact, relevance, channels, reasoning


def _numeric(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(float(value)) else None
    match = re.search(r"[-+]?\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(match.group()) if match else None


def surprise(actual: Any, forecast: Any, unit: Any, canonical: str) -> Tuple[str, Optional[float], Optional[float], str]:
    a, f = _numeric(actual), _numeric(forecast)
    if a is None or f is None:
        return "NOT_APPLICABLE", None, None, "UNCERTAIN"
    delta = a - f
    tolerance = max(abs(f) * 0.001, 1e-9)
    direction = "INLINE" if abs(delta) <= tolerance else "ABOVE" if delta > 0 else "BELOW"
    pct = (delta / abs(f) * 100.0) if f != 0 else None
    interpretation = "UNCERTAIN"
    if direction == "INLINE":
        interpretation = "MIXED"
    elif canonical in {"GDP", "INDUSTRIAL_PRODUCTION", "RETAIL_SALES", "PMI", "MANUFACTURING_PMI", "SERVICES_PMI", "NONFARM_PAYROLLS"}:
        interpretation = "POSITIVE" if direction == "ABOVE" else "NEGATIVE"
    elif canonical in {"CPI", "CORE_CPI", "PPI", "PCE", "CORE_PCE", "UNEMPLOYMENT_RATE", "INITIAL_JOBLESS_CLAIMS"}:
        interpretation = "NEGATIVE" if direction == "ABOVE" else "POSITIVE"
    return direction, round(delta, 6), round(pct, 4) if pct is not None else None, interpretation


def event_status(scheduled: datetime, actual: Any, now: datetime, source_status: str = "") -> str:
    upper = source_status.upper()
    if "CANCEL" in upper:
        return "CANCELLED"
    if actual is not None and str(actual).strip() != "":
        return "RELEASED"
    seconds = (scheduled - now).total_seconds()
    if seconds > 86400:
        return "SCHEDULED"
    if seconds > 1800:
        return "UPCOMING"
    if seconds >= -7200:
        return "DUE" if seconds >= 0 else "DELAYED"
    return "STALE"


def refresh_window(scheduled: datetime, now: datetime, status: str) -> str:
    seconds = (scheduled - now).total_seconds()
    if status in {"STALE", "CANCELLED"}:
        return "NORMAL"
    if status in {"RELEASED", "DELAYED"} and seconds >= -7200:
        return "POST_RELEASE"
    if seconds > 7 * 86400:
        return "FAR_FUTURE"
    if seconds > 86400:
        return "NORMAL"
    if seconds > 1800:
        return "APPROACHING"
    return "DUE"


def session_timing(scheduled_ist: datetime) -> str:
    hour = scheduled_ist.hour + scheduled_ist.minute / 60
    if hour < 9.25:
        return "BEFORE_OPEN" if hour >= 5 else "OVERNIGHT"
    if hour <= 15.5:
        return "DURING_SESSION"
    if hour <= 23:
        return "AFTER_CLOSE"
    return "OVERNIGHT"


def normalize_event(item: Dict[str, Any], now: datetime) -> Optional[EconomicCalendarEvent]:
    scheduled = _parse_datetime(item.get("scheduled_at"))
    if scheduled is None:
        return None
    scheduled_ist = scheduled.astimezone(IST)
    name = str(item.get("event_name") or "").strip()
    country = str(item.get("country") or "").strip()
    if not name or not country:
        return None
    canonical, category = canonicalize_event_name(name, country)
    impact, relevance, channels, reasoning = classify_event(canonical, country, item.get("provider_importance"))
    status = event_status(scheduled, item.get("actual"), now, str(item.get("status") or ""))
    identity = "|".join((country.lower(), canonical, scheduled.astimezone(timezone.utc).isoformat(timespec="minutes"),
                         str(item.get("release_period") or "").lower(), category))
    event_id = "ECON-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20].upper()
    direction, absolute, percentage, interpretation = surprise(item.get("actual"), item.get("forecast"), item.get("unit"), canonical)
    source_name = str(item.get("source_name") or item.get("source") or item.get("provider_id") or "")
    provenance = [{
        "provider_id": str(item.get("provider_id") or ""),
        "provider_event_id": str(item.get("provider_event_id") or ""),
        "source": source_name,
        "source_authority": str(item.get("source_authority") or "DISCOVERY"),
        "source_url": str(item.get("source_url") or ""),
    }]
    return EconomicCalendarEvent(
        event_id=event_id, provider_event_id=str(item.get("provider_event_id") or ""),
        event_name=name, canonical_event_name=canonical, country=country,
        region=str(item.get("region") or "OTHER"), currency=str(item.get("currency") or ""), category=category,
        scheduled_at=scheduled.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        scheduled_at_original=str(item.get("scheduled_at_original") or item.get("scheduled_at") or ""),
        source_timezone=str(item.get("source_timezone") or "UTC"),
        scheduled_at_ist=scheduled_ist.isoformat(), actual=item.get("actual"), forecast=item.get("forecast"),
        previous=item.get("previous"), unit=item.get("unit"), impact_level=impact,
        source_name=source_name, source_attribution=source_name, source=source_name,
        source_authority=str(item.get("source_authority") or "DISCOVERY"), source_url=str(item.get("source_url") or ""),
        status=status, retrieved_at=str(item.get("retrieved_at") or now.isoformat().replace("+00:00", "Z")),
        last_updated=str(item.get("last_updated") or ""), freshness_status="fresh" if status != "STALE" else "stale",
        nifty_relevance=relevance, affected_channels=channels, reasoning=reasoning,
        release_period=str(item.get("release_period") or ""), provider_provenance=provenance,
        surprise_direction=direction, surprise_absolute=absolute, surprise_percentage=percentage,
        market_interpretation=interpretation, refresh_window=refresh_window(scheduled, now, status),
        session_timing=session_timing(scheduled_ist),
    )


def merge_events(existing: EconomicCalendarEvent, incoming: EconomicCalendarEvent) -> EconomicCalendarEvent:
    primary_existing = existing.source_authority == "PRIMARY"
    anchor, supplement = (existing, incoming) if primary_existing or incoming.source_authority != "PRIMARY" else (incoming, existing)
    merged = replace(anchor)
    for field in ("actual", "forecast", "previous", "unit", "release_period", "last_updated"):
        if getattr(merged, field) in (None, "") and getattr(supplement, field) not in (None, ""):
            setattr(merged, field, getattr(supplement, field))
    seen = {(p.get("provider_id"), p.get("provider_event_id")) for p in merged.provider_provenance}
    merged.provider_provenance = list(merged.provider_provenance) + [p for p in supplement.provider_provenance
                                                                   if (p.get("provider_id"), p.get("provider_event_id")) not in seen]
    merged.status = event_status(_parse_datetime(merged.scheduled_at) or datetime.now(timezone.utc), merged.actual,
                                 _now(merged.retrieved_at), "")
    direction, absolute, percentage, interpretation = surprise(merged.actual, merged.forecast, merged.unit, merged.canonical_event_name)
    merged.surprise_direction, merged.surprise_absolute = direction, absolute
    merged.surprise_percentage, merged.market_interpretation = percentage, interpretation
    return merged


class EconomicCalendarPipeline:
    def __init__(self, providers: Optional[List[BaseEconomicCalendarProvider]] = None,
                 cache_file: Optional[Path] = None) -> None:
        self.persistence_enabled = providers is None or cache_file is not None
        self.cache_file = cache_file or CACHE_FILE_PATH
        self.providers = providers if providers is not None else [
            MospiReleaseCalendarProvider(),
            OfficialIcsCalendarProvider(
                "bls_release_calendar", "https://www.bls.gov/schedule/news_release/bls.ics",
                source_name="U.S. Bureau of Labor Statistics", country="United States", region="US",
                currency="USD", default_timezone="America/New_York"),
            OfficialIcsCalendarProvider(
                "bea_release_calendar", "https://www.bea.gov/news/schedule/ics/online-calendar-subscription.ics",
                source_name="U.S. Bureau of Economic Analysis", country="United States", region="US",
                currency="USD", default_timezone="America/New_York"),
            EcbWeeklyCalendarProvider(), BojReleaseCalendarProvider(), TradingViewCalendarProvider(),
            FederalReserveCalendarProvider(), TradingEconomicsCalendarProvider(),
        ]
        self.history: Dict[str, Dict[str, Any]] = {}
        if self.persistence_enabled:
            self.load_cache()

    def load_cache(self) -> None:
        if not self.cache_file.exists():
            return
        try:
            data = json.loads(self.cache_file.read_text(encoding="utf-8"))
            self.history = dict(data.get("released_history") or {})
            states = data.get("providers") or {}
            for provider in self.providers:
                if provider.provider_name in states:
                    provider.restore_state(states[provider.provider_name])
        except (OSError, ValueError, TypeError):
            self.history = {}

    def save_cache(self, events: Sequence[EconomicCalendarEvent], now: datetime) -> None:
        if not self.persistence_enabled:
            return
        for event in events:
            if event.status == "RELEASED":
                self.history[event.event_id] = event.to_dict()
        # Historical storage is bounded; newest releases win.
        ordered = sorted(self.history.values(), key=lambda row: str(row.get("scheduled_at") or ""), reverse=True)[:2000]
        self.history = {str(row.get("event_id")): row for row in ordered if row.get("event_id")}
        payload = {"saved_at": now.isoformat().replace("+00:00", "Z"),
                   "providers": {p.provider_name: p.get_state() for p in self.providers},
                   "released_history": self.history,
                   "events": [event.to_dict() for event in events]}
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        temp = self.cache_file.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(temp, self.cache_file)

    def run(self, current_time: Optional[str | datetime] = None, force: bool = False) -> Dict[str, Any]:
        now = _now(current_time)
        normalized: List[EconomicCalendarEvent] = []
        health: Dict[str, Any] = {}
        raw_usable = 0
        rejected = 0
        for provider in self.providers:
            if provider.is_enabled and (force or provider.should_fetch()):
                raw = provider.fetch_raw_data()
            else:
                raw = list(provider.cached_raw_data)
            valid_for_provider = 0
            for item in raw:
                event = normalize_event(item, now)
                if event is None:
                    rejected += 1
                    continue
                valid_for_provider += 1
                normalized.append(event)
            raw_usable += valid_for_provider
            # READY is semantic: at least one valid exact-time event.
            if provider.is_enabled and valid_for_provider == 0 and provider.status == "ready":
                provider.status = "unavailable"
                provider.operational_error_reason = "no_valid_scheduled_events"
                provider.failure_detail = "Provider returned no NIFTY-relevant events with exact timezone-aware timestamps."
            provider.scheduled_record_count = sum(e.status != "RELEASED" for e in normalized[-valid_for_provider:]) if valid_for_provider else 0
            provider.released_record_count = sum(e.status == "RELEASED" for e in normalized[-valid_for_provider:]) if valid_for_provider else 0
            provider.next_scheduled_event = min((e.scheduled_at_ist for e in normalized[-valid_for_provider:]
                                                  if _parse_datetime(e.scheduled_at) and _parse_datetime(e.scheduled_at) > now), default=None) if valid_for_provider else None
            health[provider.provider_name] = provider.get_health().to_dict()

        merged: Dict[str, EconomicCalendarEvent] = {}
        for event in normalized:
            merged[event.event_id] = merge_events(merged[event.event_id], event) if event.event_id in merged else event
        events = sorted(merged.values(), key=lambda event: event.scheduled_at)
        for event in events:
            scheduled = _parse_datetime(event.scheduled_at)
            if scheduled is None:
                continue
            event.status = event_status(scheduled, event.actual, now, event.status)
            event.freshness_status = "stale" if event.status == "STALE" else "fresh"
            event.refresh_window = refresh_window(scheduled, now, event.status)

        ist_now = now.astimezone(IST)
        today, tomorrow = ist_now.date(), ist_now.date() + timedelta(days=1)
        week_end = today + timedelta(days=7)
        by_region = {region: sum(event.region == region and today <= _parse_datetime(event.scheduled_at_ist).date() <= week_end
                                 for event in events) for region in ("INDIA", "US", "EUROPE", "ASIA")}
        high_events = [event for event in events if event.impact_level in {"HIGH", "CRITICAL"} and _parse_datetime(event.scheduled_at) >= now]
        usable_providers = sum(h.get("status") in {"ready", "degraded", "stale"} and h.get("item_count", 0) > 0 for h in health.values())
        covered_regions = {region for region, count in by_region.items() if count > 0}
        coverage = "FULL" if len(covered_regions) == 4 else "PARTIAL" if len(covered_regions) >= 3 else "LIMITED" if covered_regions else "UNAVAILABLE"
        metrics = {
            "providers_configured": len(self.providers), "providers_usable": usable_providers,
            "raw_usable_records": raw_usable, "normalized_records": len(normalized), "canonical_records": len(events),
            "rejected_records": rejected, "provider_to_canonical_loss": max(0, raw_usable - len(normalized)),
            "duplicates_merged": len(normalized) - len(events),
            "events_today": sum(_parse_datetime(e.scheduled_at_ist).date() == today for e in events),
            "events_tomorrow": sum(_parse_datetime(e.scheduled_at_ist).date() == tomorrow for e in events),
            "events_this_week": sum(today <= _parse_datetime(e.scheduled_at_ist).date() <= week_end for e in events),
            "india_events": by_region["INDIA"], "us_events": by_region["US"],
            "europe_events": by_region["EUROPE"], "asia_events": by_region["ASIA"],
            "high_impact_events": sum(e.impact_level == "HIGH" and today <= _parse_datetime(e.scheduled_at_ist).date() <= week_end for e in events),
            "critical_events": sum(e.impact_level == "CRITICAL" and today <= _parse_datetime(e.scheduled_at_ist).date() <= week_end for e in events),
            "events_with_forecast": sum(e.forecast not in (None, "") for e in events),
            "events_with_previous": sum(e.previous not in (None, "") for e in events),
            "released_events_with_actual": sum(e.status == "RELEASED" and e.actual not in (None, "") for e in events),
            "next_high_impact_event": high_events[0].to_dict() if high_events else None,
            "historical_released_events": len(self.history),
        }
        self.save_cache(events, now)
        metrics["historical_released_events"] = len(self.history)
        return {"events": events, "provider_health": health, "coverage": coverage, "metrics": metrics,
                "history": list(self.history.values())}
