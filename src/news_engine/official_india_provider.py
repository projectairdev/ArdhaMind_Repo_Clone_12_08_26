"""Primary-source NSE corporate intelligence providers for E1."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.news_engine import safe_utils
from src.news_engine.macro_provider import BaseMacroProvider


def safe_url_fetch(*args: Any, **kwargs: Any):
    return safe_utils.safe_url_fetch(*args, **kwargs)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(*parts: Any) -> str:
    raw = "|".join(str(part or "").strip().lower() for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _relevance(text: str) -> float:
    lowered = text.lower()
    high = ("financial result", "dividend", "bonus", "split", "buyback", "merger", "acquisition", "fund raising", "board meeting")
    medium = ("order", "contract", "agreement", "credit rating", "management change", "investor presentation")
    if any(term in lowered for term in high):
        return 8.0
    if any(term in lowered for term in medium):
        return 6.0
    return 4.0


def _impact(text: str) -> str:
    score = _relevance(text)
    return "HIGH" if score >= 8 else "MEDIUM" if score >= 6 else "LOW"


class NseOfficialDatasetProvider(BaseMacroProvider):
    """Base provider with conditional requests, validation and last-valid cache."""

    def __init__(self, provider_id: str, feed_url: str, dataset: str, *,
                 refresh_interval: float = 1800.0,
                 fixture_data: Optional[List[Dict[str, Any]]] = None,
                 max_size: int = 1024 * 1024) -> None:
        super().__init__(provider_id, refresh_interval=refresh_interval)
        self.feed_url = feed_url
        self.dataset = dataset
        self.fixture_data = fixture_data
        self.max_size = max_size

    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        if self.fixture_data is not None:
            parsed = self.parse_rows(self.fixture_data)
            self.record_success(parsed)
            return parsed
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
            "Accept": "application/json,text/plain,*/*",
            "Referer": "https://www.nseindia.com/",
        }
        if self.feed_url in self.etags:
            headers["If-None-Match"] = self.etags[self.feed_url]
        if self.feed_url in self.last_modified_headers:
            headers["If-Modified-Since"] = self.last_modified_headers[self.feed_url]
        try:
            raw, response_headers, status = safe_url_fetch(
                self.feed_url, headers=headers, timeout=25.0, max_size=self.max_size
            )
            if status == 304:
                self.status = "ready"
                return list(self.cached_raw_data)
            if status != 200:
                raise ValueError(f"{self.dataset} returned HTTP {status}")
            if "ETag" in response_headers:
                self.etags[self.feed_url] = response_headers["ETag"]
            if "Last-Modified" in response_headers:
                self.last_modified_headers[self.feed_url] = response_headers["Last-Modified"]
            decoded = json.loads(raw.decode("utf-8"))
            if not isinstance(decoded, list):
                raise ValueError(f"{self.dataset} response is not a JSON list")
            items = self.parse_rows(decoded)
            self.record_success(items)
            return items
        except Exception as exc:
            if self.cached_raw_data:
                self.record_failure(exc)
                self.status = "stale"
                return list(self.cached_raw_data)
            self.record_failure(exc)
            return []

    def parse_rows(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def _base(self, category: str, headline: str, *, symbol: str = "", company: str = "",
              isin: str = "", published_at: str = "", effective_date: str = "",
              description: str = "", source_reference: str = "", source_url: str = "") -> Dict[str, Any]:
        combined = f"{headline} {description}"
        return {
            "id": _stable_id(self.dataset, symbol, published_at, effective_date, headline, source_reference),
            "event_category": category,
            "headline": headline,
            "description": description,
            "symbol": symbol,
            "company_name": company,
            "isin": isin,
            "published_at": published_at,
            "effective_date": effective_date,
            "source_name": f"NSE India Official {self.dataset}",
            "source_url": source_url or self.feed_url,
            "source_reference": source_reference,
            "source_authority": "PRIMARY",
            "verification_status": "CONFIRMED",
            "relevance_score": _relevance(combined),
            "impact_level": _impact(combined),
            "confidence": 1.0,
            "retrieved_at": _now(),
            "freshness_status": "fresh",
            "calendar_category": category,
        }


class NseCorporateAnnouncementsProvider(NseOfficialDatasetProvider):
    def __init__(self, fixture_data: Optional[List[Dict[str, Any]]] = None) -> None:
        super().__init__("nse_corporate_announcements", "https://www.nseindia.com/api/corporate-announcements?index=equities", "Corporate Announcements", fixture_data=fixture_data)

    def parse_rows(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        items = []
        for row in rows:
            symbol = str(row.get("symbol") or "").strip().upper()
            headline = str(row.get("attchmntText") or row.get("desc") or "").strip()
            published = str(row.get("an_dt") or row.get("exchdisstime") or row.get("sort_date") or "").strip()
            if not symbol or not headline or not published:
                continue
            items.append(self._base(
                "CORPORATE_ANNOUNCEMENT", headline, symbol=symbol,
                company=str(row.get("sm_name") or symbol).strip(), isin=str(row.get("sm_isin") or "").strip(),
                published_at=published, description=str(row.get("desc") or "").strip(),
                source_reference=str(row.get("seq_id") or "").strip(),
                source_url=str(row.get("attchmntFile") or self.feed_url).strip(),
            ))
        return items


class NseBoardMeetingsProvider(NseOfficialDatasetProvider):
    def __init__(self, fixture_data: Optional[List[Dict[str, Any]]] = None) -> None:
        super().__init__("nse_board_meetings", "https://www.nseindia.com/api/corporate-board-meetings?index=equities", "Board Meetings", fixture_data=fixture_data)

    def parse_rows(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        items = []
        for row in rows:
            symbol = str(row.get("bm_symbol") or "").strip().upper()
            meeting_date = str(row.get("bm_date") or row.get("proposedMeetingDate") or "").strip()
            purpose = str(row.get("bm_purpose") or row.get("bm_desc") or "").strip()
            if not symbol or not meeting_date or not purpose:
                continue
            items.append(self._base(
                "BOARD_MEETING", f"{symbol} board meeting: {purpose}", symbol=symbol,
                company=str(row.get("sm_name") or symbol).strip(), isin=str(row.get("sm_isin") or "").strip(),
                published_at=str(row.get("bm_timestamp") or row.get("sysTime") or "").strip(),
                effective_date=meeting_date, description=str(row.get("bm_desc") or purpose).strip(),
                source_url=str(row.get("attachment") or self.feed_url).strip(),
            ))
        return items


class NseFinancialResultsProvider(NseOfficialDatasetProvider):
    def __init__(self, fixture_data: Optional[List[Dict[str, Any]]] = None) -> None:
        super().__init__("nse_financial_results", "https://www.nseindia.com/api/corporates-financial-results?index=equities&period=Quarterly", "Financial Results", fixture_data=fixture_data, max_size=8 * 1024 * 1024, refresh_interval=3600.0)

    def parse_rows(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        items = []
        for row in rows:
            symbol = str(row.get("symbol") or "").strip().upper()
            published = str(row.get("filingDate") or row.get("exchdisstime") or row.get("broadCastDate") or "").strip()
            period = str(row.get("relatingTo") or row.get("period") or "").strip()
            if not symbol or not published or not period:
                continue
            description = " · ".join(filter(None, [period, str(row.get("audited") or "").strip(), str(row.get("consolidated") or "").strip()]))
            items.append(self._base(
                "EARNINGS", f"{symbol} filed {period} financial results", symbol=symbol,
                company=str(row.get("companyName") or symbol).strip(), isin=str(row.get("isin") or "").strip(),
                published_at=published, effective_date=str(row.get("toDate") or "").strip(),
                description=description, source_reference=str(row.get("seqNumber") or "").strip(),
                source_url=str(row.get("resultDetailedDataLink") or row.get("xbrl") or self.feed_url).strip(),
            ))
        return items
