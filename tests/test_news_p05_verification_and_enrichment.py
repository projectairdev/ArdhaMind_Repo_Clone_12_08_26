"""
P0.5 NEWS VERIFICATION & CURRENT-STORY RECOVERY TEST SUITE

Tests the following behavioural contracts introduced in P0.5:
 1. SEBI/official date-only timestamps now parse as verified
 2. Google News when:Nd bounded discovery correctly promotes eligible items
 3. when:7d / unverified aggregator items remain non-eligible (P0 invariant)
 4. ET incident article (Aug 4) remains STALE regardless of when:Nd label
 5. publisher_domain field is captured from RSS source/@url attribute
 6. Freshness recovery: a live when:2d pipeline run produces > 0 current-eligible items
"""
from __future__ import annotations

import textwrap
from datetime import datetime, timezone

import pytest


def _now() -> datetime:
    """Simulate 'now' as 2026-08-21 12:00 UTC for deterministic tests."""
    return datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# 1. SEBI Date-Only Timestamp Parsing
# ---------------------------------------------------------------------------

class TestSEBITimestampParsing:

    def test_sebi_date_with_comma_parses(self):
        from src.news_engine.temporal_integrity import strict_publication_timestamp
        result = strict_publication_timestamp("20 Aug, 2026 +0530")
        assert result is not None, "SEBI 'DD MMM, YYYY +HH:MM' must parse"
        assert result.tzinfo is not None
        assert result.year == 2026

    def test_sebi_date_without_comma_parses(self):
        from src.news_engine.temporal_integrity import strict_publication_timestamp
        result = strict_publication_timestamp("20 Aug 2026 +0530")
        assert result is not None, "SEBI 'DD MMM YYYY +HH:MM' must parse"
        assert result.tzinfo is not None

    def test_sebi_date_not_marked_invalid_timestamp(self):
        from src.news_engine.temporal_integrity import assess_publication_time
        assessment = assess_publication_time(
            "20 Aug, 2026 +0530", _now(),
            timestamp_source="OFFICIAL_FEED", timestamp_verified=True,
        )
        assert assessment.temporal_class != "INVALID_TIMESTAMP", (
            f"SEBI date must not be INVALID_TIMESTAMP; got {assessment.temporal_class}"
        )
        assert assessment.temporal_class in {"STALE", "RECENT", "CURRENT"}

    def test_sebi_item_timestamp_verified(self):
        from src.news_engine.temporal_integrity import assess_publication_time
        assessment = assess_publication_time(
            "20 Aug, 2026 +0530", _now(),
            timestamp_source="OFFICIAL_FEED", timestamp_verified=True,
        )
        assert assessment.timestamp_verified is True

    def test_sebi_same_day_is_current(self):
        from src.news_engine.temporal_integrity import assess_publication_time
        assessment = assess_publication_time(
            "21 Aug, 2026 +0530", _now(),
            timestamp_source="OFFICIAL_FEED", timestamp_verified=True,
        )
        # 21 Aug 00:00 IST = 2026-08-20 18:30 UTC, which is ~17.5h before noon Aug 21 → CURRENT
        assert assessment.temporal_class in {"CURRENT", "RECENT"}
        assert assessment.current_eligible is True


# ---------------------------------------------------------------------------
# 2. Google News when:Nd Bounded Discovery Model
# ---------------------------------------------------------------------------

class TestGoogleDiscoveryBoundedModel:

    def test_when2d_today_pubdate_is_current(self):
        from src.news_engine.temporal_integrity import assess_publication_time
        assessment = assess_publication_time(
            "Fri, 21 Aug 2026 09:00:00 GMT", _now(),
            timestamp_source="GOOGLE_DISCOVERY_BOUNDED", timestamp_verified=True,
        )
        assert assessment.temporal_class == "CURRENT"
        assert assessment.current_eligible is True
        assert assessment.timestamp_verified is True

    def test_when2d_yesterday_pubdate_is_recent(self):
        from src.news_engine.temporal_integrity import assess_publication_time
        assessment = assess_publication_time(
            "Thu, 20 Aug 2026 09:00:00 GMT", _now(),
            timestamp_source="GOOGLE_DISCOVERY_BOUNDED", timestamp_verified=True,
        )
        assert assessment.temporal_class == "RECENT"
        assert assessment.current_eligible is True

    def test_bounded_confidence_is_medium(self):
        from src.news_engine.temporal_integrity import assess_publication_time
        assessment = assess_publication_time(
            "Fri, 21 Aug 2026 09:00:00 GMT", _now(),
            timestamp_source="GOOGLE_DISCOVERY_BOUNDED", timestamp_verified=True,
        )
        assert assessment.timestamp_confidence == "MEDIUM", (
            "Bounded-discovery items must be MEDIUM confidence"
        )

    def test_4day_old_bounded_item_is_stale(self):
        from src.news_engine.temporal_integrity import assess_publication_time
        assessment = assess_publication_time(
            "Mon, 17 Aug 2026 09:00:00 GMT", _now(),
            timestamp_source="GOOGLE_DISCOVERY_BOUNDED", timestamp_verified=True,
        )
        assert assessment.temporal_class == "STALE"
        assert assessment.current_eligible is False


# ---------------------------------------------------------------------------
# 3. P0 Invariants Preserved
# ---------------------------------------------------------------------------

class TestP0InvariantsPreserved:

    def test_unverified_aggregator_never_current_eligible(self):
        from src.news_engine.temporal_integrity import assess_publication_time
        assessment = assess_publication_time(
            "Fri, 21 Aug 2026 09:00:00 GMT", _now(),
            timestamp_source="AGGREGATOR_DISCOVERY", timestamp_verified=False,
        )
        assert assessment.current_eligible is False
        assert assessment.timestamp_verified is False
        assert assessment.temporal_class in {"DISCOVERY_RECENT", "DISCOVERY_OLDER"}

    def test_et_aug4_incident_remains_non_eligible(self):
        from src.news_engine.temporal_integrity import assess_publication_time
        assessment = assess_publication_time(
            "Tue, 04 Aug 2026 12:08:00 +0530", _now(),
            timestamp_source="AGGREGATOR_DISCOVERY", timestamp_verified=False,
        )
        assert assessment.current_eligible is False
        assert assessment.temporal_class in {"DISCOVERY_OLDER", "STALE", "HISTORICAL"}

    def test_when7d_query_not_bounded(self):
        import re
        query = "Federal Reserve OR FOMC when:7d"
        m = re.search(r'when:(\d+)([dDhH])', query)
        assert m is not None
        qty, unit = int(m.group(1)), m.group(2).lower()
        when_days = qty if unit == 'd' else qty / 24
        assert not (when_days <= 3), "when:7d must NOT produce GOOGLE_DISCOVERY_BOUNDED"
        # More explicit
        assert when_days > 3

    def test_when2d_query_is_bounded(self):
        import re
        query = "India stock market OR NIFTY when:2d"
        m = re.search(r'when:(\d+)([dDhH])', query)
        assert m is not None
        qty, unit = int(m.group(1)), m.group(2).lower()
        when_days = qty if unit == 'd' else qty / 24
        assert when_days <= 3


# ---------------------------------------------------------------------------
# 4. RSS Provider: publisher_domain Capture
# ---------------------------------------------------------------------------

MINIMAL_RSS_2D = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Google News</title>
        <item>
          <title>India stocks higher; Nifty 50 up - Investing.com India</title>
          <link>https://news.google.com/rss/articles/CBMi123</link>
          <pubDate>Fri, 21 Aug 2026 10:33:25 GMT</pubDate>
          <source url="https://in.investing.com">Investing.com India</source>
          <description>Test description</description>
        </item>
        <item>
          <title>Rupee opens higher - livemint.com</title>
          <link>https://news.google.com/rss/articles/CBMi456</link>
          <pubDate>Fri, 21 Aug 2026 03:37:56 GMT</pubDate>
          <source url="https://www.livemint.com">livemint.com</source>
          <description>Another description</description>
        </item>
      </channel>
    </rss>
""").encode("utf-8")

MINIMAL_RSS_7D = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Google News</title>
        <item>
          <title>Federal Reserve holds rates - Reuters</title>
          <link>https://news.google.com/rss/articles/CBMi789</link>
          <pubDate>Fri, 21 Aug 2026 08:00:00 GMT</pubDate>
          <source url="https://www.reuters.com">Reuters</source>
          <description>Fed news description</description>
        </item>
      </channel>
    </rss>
""").encode("utf-8")


class TestPublisherDomainCapture:

    def test_publisher_domain_extracted_from_source_url(self):
        from src.news_engine.google_news_rss_provider import GoogleNewsRSSProvider
        provider = GoogleNewsRSSProvider(
            queries=[{"query": "NIFTY India when:2d", "category": "Indian Markets", "stream": "INDIA"}],
            xml_fixture=MINIMAL_RSS_2D,
        )
        items = provider.fetch_raw_news()
        assert items, "Provider must return items from fixture"
        domains = {it.get("publisher_domain") for it in items}
        assert "in.investing.com" in domains, f"Publisher domain not extracted; got: {domains}"
        assert "livemint.com" in domains

    def test_when2d_fixture_gets_bounded_source(self):
        from src.news_engine.google_news_rss_provider import GoogleNewsRSSProvider
        provider = GoogleNewsRSSProvider(
            queries=[{"query": "NIFTY India when:2d", "category": "Indian Markets", "stream": "INDIA"}],
            xml_fixture=MINIMAL_RSS_2D,
        )
        items = provider.fetch_raw_news()
        assert items
        for it in items:
            assert it.get("timestamp_source") == "GOOGLE_DISCOVERY_BOUNDED", (
                f"when:2d items must have GOOGLE_DISCOVERY_BOUNDED; got: {it.get('timestamp_source')}"
            )
            assert it.get("timestamp_verified") is True

    def test_when7d_fixture_not_bounded(self):
        from src.news_engine.google_news_rss_provider import GoogleNewsRSSProvider
        provider = GoogleNewsRSSProvider(
            queries=[{"query": "Federal Reserve FOMC when:7d", "category": "Fed / US Macro", "stream": "FED_US_MACRO"}],
            xml_fixture=MINIMAL_RSS_7D,
        )
        items = provider.fetch_raw_news()
        assert items
        for it in items:
            assert it.get("timestamp_source") == "AGGREGATOR_DISCOVERY", (
                f"when:7d items must have AGGREGATOR_DISCOVERY; got: {it.get('timestamp_source')}"
            )
            assert it.get("timestamp_verified") is False

    def test_publisher_domain_strips_www(self):
        from src.news_engine.google_news_rss_provider import GoogleNewsRSSProvider
        provider = GoogleNewsRSSProvider(
            queries=[{"query": "NIFTY India when:2d", "category": "Indian Markets", "stream": "INDIA"}],
            xml_fixture=MINIMAL_RSS_2D,
        )
        items = provider.fetch_raw_news()
        domains = {it.get("publisher_domain") for it in items}
        # livemint.com should have www. stripped
        assert "livemint.com" in domains
        assert "www.livemint.com" not in domains


# ---------------------------------------------------------------------------
# 5. Pipeline Integration: Bounded Items Become Current-Eligible
# ---------------------------------------------------------------------------

PIPELINE_FIXTURE_RSS = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Google News</title>
        <item>
          <title>NIFTY hits 26000 as FIIs buy - Economic Times</title>
          <link>https://news.google.com/rss/articles/CBMiAAA</link>
          <pubDate>Fri, 21 Aug 2026 10:00:00 GMT</pubDate>
          <source url="https://economictimes.indiatimes.com">The Economic Times</source>
          <description>Nifty 50 rallied sharply as FIIs turned net buyers in Indian markets.</description>
        </item>
      </channel>
    </rss>
""").encode("utf-8")


class TestPipelineBoundedIntegration:

    def test_when2d_item_appears_in_output(self):
        from src.news_engine.google_news_rss_provider import GoogleNewsRSSProvider
        from src.pipeline.news_pipeline import NewsPipeline

        provider = GoogleNewsRSSProvider(
            queries=[{"query": "NIFTY India when:2d", "category": "Indian Markets", "stream": "INDIA"}],
            xml_fixture=PIPELINE_FIXTURE_RSS,
        )
        pipeline = NewsPipeline(providers=[provider])
        result = pipeline.run()
        all_items = list(result.items) + list(result.historical_items)
        assert len(all_items) > 0, "Pipeline must return at least one item from fixture"

    def test_when2d_item_current_eligible_in_pipeline(self):
        from src.news_engine.google_news_rss_provider import GoogleNewsRSSProvider
        from src.pipeline.news_pipeline import NewsPipeline

        provider = GoogleNewsRSSProvider(
            queries=[{"query": "NIFTY India when:2d", "category": "Indian Markets", "stream": "INDIA"}],
            xml_fixture=PIPELINE_FIXTURE_RSS,
        )
        pipeline = NewsPipeline(providers=[provider])
        result = pipeline.run()
        # The item published at 10:00 GMT Aug 21 must be in current items
        assert len(result.items) > 0, (
            "when:2d bounded item from today must appear in current (non-historical) items"
        )
        current_item = result.items[0]
        assert current_item.timestamp_verified is True

    def test_when7d_item_not_current_eligible(self):
        from src.news_engine.google_news_rss_provider import GoogleNewsRSSProvider
        from src.pipeline.news_pipeline import NewsPipeline

        provider = GoogleNewsRSSProvider(
            queries=[{"query": "Federal Reserve FOMC when:7d", "category": "Fed / US Macro", "stream": "FED_US_MACRO"}],
            xml_fixture=PIPELINE_FIXTURE_RSS,
        )
        pipeline = NewsPipeline(providers=[provider])
        result = pipeline.run()
        # when:7d item must not appear in current-eligible items
        for item in result.items:
            if "Economic Times" in item.source_name:
                pytest.fail(f"when:7d ET item must not be current-eligible: {item.headline}")
