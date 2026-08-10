from __future__ import annotations

"""Deterministic Kite-only constituent breadth and NSE sector-index telemetry."""

import json
import os
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from src.broker.services.instrument_service import InstrumentService


SECTOR_INDEX_NAMES = (
    "NIFTY BANK",
    "NIFTY IT",
    "NIFTY AUTO",
    "NIFTY PHARMA",
    "NIFTY METAL",
    "NIFTY FMCG",
    "NIFTY REALTY",
    "NIFTY ENERGY",
    "NIFTY OIL AND GAS",
    "NIFTY FIN SERVICE",
)


def _number(value: Any) -> Optional[float]:
    try:
        result = float(value)
        return result if result == result else None
    except (TypeError, ValueError):
        return None


def _timestamp(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    text = str(value).strip()
    return text or None


class KiteIntelligenceService:
    """Kite-derived intelligence with explicit availability and coverage contracts."""

    CONSTITUENT_MAP_VERSION = "kite-universe-v1"
    BREADTH_MINIMUM_COVERAGE = 40
    INDIA_VIX_CACHE_PATH = Path(".cache/kite_india_vix_snapshot.json")
    INDIA_VIX_REGIME_VERSION = "INDIA_VIX_REGIME_V1"
    _india_vix_memory: Dict[str, Any] = {}
    _india_vix_last_fetch = 0.0

    @classmethod
    def resolve_constituents(
        cls,
        instruments: Iterable[Dict[str, Any]],
        symbols: Optional[Iterable[Any]] = None,
    ) -> Dict[str, Any]:
        """Resolve a supplied *verified* membership list; Kite itself has no membership relation."""
        verified_members = []
        for value in symbols or []:
            member = value if isinstance(value, dict) else {"symbol": value}
            symbol = str(member.get("symbol") or "").strip().upper().removeprefix("NSE:")
            if symbol:
                verified_members.append({**member, "symbol": symbol})
        candidates: Dict[str, List[Dict[str, Any]]] = {}
        for item in instruments:
            symbol = str(item.get("tradingsymbol") or "").strip().upper()
            if (str(item.get("exchange") or "").upper() == "NSE" and symbol
                    and str(item.get("instrument_type") or "EQ").upper() == "EQ"):
                candidates.setdefault(symbol, []).append(item)
        resolved: List[Dict[str, Any]] = []
        claimed_tokens: set[int] = set()
        for member in verified_members:
            symbol = member["symbol"]
            matches = candidates.get(symbol, [])
            item = matches[0] if len(matches) == 1 else None
            reason = "NO_EXACT_NSE_EQ_SYMBOL_MATCH" if not matches else "DUPLICATE_NSE_EQ_SYMBOL_MATCH"
            token = item.get("instrument_token") if item else None
            if item and (token is None or int(token) in claimed_tokens):
                reason = "MISSING_OR_DUPLICATE_INSTRUMENT_TOKEN"
                item = None
            if item:
                claimed_tokens.add(int(token))
            resolved.append({
                "symbol": symbol,
                "trading_symbol": item.get("tradingsymbol") if item else None,
                "exchange": item.get("exchange") if item else "NSE",
                "instrument_token": item.get("instrument_token") if item else None,
                "company_name": member.get("company_name") or (item.get("name") if item else None),
                "isin": member.get("isin"),
                "resolution_status": "RESOLVED" if item else "UNRESOLVED",
                "resolution_reason": "EXACT_NSE_EQ_TRADINGSYMBOL" if item else reason,
            })
        return {
            "version": cls.CONSTITUENT_MAP_VERSION,
            "members": resolved,
            "resolved_count": sum(row["resolution_status"] == "RESOLVED" for row in resolved),
            "expected_count": 50,
            "membership_count": len(verified_members),
            "membership_source": "NSE_INDICES_VERIFIED_CANONICAL" if verified_members else "UNAVAILABLE",
            "reason": None if verified_members else "kite_instrument_dump_does_not_include_index_membership",
        }

    @classmethod
    def compute_breadth(
        cls,
        resolved_map: Dict[str, Any],
        quotes: Dict[str, Dict[str, Any]],
        minimum_coverage: Optional[int] = None,
        market_closed: bool = False,
        now: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        minimum = minimum_coverage or cls.BREADTH_MINIMUM_COVERAGE
        observations: List[Dict[str, Any]] = []
        for member in resolved_map.get("members", []):
            if member.get("resolution_status") != "RESOLVED":
                continue
            symbol = member.get("trading_symbol")
            quote = quotes.get(f"NSE:{symbol}") or quotes.get(symbol) or {}
            ltp = _number(quote.get("last_price"))
            previous = _number((quote.get("ohlc") or {}).get("close"))
            observed_at = _timestamp(quote.get("timestamp") or quote.get("last_trade_time"))
            freshness = cls._quote_freshness(observed_at, market_closed, now)
            if ltp is None or previous is None or previous <= 0 or freshness in {"UNAVAILABLE", "STALE"}:
                continue
            delta = ltp - previous
            observations.append({
                "symbol": member.get("symbol") or member.get("trading_symbol"),
                "last_price": ltp,
                "previous_close": previous,
                "change": delta,
                "change_pct": delta / previous * 100.0,
                "observation_timestamp": observed_at,
                "source": "Kite Quote API",
                "freshness": freshness,
            })
        valid = len(observations)
        base = {
            "status": "READY" if valid >= minimum else ("PARTIAL" if valid else "UNAVAILABLE"),
            "coverage": {"valid": valid, "expected": 50, "minimum": minimum},
            "source": "Kite Quote API",
            "quality": "VALIDATED" if valid >= minimum else "INSUFFICIENT_COVERAGE",
            "freshness": "LAST_VALID_SESSION" if market_closed and valid else ("FRESH" if valid else "UNAVAILABLE"),
            "observation_mode": "LAST_VALID_SESSION" if market_closed and valid else ("LIVE" if valid else "UNAVAILABLE"),
            "observations": observations,
        }
        if valid < minimum:
            return {**base, "advances": None, "declines": None, "unchanged": None,
                    "advance_decline_ratio": None, "percent_above_previous_close": None,
                    "percent_below_previous_close": None, "top_gainers": [], "top_losers": []}
        advances = [row for row in observations if row["change"] > 0]
        declines = [row for row in observations if row["change"] < 0]
        unchanged = valid - len(advances) - len(declines)
        timestamp = next((_timestamp((q or {}).get("timestamp")) for q in quotes.values() if (q or {}).get("timestamp")), None)
        return {
            **base,
            "advances": len(advances),
            "declines": len(declines),
            "unchanged": unchanged,
            "advance_decline_ratio": len(advances) / len(declines) if declines else None,
            "percent_above_previous_close": len(advances) / valid * 100.0,
            "percent_below_previous_close": len(declines) / valid * 100.0,
            "top_gainers": sorted(advances, key=lambda row: row["change_pct"], reverse=True)[:5],
            "top_losers": sorted(declines, key=lambda row: row["change_pct"])[:5],
            "timestamp": timestamp,
        }

    @staticmethod
    def _quote_freshness(value: Optional[str], market_closed: bool, now: Optional[datetime] = None) -> str:
        if not value:
            return "UNAVAILABLE"
        if market_closed:
            return "LAST_VALID_SESSION"
        try:
            observed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if observed.tzinfo is None:
                # Naive timestamps from Zerodha Kite API are in IST (Asia/Kolkata, UTC+5:30)
                ist = timezone(timedelta(hours=5, minutes=30))
                observed = observed.replace(tzinfo=ist)
            current = now or datetime.now(timezone.utc)
            if current.tzinfo is None:
                current = current.replace(tzinfo=timezone.utc)
            age = current - observed.astimezone(timezone.utc)
            return "FRESH" if timedelta(seconds=-300) <= age <= timedelta(minutes=15) else "STALE"
        except (TypeError, ValueError):
            return "UNAVAILABLE"

    @staticmethod
    def resolve_sector_indices(instrument_service: InstrumentService) -> List[Dict[str, Any]]:
        resolved = []
        for name in SECTOR_INDEX_NAMES:
            item = instrument_service.lookup_index_instrument(name)
            if item and item.get("instrument_token"):
                resolved.append({
                    "name": name,
                    "trading_symbol": item.get("tradingsymbol") or name,
                    "exchange": item.get("exchange") or "NSE",
                    "instrument_token": int(item["instrument_token"]),
                })
        return resolved

    @classmethod
    def build_sector_snapshot(cls, broker_service: Any, market_closed: bool = False) -> Dict[str, Any]:
        instrument_service = InstrumentService.get_instance()
        instrument_service.load_instruments(broker_service)
        instruments = cls.resolve_sector_indices(instrument_service)
        keys = [f"{row['exchange']}:{row['trading_symbol']}" for row in instruments]
        try:
            quotes = broker_service.get_quote(keys) if keys else {}
        except Exception:
            quotes = {}
        rows = []
        for instrument, key in zip(instruments, keys):
            quote = quotes.get(key) or {}
            ltp = _number(quote.get("last_price"))
            previous = _number((quote.get("ohlc") or {}).get("close"))
            if ltp is None or previous is None or previous <= 0:
                continue
            change = ltp - previous
            rows.append({
                **instrument,
                "ltp": ltp,
                "change": change,
                "change_pct": change / previous * 100.0,
                "timestamp": _timestamp(quote.get("timestamp") or quote.get("last_trade_time")),
                "source": "Kite Quote API",
                "observation_mode": "LAST_SESSION" if market_closed else "LIVE",
                "freshness": "MARKET_CLOSED" if market_closed else "FRESH",
            })
        return {
            "resolved_count": len(instruments),
            "quote_count": len(rows),
            "sectors": rows,
            "source": "Kite Quote API",
            "timestamp": next((row["timestamp"] for row in rows if row.get("timestamp")), None),
            "observation_mode": "LAST_SESSION" if market_closed else "LIVE",
            "freshness": "MARKET_CLOSED" if market_closed else "FRESH",
        }

    @classmethod
    def build_market_extensions(
        cls, broker_service: Any, market_closed: bool = False,
        constituent_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        instrument_service = InstrumentService.get_instance()
        instrument_service.load_instruments(broker_service)
        metadata = constituent_metadata or {}
        members = (metadata.get("constituents") or []) if metadata.get("is_available") else []
        if not members:
            # Fallback to cached NIFTY 50 membership snapshot when constituent_metadata is missing
            snapshot_path = Path(".cache/nifty50_membership_snapshots.json")
            if snapshot_path.exists():
                try:
                    snapshots = json.loads(snapshot_path.read_text(encoding="utf-8"))
                    if snapshots and isinstance(snapshots, list):
                        members = snapshots[-1].get("constituents") or []
                except Exception:
                    pass
        universe = cls.resolve_constituents(instrument_service._instruments, members)
        keys = [f"NSE:{row['trading_symbol']}" for row in universe["members"] if row["resolution_status"] == "RESOLVED"]
        try:
            quotes = broker_service.get_quote(keys) if keys else {}
        except Exception:
            quotes = {}
        breadth = cls.compute_breadth(universe, quotes, market_closed=market_closed)
        sectors = cls.build_sector_snapshot(broker_service, market_closed)
        return {"constituent_instruments": universe, "breadth": breadth, **sectors}

    @staticmethod
    def _load_json(path: Path) -> Dict[str, Any]:
        try:
            with path.open("r", encoding="utf-8") as handle:
                value = json.load(handle)
            return value if isinstance(value, dict) else {}
        except (OSError, ValueError):
            return {}

    @staticmethod
    def _persist_json(path: Path, payload: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=str(path.parent))
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, default=str)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    @classmethod
    def build_india_vix_snapshot(
        cls,
        broker_service: Any,
        market_closed: bool,
        cache_path: Optional[Path] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Resolve and observe the genuine NSE India VIX instrument through Kite."""
        path = cache_path or cls.INDIA_VIX_CACHE_PATH
        if not force_refresh and cache_path is None and cls._india_vix_memory and time.time() - cls._india_vix_last_fetch < 60.0:
            return dict(cls._india_vix_memory)
        attempted_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        persisted = cls._load_json(path)
        try:
            service = InstrumentService.get_instance()
            service.load_instruments(broker_service)
            instrument = service.lookup_index_instrument("INDIA VIX")
            if not instrument:
                raise ValueError("INDIA_VIX_INSTRUMENT_NOT_RESOLVED")
            if str(instrument.get("tradingsymbol") or "").upper() != "INDIA VIX" or str(instrument.get("exchange") or "").upper() != "NSE":
                raise ValueError("INDIA_VIX_SYMBOL_IDENTITY_MISMATCH")
            token = int(instrument["instrument_token"])
            source_symbol = "NSE:INDIA VIX"
            quotes = broker_service.get_quote([source_symbol]) or {}
            quote = quotes.get(source_symbol) or {}
            value = _number(quote.get("last_price"))
            previous = _number((quote.get("ohlc") or {}).get("close"))
            observed = _timestamp(quote.get("timestamp") or quote.get("last_trade_time"))
            if value is None or value <= 0 or not observed:
                raise ValueError("INDIA_VIX_QUOTE_MISSING_VALUE_OR_TIMESTAMP")
            change = value - previous if previous is not None and previous > 0 else None
            change_pct = change / previous * 100.0 if change is not None and previous else None
            history: List[Dict[str, Any]] = []
            try:
                raw_history = broker_service.get_historical_data(
                    token, datetime.now(timezone.utc) - timedelta(days=45),
                    datetime.now(timezone.utc), "day", continuous=False, oi=False,
                ) or []
                for candle in raw_history[-30:]:
                    close = _number(candle.get("close"))
                    candle_date = _timestamp(candle.get("date"))
                    if close is not None and close > 0 and candle_date:
                        history.append({"date": candle_date, "close": close})
            except Exception:
                history = list(persisted.get("historical_series") or [])[-30:]
            regime = "LOW" if value < 12.0 else "NORMAL" if value < 18.0 else "ELEVATED" if value < 25.0 else "HIGH"
            snapshot = {
                "status": "AVAILABLE", "value": value, "change": change, "change_pct": change_pct,
                "observation_timestamp": observed, "source": "Kite Quote API",
                "source_authority": "PRIMARY", "source_symbol": source_symbol,
                "instrument_token": token, "freshness": "LAST_VALID_SESSION" if market_closed else "FRESH",
                "observation_mode": "LAST_VALID_SESSION" if market_closed else "LIVE",
                "retrieved_at": attempted_at, "previous_close": previous,
                "historical_series": history, "regime": regime,
                "regime_version": cls.INDIA_VIX_REGIME_VERSION,
                "regime_thresholds": {"LOW": "<12", "NORMAL": "12-<18", "ELEVATED": "18-<25", "HIGH": ">=25"},
                "cache_restored": False, "failure_reason": None,
            }
            cls._persist_json(path, snapshot)
            if cache_path is None:
                cls._india_vix_memory = dict(snapshot)
                cls._india_vix_last_fetch = time.time()
            return snapshot
        except Exception as exc:
            if persisted.get("value") and persisted.get("observation_timestamp") and persisted.get("source_symbol") == "NSE:INDIA VIX":
                restored = {**persisted, "status": "DEGRADED", "freshness": "LAST_VALID_SESSION",
                            "observation_mode": "LAST_VALID_SESSION", "cache_restored": True,
                            "last_attempt": attempted_at, "failure_reason": str(exc)[:240]}
                if cache_path is None:
                    cls._india_vix_memory = dict(restored)
                    cls._india_vix_last_fetch = time.time()
                return restored
            return {
                "status": "UNAVAILABLE", "value": None, "change": None, "change_pct": None,
                "observation_timestamp": None, "source": "Kite Quote API",
                "source_authority": "PRIMARY", "source_symbol": "NSE:INDIA VIX",
                "freshness": "UNAVAILABLE", "observation_mode": "UNAVAILABLE",
                "retrieved_at": attempted_at, "historical_series": [], "regime": "UNAVAILABLE",
                "regime_version": cls.INDIA_VIX_REGIME_VERSION, "failure_reason": str(exc)[:240],
            }
