from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

from src.application.workstation_state_service import WorkstationStateService
from src.models.news_context_v2 import NewsItem
from src.news_engine.event_clusterer import NewsEventClusterer
from src.news_engine.provider import BaseNewsProvider
from src.news_engine.temporal_integrity import assess_publication_time, live_window, strict_publication_timestamp
from src.pipeline.news_pipeline import NewsPipeline


MONDAY = datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)
SUNDAY = datetime(2026, 8, 9, 5, 0, tzinfo=timezone.utc)


class FixtureProvider(BaseNewsProvider):
    def __init__(self, records: list[dict], name: str = "fixture") -> None:
        super().__init__(name, refresh_interval=3600)
        self.records = records
        self.discovery_streams = ["INDIA"]

    def fetch_raw_news(self) -> list[dict]:
        rows = [{**row, "provider_id": self.provider_name, "discovery_stream": "INDIA"} for row in self.records]
        self.record_success(rows)
        return rows


def raw(identifier: str, published_at: str | None, *, headline: str | None = None,
        source: str = "Reuters", query: str = "market when:1d") -> dict:
    row = {
        "headline": headline or f"NIFTY market update {identifier}",
        "summary_snippet": "India market transmission and banking impact.",
        "source_name": source,
        "source_type": "official" if source == "Federal Reserve Board" else "media",
        "original_url": f"https://example.test/{identifier}",
        "discovery_query": query,
        "received_at": MONDAY.isoformat(),
    }
    if published_at is not None:
        row["published_at"] = published_at
    return row


def pipeline(records: list[dict], now: datetime = MONDAY) -> tuple[NewsPipeline, object]:
    instance = NewsPipeline(providers=[FixtureProvider(records)])
    return instance, instance.run(now.isoformat())


def news_item(identifier: str, hours_ago: int, *, eligible: bool) -> NewsItem:
    observed = MONDAY - timedelta(hours=hours_ago)
    return NewsItem(
        id=identifier, headline="Oil shipping disruption affects India", summary_snippet="Crude and INR transmission.",
        source_name="Reuters", source_type="media", original_url=f"https://example.test/{identifier}",
        discovery_url="", discovered_via="fixture", provider_id="fixture",
        published_at=observed.isoformat(), received_at=MONDAY.isoformat(), age_seconds=hours_ago * 3600,
        freshness_status="current" if eligible else "stale", quality_status="high", verification_status="unverified",
        category="Crude", event_type="Crude", affected_symbols=[], affected_sectors=[], nifty_relevance_score=8,
        expected_direction="negative", impact_strength="high", impact_duration="daily", confidence=.75,
        publisher="Reuters", source_tier="TIER_B_HIGH_TRUST", discovery_stream="CRUDE_ENERGY",
        related_countries=["INDIA"], affected_channels=["CRUDE", "INR"], priority_score=100,
        temporal_class="CURRENT" if eligible else "STALE", canonical_eligible=eligible, workspace_eligible=eligible,
    )


def test_01_six_month_old_fetch_is_not_current() -> None:
    _, context = pipeline([raw("old", "2026-02-10T12:00:00Z")])
    assert context.items == [] and len(context.historical_items) == 1


def test_02_fetch_timestamp_never_replaces_publication_timestamp() -> None:
    assessment = assess_publication_time("2026-02-10T12:00:00Z", MONDAY)
    assert not assessment.current_eligible and assessment.temporal_class == "HISTORICAL"


def test_03_query_window_is_not_freshness_validation() -> None:
    _, context = pipeline([raw("query", "2026-07-01T12:00:00Z", query="NIFTY when:1d")])
    assert not context.items and context.historical_items[0].discovery_query.endswith("when:1d")


def test_04_weekend_uses_bounded_wider_window() -> None:
    window, _ = live_window(SUNDAY)
    assert timedelta(hours=48) <= window <= timedelta(hours=96)
    assert assess_publication_time("2026-08-07T15:00:00Z", SUNDAY).current_eligible


def test_05_old_article_retained_for_provenance() -> None:
    _, context = pipeline([raw("archive", "2025-12-26T12:00:00Z", source="Federal Reserve Board")])
    assert context.historical_items[0].source_tier == "TIER_A_PRIMARY"


def test_06_old_article_plus_new_update_makes_current_cluster() -> None:
    cluster = NewsEventClusterer.cluster([news_item("old", 30, eligible=False), news_item("new", 1, eligible=True)])[0]
    assert cluster.canonical_eligible and cluster.current_article_count == 1 and cluster.historical_article_count == 1


def test_07_old_cluster_without_update_stays_historical() -> None:
    cluster = NewsEventClusterer.cluster([news_item("old", 30, eligible=False)])[0]
    assert not cluster.canonical_eligible and cluster.temporal_class == "HISTORICAL"


def test_08_missing_timestamp_fails_closed() -> None:
    _, context = pipeline([raw("missing", None)])
    assert not context.items and context.temporal_diagnostics["counts"]["INVALID_TIMESTAMP"] == 1


def test_09_malformed_timestamp_fails_closed() -> None:
    _, context = pipeline([raw("bad", "not-a-date")])
    assert not context.items and context.temporal_diagnostics["counts"]["INVALID_TIMESTAMP"] == 1


def test_10_impossible_future_timestamp_fails_closed() -> None:
    _, context = pipeline([raw("future", "2026-08-10T13:00:00Z")])
    assert not context.items and context.historical_items[0].timestamp_validity == "INVALID_FUTURE"


def test_11_cache_restoration_recomputes_freshness() -> None:
    instance = NewsPipeline(providers=[FixtureProvider([raw("cached", "2026-08-10T11:00:00Z")])])
    assert instance.run(MONDAY.isoformat()).items
    restored = instance.run((MONDAY + timedelta(days=8)).isoformat())
    assert not restored.items and restored.historical_items[0].cache_restored


def test_12_tier_a_cannot_bypass_freshness() -> None:
    _, context = pipeline([raw("fed", "2026-03-18T18:00:00Z", source="Federal Reserve Board")])
    assert not context.items and context.historical_items[0].source_tier == "TIER_A_PRIMARY"


def test_13_high_relevance_cannot_bypass_freshness() -> None:
    _, context = pipeline([raw("critical", "2025-12-26T12:00:00Z", headline="Federal Reserve emergency rate cut crashes NIFTY banking")])
    assert not context.items and context.historical_items[0].nifty_relevance_score >= 7


def _canonical(records: list[dict], observed: str) -> dict:
    _, context = pipeline(records)
    return WorkstationStateService.build_from_legacy(
        {"marketContext": {"last_tick_time": observed}, "optionContext": {}, "newsSentiment": context.payload},
        market_state="MARKET_CLOSED", now=MONDAY,
    ).to_dict()["news_intelligence"]


def test_14_since_close_only_contains_post_close_events() -> None:
    news = _canonical([raw("before", "2026-08-10T09:00:00Z"), raw("after", "2026-08-10T11:00:00Z")], "2026-08-10T10:00:00Z")
    ids = set(news["workspace_temporal"]["since_close_item_ids"])
    assert len(ids) == 1 and next(item for item in news["items"] if item["id"] in ids)["headline"].endswith("after")


def test_15_zero_since_close_does_not_fill_from_history() -> None:
    news = _canonical([raw("before", "2026-08-10T09:00:00Z")], "2026-08-10T10:00:00Z")
    assert news["workspace_temporal"]["since_close_item_ids"] == []


def test_16_analysis_separates_previous_session_context() -> None:
    news = _canonical([raw("before", "2026-08-10T09:00:00Z"), raw("after", "2026-08-10T11:00:00Z")], "2026-08-10T10:00:00Z")
    workspace = news["workspace_temporal"]
    assert set(workspace["previous_session_context_item_ids"]).isdisjoint(workspace["current_driver_item_ids"])


def test_17_live_assistant_since_close_excludes_history() -> None:
    news = _canonical([raw("history", "2026-03-18T18:00:00Z"), raw("after", "2026-08-10T11:00:00Z")], "2026-08-10T10:00:00Z")
    assert news["workspace_temporal"]["live_assistant_since_close_count"] == 1


def test_18_no_provider_to_canonical_loss_for_eligible_unique_items() -> None:
    _, context = pipeline([raw("a", "2026-08-10T11:00:00Z"), raw("b", "2026-08-10T11:30:00Z")])
    assert context.ingestion_metrics["provider_to_canonical_current_data_loss"] == 0


def test_19_no_canonical_to_workspace_loss_for_eligible_items() -> None:
    news = _canonical([raw("a", "2026-08-10T11:00:00Z"), raw("b", "2026-08-10T11:30:00Z")], "2026-08-10T10:00:00Z")
    assert news["workspace_temporal"]["canonical_to_workspace_current_data_loss"] == 0
    assert news["workspace_temporal"]["live_feed_count"] == len(news["items"])


def test_20_historical_records_support_deduplication_provenance() -> None:
    first = raw("one", "2026-03-18T18:00:00Z", headline="Federal Reserve leaves rates unchanged")
    second = {**raw("two", "2026-03-18T18:10:00Z", headline="Federal Reserve leaves rates unchanged"), "source_name": "CNBC", "original_url": first["original_url"]}
    _, context = pipeline([first, second])
    assert not context.items and len(context.historical_items) == 1
    assert len(context.historical_items[0].warnings) >= 1


def test_timezone_naive_publication_is_invalid() -> None:
    assert strict_publication_timestamp("2026-08-10T11:00:00") is None
