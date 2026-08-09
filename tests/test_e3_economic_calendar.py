from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.application.workstation_state_service import WorkstationStateService
from src.news_engine.economic_calendar_provider import BaseEconomicCalendarProvider, parse_ics_events
from src.pipeline.economic_calendar_pipeline import (
    EconomicCalendarPipeline,
    canonicalize_event_name,
    event_status,
    normalize_event,
    session_timing,
    surprise,
)


NOW = datetime(2026, 8, 9, 4, 30, tzinfo=timezone.utc)


def raw_event(**overrides):
    value = {
        "provider_event_id": "row-1", "event_name": "Consumer Price Index CPI YoY",
        "country": "United States", "region": "US", "currency": "USD",
        "scheduled_at": "2026-08-11T12:30:00Z", "scheduled_at_original": "20260811T083000",
        "source_timezone": "America/New_York", "actual": None, "forecast": 2.8, "previous": 3.0,
        "unit": "%", "source_name": "Test Calendar", "source_authority": "DISCOVERY",
        "source_url": "https://example.test/calendar", "provider_id": "test_calendar",
        "retrieved_at": NOW.isoformat(),
    }
    value.update(overrides)
    return value


class FakeProvider(BaseEconomicCalendarProvider):
    def __init__(self, name, rows=None, failure=None, authority="DISCOVERY", regions=None):
        super().__init__(name, source_authority=authority, coverage_regions=regions or ["US"], refresh_interval=0)
        self.rows, self.failure = rows or [], failure

    def fetch_raw_data(self):
        if self.failure:
            self.record_failure(RuntimeError(self.failure))
            return []
        self.record_success(self.rows)
        return self.rows


def test_india_official_normalization_and_exact_ist():
    event = normalize_event(raw_event(event_name="RBI Monetary Policy repo rate decision", country="India",
                                      region="INDIA", scheduled_at="2026-08-10T04:30:00Z",
                                      source_authority="PRIMARY"), NOW)
    assert event is not None
    assert event.canonical_event_name == "RBI_RATE_DECISION"
    assert event.scheduled_at_ist == "2026-08-10T10:00:00+05:30"
    assert event.impact_level == "CRITICAL"
    assert {"RATES", "INR", "BANKS"}.issubset(event.affected_channels)


def test_fed_cpi_nfp_and_gdp_canonicalization():
    assert canonicalize_event_name("FOMC interest rate decision", "United States")[0] == "FOMC_RATE_DECISION"
    assert canonicalize_event_name("Consumer Price Index CPI", "United States")[0] == "CPI"
    assert canonicalize_event_name("Employment Situation: Nonfarm Payrolls", "United States")[0] == "NONFARM_PAYROLLS"
    assert canonicalize_event_name("Gross Domestic Product, 2nd estimate", "United States")[0] == "GDP"


def test_us_dst_conversion_uses_event_date_zone_rules():
    ics = ("BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nUID:winter\r\nSUMMARY:Consumer Price Index CPI\r\n"
           "DTSTART;TZID=America/New_York:20260115T083000\r\nEND:VEVENT\r\n"
           "BEGIN:VEVENT\r\nUID:summer\r\nSUMMARY:Consumer Price Index CPI\r\n"
           "DTSTART;TZID=America/New_York:20260715T083000\r\nEND:VEVENT\r\nEND:VCALENDAR").encode()
    rows = parse_ics_events(ics, provider_id="bls", source_name="BLS", source_url="https://bls.gov",
                            country="United States", region="US", currency="USD", default_timezone="America/New_York")
    times = [normalize_event(row, NOW).scheduled_at_ist for row in rows]
    assert times == ["2026-01-15T19:00:00+05:30", "2026-07-15T18:00:00+05:30"]


def test_europe_dst_conversion_uses_event_date_zone_rules():
    winter = normalize_event(raw_event(scheduled_at="2026-01-15T08:00:00+01:00", source_timezone="Europe/Berlin"), NOW)
    summer = normalize_event(raw_event(scheduled_at="2026-07-15T08:00:00+02:00", source_timezone="Europe/Berlin"), NOW)
    assert winter.scheduled_at_ist.endswith("12:30:00+05:30")
    assert summer.scheduled_at_ist.endswith("11:30:00+05:30")


def test_status_transitions_do_not_infer_release():
    assert event_status(datetime(2026, 8, 10, tzinfo=timezone.utc), None, NOW) == "UPCOMING"
    assert event_status(NOW.replace(minute=40), None, NOW) == "DUE"
    assert event_status(NOW.replace(hour=3), None, NOW) == "DELAYED"
    assert event_status(NOW.replace(day=8), None, NOW) == "STALE"
    assert event_status(NOW.replace(day=8), 0, NOW) == "RELEASED"
    assert event_status(NOW, None, NOW, "cancelled by source") == "CANCELLED"


def test_surprise_rules_and_missing_forecast():
    assert surprise(3.1, 2.8, "%", "CPI") == ("ABOVE", 0.3, 10.7143, "NEGATIVE")
    assert surprise(6.0, 5.8, "%", "GDP")[-1] == "POSITIVE"
    assert surprise(0, 0, "%", "CPI")[:2] == ("INLINE", 0.0)
    assert surprise(3.1, None, "%", "CPI") == ("NOT_APPLICABLE", None, None, "UNCERTAIN")


def test_session_buckets_are_ist_specific():
    from zoneinfo import ZoneInfo
    zone = ZoneInfo("Asia/Kolkata")
    assert session_timing(datetime(2026, 8, 9, 8, 0, tzinfo=zone)) == "BEFORE_OPEN"
    assert session_timing(datetime(2026, 8, 9, 10, 0, tzinfo=zone)) == "DURING_SESSION"
    assert session_timing(datetime(2026, 8, 9, 18, 0, tzinfo=zone)) == "AFTER_CLOSE"
    assert session_timing(datetime(2026, 8, 9, 3, 0, tzinfo=zone)) == "OVERNIGHT"


def test_duplicate_events_merge_and_primary_provider_wins():
    discovery = raw_event(provider_id="discovery", source_name="Discovery", source_authority="DISCOVERY", actual=3.1)
    primary = raw_event(provider_id="official", source_name="BLS", source_authority="PRIMARY", actual=None)
    result = EconomicCalendarPipeline([FakeProvider("discovery", [discovery]),
                                       FakeProvider("official", [primary], authority="PRIMARY")]).run(NOW, force=True)
    assert result["metrics"]["normalized_records"] == 2
    assert result["metrics"]["canonical_records"] == 1
    event = result["events"][0]
    assert event.source_name == "BLS"
    assert event.actual == 3.1
    assert len(event.provider_provenance) == 2


def test_partial_provider_failure_preserves_healthy_records():
    result = EconomicCalendarPipeline([FakeProvider("healthy", [raw_event()]),
                                       FakeProvider("broken", failure="timeout")]).run(NOW, force=True)
    assert len(result["events"]) == 1
    assert result["provider_health"]["broken"]["status"] == "degraded"
    assert result["provider_health"]["healthy"]["status"] == "ready"


def test_date_only_records_are_rejected_without_inventing_time():
    row = raw_event(scheduled_at="", scheduled_date="2026-08-11")
    result = EconomicCalendarPipeline([FakeProvider("date_only", [row])]).run(NOW, force=True)
    assert result["events"] == []
    assert result["metrics"]["rejected_records"] == 1
    assert result["provider_health"]["date_only"]["status"] == "unavailable"


def test_released_history_persists_atomically(tmp_path: Path):
    cache = tmp_path / "calendar.json"
    row = raw_event(scheduled_at="2026-08-09T04:00:00Z", actual=3.1)
    first = EconomicCalendarPipeline([FakeProvider("calendar", [row])], cache).run(NOW, force=True)
    assert first["events"][0].status == "RELEASED"
    payload = json.loads(cache.read_text(encoding="utf-8"))
    assert len(payload["released_history"]) == 1
    second = EconomicCalendarPipeline([FakeProvider("calendar", [])], cache).run(NOW, force=True)
    assert len(second["history"]) == 1


def test_canonical_workspace_propagation_and_news_link():
    released = normalize_event(raw_event(scheduled_at="2026-08-09T04:00:00Z", actual=3.1), NOW).to_dict()
    payload = {"macroIntelligence": {"economic_events": [released]}, "newsSentiment": {
        "status": "READY", "items": [{"id": "n1"}], "event_clusters": [{
            "event_cluster_id": "c1", "canonical_headline": "US CPI inflation is above forecast",
            "last_updated": "2026-08-09T04:10:00Z", "related_countries": ["United States"]}]}}
    state = WorkstationStateService.build_from_legacy(payload, broker_state="CONNECTED", market_state="HOLIDAY", now=NOW)
    assert state.macro_intelligence["economic_events"][0]["event_id"] == released["event_id"]
    assert state.news_intelligence["event_clusters"][0]["economic_event_id"] == released["event_id"]


def test_workspace_ui_contains_required_calendar_surfaces():
    root = Path("src/frontend/components")
    assert "Today's High-Impact Events" in (root / "PreMarketPlannerWorkspace.tsx").read_text(encoding="utf-8")
    assert "Event Risk Today" in (root / "PreMarketPlannerWorkspace.tsx").read_text(encoding="utf-8")
    news_ui = (root / "NewsIntelligence.tsx").read_text(encoding="utf-8")
    for label in ("TODAY", "TOMORROW", "THIS WEEK", "NIFTY RELEVANT"):
        assert label in news_ui
    assert "WHAT TO WATCH NEXT" in (root / "IntradayAssistant.tsx").read_text(encoding="utf-8")
    assert "Economic Calendar Provider Health" in (root / "SettingsDashboard.tsx").read_text(encoding="utf-8")


def test_no_production_calendar_fixture_or_synthetic_fallback():
    pipeline = Path("src/pipeline/economic_calendar_pipeline.py").read_text(encoding="utf-8").lower()
    assert "synthetic" not in pipeline
    assert "mock_event" not in pipeline
