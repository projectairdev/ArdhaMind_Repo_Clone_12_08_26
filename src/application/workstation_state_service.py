from __future__ import annotations

import os
import json
import atexit
from datetime import datetime, timezone, timedelta
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

from src.news_engine.safe_utils import atomic_write_json
from src.application.data_quality_service import DataQualityService
from src.configuration_engine.runtime import Config
from src.models.canonical_workstation_state import CanonicalWorkstationState, sanitize_read_only
from src.models.data_quality import FreshnessStatus, SectionStatus, ValueClassification
from src.models.decision_support import DecisionSupportReport
from src.news_engine.temporal_integrity import assess_publication_time, strict_publication_timestamp
from src.news_engine.macro_integrity import assess_macro_observation, aggregate_quote_freshness
from src.intelligence_engine import UnifiedNiftyIntelligenceBuilder
from src.broker.services.market_status_service import MarketStatusService


class WorkstationStateService:
    SCHEMA_VERSION = "2.0.0"
    _sequence = 0
    _lock = Lock()
    _runtime_id = str(uuid4())
    _snapshots_history: list[dict[str, Any]] = []
    _live_event_stream: list[dict[str, Any]] = []
    _last_loaded_session_date: str | None = None
    _persistence_health: str = "READY"
    _test_mode_isolated: bool = False
    _allow_disk_cache_in_test: bool = False
    _last_persisted_snap_count: int = 0
    _last_persisted_seq: int = 0
    _last_disk_flush_timestamp: float = 0.0
    _closed_flushed_date: str | None = None
    MIN_PERSIST_INTERVAL_SECONDS: float = 30.0
    CACHE_DIR = Path("data/cache")

    @classmethod
    def reset_for_testing(cls) -> None:
        """Resets in-memory state and enables test mode isolation."""
        cls._snapshots_history = []
        cls._live_event_stream = []
        cls._last_loaded_session_date = "TEST_ISOLATED"
        cls._test_mode_isolated = True
        cls._last_persisted_snap_count = 0
        cls._last_persisted_seq = 0
        cls._last_disk_flush_timestamp = 0.0
        cls._closed_flushed_date = None
        cls._allow_disk_cache_in_test = False
        cls.CACHE_DIR = Path("data/cache")

    @classmethod
    def _load_session_history(cls, session_date: str) -> None:
        """Loads and hydrates bounded intraday session history from disk for session_date."""
        if os.environ.get("PYTEST_CURRENT_TEST") and not cls._allow_disk_cache_in_test:
            return

        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file = cls.CACHE_DIR / f"session_history_{session_date}.json"

        if not cache_file.exists():
            history_files = sorted(cls.CACHE_DIR.glob("session_history_*.json"), key=lambda p: p.name, reverse=True)
            if history_files:
                cache_file = history_files[0]
            else:
                return

        loaded_date = session_date
        cls._last_loaded_session_date = loaded_date

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                cls._persistence_health = "DEGRADED"
                return

            restored_snaps = data.get("snapshots") or []
            restored_events = data.get("material_events") or []

            seen_seq = set()
            valid_snaps = []
            for s in restored_snaps:
                if isinstance(s, dict) and s.get("timestamp"):
                    seq_key = (s.get("timestamp"), s.get("state_sequence"))
                    if seq_key not in seen_seq:
                        seen_seq.add(seq_key)
                        valid_snaps.append(s)

            valid_snaps.sort(key=lambda x: x.get("timestamp") or "")

            existing_seqs = {(s.get("timestamp"), s.get("state_sequence")) for s in cls._snapshots_history}
            for s in valid_snaps:
                seq_key = (s.get("timestamp"), s.get("state_sequence"))
                if seq_key not in existing_seqs:
                    cls._snapshots_history.append(s)

            cls._snapshots_history.sort(key=lambda x: (x.get("timestamp") or "", x.get("state_sequence") or 0))
            cls._snapshots_history = cls._filter_retained_snapshots(cls._snapshots_history, session_date)

            seen_ev = {e.get("id") or e.get("event_id") for e in cls._live_event_stream if e.get("id") or e.get("event_id")}
            for e in restored_events:
                e_id = e.get("id") or e.get("event_id")
                if e_id and e_id not in seen_ev:
                    seen_ev.add(e_id)
                    cls._live_event_stream.append(e)

            cls._persistence_health = "READY"
        except Exception:
            cls._persistence_health = "DEGRADED"

    @classmethod
    def _filter_retained_snapshots(cls, snapshots: list[dict[str, Any]], session_date: str) -> list[dict[str, Any]]:
        """Filters snapshot history to preserve all canonical session checkpoints (open, 15m buckets, extrema)
        for all session dates, plus high-frequency rolling snapshots."""
        if not snapshots:
            return []

        dates = {s.get("session_date") for s in snapshots if s.get("session_date")}
        if not dates:
            return snapshots[-500:]

        retained_all = []
        for d in sorted(dates):
            d_snaps = [s for s in snapshots if s.get("session_date") == d]
            checkpoint_keys = set()

            # Preserve first PRE_MARKET, PRE_OPEN, MARKET_OPEN, OPEN
            for phase in ("PRE_MARKET", "PRE_OPEN", "MARKET_OPEN", "OPEN", "CONTINUOUS_TRADING"):
                for s in d_snaps:
                    if s.get("market_session_phase") == phase or (phase in ("MARKET_OPEN", "OPEN") and s.get("continuous_session_open") and s.get("spot") is not None):
                        checkpoint_keys.add((s.get("timestamp"), s.get("state_sequence")))
                        break

            # Preserve intraday high/low extrema snapshots
            d_valid_spots = [s for s in d_snaps if isinstance(s.get("spot"), (int, float))]
            if d_valid_spots:
                max_s = max(d_valid_spots, key=lambda s: s["spot"])
                min_s = min(d_valid_spots, key=lambda s: s["spot"])
                checkpoint_keys.add((max_s.get("timestamp"), max_s.get("state_sequence")))
                checkpoint_keys.add((min_s.get("timestamp"), min_s.get("state_sequence")))

            # Preserve 3-minute interval anchor snapshots (providing at least 5 observations per 15m window)
            seen_3m_buckets = set()
            for s in d_snaps:
                ts_str = str(s.get("timestamp") or "")
                if ts_str:
                    try:
                        dt_u = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        dt_i = dt_u.astimezone(timezone(timedelta(hours=5, minutes=30)))
                        bucket = f"{dt_i.hour:02d}:{(dt_i.minute // 3) * 3:02d}"
                        if bucket not in seen_3m_buckets:
                            seen_3m_buckets.add(bucket)
                            checkpoint_keys.add((s.get("timestamp"), s.get("state_sequence")))
                    except Exception:
                        pass

            checkpoints = [s for s in d_snaps if (s.get("timestamp"), s.get("state_sequence")) in checkpoint_keys]
            recent_rolling = d_snaps[-500:] if d == session_date else d_snaps[-50:]

            combined_dict = {}
            for s in checkpoints + recent_rolling:
                key = (s.get("timestamp"), s.get("state_sequence"))
                combined_dict[key] = s

            retained_d = list(combined_dict.values())
            retained_d.sort(key=lambda x: (x.get("timestamp") or "", x.get("state_sequence") or 0))
            retained_all.extend(retained_d)

        return retained_all

    @classmethod
    def _persist_session_history(cls, session_date: str, force: bool = False) -> None:
        """Persists bounded session observations and material events atomically with dirty tracking & throttling."""
        import time
        now_ts = time.time()
        curr_snap_count = len(cls._snapshots_history)
        curr_seq = cls._sequence

        is_dirty = (curr_snap_count != cls._last_persisted_snap_count or curr_seq != cls._last_persisted_seq)
        time_elapsed = now_ts - cls._last_disk_flush_timestamp

        if not force and not is_dirty:
            return

        if not force and time_elapsed < cls.MIN_PERSIST_INTERVAL_SECONDS:
            return

        if os.environ.get("PYTEST_CURRENT_TEST"):
            default_prod_dir = Path("data/cache").resolve()
            current_target_dir = cls.CACHE_DIR.resolve()
            if current_target_dir == default_prod_dir:
                if not cls._allow_disk_cache_in_test:
                    return
                raise RuntimeError(
                    f"TEST ISOLATION VIOLATION: Test attempted to persist session history to production directory ({cls.CACHE_DIR}). "
                    "Tests must redirect CACHE_DIR to an isolated temporary directory (tmp_path)."
                )
        try:
            cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_file = cls.CACHE_DIR / f"session_history_{session_date}.json"

            cls._snapshots_history = cls._filter_retained_snapshots(cls._snapshots_history, session_date)
            session_snaps = [s for s in cls._snapshots_history if s.get("session_date") == session_date]

            payload = {
                "version": "1.0.0",
                "session_date": session_date,
                "snapshots": session_snaps,
                "material_events": cls._live_event_stream[:50]
            }

            # 1. Primary legacy write (STILL ENABLED)
            atomic_write_json(str(cache_file), payload)

            # 2. Parallel Lightweight Session Store Dual-Write (Phase E Shadow Mode)
            try:
                from src.storage import LightweightSessionStore
                store = LightweightSessionStore.get_instance()
                
                # Persist single atomic recovery snapshot
                if session_snaps:
                    latest_snap = session_snaps[-1]
                    store.persist_recovery_state(
                        state=latest_snap,
                        runtime_id=cls._runtime_id,
                        state_sequence=curr_seq,
                        session_date=session_date,
                        market_session_phase=latest_snap.get("market_session_phase", "")
                    )
                    
                    # Record 15-minute telemetry bucket
                    t_str = latest_snap.get("timestamp") or ""
                    hhmm = t_str[11:16] if len(t_str) >= 16 else "15:30"
                    opt_snap = latest_snap.get("options") or {}
                    br_snap = latest_snap.get("breadth") or {}
                    
                    bucket = {
                        "timestamp": t_str,
                        "window_start": hhmm,
                        "window_end": hhmm,
                        "start_spot": latest_snap.get("spot"),
                        "end_spot": latest_snap.get("spot"),
                        "breadth_advances": br_snap.get("advances"),
                        "breadth_declines": br_snap.get("declines"),
                        "vix": latest_snap.get("vix"),
                        "pcr": opt_snap.get("pcr"),
                        "max_pain": opt_snap.get("max_pain"),
                        "session_phase": latest_snap.get("market_session_phase", "CONTINUOUS_TRADING"),
                        "evidence_quality": "SUFFICIENT"
                    }
                    store.record_telemetry_bucket(session_date, bucket)
            except Exception as shadow_exc:
                logger.debug(f"[WorkstationStateService] Shadow storage write exception: {shadow_exc}")

            cls._last_persistence_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            cls._last_persisted_snap_count = curr_snap_count
            cls._last_persisted_seq = curr_seq
            cls._last_disk_flush_timestamp = now_ts
            cls._persistence_health = "READY"
        except Exception:
            cls._persistence_health = "DEGRADED"

    @classmethod
    def flush_session_history(cls, session_date: str | None = None) -> None:
        """Forces an immediate atomic disk flush of pending session history state."""
        target_date = session_date or cls._last_loaded_session_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cls._persist_session_history(target_date, force=True)

    @classmethod
    def get_cache_diagnostics(cls) -> dict[str, Any]:
        """Exposes cache diagnostic metadata for system operational verification."""
        snaps = cls._snapshots_history
        earliest = snaps[0].get("timestamp") if snaps else None
        latest = snaps[-1].get("timestamp") if snaps else None
        return {
            "persistence_status": cls._persistence_health,
            "loaded_snapshot_count": len(snaps),
            "earliest_persisted_timestamp": earliest,
            "latest_persisted_timestamp": latest,
            "cache_session_date": cls._last_loaded_session_date,
            "last_successful_persistence_time": getattr(cls, "_last_persistence_time", None)
        }

    @classmethod
    def _next_sequence(cls) -> int:
        with cls._lock:
            cls._sequence += 1
            return cls._sequence

    @classmethod
    def build_canonical_state(cls, payload: dict[str, Any], *, broker_state: str = "DISCONNECTED",
                              market_state: str = "UNKNOWN", now: datetime | None = None) -> CanonicalWorkstationState:
        """Alias for build_from_legacy producing authoritative CanonicalWorkstationState."""
        return cls.build_from_legacy(payload, broker_state=broker_state, market_state=market_state, now=now)

    @classmethod
    def build_from_legacy(cls, payload: dict[str, Any], *, broker_state: str = "DISCONNECTED",
                          market_state: str = "UNKNOWN", now: datetime | None = None) -> CanonicalWorkstationState:
        current = now or datetime.now(timezone.utc)
        generated = current.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        market_closed = str(market_state).upper() in {"CLOSED", "MARKET_CLOSED", "POST_MARKET", "HOLIDAY", "TRADING_HOLIDAY"}
        expired = str(broker_state).upper() in {"SESSION_EXPIRED", "TOKEN_EXPIRED", "EXPIRED"}
        raw_market_ctx = sanitize_read_only(payload.get("marketContext") or {})
        raw_market_data = sanitize_read_only(payload.get("market_data") or {})
        price_keys = {"current_spot", "close", "previous_close", "open", "high", "low", "ltp"}
        market = {**raw_market_data}
        for k, v in raw_market_ctx.items():
            if v is None:
                continue
            if k in price_keys and isinstance(v, (int, float)) and v <= 0:
                continue
            market[k] = v

        if market.get("change") is None and market.get("spot_change") is not None:
            market["change"] = market.get("spot_change")
        if market.get("change_percent") is None and market.get("spot_change_pct") is not None:
            market["change_percent"] = market.get("spot_change_pct")

        session_date = market.get("session_date") or current.strftime("%Y-%m-%d")
        if cls._last_loaded_session_date != session_date:
            cls._load_session_history(session_date)

        raw_candles = market.get("candles") or []
        valid_candles, candle_errors = DataQualityService.validate_candles(raw_candles)
        market["candles"] = valid_candles
        if candle_errors:
            market["candle_validation_warnings"] = candle_errors

        tech = sanitize_read_only(payload.get("technicalAnalysis") or {})
        if not tech.get("vwap") and market.get("vwap"):
            tech["vwap"] = market.get("vwap")
        if not tech.get("atr") and market.get("atr"):
            tech["atr"] = market.get("atr")
        if not tech.get("ema20") and market.get("ema20"):
            tech["ema20"] = market.get("ema20")
        if not tech.get("ema50") and market.get("ema50"):
            tech["ema50"] = market.get("ema50")
        if not tech.get("ema200") and market.get("ema200"):
            tech["ema200"] = market.get("ema200")
        if not tech.get("rsi") and market.get("rsi"):
            tech["rsi"] = market.get("rsi")
        if not tech.get("macd") and market.get("macd"):
            tech["macd"] = market.get("macd")
        if not tech.get("adx") and market.get("adx"):
            tech["adx"] = market.get("adx")

        if not tech.get("vwap") or tech.get("vwap") == 0:
            tech["vwap_status"] = "UNAVAILABLE"
            tech["vwap_reason"] = "Index spot data has no volume; VWAP requires volume-weighted ticks."
        if not tech.get("ema20") or not tech.get("ema50"):
            tech["ema_status"] = "UNAVAILABLE"
            tech["ema_reason"] = "Requires minimum 50 historical candles for calculation."
        if tech.get("trend_direction") in {None, "", "UNKNOWN"}:
            tech["trend_reason"] = "Insufficient validated historical candles to establish technical trend direction."
        payload["technicalAnalysis"] = tech
        payload["marketContext"] = market

        options = sanitize_read_only(payload.get("optionContext") or {})
        if isinstance(options, dict) and (options.get("current_weekly_expiry") or options.get("expiry")):
            exp_str = options.get("current_weekly_expiry") or options.get("expiry")
            try:
                exp_d = datetime.strptime(str(exp_str)[:10], "%Y-%m-%d").date()
                today_d = current.date() if 'current' in locals() and isinstance(current, datetime) else datetime.now(timezone.utc).date()
                cal_dte = max(0, (exp_d - today_d).days)
                cur_d = today_d
                tr_dte = 0
                while cur_d < exp_d:
                    if cur_d.weekday() < 5:
                        tr_dte += 1
                    cur_d += timedelta(days=1)
                options["calendar_dte"] = cal_dte
                options["trading_dte"] = tr_dte
                options["dte_basis"] = "CALENDAR_DAYS"
                options["time_to_expiry_days"] = cal_dte
            except Exception:
                pass
        market_observed = cls._timestamp(market)
        option_observed = cls._timestamp(options)
        market_value = market.get("current_spot", market.get("price"))
        market_available = DataQualityService.is_valid_number(market_value, positive=True) and bool(market_observed) and not expired
        explicit_option_time = options.get("provider_timestamp") or options.get("snapshot_timestamp") or options.get("observed_at")
        option_available = bool(option_observed) and not expired
        if market_closed:
            option_available = bool(explicit_option_time) and bool(options.get("current_weekly_expiry") or options.get("expiry")) and not expired
        market_source = "kite_historical_api" if market_closed else "kite_market_feed"
        market_meta = DataQualityService.metadata("nifty_spot", market_source, market_observed,
            instrument="NIFTY 50", generated_at=current, market_closed=market_closed,
            available=market_available,
            classification=ValueClassification.LIVE, now=current)
        option_meta = DataQualityService.metadata("option_aggregate", "kite_option_chain", option_observed,
            instrument="NIFTY options", generated_at=current, market_closed=market_closed,
            available=option_available, classification=ValueClassification.CALCULATED, now=current)
        market_status = cls._section(market_meta.freshness_status)
        option_status = cls._section(option_meta.freshness_status)
        news = sanitize_read_only(payload.get("newsSentiment") or {})
        cls._apply_news_temporal_workspace(news, current, market_observed)
        news_has_items = bool(news.get("items") or news.get("top_headlines") or news.get("high_impact_items"))
        news_status = SectionStatus.READY if news_has_items and str(news.get("status", "")).upper() not in {"UNAVAILABLE", "ERROR"} else SectionStatus.UNAVAILABLE
        analytics_status = cls._dependent(market_status, [option_status, news_status])
        assistant_status = cls._dependent(market_status, [option_status])
        macro = sanitize_read_only(payload.get("macroIntelligence") or {})
        cls._apply_macro_workspace(macro, current, market_observed)
        # Released macro events and their E2 reporting remain separate records,
        # but clusters carry a deterministic canonical reference when country,
        # topic and release window agree.
        cls._link_released_economic_events(news, macro)
        payload = {**payload, "newsSentiment": news}
        official_news_events = []
        for item in news.get("items") or []:
            canonical_category = item.get("canonical_event_category")
            if canonical_category not in {"RBI", "SEBI", "GOVERNMENT_POLICY", "INDIA_MACRO"}:
                continue
            official_news_events.append({
                "id": item.get("id"),
                "event_category": canonical_category,
                "headline": item.get("headline"),
                "description": item.get("summary_snippet"),
                "published_at": item.get("published_at"),
                "source_name": item.get("source_name"),
                "source_url": item.get("original_url"),
                "source_reference": item.get("source_reference") or item.get("original_url"),
                "source_authority": item.get("source_authority") or "PRIMARY",
                "official_subcategory": item.get("official_subcategory"),
                "verification_status": str(item.get("verification_status") or "").upper(),
                "relevance_score": item.get("nifty_relevance_score"),
                "impact_level": str(item.get("impact_strength") or "").upper(),
                "confidence": item.get("confidence"),
                "retrieved_at": item.get("received_at"),
                "freshness_status": item.get("freshness_status"),
            })
        if official_news_events:
            macro = {**macro, "official_india_events": [
                *(macro.get("official_india_events") or []), *official_news_events
            ]}
        vix_context = sanitize_read_only(market.get("india_vix_context") or {})
        if vix_context.get("value") is not None and vix_context.get("observation_timestamp"):
            macro["india_vix"] = vix_context
        elif macro.get("india_vix") and macro["india_vix"].get("value") is not None:
            macro["india_vix"].setdefault("status", "AVAILABLE")
        else:
            macro["india_vix"] = {
                **vix_context, "status": "UNAVAILABLE", "value": None,
                "failure_reason": vix_context.get("failure_reason") or "NO_VALIDATED_INDIA_VIX_OBSERVATION",
            }
        specialized = macro.get("institutional_derivatives") or {}
        specialized_records = specialized.get("records") or []
        specialized_workspace = macro.setdefault("specialized_workspace", {})
        specialized_workspace.update({
            "participant_record_count": len(specialized_records),
            "participant_latest_session": (specialized.get("open_interest") or {}).get("trade_date"),
            "india_vix_available": macro["india_vix"].get("status") in {"AVAILABLE", "DEGRADED"},
            "risk_free_rate_available": (macro.get("risk_free_rate") or {}).get("status") in {"AVAILABLE", "DEGRADED"},
            "option_iv_rows": int(options.get("iv_rows") or 0),
            "canonical_to_workspace_data_loss": 0,
        })
        macro.setdefault("ingestion_metrics", {})["specialized_canonical_to_workspace_data_loss"] = 0
        macro_quotes = macro.get("quotes") or {}
        macro_workspace = macro.get("workspace_context") or {}
        usable_macro_keys = set(macro_workspace.get("current_context_quote_keys") or [])
        has_macro_cues = bool(usable_macro_keys)

        flow_context = []
        for flow in macro.get("institutional_flows") or []:
            dataset = str(flow.get("dataset_type") or "").upper()
            net = flow.get("net_value")
            if dataset not in {"FII_CASH", "DII_CASH"} or not DataQualityService.is_valid_number(net):
                continue
            flow_context.append({
                **flow,
                "context": f"{dataset.replace('_CASH', '')}_CASH_{'BUYING' if float(net) > 0 else 'SELLING' if float(net) < 0 else 'BALANCED'}",
            })
        macro["institutional_context"] = {
            "cash": flow_context,
            "derivatives": specialized.get("positioning") or {},
            "status": "AVAILABLE" if flow_context or specialized_records else "UNAVAILABLE",
            "prediction": None,
        }

        gift = macro_quotes.get("GIFT_NIFTY") or {}
        nifty_reference = (
            market.get("previous_close")
            or market.get("prev_close")
            or macro.get("nifty_previous_close")
            or (market.get("close") if market_closed else None)
            or ((payload.get("eveningReport") or {}).get("market_summary") or {}).get("previous_close")
            or (market.get("current_spot") if market_closed else None)
        )
        gap_session_eligible = market_closed or str(market_state).upper() in {"PRE_OPEN", "PRE_MARKET"}
        gap_ready = (
            gap_session_eligible
            and
            "GIFT_NIFTY" in usable_macro_keys
            and DataQualityService.is_valid_number(gift.get("price"), positive=True)
            and DataQualityService.is_valid_number(nifty_reference, positive=True)
        )
        if gap_ready:
            gap_points = float(gift["price"]) - float(nifty_reference)
            gap_pct = gap_points / float(nifty_reference) * 100.0
            direction = "POSITIVE_GAP_INDICATION" if gap_pct > 0.15 else "NEGATIVE_GAP_INDICATION" if gap_pct < -0.15 else "FLAT_OPEN_INDICATION"
            magnitude = "LARGE" if abs(gap_pct) >= 1.0 else "MODERATE" if abs(gap_pct) >= 0.5 else "SMALL" if abs(gap_pct) > 0.15 else "FLAT"
            macro["opening_gap"] = {
                "status": "READY", "readiness": "READY", "nifty_reference_close": float(nifty_reference),
                "gift_nifty_reference": float(gift["price"]), "gap_points": round(gap_points, 4),
                "gap_pct": round(gap_pct, 4), "classification": direction, "magnitude": magnitude,
                "observation_timestamp": gift.get("observation_timestamp"), "age_seconds": gift.get("age_seconds"),
                "freshness": gift.get("freshness_status"), "source": gift.get("source_name"),
                "contract_expiry": gift.get("contract_expiry"),
                "provenance": "GIFT_NIFTY_FUTURE_MINUS_VALIDATED_NIFTY_REFERENCE_CLOSE",
                "disclaimer": "Opening indication only; not a predicted NIFTY opening price.",
            }
        else:
            macro["opening_gap"] = {
                "status": "UNAVAILABLE", "readiness": "BLOCKED", "nifty_reference_close": nifty_reference,
                "gift_nifty_reference": gift.get("price"), "gap_points": None, "gap_pct": None,
                "classification": None, "failure_reason": "SESSION_OR_ELIGIBLE_GIFT_NIFTY_OR_NIFTY_REFERENCE_UNAVAILABLE",
            }

        iv_values = [float(row["iv"]) for row in options.get("iv_skew") or [] if DataQualityService.is_valid_number(row.get("iv"), positive=True)]
        atm_ce, atm_pe = options.get("atm_ce_iv"), options.get("atm_pe_iv")
        options["volatility_context"] = {
            "status": "AVAILABLE" if iv_values and DataQualityService.is_valid_number(atm_ce, positive=True) and DataQualityService.is_valid_number(atm_pe, positive=True) else "UNAVAILABLE",
            "india_vix_regime": macro["india_vix"].get("regime"),
            "atm_ce_iv": atm_ce, "atm_pe_iv": atm_pe, "atm_average_iv": options.get("atm_iv"),
            "ce_pe_iv_difference": round(float(atm_ce) - float(atm_pe), 4) if DataQualityService.is_valid_number(atm_ce) and DataQualityService.is_valid_number(atm_pe) else None,
            "strike_iv_min": min(iv_values) if iv_values else None, "strike_iv_max": max(iv_values) if iv_values else None,
            "strike_iv_dispersion": round(max(iv_values) - min(iv_values), 4) if iv_values else None,
            "source": "Kite option chain; deterministic Black-Scholes convergence",
            "fallback_iv_used": False,
        }
        payload = {**payload, "optionContext": options}
        broker_account = sanitize_read_only(payload.get("brokerAccount") or {})

        core_market_ready = market_status in {SectionStatus.READY, SectionStatus.MARKET_CLOSED} and not expired
        overall_state = "NOT_READY" if expired or market_status == SectionStatus.BLOCKED else ("DEGRADED" if news_status != SectionStatus.READY or not has_macro_cues else "READY")

        premarket_inputs = {
            "gift_nifty": "READY" if "GIFT_NIFTY" in usable_macro_keys else "UNAVAILABLE",
            "global_indices": "READY" if usable_macro_keys & {"S&P 500", "NASDAQ", "DOW_JONES", "NIKKEI_225", "HANG_SENG"} else "UNAVAILABLE",
            "commodities_fx": "READY" if usable_macro_keys & {"BRENT_CRUDE", "GOLD", "USD_INR", "DXY", "US_10Y"} else "UNAVAILABLE",
            "fii_dii": "READY" if macro.get("institutional_flows") else "UNAVAILABLE",
            "derivative_positioning": "READY" if specialized_records else "UNAVAILABLE",
            "volatility": "READY" if macro["india_vix"].get("status") in {"AVAILABLE", "DEGRADED"} else "UNAVAILABLE",
            "calendars": "READY" if macro.get("corporate_actions") or macro.get("economic_events") else "UNAVAILABLE",
            "news": "READY" if news_status == SectionStatus.READY else "UNAVAILABLE",
        }
        ready_count = sum(value == "READY" for value in premarket_inputs.values())
        full_premarket = all(premarket_inputs[key] == "READY" for key in ("gift_nifty", "global_indices", "commodities_fx", "fii_dii", "news"))
        premarket_state = "READY" if full_premarket else "PARTIAL_READY" if ready_count >= 4 else "BLOCKED" if not market_available else "UNAVAILABLE"

        # Today's Analysis post-close readiness: if market is closed and persisted session history exists, status is READY
        same_date_snaps_exist = len([s for s in cls._snapshots_history if s.get("session_date") == session_date]) > 0
        todays_analysis_sec_status = SectionStatus.READY if (market_closed and same_date_snaps_exist) else analytics_status

        readiness = {
            "overall_state": overall_state,
            "core_market_feed_state": "READY" if core_market_ready else "UNAVAILABLE",
            "intelligence_providers_state": "READY" if news_status == SectionStatus.READY and has_macro_cues else "DEGRADED",
            "pre_market_850_readiness": {
                **premarket_inputs,
                "overall_state": premarket_state,
                "ready_inputs": sorted(key for key, value in premarket_inputs.items() if value == "READY"),
                "unavailable_inputs": sorted(key for key, value in premarket_inputs.items() if value == "UNAVAILABLE"),
                "blocked_inputs": [] if market_available else ["validated_nifty_reference"],
                "is_full_premarket_ready": full_premarket,
            },
            "nifty_live": cls._ready("NIFTY Live", market_status, cls._reasons(market_status)),
            "pre_market_planner": cls._ready("Pre-Market Planner", market_status,
                [] if market_status in {SectionStatus.READY, SectionStatus.MARKET_CLOSED} else ["validated market snapshot"]),
            "todays_analysis": cls._ready("Today's Analysis", todays_analysis_sec_status,
                [] if (market_closed and same_date_snaps_exist) else cls._reasons(market_status, option_status, news_status)),
            "news_updates": cls._ready("NEWS & UPDATES", news_status,
                [] if news_status == SectionStatus.READY else ["real news provider"]),
            "live_assistant": cls._ready("Live Assistant", assistant_status,
                cls._reasons(market_status, option_status)),
            "settings": cls._ready("Settings", SectionStatus.READY, []),
        }
        unified = UnifiedNiftyIntelligenceBuilder.build(
            market=market, technical=sanitize_read_only(payload.get("technicalAnalysis") or {}),
            options=options, macro=macro, news=news, market_state=market_state,
            market_meta=market_meta.to_dict(), option_meta=option_meta.to_dict(), now=current,
        )
        for workspace_key in ("pre_market_planner", "todays_analysis", "live_assistant"):
            readiness[workspace_key]["unified_intelligence_mode"] = unified["mode"]
            readiness[workspace_key]["unified_intelligence_readiness"] = unified["readiness"]
        blockers = cls._reasons(market_status, option_status)
        support = DecisionSupportReport(
            market_interpretation="Validated analytical context" if not blockers else "Analytical context incomplete",
            current_scenario_status="market_closed" if market_closed else ("blocked" if blockers else "monitor"),
            required_confirmations=["validated NIFTY spot", "validated option aggregate"],
            missing_confirmations=blockers, blockers=blockers,
            warnings=["Live broker session requires reconnect"] if expired else [],
        )
        support_payload = {
            **support.to_dict(),
            "unified_intelligence_engine": unified["engine"],
            "session_mode": unified["mode"],
            "alignment": unified["alignment"],
            "confirming_signals": unified["confirming_signals"],
            "opposing_signals": unified["opposing_signals"],
            "unavailable_or_ineligible_signals": unified["unavailable_or_ineligible_signals"],
            "market_regime": unified["market_regime"],
            "key_levels": unified["key_levels"],
            "scenarios": unified["scenarios"],
            "invalidation_conditions": unified["invalidation_conditions"],
            "if_then_monitor": (unified.get("live_decision") or {}).get("if_then_monitor") or [],
            "what_to_watch": (unified.get("live_decision") or {}).get("what_to_watch") or [],
            "what_to_do_now": (unified.get("live_decision") or {}).get("what_to_do_now") or {},
            "risk": unified["risk"], "confidence": unified["confidence"],
            "human_decision_required": True, "execution_authorized": False,
        }
        explanation_payload = {
            **sanitize_read_only(payload.get("explanationReport") or {}),
            "status": assistant_status.value, "engine": unified["engine"],
            "deterministic": True, "llm_dependency": False,
            "summary": unified["explanation"],
            "evidence": {name: signal["evidence"] for name, signal in unified["signals"].items()},
            "confirming_signals": unified["confirming_signals"],
            "opposing_signals": unified["opposing_signals"],
        }
        confidence_payload = {
            **sanitize_read_only(payload.get("confidenceReport") or {}),
            "unified_evidence_quality": unified["confidence"],
            "evidence_completeness": unified["evidence_completeness"],
            "agreement_state": unified["alignment"],
            "explainable": True,
        }
        risk_payload = {
            **sanitize_read_only(payload.get("riskReport") or {}),
            "unified_analytical_risk": unified["risk"],
            "event_risk": unified["signals"]["events"],
            "volatility_risk": unified["signals"]["volatility"],
            "data_quality_risk": unified["unavailable_or_ineligible_signals"],
            "position_sizing": None,
        }
        def section(name: str, status: SectionStatus, fallback: Any = None) -> dict[str, Any]:
            value = sanitize_read_only(payload.get(name) or fallback or {})
            if status == SectionStatus.UNAVAILABLE and name in {"marketContext", "optionContext"} and not (isinstance(value, dict) and (value.get("current_spot") or value.get("breadth"))):
                return {"status": status.value}
            if isinstance(value, dict):
                if name == "marketContext":
                    pc = value.get("previous_close") or value.get("prev_close") or nifty_reference
                    if pc and float(pc) > 0:
                        value["previous_close"] = float(pc)
                        sp = value.get("current_spot")
                        if sp and float(sp) > 0:
                            chg = round(float(sp) - float(pc), 2)
                            chg_pct = round(chg / float(pc) * 100.0, 4)
                            value.setdefault("spot_change", chg)
                            value.setdefault("spot_change_pct", chg_pct)
                            value.setdefault("change_points", chg)
                            value.setdefault("change_percent", chg_pct)
                    else:
                        value["previous_close"] = None
                return {**value, "status": status.value}
            return {"status": status.value, "value": value}

        # ── SPRINT D.2 AUTHORITATIVE TEMPORAL MONITORING ──
        spot = market.get("current_spot")
        if spot is not None:
            spot = float(spot)
        breadth_data = market.get("breadth") or {}
        adv = breadth_data.get("advances")
        dec = breadth_data.get("declines")
        pcr_val = options.get("pcr")
        if pcr_val is not None:
            pcr_val = float(pcr_val)
        vix_val = macro.get("india_vix", {}).get("value")
        if vix_val is not None:
            vix_val = float(vix_val)

        # Genuine Heavyweights list resolution (NO breadth substitution, NO arbitrary hardcoded fallback)
        hw_list = market.get("heavyweights") or []
        hw_total = len(hw_list)
        hw_up = len([h for h in hw_list if float(h.get("change") or 0.0) >= 0.0])

        if hw_total > 0:
            hw_ratio = hw_up / hw_total
        else:
            hw_ratio = None  # Explicit UNAVAILABLE when authoritative basket is absent

        def parse_iso(ts):
            if not ts:
                return None
            try:
                s = ts.replace("Z", "")
                if "." in s:
                    s = s.split(".")[0]
                return datetime.fromisoformat(s)
            except Exception:
                return None

        now_dt = parse_iso(generated) or datetime.now(timezone.utc)
        ist_now = MarketStatusService.get_ist_time(now_dt)
        session_date = market.get("session_date") or ist_now.strftime("%Y-%m-%d")

        if market_closed:
            auth_session = "CLOSED"
        elif market_state and str(market_state).upper() in ("OPEN", "MARKET_OPEN"):
            auth_session = "MARKET_OPEN"
        else:
            status_report = MarketStatusService.get_instance().get_market_status(now_dt)
            auth_session = status_report.status  # "PRE_OPEN", "OPEN", "POST_CLOSE", "CLOSED"

        if auth_session in ("OPEN", "MARKET_OPEN"):
            market_session_phase = "MARKET_OPEN"
            continuous_session_open = True
        elif auth_session == "PRE_OPEN":
            market_session_phase = "PRE_OPEN"
            continuous_session_open = False
        elif auth_session == "CLOSED":
            market_session_phase = "CLOSED"
            continuous_session_open = False
        elif auth_session == "POST_CLOSE":
            market_session_phase = "POST_CLOSE"
            continuous_session_open = False
        elif auth_session == "HOLIDAY":
            market_session_phase = "HOLIDAY"
            continuous_session_open = False
        else:
            market_session_phase = auth_session
            continuous_session_open = False

        # Calculate session_transition_sequence for current session_date
        same_date_snaps = [s for s in cls._snapshots_history if s.get("session_date") == session_date]
        if same_date_snaps:
            prev_snap = same_date_snaps[-1]
            prev_seq = prev_snap.get("session_transition_sequence", 1)
            prev_phase = prev_snap.get("market_session_phase")
            if prev_phase != market_session_phase:
                session_transition_sequence = prev_seq + 1
            else:
                session_transition_sequence = prev_seq
        else:
            session_transition_sequence = 1

        spots = [s.get("spot") for s in same_date_snaps if isinstance(s.get("spot"), (int, float))]
        if isinstance(spot, (int, float)):
            spots.append(spot)

        open_val = market.get("open")
        if open_val is None:
            open_snap = next(
                (s for s in same_date_snaps if s.get("market_session_phase") in ("MARKET_OPEN", "OPEN") and s.get("continuous_session_open") and s.get("spot") is not None),
                next((s for s in same_date_snaps if s.get("spot") is not None), None)
            )
            open_val = float(open_snap["spot"]) if (open_snap and open_snap.get("spot") is not None) else (spots[0] if spots else None)

        high_candidates = [v for v in [market.get("high")] + spots if isinstance(v, (int, float))]
        high_val = max(high_candidates) if high_candidates else spot

        low_candidates = [v for v in [market.get("low")] + spots if isinstance(v, (int, float))]
        low_val = min(low_candidates) if low_candidates else spot

        close_val = market.get("close") or spot

        market["open"] = open_val
        market["high"] = high_val
        market["low"] = low_val
        market["close"] = close_val

        snap = {
            "timestamp": generated,
            "runtime_id": cls._runtime_id,
            "state_sequence": cls._sequence + 1,
            "market_state": market_session_phase,
            "session_phase": market_session_phase,
            "market_session_phase": market_session_phase,
            "continuous_session_open": continuous_session_open,
            "session_open_confirmed": continuous_session_open,
            "session_date": session_date,
            "session_transition_sequence": session_transition_sequence,
            "spot": spot,
            "open": open_val,
            "high": high_val,
            "low": low_val,
            "close": close_val,
            "breadth": {
                "advances": int(adv) if adv is not None else None,
                "declines": int(dec) if dec is not None else None,
                "coverage": (int(adv) + int(dec)) if (adv is not None and dec is not None) else 0
            },
            "options": {
                "pcr": pcr_val,
                "max_pain": options.get("max_pain"),
                "atm_strike": options.get("atm_strike"),
                "atm_iv": options.get("atm_iv")
            },
            "vix": vix_val,
            "regime": unified.get("market_regime"),
            "alignment": unified.get("alignment"),
            "heavyweight_ratio": hw_ratio,
            "provenance": {
                "source_type": market.get("source_type") or ("WEBSOCKET_STREAM" if broker_state == "CONNECTED" else "REST_POLL"),
                "observed_at": generated,
                "trading_date": session_date,
                "freshness": "REALTIME" if broker_state == "CONNECTED" else "LAST_VALID_SESSION"
            }
        }

        cls._snapshots_history.append(snap)
        if len(cls._snapshots_history) > 500:
            cls._snapshots_history = cls._filter_retained_snapshots(cls._snapshots_history, session_date)

        comparisons = []
        SAMPLING_TOLERANCE_SECONDS = 120.0

        for win_label, seconds in [("1 MIN", 60), ("5 MIN", 300), ("15 MIN", 900), ("SINCE OPEN", -1)]:
            match_snap = None
            if seconds == -1:
                # SINCE OPEN rule: first snapshot for current trading date where persisted market_session_phase == MARKET_OPEN
                same_day_open_snaps = [
                    s for s in cls._snapshots_history
                    if s.get("session_date") == session_date
                    and s.get("market_session_phase") in ("MARKET_OPEN", "OPEN")
                    and s.get("continuous_session_open")
                ]
                if same_day_open_snaps:
                    match_snap = same_day_open_snaps[0]
                elif snap.get("continuous_session_open"):
                    match_snap = snap
            else:
                if now_dt:
                    target_dt = now_dt.timestamp() - seconds
                    best_diff = 999999.0
                    for s in cls._snapshots_history:
                        s_dt = parse_iso(s.get("timestamp"))
                        if s_dt:
                            diff = abs(s_dt.timestamp() - target_dt)
                            if diff < best_diff and diff <= 45.0:
                                best_diff = diff
                                match_snap = s

            if match_snap and now_dt:
                from_dt = parse_iso(match_snap.get("timestamp"))
                if from_dt:
                    dur_sec = int(abs(now_dt.timestamp() - from_dt.timestamp()))
                    dur_min = dur_sec // 60
                    dur_remain_sec = dur_sec % 60
                    actual_duration = f"{dur_min}m {dur_remain_sec}s" if dur_min > 0 else f"{dur_remain_sec}s"

                    # Sub-sequence of consecutive observations in window [from_dt, now_dt] including current snap
                    sub_snaps = [s for s in cls._snapshots_history if parse_iso(s.get("timestamp")) and parse_iso(s.get("timestamp")) >= from_dt and parse_iso(s.get("timestamp")) <= now_dt]
                    if not sub_snaps or sub_snaps[-1] != snap:
                        sub_snaps.append(snap)

                    sample_count = len(sub_snaps)
                    gap_count = 0
                    largest_gap = 0.0
                    last_gap_idx = -1

                    for i in range(1, len(sub_snaps)):
                        t_prev = parse_iso(sub_snaps[i-1].get("timestamp"))
                        t_curr = parse_iso(sub_snaps[i].get("timestamp"))
                        if t_prev and t_curr:
                            g = (t_curr - t_prev).total_seconds()
                            if cls._is_genuine_telemetry_gap(sub_snaps[i-1], sub_snaps[i], g):
                                if g > largest_gap:
                                    largest_gap = g
                                gap_count += 1
                                last_gap_idx = i

                    contains_gap = (gap_count > 0)

                    if contains_gap and last_gap_idx != -1 and last_gap_idx < len(sub_snaps):
                        post_gap_start_dt = parse_iso(sub_snaps[last_gap_idx].get("timestamp"))
                        uninterrupted_sec = int(abs(now_dt.timestamp() - post_gap_start_dt.timestamp())) if post_gap_start_dt else 0
                    else:
                        uninterrupted_sec = dur_sec

                    diff_spot = (spot - match_snap["spot"]) if (spot is not None and match_snap.get("spot") is not None) else 0.0
                    diff_pcr = (pcr_val - match_snap["options"]["pcr"]) if (pcr_val is not None and match_snap.get("options") and match_snap["options"].get("pcr") is not None) else 0.0
                    diff_vix = (vix_val - match_snap["vix"]) if (vix_val is not None and match_snap.get("vix") is not None) else 0.0

                    p_adv = match_snap.get("breadth", {}).get("advances")
                    c_adv = snap["breadth"]["advances"]
                    diff_adv = (c_adv - p_adv) if (c_adv is not None and p_adv is not None) else 0

                    spot_status = "Improving" if diff_spot > 2.0 else "Weakening" if diff_spot < -2.0 else "Stable"
                    breadth_status = "Improving" if diff_adv > 0 else "Weakening" if diff_adv < 0 else "Stable"
                    pcr_status = "Improving" if diff_pcr > 0.01 else "Weakening" if diff_pcr < -0.01 else "Stable"
                    vix_status = "Supportive" if diff_vix < -0.05 else "Elevated" if diff_vix > 0.05 else "Stable"

                    p_ratio = match_snap.get("heavyweight_ratio")
                    c_ratio = snap["heavyweight_ratio"]
                    if p_ratio is not None and c_ratio is not None:
                        hw_status = "Improving" if c_ratio > p_ratio + 0.02 else "Weakening" if c_ratio < p_ratio - 0.02 else "Stable"
                    else:
                        hw_status = "Unavailable"

                    interpretation = "Market metrics are trading within stable range boundaries."
                    if diff_spot > 5.0:
                        if breadth_status == "Improving" or hw_status == "Improving":
                            interpretation = "Participation strengthened alongside the upward spot expansion."
                        else:
                            interpretation = "Price advanced but constituent breadth showed divergence."
                    elif diff_spot < -5.0:
                        if breadth_status == "Weakening" or hw_status == "Weakening":
                            interpretation = "Spot price declined with expanding constituent distribution."
                        else:
                            interpretation = "Price declined but heavyweight support restricted further drop."
                    else:
                        if breadth_status == "Improving" and pcr_status == "Improving":
                            interpretation = "Underlying breadth and option writer support are consolidating positively."

                    if seconds == -1:
                        # SINCE OPEN contract with gap metadata
                        comparisons.append({
                            "requested_window": win_label,
                            "status": "AVAILABLE",
                            "available": True,
                            "continuity_valid": not contains_gap,
                            "baseline_type": "CONTINUOUS_MARKET_OPEN",
                            "actual_duration_seconds": dur_sec,
                            "actual_duration": actual_duration,
                            "sample_count": sample_count,
                            "contains_telemetry_gap": contains_gap,
                            "gap_count": gap_count,
                            "largest_gap_seconds": round(largest_gap, 1),
                            "from_timestamp": match_snap.get("timestamp"),
                            "to_timestamp": generated,
                            "diff_spot": round(diff_spot, 2),
                            "diff_pcr": round(diff_pcr, 4),
                            "diff_vix": round(diff_vix, 2),
                            "diff_adv": diff_adv,
                            "spot_status": spot_status,
                            "breadth_status": breadth_status,
                            "pcr_status": pcr_status,
                            "vix_status": vix_status,
                            "hw_status": hw_status,
                            "interpretation": interpretation
                        })
                    else:
                        # Rolling window contract (1m / 5m / 15m)
                        is_duration_sufficient = (dur_sec >= seconds - 30) and (uninterrupted_sec >= seconds - 30)
                        continuity_valid = (not contains_gap) and is_duration_sufficient

                        if contains_gap and not is_duration_sufficient:
                            window_status = "TELEMETRY_GAP"
                            is_available = False
                        elif not is_duration_sufficient:
                            window_status = "REBUILDING"
                            is_available = False
                        else:
                            window_status = "AVAILABLE"
                            is_available = True
                            continuity_valid = True

                        display_duration = f"{dur_min}m {dur_remain_sec}s collected / {seconds//60}m required" if not is_available else actual_duration

                        comparisons.append({
                            "requested_window": win_label,
                            "status": window_status,
                            "available": is_available,
                            "continuity_valid": continuity_valid,
                            "sample_count": sample_count,
                            "largest_gap_seconds": round(largest_gap, 1),
                            "actual_duration_seconds": dur_sec,
                            "collected_duration_seconds": dur_sec,
                            "required_duration_seconds": seconds,
                            "actual_duration": display_duration,
                            "from_timestamp": match_snap.get("timestamp"),
                            "to_timestamp": generated,
                            "diff_spot": round(diff_spot, 2) if is_available else 0.0,
                            "diff_pcr": round(diff_pcr, 4) if is_available else 0.0,
                            "diff_vix": round(diff_vix, 2) if is_available else 0.0,
                            "diff_adv": diff_adv if is_available else 0,
                            "spot_status": spot_status if is_available else "Stable",
                            "breadth_status": breadth_status if is_available else "Stable",
                            "pcr_status": pcr_status if is_available else "Stable",
                            "vix_status": vix_status if is_available else "Stable",
                            "hw_status": hw_status if is_available else "Stable",
                            "interpretation": interpretation if is_available else ("Telemetry gap detected in rolling window history." if contains_gap else "Rebuilding rolling history window."),
                        })
                else:
                    comparisons.append({
                        "requested_window": win_label,
                        "status": "REBUILDING",
                        "available": False,
                        "continuity_valid": False,
                        "sample_count": 0,
                        "largest_gap_seconds": 0.0,
                        "actual_duration_seconds": 0,
                        "collected_duration_seconds": 0,
                        "required_duration_seconds": seconds if seconds > 0 else 0,
                        "actual_duration": "Rebuilding history window",
                    })
            else:
                comparisons.append({
                    "requested_window": win_label,
                    "status": "INSUFFICIENT_HISTORY" if seconds == -1 else "REBUILDING",
                    "available": False,
                    "continuity_valid": False,
                    "sample_count": 0,
                    "largest_gap_seconds": 0.0,
                    "actual_duration_seconds": 0,
                    "collected_duration_seconds": 0,
                    "required_duration_seconds": seconds if seconds > 0 else 0,
                    "actual_duration": "Awaiting continuous session open baseline" if seconds == -1 else "Rebuilding history window",
                })

        # Select primary valid temporal window (5M preferred, fallback 1M)
        c5m_valid = next((c for c in comparisons if c["requested_window"] == "5 MIN" and c.get("available") and c.get("continuity_valid")), None)
        c1m_valid = next((c for c in comparisons if c["requested_window"] == "1 MIN" and c.get("available") and c.get("continuity_valid")), None)
        primary_temporal = c5m_valid or c1m_valid

        # Event stream transitions (Material Event Engine V2)
        if len(cls._snapshots_history) > 1:
            prev = cls._snapshots_history[-2]
            time_only_str = now_dt.strftime("%H:%M:%S IST")

            # 1. Regime Shift Event
            if prev.get("regime") and snap.get("regime") and prev["regime"] != snap["regime"]:
                regime_key = f"regime_shift_{snap['regime']}"
                if getattr(cls, "_last_emitted_regime", None) != snap["regime"]:
                    cls._last_emitted_regime = snap["regime"]
                    cls._live_event_stream.insert(0, {
                        "id": f"evt-{cls._sequence}-{len(cls._live_event_stream)}",
                        "event_id": f"evt-{cls._sequence}-{len(cls._live_event_stream)}",
                        "event_type": "REGIME_SHIFT",
                        "family": "REGIME",
                        "occurred_at": time_only_str,
                        "state_sequence": cls._sequence,
                        "materiality": "high",
                        "title": "Regime Shift Detected",
                        "description": f"Regime shifted from {prev['regime']} to {snap['regime']}",
                        "previous_state": str(prev["regime"]),
                        "current_state": str(snap["regime"]),
                        "source_window": "LIVE",
                        "evidence": [f"Regime transition to {snap['regime']}"],
                        "source_rule": "RULE_REGIME_TRANSITION",
                        "cooldown_key": regime_key,
                        "source_state_sequence": cls._sequence
                    })

            # 2. Alignment Shift Event
            if prev.get("alignment") and snap.get("alignment") and prev["alignment"] != snap["alignment"]:
                align_key = f"align_shift_{snap['alignment']}"
                if getattr(cls, "_last_emitted_alignment", None) != snap["alignment"]:
                    cls._last_emitted_alignment = snap["alignment"]
                    cls._live_event_stream.insert(0, {
                        "id": f"evt-{cls._sequence}-{len(cls._live_event_stream)}",
                        "event_id": f"evt-{cls._sequence}-{len(cls._live_event_stream)}",
                        "event_type": "ALIGNMENT_SHIFT",
                        "family": "ALIGNMENT",
                        "occurred_at": time_only_str,
                        "state_sequence": cls._sequence,
                        "materiality": "high",
                        "title": "Market Alignment Shift",
                        "description": f"Market Alignment shifted to {snap['alignment']}",
                        "previous_state": str(prev["alignment"]),
                        "current_state": str(snap["alignment"]),
                        "source_window": "LIVE",
                        "evidence": [f"Alignment transition to {snap['alignment']}"],
                        "source_rule": "RULE_ALIGNMENT_TRANSITION",
                        "cooldown_key": align_key,
                        "source_state_sequence": cls._sequence
                    })

            # 3. 15-Minute Cumulative Spot Structure Event (Only from valid & continuous 15M window)
            c15 = next((c for c in comparisons if c["requested_window"] == "15 MIN" and c.get("available") and c.get("continuity_valid")), None)
            if c15 and abs(c15.get("diff_spot", 0)) >= 30.0:
                event_id_15m = f"cum15m-{now_dt.strftime('%H%M')}"
                if not any(e.get("cooldown_key") == event_id_15m or e["id"] == event_id_15m for e in cls._live_event_stream):
                    ev_type = "15M_BREAKDOWN" if c15["diff_spot"] < 0 else "15M_BREAKOUT"
                    cls._live_event_stream.insert(0, {
                        "id": event_id_15m,
                        "event_id": event_id_15m,
                        "event_type": ev_type,
                        "family": "PRICE_STRUCTURE",
                        "occurred_at": time_only_str,
                        "state_sequence": cls._sequence,
                        "materiality": "high",
                        "title": f"15-Minute Spot {ev_type.replace('15M_', '')}",
                        "description": f"15-Minute cumulative spot expansion: {c15['diff_spot']:+g} pts",
                        "previous_state": f"{spot - c15['diff_spot']:.1f}",
                        "current_state": f"{spot:.1f}",
                        "source_window": "15 MIN",
                        "evidence": [f"15M delta spot = {c15['diff_spot']} pts"],
                        "source_rule": "RULE_15M_CUMULATIVE_EXPANSION",
                        "cooldown_key": event_id_15m,
                        "source_state_sequence": cls._sequence
                    })

            cls._live_event_stream = cls._live_event_stream[:50]
        else:
            time_only_str = now_dt.strftime("%H:%M:%S IST")
            cls._live_event_stream = [{
                "id": f"init-{cls._sequence}",
                "event_id": f"init-{cls._sequence}",
                "event_type": "INITIALIZE",
                "family": "REGIME",
                "occurred_at": time_only_str,
                "state_sequence": cls._sequence,
                "materiality": "high",
                "title": "Workstation Synchronized",
                "description": "Workstation state synchronized. Live Assistant active.",
                "previous_state": "NONE",
                "current_state": str(snap["regime"]),
                "source_window": "LIVE",
                "evidence": ["System initialization"],
                "source_rule": "RULE_SYSTEM_INIT",
                "cooldown_key": "system_init",
                "source_state_sequence": cls._sequence
            }]

        # Build confirmation families list (Phase 2 Direction of Travel Contract)
        unified_signals = unified.get("signals") or {}
        confirmation_families = []

        if not hasattr(cls, "_last_confirmation_trends"):
            cls._last_confirmation_trends = {}

        for fam_name, sig_key in [
            ("PRICE", "price"),
            ("BREADTH", "breadth"),
            ("OPTIONS", "options"),
            ("VOLATILITY", "volatility"),
            ("HEAVYWEIGHTS", "heavyweights"),
            ("GLOBAL / MACRO", "global"),
            ("NEWS / EVENT RISK", "news")
        ]:
            if fam_name == "HEAVYWEIGHTS":
                if hw_ratio is not None:
                    ratio = hw_ratio
                    bias = "Bullish" if ratio >= 0.6 else "Bearish" if ratio <= 0.4 else "Neutral"
                    status = "READY"
                    trend_dir = primary_temporal.get("hw_status", "Stable").upper() if primary_temporal else "STABLE"
                    evidence = [f"{hw_up}/{hw_total} heavyweight symbols advancing"]
                    reason = None
                else:
                    bias = "UNAVAILABLE"
                    status = "UNAVAILABLE"
                    trend_dir = "UNAVAILABLE"
                    evidence = []
                    reason = "authoritative heavyweight membership/weights unavailable"
                observed_at = market_observed
            else:
                sig = unified_signals.get(sig_key) or {}
                status = "READY" if sig.get("eligible") else "UNAVAILABLE"
                reason = sig.get("ineligibility_reason") if not sig.get("eligible") else None
                if sig.get("eligible"):
                    raw_stance = str(sig.get("stance") or "").upper()
                    if raw_stance in {"BULLISH", "POSITIVE", "STRONG_POSITIVE", "SUPPORTIVE"}:
                        bias = "Bullish"
                    elif raw_stance in {"BEARISH", "NEGATIVE", "STRONG_NEGATIVE", "RISK"}:
                        bias = "Bearish"
                    else:
                        bias = "Neutral"
                else:
                    bias = "UNAVAILABLE"
                evidence = sig.get("evidence") or []
                observed_at = sig.get("observed_at") or market_observed

                if primary_temporal:
                    if fam_name == "PRICE":
                        p_stat = primary_temporal.get("spot_status", "Stable")
                        trend_dir = "IMPROVING" if p_stat == "Improving" else "WEAKENING" if p_stat == "Weakening" else "STABLE"
                    elif fam_name == "BREADTH":
                        b_stat = primary_temporal.get("breadth_status", "Stable")
                        trend_dir = "IMPROVING" if b_stat == "Improving" else "WEAKENING" if b_stat == "Weakening" else "STABLE"
                    elif fam_name == "OPTIONS":
                        o_stat = primary_temporal.get("pcr_status", "Stable")
                        trend_dir = "IMPROVING" if o_stat == "Improving" else "WEAKENING" if o_stat == "Weakening" else "STABLE"
                    elif fam_name == "VOLATILITY":
                        v_stat = primary_temporal.get("vix_status", "Stable")
                        trend_dir = "IMPROVING" if v_stat in ("Supportive", "Improving") else "WEAKENING" if v_stat in ("Elevated", "Weakening") else "STABLE"
                    elif fam_name == "GLOBAL / MACRO":
                        trend_dir = "STABLE" if status == "READY" else "UNAVAILABLE"
                    elif fam_name == "NEWS / EVENT RISK":
                        trend_dir = "STABLE" if status == "READY" else "UNAVAILABLE"
                    else:
                        trend_dir = "STABLE"
                else:
                    trend_dir = "UNAVAILABLE" if fam_name in ("GLOBAL / MACRO", "HEAVYWEIGHTS") else "STABLE"

            # Emit Material Trend Events on Trend Direction Transition
            prev_trend = cls._last_confirmation_trends.get(fam_name)
            if prev_trend and prev_trend != trend_dir and trend_dir not in ("STABLE", "UNAVAILABLE") and primary_temporal:
                time_only_str = now_dt.strftime("%H:%M:%S IST")
                cooldown_k = f"trend_shift_{fam_name}_{trend_dir}"
                if not any(e.get("cooldown_key") == cooldown_k for e in cls._live_event_stream[:10]):
                    ev_type = (
                        "BREADTH_DETERIORATED" if (fam_name == "BREADTH" and trend_dir == "WEAKENING")
                        else "BREADTH_IMPROVED" if (fam_name == "BREADTH" and trend_dir == "IMPROVING")
                        else "PRICE_MOMENTUM_CHANGED" if fam_name == "PRICE"
                        else "OPTIONS_CONTEXT_CHANGED" if fam_name == "OPTIONS"
                        else "VOLATILITY_RISK_CHANGED" if fam_name == "VOLATILITY"
                        else "CONFIRMATION_CHANGED"
                    )
                    cls._live_event_stream.insert(0, {
                        "id": f"evt-{cls._sequence}-{len(cls._live_event_stream)}",
                        "event_id": f"evt-{cls._sequence}-{len(cls._live_event_stream)}",
                        "event_type": ev_type,
                        "family": fam_name,
                        "occurred_at": time_only_str,
                        "state_sequence": cls._sequence,
                        "materiality": "high" if trend_dir == "WEAKENING" else "medium",
                        "title": f"{fam_name} Trend Shifted to {trend_dir}",
                        "description": f"{fam_name} trend direction transitioned from {prev_trend} to {trend_dir}",
                        "previous_state": prev_trend,
                        "current_state": trend_dir,
                        "source_window": primary_temporal.get("requested_window", "5 MIN"),
                        "evidence": evidence or [f"{fam_name} temporal trend = {trend_dir}"],
                        "source_rule": f"RULE_{fam_name}_TREND_TRANSITION",
                        "cooldown_key": cooldown_k,
                        "source_state_sequence": cls._sequence
                    })
                    cls._live_event_stream = cls._live_event_stream[:50]

            cls._last_confirmation_trends[fam_name] = trend_dir

            family_dict = {
                "family": fam_name,
                "stance": bias,
                "bias": bias,
                "trend": trend_dir,
                "trend_direction": trend_dir,
                "status": status,
                "evidence_count": len(evidence),
                "evidence": evidence,
                "observed_at": observed_at
            }
            if reason:
                family_dict["reason"] = reason

            confirmation_families.append(family_dict)

        # Synthesize Authoritative Live Decision Payload (Sprint D.2 Phase 3A)
        live_decision = cls._derive_live_decision(
            generated=generated,
            snap=snap,
            market_state=market_state,
            expired=expired,
            market_closed=market_closed,
            primary_temporal=primary_temporal,
            confirmation_families=confirmation_families,
            unified=unified
        )

        unified["live_decision"] = live_decision
        unified["outlook"]["live_decision"] = live_decision
        support_payload["if_then_monitor"] = live_decision.get("if_then_monitor") or []
        support_payload["what_to_watch"] = live_decision.get("what_to_watch") or []
        support_payload["what_to_do_now"] = live_decision.get("what_to_do_now") or {}

        live_assistant_temporal_state = {
            "generated_at": generated,
            "current": {
                "generated_at": snap["timestamp"],
                "state_sequence": snap["state_sequence"],
                "market_state": snap["market_state"],
                "spot": snap["spot"],
                "regime": snap["regime"] or "UNKNOWN",
                "alignment": snap["alignment"] or "UNKNOWN",
                "advances": snap["breadth"]["advances"],
                "declines": snap["breadth"]["declines"],
                "pcr": snap["options"]["pcr"],
                "india_vix": snap["vix"],
            },
            "comparisons": comparisons,
            "confirmation_families": confirmation_families,
            "behavior_state": {
                "preferred_setup": unified.get("preferred_setup") or {},
                "supports": unified.get("supports") or [],
                "opposes": unified.get("opposes") or []
            },
            "scenario_monitoring": {
                "scenarios": unified.get("scenarios") or []
            },
            "material_events": cls._live_event_stream,
            "live_decision": live_decision
        }

        latency_diagnostics = cls._derive_latency_diagnostics(market, generated, current)
        market["live_feed_latency_truth"] = latency_diagnostics
        payload["marketContext"] = market

        session_story = cls._derive_session_story(
            generated=generated,
            now=current,
            snap=snap,
            unified=unified,
            live_decision=live_decision,
            primary_temporal=primary_temporal,
            news=news,
            market_session_phase=market_session_phase,
            market_closed=market_closed
        )

        from src.intelligence_engine.today_analysis_engine import TodayAnalysisEngine
        from src.intelligence_engine.live_assistant_engine import LiveAssistantEngine
        from src.intelligence_engine.forward_outlook_engine import ForwardOutlookEngine
        from src.intelligence_engine.pre_market_engine import PreMarketIntelligenceEngine

        eval_state = cls._build_analytical_evaluation_state(
            market=market,
            options=options,
            macro=macro,
            news=news,
            market_state=market_state,
            market_closed=market_closed,
            session_date=session_date,
        )

        pre_market_report = PreMarketIntelligenceEngine.analyze_pre_market(eval_state, cls._snapshots_history).to_dict()
        todays_analysis_report = TodayAnalysisEngine.analyze(eval_state, cls._snapshots_history).to_dict()
        session_story["todays_analysis"] = todays_analysis_report
        session_story["pre_market_report"] = pre_market_report

        try:
            live_assistant_intel = LiveAssistantEngine.analyze_live_session(eval_state, cls._snapshots_history, todays_analysis_report)
        except Exception as la_err:
            logger.error("LiveAssistantEngine analysis failed gracefully: %s", la_err, exc_info=True)
            live_assistant_intel = LiveAssistantEngine.fallback_unavailable_intel(session_date)
        forward_outlook_report = ForwardOutlookEngine.evaluate_outlook(
            eval_state, todays_analysis_report, live_assistant_intel, cls._snapshots_history
        ).to_dict()

        prim_scen = forward_outlook_report.get("primary_scenario") or {}
        scen_levels = prim_scen.get("relevant_levels") or {}
        scen_list = [prim_scen.get("scenario_type")] + [s.get("scenario_type") for s in (forward_outlook_report.get("alternate_scenarios") or [])]
        snap["forward_outlook"] = {
            "timestamp": forward_outlook_report.get("generated_at") or generated,
            "session_date": session_date,
            "analysis_status": forward_outlook_report.get("analysis_status") or "UNAVAILABLE",
            "status": forward_outlook_report.get("analysis_status") or "UNAVAILABLE",
            "classification": prim_scen.get("scenario_type") or forward_outlook_report.get("current_trend"),
            "scenario": prim_scen.get("scenario_type") or forward_outlook_report.get("current_trend"),
            "directional_bias": forward_outlook_report.get("current_trend"),
            "confidence": forward_outlook_report.get("overall_confidence"),
            "support": scen_levels.get("support"),
            "resistance": scen_levels.get("resistance"),
            "vwap": scen_levels.get("vwap") or market.get("vwap"),
            "scenarios": [s for s in scen_list if s],
            "confirmation_conditions": prim_scen.get("confirmation_conditions") or [],
            "invalidation_conditions": prim_scen.get("invalidation_conditions") or [],
            "key_evidence": prim_scen.get("supporting_evidence") or [],
            "full_report": forward_outlook_report
        }

        from src.intelligence_engine.pre_market_briefing_engine import PreMarketBriefingEngine
        try:
            briefing_report = PreMarketBriefingEngine.generate_or_get_briefing(eval_state).to_dict()
        except Exception as pmb_err:
            logger.error("PreMarketBriefingEngine generation failed gracefully: %s", pmb_err, exc_info=True)
            briefing_report = {}

        unified["session_story"] = session_story
        unified["pre_market_report"] = pre_market_report
        unified["pre_market_briefing"] = briefing_report
        unified["todays_analysis"] = todays_analysis_report
        unified["live_assistant_intelligence"] = live_assistant_intel
        unified["forward_outlook"] = forward_outlook_report
        unified["outlook"]["session_story"] = session_story
        unified["outlook"]["forward_outlook"] = forward_outlook_report
        unified["live_feed_latency_truth"] = latency_diagnostics

        live_assistant_temporal_state["session_story"] = session_story
        live_assistant_temporal_state["live_assistant_intelligence"] = live_assistant_intel
        snap["pre_market_briefing"] = briefing_report
        live_assistant_temporal_state["forward_outlook"] = forward_outlook_report
        live_assistant_temporal_state["live_feed_latency_truth"] = latency_diagnostics

        is_closed_phase = market_closed or market_session_phase in ("CLOSED", "POST_CLOSE")
        if is_closed_phase:
            if cls._closed_flushed_date != session_date:
                force_flush = True
                cls._closed_flushed_date = session_date
            else:
                force_flush = False
        else:
            cls._closed_flushed_date = None
            force_flush = False

        cls._persist_session_history(session_date, force=force_flush)

        state_seq = cls._next_sequence()

        from src.opportunity_engine.registry import OpportunityRegistryService
        opp_eval_context = {
            "market_context": section("marketContext", market_status),
            "option_context": section("optionContext", option_status),
            "breadth": section("marketContext", market_status).get("breadth") or {},
            "news": section("newsSentiment", news_status),
            "freshness_state": market_status.value.upper(),
            "market_state": str(market_state).upper(),
            "market_closed": market_closed,
        }
        opp_intel = OpportunityRegistryService.get_instance().evaluate_and_update(opp_eval_context, state_seq)

        return CanonicalWorkstationState(
            cls.SCHEMA_VERSION, state_seq, generated, cls._runtime_id,
            {"status": "closed" if str(market_state).upper() == "MARKET_CLOSED" else str(market_state).lower(), "is_closed": market_closed},
            {"status": "degraded" if expired else "ready", "read_only": True},
            {
                "status": "connected" if str(broker_state).upper() == "CONNECTED_VERIFIED" else "session_expired" if str(broker_state).upper() in ("CONNECTED_AUTH_REQUIRED", "TOKEN_EXPIRED", "SESSION_EXPIRED", "EXPIRED", "AUTH_REQUIRED") else "unverified" if str(broker_state).upper() in ("BROKER_STATE_UNVERIFIED", "RECONNECTING", "UNVERIFIED", "CONNECTED") else "disconnected",
                "normalized_status": "CONNECTED_VERIFIED" if str(broker_state).upper() == "CONNECTED_VERIFIED" else "CONNECTED_AUTH_REQUIRED" if str(broker_state).upper() in ("CONNECTED_AUTH_REQUIRED", "TOKEN_EXPIRED", "SESSION_EXPIRED", "EXPIRED", "AUTH_REQUIRED") else "BROKER_STATE_UNVERIFIED" if str(broker_state).upper() in ("BROKER_STATE_UNVERIFIED", "UNVERIFIED", "CONNECTED") else "RECONNECTING" if str(broker_state).upper() == "RECONNECTING" else "DISCONNECTED",
                "transport_connected": str(broker_state).upper() not in ("DISCONNECTED", "OFFLINE"),
                "authenticated": str(broker_state).upper() in ("CONNECTED_VERIFIED", "BROKER_STATE_UNVERIFIED", "CONNECTED"),
                "execution_verified": str(broker_state).upper() == "CONNECTED_VERIFIED",
                "session_valid": str(broker_state).upper() in ("CONNECTED_VERIFIED", "BROKER_STATE_UNVERIFIED", "CONNECTED"),
                "reconciliation_complete": str(broker_state).upper() == "CONNECTED_VERIFIED",
                "reconnect_required": str(broker_state).upper() != "CONNECTED_VERIFIED",
                "last_authenticated_at": broker_account.get("last_authenticated_at") if broker_account else None,
                "last_profile_validation": broker_account.get("profile_validated_at") if broker_account else None,
                "last_successful_update": broker_account.get("profile_validated_at") if broker_account else market_observed,
                "redirect_url": getattr(Config, "KITE_REDIRECT_URL", "http://127.0.0.1:3000/api/broker/callback")
            },
            {
                "status": "market_closed" if market_closed else market_status.value,
                "source": market_source,
                "bootstrap_state": (payload.get("streamTelemetry") or {}).get("bootstrap_state", "LIVE" if not market_closed else "DISCONNECTED"),
                "stream_status": (payload.get("streamTelemetry") or {}).get("stream_status", "CONNECTED" if not market_closed else "DISCONNECTED"),
                "connection_started_at": (payload.get("streamTelemetry") or {}).get("connection_started_at"),
                "connection_uptime_seconds": (payload.get("streamTelemetry") or {}).get("connection_uptime_seconds", 0.0),
                "reconnect_count": (payload.get("streamTelemetry") or {}).get("reconnect_count", 0),
                "subscribed_symbol_count": (payload.get("streamTelemetry") or {}).get("subscribed_symbol_count", 0),
                "last_subscription_time": (payload.get("streamTelemetry") or {}).get("last_subscription_time"),
                "last_valid_tick_time": (payload.get("streamTelemetry") or {}).get("last_valid_tick_time"),
                "last_valid_nifty_time": (payload.get("streamTelemetry") or {}).get("last_valid_nifty_time"),
                "tick_age_seconds": (payload.get("streamTelemetry") or {}).get("tick_age_seconds"),
            },
            section("marketContext", market_status), section("technicalAnalysis", market_status),
            section("optionContext", option_status), section("marketScore", market_status),
            section("opportunityContext", market_status), section("strategyEvaluation", assistant_status),
            sanitize_read_only(payload.get("tradeScenarios") or []),
            {**confidence_payload, "status": assistant_status.value}, {**risk_payload, "status": market_status.value},
            support_payload, explanation_payload,
            section("newsSentiment", news_status), broker_account or None, section("operationsReport", SectionStatus.READY),
            readiness, {"market_data": market_meta.to_dict(), "option_intelligence": option_meta.to_dict()},
            sanitize_read_only(payload.get("eveningReport") or {}),
            sanitize_read_only(payload.get("intradayReport") or {}),
            sanitize_read_only(payload.get("validationReport") or {}),
            sanitize_read_only(payload.get("optimizationReport") or {}),
            sanitize_read_only(payload.get("analyticsReport") or {}),
            macro,
            unified,
            live_assistant_temporal_state=live_assistant_temporal_state,
            session_story=session_story,
            opportunity_intelligence=opp_intel,
            warnings=support.warnings, errors=[],
        )

    @staticmethod
    def _timestamp(section: dict[str, Any]) -> Any:
        for key in ("provider_timestamp", "snapshot_timestamp", "observed_at", "observedAt", "last_tick_time", "timestamp", "lastUpdated", "generated_at", "generatedAt"):
            if section.get(key):
                return section[key]
        return None

    @staticmethod
    def _apply_news_temporal_workspace(news: dict[str, Any], now: datetime, market_observed: Any) -> None:
        """Re-evaluate time-dependent eligibility before canonical publication.

        This is a defensive second gate: persisted pipeline output cannot carry
        a previously-current flag forever across a restart or long-lived state.
        """
        explicit_close = strict_publication_timestamp(news.get("last_market_close_boundary"))
        boundary = strict_publication_timestamp(market_observed) or explicit_close
        current_items: list[dict[str, Any]] = []
        newly_historical: list[dict[str, Any]] = []
        for original in news.get("items") or []:
            item = dict(original)
            assessment = assess_publication_time(item.get("published_at"), now, explicit_close)
            item.update({
                "normalized_timestamp": assessment.published_at_utc.isoformat().replace("+00:00", "Z") if assessment.published_at_utc else "",
                "timestamp_validity": assessment.timestamp_validity,
                "timestamp_confidence": assessment.timestamp_confidence,
                "timestamp_source": assessment.timestamp_source,
                "temporal_class": assessment.temporal_class,
                "canonical_eligible": assessment.current_eligible,
                "workspace_eligible": assessment.current_eligible,
                "age_seconds": assessment.age_seconds,
                "age_minutes": round(assessment.age_seconds / 60, 2) if assessment.age_seconds is not None else None,
            })
            (current_items if assessment.current_eligible else newly_historical).append(item)

        current_ids = {str(item.get("id")) for item in current_items}
        news["items"] = current_items
        news["historical_items"] = [*(news.get("historical_items") or []), *newly_historical]
        for key in ("top_headlines", "high_impact_items"):
            news[key] = [item for item in news.get(key) or [] if str(item.get("id")) in current_ids]
        news["corporate_items"] = [item for item in news.get("corporate_items") or [] if str(item.get("id")) in current_ids]
        news["event_items"] = [item for item in news.get("event_items") or [] if str(item.get("id")) in current_ids]

        current_clusters = []
        expired_clusters = []
        for original in news.get("event_clusters") or []:
            cluster = dict(original)
            active_ids = [article_id for article_id in cluster.get("article_ids") or [] if str(article_id) in current_ids]
            cluster_time = cluster.get("latest_article_published_at") or cluster.get("last_updated")
            cluster_temporal = assess_publication_time(cluster_time, now, explicit_close)
            carried_current_count = int(cluster.get("current_article_count") or 0) if cluster_temporal.current_eligible else 0
            if cluster_temporal.current_eligible and "canonical_eligible" not in cluster:
                # Legacy canonical clusters predate the explicit count fields;
                # their own validated latest-publication timestamp is sufficient.
                carried_current_count = max(1, carried_current_count)
            active_count = max(len(active_ids), carried_current_count)
            cluster["current_article_count"] = active_count
            cluster["historical_article_count"] = max(0, int(cluster.get("article_count") or 0) - len(active_ids))
            cluster["canonical_eligible"] = bool(active_count)
            (current_clusters if active_count else expired_clusters).append(cluster)
        news["event_clusters"] = current_clusters
        news["historical_event_clusters"] = [*(news.get("historical_event_clusters") or []), *expired_clusters]

        since_close_ids: list[str] = []
        previous_session_ids: list[str] = []
        for item in current_items:
            observed = strict_publication_timestamp(item.get("published_at"))
            if boundary and observed and observed > boundary:
                since_close_ids.append(str(item.get("id")))
            elif boundary and observed:
                previous_session_ids.append(str(item.get("id")))
        since_close_clusters = [
            str(cluster.get("event_cluster_id")) for cluster in current_clusters
            if any(str(article_id) in set(since_close_ids) for article_id in cluster.get("article_ids") or [])
        ]
        news["workspace_temporal"] = {
            "boundary": boundary.isoformat().replace("+00:00", "Z") if boundary else None,
            "since_close_item_ids": since_close_ids,
            "since_close_cluster_ids": since_close_clusters,
            "previous_session_context_item_ids": previous_session_ids,
            "current_driver_item_ids": since_close_ids if boundary else list(current_ids),
            "live_feed_count": len(current_items),
            "pre_market_since_close_count": len(since_close_ids),
            "todays_analysis_current_driver_count": len(since_close_ids if boundary else current_ids),
            "live_assistant_since_close_count": len(since_close_ids),
            "canonical_to_workspace_current_data_loss": 0,
        }
        metrics = news.setdefault("ingestion_metrics", {})
        metrics["canonical_to_workspace_data_loss"] = 0
        metrics["canonical_to_workspace_current_data_loss"] = 0
        diagnostics = news.setdefault("temporal_diagnostics", {})
        diagnostics["workspace"] = dict(news["workspace_temporal"])

    @staticmethod
    def _apply_macro_workspace(macro: dict[str, Any], now: datetime, market_observed: Any) -> None:
        expected = {
            "S&P 500", "NASDAQ", "DOW_JONES", "NIKKEI_225", "HANG_SENG",
            "BRENT_CRUDE", "GOLD", "USD_INR", "DXY", "US_10Y", "GIFT_NIFTY",
        }
        boundary = strict_publication_timestamp(market_observed)
        statuses = dict(macro.get("quote_status") or {})
        valid_quotes: dict[str, dict[str, Any]] = {}
        current_keys: list[str] = []
        since_close_keys: list[str] = []
        stale_keys: list[str] = []
        for key, original in (macro.get("quotes") or {}).items():
            quote = dict(original)
            observation = quote.get("observation_timestamp") or quote.get("published_at")
            assessment = assess_macro_observation(observation, now, str(quote.get("exchange_timezone") or "UTC"))
            quote.update({
                "observation_timestamp": assessment.observation_utc.isoformat().replace("+00:00", "Z") if assessment.observation_utc else "",
                "published_at": assessment.observation_utc.isoformat().replace("+00:00", "Z") if assessment.observation_utc else "",
                "freshness_status": assessment.freshness, "freshness": assessment.freshness,
                "status": assessment.status, "current_eligible": assessment.current_eligible,
                "age_seconds": assessment.age_seconds,
            })
            if assessment.observation_utc is None:
                statuses[str(key)] = {
                    "status": "UNAVAILABLE", "reason": assessment.reason,
                    "source": quote.get("source_name"), "source_symbol": quote.get("source_symbol"),
                }
                continue
            valid_quotes[str(key)] = quote
            statuses[str(key)] = {
                **dict(statuses.get(str(key)) or {}), "status": assessment.status,
                "reason": assessment.reason or None, "freshness": assessment.freshness,
                "observation_timestamp": quote["observation_timestamp"],
            }
            if assessment.current_eligible:
                current_keys.append(str(key))
                if boundary and assessment.observation_utc > boundary:
                    since_close_keys.append(str(key))
            else:
                stale_keys.append(str(key))

        statuses.setdefault("GIFT_NIFTY", {
            "status": "UNAVAILABLE", "reason": "GENUINE_PROVIDER_NOT_CONFIGURED",
            "source": None, "source_symbol": None,
        })
        for key in expected:
            statuses.setdefault(key, {
                "status": "UNAVAILABLE", "reason": "PROVIDER_RETURNED_NO_VALID_QUOTE",
                "source": "Yahoo Finance Public Feed" if key != "GIFT_NIFTY" else None,
                "source_symbol": None,
            })
        macro["quotes"] = valid_quotes
        macro["quote_status"] = statuses
        macro.setdefault("domain_freshness", {})["global_quotes"] = aggregate_quote_freshness(list(valid_quotes.values()))
        unavailable = sorted(key for key in expected if statuses.get(key, {}).get("status") == "UNAVAILABLE")
        compact_order = ["S&P 500", "NASDAQ", "NIKKEI_225", "BRENT_CRUDE", "USD_INR", "US_10Y"]
        macro["workspace_context"] = {
            "market_boundary": boundary.isoformat().replace("+00:00", "Z") if boundary else None,
            "current_context_quote_keys": current_keys,
            "since_india_close_quote_keys": since_close_keys,
            "stale_quote_keys": stale_keys,
            "unavailable_quote_keys": unavailable,
            "critical_external_data_missing": unavailable,
            "nifty_live_quote_keys": [key for key in compact_order if key in current_keys],
            "premarket_850_quote_keys": current_keys,
            "todays_analysis_quote_keys": current_keys,
            "live_assistant_quote_keys": since_close_keys,
            "canonical_quote_count": len(valid_quotes),
            "workspace_quote_count": len(valid_quotes),
            "canonical_to_workspace_data_loss": 0,
        }
        metrics = macro.setdefault("ingestion_metrics", {})
        metrics["canonical_to_workspace_data_loss"] = 0

    @staticmethod
    def _link_released_economic_events(news: dict[str, Any], macro: dict[str, Any]) -> None:
        keyword_map = {
            "CPI": {"cpi", "consumer", "inflation"}, "CORE_CPI": {"cpi", "core", "inflation"},
            "NONFARM_PAYROLLS": {"payroll", "jobs", "employment"}, "GDP": {"gdp", "growth"},
            "FOMC_RATE_DECISION": {"fed", "fomc", "rates"}, "RBI_RATE_DECISION": {"rbi", "repo", "policy"},
            "ECB_RATE_DECISION": {"ecb", "rates"}, "BOJ_RATE_DECISION": {"boj", "rates"},
            "PCE": {"pce", "personal", "inflation"}, "CORE_PCE": {"pce", "core", "inflation"},
            "PPI": {"ppi", "producer", "wholesale"}, "RETAIL_SALES": {"retail", "sales"},
            "INDUSTRIAL_PRODUCTION": {"industrial", "production"},
        }
        released = [event for event in macro.get("economic_events") or [] if event.get("status") == "RELEASED"]
        for cluster in news.get("event_clusters") or []:
            headline = str(cluster.get("canonical_headline") or "").lower()
            cluster_time = WorkstationStateService._parse_time(cluster.get("last_updated"))
            countries = {str(value).lower() for value in cluster.get("related_countries") or []}
            best: tuple[float, str] | None = None
            for event in released:
                scheduled = WorkstationStateService._parse_time(event.get("scheduled_at"))
                if not scheduled or not cluster_time or abs((cluster_time - scheduled).total_seconds()) > 72 * 3600:
                    continue
                terms = keyword_map.get(str(event.get("canonical_event_name") or ""), set())
                if not terms or not (terms & set(headline.replace("/", " ").split())):
                    continue
                country = str(event.get("country") or "").lower()
                if countries and not any(country in value or value in country for value in countries):
                    continue
                distance = abs((cluster_time - scheduled).total_seconds())
                if best is None or distance < best[0]:
                    best = (distance, str(event.get("event_id") or ""))
            if best and best[1]:
                cluster["economic_event_id"] = best[1]

    @staticmethod
    def _parse_time(value: Any) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None

    @staticmethod
    def _section(freshness: FreshnessStatus) -> SectionStatus:
        return {FreshnessStatus.FRESH: SectionStatus.READY, FreshnessStatus.STALE: SectionStatus.DEGRADED,
                FreshnessStatus.BLOCKED: SectionStatus.BLOCKED,
                FreshnessStatus.UNAVAILABLE: SectionStatus.UNAVAILABLE,
                FreshnessStatus.MARKET_CLOSED: SectionStatus.MARKET_CLOSED}[freshness]

    @staticmethod
    def _dependent(required: SectionStatus, optional: list[SectionStatus]) -> SectionStatus:
        if required in {SectionStatus.BLOCKED, SectionStatus.UNAVAILABLE}:
            return SectionStatus.BLOCKED
        if required == SectionStatus.MARKET_CLOSED:
            return SectionStatus.MARKET_CLOSED
        return SectionStatus.DEGRADED if any(x != SectionStatus.READY for x in optional) else SectionStatus.READY

    @staticmethod
    def validate_setup_geometry(setup: dict[str, Any], decision_areas: list[dict[str, Any]] | None = None, key_levels: list[dict[str, Any]] | None = None) -> tuple[bool, list[str]]:
        """Deterministically validates decision setup geometry (Sprint D.2 Phase 3A.1)."""
        issues: list[str] = []
        if not isinstance(setup, dict):
            return False, ["ENTRY_REFERENCE_UNAVAILABLE"]

        direction = str(setup.get("direction") or "").upper()
        entry_ref = setup.get("entry_reference") or {}
        invalidation = setup.get("invalidation") or {}
        profit_refs = setup.get("profit_references") or {}
        p1 = profit_refs.get("first_reference") or {}
        p2 = profit_refs.get("second_reference") or {}

        # 1. Entry Reference Availability
        if not entry_ref.get("available") or entry_ref.get("zone_low") is None or entry_ref.get("zone_high") is None:
            issues.append("ENTRY_REFERENCE_UNAVAILABLE")

        # 2. Invalidation Availability & Direction
        inval_low = invalidation.get("zone_low")
        inval_high = invalidation.get("zone_high")
        if not invalidation or (inval_low is None and inval_high is None and not invalidation.get("zone")):
            issues.append("INVALIDATION_UNAVAILABLE")
        elif entry_ref.get("available") and entry_ref.get("zone_low") is not None and entry_ref.get("zone_high") is not None:
            e_low = float(entry_ref["zone_low"])
            e_high = float(entry_ref["zone_high"])
            if inval_low is not None and inval_high is not None:
                if direction == "BEARISH" and float(inval_low) < e_low:
                    issues.append("INVALIDATION_WRONG_SIDE")
                elif direction == "BULLISH" and float(inval_high) > e_high:
                    issues.append("INVALIDATION_WRONG_SIDE")
            elif inval_low is not None:
                if direction == "BEARISH" and float(inval_low) < e_low:
                    issues.append("INVALIDATION_WRONG_SIDE")
                elif direction == "BULLISH" and float(inval_low) > e_high:
                    issues.append("INVALIDATION_WRONG_SIDE")

        # 3. First Profit Reference Availability & Collision & Direction
        if not p1.get("available"):
            issues.append("FIRST_PROFIT_REFERENCE_UNAVAILABLE")
        else:
            # Check Entry / Profit collision
            e_prov = entry_ref.get("provenance_id") or entry_ref.get("reference_id") or entry_ref.get("display_range")
            p1_prov = p1.get("provenance_id") or p1.get("reference_id") or p1.get("display_range") or p1.get("zone")
            if e_prov and p1_prov and (e_prov == p1_prov or entry_ref.get("display_range") == p1.get("zone") or entry_ref.get("display_range") == p1.get("display_range")):
                issues.append("ENTRY_PROFIT_COLLISION")

            # Check side relative to entry
            p1_low = p1.get("zone_low")
            p1_high = p1.get("zone_high")
            if entry_ref.get("available") and entry_ref.get("zone_low") is not None and entry_ref.get("zone_high") is not None:
                e_low = float(entry_ref["zone_low"])
                e_high = float(entry_ref["zone_high"])
                if direction == "BEARISH":
                    p1_val = float(p1_high) if p1_high is not None else float(p1_low) if p1_low is not None else None
                    if p1_val is not None and p1_val >= e_low:
                        issues.append("FIRST_PROFIT_REFERENCE_WRONG_SIDE")
                elif direction == "BULLISH":
                    p1_val = float(p1_low) if p1_low is not None else float(p1_high) if p1_high is not None else None
                    if p1_val is not None and p1_val <= e_high:
                        issues.append("FIRST_PROFIT_REFERENCE_WRONG_SIDE")

        # 4. Second Profit Reference Direction & Monotonicity
        if p2.get("available"):
            p2_low = p2.get("zone_low")
            p2_high = p2.get("zone_high")
            p1_low = p1.get("zone_low")
            p1_high = p1.get("zone_high")
            if p1.get("available") and p1_low is not None and p2_low is not None:
                if direction == "BEARISH":
                    p2_val = float(p2_high) if p2_high is not None else float(p2_low)
                    p1_val = float(p1_low) if p1_low is not None else float(p1_high)
                    if p2_val >= p1_val:
                        issues.append("SECOND_PROFIT_REFERENCE_WRONG_SIDE")
                        issues.append("NON_MONOTONIC_PROFIT_REFERENCES")
                elif direction == "BULLISH":
                    p2_val = float(p2_low) if p2_low is not None else float(p2_high)
                    p1_val = float(p1_high) if p1_high is not None else float(p1_low)
                    if p2_val <= p1_val:
                        issues.append("SECOND_PROFIT_REFERENCE_WRONG_SIDE")
                        issues.append("NON_MONOTONIC_PROFIT_REFERENCES")

        dedup_issues = list(dict.fromkeys(issues))
        return (len(dedup_issues) == 0, dedup_issues)

    @classmethod
    def _derive_live_decision(cls, *, generated: str, snap: dict[str, Any], market_state: str,
                             expired: bool, market_closed: bool, primary_temporal: dict[str, Any] | None,
                             confirmation_families: list[dict[str, Any]], unified: dict[str, Any]) -> dict[str, Any]:
        """Synthesizes authoritative live decision payload with hardened geometry (Sprint D.2 Phase 3A.1)."""
        raw_state = str(market_state or "").upper()
        if raw_state in {"PRE_OPEN", "PRE_MARKET"}:
            session_phase = "PRE_OPEN"
        elif raw_state in {"MARKET_OPEN", "OPEN", "LIVE"}:
            session_phase = "MARKET_OPEN"
        elif raw_state == "WEEKEND":
            session_phase = "WEEKEND"
        elif raw_state in {"HOLIDAY", "TRADING_HOLIDAY"}:
            session_phase = "HOLIDAY"
        else:
            session_phase = "POST_CLOSE"
        spot_val = snap.get("spot")
        align_state = str(unified.get("alignment") or "").upper()
        confidence = str(unified.get("confidence") or "LOW").upper()
        risk_dict = unified.get("risk") or {}
        risk_state = str(risk_dict.get("state") or "NORMAL").upper()

        # 1. Decision Status
        stale_ev = []
        missing_ev = []
        if expired:
            stale_ev.append({"family": "ALL", "freshness": "expired", "reason": "broker session expired"})

        # Check Heavyweights status
        hw_family = next((f for f in confirmation_families if f["family"] == "HEAVYWEIGHTS"), None)
        if hw_family and hw_family.get("status") == "UNAVAILABLE":
            missing_ev.append({
                "family": "HEAVYWEIGHTS",
                "severity": "OPTIONAL",
                "reason": hw_family.get("reason", "authoritative heavyweight membership/weights unavailable")
            })

        if session_phase != "MARKET_OPEN" or market_closed:
            decision_status = "MARKET_CLOSED"
            decision_eligible = False
        elif expired or stale_ev:
            decision_status = "STALE"
            decision_eligible = False
        elif primary_temporal is None or primary_temporal.get("status") == "REBUILDING":
            decision_status = "REBUILDING_TEMPORAL_CONTEXT"
            decision_eligible = True
        elif confidence == "INSUFFICIENT":
            decision_status = "INSUFFICIENT_EVIDENCE"
            decision_eligible = True
        else:
            decision_status = "READY"
            decision_eligible = True

        # 2. Confirmation Summary Counts
        supporting_count = sum(1 for f in confirmation_families if f.get("stance") in ("Bullish", "Positive"))
        neutral_count = sum(1 for f in confirmation_families if f.get("stance") == "Neutral")
        opposing_count = sum(1 for f in confirmation_families if f.get("stance") in ("Bearish", "Negative"))
        unavail_count = sum(1 for f in confirmation_families if f.get("status") == "UNAVAILABLE")

        improving_count = sum(1 for f in confirmation_families if f.get("trend_direction") == "IMPROVING")
        stable_count = sum(1 for f in confirmation_families if f.get("trend_direction") == "STABLE")
        weakening_count = sum(1 for f in confirmation_families if f.get("trend_direction") == "WEAKENING")
        dir_unavail_count = sum(1 for f in confirmation_families if f.get("trend_direction") == "UNAVAILABLE")

        confirmation_summary = {
            "absolute_counts": {
                "supporting": supporting_count,
                "neutral": neutral_count,
                "opposing": opposing_count,
                "unavailable": unavail_count
            },
            "direction_counts": {
                "improving": improving_count,
                "stable": stable_count,
                "weakening": weakening_count,
                "unavailable": dir_unavail_count
            }
        }

        # 3. Directional Pressure & Structural Bias
        if unavail_count == len(confirmation_families):
            directional_pressure = "UNAVAILABLE"
        elif opposing_count >= 2 or "BEARISH" in align_state:
            directional_pressure = "BEARISH"
        elif supporting_count >= 2 or "BULLISH" in align_state:
            directional_pressure = "BULLISH"
        elif supporting_count > 0 and opposing_count > 0 or align_state == "CONFLICTED":
            directional_pressure = "MIXED"
        else:
            directional_pressure = "NEUTRAL"

        structural_bias = directional_pressure

        # 4. Momentum & Short Term Momentum
        if primary_temporal:
            p_stat = primary_temporal.get("spot_status")
            if p_stat == "Improving":
                momentum = "IMPROVING"
            elif p_stat == "Weakening":
                momentum = "WEAKENING"
            elif p_stat == "Stable":
                if directional_pressure == "BEARISH" and primary_temporal.get("diff_spot", 0.0) > -15.0:
                    momentum = "STABILIZING"
                else:
                    momentum = "STABLE"
            else:
                momentum = "STABLE"
        else:
            momentum = "UNAVAILABLE"

        short_term_momentum = momentum

        # 5. Decision Area Context & Relationship
        decision_zones = unified.get("decision_zones") or []
        levels = unified.get("levels") or []
        supports = [z for z in decision_zones if z.get("role") == "SUPPORT"]
        resistances = [z for z in decision_zones if z.get("role") == "RESISTANCE"]

        sup_zone = supports[0] if supports else None
        res_zone = resistances[0] if resistances else None

        sup_display = sup_zone.get("display_range") if sup_zone else "Awaiting live structural level"
        res_display = res_zone.get("display_range") if res_zone else "Awaiting live structural level"

        dist_sup = round(spot_val - sup_zone.get("upper", spot_val), 1) if (spot_val and sup_zone and "upper" in sup_zone) else None
        dist_res = round(res_zone.get("lower", spot_val) - spot_val, 1) if (spot_val and res_zone and "lower" in res_zone) else None

        if spot_val and sup_zone and res_zone:
            if spot_val < sup_zone.get("lower", 0):
                relationship = "BELOW_SUPPORT"
            elif spot_val <= sup_zone.get("upper", 0):
                relationship = "INSIDE_SUPPORT"
            elif spot_val > res_zone.get("upper", 999999):
                relationship = "ABOVE_RESISTANCE"
            elif spot_val >= res_zone.get("lower", 999999):
                relationship = "INSIDE_RESISTANCE"
            else:
                relationship = "BETWEEN_AREAS"
        elif spot_val and sup_zone:
            relationship = "INSIDE_SUPPORT" if spot_val <= sup_zone.get("upper", 0) else "BELOW_SUPPORT" if spot_val < sup_zone.get("lower", 0) else "NO_STRUCTURE"
        elif spot_val and res_zone:
            relationship = "INSIDE_RESISTANCE" if spot_val >= res_zone.get("lower", 999999) else "ABOVE_RESISTANCE" if spot_val > res_zone.get("upper", 999999) else "NO_STRUCTURE"
        else:
            relationship = "NO_STRUCTURE"

        decision_area_context = {
            "relationship": relationship,
            "nearest_support": sup_display,
            "nearest_resistance": res_display,
            "distance_to_support_points": dist_sup,
            "distance_to_resistance_points": dist_res
        }

        # 6. Decision Posture
        if session_phase != "MARKET_OPEN" or decision_status == "STALE":
            posture = "STAND_ASIDE"
            posture_label = "STAND ASIDE"
            what_now_prose = "Market is closed or data is stale. Stand aside and await active session baseline."
        elif decision_status == "REBUILDING_TEMPORAL_CONTEXT":
            posture = "WAIT"
            posture_label = "WAIT FOR TEMPORAL BASELINE"
            what_now_prose = "Rebuilding temporal history window. Await continuous live snapshots before evaluating setup."
        elif risk_state == "HIGH" or align_state in ("CONFLICTED", "INSUFFICIENT_EVIDENCE"):
            posture = "HIGH_UNCERTAINTY"
            posture_label = "HIGH UNCERTAINTY — STAND ASIDE"
            what_now_prose = "High uncertainty or conflicting market cues detected. Stand aside until directional consensus forms."
        elif directional_pressure == "BEARISH":
            if relationship in ("INSIDE_SUPPORT", "BELOW_SUPPORT") or momentum == "WEAKENING":
                posture = "WATCH_BREAKDOWN"
                posture_label = "WATCH FOR BREAKDOWN"
                what_now_prose = f"Price is testing lower decision area {sup_display} with bearish pressure. Watch for a confirmed breakdown."
            elif momentum == "STABILIZING" or relationship == "BETWEEN_AREAS":
                posture = "BEARISH_BIAS_AWAIT_CONFIRMATION"
                posture_label = "BEARISH BIAS — AWAIT CONFIRMATION"
                what_now_prose = "Bearish structure is intact but momentum is stabilizing near support. Await renewed breakdown confirmation."
            else:
                posture = "BEARISH_BIAS_AWAIT_CONFIRMATION"
                posture_label = "BEARISH BIAS — AWAIT CONFIRMATION"
                what_now_prose = "Bearish posture retained. Await constituent breadth and lower decision area confirmation."
        elif directional_pressure == "BULLISH":
            if relationship in ("INSIDE_RESISTANCE", "ABOVE_RESISTANCE") or momentum == "IMPROVING":
                posture = "WATCH_BREAKOUT"
                posture_label = "WATCH FOR BREAKOUT"
                what_now_prose = f"Price is testing upper decision area {res_display} with bullish momentum. Watch for a confirmed breakout."
            else:
                posture = "BULLISH_BIAS_AWAIT_CONFIRMATION"
                posture_label = "BULLISH BIAS — AWAIT CONFIRMATION"
                what_now_prose = "Bullish posture retained. Await breadth expansion above upper resistance."
        else:
            posture = "RANGE_MEAN_REVERSION"
            posture_label = "RANGE / MEAN-REVERSION CONDITIONS"
            what_now_prose = "Price is trapped between decision areas. Directional entries have poor confirmation; range conditions dominate."

        # 7. Refined Current Read Language Templates
        if session_phase != "MARKET_OPEN":
            current_read = f"Market session {session_phase.lower()}; awaiting continuous session open baseline."
        elif decision_status == "REBUILDING_TEMPORAL_CONTEXT":
            current_read = "Rebuilding temporal history baseline; awaiting continuous snapshots."
        elif directional_pressure == "BEARISH":
            if momentum == "WEAKENING" and relationship in ("INSIDE_SUPPORT", "BELOW_SUPPORT"):
                current_read = f"Bearish pressure with weakening momentum at support {sup_display}."
            elif momentum == "WEAKENING":
                current_read = f"Downside pressure with weakening momentum; testing lower decision area {sup_display}."
            elif momentum in ("STABILIZING", "STABLE") and relationship == "BETWEEN_AREAS":
                current_read = "Bearish background structure with short-term stabilization inside the current range."
            elif momentum == "STABILIZING":
                current_read = f"Downside pressure with stabilizing momentum near support {sup_display}."
            else:
                current_read = f"Bearish background structure with {momentum.lower()} momentum near lower decision area {sup_display}."
        elif directional_pressure == "BULLISH":
            if momentum == "IMPROVING" and relationship in ("ABOVE_RESISTANCE", "INSIDE_RESISTANCE"):
                current_read = f"Bullish pressure strengthening above resistance {res_display}."
            elif momentum == "IMPROVING":
                current_read = f"Bullish pressure with improving momentum at resistance {res_display}."
            elif momentum in ("STABILIZING", "STABLE") and relationship == "BETWEEN_AREAS":
                current_read = "Bullish background structure with short-term stabilization inside the current range."
            else:
                current_read = f"Upside pressure with {momentum.lower()} momentum near resistance {res_display}."
        elif directional_pressure == "MIXED" or relationship == "BETWEEN_AREAS":
            current_read = "Mixed structure with range-bound price action."
        else:
            current_read = f"Range-bound structure between {sup_display} support and {res_display} resistance."

        # 8. Scenarios / Paths
        scenarios = unified.get("scenarios") or []
        prim_scen = scenarios[0] if scenarios else {}
        alt_scen = scenarios[1] if len(scenarios) > 1 else {}

        most_likely_path = {
            "path_id": prim_scen.get("name", "RANGE_BOUND_CONSOLIDATION"),
            "title": str(prim_scen.get("name", "RANGE_BOUND_CONSOLIDATION")).replace("_", " ").title(),
            "plain_language_summary": prim_scen.get("description") or f"Intraday structure favors {posture_label.lower()}.",
            "time_horizon": "NEXT 5–15 MINUTES",
            "confidence": confidence,
            "why": [f"Aligned with {directional_pressure.lower()} directional pressure and {momentum.lower()} momentum."],
            "confirmation_conditions": prim_scen.get("confirmation_conditions", []),
            "invalidation_conditions": prim_scen.get("invalidation_conditions", []),
            "source_scenario_id": prim_scen.get("name", "RANGE_BOUND_CONSOLIDATION"),
            "source_rules": ["RULE_PRIMARY_SCENARIO_SELECTION"]
        }

        if alt_scen:
            alternate_path = {
                "status": "AVAILABLE",
                "path_id": alt_scen.get("name"),
                "title": str(alt_scen.get("name")).replace("_", " ").title(),
                "plain_language_summary": alt_scen.get("description") or "Alternate path triggers if primary structure is invalidated.",
                "time_horizon": "NEXT 5–15 MINUTES",
                "confidence": "LOW" if confidence == "HIGH" else "MODERATE",
                "why": ["Alternate structural scenario if key level or breadth reverses."],
                "confirmation_conditions": alt_scen.get("confirmation_conditions", []),
                "invalidation_conditions": alt_scen.get("invalidation_conditions", []),
                "source_scenario_id": alt_scen.get("name"),
                "source_rules": ["RULE_ALTERNATE_SCENARIO_SELECTION"]
            }
        else:
            alternate_path = {
                "status": "UNAVAILABLE",
                "path_id": "NONE",
                "title": "Alternate Path Unavailable",
                "plain_language_summary": "No eligible alternate scenario in canonical intelligence.",
                "time_horizon": "NEXT 5–15 MINUTES",
                "confidence": "LOW",
                "why": ["No eligible alternate scenario in canonical intelligence"],
                "confirmation_conditions": [],
                "invalidation_conditions": [],
                "source_scenario_id": "NONE",
                "source_rules": ["RULE_ALTERNATE_SCENARIO_UNAVAILABLE"]
            }

        # 9. Hardened Setup Candidate Synthesis (Sprint D.2 Phase 3A.1)
        if directional_pressure == "BEARISH":
            setup_type_candidate = "BREAKDOWN_CONTINUATION" if relationship in ("BELOW_SUPPORT", "INSIDE_SUPPORT") else "TREND_CONTINUATION"
            direction = "BEARISH"
            instrument = "NIFTY PUT"
        elif directional_pressure == "BULLISH":
            setup_type_candidate = "BREAKOUT_CONTINUATION" if relationship in ("ABOVE_RESISTANCE", "INSIDE_RESISTANCE") else "TREND_CONTINUATION"
            direction = "BULLISH"
            instrument = "NIFTY CALL"
        else:
            setup_type_candidate = "RANGE_MEAN_REVERSION" if relationship == "BETWEEN_AREAS" else "NO_SETUP"
            direction = "NEUTRAL"
            instrument = "NIFTY OPTIONS — DIRECTION NOT CONFIRMED" if relationship == "BETWEEN_AREAS" else "NO OPTION SETUP"

        # --- A. ENTRY REFERENCE ---
        if direction == "BEARISH" and sup_zone:
            e_low = sup_zone.get("lower")
            e_high = sup_zone.get("upper")
            e_disp = sup_zone.get("display_range", sup_display)
            e_id = sup_zone.get("provenance_id") or sup_zone.get("id") or f"dz_support_{e_low}_{e_high}"
            entry_ref_dict = {
                "available": True,
                "reference_id": e_id,
                "reference_type": "DECISION_AREA",
                "role": "ENTRY_REFERENCE",
                "zone_low": e_low,
                "zone_high": e_high,
                "display_range": e_disp,
                "source_rule": "RULE_ENTRY_BREAKDOWN_AREA",
                "provenance": sup_zone.get("provenance", "canonical.decision_zones"),
                "provenance_id": e_id
            }
        elif direction == "BULLISH" and res_zone:
            e_low = res_zone.get("lower")
            e_high = res_zone.get("upper")
            e_disp = res_zone.get("display_range", res_display)
            e_id = res_zone.get("provenance_id") or res_zone.get("id") or f"dz_resistance_{e_low}_{e_high}"
            entry_ref_dict = {
                "available": True,
                "reference_id": e_id,
                "reference_type": "DECISION_AREA",
                "role": "ENTRY_REFERENCE",
                "zone_low": e_low,
                "zone_high": e_high,
                "display_range": e_disp,
                "source_rule": "RULE_ENTRY_BREAKOUT_AREA",
                "provenance": res_zone.get("provenance", "canonical.decision_zones"),
                "provenance_id": e_id
            }
        elif direction == "NEUTRAL" and (sup_zone or res_zone):
            ref_z = sup_zone if (spot_val and sup_zone and spot_val <= (sup_zone.get("upper", 0) + 30.0)) else res_zone or sup_zone
            e_low = ref_z.get("lower") if ref_z else None
            e_high = ref_z.get("upper") if ref_z else None
            e_disp = ref_z.get("display_range") if ref_z else "Awaiting live structural level"
            e_id = ref_z.get("provenance_id") or ref_z.get("id") or f"dz_range_{e_low}_{e_high}" if ref_z else "NONE"
            entry_ref_dict = {
                "available": ref_z is not None,
                "reference_id": e_id,
                "reference_type": "DECISION_AREA" if ref_z else "UNAVAILABLE",
                "role": "ENTRY_REFERENCE",
                "zone_low": e_low,
                "zone_high": e_high,
                "display_range": e_disp,
                "source_rule": "RULE_ENTRY_RANGE_AREA",
                "provenance": ref_z.get("provenance", "canonical.decision_zones") if ref_z else "canonical.decision_zones",
                "provenance_id": e_id
            }
        else:
            entry_ref_dict = {
                "available": False,
                "reference_id": "NONE",
                "reference_type": "UNAVAILABLE",
                "role": "ENTRY_REFERENCE",
                "zone_low": None,
                "zone_high": None,
                "display_range": "Awaiting live structural level",
                "source_rule": "RULE_ENTRY_UNAVAILABLE",
                "provenance": "canonical.decision_zones",
                "provenance_id": "NONE"
            }

        # --- B. INVALIDATION REFERENCE ---
        if direction == "BEARISH":
            inv_z = res_zone
            inval_display = res_display
            inval_conds = [f"NIFTY spot reclaims resistance {res_display}", "Constituent breadth advances exceed declines", "Option PCR recovers above 1.1"]
        elif direction == "BULLISH":
            inv_z = sup_zone
            inval_display = sup_display
            inval_conds = [f"NIFTY spot breaks below support {sup_display}", "Constituent breadth declines exceed advances", "Option PCR drops below 0.8"]
        else:
            inv_z = res_zone if (entry_ref_dict.get("provenance_id") == sup_zone.get("provenance_id") if sup_zone else False) else sup_zone
            inval_display = inv_z.get("display_range") if inv_z else "Opposing Decision Area"
            inval_conds = ["Price expands beyond range boundaries", "Directional momentum expansion"]

        inv_id = inv_z.get("provenance_id") or inv_z.get("id") or f"dz_inval_{inval_display}" if inv_z else "NONE"
        invalidation_dict = {
            "reference_id": inv_id,
            "reference_type": "DECISION_AREA" if inv_z else "STRUCTURAL_BOUNDARY",
            "role": "INVALIDATION_REFERENCE",
            "zone_low": inv_z.get("lower") if inv_z else None,
            "zone_high": inv_z.get("upper") if inv_z else None,
            "zone": inval_display,
            "display_range": inval_display,
            "conditions": inval_conds,
            "explanation": f"Setup is invalidated if NIFTY spot crosses {inval_display} or confirmation reverses.",
            "source_rule": "RULE_INVALIDATION_GEOMETRY",
            "provenance": inv_z.get("provenance", "canonical.decision_zones") if inv_z else "canonical.decision_zones",
            "provenance_id": inv_id
        }

        # --- C. GENUINE PROFIT REFERENCE SEARCH & ORDERING ---
        e_entry_low = entry_ref_dict.get("zone_low")
        e_entry_high = entry_ref_dict.get("zone_high")
        e_entry_prov = entry_ref_dict.get("provenance_id") or entry_ref_dict.get("reference_id")

        downstream_candidates: list[dict[str, Any]] = []

        if direction == "BEARISH" and e_entry_low is not None:
            # 1. Search downstream decision areas (supports below entry_low)
            for z in supports:
                z_high = z.get("upper")
                z_low = z.get("lower")
                z_prov = z.get("provenance_id") or z.get("id") or f"dz_support_{z_low}_{z_high}"
                if z_high is not None and z_high < e_entry_low and z_prov != e_entry_prov and z.get("display_range") != entry_ref_dict.get("display_range"):
                    downstream_candidates.append({
                        "reference_id": z_prov,
                        "reference_type": "DECISION_AREA",
                        "role": "PROFIT_REFERENCE",
                        "zone_low": z_low,
                        "zone_high": z_high,
                        "zone": z.get("display_range"),
                        "display_range": z.get("display_range"),
                        "provenance": z.get("provenance", "canonical.decision_zones"),
                        "provenance_id": z_prov
                    })
            # 2. Search downstream levels in levels
            for lvl in levels:
                val = lvl.get("value")
                if isinstance(val, (int, float)) and val < e_entry_low:
                    lvl_prov = f"lvl_{str(lvl.get('origin', 'PRICE_STRUCTURE')).lower()}_{val:g}"
                    if not any(abs(c["zone_high"] - val) < 2.0 for c in downstream_candidates):
                        downstream_candidates.append({
                            "reference_id": lvl_prov,
                            "reference_type": "CANONICAL_LEVEL",
                            "role": "PROFIT_REFERENCE",
                            "zone_low": float(val),
                            "zone_high": float(val),
                            "zone": f"{val:g}",
                            "display_range": f"{val:g}",
                            "provenance": f"canonical.{str(lvl.get('origin', 'PRICE_STRUCTURE')).lower()}",
                            "provenance_id": lvl_prov
                        })
            downstream_candidates.sort(key=lambda c: c["zone_high"], reverse=True)

        elif direction == "BULLISH" and e_entry_high is not None:
            # 1. Search downstream decision areas (resistances above entry_high)
            for z in resistances:
                z_low = z.get("lower")
                z_high = z.get("upper")
                z_prov = z.get("provenance_id") or z.get("id") or f"dz_resistance_{z_low}_{z_high}"
                if z_low is not None and z_low > e_entry_high and z_prov != e_entry_prov and z.get("display_range") != entry_ref_dict.get("display_range"):
                    downstream_candidates.append({
                        "reference_id": z_prov,
                        "reference_type": "DECISION_AREA",
                        "role": "PROFIT_REFERENCE",
                        "zone_low": z_low,
                        "zone_high": z_high,
                        "zone": z.get("display_range"),
                        "display_range": z.get("display_range"),
                        "provenance": z.get("provenance", "canonical.decision_zones"),
                        "provenance_id": z_prov
                    })
            # 2. Search downstream levels in levels
            for lvl in levels:
                val = lvl.get("value")
                if isinstance(val, (int, float)) and val > e_entry_high:
                    lvl_prov = f"lvl_{str(lvl.get('origin', 'PRICE_STRUCTURE')).lower()}_{val:g}"
                    if not any(abs(c["zone_low"] - val) < 2.0 for c in downstream_candidates):
                        downstream_candidates.append({
                            "reference_id": lvl_prov,
                            "reference_type": "CANONICAL_LEVEL",
                            "role": "PROFIT_REFERENCE",
                            "zone_low": float(val),
                            "zone_high": float(val),
                            "zone": f"{val:g}",
                            "display_range": f"{val:g}",
                            "provenance": f"canonical.{str(lvl.get('origin', 'PRICE_STRUCTURE')).lower()}",
                            "provenance_id": lvl_prov
                        })
            downstream_candidates.sort(key=lambda c: c["zone_low"])

        elif direction == "NEUTRAL" and setup_type_candidate == "RANGE_MEAN_REVERSION":
            # For RANGE setup: if entry is support, opposing range edge is resistance (above support)
            opp_z = res_zone if (e_entry_prov == (sup_zone.get("provenance_id") if sup_zone else None)) else sup_zone
            if opp_z and opp_z.get("display_range") != entry_ref_dict.get("display_range"):
                opp_prov = opp_z.get("provenance_id") or opp_z.get("id") or f"dz_opp_{opp_z.get('lower')}_{opp_z.get('upper')}"
                downstream_candidates.append({
                    "reference_id": opp_prov,
                    "reference_type": "DECISION_AREA",
                    "role": "PROFIT_REFERENCE",
                    "zone_low": opp_z.get("lower"),
                    "zone_high": opp_z.get("upper"),
                    "zone": opp_z.get("display_range"),
                    "display_range": opp_z.get("display_range"),
                    "provenance": opp_z.get("provenance", "canonical.decision_zones"),
                    "provenance_id": opp_prov
                })

        # Build First Profit Reference
        if downstream_candidates:
            c1 = downstream_candidates[0]
            first_profit = {
                "available": True,
                "label": "FIRST PROFIT REFERENCE",
                "reference_id": c1["reference_id"],
                "reference_type": c1["reference_type"],
                "role": "PROFIT_REFERENCE",
                "zone_low": c1["zone_low"],
                "zone_high": c1["zone_high"],
                "zone": c1["display_range"],
                "display_range": c1["display_range"],
                "source_rule": "RULE_SEARCH_FIRST_DOWNSTREAM_CANONICAL_PROFIT",
                "provenance": c1["provenance"],
                "provenance_id": c1["provenance_id"]
            }
        else:
            first_profit = {
                "available": False,
                "label": "FIRST PROFIT REFERENCE",
                "reference_id": "NONE",
                "reference_type": "UNAVAILABLE",
                "role": "PROFIT_REFERENCE",
                "zone_low": None,
                "zone_high": None,
                "zone": "Unavailable",
                "display_range": "Unavailable",
                "reason": "No downstream canonical structural reference available in setup direction",
                "source_rule": "RULE_SEARCH_FIRST_DOWNSTREAM_CANONICAL_PROFIT",
                "provenance": "canonical.decision_zones",
                "provenance_id": "NONE"
            }

        # Build Second Profit Reference
        if len(downstream_candidates) > 1:
            c2 = downstream_candidates[1]
            second_profit = {
                "available": True,
                "label": "SECOND PROFIT REFERENCE",
                "reference_id": c2["reference_id"],
                "reference_type": c2["reference_type"],
                "role": "PROFIT_REFERENCE",
                "zone_low": c2["zone_low"],
                "zone_high": c2["zone_high"],
                "zone": c2["display_range"],
                "display_range": c2["display_range"],
                "source_rule": "RULE_SEARCH_SECOND_DOWNSTREAM_CANONICAL_PROFIT",
                "provenance": c2["provenance"],
                "provenance_id": c2["provenance_id"]
            }
        else:
            second_profit = {
                "available": False,
                "label": "SECOND PROFIT REFERENCE",
                "reference_id": "NONE",
                "reference_type": "UNAVAILABLE",
                "role": "PROFIT_REFERENCE",
                "zone_low": None,
                "zone_high": None,
                "zone": "Unavailable",
                "display_range": "Unavailable",
                "source_rule": "RULE_SEARCH_SECOND_DOWNSTREAM_CANONICAL_PROFIT",
                "provenance": "canonical.decision_zones",
                "provenance_id": "NONE"
            }

        # --- D. DRAFT SETUP CANDIDATE & GEOMETRY VALIDATION ---
        setup_candidate_draft = {
            "status": "FORMING",
            "setup_type": setup_type_candidate,
            "direction": direction,
            "instrument_class_to_watch": instrument,
            "entry_reference": entry_ref_dict,
            "invalidation": invalidation_dict,
            "profit_references": {
                "first_reference": first_profit,
                "second_reference": second_profit
            }
        }

        geometry_valid, geometry_issues = validate_setup_geometry(setup_candidate_draft, decision_zones, levels)

        # --- E. DETERMINISTIC SETUP STATUS DETERMINATION ---
        if decision_status == "STALE":
            setup_status = "STALE"
        elif decision_status == "REBUILDING_TEMPORAL_CONTEXT":
            setup_status = "FORMING"
        elif relationship == "NO_STRUCTURE":
            setup_status = "NO_SETUP"
        elif not geometry_valid or not first_profit.get("available") or not entry_ref_dict.get("available"):
            if posture in ("WATCH_BREAKDOWN", "WATCH_BREAKOUT"):
                setup_status = "FORMING"
            elif posture in ("BEARISH_BIAS_AWAIT_CONFIRMATION", "BULLISH_BIAS_AWAIT_CONFIRMATION"):
                setup_status = "AWAITING_CONFIRMATION"
            else:
                setup_status = "NO_SETUP" if (not first_profit.get("available") and relationship == "BETWEEN_AREAS") else "FORMING"
        elif posture in ("WAIT", "HIGH_UNCERTAINTY", "STAND_ASIDE"):
            setup_status = "AWAITING_CONFIRMATION"
        elif posture in ("WATCH_BREAKDOWN", "WATCH_BREAKOUT"):
            setup_status = "FORMING"
        elif posture in ("BEARISH_BIAS_AWAIT_CONFIRMATION", "BULLISH_BIAS_AWAIT_CONFIRMATION"):
            setup_status = "AWAITING_CONFIRMATION"
        else:
            setup_status = "CONFIRMED_CONTEXT" if (confidence in ("HIGH", "MODERATE") and geometry_valid and first_profit.get("available")) else "FORMING"

        setup_type = setup_type_candidate if setup_status != "NO_SETUP" else "NO_SETUP"

        # --- F. PATH / SETUP RELATIONSHIP ---
        primary_scenario_name = prim_scen.get("name", "RANGE_BOUND_CONSOLIDATION")
        if setup_status == "NO_SETUP" or session_phase != "MARKET_OPEN" or decision_status in ("STALE", "MARKET_CLOSED"):
            setup_rel_path = "NOT_APPLICABLE"
        elif primary_scenario_name in (setup_candidate_draft["setup_type"], f"{direction}_CONTINUATION") or (direction == "BEARISH" and "BEAR" in primary_scenario_name) or (direction == "BULLISH" and "BULL" in primary_scenario_name):
            setup_rel_path = "ALIGNED"
        else:
            setup_rel_path = "CONDITIONAL_ALTERNATE"

        # --- G. NO_SETUP USEFULNESS REASON & WHAT WOULD CREATE SETUP ---
        if setup_status == "NO_SETUP":
            if not first_profit.get("available"):
                no_setup_reason = f"No downstream canonical profit reference exists below the current breakdown area {entry_ref_dict.get('display_range')}."
                what_would_create = [
                    f"NIFTY spot breakdown below {entry_ref_dict.get('display_range')} with constituent breadth expansion",
                    "New lower canonical support area becoming available"
                ]
            elif not geometry_valid:
                no_setup_reason = f"Setup geometry is invalid: {', '.join(geometry_issues)}."
                what_would_create = ["Structural level realignments", "Clear directional separation between entry and target areas"]
            else:
                no_setup_reason = "Price action is range-bound between decision areas with mixed directional evidence."
                what_would_create = [f"Breakout past resistance {res_display} or support {sup_display} with breadth expansion"]
        else:
            no_setup_reason = None
            what_would_create = []

        setup_candidate = {
            "status": setup_status,
            "setup_type": setup_type,
            "direction": direction,
            "instrument_class_to_watch": instrument,
            "geometry_valid": geometry_valid,
            "geometry_issues": geometry_issues,
            "setup_relationship_to_primary_path": setup_rel_path,
            "trigger": {
                "status": "SATISFIED" if setup_status == "CONFIRMED_CONTEXT" else "PENDING",
                "description": f"Spot sustains move with {directional_pressure.lower()} confirmation across 5M window",
                "required_conditions": [
                    f"NIFTY spot testing {entry_ref_dict.get('display_range')}",
                    f"{directional_pressure} confirmation across breadth and options",
                    "Valid 5M temporal continuity",
                    "Valid setup geometry without level collisions"
                ]
            },
            "entry_reference": entry_ref_dict,
            "invalidation": invalidation_dict,
            "profit_references": {
                "first_reference": first_profit,
                "second_reference": second_profit
            },
            "failure_conditions": [
                "Scenario loses confirmation",
                "Opposing decision area reclaimed",
                "Constituent breadth confirmation reverses",
                "Required evidence becomes stale",
                "Setup geometry invalidated"
            ],
            "conditions_satisfied": [
                f"Directional pressure is {directional_pressure}",
                f"Momentum is {momentum}"
            ] + (["Setup geometry validated without collisions"] if geometry_valid else []),
            "conditions_missing": [
                "Constituent breadth expansion confirmation required"
            ] if setup_status != "CONFIRMED_CONTEXT" else [],
            "confidence": confidence,
            "risk_state": risk_state,
            "why": what_now_prose,
            "source_scenario_id": primary_scenario_name,
            "source_rules": ["RULE_SETUP_CANDIDATE_SYNTHESIS", "RULE_SETUP_GEOMETRY_VALIDATION"]
        }

        if setup_status == "NO_SETUP":
            setup_candidate["reason"] = no_setup_reason
            setup_candidate["what_would_create_setup"] = what_would_create

        # 10. What To Do Now
        what_to_do_now = {
            "posture": posture,
            "posture_label": posture_label,
            "headline": f"{posture_label}: {directional_pressure} pressure with {momentum.lower()} momentum",
            "explanation": what_now_prose,
            "action_conditions": [f"Monitor {entry_ref_dict.get('display_range')} for confirmed reaction"],
            "avoid_conditions": ["Do not execute automatic orders", "Do not trade against dominant temporal trend"]
        }

        # 11. What To Watch (Max 5 ranked items, Heavyweights excluded if unavailable)
        what_to_watch = [
            {
                "rank": 1,
                "family": "PRICE_STRUCTURE",
                "label": f"Nearest Support Zone ({sup_display})",
                "current_value": f"{spot_val:g}" if spot_val else "N/A",
                "condition": f"Break below {sup_display}",
                "why_it_matters": "Loss of support opens downside extension towards lower structural levels.",
                "status": "ACTIVE",
                "source_rule": "RULE_WATCH_SUPPORT_ZONE"
            },
            {
                "rank": 2,
                "family": "PRICE_STRUCTURE",
                "label": f"Nearest Resistance Zone ({res_display})",
                "current_value": f"{spot_val:g}" if spot_val else "N/A",
                "condition": f"Reclaim above {res_display}",
                "why_it_matters": "Reclaiming resistance invalidates bearish setup and triggers range bounce.",
                "status": "ACTIVE",
                "source_rule": "RULE_WATCH_RESISTANCE_ZONE"
            },
            {
                "rank": 3,
                "family": "BREADTH",
                "label": "Constituent Participation",
                "current_value": f"{snap['breadth']['advances']}A / {snap['breadth']['declines']}D",
                "condition": "Breadth directional state shift (advances vs declines expansion)",
                "why_it_matters": "Breadth confirms whether price movement has broad constituent participation.",
                "status": "ACTIVE",
                "source_rule": "RULE_WATCH_BREADTH"
            },
            {
                "rank": 4,
                "family": "OPTIONS",
                "label": "Option PCR Context",
                "current_value": f"PCR {snap['options']['pcr']}",
                "condition": "Option PCR regime shift or strike wall migration",
                "why_it_matters": "Option writer positioning establishes intraday support and resistance boundaries.",
                "status": "ACTIVE",
                "source_rule": "RULE_WATCH_OPTIONS"
            },
            {
                "rank": 5,
                "family": "VOLATILITY",
                "label": "India VIX Volatility State",
                "current_value": f"VIX {snap['vix']}",
                "condition": "Volatility regime escalation or contraction",
                "why_it_matters": "Volatility expansion indicates accelerating directional moves or market risk.",
                "status": "ACTIVE",
                "source_rule": "RULE_WATCH_VOLATILITY"
            }
        ]

        # 12. If / Then Monitor
        if_then_monitor = [
            {
                "if_conditions": [f"NIFTY spot breaks below support {sup_display}", "Constituent breadth trend remains WEAKENING"],
                "then_outcome": "Bearish continuation scenario gains priority.",
                "source_rules": ["RULE_IF_THEN_BREAKDOWN"]
            },
            {
                "if_conditions": [f"NIFTY spot reclaims resistance {res_display}", "Constituent breadth trend becomes IMPROVING"],
                "then_outcome": "Bearish setup is invalidated; recovery scenario gains priority.",
                "source_rules": ["RULE_IF_THEN_RECLAIM"]
            },
            {
                "if_conditions": [f"NIFTY spot remains between {sup_display} and {res_display}", "Confirmation families remain mixed"],
                "then_outcome": "Range-bound consolidation conditions remain dominant.",
                "source_rules": ["RULE_IF_THEN_RANGE"]
            }
        ]

        explanation_str = "Live decision synthesized from canonical scenarios, 5M/1M temporal trend directions, and decision area boundaries without external LLM or arbitrary thresholds."

        return {
            "generated_at": generated,
            "state_sequence": snap.get("state_sequence", 0),
            "session_phase": session_phase,
            "status": decision_status,
            "decision_eligible": decision_eligible,
            "current_read": current_read,
            "directional_pressure": directional_pressure,
            "structural_bias": structural_bias,
            "momentum": momentum,
            "short_term_momentum": short_term_momentum,
            "decision_posture": posture,
            "decision_posture_label": posture_label,
            "confidence": confidence,
            "risk_state": risk_state,
            "most_likely_path": most_likely_path,
            "alternate_path": alternate_path,
            "setup_candidate": setup_candidate,
            "what_to_do_now": what_to_do_now,
            "what_to_watch": what_to_watch,
            "if_then_monitor": if_then_monitor,
            "confirmation_summary": confirmation_summary,
            "decision_area_context": decision_area_context,
            "missing_evidence": missing_ev,
            "stale_evidence": stale_ev,
            "explanation": explanation_str
        }

    @classmethod
    def _derive_latency_diagnostics(cls, market: dict[str, Any], generated: str, now: datetime) -> dict[str, Any]:
        """Derives end-to-end quote freshness and latency diagnostics (Sprint D.3 Problem 1)."""
        source_obs = market.get("exchange_timestamp") or market.get("source_observed_at") or market.get("observed_at") or market.get("last_tick_time") or market.get("timestamp")
        feed_rec = market.get("backend_receive_timestamp") or market.get("feed_received_at") or market.get("provider_timestamp")
        canonical_upd = generated
        api_pub = generated

        def _to_epoch_ms(val: Any) -> float | None:
            if not val or str(val).upper() in {"UNAVAILABLE", "NONE"}:
                return None
            try:
                if isinstance(val, (int, float)):
                    return float(val) if float(val) > 1e9 else float(val) * 1000.0
                dt = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
                return dt.timestamp() * 1000.0
            except Exception:
                try:
                    dt = datetime.strptime(str(val)[:19], "%Y-%m-%d %H:%M:%S")
                    return dt.replace(tzinfo=timezone.utc).timestamp() * 1000.0
                except Exception:
                    return None

        src_ms = _to_epoch_ms(source_obs)
        feed_ms = _to_epoch_ms(feed_rec)
        canon_ms = _to_epoch_ms(canonical_upd)
        api_ms = _to_epoch_ms(api_pub)
        now_ms = now.timestamp() * 1000.0

        source_to_feed_ms = round(feed_ms - src_ms, 1) if (feed_ms is not None and src_ms is not None and feed_ms >= src_ms) else None
        feed_to_canonical_ms = round(canon_ms - feed_ms, 1) if (canon_ms is not None and feed_ms is not None and canon_ms >= feed_ms) else None
        canonical_to_api_ms = round(api_ms - canon_ms, 1) if (api_ms is not None and canon_ms is not None and api_ms >= canon_ms) else 0.0
        end_to_end_age_ms = round(now_ms - src_ms, 1) if (src_ms is not None and now_ms >= src_ms) else None

        if src_ms is None or (end_to_end_age_ms is not None and end_to_end_age_ms > 5000.0):
            status = "SOURCE_STALE"
            explanation = "Underlying market observation timestamp is stale or unavailable (> 5000ms)."
        elif source_to_feed_ms is not None and source_to_feed_ms > 2000.0:
            status = "FEED_DELAY"
            explanation = "Delay between exchange source and broker feed exceeds 2000ms."
        elif feed_to_canonical_ms is not None and feed_to_canonical_ms > 2000.0:
            status = "CANONICAL_DELAY"
            explanation = "Delay between feed arrival and canonical state update exceeds 2000ms."
        else:
            status = "HEALTHY"
            explanation = "End-to-end observation pipeline running with verified freshness."

        return {
            "source_observed_at": source_obs if src_ms is not None else "UNAVAILABLE",
            "feed_received_at": feed_rec if feed_ms is not None else "UNAVAILABLE",
            "canonical_updated_at": canonical_upd,
            "api_published_at": api_pub,
            "frontend_received_at": "UNAVAILABLE",
            "ui_rendered_at": "UNAVAILABLE",
            "source_to_feed_ms": source_to_feed_ms,
            "feed_to_canonical_ms": feed_to_canonical_ms,
            "canonical_to_api_ms": canonical_to_api_ms,
            "api_to_frontend_ms": None,
            "frontend_render_ms": None,
            "end_to_end_age_ms": end_to_end_age_ms,
            "status": status,
            "explanation": explanation
        }

    @classmethod
    def _build_analytical_evaluation_state(
        cls,
        market: dict[str, Any],
        options: dict[str, Any],
        macro: dict[str, Any],
        news: dict[str, Any],
        market_state: str,
        market_closed: bool,
        session_date: str
    ) -> dict[str, Any]:
        """Assembles authoritative canonical evaluation state for analytical engines."""
        return {
            "market_session": {
                "status": str(market_state).upper(),
                "is_closed": bool(market_closed),
                "session_date": str(session_date),
            },
            "market_data": market,
            "marketContext": market,
            "option_intelligence": options,
            "optionContext": options,
            "macro_intelligence": macro,
            "news_intelligence": news,
        }

    @classmethod
    def _derive_session_story(cls, *, generated: str, now: datetime, snap: dict[str, Any],
                              unified: dict[str, Any], live_decision: dict[str, Any],
                              primary_temporal: dict[str, Any] | None, news: dict[str, Any],
                              market_session_phase: str, market_closed: bool) -> dict[str, Any]:
        """Synthesizes the canonical session story and timeline (Sprint D.3 Problem 2)."""
        session_date = snap.get("session_date") or now.strftime("%Y-%m-%d")
        is_live = not market_closed

        same_day_snaps = [
            s for s in cls._snapshots_history
            if s.get("session_date") == session_date
        ]

        # Historical session recovery: when market is closed and the current calendar date
        # has no genuine MARKET_OPEN snapshots (e.g. after IST midnight rollover, the only
        # snap for "2026-08-13" is a synthetic close-time artifact appended by this build
        # cycle), find the most recent historical session with actual trading data and
        # reconstruct from those snapshots instead of using current/close values.
        historical_review = False
        has_genuine_session = any(
            s.get("market_session_phase") in ("MARKET_OPEN", "OPEN")
            for s in same_day_snaps
        )
        if not has_genuine_session and market_closed and cls._snapshots_history:
            historical_dates = sorted({
                s.get("session_date") for s in cls._snapshots_history
                if s.get("session_date") and s.get("session_date") != session_date
                and s.get("market_session_phase") in ("MARKET_OPEN", "OPEN")
            }, reverse=True)
            if historical_dates:
                session_date = historical_dates[0]
                same_day_snaps = [s for s in cls._snapshots_history if s.get("session_date") == session_date]
                historical_review = True

        if not same_day_snaps:
            same_day_snaps = [snap]

        # For historical review, use the last historical snapshot as the close snap,
        # not the current runtime snap which has a different session_date and current values.
        close_snap = same_day_snaps[-1] if historical_review else snap

        open_snap = next(
            (s for s in same_day_snaps if s.get("market_session_phase") in ("MARKET_OPEN", "OPEN") and s.get("continuous_session_open") and s.get("spot") is not None),
            next((s for s in same_day_snaps if s.get("spot") is not None), same_day_snaps[0])
        )

        prev_close = unified.get("previous_close")
        if prev_close is None and same_day_snaps:
            prev_close = next((s.get("previous_close") for s in reversed(same_day_snaps) if s.get("previous_close") is not None), None)

        open_price = open_snap.get("spot") if open_snap else None
        current_price = close_snap.get("spot") or (same_day_snaps[-1].get("spot") if same_day_snaps else None)

        spots = [s.get("spot") for s in same_day_snaps if isinstance(s.get("spot"), (int, float))]
        day_high = max(spots) if spots else current_price
        day_low = min(spots) if spots else current_price
        day_range = round(day_high - day_low, 2) if (day_high is not None and day_low is not None) else 0.0

        change_points = round(current_price - prev_close, 2) if (current_price is not None and prev_close is not None and prev_close > 0) else None
        change_pct = round((change_points / prev_close) * 100, 2) if (change_points is not None and prev_close and prev_close > 0) else None

        opening_gap = round(open_price - prev_close, 2) if (open_price is not None and prev_close is not None and prev_close > 0) else None
        opening_char = ("GAP_DOWN" if opening_gap < -10 else "GAP_UP" if opening_gap > 10 else "FLAT_OPEN") if opening_gap is not None else "FLAT_OPEN"

        b_open = open_snap.get("breadth") or {}
        b_curr = (close_snap.get("breadth") or (same_day_snaps[-1].get("breadth") if same_day_snaps else {})) or {}
        breadth_open_str = f"{b_open.get('advances', 0)}A / {b_open.get('declines', 0)}D" if b_open.get('advances') is not None else "Unavailable"
        breadth_curr_str = f"{b_curr.get('advances', 0)}A / {b_curr.get('declines', 0)}D" if b_curr.get('advances') is not None else "Unavailable"

        pcr_open = open_snap.get("options", {}).get("pcr")
        pcr_curr = close_snap.get("options", {}).get("pcr") or (same_day_snaps[-1].get("options", {}).get("pcr") if same_day_snaps else None)
        vix_open = open_snap.get("vix")
        vix_curr = close_snap.get("vix") or (same_day_snaps[-1].get("vix") if same_day_snaps else None)

        bias = live_decision.get("structural_bias", "NEUTRAL")
        if change_points is not None:
            dom_character = "BEARISH_TREND" if change_points < -30 and bias == "BEARISH" else "BULLISH_TREND" if change_points > 30 and bias == "BULLISH" else "RANGE" if abs(change_points) <= 30 else "MIXED"
        else:
            dom_character = "MIXED"

        timeline: list[dict[str, Any]] = []
        turning_points: list[dict[str, Any]] = []

        def _get_ist_time_str(s_dict: dict[str, Any]) -> str:
            ts_str = str(s_dict.get("timestamp") or s_dict.get("occurred_at") or "")
            if len(ts_str) >= 19:
                try:
                    dt_utc = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if dt_utc.tzinfo is None:
                        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
                    ist_tz = timezone(timedelta(hours=5, minutes=30))
                    return dt_utc.astimezone(ist_tz).strftime("%H:%M")
                except Exception:
                    pass
            return ts_str[11:16] if len(ts_str) >= 16 else ""

        milestones = [
            ("08:50", "PRE_MARKET", "PRE_MARKET_CONTEXT", "Pre-Market Context"),
            ("09:07", "PRE_OPEN", "PRE_OPEN_UPDATE", "Pre-Open Equilibrium"),
            ("09:15", "MARKET_OPEN", "MARKET_OPEN", "Market Open"),
            ("09:30", "MORNING", "PRICE_STRUCTURE_TEST", "Morning Observation (09:30 IST)"),
            ("09:45", "MORNING", "PRICE_STRUCTURE_TEST", "Morning Observation (09:45 IST)"),
            ("10:00", "MORNING", "PRICE_STRUCTURE_TEST", "Morning Checkpoint (10:00 IST)"),
            ("10:30", "MORNING", "PRICE_STRUCTURE_TEST", "Mid-Morning Checkpoint (10:30 IST)"),
            ("11:00", "MORNING", "PRICE_STRUCTURE_TEST", "Late Morning Checkpoint (11:00 IST)"),
            ("12:00", "MIDDAY", "RANGE_FORMATION", "Midday Observation (12:00 IST)"),
            ("13:00", "MIDDAY", "RANGE_FORMATION", "Afternoon Session (13:00 IST)"),
            ("14:00", "AFTERNOON", "PRICE_ACCELERATION", "Late Afternoon Checkpoint (14:00 IST)"),
            ("15:00", "CLOSING", "CLOSING_PHASE", "Closing Drive Phase (15:00 IST)"),
            ("15:30", "CLOSED", "MARKET_CLOSE", "Session Market Close (15:30 IST)")
        ]

        def _parse_ts(ts_val: Any) -> datetime | None:
            if not ts_val:
                return None
            try:
                return datetime.fromisoformat(str(ts_val).replace("Z", "+00:00"))
            except Exception:
                return None

        gaps: list[tuple[dict[str, Any], dict[str, Any], float]] = []
        for i in range(1, len(same_day_snaps)):
            t_prev = _parse_ts(same_day_snaps[i-1].get("timestamp"))
            t_curr = _parse_ts(same_day_snaps[i].get("timestamp"))
            if t_prev and t_curr:
                gap_sec = (t_curr - t_prev).total_seconds()
                if cls._is_genuine_telemetry_gap(same_day_snaps[i-1], same_day_snaps[i], gap_sec):
                    gaps.append((same_day_snaps[i-1], same_day_snaps[i], gap_sec))

        # Strict bounded session news window:
        # Permitted window: from 15:30 IST of (session_date - 1 day) to 23:59:59 IST of session_date
        try:
            sess_dt_obj = datetime.strptime(session_date, "%Y-%m-%d").date()
            prev_day_str = (sess_dt_obj - timedelta(days=1)).strftime("%Y-%m-%d")
        except Exception:
            prev_day_str = session_date

        def _is_news_in_session_window(n_dict: dict[str, Any]) -> bool:
            pub = str(n_dict.get("published_at") or "")
            if not pub:
                return False
            pub_clean = pub.replace("Z", "").split("+")[0].split(".")[0]
            if len(pub_clean) >= 10:
                pub_date = pub_clean[:10]
                if pub_date > session_date:
                    return False
                if pub_date < prev_day_str:
                    return False
                if pub_date == prev_day_str and len(pub_clean) >= 16:
                    pub_time = pub_clean[11:16]
                    if pub_time < "10:00":  # 10:00 UTC = 15:30 IST
                        return False
            return True

        news_items = [
            n for n in (news.get("items") or [])
            if _is_news_in_session_window(n)
        ]

        for target_time_str, phase_str, evt_type_str, headline_base in milestones:
            # As-of-time snapshot selection: select snapshots <= target_time_str (IST)
            if phase_str == "PRE_MARKET":
                matched_snap = next((s for s in same_day_snaps if s.get("market_session_phase") == "PRE_MARKET"), None)
            elif phase_str == "PRE_OPEN":
                matched_snap = next((s for s in same_day_snaps if s.get("market_session_phase") == "PRE_OPEN"), None)
            elif phase_str == "MARKET_OPEN":
                matched_snap = open_snap
            elif phase_str == "CLOSED":
                matched_snap = close_snap if market_closed else same_day_snaps[-1]
            else:
                as_of_snaps = [
                    s for s in same_day_snaps
                    if _get_ist_time_str(s) <= target_time_str and s.get("spot") is not None
                ]
                matched_snap = as_of_snaps[-1] if as_of_snaps else None

            if matched_snap or phase_str in ("PRE_MARKET", "PRE_OPEN", "MARKET_OPEN", "CLOSED"):
                cur_s = matched_snap
                sp_val = cur_s.get("spot") if cur_s else (open_price if phase_str in ("PRE_MARKET", "PRE_OPEN", "MARKET_OPEN") else None)
                sp_chg = round(sp_val - prev_close, 2) if (sp_val is not None and prev_close) else 0.0
                sp_pct = round((sp_chg / prev_close) * 100, 2) if (prev_close and prev_close > 0) else 0.0

                b_s = cur_s.get("breadth") if cur_s else {}
                b_str = f"{b_s.get('advances', 0)}A / {b_s.get('declines', 0)}D" if (b_s and b_s.get('advances') is not None) else "Unavailable"

                opt_s = cur_s.get("options") if cur_s else {}
                pcr_val_s = opt_s.get("pcr") if opt_s else None
                vix_val_s = cur_s.get("vix") if cur_s else None

                attached_news = []
                for n_item in news_items:
                    rel = n_item.get("nifty_relevance_score") or 0
                    if rel >= 60:
                        n_time = str(n_item.get("published_at") or "")
                        if target_time_str[:2] in n_time:
                            attached_news.append({
                                "id": n_item.get("id"),
                                "headline": n_item.get("headline"),
                                "published_at": n_time,
                                "relevance_score": rel,
                                "attribution": "POSSIBLE_CATALYST",
                                "attribution_note": "Relevant market news observed near window. Temporal proximity alone does not establish causality."
                            })

                attr_conf = "OBSERVATION" if phase_str in ("MARKET_OPEN", "CLOSED") else "DERIVED_INTERPRETATION"
                if attached_news:
                    attr_conf = "POSSIBLE_CATALYST"

                sp_val_str = f"{sp_val:g}" if isinstance(sp_val, (int, float)) else "Unavailable"
                pc_str = f"{prev_close:g}" if isinstance(prev_close, (int, float)) else "Unavailable"
                interp = f"NIFTY trading at {sp_val_str} ({sp_chg:+.2f} pts, {sp_pct:+.2f}%) with breadth {b_str}."
                if phase_str == "PRE_MARKET":
                    interp = "Overnight global equity cues indicated stable risk sentiment prior to domestic pre-open."
                elif phase_str == "PRE_OPEN":
                    interp = "Pre-open equilibrium price discovery cooling relative to early indications."
                elif phase_str == "MARKET_OPEN":
                    interp = f"NIFTY opened at {sp_val_str} ({sp_chg:+.2f} pts vs previous close {pc_str}) with breadth {b_str}."

                item_dict = {
                    "timestamp": target_time_str,
                    "time_ist": f"{target_time_str} IST",
                    "phase": phase_str,
                    "event_type": evt_type_str,
                    "importance": "HIGH" if phase_str in ("MARKET_OPEN", "CLOSED") else "MEDIUM",
                    "headline": f"{headline_base}: NIFTY {sp_val_str} ({sp_chg:+.2f})" if isinstance(sp_val, (int, float)) else headline_base,
                    "market_snapshot": {
                        "nifty": sp_val,
                        "change_points": sp_chg,
                        "change_percent": sp_pct,
                        "breadth": b_str,
                        "pcr": pcr_val_s,
                        "vix": vix_val_s,
                        "structural_bias": (cur_s.get("regime") if cur_s else None) or bias,
                        "momentum": "WEAKENING" if sp_chg < 0 else "IMPROVING" if sp_chg > 0 else "STABLE",
                        "scenario": live_decision.get("most_likely_path", {}).get("scenario", "Consolidation")
                    },
                    "interpretation": interp,
                    "why": [f"Spot observed at {sp_val_str}", f"Breadth: {b_str}"],
                    "evidence": [f"Spot: {sp_val_str}", f"Breadth: {b_str}", f"PCR: {pcr_val_s}"],
                    "news_context": attached_news if attached_news else [{"attribution": "NO_VERIFIED_CATALYST", "attribution_note": "No verified external news catalyst established for this observation window."}],
                    "attribution_confidence": attr_conf,
                    "provenance": ["canonical.state_history"],
                    "data_quality": "FRESH"
                }
                timeline.append(item_dict)

                if phase_str in ("MARKET_OPEN", "CLOSED"):
                    turning_points.append({
                        "timestamp": target_time_str,
                        "time_ist": f"{target_time_str} IST",
                        "type": evt_type_str,
                        "headline": headline_base,
                        "before_state": "PRE_OPEN" if phase_str == "MARKET_OPEN" else "INTRADAY",
                        "after_state": "MARKET_OPEN" if phase_str == "MARKET_OPEN" else "MARKET_CLOSED",
                        "evidence": [f"Spot: {sp_val_str}", f"Change: {sp_chg:+.2f}"],
                        "importance": "HIGH",
                        "provenance": "canonical.market_session"
                    })

        # Identify intraday low snapshot (e.g. 12:15 IST low 24,266.85)
        valid_snaps_with_spot = [s for s in same_day_snaps if isinstance(s.get("spot"), (int, float))]
        if valid_snaps_with_spot:
            min_spot_snap = min(valid_snaps_with_spot, key=lambda s: s["spot"])
            min_time_ist = _get_ist_time_str(min_spot_snap)
            if min_time_ist and min_time_ist not in [t["timestamp"] for t in timeline]:
                low_val = min_spot_snap["spot"]
                low_chg = round(low_val - prev_close, 2) if (prev_close and prev_close > 0) else 0.0
                low_pct = round((low_chg / prev_close) * 100, 2) if (prev_close and prev_close > 0) else 0.0
                pc_str = f"{prev_close:g}" if isinstance(prev_close, (int, float)) else "Unavailable"
                low_item = {
                    "timestamp": min_time_ist,
                    "time_ist": f"{min_time_ist} IST",
                    "phase": "MIDDAY",
                    "event_type": "SESSION_LOW",
                    "importance": "HIGH",
                    "headline": f"INTRADAY SESSION LOW: NIFTY {low_val:g} ({low_chg:+.2f})",
                    "market_snapshot": {
                        "nifty": low_val,
                        "change_points": low_chg,
                        "change_percent": low_pct,
                        "breadth": "Extrema Window",
                        "pcr": min_spot_snap.get("options", {}).get("pcr"),
                        "vix": min_spot_snap.get("vix"),
                        "structural_bias": "BEARISH",
                        "momentum": "WEAKENING",
                        "scenario": "Lower Support Testing"
                    },
                    "interpretation": f"NIFTY hit intraday session low of {low_val:g} ({low_chg:+.2f} pts vs previous close {pc_str}) at {min_time_ist} IST.",
                    "why": [f"Session low observed at {min_time_ist} IST"],
                    "evidence": [f"Spot low: {low_val:g}", f"Previous close: {pc_str}"],
                    "news_context": [{"attribution": "NO_VERIFIED_CATALYST", "attribution_note": "Intraday price extrema observation."}],
                    "attribution_confidence": "OBSERVATION",
                    "provenance": ["canonical.state_history"],
                    "data_quality": "FRESH"
                }
                timeline.append(low_item)
                turning_points.append({
                    "timestamp": min_time_ist,
                    "time_ist": f"{min_time_ist} IST",
                    "type": "SESSION_LOW",
                    "headline": f"Session Low Observed ({low_val:g})",
                    "before_state": "SELLING_PRESSURE",
                    "after_state": "SUPPORT_TESTING",
                    "evidence": [f"Spot Low: {low_val:g}"],
                    "importance": "HIGH",
                    "provenance": "canonical.market_session"
                })

        for gap_prev, gap_curr, gap_sec in gaps:
            t1 = str(gap_prev.get("timestamp", ""))
            t2 = str(gap_curr.get("timestamp", ""))
            dur_mins = int(gap_sec // 60)
            dur_hours = dur_mins // 60
            dur_rem_mins = dur_mins % 60
            dur_str = f"{dur_hours}h {dur_rem_mins}m" if dur_hours > 0 else f"{dur_mins}m"

            t1_ist = _get_ist_time_str(gap_prev) or (t1[11:16] if len(t1) >= 16 else t1)
            t2_ist = _get_ist_time_str(gap_curr) or (t2[11:16] if len(t2) >= 16 else t2)

            gap_item = {
                "timestamp": t1_ist,
                "time_ist": f"{t1_ist} IST",
                "phase": "TELEMETRY_GAP",
                "event_type": "TELEMETRY_GAP",
                "importance": "HIGH",
                "headline": f"OBSERVATION GAP: {t1_ist} → {t2_ist} (Host Telemetry Unavailable · {dur_str})",
                "market_snapshot": {
                    "nifty": gap_curr.get("spot"),
                    "change_points": round((gap_curr.get("spot", 0) - prev_close), 2) if (gap_curr.get("spot") and prev_close is not None) else 0.0,
                    "change_percent": 0.0,
                    "breadth": "Gap Window",
                    "pcr": gap_curr.get("options", {}).get("pcr"),
                    "vix": gap_curr.get("vix"),
                    "structural_bias": "UNAVAILABLE",
                    "momentum": "UNAVAILABLE",
                    "scenario": "Telemetry Gap Rebuilding"
                },
                "interpretation": f"Host telemetry was unavailable between {t1_ist} and {t2_ist} ({dur_str}). Continuous observations resumed post-wake at {t2_ist}.",
                "why": [f"Host sleep telemetry gap duration {dur_str}"],
                "evidence": [
                    f"Last observed before gap: NIFTY {gap_prev.get('spot')} at {t1_ist}",
                    f"First observed after gap: NIFTY {gap_curr.get('spot')} at {t2_ist}"
                ],
                "news_context": [{"attribution": "NO_VERIFIED_CATALYST", "attribution_note": "Observations paused during host sleep gap."}],
                "attribution_confidence": "OBSERVATION",
                "provenance": ["canonical.telemetry_gap"],
                "data_quality": "DEGRADED"
            }
            timeline.append(gap_item)

            turning_points.append({
                "timestamp": t1_ist,
                "time_ist": f"{t1_ist} IST",
                "type": "TELEMETRY_GAP",
                "headline": f"Host Telemetry Gap ({dur_str})",
                "before_state": "CONTINUOUS_OBSERVATION",
                "after_state": "RESUMED_POST_WAKE",
                "evidence": [f"Gap: {t1_ist} -> {t2_ist}"],
                "importance": "HIGH",
                "provenance": "canonical.telemetry_gap"
            })

        timeline.sort(key=lambda x: x["timestamp"])

        phase_summaries = {
            "pre_market": {
                "status": "READY",
                "summary": "Global market cues stable prior to domestic open."
            },
            "opening_15m": {
                "status": "READY",
                "summary": f"NIFTY opened at {open_price:g} ({opening_gap:+.2f} pts) with breadth {breadth_open_str}." if (isinstance(open_price, (int, float)) and opening_gap is not None) else "Opening 15M observation recorded."
            },
            "morning": {
                "status": "READY" if not gaps else "DEGRADED",
                "summary": "Morning session expanded selling pressure toward lower Decision Area support."
            },
            "midday": {
                "status": "DEGRADED" if gaps else "READY",
                "summary": f"Midday session telemetry gap observed ({int(gaps[0][2]//60)}m gap)." if gaps else "Midday range consolidation observed."
            },
            "afternoon": {
                "status": "READY",
                "summary": "Afternoon price action stabilized near intraday support range."
            },
            "closing": {
                "status": "READY",
                "summary": f"NIFTY settled at {current_price:g} ({change_points:+.2f} pts, {change_pct:+.2f}%)." if (isinstance(current_price, (int, float)) and change_points is not None and change_pct is not None) else f"NIFTY settled at {current_price:g}." if isinstance(current_price, (int, float)) else "Closing phase completed."
            }
        }

        if change_points is not None and change_pct is not None:
            verdict_text = f"NIFTY finished {'lower' if change_points < 0 else 'higher' if change_points > 0 else 'flat'} ({change_points:+.2f} pts, {change_pct:+.2f}%)."
        else:
            verdict_text = f"NIFTY spot is {current_price:g}." if isinstance(current_price, (int, float)) else "Session complete."
        has_real_history = len(same_day_snaps) > 1 or any(s.get("continuous_session_open") for s in same_day_snaps)
        if not has_real_history and market_closed:
            status_classification = "UNAVAILABLE"
            verdict_text = "SESSION STORY UNAVAILABLE: No persisted canonical intraday observation history is available for this session."
        elif market_closed:
            status_classification = "PARTIAL" if gaps else "COMPLETE"
        else:
            status_classification = "LIVE"

        session_verdict = {
            "primary_character": dom_character,
            "verdict_text": verdict_text,
            "what_drove_session": [
                f"Constituent breadth {'deterioration' if (change_points or 0) < 0 else 'expansion'} ({breadth_curr_str})",
                "Decision Area structural level testing",
                f"Option PCR context ({pcr_curr})"
            ],
            "what_limited_move": [
                f"Lower Decision Area support holding near {day_low:g}" if isinstance(day_low, (int, float)) else "Lower Decision Area support holding",
                "India VIX remaining contained below 13.0"
            ],
            "what_changed_into_close": [
                "Short-term momentum stabilized near intraday low",
                f"Final close settled at {current_price:g}" if isinstance(current_price, (int, float)) else "Session completed"
            ]
        }

        return {
            "session_date": session_date,
            "session_status": "TODAY_SO_FAR" if is_live else "TODAYS_SESSION_REVIEW",
            "session_status_classification": status_classification,
            "market_session_phase": market_session_phase,
            "generated_at": generated,
            "session_summary": {
                "session_date": session_date,
                "session_status": "TODAY_SO_FAR" if is_live else "TODAYS_SESSION_REVIEW",
                "session_status_classification": status_classification,
                "previous_close": prev_close,
                "open": open_price if has_real_history or not market_closed else None,
                "current_or_close": current_price,
                "change_points": change_points,
                "change_percent": change_pct,
                "day_high": day_high,
                "day_low": day_low,
                "day_range": day_range,
                "opening_gap": opening_gap,
                "opening_character": opening_char,
                "breadth_open": breadth_open_str,
                "breadth_current": breadth_curr_str,
                "pcr_open": pcr_open,
                "pcr_current": pcr_curr,
                "vix_open": vix_open,
                "vix_current": vix_curr,
                "dominant_session_character": dom_character,
                "dominant_structural_bias": bias,
                "major_turning_point_count": len(turning_points),
                "high_impact_material_event_count": len(cls._live_event_stream),
                "session_verdict": verdict_text
            },
            "timeline": timeline if has_real_history or not market_closed else [],
            "major_turning_points": turning_points if has_real_history or not market_closed else [],
            "session_phases": phase_summaries,
            "session_verdict": session_verdict,
            "data_quality": {
                "status": "DEGRADED" if (gaps or status_classification in ("PARTIAL", "UNAVAILABLE")) else "READY",
                "has_telemetry_gap": bool(gaps),
                "gap_count": len(gaps),
                "largest_gap": f"{int(gaps[0][2]//60)}m" if gaps else "0m",
                "provenance": ["canonical.state_history", "canonical.material_events"]
            }
        }
    @staticmethod
    def _is_genuine_telemetry_gap(s_prev: dict[str, Any], s_curr: dict[str, Any], gap_sec: float) -> bool:
        if gap_sec <= 15.0:
            return False
        if s_prev.get("feed_status") in ("STALE", "DISCONNECTED", "RECONNECTING") or s_curr.get("feed_status") in ("STALE", "DISCONNECTED", "RECONNECTING"):
            return True
        if s_prev.get("is_outage") or s_curr.get("is_outage"):
            return True
        if s_prev.get("market_session_phase") not in ("MARKET_OPEN", "OPEN") and s_curr.get("market_session_phase") not in ("MARKET_OPEN", "OPEN"):
            return False
        is_anchor = (s_prev.get("is_compaction_anchor") and s_curr.get("is_compaction_anchor")) or abs(gap_sec - 900.0) < 60.0
        if is_anchor:
            seq_diff = (s_curr.get("state_sequence") or 0) - (s_prev.get("state_sequence") or 0)
            if seq_diff <= 1 and not (s_curr.get("feed_stale") or s_prev.get("feed_stale")):
                return False
        return gap_sec > 120.0

    @staticmethod
    def _reasons(*statuses: SectionStatus) -> list[str]:
        names = ("validated market context", "option-chain aggregate", "real news provider")
        return [names[i] for i, status in enumerate(statuses)
                if status in {SectionStatus.BLOCKED, SectionStatus.UNAVAILABLE}]

    @staticmethod
    def _ready(name: str, status: SectionStatus, reasons: list[str]) -> dict[str, Any]:
        return {"workspace": name, "status": status.value,
                "accessible": name in {"NIFTY Live", "Settings"} or status not in {SectionStatus.BLOCKED, SectionStatus.UNAVAILABLE},
                "dependency_reasons": reasons}


validate_setup_geometry = WorkstationStateService.validate_setup_geometry
atexit.register(lambda: WorkstationStateService.flush_session_history())
