"""E2 global event-intelligence pipeline with bounded provider isolation."""
from __future__ import annotations

import json
import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.models.news_context_v2 import CorporateAnnouncement, NewsContext, NewsItem, ScheduledEvent
from src.news_engine.deduplicator import NewsDeduplicator
from src.news_engine.event_classifier import EventClassifier
from src.news_engine.event_clusterer import NewsEventClusterer
from src.news_engine.financial_news_provider import MarketauxFinancialNewsProvider
from src.news_engine.google_news_rss_provider import GoogleNewsRSSProvider
from src.news_engine.normalizer import clean_html_text
from src.news_engine.official_source_provider import OfficialSourceProvider
from src.news_engine.provider import BaseNewsProvider
from src.news_engine.relevance_v2 import NiftyRelevanceEngineV2, STREAMS, load_nifty_universe, parse_timestamp, recency
from src.news_engine.source_authority import authority_rank, classify_source
from src.news_engine.temporal_integrity import assess_publication_time, live_window, strict_publication_timestamp
from src.utils import setup_logger

logger = setup_logger("NewsPipeline")
CACHE_FILE_PATH = Path(".cache") / "news_cache.json"


def _focused_streams(nifty_universe: Dict[str, str]) -> List[GoogleNewsRSSProvider]:
    configs = [
        ("india", "INDIA", "India stock market OR NIFTY OR Indian economy OR Indian banking OR rupee OR foreign investors India when:2d", "Indian Markets", 900.0),
        ("us_markets", "US_MARKETS", "S&P 500 OR Nasdaq OR Dow OR Wall Street OR US stock futures OR US market selloff OR US market rally when:2d", "US Markets", 900.0),
        ("fed_us_macro", "FED_US_MACRO", "Federal Reserve OR FOMC OR US CPI OR US inflation OR nonfarm payrolls OR US GDP OR PMI OR Treasury yields when:7d", "Fed / US Macro", 900.0),
        ("china_asia", "CHINA_ASIA", "China economy OR PBOC OR Chinese markets OR Nikkei OR Hang Seng OR Asian markets OR Bank of Japan when:3d", "China / Asia", 1200.0),
        ("europe", "EUROPE", "ECB OR European markets OR Eurozone inflation OR European economy when:7d", "Europe", 1800.0),
        ("crude_energy", "CRUDE_ENERGY", "Brent crude OR WTI OR OPEC OR oil supply disruption OR Strait of Hormuz OR energy prices when:7d", "Crude / Energy", 900.0),
        ("geopolitics", "GEOPOLITICS", "war escalation OR sanctions OR Middle East tensions OR Russia Ukraine OR Israel Iran OR India Pakistan OR Red Sea shipping disruption OR trade war tariffs when:7d", "Geopolitics", 900.0),
        ("currency_rates", "CURRENCY_RATES", "USD INR OR Indian rupee OR Dollar Index OR DXY OR US Treasury yields OR dollar surge OR dollar decline when:3d", "Currency / Rates", 900.0),
        ("global_risk", "GLOBAL_RISK", "banking crisis OR sovereign debt OR financial instability OR emergency rate decision OR political shock OR global recession when:7d", "Global Risk", 1800.0),
    ]
    providers = [
        GoogleNewsRSSProvider(
            queries=[{"query": query, "category": category, "stream": stream}],
            provider_name=f"google_news_{name}", refresh_interval=interval,
        )
        for name, stream, query, category, interval in configs
    ]
    symbols = sorted(nifty_universe)
    grouped = [symbols[index:index + 13] for index in range(0, len(symbols), 13)] if symbols else []
    queries = [
        {"query": f"({' OR '.join(group)}) NSE India earnings acquisition order board when:7d", "category": "NIFTY Corporate", "stream": "NIFTY_CORPORATE"}
        for group in grouped
    ] or [{"query": "NIFTY 50 companies earnings acquisition order board India when:7d", "category": "NIFTY Corporate", "stream": "NIFTY_CORPORATE"}]
    providers.append(GoogleNewsRSSProvider(
        queries=queries, provider_name="google_news_nifty_corporate",
        refresh_interval=1800.0, max_items_per_query=10,
    ))
    return providers


def _default_providers() -> List[BaseNewsProvider]:
    universe = load_nifty_universe()
    providers: List[BaseNewsProvider] = list(_focused_streams(universe))
    providers.extend([
        OfficialSourceProvider("rbi_press_releases", "https://www.rbi.org.in/pressreleases_rss.xml", discovery_stream="INDIA"),
        OfficialSourceProvider("rbi_notifications", "https://www.rbi.org.in/notifications_rss.xml", discovery_stream="INDIA"),
        OfficialSourceProvider("sebi_rss", "https://www.sebi.gov.in/sebirss.xml", discovery_stream="INDIA"),
        OfficialSourceProvider("pib_market_releases", "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3", refresh_interval=900.0, market_relevant_only=True, discovery_stream="INDIA"),
        OfficialSourceProvider(
            "federal_reserve_monetary", "https://www.federalreserve.gov/feeds/press_monetary.xml",
            refresh_interval=900.0, source_name="Federal Reserve Board",
            canonical_event_category="FED_US_MACRO", discovery_stream="FED_US_MACRO",
        ),
        OfficialSourceProvider(
            "ecb_press_releases", "https://www.ecb.europa.eu/rss/press.html",
            refresh_interval=1800.0, source_name="European Central Bank",
            canonical_event_category="EUROPE", discovery_stream="EUROPE",
        ),
        OfficialSourceProvider(
            "bls_latest_releases", "https://www.bls.gov/feed/bls_latest.rss",
            refresh_interval=1800.0, source_name="U.S. Bureau of Labor Statistics",
            canonical_event_category="FED_US_MACRO", discovery_stream="FED_US_MACRO",
        ),
    ])
    selected = os.getenv("FINANCIAL_NEWS_PROVIDER", "").strip().lower()
    api_provider = MarketauxFinancialNewsProvider()
    if selected not in {"", "marketaux"}:
        api_provider.status = "disabled"
        api_provider.operational_error_reason = "unsupported_provider_selection"
        api_provider.failure_detail = f"FINANCIAL_NEWS_PROVIDER={selected} is not implemented."
    providers.append(api_provider)
    return providers


class NewsPipeline:
    def __init__(self, providers: Optional[List[BaseNewsProvider]] = None, cache_file: Optional[Path] = None) -> None:
        self.cache_file = cache_file or CACHE_FILE_PATH
        # Injected providers without an explicit cache are isolated test/runtime
        # compositions and must never overwrite the production warm-start file.
        self.persistence_enabled = providers is None or cache_file is not None
        self.providers = providers if providers is not None else _default_providers()
        self.nifty_universe = load_nifty_universe()
        self.last_compiled: Dict[str, Any] = {}
        if providers is None or cache_file is not None:
            self.load_cache()

    def save_cache(self, compiled: Optional[Dict[str, Any]] = None) -> None:
        if not self.persistence_enabled:
            return
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "saved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "providers": {provider.provider_name: provider.get_state() for provider in self.providers},
                "compiled": compiled or self.last_compiled,
            }
            temporary = self.cache_file.with_suffix(self.cache_file.suffix + ".tmp")
            temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            temporary.replace(self.cache_file)
        except Exception as exc:
            logger.warning(f"Failed to persist news cache: {exc}")

    def load_cache(self) -> None:
        if not self.cache_file.exists():
            return
        try:
            payload = json.loads(self.cache_file.read_text(encoding="utf-8"))
            states = payload.get("providers") or {}
            self.last_compiled = payload.get("compiled") or {}
            for provider in self.providers:
                state = states.get(provider.provider_name)
                if not state:
                    continue
                state = dict(state)
                if not state.get("cached_items") and state.get("status") not in {"ready", "disabled"}:
                    state.update({"last_fetch_timestamp": 0.0, "cb_state": "closed", "circuit_open_until": 0.0})
                provider.restore_state(state)
        except Exception as exc:
            logger.warning(f"Failed to load news cache: {exc}")

    @staticmethod
    def _normalize_story(story: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        headline = clean_html_text(story.get("headline") or story.get("title") or "", max_length=200)
        publisher = clean_html_text(story.get("source_name") or story.get("publisher") or "", max_length=100)
        published = str(story.get("published_at") or story.get("pubDate") or "").strip()
        if not headline or not publisher or parse_timestamp(published) is None:
            return None
        summary = clean_html_text(story.get("summary_snippet") or story.get("description") or "", max_length=500)
        normalized = dict(story)
        normalized.update({
            "headline": headline,
            "summary_snippet": summary,
            "source_name": publisher,
            "publisher": publisher,
            "published_at": published,
            "received_at": str(story.get("received_at") or ""),
            "source_authority": story.get("source_authority") or ("PRIMARY" if story.get("source_type") == "official" else "DISCOVERY"),
            "discovery_stream": str(story.get("discovery_stream") or story.get("discovery_category") or "OTHER").upper().replace(" ", "_"),
            "language": str(story.get("language") or "en"),
        })
        return normalized

    def _build_item(self, story: Dict[str, Any], now: datetime) -> NewsItem:
        source_type = str(story.get("source_type") or "unknown")
        source_url = str(story.get("original_url") or story.get("discovery_url") or "")
        tier = classify_source(str(story["source_name"]), source_url, source_type)
        category = EventClassifier.classify(story["headline"], story["summary_snippet"])
        stream = str(story.get("discovery_stream") or "OTHER")
        relevance = NiftyRelevanceEngineV2.assess(
            story["headline"], story["summary_snippet"], category, stream, tier, self.nifty_universe,
        )
        temporal = story["_temporal_assessment"]
        age, recency_state, decay = recency(story["published_at"], now)
        impact_rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}[relevance["impact_level"]]
        priority = round(relevance["nifty_relevance_score"] * 10 + impact_rank * 8 + authority_rank(tier) * 3 + decay * 10, 2)
        symbols = list(dict.fromkeys([*(story.get("related_symbols") or []), *relevance["related_symbols"]]))
        normalized_timestamp = temporal.published_at_utc.isoformat().replace("+00:00", "Z") if temporal.published_at_utc else ""
        return NewsItem(
            id=story["id"], headline=story["headline"], summary_snippet=story["summary_snippet"],
            source_name=story["source_name"], source_type=source_type,
            original_url=str(story.get("original_url") or ""), discovery_url=str(story.get("discovery_url") or ""),
            discovered_via=str(story.get("discovered_via") or ""),
            provider_id=str(story.get("provider_id") or story.get("discovered_via") or ""),
            published_at=story["published_at"], received_at=str(story.get("received_at") or ""),
            age_seconds=age, freshness_status=temporal.temporal_class.lower(),
            quality_status="high" if tier in {"TIER_A_PRIMARY", "TIER_B_HIGH_TRUST"} else "medium" if tier == "TIER_C_ESTABLISHED_MEDIA" else "discovery",
            verification_status="confirmed" if tier == "TIER_A_PRIMARY" else "verified" if tier == "TIER_B_HIGH_TRUST" else str(story.get("verification_status") or "unverified"),
            category=category, event_type=category, affected_symbols=symbols,
            affected_sectors=[], nifty_relevance_score=relevance["nifty_relevance_score"],
            expected_direction=relevance["expected_direction"], impact_strength=relevance["impact_level"].lower(),
            impact_duration="weekly" if category in {"Macro", "Geopolitics", "RBI", "SEBI"} else "daily",
            confidence=1.0 if tier == "TIER_A_PRIMARY" else 0.75 if tier == "TIER_B_HIGH_TRUST" else 0.6 if tier == "TIER_C_ESTABLISHED_MEDIA" else 0.4,
            discovery_query=str(story.get("discovery_query") or ""), discovery_category=str(story.get("discovery_category") or category),
            why_it_matters=relevance["why_it_matters"], assessment_reasons=relevance["assessment_reasons"],
            rule_version=relevance["rule_version"], duplicate_group_id=story.get("duplicate_group_id"),
            warnings=list(story.get("warnings") or []), canonical_event_category=str(story.get("canonical_event_category") or ""),
            source_authority=str(story.get("source_authority") or ""),
            source_reference=str(story.get("source_reference") or story.get("discovery_url") or story.get("original_url") or ""),
            official_subcategory=str(story.get("official_subcategory") or ""), publisher=story["source_name"],
            source_tier=tier, discovery_stream=stream, language=str(story.get("language") or "en"),
            related_countries=relevance["related_countries"], affected_channels=relevance["affected_channels"],
            recency_state=recency_state, priority_score=priority,
            updated_at=str(story.get("updated_at") or ""), normalized_timestamp=normalized_timestamp,
            timestamp_source=temporal.timestamp_source, timestamp_validity=temporal.timestamp_validity,
            timestamp_confidence=temporal.timestamp_confidence, temporal_class=temporal.temporal_class,
            canonical_eligible=temporal.current_eligible, workspace_eligible=temporal.current_eligible,
            cache_restored=bool(story.get("_cache_restored")),
            age_minutes=round(temporal.age_seconds / 60, 2) if temporal.age_seconds is not None else None,
        )

    def run(self, current_time: Optional[str] = None) -> NewsContext:
        scanned_at = current_time or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        now = strict_publication_timestamp(scanned_at) or parse_timestamp(scanned_at) or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        now = now.astimezone(timezone.utc)
        allowed_window, close_boundary = live_window(now)
        raw_stories: List[Dict[str, Any]] = []
        provider_records: Dict[str, List[Dict[str, Any]]] = {}
        errors: List[str] = []

        def fetch(provider: BaseNewsProvider) -> List[Dict[str, Any]]:
            if not provider.is_enabled:
                return []
            should_fetch = provider.should_fetch()
            if not should_fetch:
                records = [{**record, "_cache_restored": True} for record in provider.cached_items]
                if len(provider.discovery_streams) == 1 and provider.discovery_streams[0] in STREAMS:
                    records = [{**record, "discovery_stream": provider.discovery_streams[0]} for record in records]
                return records
            try:
                records = provider.fetch_raw_news()
                restored = bool(records) and provider.status != "ready"
                records = [{**record, "_cache_restored": restored} for record in records]
                if len(provider.discovery_streams) == 1 and provider.discovery_streams[0] in STREAMS:
                    records = [{**record, "discovery_stream": provider.discovery_streams[0]} for record in records]
                return records
            except Exception as exc:
                errors.append(f"Provider {provider.provider_name} failed: {exc}")
                records = [{**record, "_cache_restored": True} for record in provider.cached_items]
                if len(provider.discovery_streams) == 1 and provider.discovery_streams[0] in STREAMS:
                    records = [{**record, "discovery_stream": provider.discovery_streams[0]} for record in records]
                return records

        with ThreadPoolExecutor(max_workers=min(8, max(1, len(self.providers)))) as pool:
            futures = {provider: pool.submit(fetch, provider) for provider in self.providers}
            for provider in self.providers:
                records = futures[provider].result()
                provider_records[provider.provider_name] = records
                raw_stories.extend(records)
                provider.raw_item_count = len(records)

        normalized = [item for item in (self._normalize_story(story) for story in raw_stories) if item is not None]
        for story in normalized:
            story["_temporal_assessment"] = assess_publication_time(story.get("published_at"), now)
        eligible_stories = [story for story in normalized if story["_temporal_assessment"].current_eligible]
        historical_stories = [story for story in normalized if not story["_temporal_assessment"].current_eligible]
        unique_current = NewsDeduplicator.deduplicate(eligible_stories)
        unique_historical = NewsDeduplicator.deduplicate(historical_stories)
        items = [self._build_item(story, now) for story in unique_current]
        historical_items = [self._build_item(story, now) for story in unique_historical]

        items.sort(key=lambda item: item.priority_score, reverse=True)
        cluster_input = [item for item in [*items, *historical_items] if item.nifty_relevance_score >= 2.5]
        all_clusters = NewsEventClusterer.cluster(cluster_input)
        clusters = [cluster for cluster in all_clusters if cluster.canonical_eligible]
        historical_clusters = [cluster for cluster in all_clusters if not cluster.canonical_eligible]
        top_headlines = items[:10]
        high_impact_items = [item for item in items if item.impact_strength in {"high", "critical"}]

        event_items = [ScheduledEvent(
            id=item.id, event_name=item.headline, description=item.summary_snippet,
            scheduled_at=item.published_at, importance=item.impact_strength,
            source_name=item.source_name, verification_status=item.verification_status,
            category=item.category, expected_direction=item.expected_direction,
            relevance_score=item.nifty_relevance_score, status="completed", warnings=item.warnings,
        ) for item in items if item.source_tier == "TIER_A_PRIMARY"]
        corporate_items = [CorporateAnnouncement(
            id=item.id, company_symbol=item.affected_symbols[0] if item.affected_symbols else "GENERAL",
            announcement_type="earnings" if item.category == "Earnings" else "filing",
            headline=item.headline, description=item.summary_snippet, published_at=item.published_at,
            source_name=item.source_name, original_url=item.original_url,
            verification_status=item.verification_status, nifty_relevance_score=item.nifty_relevance_score,
            expected_direction=item.expected_direction, warnings=item.warnings,
        ) for item in items if item.category in {"Earnings", "Corporate"}]

        item_by_id = {item.id: item for item in [*items, *historical_items]}
        for provider in self.providers:
            provider.normalized_item_count = sum(1 for story in normalized if story.get("provider_id") == provider.provider_name)
            provider.unique_item_count = sum(1 for item in items if item.provider_id == provider.provider_name)
            provider.event_cluster_count = sum(1 for cluster in clusters if any(item_by_id.get(article_id) and item_by_id[article_id].provider_id == provider.provider_name for article_id in cluster.article_ids))

        coverage = self._coverage_matrix(raw_stories, normalized, items, clusters)
        active_streams = sum(row["status"] in {"READY", "HEALTHY_EMPTY"} for row in coverage)
        coverage_status = "FULL" if active_streams >= 8 else "PARTIAL" if active_streams >= 5 else "LIMITED" if active_streams else "UNAVAILABLE"
        provider_health = {provider.provider_name: provider.get_health().to_dict() for provider in self.providers}
        duplicate_count = max(0, len(eligible_stories) - len(unique_current)) + max(0, len(historical_stories) - len(unique_historical))
        tier_counts = Counter(item.source_tier for item in items)
        temporal_counts = Counter(story["_temporal_assessment"].temporal_class for story in normalized)
        invalid_raw_count = len(raw_stories) - len(normalized)
        invalid_timestamp_count = invalid_raw_count + temporal_counts.get("INVALID_TIMESTAMP", 0)
        valid_timestamp_count = len(normalized) - temporal_counts.get("INVALID_TIMESTAMP", 0)
        cache_rejected = sum(bool(story.get("_cache_restored")) and not story["_temporal_assessment"].current_eligible for story in normalized)
        current_times = [strict_publication_timestamp(item.published_at) for item in items]
        current_times = [value for value in current_times if value is not None]
        provider_trace: Dict[str, Any] = {}
        for provider in self.providers:
            records = provider_records.get(provider.provider_name, [])
            request = getattr(provider, "queries", None) or getattr(provider, "feed_url", None) or provider.__class__.__name__
            record_trace = []
            for raw in records:
                normalized_story = self._normalize_story(raw)
                temporal = assess_publication_time((normalized_story or raw).get("published_at") or raw.get("pubDate"), now)
                record_trace.append({
                    "headline": clean_html_text(raw.get("headline") or raw.get("title") or "", max_length=200),
                    "published_at": raw.get("published_at") or raw.get("pubDate"), "updated_at": raw.get("updated_at"),
                    "normalized_timestamp": temporal.published_at_utc.isoformat().replace("+00:00", "Z") if temporal.published_at_utc else None,
                    "timestamp_source": temporal.timestamp_source, "timestamp_validity": temporal.timestamp_validity,
                    "timestamp_confidence": temporal.timestamp_confidence, "temporal_class": temporal.temporal_class,
                    "age_minutes": round(temporal.age_seconds / 60, 2) if temporal.age_seconds is not None else None,
                    "cache_restored": bool(raw.get("_cache_restored")), "canonical_eligible": temporal.current_eligible,
                    "workspace_eligible": temporal.current_eligible,
                })
            provider_trace[provider.provider_name] = {
                "request": request, "last_attempted_fetch": provider.last_attempted_fetch,
                "last_successful_fetch": provider.last_successful_fetch, "raw_count": len(records), "records": record_trace,
            }
        metrics = {
            "providers_configured": len(self.providers),
            "providers_returning_usable_data": sum(health["status"] == "ready" and health["normalized_item_count"] > 0 for health in provider_health.values()),
            "focused_discovery_streams": len(STREAMS),
            "raw_articles": len(raw_stories), "normalized_articles": len(normalized), "timestamp_valid": valid_timestamp_count,
            "freshness_eligible": len(eligible_stories), "unique_articles": len(items), "unique_current_articles": len(items),
            "duplicate_articles_removed": duplicate_count,
            "event_clusters": len(clusters), "source_tier_counts": dict(tier_counts),
            "current": temporal_counts.get("CURRENT", 0), "recent": temporal_counts.get("RECENT", 0),
            "stale": temporal_counts.get("STALE", 0), "historical": temporal_counts.get("HISTORICAL", 0),
            "invalid_timestamp": invalid_timestamp_count, "current_event_clusters": len(clusters),
            "historical_event_clusters": len(historical_clusters),
            "historical_records_retained": len(historical_items) + invalid_raw_count,
            "cache_records_rejected_from_current_eligibility": cache_rejected,
            "provider_to_canonical_data_loss": max(0, len(eligible_stories) - len(unique_current) - len(items)),
            "provider_to_canonical_current_data_loss": max(0, len(eligible_stories) - len(unique_current) - len(items)),
            "canonical_to_workspace_data_loss": 0, "canonical_to_workspace_current_data_loss": 0,
            "oldest_current_timestamp": min(current_times).isoformat().replace("+00:00", "Z") if current_times else None,
            "newest_current_timestamp": max(current_times).isoformat().replace("+00:00", "Z") if current_times else None,
            "current_window_hours": int(allowed_window.total_seconds() // 3600),
            "last_valid_market_close": close_boundary.isoformat().replace("+00:00", "Z"),
        }
        overall_freshness = "fresh" if items else "unavailable"
        context = NewsContext(
            scanned_at=scanned_at, items=items, top_headlines=top_headlines,
            high_impact_items=high_impact_items, corporate_items=corporate_items,
            event_items=event_items, provider_health=provider_health,
            freshness=overall_freshness, warnings=[], errors=errors,
            generated_at=scanned_at, usable=bool(items), event_clusters=clusters,
            coverage_matrix=coverage, coverage_status=coverage_status,
            raw_article_count=len(raw_stories), normalized_article_count=len(normalized),
            unique_article_count=len(items), duplicate_article_count=duplicate_count,
            ingestion_metrics=metrics,
            historical_items=historical_items, historical_event_clusters=historical_clusters,
            temporal_diagnostics={"counts": {
                "RAW": len(raw_stories), "NORMALIZED": len(normalized), "TIMESTAMP_VALID": valid_timestamp_count,
                "CURRENT": temporal_counts.get("CURRENT", 0), "RECENT": temporal_counts.get("RECENT", 0),
                "STALE": temporal_counts.get("STALE", 0), "HISTORICAL": temporal_counts.get("HISTORICAL", 0),
                "INVALID_TIMESTAMP": invalid_timestamp_count, "CURRENT_CLUSTERS": len(clusters),
                "HISTORICAL_CLUSTERS": len(historical_clusters),
            }, "providers": provider_trace,
               "oldest_current_timestamp": metrics["oldest_current_timestamp"],
               "newest_current_timestamp": metrics["newest_current_timestamp"]},
            last_market_close_boundary=metrics["last_valid_market_close"],
            current_window_hours=metrics["current_window_hours"],
        )
        self.last_compiled = context.payload
        self.save_cache(context.payload)
        return context

    def _coverage_matrix(self, raw_stories: List[Dict[str, Any]], normalized: List[Dict[str, Any]], items: List[NewsItem], clusters: List[Any]) -> List[Dict[str, Any]]:
        rows = []
        for stream in STREAMS:
            raw = [story for story in raw_stories if story.get("discovery_stream") == stream]
            normalized_stream = [story for story in normalized if story.get("discovery_stream") == stream]
            unique = [item for item in items if item.discovery_stream == stream]
            related_clusters = [cluster for cluster in clusters if stream in cluster.discovery_streams]
            relevant_providers = [provider for provider in self.providers if stream in provider.discovery_streams]
            executed = any(provider.last_attempted_fetch for provider in relevant_providers)
            healthy = any(provider.status == "ready" for provider in relevant_providers)
            status = "READY" if raw else "HEALTHY_EMPTY" if executed and healthy else "UNAVAILABLE"
            latest = max((item.published_at for item in unique), default="")
            rows.append({
                "stream": stream,
                "sources": list(dict.fromkeys(item.publisher for item in unique)),
                "raw_items": len(raw), "normalized_items": len(normalized_stream), "unique_items": len(unique),
                "clusters": len(related_clusters), "latest_timestamp": latest,
                "status": status,
            })
        return rows
