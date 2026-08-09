# src/news_engine/nifty_metadata_provider.py
"""
NiftyMetadataProvider — manages versioned NIFTY 50 constituent metadata & weights.

Must have:
  - verified_source
  - metadata_version
  - effective_from date
  - retrieved_at date
  - source_attribution

If verified current weights are unavailable, exposes metadata as unavailable
(is_available=False) instead of fabricating approximate values.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.models.macro_context import NiftyConstituentMetadata, NiftyConstituentItem
from src.news_engine.macro_provider import BaseMacroProvider
from src.news_engine import safe_utils
from src.broker.utils.cache_manager import InstrumentCacheManager


OFFICIAL_CONSTITUENTS_URL = "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv"
MEMBERSHIP_SNAPSHOT_PATH = Path(".cache/nifty50_membership_snapshots.json")


def safe_url_fetch(*args: Any, **kwargs: Any):
    return safe_utils.safe_url_fetch(*args, **kwargs)


class NiftyMetadataProvider(BaseMacroProvider):
    """
    Ingests and provides verified versioned NIFTY 50 constituent metadata.
    """

    def __init__(
        self,
        provider_id: str = "nifty_metadata_provider",
        refresh_interval: float = 86400.0,
        metadata_fixture: Optional[NiftyConstituentMetadata] = None,
        feed_url: str = OFFICIAL_CONSTITUENTS_URL,
    ) -> None:
        super().__init__(provider_id, refresh_interval=refresh_interval)
        self.metadata_fixture = metadata_fixture
        self.feed_url = feed_url

    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        # Not used directly; fetch_metadata is primary
        meta = self.fetch_metadata()
        return [meta.to_dict()] if meta else []

    def fetch_metadata(self) -> NiftyConstituentMetadata:
        """
        Retrieves verified NIFTY constituent metadata.
        If fixture/live source is provided, returns validated metadata.
        Otherwise returns an explicit unavailable metadata object.
        """
        if self.metadata_fixture is not None:
            self.record_success([self.metadata_fixture.to_dict()])
            return self.metadata_fixture

        now = datetime.now(timezone.utc)
        now_str = now.isoformat().replace("+00:00", "Z")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
            "Accept": "text/csv,*/*",
            "Referer": "https://www.niftyindices.com/",
        }
        try:
            raw, _, status = safe_url_fetch(self.feed_url, headers=headers, timeout=20.0, max_size=512 * 1024)
            if status != 200:
                raise ValueError(f"official constituent download returned HTTP {status}")
            text = raw.decode("utf-8-sig")
            rows = list(csv.DictReader(io.StringIO(text)))
            if len(rows) != 50:
                raise ValueError(f"expected 50 NIFTY constituents, received {len(rows)}")
            symbols = [str(row.get("Symbol") or "").strip().upper() for row in rows]
            if not all(symbols) or len(set(symbols)) != 50:
                raise ValueError("official constituent file contains missing or duplicate symbols")

            version = f"nifty50-{now.date().isoformat()}-{hashlib.sha256(raw).hexdigest()[:12]}"
            instruments = InstrumentCacheManager.load_cache("ZERODHA") or []
            kite_eq = {
                str(item.get("tradingsymbol") or "").upper(): item
                for item in instruments
                if str(item.get("exchange") or "").upper() == "NSE"
                and str(item.get("instrument_type") or "").upper() == "EQ"
            }
            constituents: List[NiftyConstituentItem] = []
            for row, symbol in zip(rows, symbols):
                kite = kite_eq.get(symbol)
                constituents.append(NiftyConstituentItem(
                    symbol=symbol,
                    company_name=str(row.get("Company Name") or "").strip(),
                    sector=str(row.get("Industry") or "").strip(),
                    weight_pct=None,
                    isin=str(row.get("ISIN Code") or "").strip(),
                    effective_from="",
                    effective_to="",
                    metadata_version=version,
                    source=self.feed_url,
                    retrieved_at=now_str,
                    resolution_status="RESOLVED" if kite else "UNRESOLVED",
                    kite_trading_symbol=str(kite.get("tradingsymbol") or "") if kite else "",
                    kite_instrument_token=int(kite["instrument_token"]) if kite and kite.get("instrument_token") is not None else None,
                ))
            resolved = sum(item.resolution_status == "RESOLVED" for item in constituents)
            meta = NiftyConstituentMetadata(
                metadata_version=version,
                effective_from="",
                retrieved_at=now_str,
                verified_source="NSE Indices Limited",
                source_attribution="NSE Indices Limited official NIFTY 50 constituent download",
                is_available=True,
                constituents=constituents,
                weights_status="LICENSE_REQUIRED",
                weights_reason="OFFICIAL_NIFTY_WEIGHTS_LICENSE_REQUIRED",
                effective_date_status="UNAVAILABLE_SOURCE_DOES_NOT_PUBLISH_EFFECTIVE_DATES",
                source_url=self.feed_url,
                source_authority="PRIMARY",
                resolution_count=resolved,
                effective_snapshot_date=now.date().isoformat(),
            )
            self.record_success([meta.to_dict()])
            self._persist_membership_snapshot(meta)
            return meta
        except Exception as exc:
            if self.cached_raw_data:
                try:
                    cached = dict(self.cached_raw_data[0])
                    cached["constituents"] = [NiftyConstituentItem(**item) for item in cached.get("constituents", [])]
                    self.status = "stale"
                    return NiftyConstituentMetadata(**cached)
                except Exception:
                    pass
            self.record_failure(exc)
            return NiftyConstituentMetadata(
                metadata_version="UNAVAILABLE",
                effective_from="",
                retrieved_at=now_str,
                verified_source="NSE Indices Limited",
                source_attribution="NSE Indices Limited official NIFTY 50 constituent download",
                is_available=False,
                constituents=[],
                weights_status="LICENSE_REQUIRED",
                weights_reason="membership_unavailable",
                effective_date_status="UNAVAILABLE",
                source_url=self.feed_url,
            )

    @staticmethod
    def _persist_membership_snapshot(metadata: NiftyConstituentMetadata) -> None:
        """Persist bounded versioned snapshots without inventing constituent dates."""
        try:
            existing: List[Dict[str, Any]] = []
            if MEMBERSHIP_SNAPSHOT_PATH.exists():
                with MEMBERSHIP_SNAPSHOT_PATH.open("r", encoding="utf-8") as handle:
                    value = json.load(handle)
                if isinstance(value, list):
                    existing = value
            snapshot = metadata.to_dict()
            by_version = {str(item.get("metadata_version")): item for item in existing if isinstance(item, dict)}
            by_version[metadata.metadata_version] = snapshot
            bounded = sorted(by_version.values(), key=lambda item: str(item.get("retrieved_at") or ""))[-24:]
            safe_utils.atomic_write_json(str(MEMBERSHIP_SNAPSHOT_PATH), bounded)
        except Exception:
            # The live canonical record remains usable even if history persistence fails.
            return
