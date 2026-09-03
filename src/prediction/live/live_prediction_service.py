"""
LivePredictionService
=====================

Read-only bridge that connects the deterministic backend prediction subsystem
(``src/prediction`` + ``src/analytics``) to the live workstation state envelope.

It is a pure computation / serialization layer:

* It never mutates broker, order, or session state.
* It builds an ephemeral :class:`MarketAnalyticsSnapshot` from the market data
  already present in the live legacy payload (spot, OHLC, 1-minute candles, VIX),
  runs :meth:`PredictionEngine.generate_prediction`, and serializes the resulting
  immutable :class:`PredictionSnapshot` into a JSON-safe dict.
* On any failure it returns an explicit ``status="UNAVAILABLE"`` payload - it never
  fabricates a prediction or falls back to hardcoded-looking numbers.

Refresh cadence
---------------
``PredictionEngine`` is designed to be invoked once per prediction *phase*, and
all of its inputs (ATR-14, compression, trend, regime) are derived from
*1-minute* canonical candles. Within a single forming minute those inputs do not
change, so recomputing on every ~3 second daemon tick would produce an identical
snapshot at ~20x the cost while churning the ``generated_at`` timestamp
misleadingly.

``LivePredictionService`` therefore memoizes the serialized snapshot and only
recomputes when the **1-minute candle boundary changes** (falling back to the
wall-clock minute when candles are unavailable). Net effect: at most one fresh
prediction per minute, reused on the intervening daemon ticks.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, time as dt_time, timedelta, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_IST = timezone(timedelta(hours=5, minutes=30))
_NIFTY_ID = "IDX:NSE:NIFTY_50"
_VIX_ID = "IDX:NSE:INDIA_VIX"


class LivePredictionService:
    """Stateless-except-for-cache coordinator. All methods are classmethods."""

    _lock = Lock()
    _cache_key: Optional[str] = None
    _cache_payload: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------ public

    @classmethod
    def get_prediction_payload(
        cls,
        *,
        market_context: Optional[Dict[str, Any]] = None,
        option_context: Optional[Dict[str, Any]] = None,
        session_phase: str = "PRE_MARKET",
        is_live_session: bool = False,
        now_utc: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Return a JSON-safe prediction snapshot dict for the canonical envelope.

        Never raises: a failure to produce a prediction yields an explicit
        ``status="UNAVAILABLE"`` payload.
        """
        now_utc = now_utc or datetime.now(timezone.utc)
        m_ctx = market_context or {}
        o_ctx = option_context or {}

        raw_candles = m_ctx.get("candles") or []
        minute_bucket = cls._resolve_minute_bucket(raw_candles, now_utc)
        session_date = str(m_ctx.get("session_date") or now_utc.astimezone(_IST).strftime("%Y-%m-%d"))
        cache_key = f"{session_date}|{session_phase}|{is_live_session}|{minute_bucket}"

        with cls._lock:
            if cache_key == cls._cache_key and cls._cache_payload is not None:
                return dict(cls._cache_payload)

        try:
            payload = cls._compute(m_ctx, o_ctx, session_phase, is_live_session, now_utc, session_date)
        except Exception as exc:  # noqa: BLE001 - never propagate into the envelope build
            logger.warning("[LivePredictionService] prediction unavailable: %s", exc, exc_info=True)
            payload = cls._unavailable_payload(now_utc, reason=f"{type(exc).__name__}: {exc}")

        with cls._lock:
            cls._cache_key = cache_key
            cls._cache_payload = payload
        return dict(payload)

    # ----------------------------------------------------------------- compute

    @classmethod
    def _compute(
        cls,
        m_ctx: Dict[str, Any],
        o_ctx: Dict[str, Any],
        session_phase: str,
        is_live_session: bool,
        now_utc: datetime,
        session_date: str,
    ) -> Dict[str, Any]:
        from src.analytics.market_analytics_engine import MarketAnalyticsEngine
        from src.market_data.services.candle_engine import CanonicalCandleEngine
        from src.market_data.session.session_authority import CanonicalSessionAuthority
        from src.market_data.state.live_market_state import LiveMarketState
        from src.market_data.models.quality_enums import Timeframe
        from src.prediction.models.prediction_models import PredictionPhase
        from src.prediction.prediction_engine import PredictionEngine

        spot = cls._num(m_ctx.get("current_spot") or m_ctx.get("spot") or m_ctx.get("ltp"))
        if spot is None or spot <= 0:
            return cls._unavailable_payload(now_utc, reason="No validated NIFTY spot in live payload.")

        try:
            sess_date_obj = date.fromisoformat(session_date[:10])
        except ValueError:
            sess_date_obj = now_utc.astimezone(_IST).date()

        prev_close = cls._num(m_ctx.get("previous_close") or m_ctx.get("prev_close"))
        open_px = cls._num(m_ctx.get("open")) or spot
        high_px = cls._num(m_ctx.get("high")) or spot
        low_px = cls._num(m_ctx.get("low")) or spot
        vix = cls._num(m_ctx.get("india_vix") or m_ctx.get("vix"))

        candle_engine = CanonicalCandleEngine()
        canon_candles = cls._build_canonical_candles(m_ctx.get("candles") or [], sess_date_obj, spot)
        if canon_candles:
            candle_engine.hydrate_candles(canon_candles)

        state_store = LiveMarketState()
        cls._push_tick(state_store, _NIFTY_ID, sess_date_obj, now_utc, spot, open_px, high_px, low_px, prev_close)
        if vix is not None and vix > 0:
            cls._push_tick(state_store, _VIX_ID, sess_date_obj, now_utc, vix)

        analytics_engine = MarketAnalyticsEngine(state_store, candle_engine, CanonicalSessionAuthority())
        analytics_snap = analytics_engine.generate_snapshot()

        target_date = analytics_snap.session_date or sess_date_obj
        phase = cls._map_phase(session_phase)
        historical = cls._load_historical_sessions(target_date)

        pred = PredictionEngine.generate_prediction(
            snapshot=analytics_snap,
            target_session_date=target_date,
            phase=phase,
            historical_sessions=historical,
        )
        return cls._serialize(pred, spot=spot, is_live_session=is_live_session, now_utc=now_utc)

    # --------------------------------------------------------------- serialize

    @classmethod
    def _serialize(
        cls,
        pred: Any,
        *,
        spot: float,
        is_live_session: bool,
        now_utc: datetime,
    ) -> Dict[str, Any]:
        rec = pred.prediction_record
        mag = rec.magnitude_distribution
        direction = rec.direction_prediction.value
        ref_price = float(rec.reference_price or spot)

        # Signed expected move + 1-sigma corridor (points -> price levels).
        signed_move = float(rec.expected_move_points or 0.0)
        upper = float(mag.upper_band_pts or 0.0)
        lower = float(mag.lower_band_pts or 0.0)

        if direction == "BEARISH":
            primary_target = round(ref_price - abs(signed_move or mag.expected_magnitude), 2)
            corridor_far = round(ref_price - upper, 2)
            corridor_near = round(ref_price - lower, 2)
            invalidation = round(ref_price + lower, 2)
        elif direction == "BULLISH":
            primary_target = round(ref_price + abs(signed_move or mag.expected_magnitude), 2)
            corridor_far = round(ref_price + upper, 2)
            corridor_near = round(ref_price + lower, 2)
            invalidation = round(ref_price - lower, 2)
        else:
            primary_target = round(ref_price, 2)
            corridor_far = round(ref_price + upper, 2)
            corridor_near = round(ref_price - upper, 2)
            invalidation = None

        prob = float(rec.direction_probability or 0.5)
        p_range = float(mag.p_0_50 or 0.0)  # smallest bucket ~ range / chop
        directional_pool = max(0.0, 1.0 - p_range)
        if direction == "BEARISH":
            scenario_down = round(directional_pool * prob, 3)
            scenario_up = round(directional_pool * (1.0 - prob), 3)
        elif direction == "BULLISH":
            scenario_up = round(directional_pool * prob, 3)
            scenario_down = round(directional_pool * (1.0 - prob), 3)
        else:
            scenario_up = round(directional_pool * 0.5, 3)
            scenario_down = round(directional_pool * 0.5, 3)
        scenario_range = round(max(0.0, 1.0 - scenario_up - scenario_down), 3)

        conf_pct = int(round(float(rec.confidence_score or 0.0) * 100))
        maturity = str(getattr(pred, "calibration_status", "") or "CALIBRATED")

        magnitude_buckets = [
            {"bucket_name": "0-50 pts", "range_label": "< 50 pts", "probability": float(mag.p_0_50)},
            {"bucket_name": "50-100 pts", "range_label": "50-100 pts", "probability": float(mag.p_50_100)},
            {"bucket_name": "100-150 pts", "range_label": "100-150 pts", "probability": float(mag.p_100_150)},
            {"bucket_name": "150-200 pts", "range_label": "150-200 pts", "probability": float(mag.p_150_200)},
            {"bucket_name": "200+ pts", "range_label": "> 200 pts", "probability": float(mag.p_200_plus)},
        ]

        factor_contribs = [
            {
                "factor_name": name,
                "vote": "NEUTRAL",
                "nominal_weight": 0.0,
                "effective_weight": 0.0,
                "is_available": True,
                "rationale": name.replace("_", " ").title(),
            }
            for name in (rec.features_used or [])
        ]

        analogs = [
            {
                "session_date": m.session_date.isoformat(),
                "similarity_score": round(float(m.similarity_score), 3),
                "similarity_pct": int(round(float(m.similarity_score) * 100)),
                "regime": m.regime,
                "observed_move_pts": round(float(m.observed_move_pts), 2),
                "observed_range_pts": round(float(m.observed_range_pts), 2),
                "observed_direction": m.observed_direction,
            }
            for m in (pred.similar_sessions or [])
        ]

        bias_map = {"BULLISH": "BULLISH", "BEARISH": "BEARISH", "NEUTRAL": "NEUTRAL"}
        quality_ok = str(getattr(pred, "quality", "")).upper() in {"VALID", "DELAYED", "DATAQUALITYSTATUS.VALID", "DATAQUALITYSTATUS.DELAYED"}

        generated_ist = rec.created_at.astimezone(_IST)

        return {
            "status": "OK",
            "quality": "VALID" if quality_ok else "UNAVAILABLE",
            # --- typed CanonicalPredictionSnapshot fields ---
            "target_session_date": rec.target_session_date.isoformat(),
            "phase": rec.prediction_phase.value,
            "direction_bias": bias_map.get(direction, "UNCERTAIN"),
            "direction_confidence": round(prob, 3),
            "factor_contributions": factor_contribs,
            "magnitude_distribution": magnitude_buckets,
            "expected_range_points": round(float(mag.expected_magnitude), 1),
            "confidence_score": conf_pct,
            "confidence_band": rec.confidence_band.value,
            "calibration_maturity": maturity,
            # --- live projection detail (consumed by Predictions tab) ---
            "prediction_id": rec.prediction_id,
            "model_version": rec.model_version,
            "calibration_version": rec.calibration_version,
            "generated_at": rec.created_at.isoformat().replace("+00:00", "Z"),
            "generated_at_ist": generated_ist.strftime("%H:%M:%S"),
            "reference_price": round(ref_price, 2),
            "expected_move_points": round(signed_move, 1),
            "primary_target": primary_target,
            "invalidation_level": invalidation,
            "scenario_up_prob": scenario_up,
            "scenario_down_prob": scenario_down,
            "scenario_range_prob": scenario_range,
            "magnitude_lower_band_pts": round(lower, 1),
            "magnitude_upper_band_pts": round(upper, 1),
            "volatility_corridor": {
                "near_level": corridor_near,
                "far_level": corridor_far,
                "lower_band_pts": round(lower, 1),
                "upper_band_pts": round(upper, 1),
            },
            "similar_sessions": analogs,
            "supporting_factors": list(rec.supporting_factors or []),
            "caution_factors": list(rec.caution_factors or []),
            "market_regime": rec.market_regime,
            "is_live_projection": bool(is_live_session),
            "basis": "LIVE_SESSION" if is_live_session else "LAST_COMPLETED_SESSION",
            # legacy keys kept for backward compatibility with earlier envelope readers
            "snapshot_time": rec.created_at.isoformat().replace("+00:00", "Z"),
            "timeframe": "15m",
            "confidence": conf_pct,
        }

    @classmethod
    def _unavailable_payload(cls, now_utc: datetime, *, reason: str) -> Dict[str, Any]:
        from src.prediction.prediction_engine import PredictionEngine

        return {
            "status": "UNAVAILABLE",
            "quality": "UNAVAILABLE",
            "unavailable_reason": reason,
            "target_session_date": now_utc.astimezone(_IST).strftime("%Y-%m-%d"),
            "phase": "PRE_MARKET",
            "direction_bias": "NEUTRAL",
            "direction_confidence": 0,
            "factor_contributions": [],
            "magnitude_distribution": [],
            "expected_range_points": None,
            "confidence_score": 0,
            "confidence_band": "LOW",
            "calibration_maturity": "UNAVAILABLE",
            "model_version": PredictionEngine.MODEL_VERSION,
            "generated_at": now_utc.isoformat().replace("+00:00", "Z"),
            "generated_at_ist": now_utc.astimezone(_IST).strftime("%H:%M:%S"),
            "primary_target": None,
            "invalidation_level": None,
            "scenario_up_prob": None,
            "scenario_down_prob": None,
            "scenario_range_prob": None,
            "volatility_corridor": {},
            "similar_sessions": [],
            "is_live_projection": False,
            "basis": "UNAVAILABLE",
            "snapshot_time": now_utc.isoformat().replace("+00:00", "Z"),
            "timeframe": "15m",
        }

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _num(value: Any) -> Optional[float]:
        try:
            if value is None:
                return None
            f = float(value)
            return f if f == f else None  # reject NaN
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _map_phase(session_phase: str) -> Any:
        from src.prediction.models.prediction_models import PredictionPhase

        s = str(session_phase or "").upper()
        if s in {"MARKET_OPEN", "OPEN", "CONTINUOUS_TRADING", "NEAR_CLOSE"}:
            return PredictionPhase.INTRADAY
        if s in {"OPENING_RANGE", "OPENING"}:
            return PredictionPhase.OPENING
        if s == "PRE_OPEN":
            return PredictionPhase.PRE_OPEN
        return PredictionPhase.PRE_MARKET

    @classmethod
    def _resolve_minute_bucket(cls, raw_candles: List[Any], now_utc: datetime) -> str:
        """Cache key component: latest 1m candle boundary, else wall-clock minute."""
        last = raw_candles[-1] if raw_candles else None
        if isinstance(last, dict):
            stamp = last.get("date") or last.get("timestamp") or last.get("time") or last.get("t")
            if stamp:
                return str(stamp)[:16]
        return now_utc.strftime("%Y-%m-%dT%H:%M")

    @classmethod
    def _build_canonical_candles(cls, raw: List[Any], session_date: date, spot: float) -> List[Any]:
        """Synthesize validated 1-minute CanonicalCandles from the legacy candle list.

        Legacy candles carry no reliable canonical timestamps, so buckets are
        assigned sequentially from the 09:15 IST session anchor. Rows that cannot
        satisfy OHLC invariants are skipped rather than coerced with fake data.
        """
        from src.market_data.models.canonical_candle import CanonicalCandle
        from src.market_data.models.quality_enums import CandleQuality, Timeframe

        anchor = datetime.combine(session_date, dt_time(9, 15), tzinfo=_IST)
        out: List[Any] = []
        rows = raw[-375:] if len(raw) > 375 else raw
        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            o = cls._num(row.get("open") if row.get("open") is not None else row.get("o"))
            h = cls._num(row.get("high") if row.get("high") is not None else row.get("h"))
            low_v = cls._num(row.get("low") if row.get("low") is not None else row.get("l"))
            c = cls._num(row.get("close") if row.get("close") is not None else row.get("c"))
            if None in (o, h, low_v, c) or min(o, h, low_v, c) <= 0:
                continue
            hi = max(o, h, low_v, c)
            lo = min(o, h, low_v, c)
            vol = row.get("volume") if row.get("volume") is not None else row.get("v")
            try:
                vol = int(vol) if vol is not None and int(vol) >= 0 else None
            except (TypeError, ValueError):
                vol = None
            start = anchor + timedelta(minutes=i)
            try:
                out.append(
                    CanonicalCandle(
                        canonical_instrument_id=_NIFTY_ID,
                        provider="LEGACY_BRIDGE",
                        session_date=session_date,
                        timeframe=Timeframe.M1,
                        start_timestamp=start,
                        end_timestamp=start + timedelta(minutes=1),
                        open=o,
                        high=hi,
                        low=lo,
                        close=c,
                        volume=vol,
                        quality=CandleQuality.VALID,
                    )
                )
            except (ValueError, TypeError):
                continue
        return out

    @classmethod
    def _push_tick(
        cls,
        store: Any,
        cid: str,
        session_date: date,
        now_utc: datetime,
        last_price: float,
        open_px: Optional[float] = None,
        high_px: Optional[float] = None,
        low_px: Optional[float] = None,
        prev_close: Optional[float] = None,
    ) -> None:
        from src.market_data.bus.events import MarketEvent, MarketEventType
        from src.market_data.models.canonical_tick import CanonicalTick

        kwargs: Dict[str, Any] = {}
        if open_px and open_px > 0:
            kwargs["open"] = open_px
        if high_px and high_px > 0:
            kwargs["high"] = max(high_px, last_price)
        if low_px and low_px > 0:
            kwargs["low"] = min(low_px, last_price)
        if prev_close and prev_close > 0:
            kwargs["previous_close"] = prev_close

        tick = CanonicalTick(
            canonical_instrument_id=cid,
            provider="LEGACY_BRIDGE",
            exchange_timestamp=now_utc,
            received_at=now_utc,
            session_date=session_date,
            last_price=last_price,
            **kwargs,
        )
        store.apply_tick_event(
            MarketEvent("live_pred_tick", MarketEventType.TICK, now_utc, 1, tick, canonical_instrument_id=cid)
        )

    @classmethod
    def _load_historical_sessions(cls, as_of: date, limit: int = 25) -> List[Any]:
        """Best-effort load of recent completed-session snapshots for analog matching."""
        try:
            from src.market_data.models.completed_session_snapshot import CompletedSessionSnapshot
            from src.market_data.models.quality_enums import DataQualityStatus
            from src.storage import LightweightSessionStore

            store = LightweightSessionStore.get_instance()
            close_dir = getattr(store, "close_dir", None)
            if close_dir is None or not close_dir.exists():
                return []

            files = sorted(
                (f for f in close_dir.glob("*.json") if not f.name.endswith(".tmp")),
                key=lambda p: p.name,
                reverse=True,
            )[:limit]

            out: List[Any] = []
            for f in files:
                try:
                    core = store.load_session_close(f.stem)
                except Exception:
                    continue
                if not core or not core.market_ohlcv:
                    continue
                o = cls._num(core.market_ohlcv.open)
                h = cls._num(core.market_ohlcv.high)
                low_v = cls._num(core.market_ohlcv.low)
                c = cls._num(core.market_ohlcv.close)
                if None in (o, h, low_v, c) or min(o, h, low_v, c) <= 0 or h < low_v:
                    continue
                try:
                    sd = date.fromisoformat(str(core.session_date)[:10])
                except ValueError:
                    continue
                pc = cls._num(core.market_ohlcv.previous_close)
                rng = cls._num(core.market_ohlcv.session_range_points) or round(h - low_v, 2)
                abs_chg = round(c - pc, 2) if pc else round(c - o, 2)
                out.append(
                    CompletedSessionSnapshot(
                        canonical_instrument_id=_NIFTY_ID,
                        session_date=sd,
                        open=o,
                        high=h,
                        low=low_v,
                        close=c,
                        previous_close=pc,
                        absolute_change=abs_chg,
                        percent_change=round((abs_chg / pc) * 100, 4) if pc else None,
                        range=rng,
                        final_candle_timestamp=datetime.now(timezone.utc),
                        quality=DataQualityStatus.VALID,
                    )
                )
            return out
        except Exception as exc:  # noqa: BLE001
            logger.debug("[LivePredictionService] historical session load skipped: %s", exc)
            return []
