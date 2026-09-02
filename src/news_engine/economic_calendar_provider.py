"""E3 economic-calendar providers with official-first, bounded ingestion."""
from __future__ import annotations

import html
import json
import os
import re
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional
from urllib.parse import quote
from zoneinfo import ZoneInfo

from src.models.news_context_v2 import ProviderHealth
from src.news_engine.macro_provider import BaseMacroProvider
from src.news_engine.normalizer import clean_html_text
from src.news_engine.safe_utils import safe_url_fetch


RELEVANT_TERMS = (
    "monetary policy", "interest rate", "rate decision", "fomc", "press conference",
    "consumer price", "cpi", "producer price", "ppi", "personal income and outlays", "pce",
    "employment situation", "nonfarm payroll", "unemployment", "jobless claims", "gross domestic product",
    "gdp", "industrial production", "iip", "retail sales", "trade balance", "international trade",
    "pmi", "ism", "forex reserves", "foreign exchange reserves", "fiscal deficit", "core industries",
    "summary of opinions", "bank lending", "current account",
)


def _relevant(name: str) -> bool:
    lowered = name.lower()
    return any(term in lowered for term in RELEVANT_TERMS)


def _unfold_ics(text: str) -> List[str]:
    lines: List[str] = []
    for raw in text.replace("\r\n", "\n").split("\n"):
        if raw.startswith((" ", "\t")) and lines:
            lines[-1] += raw[1:]
        else:
            lines.append(raw)
    return lines


def parse_ics_events(data: bytes, *, provider_id: str, source_name: str, source_url: str,
                     country: str, region: str, currency: str, default_timezone: str,
                     source_authority: str = "PRIMARY") -> List[Dict[str, Any]]:
    """Parse the bounded VEVENT subset used by official release calendars."""
    events: List[Dict[str, Any]] = []
    current: Dict[str, str] | None = None
    for line in _unfold_ics(data.decode("utf-8", "ignore")):
        if line == "BEGIN:VEVENT":
            current = {}
            continue
        if line == "END:VEVENT":
            if current:
                name = clean_html_text(current.get("SUMMARY", "").replace("\\,", ","), max_length=200)
                raw_start = current.get("DTSTART", "")
                timezone_name = current.get("DTSTART_TZID") or default_timezone
                if name and raw_start and _relevant(name):
                    try:
                        if raw_start.endswith("Z"):
                            observed = datetime.strptime(raw_start, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
                            timezone_name = "UTC"
                        else:
                            observed = datetime.strptime(raw_start, "%Y%m%dT%H%M%S").replace(tzinfo=ZoneInfo(timezone_name))
                        events.append({
                            "provider_event_id": current.get("UID", ""), "event_name": name,
                            "country": country, "region": region, "currency": currency,
                            "category": name, "scheduled_at": observed.isoformat(),
                            "scheduled_at_original": raw_start, "source_timezone": timezone_name,
                            "actual": None, "forecast": None, "previous": None, "unit": None,
                            "release_period": "", "source": source_name, "source_name": source_name,
                            "source_authority": source_authority, "source_url": source_url,
                            "retrieved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                            "last_updated": current.get("DTSTAMP", ""), "provider_id": provider_id,
                        })
                    except (ValueError, KeyError):
                        pass
            current = None
            continue
        if current is None or ":" not in line:
            continue
        key_part, value = line.split(":", 1)
        key, *params = key_part.split(";")
        current[key] = value
        if key == "DTSTART":
            for param in params:
                if param.startswith("TZID="):
                    current["DTSTART_TZID"] = param.split("=", 1)[1]
    return events


class BaseEconomicCalendarProvider(BaseMacroProvider):
    def __init__(self, provider_name: str, *, source_authority: str, coverage_regions: List[str],
                 refresh_interval: float = 3600.0, is_enabled: bool = True) -> None:
        super().__init__(provider_name, refresh_interval=refresh_interval, is_enabled=is_enabled)
        self.source_authority = source_authority
        self.coverage_regions = coverage_regions
        self.scheduled_record_count = 0
        self.released_record_count = 0
        self.next_scheduled_event: Optional[str] = None
        self.rate_limit_state = "READY" if is_enabled else "DISABLED"
        self.raw_record_count = 0

    def record_success(self, items: List[Dict[str, Any]]) -> None:
        super().record_success(items)
        self.scheduled_record_count = sum(item.get("actual") is None for item in items)
        self.released_record_count = sum(item.get("actual") is not None for item in items)
        future = sorted(item.get("scheduled_at", "") for item in items if item.get("scheduled_at", "") > datetime.now(timezone.utc).isoformat())
        self.next_scheduled_event = future[0] if future else None

    def record_failure(self, exc: Exception) -> None:
        super().record_failure(exc)
        if "429" in str(exc) or "rate" in str(exc).lower():
            self.rate_limit_state = "RATE_LIMITED"

    def get_state(self) -> Dict[str, Any]:
        return {**super().get_state(), "source_authority": self.source_authority,
                "coverage_regions": self.coverage_regions, "scheduled_record_count": self.scheduled_record_count,
                "released_record_count": self.released_record_count, "next_scheduled_event": self.next_scheduled_event,
                "rate_limit_state": self.rate_limit_state, "raw_record_count": self.raw_record_count}

    def restore_state(self, state: Dict[str, Any]) -> None:
        super().restore_state(state)
        for key in ("scheduled_record_count", "released_record_count", "next_scheduled_event", "rate_limit_state", "raw_record_count"):
            if key in state:
                setattr(self, key, state[key])

    def get_health(self) -> ProviderHealth:
        return replace(super().get_health(), coverage_regions=list(self.coverage_regions),
                       scheduled_record_count=self.scheduled_record_count,
                       released_record_count=self.released_record_count,
                       next_scheduled_event=self.next_scheduled_event,
                       rate_limit_state=self.rate_limit_state)


class OfficialIcsCalendarProvider(BaseEconomicCalendarProvider):
    def __init__(self, provider_name: str, url: str, *, source_name: str, country: str,
                 region: str, currency: str, default_timezone: str) -> None:
        super().__init__(provider_name, source_authority="PRIMARY", coverage_regions=[region])
        self.url, self.source_name, self.country = url, source_name, country
        self.region, self.currency, self.default_timezone = region, currency, default_timezone

    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        try:
            raw, _headers, status = safe_url_fetch(
                self.url, timeout=25.0, max_size=2 * 1024 * 1024,
                headers={"Accept": "text/calendar,*/*", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            )
            if status == 304:
                return list(self.cached_raw_data)
            items = parse_ics_events(raw, provider_id=self.provider_name, source_name=self.source_name,
                                     source_url=self.url, country=self.country, region=self.region,
                                     currency=self.currency, default_timezone=self.default_timezone)
            self.raw_record_count = raw.decode("utf-8", "ignore").count("BEGIN:VEVENT")
            self.record_success(items)
            return items
        except Exception as exc:
            self.record_failure(exc)
            return list(self.cached_raw_data)


class MospiReleaseCalendarProvider(BaseEconomicCalendarProvider):
    URL = "https://www.mospi.gov.in/api/release-calender/fetch-all-release-calender-Web"

    def __init__(self) -> None:
        super().__init__("mospi_release_calendar", source_authority="PRIMARY", coverage_regions=["INDIA"], refresh_interval=21600.0)

    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        try:
            payload = json.dumps({"lang": "en", "page": 1, "limit": 200, "year": datetime.now(ZoneInfo("Asia/Kolkata")).year}).encode()
            raw, _, _ = safe_url_fetch(self.URL, timeout=25.0, max_size=2 * 1024 * 1024, method="POST", data=payload,
                                       headers={"Content-Type": "application/json", "Accept": "application/json"})
            rows = (json.loads(raw.decode("utf-8")) or {}).get("data") or []
            self.raw_record_count = len(rows)
            # MoSPI currently publishes dates but no exact release times in this API.
            # Keep them observable as rejected raw records; do not invent a timestamp.
            items = [{"provider_event_id": str(row.get("id") or ""), "event_name": clean_html_text(row.get("title", ""), 200),
                      "country": "India", "region": "INDIA", "currency": "INR", "category": row.get("title", ""),
                      "scheduled_at": "", "scheduled_date": f"{row.get('year', '')}-{int(row.get('month') or 0):02d}-{int(row.get('day') or 0):02d}",
                      "source": "MoSPI", "source_name": "MoSPI", "source_authority": "PRIMARY", "source_url": "https://mospi.gov.in/release-calendar",
                      "provider_id": self.provider_name, "actual": None, "forecast": None, "previous": None}
                     for row in rows if _relevant(str(row.get("title") or ""))]
            self.status = "unavailable"
            self.last_attempted_fetch = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            self.operational_error_reason = "no_exact_release_times"
            self.failure_detail = "Official MoSPI calendar returned date-only records; E3 rejects them rather than inventing release times."
            self.item_count = 0
            self.cached_raw_data = []
            self.last_fetch_timestamp = datetime.now(timezone.utc).timestamp()
            return items
        except Exception as exc:
            self.record_failure(exc)
            return []


class TradingViewCalendarProvider(BaseEconomicCalendarProvider):
    BASE = "https://economic-calendar.tradingview.com/events"

    def __init__(self) -> None:
        super().__init__("tradingview_calendar_discovery", source_authority="DISCOVERY",
                         coverage_regions=["INDIA", "US", "EUROPE", "ASIA"], refresh_interval=1800.0)

    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        start = (now - timedelta(days=2)).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        end = (now + timedelta(days=8)).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        url = f"{self.BASE}?from={quote(start)}&to={quote(end)}&countries=IN,US,EU,GB,JP,CN"
        try:
            raw, _, _ = safe_url_fetch(url, timeout=25.0, max_size=2 * 1024 * 1024,
                                       headers={"Accept": "application/json", "Origin": "https://www.tradingview.com", "User-Agent": "Mozilla/5.0"})
            rows = (json.loads(raw.decode("utf-8")) or {}).get("result") or []
            self.raw_record_count = len(rows)
            region_map = {"IN": "INDIA", "US": "US", "EU": "EUROPE", "GB": "EUROPE", "JP": "ASIA", "CN": "ASIA"}
            country_map = {"IN": "India", "US": "United States", "EU": "Euro Area", "GB": "United Kingdom", "JP": "Japan", "CN": "China"}
            items = []
            for row in rows:
                name = clean_html_text(row.get("title") or row.get("indicator") or "", 200)
                if not name or not _relevant(name) or not row.get("date"):
                    continue
                items.append({
                    "provider_event_id": str(row.get("id") or ""), "event_name": name,
                    "country": country_map.get(row.get("country"), row.get("country") or ""),
                    "region": region_map.get(row.get("country"), "OTHER"), "currency": str(row.get("currency") or ""),
                    "category": str(row.get("indicator") or name), "scheduled_at": str(row.get("date")),
                    "scheduled_at_original": str(row.get("date")), "source_timezone": "UTC",
                    "actual": row.get("actual"), "forecast": row.get("forecast"), "previous": row.get("previous"),
                    "unit": row.get("unit"), "release_period": str(row.get("period") or ""),
                    "source": str(row.get("source") or "TradingView Economic Calendar"),
                    "source_name": "TradingView Economic Calendar", "source_authority": "DISCOVERY",
                    "source_url": url, "retrieved_at": now.isoformat().replace("+00:00", "Z"),
                    "last_updated": str(row.get("date") or ""), "provider_id": self.provider_name,
                    "provider_importance": row.get("importance"),
                })
            self.record_success(items)
            return items
        except Exception as exc:
            self.record_failure(exc)
            return list(self.cached_raw_data)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: List[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())


class EcbWeeklyCalendarProvider(BaseEconomicCalendarProvider):
    URL = "https://www.ecb.europa.eu/press/calendars/weekly/html/index.en.html"

    def __init__(self) -> None:
        super().__init__("ecb_weekly_calendar", source_authority="PRIMARY", coverage_regions=["EUROPE"], refresh_interval=21600.0)

    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        try:
            raw, _, _ = safe_url_fetch(self.URL, timeout=25.0, max_size=2 * 1024 * 1024, headers={"Accept": "text/html,*/*"})
            parser = _TextExtractor(); parser.feed(raw.decode("utf-8", "ignore")); text = " ".join(parser.parts)
            pattern = re.compile(r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(\d{1,2}\s+\w+\s+\d{4})\s+Event:\s+(.+?)\s+Time:\s+(\d{1,2}:\d{2})\s+(CET|CEST)")
            items = []
            for date_text, name, time_text, zone_label in pattern.findall(text):
                name = clean_html_text(name, 200)
                if not _relevant(name):
                    continue
                naive = datetime.strptime(f"{date_text} {time_text}", "%d %B %Y %H:%M")
                observed = naive.replace(tzinfo=ZoneInfo("Europe/Berlin"))
                items.append({"provider_event_id": f"ECB-{observed.isoformat()}-{name}", "event_name": name,
                              "country": "Euro Area", "region": "EUROPE", "currency": "EUR", "category": name,
                              "scheduled_at": observed.isoformat(), "scheduled_at_original": f"{date_text} {time_text} {zone_label}",
                              "source_timezone": "Europe/Berlin", "actual": None, "forecast": None, "previous": None,
                              "unit": None, "source": "European Central Bank", "source_name": "European Central Bank",
                              "source_authority": "PRIMARY", "source_url": self.URL, "provider_id": self.provider_name,
                              "retrieved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")})
            self.raw_record_count = len(pattern.findall(text)); self.record_success(items); return items
        except Exception as exc:
            self.record_failure(exc); return list(self.cached_raw_data)


class BojReleaseCalendarProvider(BaseEconomicCalendarProvider):
    URL = "https://www.boj.or.jp/en/about/calendar/index.htm"

    def __init__(self) -> None:
        super().__init__("boj_release_calendar", source_authority="PRIMARY", coverage_regions=["ASIA"], refresh_interval=21600.0)

    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        try:
            raw, _, _ = safe_url_fetch(self.URL, timeout=25.0, max_size=1024 * 1024, headers={"Accept": "text/html,*/*"})
            parser = _TextExtractor(); parser.feed(raw.decode("utf-8", "ignore")); text = " ".join(parser.parts)
            year = datetime.now(ZoneInfo("Asia/Tokyo")).year
            pattern = re.compile(r"(Jan\.|Feb\.|Mar\.|Apr\.|May|June|July|Aug\.|Sept\.|Oct\.|Nov\.|Dec\.)\s+(\d{1,2})\s+(\d{1,2}:\d{2})\s+(.+?)(?=\s+(?:\d{1,2}\s+)?\d{1,2}:\d{2}\s+|\s+(?:Jan\.|Feb\.|Mar\.|Apr\.|May|June|July|Aug\.|Sept\.|Oct\.|Nov\.|Dec\.)\s+\d{1,2}|$)")
            months = {"Jan.":1,"Feb.":2,"Mar.":3,"Apr.":4,"May":5,"June":6,"July":7,"Aug.":8,"Sept.":9,"Oct.":10,"Nov.":11,"Dec.":12}
            items = []
            matches = pattern.findall(text)
            for month, day, clock, name in matches:
                name = clean_html_text(name, 200)
                if not _relevant(name):
                    continue
                hour, minute = (int(part) for part in clock.split(":", 1))
                observed = datetime(year, months[month], int(day), hour, minute, tzinfo=ZoneInfo("Asia/Tokyo"))
                items.append({"provider_event_id": f"BOJ-{observed.isoformat()}-{name}", "event_name": name,
                              "country": "Japan", "region": "ASIA", "currency": "JPY", "category": name,
                              "scheduled_at": observed.isoformat(), "scheduled_at_original": f"{month} {day} {clock} JST",
                              "source_timezone": "Asia/Tokyo", "actual": None, "forecast": None, "previous": None,
                              "unit": None, "source": "Bank of Japan", "source_name": "Bank of Japan",
                              "source_authority": "PRIMARY", "source_url": self.URL, "provider_id": self.provider_name,
                              "retrieved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")})
            self.raw_record_count = len(matches); self.record_success(items); return items
        except Exception as exc:
            self.record_failure(exc); return list(self.cached_raw_data)


class TradingEconomicsCalendarProvider(BaseEconomicCalendarProvider):
    """Optional vendor adapter; disabled without server-side credentials."""
    def __init__(self) -> None:
        key = os.getenv("ECONOMIC_CALENDAR_API_KEY", "").strip()
        super().__init__("tradingeconomics_calendar", source_authority="DISCOVERY",
                         coverage_regions=["INDIA", "US", "EUROPE", "ASIA"], is_enabled=bool(key))
        self.api_key = key
        if not key:
            self.status = "disabled"; self.rate_limit_state = "DISABLED"
            self.operational_error_reason = "api_key_not_configured"
            self.failure_detail = "Awaiting Provider Configuration"

    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        if not self.api_key:
            return []
        now = datetime.now(timezone.utc)
        start, end = (now - timedelta(days=2)).date().isoformat(), (now + timedelta(days=8)).date().isoformat()
        url = ("https://api.tradingeconomics.com/calendar/country/india,united%20states,euro%20area,"
               f"united%20kingdom,japan,china/{start}/{end}?c={quote(self.api_key)}")
        try:
            raw, _, _ = safe_url_fetch(url, timeout=25.0, max_size=2 * 1024 * 1024,
                                       headers={"Accept": "application/json"})
            rows = json.loads(raw.decode("utf-8")) or []
            self.raw_record_count = len(rows)
            region_map = {"India": "INDIA", "United States": "US", "Euro Area": "EUROPE",
                          "United Kingdom": "EUROPE", "Japan": "ASIA", "China": "ASIA"}
            items = []
            for row in rows:
                name = clean_html_text(row.get("Event") or "", 200)
                if not name or not _relevant(name) or not row.get("Date"):
                    continue
                items.append({"provider_event_id": str(row.get("CalendarId") or ""), "event_name": name,
                              "country": str(row.get("Country") or ""), "region": region_map.get(row.get("Country"), "OTHER"),
                              "currency": str(row.get("Currency") or ""), "category": str(row.get("Category") or name),
                              "scheduled_at": str(row.get("Date")), "scheduled_at_original": str(row.get("Date")),
                              "source_timezone": "UTC", "actual": row.get("Actual"), "forecast": row.get("Forecast"),
                              "previous": row.get("Previous"), "unit": row.get("Unit"), "release_period": str(row.get("Reference") or ""),
                              "source": str(row.get("Source") or "Trading Economics"), "source_name": "Trading Economics",
                              "source_authority": "DISCOVERY", "source_url": str(row.get("SourceURL") or url),
                              "retrieved_at": now.isoformat().replace("+00:00", "Z"), "last_updated": str(row.get("LastUpdate") or ""),
                              "provider_id": self.provider_name, "provider_importance": row.get("Importance")})
            self.record_success(items)
            return items
        except Exception as exc:
            self.record_failure(exc)
            return list(self.cached_raw_data)


class FederalReserveCalendarProvider(BaseEconomicCalendarProvider):
    """Observes the official FOMC calendar without inventing its omitted clock time."""
    URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"

    def __init__(self) -> None:
        super().__init__("federal_reserve_fomc_calendar", source_authority="PRIMARY", coverage_regions=["US"], refresh_interval=21600.0)

    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        try:
            raw, _, _ = safe_url_fetch(self.URL, timeout=25.0, max_size=2 * 1024 * 1024,
                                       headers={"Accept": "text/html,*/*"})
            text = raw.decode("utf-8", "ignore")
            self.raw_record_count = len(re.findall(r"\b(?:January|March|April|May|June|July|September|October|November|December)\b", text))
            self.status = "unavailable"
            self.last_attempted_fetch = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            self.last_fetch_timestamp = datetime.now(timezone.utc).timestamp()
            self.item_count = 0
            self.operational_error_reason = "no_exact_release_times"
            self.failure_detail = "The official FOMC meeting calendar publishes meeting dates but no exact statement time; E3 does not invent one."
            return []
        except Exception as exc:
            self.record_failure(exc)
            return []
