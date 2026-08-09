from __future__ import annotations

from typing import Any, Dict, List, Tuple
import re
import html

def clean_html_text(text: str, max_length: int = 500) -> str:
    if not text or not isinstance(text, str):
        return ""
    decoded = html.unescape(text)
    decoded = re.sub(r"<(script|style)\b[^>]*>.*?</\1\s*>", " ", decoded, flags=re.IGNORECASE | re.DOTALL)
    stripped = re.sub(r"<[^>]+>", " ", decoded)
    collapsed = re.sub(r"\s+", " ", stripped).strip()
    if len(collapsed) > max_length:
        return collapsed[:max_length].rstrip() + "..."
    return collapsed

class NewsNormalizer:
    """
    Stateless normalization layer converting raw provider structures into a unified internal representation.
    """

    @staticmethod
    def normalize_google_article(raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts raw fields from GoogleNewsProvider, RBI, or RSS formats into clean article dictionary.
        """
        article_id = raw.get("id") or raw.get("link") or raw.get("title", "")
        if not str(article_id).startswith("raw_"):
            article_id = f"art_{hash(article_id) & 0xffffffff:x}"

        raw_title = raw.get("title") or raw.get("headline") or ""
        raw_content = raw.get("content") or raw.get("description") or raw_title
        clean_title_str = clean_html_text(raw_title, max_length=200)
        clean_content_str = clean_html_text(raw_content, max_length=500)

        source = clean_html_text(raw.get("source") or raw.get("source_name") or "", max_length=100)
        published_at = raw.get("pubDate") or raw.get("published_at") or ""
        if published_at:
            try:
                from email.utils import parsedate_to_datetime
                published_at = parsedate_to_datetime(published_at).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass
        url = raw.get("link") or raw.get("url") or ""

        return {
            "article_id": article_id,
            "title": clean_title_str,
            "headline": clean_title_str,
            "content": clean_content_str,
            "summary_snippet": clean_content_str,
            "source": source,
            "source_name": source,
            "source_type": "media",
            "published_at": published_at,
            "url": url.strip(),
            "original_url": url.strip(),
            "discovery_url": url.strip(),
            "discovered_via": raw.get("discovered_via", "news_rss"),
            "verification_status": "unverified"
        }

    @staticmethod
    def normalize_macro_event(raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts raw scheduled calendar events into normalized event dictionary.
        """
        event_id = raw.get("event_id") or raw.get("id")
        if not event_id:
            event_id = f"ev_{hash(raw.get('event_title', '')) & 0xffffffff:x}"

        title = raw.get("event_title") or raw.get("title") or "Macroeconomic Event"
        description = raw.get("event_description") or raw.get("description") or title
        event_type = raw.get("category") or raw.get("event_type") or "Macro Economy"
        importance = raw.get("importance") or "MEDIUM"
        scheduled_time = raw.get("target_date") or raw.get("scheduled_time") or ""
        source = raw.get("source_ref") or raw.get("source") or "Unknown"

        return {
            "event_id": event_id,
            "title": title.strip(),
            "description": description.strip(),
            "event_type": event_type.strip(),
            "importance": importance.strip(),
            "scheduled_time": scheduled_time,
            "sources": [source],
        }
