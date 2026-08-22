# src/news_engine/official_source_provider.py
"""
OfficialSourceProvider — ingests news from authoritative regulatory RSS feeds
(RBI press releases, RBI notifications, SEBI announcements).

Items are marked:
  source_type          = "official"
  verification_status  = "confirmed"

ETag / Last-Modified caching is used to avoid redundant fetches.
When a 304 Not Modified is returned, the provider returns its last cached
items instead of an empty list, so the pipeline always has data on hand.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.news_engine.provider import BaseNewsProvider
from src.news_engine.safe_utils import safe_url_fetch, safe_parse_xml, normalize_url


class OfficialSourceProvider(BaseNewsProvider):
    """
    Ingests news from official regulatory RSS feeds.
    """

    def __init__(
        self,
        provider_id: str,
        feed_url: str,
        refresh_interval: float = 300.0,
        xml_fixture: Optional[bytes] = None,
        market_relevant_only: bool = False,
        source_name: Optional[str] = None,
        canonical_event_category: Optional[str] = None,
        discovery_stream: Optional[str] = None,
    ) -> None:
        super().__init__(provider_id, refresh_interval=refresh_interval)
        self.feed_url = feed_url
        self.xml_fixture = xml_fixture
        self.market_relevant_only = market_relevant_only
        self.explicit_source_name = source_name
        self.explicit_event_category = canonical_event_category
        self.explicit_discovery_stream = discovery_stream
        self.discovery_streams = [discovery_stream] if discovery_stream else []

    def fetch_raw_news(self) -> List[Dict[str, Any]]:
        # --- Fixture path (for tests) ---
        if self.xml_fixture is not None:
            try:
                items = self._parse_official_xml(self.xml_fixture)
                self.raw_item_count = len(items)
                self.normalized_item_count = len(items)
                self.record_success(items)
                return items
            except Exception as e:
                self.record_failure(e)
                return list(self.cached_items)  # return last good on failure

        # --- Live HTTP path ---
        headers: Dict[str, str] = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
            "Accept": "application/rss+xml,application/xml,text/xml,*/*",
        }
        if self.feed_url in self.etags:
            headers["If-None-Match"] = self.etags[self.feed_url]
        if self.feed_url in self.last_modified_headers:
            headers["If-Modified-Since"] = self.last_modified_headers[self.feed_url]

        try:
            xml_bytes, resp_hdrs, status = safe_url_fetch(self.feed_url, headers=headers, max_size=1024 * 1024, timeout=15.0)

            if status == 304:
                # Not modified — return last good cached result unchanged
                self.status = "ready"
                return list(self.cached_items)

            # Persist conditional request headers for next fetch
            if "ETag" in resp_hdrs:
                self.etags[self.feed_url] = resp_hdrs["ETag"]
            if "Last-Modified" in resp_hdrs:
                self.last_modified_headers[self.feed_url] = resp_hdrs["Last-Modified"]

            items = self._parse_official_xml(xml_bytes)
            self.raw_item_count = len(items)
            self.normalized_item_count = len(items)
            self.record_success(items)
            return items

        except Exception as e:
            self.record_failure(e)
            return list(self.cached_items)  # return last good on failure

    def _parse_official_xml(self, xml_bytes: bytes) -> List[Dict[str, Any]]:
        root = safe_parse_xml(xml_bytes)
        items: List[Dict[str, Any]] = []

        if self.explicit_source_name:
            source_name = self.explicit_source_name
        elif "rbi" in self.provider_name.lower():
            source_name = "RBI"
        elif "sebi" in self.provider_name.lower():
            source_name = "SEBI"
        elif "pib" in self.provider_name.lower():
            source_name = "PIB"
        else:
            source_name = "Official Source"

        for el in root.findall(".//item")[:20]:
            title_el = el.find("title")
            link_el = el.find("link")
            pub_date_el = el.find("pubDate")
            description_el = el.find("description")

            title = (title_el.text or "").strip() if title_el is not None else ""
            link = (link_el.text or "").strip() if link_el is not None else ""
            pub_date = (pub_date_el.text or "").strip() if pub_date_el is not None else ""
            desc = (description_el.text or "").strip() if description_el is not None else ""

            # Normalize canonical URL (strips tracking params)
            canonical_url = normalize_url(link) if link else link

            from src.news_engine.normalizer import clean_html_text
            clean_title = clean_html_text(title, max_length=200)
            clean_desc = clean_html_text(desc, max_length=500)
            if not clean_title or not canonical_url or not pub_date:
                continue
            combined = f"{clean_title} {clean_desc}".lower()
            if self.market_relevant_only:
                market_terms = (
                    "ministry of finance", "finance ministry", "budget", "tax", "gst", "customs",
                    "inflation", "consumer price", "wholesale price", "cpi", "wpi", "gdp", "gva",
                    "industrial production", "iip", "trade deficit", "exports", "imports", "fiscal",
                    "capital market", "banking", "securities", "economy", "economic", "mospi",
                )
                if not any(term in combined for term in market_terms):
                    continue

            if self.explicit_event_category:
                canonical_category = self.explicit_event_category
            elif source_name == "RBI":
                canonical_category = "RBI"
            elif source_name == "SEBI":
                canonical_category = "SEBI"
            elif any(term in combined for term in ("inflation", "cpi", "wpi", "gdp", "gva", "industrial production", "iip", "mospi", "trade deficit")):
                canonical_category = "INDIA_MACRO"
            else:
                canonical_category = "GOVERNMENT_POLICY"

            if source_name == "RBI":
                if any(term in combined for term in ("repo", "liquidity", "auction", "laf", "reserve ratio")):
                    official_subcategory = "MONETARY_OPERATIONS"
                elif any(term in combined for term in ("penalty", "enforcement", "fraud")):
                    official_subcategory = "ENFORCEMENT"
                elif any(term in combined for term in ("bulletin", "statistics", "survey", "data")):
                    official_subcategory = "STATISTICS"
                else:
                    official_subcategory = "REGULATION_AND_SUPERVISION"
            elif source_name == "SEBI":
                if any(term in combined for term in ("order", "adjudication", "penalty")):
                    official_subcategory = "ORDERS_AND_ENFORCEMENT"
                elif any(term in combined for term in ("circular", "framework", "regulation")):
                    official_subcategory = "CIRCULARS_AND_REGULATION"
                else:
                    official_subcategory = "PRESS_RELEASES_AND_MARKET_STRUCTURE"
            elif canonical_category == "INDIA_MACRO":
                official_subcategory = "OFFICIAL_MACRO_RELEASE"
            else:
                official_subcategory = "MARKET_RELEVANT_POLICY"

            items.append({
                "headline": clean_title,
                "summary_snippet": clean_desc,
                "source_name": source_name,
                "source_type": "official",
                "original_url": canonical_url,
                "discovery_url": link,
                "discovered_via": self.provider_name,
                "provider_id": self.provider_name,
                "discovery_category": source_name,
                "discovery_stream": self.explicit_discovery_stream or canonical_category,
                "language": "en",
                "published_at": pub_date,
                "discovered_at": pub_date,
                "received_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "timestamp_source": "OFFICIAL_FEED",
                "timestamp_verified": True,
                "verification_status": "confirmed",
                "canonical_event_category": canonical_category,
                "source_authority": "PRIMARY",
                "source_reference": canonical_url,
                "official_subcategory": official_subcategory,
            })
        return items
