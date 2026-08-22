"""
src/storage/lightweight_session_store.py

Master Lightweight Session Storage Subsystem for AIR Ardha.
Implements modular, domain-partitioned, atomic persistence for all market sessions.
"""
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.storage.atomic_store import atomic_read_json, atomic_write_json, append_jsonl, read_jsonl
from src.storage.reconciliation import CloseReconciler
from src.storage.retention_manager import RetentionManager
from src.storage.schemas import (
    CloseReconciliationPolicy,
    ConnectivityEvent,
    IntradayTelemetrySeries,
    LatestCanonicalRecoverySnapshot,
    MarketOHLCV,
    OptionsCloseBaseline,
    SessionCloseCore,
    SessionIntegrityEnvelope,
    StructuralLevels,
    TelemetryBucket,
)

logger = logging.getLogger(__name__)


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
        self.base_dir = Path(base_dir or "/opt/ardhamind/staging/data/session_store").resolve()
        self.close_dir = self.base_dir / "close"
        self.options_dir = self.base_dir / "options_close"
        self.telemetry_dir = self.base_dir / "telemetry"
        self.integrity_dir = self.base_dir / "integrity"
        self.connectivity_dir = self.base_dir / "connectivity"
        self.cache_dir = self.base_dir / "cache"

        # Ensure base directories exist
        for d in (self.close_dir, self.options_dir, self.telemetry_dir, self.integrity_dir, self.connectivity_dir, self.cache_dir):
            d.mkdir(parents=True, exist_ok=True)

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
        snap = LatestCanonicalRecoverySnapshot(
            schema_name="LATEST_CANONICAL_RECOVERY_SNAPSHOT",
            schema_version="1.1.0",
            runtime_id=runtime_id,
            state_sequence=state_sequence,
            generated_at=now_str,
            session_date=session_date,
            market_session_phase=market_session_phase,
            state=state
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

    def load_latest_session_close(self) -> Optional[SessionCloseCore]:
        """
        Returns the most recent finalized trading session close.
        Automatically steps backwards across weekends/holidays.
        """
        files = sorted(
            [f for f in self.close_dir.glob("*.json") if not f.name.endswith(".tmp")],
            key=lambda p: p.name,
            reverse=True
        )
        for f in files:
            data = atomic_read_json(f)
            if data:
                return SessionCloseCore.from_dict(data)
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
        
        close_core = SessionCloseCore(
            session_date=session_date,
            finalized_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
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
            structural_levels=StructuralLevels(pivot=pivot, r1=r1, r2=r2, s1=s1, s2=s2),
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
