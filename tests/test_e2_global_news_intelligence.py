from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.application.workstation_state_service import WorkstationStateService
from src.models.news_context_v2 import NewsItem
from src.news_engine.deduplicator import NewsDeduplicator
from src.news_engine.event_clusterer import NewsEventClusterer
from src.news_engine.google_news_rss_provider import GoogleNewsRSSProvider
from src.news_engine.relevance_v2 import NiftyRelevanceEngineV2, STREAMS, recency
from src.news_engine.source_authority import classify_source
from src.pipeline.news_pipeline import _focused_streams, NewsPipeline


NOW = datetime.now(timezone.utc).replace(microsecond=0)


def item(identifier: str, headline: str, publisher: str, *, tier: str = "TIER_C_ESTABLISHED_MEDIA",
         category: str = "Crude", countries: list[str] | None = None,
         stream: str = "CRUDE_ENERGY", hours_ago: int = 1) -> NewsItem:
    published = (NOW - timedelta(hours=hours_ago)).isoformat().replace("+00:00", "Z")
    return NewsItem(
        id=identifier, headline=headline, summary_snippet="Oil shipping risk affects India import costs.",
        source_name=publisher, source_type="official" if tier == "TIER_A_PRIMARY" else "media",
        original_url=f"https://example.com/{identifier}", discovery_url=f"https://news.google.com/{identifier}",
        discovered_via="test", provider_id="test", published_at=published, received_at=published,
        age_seconds=hours_ago * 3600, freshness_status="fresh", quality_status="high",
        verification_status="confirmed" if tier == "TIER_A_PRIMARY" else "unverified",
        category=category, event_type=category, affected_symbols=[], affected_sectors=[],
        nifty_relevance_score=8.0, expected_direction="negative", impact_strength="high",
        impact_duration="daily", confidence=0.8, publisher=publisher, source_tier=tier,
        discovery_stream=stream, related_countries=countries or ["MIDDLE_EAST"],
        affected_channels=["CRUDE", "INR", "INDEX"], assessment_reasons=["India oil-import transmission"],
        recency_state="RECENT", priority_score=100.0,
    )


def test_ten_focused_bounded_discovery_streams() -> None:
    universe = {f"SYM{i:02d}": f"Company {i}" for i in range(50)}
    providers = _focused_streams(universe)
    assert len(providers) == 10
    assert set(stream for provider in providers for stream in provider.discovery_streams) == set(STREAMS)
    corporate = next(provider for provider in providers if provider.provider_name.endswith("nifty_corporate"))
    assert len(corporate.queries) == 4
    assert corporate.refresh_interval >= 900


def test_normalization_rejects_missing_real_timestamp_and_sanitizes_html() -> None:
    valid = NewsPipeline._normalize_story({
        "headline": "<b>Fed decision</b>", "source_name": "Reuters",
        "published_at": "2026-08-09T00:00:00Z", "summary_snippet": "<i>Rates</i>",
    })
    assert valid and valid["headline"] == "Fed decision" and valid["summary_snippet"] == "Rates"
    assert NewsPipeline._normalize_story({"headline": "Fed", "source_name": "Reuters"}) is None


def test_explicit_source_authority_tiers_are_separate() -> None:
    assert classify_source("Federal Reserve Board", source_type="official") == "TIER_A_PRIMARY"
    assert classify_source("Reuters") == "TIER_B_HIGH_TRUST"
    assert classify_source("Moneycontrol") == "TIER_C_ESTABLISHED_MEDIA"
    assert classify_source("Unknown Blog") == "TIER_D_DISCOVERY"


def test_exact_and_near_duplicate_removal_preserves_provenance() -> None:
    raw = [
        {"headline": "Oil surges as Hormuz shipping risk grows", "source_name": "Reuters", "published_at": "2026-08-09T00:00:00Z", "original_url": "https://x.test/a?utm_source=a"},
        {"headline": "Oil surges as Hormuz shipping risk grows", "source_name": "CNBC", "published_at": "2026-08-09T00:10:00Z", "original_url": "https://x.test/a"},
    ]
    unique = NewsDeduplicator.deduplicate(raw)
    assert len(unique) == 1
    assert {row["publisher"] for row in unique[0]["provenance"]} == {"Reuters", "CNBC"}


def test_near_duplicate_outside_time_window_is_not_removed() -> None:
    raw = [
        {"headline": "Fed holds rates after policy meeting", "source_name": "Reuters", "published_at": "2026-08-01T00:00:00Z"},
        {"headline": "Fed holds rates after policy meeting", "source_name": "Reuters", "published_at": "2026-08-09T00:00:00Z"},
    ]
    assert len(NewsDeduplicator.deduplicate(raw)) == 2


def test_event_clustering_and_cross_source_confirmation() -> None:
    rows = [
        item("a", "Hormuz closure threat pushes crude oil higher", "Reuters", tier="TIER_B_HIGH_TRUST"),
        item("b", "Crude oil rises on Hormuz shipping closure threat", "CNBC"),
        item("c", "Official warning on Hormuz oil shipping disruption", "Federal Reserve Board", tier="TIER_A_PRIMARY"),
    ]
    clusters = NewsEventClusterer.cluster(rows)
    assert len(clusters) == 1
    assert clusters[0].article_count == 3
    assert clusters[0].verification_strength == "VERY_HIGH"
    assert len(clusters[0].publishers) == 3


def test_unrelated_events_do_not_cluster() -> None:
    crude = item("a", "Hormuz closure pushes oil higher", "Reuters")
    fed = replace(item("b", "Federal Reserve cuts rates unexpectedly", "CNBC"), category="Macro", discovery_stream="FED_US_MACRO", related_countries=["US"])
    assert len(NewsEventClusterer.cluster([crude, fed])) == 2


def test_nifty_relevance_requires_geopolitical_transmission() -> None:
    remote = NiftyRelevanceEngineV2.assess("Leaders exchange statements", "regional diplomatic dispute", "Geopolitics", "GEOPOLITICS", "TIER_B_HIGH_TRUST", {})
    transmitted = NiftyRelevanceEngineV2.assess("Hormuz shipping closure threatens crude oil", "sanctions may disrupt oil trade", "Geopolitics", "GEOPOLITICS", "TIER_B_HIGH_TRUST", {})
    assert remote["nifty_relevance_score"] <= 2.0
    assert transmitted["nifty_relevance_score"] >= 6.5
    assert "CRUDE" in transmitted["affected_channels"]


def test_crude_fed_and_nifty_company_rules() -> None:
    crude = NiftyRelevanceEngineV2.assess("Brent crude surges on supply disruption", "", "Crude", "CRUDE_ENERGY", "TIER_B_HIGH_TRUST", {})
    fed = NiftyRelevanceEngineV2.assess("Federal Reserve surprises with rate hike", "Treasury yields surge", "Macro", "FED_US_MACRO", "TIER_A_PRIMARY", {})
    company = NiftyRelevanceEngineV2.assess("RELIANCE announces acquisition", "", "Corporate", "NIFTY_CORPORATE", "TIER_C_ESTABLISHED_MEDIA", {"RELIANCE": "Reliance Industries Limited"})
    assert crude["impact_level"] == "HIGH" and "INR" in crude["affected_channels"]
    assert fed["impact_level"] == "HIGH" and "YIELDS" in fed["affected_channels"]
    assert company["nifty_relevance_score"] >= 8 and company["related_symbols"] == ["RELIANCE"]


def test_recency_decay_and_priority_ordering() -> None:
    _, recent_state, recent_decay = recency((NOW - timedelta(minutes=30)).isoformat(), NOW)
    _, stale_state, stale_decay = recency((NOW - timedelta(days=5)).isoformat(), NOW)
    assert recent_state == "BREAKING" and stale_state == "STALE" and recent_decay > stale_decay
    recent = item("recent", "Hormuz shipping oil disruption", "Reuters", hours_ago=1)
    stale = replace(item("stale", "Hormuz shipping oil disruption", "Reuters", hours_ago=120), priority_score=10)
    assert NewsEventClusterer.cluster([stale, recent])[0].last_updated == recent.published_at


def test_official_sebi_timestamp_format_remains_valid() -> None:
    normalized = NewsPipeline._normalize_story({
        "headline": "SEBI official order", "source_name": "SEBI",
        "published_at": "07 Aug, 2026 +0530", "source_type": "official",
    })
    assert normalized is not None


def test_pipeline_persists_compiled_articles_clusters_provider_and_query_state(tmp_path: Path) -> None:
    rss = b"""<rss><channel><item><title>Brent oil surges on Hormuz risk - Reuters</title><link>https://news.google.com/a</link><pubDate>Sun, 09 Aug 2026 00:00:00 GMT</pubDate><description><![CDATA[<b>Oil risk</b>]]></description><source>Reuters</source></item></channel></rss>"""
    provider = GoogleNewsRSSProvider(
        queries=[{"query": "Brent crude", "category": "Crude", "stream": "CRUDE_ENERGY"}],
        xml_fixture=rss, provider_name="fixture_crude",
    )
    cache = tmp_path / "news.json"
    context = NewsPipeline(providers=[provider], cache_file=cache).run("2026-08-09T00:01:00Z")
    persisted = json.loads(cache.read_text(encoding="utf-8"))
    assert context.items and context.event_clusters
    assert persisted["compiled"]["items"] and persisted["compiled"]["event_clusters"]
    assert persisted["providers"]["fixture_crude"]["query_state"][0]["stream"] == "CRUDE_ENERGY"


def test_injected_test_pipeline_cannot_overwrite_production_cache() -> None:
    pipeline = NewsPipeline(providers=[])
    assert pipeline.persistence_enabled is False


def test_canonical_and_workspace_tab_propagation() -> None:
    cluster = NewsEventClusterer.cluster([item("a", "Hormuz oil shipping disruption", "Reuters")])[0].to_dict()
    payload = {"marketContext": {}, "optionContext": {}, "newsSentiment": {"items": [{"id": "a"}], "event_clusters": [cluster], "coverage_status": "PARTIAL"}}
    state = WorkstationStateService.build_from_legacy(payload).to_dict()
    assert state["news_intelligence"]["event_clusters"][0]["event_cluster_id"] == cluster["event_cluster_id"]
    root = Path(__file__).parents[1] / "src" / "frontend" / "components"
    news_ui = (root / "NewsIntelligence.tsx").read_text(encoding="utf-8")
    assert "data-event-cluster" in news_ui and "Economic calendar scope" in news_ui and "Corporate scope" in news_ui
    assert "data-overnight-cluster" in (root / "PreMarketPlannerWorkspace.tsx").read_text(encoding="utf-8")
    assert "CANONICAL GLOBAL EVENTS" in (root / "IntradayAssistant.tsx").read_text(encoding="utf-8")
