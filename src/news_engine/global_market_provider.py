# src/news_engine/global_market_provider.py
"""
GlobalMarketProvider — ingests global market quotes (GIFT Nifty, S&P 500, Nasdaq,
Dow Jones, Nikkei 225, Hang Seng, Brent Crude, Gold, USD/INR, DXY, US 10Y Yield).

Uses safe_url_fetch with SSRF validation, ETag support, and explicit source provenance.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.news_engine.macro_provider import BaseMacroProvider
from src.news_engine.safe_utils import safe_url_fetch, safe_parse_xml


class GlobalMarketProvider(BaseMacroProvider):
    """
    Ingests global indices, commodities, forex, and yields.
    """

    def __init__(
        self,
        provider_id: str = "global_market_provider",
        endpoints: Optional[Dict[str, str]] = None,
        refresh_interval: float = 300.0,
        fixture_data: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(provider_id, refresh_interval=refresh_interval)
        self.symbol_map = {
            "S&P 500": ("^GSPC", "S&P 500", "GLOBAL_INDEX"),
            "NASDAQ": ("^IXIC", "Nasdaq", "GLOBAL_INDEX"),
            "DOW_JONES": ("^DJI", "Dow Jones", "GLOBAL_INDEX"),
            "NIKKEI_225": ("^N225", "Nikkei 225", "GLOBAL_INDEX"),
            "HANG_SENG": ("^HSI", "Hang Seng", "GLOBAL_INDEX"),
            "BRENT_CRUDE": ("BZ=F", "Brent Crude", "COMMODITY"),
            "GOLD": ("GC=F", "Gold", "COMMODITY"),
            "USD_INR": ("USDINR=X", "USD/INR", "FOREX"),
            "DXY": ("DX-Y.NYB", "US Dollar Index", "FOREX"),
            "US_10Y": ("^TNX", "US 10Y Yield", "YIELD"),
        }
        self.fixture_data = fixture_data
        self.instrument_health: Dict[str, Dict[str, Any]] = {}

    def get_state(self) -> Dict[str, Any]:
        state = super().get_state()
        state["instrument_health"] = self.instrument_health
        return state

    def restore_state(self, state: Dict[str, Any]) -> None:
        super().restore_state(state)
        self.instrument_health = dict(state.get("instrument_health") or {})

    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        if self.fixture_data is not None:
            self.record_success(self.fixture_data)
            return self.fixture_data

        fetched_items: List[Dict[str, Any]] = []
        failed_symbols: List[str] = []
        prior_by_symbol = {str(item.get("symbol")): item for item in self.cached_raw_data}

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        for display_name, (sym, name, category) in self.symbol_map.items():
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d"
            try:
                raw_bytes, resp_hdrs, status = safe_url_fetch(url, headers=headers)
                if status != 200 or not raw_bytes:
                    raise ConnectionError(f"quote_http_or_empty_response:{sym}:{status}")
                data = json.loads(raw_bytes.decode("utf-8"))
                result_list = data.get("chart", {}).get("result", [])
                if not result_list:
                    raise ValueError(f"quote_result_missing:{sym}")
                meta = result_list[0].get("meta", {})
                returned_symbol = str(meta.get("symbol") or "")
                if returned_symbol != sym:
                    raise ValueError(f"symbol_identity_mismatch:{sym}:{returned_symbol}")
                price = float(meta.get("regularMarketPrice") or 0.0)
                previous_raw = meta.get("chartPreviousClose") or meta.get("previousClose")
                previous_close = float(previous_raw) if previous_raw is not None else 0.0
                observed_epoch = int(meta.get("regularMarketTime") or 0)
                if price <= 0 or previous_close <= 0 or observed_epoch <= 0:
                    raise ValueError(f"incomplete_quote:{sym}")
                observed = datetime.fromtimestamp(observed_epoch, timezone.utc).isoformat().replace("+00:00", "Z")
                retrieved = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                raw_change = price - previous_close
                change = round(raw_change, 6)
                change_pct = round((raw_change / previous_close) * 100.0, 4)
                fetched_items.append({
                                "symbol": display_name,
                                "name": name,
                                "category": category,
                                "price": price,
                                "change": change,
                                "change_pct": change_pct,
                                "currency": meta.get("currency", "USD"),
                                "source_name": "Yahoo Finance Public Feed",
                                "source_attribution": "Yahoo Finance chart API",
                                "source_symbol": sym,
                                "provider_symbol": returned_symbol,
                                "exchange": str(meta.get("exchangeName") or "UNKNOWN"),
                                "exchange_timezone": str(meta.get("exchangeTimezoneName") or "UTC"),
                                "instrument_type": str(meta.get("instrumentType") or "UNKNOWN"),
                                "source_session": str(meta.get("marketState") or "UNKNOWN"),
                                "observation_timestamp": observed,
                                "published_at": observed,
                                "retrieved_at": retrieved,
                                "reference_value": previous_close,
                                "reference_type": "PREVIOUS_CLOSE",
                                "reference_timestamp": "",
                                "change_source": "CALCULATED_FROM_PREVIOUS_CLOSE",
                                "observation_mode": "LAST_VALID_SOURCE_OBSERVATION",
                                "cache_restored": False,
                })
                self.instrument_health[display_name] = {
                    "status": "READY", "source_symbol": sym, "provider_symbol": returned_symbol,
                    "observation_timestamp": observed, "failure_reason": None,
                }
            except Exception as exc:
                failed_symbols.append(display_name)
                self.instrument_health[display_name] = {
                    "status": "UNAVAILABLE", "source_symbol": sym, "provider_symbol": None,
                    "observation_timestamp": None, "failure_reason": str(exc)[:200],
                }

        fresh_count = len(fetched_items)
        for display_name in failed_symbols:
            cached = prior_by_symbol.get(display_name)
            if cached:
                restored = {**cached, "cache_restored": True}
                fetched_items.append(restored)
                self.instrument_health[display_name] = {
                    **self.instrument_health[display_name], "status": "STALE_CACHE",
                    "observation_timestamp": restored.get("observation_timestamp") or restored.get("published_at"),
                }

        if fresh_count:
            self.record_success(fetched_items)
            if failed_symbols:
                self.status = "degraded"
                self.operational_error_reason = "partial_symbol_failure"
                self.failure_detail = f"Failed symbols: {', '.join(failed_symbols)}"
            return fetched_items
        elif fetched_items or self.cached_raw_data:
            self.record_failure(ConnectionError("All global market endpoints failed; preserving cached observations"))
            self.status = "stale"
            return fetched_items or [{**item, "cache_restored": True} for item in self.cached_raw_data]
        else:
            self.record_failure(ConnectionError("All global market endpoints failed or unconfigured"))
            return []

    def _parse_payload(self, key: str, payload_bytes: bytes) -> List[Dict[str, Any]]:
        items = []
        try:
            data = json.loads(payload_bytes.decode("utf-8"))
            if isinstance(data, dict) and "quoteResponse" in data:
                quotes = data["quoteResponse"].get("result", [])
                for q in quotes:
                    returned_symbol = str(q.get("symbol") or "")
                    observed_epoch = int(q.get("regularMarketTime") or 0)
                    previous_close = float(q.get("regularMarketPreviousClose") or 0.0)
                    price = float(q.get("regularMarketPrice") or 0.0)
                    if not returned_symbol or observed_epoch <= 0 or previous_close <= 0 or price <= 0:
                        continue
                    observed = datetime.fromtimestamp(observed_epoch, timezone.utc).isoformat().replace("+00:00", "Z")
                    retrieved = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                    raw_change = price - previous_close
                    items.append({
                        "symbol": q.get("symbol", ""),
                        "name": q.get("shortName") or q.get("symbol", ""),
                        "category": self._categorize_symbol(q.get("symbol", "")),
                        "price": price,
                        "change": round(raw_change, 6),
                        "change_pct": round((raw_change / previous_close) * 100.0, 4),
                        "currency": q.get("currency", "USD"),
                        "source_name": "Yahoo Finance API",
                        "source_attribution": "Yahoo Finance quote API",
                        "source_symbol": returned_symbol, "provider_symbol": returned_symbol,
                        "exchange": str(q.get("fullExchangeName") or q.get("exchange") or "UNKNOWN"),
                        "exchange_timezone": str(q.get("exchangeTimezoneName") or "UTC"),
                        "instrument_type": str(q.get("quoteType") or "UNKNOWN"),
                        "source_session": str(q.get("marketState") or "UNKNOWN"),
                        "observation_timestamp": observed, "published_at": observed, "retrieved_at": retrieved,
                        "reference_value": previous_close, "reference_type": "PREVIOUS_CLOSE",
                        "reference_timestamp": "", "change_source": "CALCULATED_FROM_PREVIOUS_CLOSE",
                        "observation_mode": "LAST_VALID_SOURCE_OBSERVATION", "cache_restored": False,
                    })
        except Exception:
            pass
        return items

    def _categorize_symbol(self, symbol: str) -> str:
        s = symbol.upper()
        if any(x in s for x in ["CL=F", "GC=F", "BRENT", "GOLD"]):
            return "COMMODITY"
        if any(x in s for x in ["INR=X", "DX-Y.NYB", "DXY", "USD"]):
            return "FOREX"
        if any(x in s for x in ["TNX", "YIELD"]):
            return "YIELD"
        return "GLOBAL_INDEX"
