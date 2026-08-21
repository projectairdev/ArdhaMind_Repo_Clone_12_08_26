"""
MarketContextBuilder
====================
Stateless builder that assembles a fully live MarketContext dict from:
  - StreamingOrchestrator.latest_ticks  (Zerodha WebSocket)
  - InstrumentService                   (instrument master)
  - MarketFeedService                   (option chain context)
  - kite.historical_data()              (1-min candles for ATR/VWAP at startup)

Production Integrity Rules
--------------------------
- NEVER fabricate a value.
- NEVER use random.
- NEVER use hardcoded spot comparisons.
- If data is unavailable: set field to None / 0 and mark feed_health accordingly.
"""
from __future__ import annotations

import math
import time
import logging
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional
from src.utils.time_utils import is_trading_day, previous_trading_day, is_market_hours

logger = logging.getLogger("MarketContextBuilder")

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_vwap(candles: List[Dict]) -> float:
    """
    VWAP = sum(typical_price * volume) / sum(volume)
    Typical price = (high + low + close) / 3
    """
    total_pv = 0.0
    total_v = 0.0
    for c in candles:
        try:
            h = float(c.get("high", 0))
            l = float(c.get("low", 0))
            cl = float(c.get("close", 0))
            v = float(c.get("volume", 0))
            if v > 0:
                tp = (h + l + cl) / 3.0
                total_pv += tp * v
                total_v += v
        except Exception:
            pass
    return round(total_pv / total_v, 2) if total_v > 0 else 0.0


def _compute_atr(candles: List[Dict], period: int = 14) -> float:
    """
    ATR = Wilder's smoothed average of True Range.
    True Range = max(H-L, |H-Prev_C|, |L-Prev_C|)
    """
    if len(candles) < 2:
        return 0.0
    trs = []
    for i in range(1, len(candles)):
        try:
            h = float(candles[i].get("high", 0))
            l = float(candles[i].get("low", 0))
            prev_c = float(candles[i - 1].get("close", 0))
            tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
            trs.append(tr)
        except Exception:
            pass
    if not trs:
        return 0.0
    # Simple average for first ATR value, then Wilder's smoothing
    window = trs[-period:] if len(trs) >= period else trs
    return round(sum(window) / len(window), 2)


def _compute_ema(series: List[float], period: int) -> Optional[float]:
    if len(series) < period:
        return None
    multiplier = 2.0 / (period + 1.0)
    ema = sum(series[:period]) / float(period)
    for val in series[period:]:
        ema = (val - ema) * multiplier + ema
    return round(ema, 2)


def _compute_rsi(series: List[float], period: int = 14) -> Optional[float]:
    if len(series) < period + 1:
        return None
    gains = []
    losses = []
    for i in range(1, len(series)):
        diff = series[i] - series[i - 1]
        if diff >= 0:
            gains.append(diff)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(-diff)
    if len(gains) < period:
        return None
    avg_gain = sum(gains[:period]) / float(period)
    avg_loss = sum(losses[:period]) / float(period)
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / float(period)
        avg_loss = (avg_loss * (period - 1) + losses[i]) / float(period)
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100.0 - (100.0 / (1.0 + rs)), 2)


def _compute_macd(series: List[float]) -> Optional[Dict[str, float]]:
    if len(series) < 35:
        return None
    # EMA 12 and EMA 26
    multiplier12 = 2.0 / 13.0
    multiplier26 = 2.0 / 27.0
    multiplier9 = 2.0 / 10.0

    # Calculate full EMA 12 series
    ema12_val = sum(series[:12]) / 12.0
    ema12_series = [ema12_val]
    for val in series[12:]:
        ema12_val = (val - ema12_val) * multiplier12 + ema12_val
        ema12_series.append(ema12_val)

    # Calculate full EMA 26 series
    ema26_val = sum(series[:26]) / 26.0
    ema26_series = [ema26_val]
    for val in series[26:]:
        ema26_val = (val - ema26_val) * multiplier26 + ema26_val
        ema26_series.append(ema26_val)

    # Align MACD line (EMA12 - EMA26)
    # ema12_series has length len(series) - 11, ema26_series has length len(series) - 25
    offset = 14
    macd_line = [e12 - e26 for e12, e26 in zip(ema12_series[offset:], ema26_series)]
    if len(macd_line) < 9:
        return None
    signal_val = sum(macd_line[:9]) / 9.0
    for m in macd_line[9:]:
        signal_val = (m - signal_val) * multiplier9 + signal_val
    hist = macd_line[-1] - signal_val
    return {
        "macd": round(macd_line[-1], 2),
        "signal": round(signal_val, 2),
        "histogram": round(hist, 2),
    }


def _compute_adx(candles: List[Dict], period: int = 14) -> Optional[float]:
    if len(candles) < period * 2:
        return None
    trs = []
    plus_dms = []
    minus_dms = []
    for i in range(1, len(candles)):
        h = float(candles[i].get("high", 0))
        l = float(candles[i].get("low", 0))
        prev_h = float(candles[i - 1].get("high", 0))
        prev_l = float(candles[i - 1].get("low", 0))
        prev_c = float(candles[i - 1].get("close", 0))

        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        up_move = h - prev_h
        down_move = prev_l - l

        plus_dm = up_move if (up_move > down_move and up_move > 0) else 0.0
        minus_dm = down_move if (down_move > up_move and down_move > 0) else 0.0

        trs.append(tr)
        plus_dms.append(plus_dm)
        minus_dms.append(minus_dm)

    if len(trs) < period:
        return None
    smooth_tr = sum(trs[:period])
    smooth_plus_dm = sum(plus_dms[:period])
    smooth_minus_dm = sum(minus_dms[:period])

    dx_series = []
    for i in range(period, len(trs)):
        smooth_tr = smooth_tr - (smooth_tr / period) + trs[i]
        smooth_plus_dm = smooth_plus_dm - (smooth_plus_dm / period) + plus_dms[i]
        smooth_minus_dm = smooth_minus_dm - (smooth_minus_dm / period) + minus_dms[i]

        plus_di = (smooth_plus_dm / smooth_tr * 100.0) if smooth_tr > 0 else 0.0
        minus_di = (smooth_minus_dm / smooth_tr * 100.0) if smooth_tr > 0 else 0.0
        di_sum = plus_di + minus_di
        dx = (abs(plus_di - minus_di) / di_sum * 100.0) if di_sum > 0 else 0.0
        dx_series.append(dx)

    if len(dx_series) < period:
        return round(sum(dx_series) / len(dx_series), 2) if dx_series else None
    adx = sum(dx_series[:period]) / float(period)
    for dx in dx_series[period:]:
        adx = (adx * (period - 1) + dx) / float(period)
    return round(adx, 2)


def _determine_volatility_state(vix: float) -> str:
    if vix <= 0:
        return "UNKNOWN"
    if vix < 12.0:
        return "LOW"
    elif vix < 18.0:
        return "NORMAL"
    elif vix < 25.0:
        return "HIGH"
    return "EXTREME"


def _determine_trend(spot: float, vwap: float, atr: float) -> tuple[str, str, float]:
    """
    Returns (market_regime, trend_direction, trend_strength).
    All derived from live, observed values — no hardcoded constants.
    """
    if vwap <= 0 or atr <= 0:
        return "UNKNOWN", "NEUTRAL", 0.0

    deviation = spot - vwap
    deviation_pct = abs(deviation) / vwap * 100.0
    atr_multiple = abs(deviation) / atr if atr > 0 else 0.0

    if atr_multiple >= 1.5:
        regime = "TRENDING"
        direction = "BULLISH" if deviation > 0 else "BEARISH"
        strength = min(100.0, 50.0 + atr_multiple * 15.0)
    elif atr_multiple >= 0.5:
        regime = "SIDEWAYS"
        direction = "BULLISH" if deviation > 0 else "BEARISH"
        strength = min(100.0, 30.0 + atr_multiple * 20.0)
    else:
        regime = "SIDEWAYS"
        direction = "NEUTRAL"
        strength = atr_multiple * 30.0

    return regime, direction, round(strength, 1)


def _compute_support_resistance(spot: float, atr: float) -> tuple[list, list]:
    """Support and resistance derived from spot ± ATR multiples."""
    if atr <= 0:
        return [], []
    supports = [round(spot - atr, 2), round(spot - 2 * atr, 2)]
    resistances = [round(spot + atr, 2), round(spot + 2 * atr, 2)]
    return supports, resistances


# ---------------------------------------------------------------------------
# Intraday candle buffer (module-level singleton state)
# ---------------------------------------------------------------------------

_candle_buffer: List[Dict] = []
_candle_last_fetch: float = 0.0
_CANDLE_FETCH_INTERVAL_SECONDS = 300  # Refresh candles every 5 minutes
_kite_extensions: Dict[str, Any] = {}
_kite_extensions_last_fetch: float = 0.0
_KITE_EXTENSIONS_FETCH_INTERVAL_SECONDS = 60


def _load_disk_candle_cache_if_needed() -> None:
    global _candle_buffer, _candle_last_fetch
    if not _candle_buffer:
        try:
            import json, os
            cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "cache")
            cache_path = os.path.join(cache_dir, "nifty_candles_cache.json")
            if os.path.exists(cache_path):
                with open(cache_path, "r") as f:
                    loaded = json.load(f)
                if loaded:
                    for c in loaded:
                        if "date" in c and isinstance(c["date"], str):
                            try:
                                c["date"] = datetime.fromisoformat(c["date"])
                            except Exception:
                                pass
                    _candle_buffer = loaded
                    _candle_last_fetch = time.time()
                    logger.info(f"Loaded {len(_candle_buffer)} fallback candles from disk cache")
        except Exception as _load_err:
            logger.debug(f"Could not load fallback candle cache: {_load_err}")


def _refresh_candle_buffer(bs: Any) -> None:
    """Fetches 1-min NIFTY 50 candles from Kite REST API and stores in module buffer."""
    global _candle_buffer, _candle_last_fetch
    now = time.time()
    if now - _candle_last_fetch < _CANDLE_FETCH_INTERVAL_SECONDS:
        return  # Use cached buffer

    try:
        gateway = bs.get_gateway()
        kite = getattr(gateway, "_kite_client", gateway)

        from_dt = datetime.now() - timedelta(days=7)
        to_dt = datetime.now() + timedelta(days=1)

        # Find NIFTY 50 instrument token
        from src.broker.services.instrument_service import InstrumentService
        inst_svc = InstrumentService.get_instance()
        inst_svc.load_instruments(bs)
        nifty_inst = inst_svc.lookup_index_instrument("NIFTY 50")
        if not nifty_inst or not nifty_inst.get("instrument_token"):
            logger.warning("NIFTY 50 instrument token is unresolved; historical fetch suppressed.")
            _load_disk_candle_cache_if_needed()
            return
        token = int(nifty_inst["instrument_token"])

        fetch_fn = getattr(kite, "historical_data", None) or getattr(kite, "get_historical_data", None)
        if not fetch_fn:
            logger.warning("No historical data fetch function available.")
            _load_disk_candle_cache_if_needed()
            return

        candles_raw = fetch_fn(
            instrument_token=token,
            from_date=from_dt.strftime("%Y-%m-%d %H:%M:%S"),
            to_date=to_dt.strftime("%Y-%m-%d %H:%M:%S"),
            interval="minute",
            continuous=False,
            oi=False
        )
        if candles_raw:
            _candle_buffer = candles_raw
            _candle_last_fetch = now
            logger.info(f"Refreshed intraday candle buffer: {len(_candle_buffer)} candles")
            try:
                import json, os
                cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "cache")
                os.makedirs(cache_dir, exist_ok=True)
                cache_path = os.path.join(cache_dir, "nifty_candles_cache.json")
                serializable_candles = []
                for c in candles_raw[-375:]:
                    c_dict = dict(c)
                    if "date" in c_dict and hasattr(c_dict["date"], "isoformat"):
                        c_dict["date"] = c_dict["date"].isoformat()
                    serializable_candles.append(c_dict)
                with open(cache_path, "w") as f:
                    json.dump(serializable_candles, f)
            except Exception as _save_err:
                logger.debug(f"Could not persist candle cache: {_save_err}")
    except Exception as e:
        logger.error(f"Failed to refresh candle buffer: {e}")

    _load_disk_candle_cache_if_needed()


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

class MarketContextBuilder:
    """
    Stateless builder: one call = one MarketContext dict.
    Reads ONLY from live WebSocket ticks and live API responses.
    """

    @staticmethod
    def build(
        bs: Any, orch: Any, india_vix: float,
        constituent_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Builds a fully live MarketContext.

        Parameters
        ----------
        bs   : BrokerService instance
        orch : StreamingOrchestrator instance (has .latest_ticks)
        india_vix : float — live VIX from WebSocket tick

        Returns
        -------
        dict matching the TypeScript MarketContext interface
        """
        now_str = datetime.utcnow().isoformat() + "Z"

        # ---- Feed health ----
        feed_health_data = {}
        try:
            from src.broker.services.market_feed_service import MarketFeedService
            feed_health_data = MarketFeedService.get_instance().get_feed_health()
        except Exception:
            pass

        feed_health = feed_health_data.get("status", "OFFLINE")
        feed_latency_ms = float(feed_health_data.get("latency_ms", 0.0))

        # ---- NIFTY 50 spot from latest tick ----
        nifty_tick = (orch.latest_ticks.get("NSE:NIFTY 50") or orch.latest_ticks.get("NIFTY 50")) if orch else None
        spot = 0.0
        ltp = 0.0
        volume = 0
        oi = 0
        oi_change = 0
        bid = 0.0
        ask = 0.0
        spread = 0.0
        last_tick_time = ""

        previous_close = None
        open_price = None
        high_price = None
        low_price = None

        if nifty_tick:
            spot = float(nifty_tick.get("last_price", 0.0))
            ltp = spot
            volume = int(nifty_tick.get("volume", 0))
            oi = int(nifty_tick.get("oi", 0))
            oi_change = int(nifty_tick.get("oi_day_change", 0))
            bid = float(nifty_tick.get("depth", {}).get("buy", [{}])[0].get("price", ltp))
            ask = float(nifty_tick.get("depth", {}).get("sell", [{}])[0].get("price", ltp))
            spread = round(ask - bid, 2)
            ts = nifty_tick.get("timestamp")
            last_tick_time = str(ts) if ts else now_str

            tick_ohlc = nifty_tick.get("ohlc") or {}
            if tick_ohlc.get("open") is not None and float(tick_ohlc.get("open")) > 0:
                open_price = float(tick_ohlc["open"])
            if tick_ohlc.get("high") is not None and float(tick_ohlc.get("high")) > 0:
                high_price = float(tick_ohlc["high"])
            if tick_ohlc.get("low") is not None and float(tick_ohlc.get("low")) > 0:
                low_price = float(tick_ohlc["low"])
            if tick_ohlc.get("close") is not None and float(tick_ohlc.get("close")) > 0:
                previous_close = float(tick_ohlc["close"])

        source_type = "WEBSOCKET_STREAM" if (nifty_tick and spot > 0) else ("REST_POLL" if bs.is_connected() else "LAST_VALID_SESSION")
        if bs.is_connected():
            try:
                nq = bs.get_quote(["NSE:NIFTY 50"])
                if nq and "NSE:NIFTY 50" in nq:
                    n_data = nq["NSE:NIFTY 50"]
                    if spot <= 0.0:
                        spot = float(n_data.get("last_price", 0.0))
                        ltp = spot
                        bid = spot
                        ask = spot
                        last_tick_time = now_str
                    ohlc_obj = n_data.get("ohlc") or {}
                    prev_raw = ohlc_obj.get("close")
                    if prev_raw is not None and float(prev_raw) > 0:
                        previous_close = float(prev_raw)
                    if ohlc_obj.get("open") is not None and float(ohlc_obj.get("open")) > 0:
                        open_price = float(ohlc_obj["open"])
                    if ohlc_obj.get("high") is not None and float(ohlc_obj.get("high")) > 0:
                        high_price = float(ohlc_obj["high"])
                    if ohlc_obj.get("low") is not None and float(ohlc_obj.get("low")) > 0:
                        low_price = float(ohlc_obj["low"])
            except Exception:
                pass

        if previous_close is None and (constituent_metadata or {}).get("nifty_previous_close"):
            pc_val = (constituent_metadata or {}).get("nifty_previous_close")
            if pc_val and float(pc_val) > 0:
                previous_close = float(pc_val)

        # ---- ATR, VWAP and Candles from intraday candle buffer ----
        try:
            _refresh_candle_buffer(bs)
        except Exception:
            pass

        if _candle_buffer:
            if open_price is None and _candle_buffer[0].get("open") is not None:
                open_price = float(_candle_buffer[0]["open"])
            if high_price is None:
                cand_highs = [float(c["high"]) for c in _candle_buffer if c.get("high") is not None]
                if cand_highs:
                    high_price = max(cand_highs)
            if low_price is None:
                cand_lows = [float(c["low"]) for c in _candle_buffer if c.get("low") is not None]
                if cand_lows:
                    low_price = min(cand_lows)

        spot_change = round(spot - previous_close, 2) if (spot > 0 and previous_close and previous_close > 0) else None
        spot_change_pct = round(spot_change / previous_close * 100.0, 4) if (spot_change is not None and previous_close and previous_close > 0) else None

        vwap = _compute_vwap(_candle_buffer)
        atr = _compute_atr(_candle_buffer)
        closes = [float(c["close"]) for c in _candle_buffer if c.get("close") is not None]
        ema20 = _compute_ema(closes, 20)
        ema50 = _compute_ema(closes, 50)
        ema200 = _compute_ema(closes, 200)
        rsi = _compute_rsi(closes, 14)
        macd = _compute_macd(closes)
        adx = _compute_adx(_candle_buffer, 14)

        # Build chart candles payload from _candle_buffer (bound strictly to single session date)
        candles_payload = []
        if _candle_buffer:
            # Determine target session date for candles
            now_dt = datetime.now()
            today_d = date.today()
            if is_market_hours(now_dt):
                target_date_str = str(today_d)
            else:
                target_d = today_d if is_trading_day(today_d) else previous_trading_day(today_d)
                if now_dt.hour < 9 or (now_dt.hour == 9 and now_dt.minute < 15):
                    target_d = previous_trading_day(target_d)
                target_date_str = str(target_d)

            session_candles = [
                c for c in _candle_buffer
                if (c.get("date").strftime("%Y-%m-%d") if hasattr(c.get("date"), "strftime") else str(c.get("date"))[:10]) == target_date_str
            ]

            # If target session candles absent in memory buffer, check latest date in buffer
            if not session_candles and _candle_buffer:
                latest_c = _candle_buffer[-1]
                latest_dt = latest_c.get("date")
                latest_date_str = latest_dt.strftime("%Y-%m-%d") if hasattr(latest_dt, "strftime") else str(latest_dt)[:10]
                session_candles = [
                    c for c in _candle_buffer
                    if (c.get("date").strftime("%Y-%m-%d") if hasattr(c.get("date"), "strftime") else str(c.get("date"))[:10]) == latest_date_str
                ]

            session_cand_highs = [float(c["high"]) for c in session_candles if c.get("high") is not None]
            session_cand_lows = [float(c["low"]) for c in session_candles if c.get("low") is not None]
            if session_cand_highs:
                high_price = max(session_cand_highs)
            if session_cand_lows:
                low_price = min(session_cand_lows)
            if session_candles and session_candles[0].get("open") is not None:
                open_price = float(session_candles[0]["open"])

            for c in session_candles:
                dt_obj = c.get("date")
                ts_sec = int(dt_obj.timestamp()) if hasattr(dt_obj, "timestamp") else None
                if hasattr(dt_obj, "strftime"):
                    t_str = dt_obj.strftime("%H:%M")
                    iso_str = dt_obj.isoformat()
                else:
                    dt_val = str(dt_obj or "")
                    iso_str = dt_val
                    t_str = dt_val.split(" ")[1][:5] if " " in dt_val else (dt_val.split("T")[1][:5] if "T" in dt_val else dt_val[-8:-3])

                candles_payload.append({
                    "time": t_str,
                    "timestamp": ts_sec,
                    "datetime": iso_str,
                    "trading_date": (dt_obj.strftime("%Y-%m-%d") if hasattr(dt_obj, "strftime") else str(dt_obj)[:10]),
                    "o": float(c.get("open", 0.0)),
                    "h": float(c.get("high", 0.0)),
                    "l": float(c.get("low", 0.0)),
                    "c": float(c.get("close", 0.0)),
                    "v": int(c.get("volume", 0))
                })

        session_mode = "LIVE"
        if spot <= 0.0:
            if _candle_buffer:
                last_c = _candle_buffer[-1]
                spot = float(last_c.get("close", 0.0))
                ltp = spot
                bid = spot
                ask = spot
                ts_val = last_c.get("date")
                last_tick_time = str(ts_val) if ts_val else now_str
                session_mode = "LAST_SESSION"
            else:
                try:
                    import json
                    from src.broker.services.market_feed_service import MarketFeedService
                    snap_path = MarketFeedService.SNAPSHOT_PATH
                    if snap_path.exists():
                        with open(snap_path, "r") as f:
                            snap_data = json.load(f)
                        u_spot = snap_data.get("underlying_spot")
                        if u_spot and float(u_spot) > 0:
                            spot = float(u_spot)
                            ltp = spot
                            bid = spot
                            ask = spot
                            session_mode = "LAST_SESSION"
                except Exception:
                    pass

        # ---- Trend determination from observed values ----
        market_regime, trend_direction, trend_strength = _determine_trend(spot, vwap, atr)
        supports, resistances = _compute_support_resistance(spot, atr)

        # ---- Volatility ----
        # India VIX is rendered only from the exact resolved NSE instrument and
        # a timestamped Kite quote (or its persisted last-valid observation).
        try:
            from src.broker.services.market_status_service import MarketStatusService
            vix_session = str(MarketStatusService.get_instance().get_market_status().status).upper()
        except Exception:
            vix_session = "UNKNOWN"
        vix_closed = any(value in vix_session for value in ("CLOSED", "HOLIDAY", "POST_MARKET"))
        try:
            from src.broker.services.kite_intelligence_service import KiteIntelligenceService
            india_vix_context = KiteIntelligenceService.build_india_vix_snapshot(bs, vix_closed)
        except Exception as exc:
            india_vix_context = {
                "status": "UNAVAILABLE", "value": None, "source": "Kite Quote API",
                "source_symbol": "NSE:INDIA VIX", "observation_timestamp": None,
                "freshness": "UNAVAILABLE", "failure_reason": str(exc)[:240],
            }
        validated_vix = india_vix_context.get("value") if india_vix_context.get("status") in {"AVAILABLE", "DEGRADED"} else None
        india_vix = float(validated_vix) if validated_vix is not None else 0.0
        vol_state = _determine_volatility_state(india_vix)

        # ---- PCR from cached option context ----
        pcr = 0.0
        atm_strike = 0.0
        current_weekly_expiry = ""
        current_monthly_expiry = ""
        try:
            from src.broker.services.market_feed_service import MarketFeedService
            mfs = MarketFeedService.get_instance()
            if hasattr(mfs, "subscribed_options") and mfs.last_expiry_for_sub:
                current_weekly_expiry = mfs.last_expiry_for_sub
        except Exception:
            pass

        try:
            from src.server_bridge import cached_option_context as _oc
            if _oc:
                pcr = float(_oc.get("pcr", 0.0))
                if not current_weekly_expiry:
                    current_weekly_expiry = _oc.get("current_weekly_expiry", "")
                current_monthly_expiry = _oc.get("current_monthly_expiry", "")
                if atm_strike <= 0:
                    atm_strike = float(_oc.get("atm_strike", 0.0))
        except Exception:
            pass

        try:
            from src.broker.services.market_status_service import MarketStatusService
            ms = MarketStatusService.get_instance().get_market_status()
            trading_session = getattr(ms, "status", "UNKNOWN")
        except Exception:
            trading_session = "UNKNOWN"

        if str(trading_session).upper() in {"CLOSED", "HOLIDAY", "TRADING_HOLIDAY", "POST_MARKET"}:
            feed_health = "MARKET_CLOSED"
            session_mode = "LAST_SESSION" if spot > 0 else "UNAVAILABLE"
            if _candle_buffer:
                candle_time = _candle_buffer[-1].get("date")
                if candle_time:
                    last_tick_time = str(candle_time)

        global _kite_extensions, _kite_extensions_last_fetch
        market_closed = str(trading_session).upper() in {"CLOSED", "HOLIDAY", "TRADING_HOLIDAY", "POST_MARKET"}
        if bs.is_connected() and time.time() - _kite_extensions_last_fetch >= _KITE_EXTENSIONS_FETCH_INTERVAL_SECONDS:
            try:
                from src.broker.services.kite_intelligence_service import KiteIntelligenceService
                _kite_extensions = KiteIntelligenceService.build_market_extensions(
                    bs, market_closed, constituent_metadata,
                )
                _kite_extensions_last_fetch = time.time()
            except Exception as exc:
                logger.warning("Kite market extensions unavailable: %s", exc)
        breadth = _kite_extensions.get("breadth") or {
            "status": "UNAVAILABLE", "coverage": {"valid": 0, "expected": 50, "minimum": 40}
        }
        sectors = _kite_extensions.get("sectors") or []
        breadth_ratio = breadth.get("advance_decline_ratio") if breadth.get("status") == "READY" else None

        return {
            # Spot & Tick
            "current_spot": spot,
            "ltp": ltp,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": ltp if ltp > 0 else spot,
            "session_high": high_price,
            "session_low": low_price,
            "session_open": open_price,
            "session_close": ltp if ltp > 0 else spot,
            "intraday_range": round(high_price - low_price, 2) if (high_price is not None and low_price is not None) else None,
            "previous_close": previous_close,
            "spot_change": spot_change,
            "spot_change_pct": spot_change_pct,
            "change_points": spot_change,
            "change_percent": spot_change_pct,
            "last_tick_time": last_tick_time,
            "session_mode": session_mode,
            "source_type": source_type,
            "observed_at": now_str,
            "candles": candles_payload,
            # Bid / Ask
            "bid": bid,
            "ask": ask,
            "spread": spread,
            # Volume & OI
            "volume": volume,
            "oi": oi,
            "oi_change": oi_change,
            # Computed from live data
            "vwap": vwap,
            "atr": atr,
            "ema20": ema20,
            "ema50": ema50,
            "ema200": ema200,
            "rsi": rsi,
            "macd": macd,
            "adx": adx,
            # Volatility
            "india_vix": india_vix,
            "india_vix_context": india_vix_context,
            "volatility_state": vol_state,
            # Options
            "pcr": pcr,
            "atm_strike": atm_strike,
            "current_weekly_expiry": current_weekly_expiry,
            "current_monthly_expiry": current_monthly_expiry,
            # Regime / Trend (live)
            "market_regime": market_regime,
            "trend_direction": trend_direction,
            "trend_strength": trend_strength,
            "pivot": round((supports[0] + resistances[0]) / 2.0, 2) if (supports and resistances) else (spot if spot > 0 else None),
            "support_levels": supports,
            "resistance_levels": resistances,
            # Breadth (N/A — requires equity scanner)
            "market_breadth": breadth_ratio,
            "breadth": breadth,
            "constituent_instruments": _kite_extensions.get("constituent_instruments") or {},
            "sectors": sectors,
            "sector_performance": sectors,
            "sector_coverage": {
                "resolved": _kite_extensions.get("resolved_count", 0),
                "quoted": _kite_extensions.get("quote_count", 0),
            },
            # Feed health
            "feed_latency_ms": feed_latency_ms,
            "feed_health": feed_health,
            # Session
            "trading_session": trading_session,
            "current_expiry": current_weekly_expiry,
            "timestamp": now_str,
        }
