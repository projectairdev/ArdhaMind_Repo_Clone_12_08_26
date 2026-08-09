"""Optional vendor-neutral structured financial-news API providers."""
from __future__ import annotations

import json
import os
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.news_engine import safe_utils
from src.news_engine.normalizer import clean_html_text
from src.news_engine.provider import BaseNewsProvider
from src.news_engine.safe_utils import normalize_url


def safe_url_fetch(*args: Any, **kwargs: Any):
    return safe_utils.safe_url_fetch(*args, **kwargs)


class FinancialNewsProvider(BaseNewsProvider):
    """Vendor-neutral adapter contract. Disabled providers remain observable."""

    def __init__(self, provider_name: str, *, api_key: str = "", refresh_interval: float = 900.0) -> None:
        super().__init__(provider_name, refresh_interval=refresh_interval, is_enabled=bool(api_key))
        self.api_key = api_key
        self.discovery_streams = ["STRUCTURED_FINANCIAL_API"]
        if not self.is_enabled:
            self.status = "disabled"
            self.rate_limit_state = "DISABLED"
            self.operational_error_reason = "api_key_not_configured"
            self.failure_detail = "Optional structured financial-news API is disabled because no server-side API key is configured."

    def fetch_raw_news(self) -> List[Dict[str, Any]]:
        raise NotImplementedError


class MarketauxFinancialNewsProvider(FinancialNewsProvider):
    ENDPOINT = "https://api.marketaux.com/v1/news/all"

    def __init__(self, api_key: Optional[str] = None, fixture_data: Optional[Dict[str, Any]] = None) -> None:
        key = api_key if api_key is not None else os.getenv("FINANCIAL_NEWS_API_KEY", "")
        super().__init__("financial_news_marketaux", api_key=key)
        self.fixture_data = fixture_data

    def fetch_raw_news(self) -> List[Dict[str, Any]]:
        if not self.is_enabled and self.fixture_data is None:
            return []
        try:
            if self.fixture_data is not None:
                payload = self.fixture_data
            else:
                params = urllib.parse.urlencode({
                    "api_token": self.api_key,
                    "language": "en",
                    "countries": "in,us,cn,hk,jp,gb,de,fr",
                    "limit": 50,
                })
                raw, _, status = safe_url_fetch(f"{self.ENDPOINT}?{params}", headers={"Accept": "application/json"}, timeout=20.0, max_size=2 * 1024 * 1024)
                if status != 200:
                    raise ValueError(f"Marketaux returned HTTP {status}")
                payload = json.loads(raw.decode("utf-8"))
            rows = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(rows, list):
                raise ValueError("Marketaux response missing data array")
            items = []
            for row in rows:
                headline = clean_html_text(row.get("title", ""), max_length=200)
                publisher = clean_html_text(row.get("source") or row.get("domain") or "", max_length=100)
                published = str(row.get("published_at") or "")
                if not headline or not publisher or not published:
                    continue
                entities = row.get("entities") if isinstance(row.get("entities"), list) else []
                symbols = [str(entity.get("symbol") or "").upper() for entity in entities if isinstance(entity, dict) and entity.get("symbol")]
                url = normalize_url(str(row.get("url") or ""))
                items.append({
                    "headline": headline,
                    "summary_snippet": clean_html_text(row.get("description") or row.get("snippet") or "", max_length=500),
                    "source_name": publisher,
                    "source_type": "media",
                    "original_url": url,
                    "discovery_url": url,
                    "discovered_via": "structured_financial_api",
                    "provider_id": self.provider_name,
                    "discovery_query": "marketaux global financial news",
                    "discovery_category": "Structured Financial News",
                    "discovery_stream": "STRUCTURED_FINANCIAL_API",
                    "published_at": published,
                    "received_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "verification_status": "unverified",
                    "language": str(row.get("language") or "en"),
                    "related_symbols": symbols,
                })
            self.raw_item_count = len(rows)
            self.normalized_item_count = len(items)
            self.record_success(items)
            return items
        except Exception as exc:
            self.record_failure(exc)
            return list(self.cached_items)
