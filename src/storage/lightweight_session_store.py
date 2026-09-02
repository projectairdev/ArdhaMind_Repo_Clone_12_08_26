"""
src/storage/lightweight_session_store.py

Master Lightweight Session Storage Subsystem for AIR Ardha.
Implements modular, domain-partitioned, atomic persistence for all market sessions.
"""
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.storage.atomic_store import atomic_read_json, atomic_write_json, append_jsonl, read_jsonl, cleanup_orphaned_tmp_files
from src.storage.reconciliation import CloseReconciler
from src.storage.retention_manager import RetentionManager
from src.storage.schemas import (
    CloseReconciliationPolicy,
    ConnectivityEvent,
    IntradayTelemetrySeries,
    LatestCanonicalRecoverySnapshot,
    MarketOHLCV,
    MarketRegime,
    OptionsCloseBaseline,
    SessionCloseCore,
    SessionIntegrityEnvelope,
    StructuralLevels,
    TelemetryBucket,
)

logger = logging.getLogger(__name__)


def _extract_lean_recovery_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts lean numerical and analytical telemetry for recovery snapshot,
    purging large narrative paragraphs, HTML formatting, and presentation blobs.
    Target footprint: ~12 KB / save (reduced from ~185 KB).
    """
    if not isinstance(state, dict):
        return {}

    lean: Dict[str, Any] = {}

    # 1. Essential metadata & sequence identifiers
    for k in ("generated_at", "sequence", "state_sequence", "runtime_id", "timestamp", "session_date", "trading_date", "version"):
        if k in state:
            lean[k] = state[k]

    # 2. Market Data & Context (spot, OHLC, VIX, breadth)
    if "market_data" in state and isinstance(state["market_data"], dict):
        md = state["market_data"]
        lean["market_data"] = {
            k: v for k, v in md.items()
            if k in (
                "current_spot", "open", "high", "low", "previous_close", "volume", "vwap",
                "oi", "change_points", "change_pct", "observed_at", "last_tick_time",
                "feed_health", "source_type", "vix", "breadth", "nifty_previous_close"
            )
        }
    elif "marketContext" in state and isinstance(state["marketContext"], dict):
        mc = state["marketContext"]
        lean["marketContext"] = {
            k: v for k, v in mc.items()
            if k in (
                "current_spot", "spot", "open", "high", "low", "previous_close", "volume",
                "vwap", "oi", "change_points", "change_pct", "vix", "breadth", "timestamp"
            )
        }

    # 3. Market Session status
    if "market_session" in state:
        lean["market_session"] = state["market_session"]
    elif "sessionPhase" in state:
        lean["sessionPhase"] = state["sessionPhase"]

    # 4. Structural Levels
    if "structural_levels" in state:
        lean["structural_levels"] = state["structural_levels"]

    # 5. Option Intelligence / Context (key metrics only)
    if "option_intelligence" in state and isinstance(state["option_intelligence"], dict):
        opt = state["option_intelligence"]
        lean["option_intelligence"] = {
            k: v for k, v in opt.items()
            if k in (
                "underlying_price", "atm_strike", "pcr", "pcr_volume", "max_pain",
                "call_wall", "put_wall", "atm_iv", "total_call_oi", "total_put_oi",
                "highest_call_oi_strike", "highest_put_oi_strike"
            )
        }
    elif "optionContext" in state and isinstance(state["optionContext"], dict):
        opt = state["optionContext"]
        lean["optionContext"] = {
            k: v for k, v in opt.items()
            if k in (
                "underlying_spot", "atm_strike", "pcr_oi", "pcr_volume", "max_pain",
                "call_wall", "put_wall", "atm_iv_pct", "total_call_oi_crores", "total_put_oi_crores"
            )
        }

    # 6. Data Quality
    if "data_quality" in state:
        lean["data_quality"] = state["data_quality"]

    return lean


class LightweightSessionStore:
    """
    Central storage interface managing all lightweight session domains:
    1. Recovery Snapshots (cache/latest_canonical_state.json)
    2. Rolling 5-day Candle Caches (cache/nifty_5m_candles.json)
    3. Permanent EOD Session Close Core (close/YYYY-MM-DD.json)
    4. Permanent EOD Options Close Baseline (options_close/YYYY-MM-DD.json)
    5. Rolling 5-day Intraday Telemetry Series (telemetry/YYYY-MM-DD.json)
    6. Rolling 30-day Connectivity Event Logs (connectivity/YYYY-MM-DD.jsonl)
    7. Permanent Session Integrity Envelopes (integrity/YYYY-MM-DD.json)
    8. Active Catalyst Carry-Forward (cache/active_catalysts.json)
    """

    _instance: Optional["LightweightSessionStore"] = None

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir:
            self.base_dir = Path(base_dir).resolve()
        else:
            workspace_data_store = Path(__file__).resolve().parent.parent.parent / "data" / "session_store"
            if workspace_data_store.parent.exists():
                self.base_dir = workspace_data_store.resolve()
            else:
                self.base_dir = Path("/opt/ardhamind/staging/data/session_store").resolve()
        self.close_dir = self.base_dir / "close"
        self.options_dir = self.base_dir / "options_close"
        self.telemetry_dir = self.base_dir / "telemetry"
        self.integrity_dir = self.base_dir / "integrity"
        self.connectivity_dir = self.base_dir / "connectivity"
        self.cache_dir = self.base_dir / "cache"

        # Ensure base directories exist
        for d in (self.close_dir, self.options_dir, self.telemetry_dir, self.integrity_dir, self.connectivity_dir, self.cache_dir):
            d.mkdir(parents=True, exist_ok=True)

        # Boot-time orphan temp file sweep (age-gated > 5 mins)
        cleanup_orphaned_tmp_files(self.base_dir, max_age_seconds=300.0)

        # In-memory transient candidate buffers
        self._latest_valid_options_cache: Dict[str, OptionsCloseBaseline] = {}
        self._latest_valid_candle_cache: List[Dict[str, Any]] = []

    @classmethod
    def get_instance(cls, base_dir: Optional[Path] = None) -> "LightweightSessionStore":
        if cls._instance is None:
            cls._instance = cls(base_dir)
        return cls._instance

    # ── 1. Recovery Snapshot ──────────────────────────────────────────────────

    def load_recovery_state(self) -> Optional[LatestCanonicalRecoverySnapshot]:
        target = self.cache_dir / "latest_canonical_state.json"
        data = atomic_read_json(target)
        if not data:
            return None
        return LatestCanonicalRecoverySnapshot.from_dict(data)

    def persist_recovery_state(
        self,
        state: Dict[str, Any],
        runtime_id: str = "",
        state_sequence: int = 0,
        session_date: str = "",
        market_session_phase: str = ""
    ) -> bool:
        target = self.cache_dir / "latest_canonical_state.json"
        now_str = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        lean_state = _extract_lean_recovery_state(state)
        snap = LatestCanonicalRecoverySnapshot(
            schema_name="LATEST_CANONICAL_RECOVERY_SNAPSHOT",
            schema_version="1.2.0",
            runtime_id=runtime_id,
            state_sequence=state_sequence,
            generated_at=now_str,
            session_date=session_date,
            market_session_phase=market_session_phase,
            state=lean_state
        )
        return atomic_write_json(target, snap.to_dict())

    # ── 2. Candle Cache ───────────────────────────────────────────────────────

    def load_candle_cache(self, timeframe: str = "5m") -> List[Dict[str, Any]]:
        target = self.cache_dir / f"nifty_{timeframe}_candles.json"
        data = atomic_read_json(target)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "candles" in data:
            return data["candles"]
        return []

    def sync_candles(self, candles: List[Dict[str, Any]], timeframe: str = "5m", max_sessions: int = 5) -> bool:
        """
        Synchronizes candle buffer, deduplicates by timestamp, and retains last 5 trading sessions.
        """
        if not candles:
            return True
            
        target = self.cache_dir / f"nifty_{timeframe}_candles.json"
        
        # Deduplicate candles by date/timestamp string
        seen = {}
        for c in candles:
            dt_key = str(c.get("date") or c.get("timestamp") or "")
            if dt_key:
                seen[dt_key] = c
                
        # Sort chronologically
        sorted_candles = [seen[k] for k in sorted(seen.keys())]
        
        # Keep maximum 5 trading sessions (approx 375 5-min bars)
        # Cap at 500 bars to guarantee safe margin for 5 sessions
        if len(sorted_candles) > 500:
            sorted_candles = sorted_candles[-500:]
            
        self._latest_valid_candle_cache = sorted_candles
        return atomic_write_json(target, sorted_candles)

    # ── 3. Session Close Core (PERMANENT) ──────────────────────────────────────

    def load_session_close(self, session_date: str) -> Optional[SessionCloseCore]:
        target = self.close_dir / f"{session_date}.json"
        data = atomic_read_json(target)
        if not data:
            return None
        return SessionCloseCore.from_dict(data)

    def load_latest_session_close(self, force_reload: bool = False) -> Optional[SessionCloseCore]:
        """
        Returns the most recent finalized trading session close with in-memory memoization.
        Automatically steps backwards across weekends/holidays.
        If no finalized close file exists, recovers from candle cache or performance records.
        """
        import time
        now = time.time()
        cached_close = getattr(self, "_cached_latest_close", None)
        cached_time = getattr(self, "_cached_latest_close_time", 0.0)
        if not force_reload and cached_close is not None and (now - cached_time) < 2.0:
            return cached_close

        # Check for auto-recovery from local candle cache first to guarantee most recent session
        recovered = self._auto_recover_latest_close()

        files = sorted(
            [f for f in self.close_dir.glob("*.json") if not f.name.endswith(".tmp")],
            key=lambda p: p.name,
            reverse=True
        )
        for f in files:
            data = atomic_read_json(f)
            if data:
                close_obj = SessionCloseCore.from_dict(data)
                # If recovered candle cache is strictly newer than this file, prefer recovered
                if recovered and recovered.session_date and close_obj.session_date and recovered.session_date > close_obj.session_date:
                    self._cached_latest_close = recovered
                    self._cached_latest_close_time = now
                    return recovered
                self._cached_latest_close = close_obj
                self._cached_latest_close_time = now
                return close_obj

        if recovered:
            self._cached_latest_close = recovered
            self._cached_latest_close_time = now
        return recovered

    def load_fast_boot_baseline(self) -> Dict[str, Any]:
        """
        Fast-boot non-blocking baseline loader for lean cold start.
        Reads only the lean carry-forward file (close/YYYY-MM-DD.json ~12 KB)
        and options baseline (224 bytes), completely bypassing multi-MB historical session files.
        """
        close_core = self.load_latest_session_close()
        opt_baseline = self.load_latest_options_baseline()
        return {
            "close_core": close_core,
            "options_baseline": opt_baseline,
            "loaded_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

    def _auto_recover_latest_close(self) -> Optional[SessionCloseCore]:
        """Auto-recovers SessionCloseCore from verified local candle cache."""
        try:
            cache_file = Path("data/cache/nifty_candles_cache.json").resolve()
            if not cache_file.exists():
                cache_file = (self.base_dir / "cache" / "nifty_candles_cache.json").resolve()
            if not cache_file.exists():
                cache_file = (self.base_dir.parent / "cache" / "nifty_candles_cache.json").resolve()
            if cache_file.exists():
                candles = atomic_read_json(cache_file)
                if isinstance(candles, list) and len(candles) > 0:
                    first_date = str(candles[0].get("date", ""))
                    session_date = first_date[:10] if len(first_date) >= 10 else None
                    if not session_date:
                        return None

                    c_open = float(candles[0]["open"]) if candles[0].get("open") is not None else None
                    highs = [float(c["high"]) for c in candles if c.get("high") is not None]
                    lows = [float(c["low"]) for c in candles if c.get("low") is not None]
                    if not highs or not lows or c_open is None or candles[-1].get("close") is None:
                        return None

                    c_high = max(highs)
                    c_low = min(lows)
                    c_close = float(candles[-1]["close"])
                    c_vol = int(sum(int(c.get("volume", 0) or 0) for c in candles))

                    # 15m Opening Range (first 15 1m candles)
                    or_candles = candles[:15] if len(candles) >= 15 else candles
                    or_highs = [float(c["high"]) for c in or_candles if c.get("high") is not None]
                    or_lows = [float(c["low"]) for c in or_candles if c.get("low") is not None]
                    or_h = max(or_highs) if or_highs else None
                    or_l = min(or_lows) if or_lows else None

                    # Typical VWAP from candles
                    c_vwap = round(sum(float(c.get("close", 0)) for c in candles) / len(candles), 2)

                    # Structural pivots calculated purely from candle OHLC
                    pivot = round((c_high + c_low + c_close) / 3.0, 2)
                    r1 = round((2.0 * pivot) - c_low, 2)
                    s1 = round((2.0 * pivot) - c_high, 2)
                    r2 = round(pivot + (c_high - c_low), 2)
                    s2 = round(pivot - (c_high - c_low), 2)

                    close_core = SessionCloseCore(
                        session_date=session_date,
                        finalized_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                        session_vwap=c_vwap,
                        or_high=or_h,
                        or_low=or_l,
                        market_ohlcv=MarketOHLCV(
                            open=c_open,
                            high=c_high,
                            low=c_low,
                            close=c_close,
                            volume=c_vol,
                            previous_close=None,
                            change_points=None,
                            change_percent=None,
                            session_range_points=round(c_high - c_low, 2)
                        ),
                        structural_levels=StructuralLevels(pivot=pivot, r1=r1, r2=r2, s1=s1, s2=s2, raw_atr_14=None),
                        market_regime=MarketRegime(regime="RANGE_BOUND"),
                        closing_vix=None,
                        closing_breadth=None,
                        institutional_flows=None,
                        provenance={
                            "provider": "LOCAL_CANDLE_CACHE_RECOVERY",
                            "reconciliation_policy": "v1.0-standard",
                            "reconciliation_status": "AUTO_RECOVERED"
                        }
                    )
                    self.finalize_session_close(close_core)
                    return close_core
        except Exception as exc:
            logger.warning(f"[SessionStore] Auto-recovery of latest close failed: {exc}")
        return None

    def finalize_session_close(self, close_core: SessionCloseCore) -> bool:
        if not close_core.session_date:
            logger.error("[SessionStore] Cannot finalize SessionCloseCore without session_date")
            return False
            
        target = self.close_dir / f"{close_core.session_date}.json"
        if not close_core.finalized_at:
            close_core.finalized_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            
        return atomic_write_json(target, close_core.to_dict())

    # ── 4. Options Close Baseline (PERMANENT) ──────────────────────────────────

    def load_options_baseline(self, session_date: str) -> Optional[OptionsCloseBaseline]:
        target = self.options_dir / f"{session_date}.json"
        data = atomic_read_json(target)
        if not data:
            return None
        return OptionsCloseBaseline.from_dict(data)

    def load_latest_options_baseline(self) -> Optional[OptionsCloseBaseline]:
        files = sorted(
            [f for f in self.options_dir.glob("*.json") if not f.name.endswith(".tmp")],
            key=lambda p: p.name,
            reverse=True
        )
        for f in files:
            data = atomic_read_json(f)
            if data:
                return OptionsCloseBaseline.from_dict(data)
        return None

    def record_pre_close_options(self, baseline: OptionsCloseBaseline) -> None:
        """
        Stores valid options depth candidate in memory during 15:20 pre-close window.
        Guarantees that an off-hours empty packet will not overwrite this candidate.
        """
        if baseline and baseline.strike_baseline:
            self._latest_valid_options_cache[baseline.session_date] = baseline

    def finalize_options_baseline(self, baseline: OptionsCloseBaseline) -> bool:
        """
        Finalizes closing options baseline.
        If the provided baseline has no strikes (off-hours), uses latest valid pre-close candidate.
        """
        target_baseline = baseline
        if (not target_baseline.strike_baseline) and (baseline.session_date in self._latest_valid_options_cache):
            target_baseline = self._latest_valid_options_cache[baseline.session_date]
            
        if not target_baseline.session_date or not target_baseline.strike_baseline:
            logger.warning("[SessionStore] Finalizing OptionsCloseBaseline with empty strike baseline")
            
        target = self.options_dir / f"{target_baseline.session_date}.json"
        if not target_baseline.captured_at:
            target_baseline.captured_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            
        return atomic_write_json(target, target_baseline.to_dict())

    # ── 5. Intraday Telemetry Series (Rolling 5 Sessions) ──────────────────────

    def load_telemetry_series(self, session_date: str) -> List[Dict[str, Any]]:
        target = self.telemetry_dir / f"{session_date}.json"
        data = atomic_read_json(target)
        if not data:
            return []
        series = IntradayTelemetrySeries.from_dict(data)
        return series.buckets

    def record_telemetry_bucket(self, session_date: str, bucket: Dict[str, Any]) -> bool:
        target = self.telemetry_dir / f"{session_date}.json"
        existing = atomic_read_json(target)
        
        series = IntradayTelemetrySeries.from_dict(existing) if existing else IntradayTelemetrySeries(session_date=session_date)
        
        # Deduplicate/update bucket by index or window_start
        b_idx = bucket.get("index") or len(series.buckets) + 1
        bucket["index"] = b_idx
        
        updated_buckets = [b for b in series.buckets if b.get("index") != b_idx]
        updated_buckets.append(bucket)
        updated_buckets.sort(key=lambda x: x.get("index", 0))
        
        series.buckets = updated_buckets
        series.total_buckets = len(updated_buckets)
        
        return atomic_write_json(target, series.to_dict())

    # ── 6. Connectivity Events (Rolling 30 Sessions) ──────────────────────────

    def record_connectivity_event(self, event: ConnectivityEvent) -> bool:
        target = self.connectivity_dir / f"{event.session_date}.jsonl"
        return append_jsonl(target, event.to_dict())

    def load_connectivity_events(self, session_date: str) -> List[Dict[str, Any]]:
        target = self.connectivity_dir / f"{session_date}.jsonl"
        return read_jsonl(target)

    # ── 7. Session Integrity Envelope (PERMANENT) ─────────────────────────────

    def load_integrity_envelope(self, session_date: str) -> Optional[SessionIntegrityEnvelope]:
        target = self.integrity_dir / f"{session_date}.json"
        data = atomic_read_json(target)
        if not data:
            return None
        return SessionIntegrityEnvelope.from_dict(data)

    def finalize_integrity_envelope(self, envelope: SessionIntegrityEnvelope) -> bool:
        target = self.integrity_dir / f"{envelope.session_date}.json"
        envelope.finalization_status = "FINALIZED"
        return atomic_write_json(target, envelope.to_dict())

    # ── 8. Active Catalysts ───────────────────────────────────────────────────

    def load_active_catalysts(self) -> List[Dict[str, Any]]:
        target = self.cache_dir / "active_catalysts.json"
        data = atomic_read_json(target)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "active_catalysts" in data:
            return data["active_catalysts"]
        return []

    def update_active_catalysts(self, catalysts: List[Dict[str, Any]]) -> bool:
        target = self.cache_dir / "active_catalysts.json"
        return atomic_write_json(target, {"active_catalysts": catalysts, "updated_at": datetime.now(timezone.utc).isoformat()})

    # ── 9. Missed-Close Recovery ──────────────────────────────────────────────

    def recover_missed_close(
        self,
        session_date: str,
        historical_ohlc: Dict[str, Any],
        policy: Optional[CloseReconciliationPolicy] = None
    ) -> bool:
        """
        Recovers missed session close upon server restart using historical OHLC from broker API.
        """
        logger.info(f"[SessionStore] Initiating missed close recovery for {session_date}")
        
        c_open = float(historical_ohlc.get("open", 0))
        c_high = float(historical_ohlc.get("high", 0))
        c_low = float(historical_ohlc.get("low", 0))
        c_close = float(historical_ohlc.get("close", 0))
        c_volume = int(historical_ohlc.get("volume", 0))
        
        if c_close <= 0:
            logger.error(f"[SessionStore] Historical OHLC invalid for recovery: {historical_ohlc}")
            return False
            
        prev_close_obj = self.load_latest_session_close()
        prev_close_val = prev_close_obj.market_ohlcv.close if prev_close_obj and prev_close_obj.market_ohlcv else c_open
        
        # Derive structural pivot levels
        pivot = round((c_high + c_low + c_close) / 3.0, 2)
        r1 = round((2.0 * pivot) - c_low, 2)
        s1 = round((2.0 * pivot) - c_high, 2)
        r2 = round(pivot + (c_high - c_low), 2)
        s2 = round(pivot - (c_high - c_low), 2)
        
        c_vwap = float(historical_ohlc["vwap"]) if historical_ohlc.get("vwap") is not None else None
        c_or_high = float(historical_ohlc["or_high"]) if historical_ohlc.get("or_high") is not None else None
        c_or_low = float(historical_ohlc["or_low"]) if historical_ohlc.get("or_low") is not None else None
        c_atr = float(historical_ohlc.get("raw_atr_14") or historical_ohlc.get("atr_14") or historical_ohlc.get("atr")) if (historical_ohlc.get("raw_atr_14") or historical_ohlc.get("atr_14") or historical_ohlc.get("atr")) else None

        close_core = SessionCloseCore(
            session_date=session_date,
            finalized_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            session_vwap=c_vwap,
            or_high=c_or_high,
            or_low=c_or_low,
            market_ohlcv=MarketOHLCV(
                open=c_open,
                high=c_high,
                low=c_low,
                close=c_close,
                volume=c_volume,
                previous_close=prev_close_val,
                change_points=round(c_close - prev_close_val, 2) if prev_close_val else None,
                change_percent=round(((c_close - prev_close_val) / prev_close_val) * 100.0, 4) if prev_close_val else None,
                session_range_points=round(c_high - c_low, 2)
            ),
            structural_levels=StructuralLevels(pivot=pivot, r1=r1, r2=r2, s1=s1, s2=s2, raw_atr_14=c_atr),
            provenance={
                "provider": "ZERODHA_KITE_HISTORICAL_API",
                "reconciliation_policy": (policy or CloseReconciliationPolicy()).policy_version,
                "reconciliation_status": "RECOVERED_HISTORICAL_API"
            }
        )
        
        # Finalize recovered session close
        res_close = self.finalize_session_close(close_core)
        
        # Write integrity record for recovery
        envelope = SessionIntegrityEnvelope(
            session_date=session_date,
            finalization_status="RECOVERED_POST_CLOSE",
            completeness_status="RECOVERED_HISTORICAL",
            warnings=["Missed market-close finalization recovered from Kite historical daily API on restart."]
        )
        self.finalize_integrity_envelope(envelope)
        
        return res_close

    # ── 10. Maintenance & Health ──────────────────────────────────────────────

    def prune_expired_sessions(self) -> Dict[str, int]:
        return RetentionManager.prune_rolling_stores(self.base_dir)

    def get_storage_health(self) -> Dict[str, Any]:
        close_count = len(list(self.close_dir.glob("*.json")))
        options_count = len(list(self.options_dir.glob("*.json")))
        telemetry_count = len(list(self.telemetry_dir.glob("*.json")))
        integrity_count = len(list(self.integrity_dir.glob("*.json")))
        
        latest_close = self.load_latest_session_close()
        
        return {
            "status": "HEALTHY",
            "close_core_files": close_count,
            "options_baseline_files": options_count,
            "telemetry_files": telemetry_count,
            "integrity_files": integrity_count,
            "latest_finalized_session": latest_close.session_date if latest_close else "NONE",
            "base_dir": str(self.base_dir)
        }
