# src/news_engine/corporate_calendar_provider.py
"""
CorporateCalendarProvider — ingests corporate calendars:
  - Economic Calendar Events
  - Corporate Actions (Dividends, Splits, Bonuses)
  - Earnings Announcements
  - IPO Schedules
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.news_engine.macro_provider import BaseMacroProvider
from src.news_engine import safe_utils


def safe_url_fetch(*args: Any, **kwargs: Any):
    """Patchable proxy retaining centralized URL validation."""
    return safe_utils.safe_url_fetch(*args, **kwargs)


class CorporateCalendarProvider(BaseMacroProvider):
    """
    Ingests corporate and economic calendar records.
    """

    def __init__(
        self,
        provider_id: str = "corporate_calendar_provider",
        feed_url: str = "https://www.nseindia.com/api/corporates-corporateActions?index=equities",
        refresh_interval: float = 3600.0,
        fixture_data: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> None:
        super().__init__(provider_id, refresh_interval=refresh_interval)
        self.feed_url = feed_url
        self.fixture_data = fixture_data

    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        if self.fixture_data is not None:
            # Flatten fixture dictionary into raw items
            flattened = []
            for category, items in self.fixture_data.items():
                for item in items:
                    item_copy = dict(item)
                    item_copy["calendar_category"] = category
                    flattened.append(item_copy)
            self.record_success(flattened)
            return flattened

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
            "Accept": "application/json,text/plain,*/*",
            "Referer": "https://www.nseindia.com/",
        }
        if self.feed_url in self.etags:
            headers["If-None-Match"] = self.etags[self.feed_url]

        try:
            raw_bytes, resp_hdrs, status = safe_url_fetch(self.feed_url, headers=headers, timeout=20.0, max_size=1024 * 1024)
            if status == 304:
                return list(self.cached_raw_data)

            if "ETag" in resp_hdrs:
                self.etags[self.feed_url] = resp_hdrs["ETag"]

            items = self._parse_calendar_json(raw_bytes)
            self.record_success(items)
            return items
        except Exception as e:
            if self.cached_raw_data:
                self.status = "stale"
                return list(self.cached_raw_data)
            self.record_failure(e)
            return []

    def _parse_calendar_json(self, raw_bytes: bytes) -> List[Dict[str, Any]]:
        items = []
        try:
            data = json.loads(raw_bytes.decode("utf-8"))
            if isinstance(data, list):
                for row in data:
                    symbol = str(row.get("symbol") or "").strip().upper()
                    subject = str(row.get("subject") or "").strip()
                    ex_date = str(row.get("exDate") or "").strip()
                    if not symbol or not subject or not ex_date:
                        continue
                    items.append({
                        "calendar_category": "CORPORATE_ACTION",
                        "event_category": "CORPORATE_ACTION",
                        "symbol": symbol,
                        "company_name": str(row.get("comp") or symbol).strip(),
                        "isin": str(row.get("isin") or "").strip(),
                        "action_type": subject,
                        "ex_date": ex_date,
                        "record_date": row.get("recordDate") or row.get("recDate", ""),
                        "details": subject,
                        "source_name": "NSE Corporate Actions Feed",
                        "source_attribution": "NSE Official Corporate Filings",
                        "source_authority": "PRIMARY",
                        "source_url": self.feed_url,
                        "verification_status": "CONFIRMED",
                        "relevance_score": 8.0,
                        "impact_level": "HIGH",
                        "confidence": 1.0,
                        "retrieved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    })
        except Exception as exc:
            raise ValueError(f"NSE corporate-actions JSON parse failed: {exc}") from exc
        return items
