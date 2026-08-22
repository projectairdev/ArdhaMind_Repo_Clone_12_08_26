# src/news_engine/deduplicator.py
"""
NewsDeduplicator — stable identity and fuzzy deduplication.

Canonical ID strategy (Item 6):
  ID = MD5(normalized_source + normalized_url + normalized_headline + published_at)

  - normalized_url: scheme/host lowercased, tracking params stripped
    (uses safe_utils.normalize_url so IDs are stable even when ?utm_* etc change)
  - normalized_headline: lowercased, punctuation stripped
  - published_at: ISO-8601 UTC string; empty string when unavailable

Supports compatibility field aliases (headline/title, source_name/source, original_url/url).
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List

from src.news_engine.safe_utils import normalize_url


class NewsDeduplicator:
    """
    Stateless deduplication layer.
    Computes stable canonical item IDs and stable duplicate group IDs.
    Filters duplicates using Jaccard word-overlap similarity (IoU ≥ 0.70).
    """

    @staticmethod
    def _normalize_headline(text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", "", text)
        return " ".join(text.split())

    @staticmethod
    def compute_stable_id(
        headline: str,
        url: str,
        source_name: str = "",
        published_at: str = "",
    ) -> str:
        """
        Generates a deterministic stable ID.
        - For aggregator articles (Google News redirect URLs or missing direct URLs):
          ID is based strictly on normalized publisher + normalized headline.
        - For direct publisher URLs (RBI, SEBI, PIB, direct article URLs):
          ID is based on normalized publisher + normalized canonical URL.
        Crawl/discovery timestamps are explicitly excluded so recrawls map to the same canonical ID.
        """
        norm_headline = NewsDeduplicator._normalize_headline(headline)
        norm_source = source_name.strip().lower()
        norm_url = normalize_url(url.strip()) if url.strip() else ""

        # If URL is a Google News redirect or empty, compute stable ID strictly from publisher + headline
        if not norm_url or "news.google.com" in norm_url:
            combined = f"agg:{norm_source}:{norm_headline}"
        else:
            combined = f"pub:{norm_source}:{norm_url}"

        return hashlib.md5(combined.encode("utf-8")).hexdigest()

    @staticmethod
    def _similarity_ratio(str1: str, str2: str) -> float:
        """Jaccard similarity (Intersection over Union) of word sets."""
        words1 = set(str1.split())
        words2 = set(str2.split())
        if not words1 or not words2:
            return 0.0
        return len(words1 & words2) / len(words1 | words2)

    @staticmethod
    def _published_epoch(value: str) -> float | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            try:
                parsed = parsedate_to_datetime(value)
            except (TypeError, ValueError):
                return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()

    @classmethod
    def deduplicate(
        cls, raw_items: List[Dict[str, Any]], threshold: float = 0.70
    ) -> List[Dict[str, Any]]:
        """
        1. Computes canonical stable IDs for every item.
        2. Deduplicates by:
           a. Normalized resolved URL match, OR
           b. Headline Jaccard similarity >= threshold
        3. Groups duplicates under the earliest story's ID as duplicate_group_id.
        4. Merges source names into the canonical anchor item.
        5. Returns only the anchor (earliest) item from each duplicate group.
        """
        if not raw_items:
            return []

        # Sort chronologically so the earliest article becomes the group anchor
        items = sorted(
            raw_items,
            key=lambda x: x.get("published_at", "") or x.get("pubDate", "") or "",
        )

        processed_items: List[Dict[str, Any]] = []

        for item in items:
            headline = item.get("headline") or item.get("title") or ""
            source_name = item.get("source_name") or item.get("source") or ""
            published_at = item.get("published_at") or item.get("pubDate") or ""
            url = item.get("original_url") or item.get("discovery_url") or item.get("url") or ""

            stable_id = cls.compute_stable_id(headline, url, source_name, published_at)
            item["id"] = stable_id
            if "article_id" in item or "title" in item:
                item["article_id"] = stable_id

            norm_headline = cls._normalize_headline(headline)
            norm_url = normalize_url(url) if url else ""
            found_duplicate = False

            for processed in processed_items:
                proc_url = processed.get("original_url") or processed.get("discovery_url") or processed.get("url") or ""
                proc_norm_url = normalize_url(proc_url) if proc_url else ""
                proc_headline = processed.get("headline") or processed.get("title") or ""
                proc_norm_headline = cls._normalize_headline(proc_headline)

                url_match = bool(norm_url and norm_url == proc_norm_url)
                sim = cls._similarity_ratio(norm_headline, proc_norm_headline)
                item_epoch = cls._published_epoch(published_at)
                proc_epoch = cls._published_epoch(processed.get("published_at") or processed.get("pubDate") or "")
                within_window = item_epoch is None or proc_epoch is None or abs(item_epoch - proc_epoch) <= 48 * 3600

                if url_match or (sim >= threshold and within_window):
                    found_duplicate = True
                    group_id = processed.get("duplicate_group_id") or processed.get("id") or processed.get("article_id")
                    processed["duplicate_group_id"] = group_id
                    item["duplicate_group_id"] = group_id

                    # Preserve the anchor publisher while retaining all source
                    # provenance. A comma-joined publisher is not a publisher.
                    proc_src = processed.get("source_name") or processed.get("source") or "Unknown"
                    item_src = item.get("source_name") or item.get("source") or "Unknown"
                    sources = processed.setdefault("sources", [proc_src])
                    if item_src not in sources:
                        sources.append(item_src)
                    processed["source"] = ", ".join(sources)  # legacy compatibility only
                    provenance = processed.setdefault("provenance", [{
                        "publisher": proc_src,
                        "url": processed.get("original_url") or processed.get("discovery_url") or "",
                        "published_at": processed.get("published_at") or processed.get("pubDate") or "",
                        "provider_id": processed.get("provider_id") or processed.get("discovered_via") or "",
                    }])
                    provenance.append({
                        "publisher": item_src,
                        "url": item.get("original_url") or item.get("discovery_url") or "",
                        "published_at": item.get("published_at") or item.get("pubDate") or "",
                        "provider_id": item.get("provider_id") or item.get("discovered_via") or "",
                    })
                    processed["duplicate_count"] = int(processed.get("duplicate_count") or 0) + 1

                    if (
                        item.get("verification_status") == "confirmed"
                        and processed.get("verification_status") != "confirmed"
                    ):
                        processed["original_url"] = item.get("original_url") or processed.get("original_url")

                    warnings = processed.setdefault("warnings", [])
                    msg = f"Duplicate grouped from {item_src}"
                    if msg not in warnings:
                        warnings.append(msg)
                    break

            if not found_duplicate:
                item["duplicate_group_id"] = None
                processed_items.append(item)

        return processed_items
