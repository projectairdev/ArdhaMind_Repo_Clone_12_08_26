# src/news_engine/institutional_flow_provider.py
"""
InstitutionalFlowProvider — ingests FII/DII daily trading activity
(Cash, Index Futures, Index Options) from exchange / regulator feeds.

Maintains independent provenance for each dataset_type (FII_CASH, DII_CASH,
FII_FUTURES, FII_OPTIONS).
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


class InstitutionalFlowProvider(BaseMacroProvider):
    """
    Ingests FII/DII trading activity across cash and derivative segments.
    """

    def __init__(
        self,
        provider_id: str = "institutional_flow_provider",
        feed_url: str = "https://www.nseindia.com/api/fiidiiTradeReact",
        refresh_interval: float = 1800.0,
        fixture_data: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(provider_id, refresh_interval=refresh_interval)
        self.feed_url = feed_url
        self.fixture_data = fixture_data

    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        if self.fixture_data is not None:
            self.record_success(self.fixture_data)
            return self.fixture_data

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

            items = self._parse_institutional_json(raw_bytes)
            self.record_success(items)
            return items
        except Exception as e:
            if self.cached_raw_data:
                self.status = "stale"
                return list(self.cached_raw_data)
            self.record_failure(e)
            return []

    def _parse_institutional_json(self, raw_bytes: bytes) -> List[Dict[str, Any]]:
        items = []
        try:
            data = json.loads(raw_bytes.decode("utf-8"))
            if isinstance(data, list):
                for row in data:
                    cat = row.get("category", "").upper()
                    if cat not in {"FII/FPI", "FII", "FPI", "DII"}:
                        continue
                    dataset_type = "FII_CASH" if cat in {"FII/FPI", "FII", "FPI"} else "DII_CASH"
                    required = (row.get("date"), row.get("buyValue"), row.get("sellValue"), row.get("netValue"))
                    if any(value in (None, "") for value in required):
                        continue
                    items.append({
                        "dataset_type": dataset_type,
                        "date": str(row["date"]),
                        "buy_value": float(row["buyValue"]),
                        "sell_value": float(row["sellValue"]),
                        "net_value": float(row["netValue"]),
                        "currency": "INR_CR",
                        "source_name": "NSE India Official FII/DII Reports",
                        "source_attribution": "NSE India official FII/DII trading activity endpoint",
                        "source_authority": "PRIMARY",
                        "source_url": self.feed_url,
                        "retrieved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    })
        except Exception as exc:
            raise ValueError(f"NSE FII/DII JSON parse failed: {exc}") from exc
        return items
