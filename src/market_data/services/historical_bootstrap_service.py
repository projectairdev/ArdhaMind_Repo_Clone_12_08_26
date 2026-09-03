from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timezone
import threading
from typing import Any, Dict, List, Optional, Sequence
from uuid import uuid4

from src.market_data.interfaces.historical_data_provider import IHistoricalDataProvider
from src.market_data.models.canonical_candle import CanonicalCandle
from src.market_data.models.canonical_instrument import CanonicalInstrument
from src.market_data.models.quality_enums import CandleQuality, Timeframe


def _sanitize_path_component(name: str) -> str:
    """Replaces colons and slashes with underscores for filesystem directory safety."""
    return re.sub(r"[:/\\ ]+", "_", name.strip())


def _parse_iso_datetime(ts_str: str) -> datetime:
    """Parses an ISO datetime string into a timezone-aware UTC datetime."""
    dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class HistoricalBootstrapService:
    """
    Manages local filesystem caching and on-demand fetching of historical CanonicalCandles.
    Enforces atomic file persistence, schema validation, and zero synthetic interpolation.
    """

    DEFAULT_STORAGE_DIR = os.path.join("data", "market_history")

    def __init__(
        self,
        historical_provider: Optional[IHistoricalDataProvider] = None,
        storage_dir: str = DEFAULT_STORAGE_DIR,
    ) -> None:
        self.historical_provider = historical_provider
        self.storage_dir = storage_dir
        self._lock = threading.RLock()
        os.makedirs(self.storage_dir, exist_ok=True)

    def _get_file_path(
        self,
        canonical_id: str,
        timeframe: Timeframe | str,
        session_date: date,
    ) -> str:
        clean_id = _sanitize_path_component(canonical_id)
        tf_str = timeframe.value if hasattr(timeframe, "value") else str(timeframe)
        date_str = session_date.isoformat()
        dir_path = os.path.join(self.storage_dir, clean_id, tf_str)
        os.makedirs(dir_path, exist_ok=True)
        return os.path.join(dir_path, f"{date_str}.json")

    def load_session_candles(
        self,
        instrument: CanonicalInstrument,
        session_date: date,
        timeframe: Timeframe | str,
    ) -> Optional[List[CanonicalCandle]]:
        """
        Loads and validates historical candles from local disk storage.
        Returns None if file is missing, corrupt, or fails OHLC invariants.
        """
        cid = instrument.canonical_id
        tf_str = timeframe.value if hasattr(timeframe, "value") else str(timeframe)
        file_path = self._get_file_path(cid, tf_str, session_date)

        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Metadata validation
            if data.get("canonical_instrument_id") != cid:
                return None
            if data.get("session_date") != session_date.isoformat():
                return None
            if data.get("timeframe") != tf_str:
                return None

            provider_str = data.get("provider", "UNKNOWN")
            raw_candles = data.get("candles", [])
            parsed_candles: List[CanonicalCandle] = []

            for rc in raw_candles:
                start_dt = _parse_iso_datetime(rc["start_timestamp"])
                end_dt = _parse_iso_datetime(rc["end_timestamp"])
                q_val = CandleQuality(rc.get("quality", CandleQuality.VALID.value))

                candle = CanonicalCandle(
                    canonical_instrument_id=cid,
                    provider=provider_str,
                    session_date=session_date,
                    timeframe=Timeframe(tf_str) if tf_str in [t.value for t in Timeframe] else tf_str,
                    start_timestamp=start_dt,
                    end_timestamp=end_dt,
                    open=float(rc["open"]),
                    high=float(rc["high"]),
                    low=float(rc["low"]),
                    close=float(rc["close"]),
                    volume=int(rc["volume"]) if rc.get("volume") is not None else None,
                    oi=int(rc["oi"]) if rc.get("oi") is not None else None,
                    quality=q_val,
                )
                parsed_candles.append(candle)

            parsed_candles.sort(key=lambda c: c.start_timestamp)
            return parsed_candles
        except Exception:
            # Corrupted or malformed file is rejected safely
            return None

    def save_session_candles(
        self,
        instrument: CanonicalInstrument,
        session_date: date,
        timeframe: Timeframe | str,
        provider: str,
        candles: Sequence[CanonicalCandle],
    ) -> None:
        """
        Atomically persists validated CanonicalCandles to disk JSON format.
        """
        cid = instrument.canonical_id
        tf_str = timeframe.value if hasattr(timeframe, "value") else str(timeframe)
        file_path = self._get_file_path(cid, tf_str, session_date)

        candle_dicts = []
        for c in candles:
            if not isinstance(c, CanonicalCandle):
                continue
            candle_dicts.append({
                "start_timestamp": c.start_timestamp.isoformat().replace("+00:00", "Z"),
                "end_timestamp": c.end_timestamp.isoformat().replace("+00:00", "Z"),
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
                "volume": c.volume,
                "oi": c.oi,
                "quality": c.quality.value if hasattr(c.quality, "value") else str(c.quality),
            })

        payload = {
            "canonical_instrument_id": cid,
            "session_date": session_date.isoformat(),
            "timeframe": tf_str,
            "provider": provider,
            "saved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "candle_count": len(candle_dicts),
            "candles": candle_dicts,
        }

        tmp_path = f"{file_path}.tmp.{uuid4().hex[:8]}"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        # Atomic replacement
        os.replace(tmp_path, file_path)

    def bootstrap(
        self,
        instruments: Sequence[CanonicalInstrument],
        dates: Sequence[date],
        timeframes: Sequence[Timeframe | str] = (Timeframe.M1,),
    ) -> Dict[str, List[CanonicalCandle]]:
        """
        Ensures historical candles exist locally for all requested instruments, dates, and timeframes.
        Reuses local disk archives when valid; fetches missing sessions from historical provider.
        Returns a dictionary mapping 'canonical_id:timeframe:session_date' -> list of CanonicalCandle.
        """
        results: Dict[str, List[CanonicalCandle]] = {}

        for inst in instruments:
            cid = inst.canonical_id
            for s_date in dates:
                for tf in timeframes:
                    tf_str = tf.value if hasattr(tf, "value") else str(tf)
                    key = f"{cid}:{tf_str}:{s_date.isoformat()}"

                    # 1. Try local cache
                    cached = self.load_session_candles(inst, s_date, tf)
                    if cached is not None and len(cached) > 0:
                        results[key] = cached
                        continue

                    # 2. Fetch from provider if available
                    if self.historical_provider is not None:
                        start_dt = datetime(s_date.year, s_date.month, s_date.day, 0, 0, 0, tzinfo=timezone.utc)
                        end_dt = datetime(s_date.year, s_date.month, s_date.day, 23, 59, 59, tzinfo=timezone.utc)
                        fetched = self.historical_provider.fetch_candles(
                            instrument=inst,
                            timeframe=tf,
                            start=start_dt,
                            end=end_dt,
                        )
                        if fetched:
                            valid_candles = [c for c in fetched if isinstance(c, CanonicalCandle)]
                            prov_name = self.historical_provider.provider_name()
                            self.save_session_candles(inst, s_date, tf, prov_name, valid_candles)
                            results[key] = valid_candles
                        else:
                            results[key] = []
                    else:
                        results[key] = []

        return results
