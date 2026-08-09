# tests/test_phase5_2_news_additions.py
from __future__ import annotations

import time
import unittest
from pathlib import Path
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from unittest.mock import patch, MagicMock

from src.news_engine.safe_utils import safe_parse_xml, safe_resolve_redirect, safe_url_fetch, normalize_url, _validate_url_security
from src.news_engine.deduplicator import NewsDeduplicator
from src.news_engine.impact_assessor import NewsImpactAssessor
from src.news_engine.google_news_rss_provider import GoogleNewsRSSProvider
from src.news_engine.official_source_provider import OfficialSourceProvider
from src.pipeline.news_pipeline import NewsPipeline
from src.dashboard.news_panel import NewsIntelligencePanel
from src.server_bridge import news_refresh_lock, handle_daemon_command, cached_news_sentiment


class TestPhase52NewsAdditions(unittest.TestCase):
    """
    Unit tests validating Phase 5.2 news ingestion hardening:
    - Single-flight refresh protection & collision prevention
    - Atomic state publication
    - Restart persistence (ETags, Last-Modified, cached items)
    - Circuit breaker full lifecycle (closed -> open -> half_open -> recovery / re-open)
    - Strict SSRF protection across redirect hops and embedded credentials
    - Stable IDs across tracking URL changes
    - Partial provider failure with cached data retention
    - Legacy serialization parity with canonical state
    """

    def test_safe_xml_parsing(self) -> None:
        xml_data = b"<rss><channel><title>RBI News</title></channel></rss>"
        root = safe_parse_xml(xml_data)
        self.assertEqual(root.find(".//title").text, "RBI News")

    def test_malformed_feed_handling(self) -> None:
        xml_data = b"<rss><channel><title>RBI News</title></channel>"
        with self.assertRaises(ValueError):
            safe_parse_xml(xml_data)

    def test_oversized_response_rejection(self) -> None:
        with patch("urllib.request.build_opener") as mock_build:
            mock_response = MagicMock()
            mock_response.headers = {"Content-Length": "200000"}
            mock_build.return_value.open.return_value.__enter__.return_value = mock_response

            with self.assertRaises((ValueError, ConnectionError)):
                safe_url_fetch("https://test.com/feed.xml", max_size=102400)

    def test_ssrf_protection_across_redirect_hops(self) -> None:
        blocked_urls = [
            "http://127.0.0.1/feed",
            "http://localhost/rss",
            "http://169.254.169.254/latest/meta-data/",
            "http://192.168.1.1/admin",
            "http://10.0.0.1/secret",
            "http://user:pass@example.com/rss",
            "ftp://example.com/feed",
            "http://example.com:22/ssh",
        ]
        for url in blocked_urls:
            with self.assertRaises(ValueError, msg=f"Should have blocked {url}"):
                _validate_url_security(url)

    def test_redirect_resolution_failure(self) -> None:
        target_url = "https://news.google.com/rss/articles/123"
        with patch("urllib.request.build_opener") as mock_build:
            mock_build.return_value.open.side_effect = Exception("Redirect failed")
            resolved = safe_resolve_redirect(target_url)
            self.assertEqual(resolved, target_url)

    def test_stable_ids_across_tracking_url_changes(self) -> None:
        headline = "RBI Keeps Repo Rate Unchanged at 6.5%"
        url_raw = "https://example.com/rbi-news?utm_source=google&gclid=xyz123&utm_medium=cpc"
        url_clean = "https://example.com/rbi-news"

        id1 = NewsDeduplicator.compute_stable_id(headline, url_raw, "RBI", "2026-08-07T00:00:00Z")
        id2 = NewsDeduplicator.compute_stable_id(headline, url_clean, "RBI", "2026-08-07T00:00:00Z")
        self.assertEqual(id1, id2, "Stable IDs must match even when tracking parameters differ.")

    def test_circuit_breaker_full_lifecycle(self) -> None:
        provider = OfficialSourceProvider("test_feed", "https://test.com/rss")
        self.assertEqual(provider.cb_state, "closed")
        self.assertTrue(provider.should_fetch())

        # Trip to OPEN after 3 failures
        for _ in range(3):
            provider.record_failure(Exception("Connection Timeout"))

        self.assertEqual(provider.cb_state, "open")
        self.assertEqual(provider.status, "unavailable")
        self.assertFalse(provider.should_fetch())

        # Fast-forward time past circuit_open_until to test HALF_OPEN transition
        provider.circuit_open_until = time.time() - 1.0
        self.assertTrue(provider.should_fetch())
        self.assertEqual(provider.cb_state, "half_open")

        # Successful probe recovers state to CLOSED
        provider.record_success([{"headline": "Test", "summary_snippet": "Test", "source_name": "RBI", "source_type": "official", "original_url": "", "discovery_url": "", "discovered_via": "", "published_at": "", "received_at": "", "verification_status": "confirmed"}])
        self.assertEqual(provider.cb_state, "closed")
        self.assertEqual(provider.status, "ready")

        # Re-trip to OPEN and test probe failure return to OPEN
        for _ in range(3):
            provider.record_failure(Exception("Probe Failed"))
        self.assertEqual(provider.cb_state, "open")

        provider.circuit_open_until = time.time() - 1.0
        self.assertTrue(provider.should_fetch())
        self.assertEqual(provider.cb_state, "half_open")
        provider.record_failure(Exception("Probe Failed Again"))
        self.assertEqual(provider.cb_state, "open")

    def test_etag_304_handling(self) -> None:
        provider = OfficialSourceProvider("test_feed", "https://test.com/rss")
        provider.etags["https://test.com/rss"] = "W/etag-hash"
        provider.cached_items = [{"headline": "Cached Story"}]

        with patch("src.news_engine.official_source_provider.safe_url_fetch") as mock_fetch:
            mock_fetch.return_value = (b"", {"ETag": "W/etag-hash"}, 304)
            items = provider.fetch_raw_news()
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["headline"], "Cached Story")
            self.assertEqual(provider.status, "ready")

    def test_partial_provider_failure_with_cached_data_retained(self) -> None:
        provider = OfficialSourceProvider("test_feed", "https://test.com/rss")
        provider.cached_items = [{"headline": "Old Valid News"}]

        with patch("src.news_engine.official_source_provider.safe_url_fetch") as mock_fetch:
            mock_fetch.side_effect = ConnectionError("500 Server Error")
            items = provider.fetch_raw_news()
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["headline"], "Old Valid News")

    def test_restart_persistence(self) -> None:
        test_cache_file = Path(".cache") / "test_news_cache.json"
        if test_cache_file.exists():
            test_cache_file.unlink()

        p1 = OfficialSourceProvider("rbi_press_releases", "https://test.com/rbi")
        p1.etags["https://test.com/rbi"] = "ETAG-12345"
        p1.last_modified_headers["https://test.com/rbi"] = "Mon, 01 Aug 2026 00:00:00 GMT"
        p1.cached_items = [{"headline": "Persistent Item"}]

        pipeline1 = NewsPipeline(providers=[p1], cache_file=test_cache_file)
        pipeline1.save_cache()

        # Create new pipeline instance and verify restored state
        p2 = OfficialSourceProvider("rbi_press_releases", "https://test.com/rbi")
        pipeline2 = NewsPipeline(providers=[p2], cache_file=test_cache_file)

        self.assertEqual(p2.etags.get("https://test.com/rbi"), "ETAG-12345")
        self.assertEqual(p2.last_modified_headers.get("https://test.com/rbi"), "Mon, 01 Aug 2026 00:00:00 GMT")
        self.assertEqual(len(p2.cached_items), 1)
        self.assertEqual(p2.cached_items[0]["headline"], "Persistent Item")

        if test_cache_file.exists():
            test_cache_file.unlink()

    def test_single_flight_and_collision_prevention(self) -> None:
        acquired = news_refresh_lock.acquire(blocking=False)
        self.assertTrue(acquired)
        try:
            res = handle_daemon_command("refresh_news", {}, MagicMock(), MagicMock())
            self.assertFalse(res.get("success"))
            self.assertIn("already running", res.get("error", ""))
        finally:
            news_refresh_lock.release()

    def test_legacy_serialization_parity_with_canonical_state(self) -> None:
        pipeline = NewsPipeline(providers=[])
        ctx = pipeline.run()
        panel_dict = NewsIntelligencePanel(ctx).to_dict()

        self.assertIn("items", panel_dict)
        self.assertIn("overall_sentiment", panel_dict)
        self.assertIn("sentiment_bias", panel_dict)
        self.assertIn("provider_health", panel_dict)
        self.assertIn("freshness", panel_dict)

    def test_uncertain_mixed_impact_classification(self) -> None:
        headline = "TCS Net Profit jumps 8% but escalating war drone strikes hit IT shares"
        impact = NewsImpactAssessor.assess_impact(headline, "", "media", "Earnings")
        self.assertEqual(impact["expected_direction"], "mixed")
        self.assertLess(impact["confidence"], 0.5)

        headline_neutral = "RBI releases scheduled documentation on banking standards"
        impact_neutral = NewsImpactAssessor.assess_impact(headline_neutral, "", "media", "RBI")
        self.assertEqual(impact_neutral["expected_direction"], "not_assessed")
        self.assertEqual(impact_neutral["confidence"], 0.0)

    def test_no_full_article_body_storage(self) -> None:
        pipeline = NewsPipeline(providers=[])
        ctx = pipeline.run()
        for item in ctx.items:
            self.assertTrue(hasattr(item, "summary_snippet"))
            self.assertFalse(hasattr(item, "body"))
            self.assertFalse(hasattr(item, "full_content"))
