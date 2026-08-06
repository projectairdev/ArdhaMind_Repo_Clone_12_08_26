from __future__ import annotations

from typing import Any, Dict, List, Tuple
from datetime import datetime

class NewsNormalizer:
    """
    Stateless normalization layer converting raw provider structures into a unified internal representation.
    """

    @staticmethod
    def normalize_google_article(raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts raw fields from GoogleNewsProvider or RSS format into normalized article dictionary.
        """
        # Map fields intelligently, using fallback defaults
        article_id = raw.get("id") or raw.get("link") or raw.get("title", "")
        # Create a hash-like ID for stability if link or title
        if not str(article_id).startswith("raw_"):
            article_id = f"art_{hash(article_id) & 0xffffffff:x}"

        title = raw.get("title") or raw.get("headline") or "Untitled Article"
        content = raw.get("content") or raw.get("description") or title
        source = raw.get("source") or "Unknown Source"
        published_at = raw.get("pubDate") or raw.get("published_at") or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        if published_at:
            try:
                from email.utils import parsedate_to_datetime
                published_at = parsedate_to_datetime(published_at).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass
        url = raw.get("link") or raw.get("url") or ""

        return {
            "article_id": article_id,
            "title": title.strip(),
            "content": content.strip(),
            "source": source.strip(),
            "published_at": published_at,
            "url": url.strip(),
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
        scheduled_time = raw.get("target_date") or raw.get("scheduled_time") or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
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
