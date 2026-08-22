# src/news_engine/google_news_rss_provider.py
"""
GoogleNewsRSSProvider — ingests Google News RSS search query items securely.

Items are marked:
  discovered_via       = "google_news_rss"
  verification_status  = "unverified"

ETag / Last-Modified caching is used to avoid redundant fetches.
When 304 Not Modified is returned, the provider returns cached items.
"""
from __future__ import annotations

import time
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from src.news_engine.provider import BaseNewsProvider
from src.news_engine.safe_utils import safe_url_fetch, safe_parse_xml, normalize_url


class GoogleNewsRSSProvider(BaseNewsProvider):
    """
    Ingests Google News RSS search query items securely.
    """
    def __init__(
        self,
        queries: Optional[List[Union[str, Dict[str, str]]]] = None,
        refresh_interval: float = 300.0,
        xml_fixture: Optional[bytes] = None,
        provider_name: str = "google_news_rss",
        max_items_per_query: int = 20,
    ) -> None:
        super().__init__(provider_name, refresh_interval=refresh_interval)
        self.queries = queries or [{"query": "Nifty 50 India", "category": "Indian Markets"}]
        self.xml_fixture = xml_fixture
        self.max_items_per_query = max_items_per_query
        self.empty_success_is_healthy = True
        self.discovery_streams = list(dict.fromkeys(
            str(item.get("stream") or item.get("category") or "OTHER")
            for item in self.queries if isinstance(item, dict)
        ))

    def get_state(self) -> Dict[str, Any]:
        state = super().get_state()
        state["query_state"] = [dict(item) if isinstance(item, dict) else {"query": item} for item in self.queries]
        return state

    def fetch_raw_news(self) -> List[Dict[str, Any]]:
        if self.xml_fixture is not None:
            try:
                # Use the first configured query's metadata so that the
                # when:Nd bounded-discovery detection works in fixtures/tests.
                first_q = self.queries[0] if self.queries else {}
                if isinstance(first_q, dict):
                    fix_query = first_q.get("query", "")
                    fix_cat = first_q.get("category", "Other")
                    fix_stream = first_q.get("stream", "OTHER")
                else:
                    fix_query, fix_cat, fix_stream = str(first_q), "Other", "OTHER"
                items = self._parse_rss_xml(self.xml_fixture, fix_query, fix_cat, fix_stream)
                self.raw_item_count = len(items)
                self.normalized_item_count = len(items)
                self.record_success(items)
                return items
            except Exception as e:
                self.record_failure(e)
                return list(self.cached_items)

        raw_items = []
        any_failed = False
        for query_config in self.queries:
            if isinstance(query_config, dict):
                q = query_config.get("query", "")
                discovery_category = query_config.get("category", "Other")
                discovery_stream = query_config.get("stream", discovery_category)
            else:
                q = query_config
                discovery_category = "Other"
                discovery_stream = "OTHER"
            query_esc = urllib.parse.quote(q)
            url = f"https://news.google.com/rss/search?q={query_esc}&hl=en-IN&gl=IN&ceid=IN:en"

            headers = {}
            if url in self.etags:
                headers["If-None-Match"] = self.etags[url]
            if url in self.last_modified_headers:
                headers["If-Modified-Since"] = self.last_modified_headers[url]

            try:
                # Focused Google News feeds commonly exceed 100 KB. The one MiB
                # bound remains strict while allowing the RSS document to parse.
                xml_bytes, resp_hdrs, status = safe_url_fetch(
                    url, headers=headers, max_size=1024 * 1024, timeout=15.0
                )
                if status == 304:
                    continue

                if "ETag" in resp_hdrs:
                    self.etags[url] = resp_hdrs["ETag"]
                if "Last-Modified" in resp_hdrs:
                    self.last_modified_headers[url] = resp_hdrs["Last-Modified"]

                items = self._parse_rss_xml(xml_bytes, q, discovery_category, discovery_stream)
                raw_items.extend(items)
            except Exception as e:
                any_failed = True
                self.record_failure(e)

        if not any_failed or raw_items:
            selected = raw_items if raw_items else self.cached_items
            self.raw_item_count = len(raw_items)
            self.normalized_item_count = len(selected)
            self.record_success(selected)
            return raw_items if raw_items else list(self.cached_items)

        return list(self.cached_items)

    def _parse_rss_xml(
        self,
        xml_bytes: bytes,
        discovery_query: str = "",
        discovery_category: str = "Other",
        discovery_stream: str = "OTHER",
    ) -> List[Dict[str, Any]]:
        import re as _re
        root = safe_parse_xml(xml_bytes)
        items = []

        # Determine the when:Nd restriction of this query to assess staleness bound
        when_match = _re.search(r'when:(\d+)([dDhH])', discovery_query)
        when_days = None
        if when_match:
            qty = int(when_match.group(1))
            unit = when_match.group(2).lower()
            when_days = qty if unit == 'd' else qty / 24

        for el in root.findall('.//item')[: self.max_items_per_query]:
            title_el = el.find('title')
            link_el = el.find('link')
            pub_date_el = el.find('pubDate')
            description_el = el.find('description')
            source_el = el.find('source')

            title = title_el.text if title_el is not None and title_el.text else ""
            link = link_el.text if link_el is not None and link_el.text else ""
            pub_date = pub_date_el.text if pub_date_el is not None and pub_date_el.text else ""
            desc = description_el.text if description_el is not None and description_el.text else ""
            source = source_el.text if source_el is not None and source_el.text else ""

            # Extract publisher domain from the source/@url attribute (available in Google News RSS)
            publisher_domain = ""
            if source_el is not None:
                src_url_attr = source_el.get("url") or ""
                if src_url_attr:
                    try:
                        from urllib.parse import urlparse as _urlparse
                        parsed_host = _urlparse(src_url_attr).hostname or ""
                        publisher_domain = parsed_host.replace("www.", "")
                    except Exception:
                        pass

            headline = title
            source_name = source
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                headline = parts[0]
                if not source_name:
                    source_name = parts[1]

            # Google RSS links are discovery URLs. Resolving every link with a
            # separate network call makes ingestion unbounded and does not
            # reliably reveal the publisher URL, so keep original_url empty
            # unless the feed itself supplies a non-Google destination.
            original_url = "" if "news.google.com" in link else link
            canonical_url = normalize_url(original_url)

            from src.news_engine.normalizer import clean_html_text
            clean_headline = clean_html_text(headline, max_length=200)
            clean_desc = clean_html_text(desc, max_length=500)
            clean_source = clean_html_text(source_name, max_length=100)
            if not clean_headline or not clean_source or not pub_date:
                continue

            # Google News `when:Nd` bounded-window verification model:
            # When a query has a tight recency filter (when:2d or when:3d), the aggregator's
            # pubDate is bounded evidence that the article appeared within that window.
            # This isn't as strong as a verified publisher timestamp, but it is a structural
            # guarantee from the search engine — we label it GOOGLE_DISCOVERY_BOUNDED
            # so the temporal integrity engine can apply reduced-confidence current-eligibility
            # rather than treating it as completely unverified.
            if when_days is not None and when_days <= 3:
                ts_source = "GOOGLE_DISCOVERY_BOUNDED"
                ts_verified = True
            else:
                ts_source = "AGGREGATOR_DISCOVERY"
                ts_verified = False

            items.append({
                "headline": clean_headline,
                "summary_snippet": clean_desc,
                "source_name": clean_source,
                "source_type": "media",
                "original_url": canonical_url,
                "discovery_url": link,
                "discovered_via": "google_news_rss",
                "provider_id": self.provider_name,
                "discovery_query": discovery_query,
                "discovery_category": discovery_category,
                "discovery_stream": discovery_stream,
                "publisher_domain": publisher_domain,
                "language": "en",
                "published_at": pub_date,
                "discovered_at": pub_date,
                "received_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "timestamp_source": ts_source,
                "timestamp_verified": ts_verified,
                "verification_status": "unverified"
            })
        return items
