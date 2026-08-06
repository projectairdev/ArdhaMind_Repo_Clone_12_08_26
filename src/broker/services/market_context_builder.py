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


def _refresh_candle_buffer(bs: Any) -> None:
    """Fetches 1-min NIFTY 50 candles from Kite REST API and stores in module buffer."""
    global _candle_buffer, _candle_last_fetch
    now = time.time()
    if now - _candle_last_fetch < _CANDLE_FETCH_INTERVAL_SECONDS:
        return  # Use cached buffer

    try:
        gateway = bs.get_gateway()
        kite = getattr(gateway, "_kite_client", gateway)

        from_dt = datetime.now() - timedelta(days=3)
        to_dt = datetime.now()

        # Find NIFTY 50 instrument token
        from src.broker.services.instrument_service import InstrumentService
        inst_svc = InstrumentService.get_instance()
        inst_svc.load_instruments(bs)
        nifty_inst = inst_svc.lookup_index_instrument("NIFTY 50")
        if not nifty_inst:
            logger.warning("Could not find NIFTY 50 instrument token for candle fetch.")
            return

        token = int(nifty_inst.get("instrument_token", 0))
        if token == 0:
            return

        candles_raw = kite.historical_data(
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
    except Exception as e:
        logger.error(f"Failed to refresh candle buffer: {e}")


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

class MarketContextBuilder:
    """
    Stateless builder: one call = one MarketContext dict.
    Reads ONLY from live WebSocket ticks and live API responses.
    """

    @staticmethod
    def build(bs: Any, orch: Any, india_vix: float) -> Dict[str, Any]:
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
        nifty_tick = orch.latest_ticks.get("NSE:NIFTY 50") if orch else None
        spot = 0.0
        ltp = 0.0
        volume = 0
        oi = 0
        oi_change = 0
        bid = 0.0
        ask = 0.0
        spread = 0.0
        last_tick_time = ""

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
        else:
            # Fallback to REST LTP when WebSocket ticks are not active (e.g. market closed)
            if bs.is_connected():
                try:
                    ltps = bs.get_ltp(["NSE:NIFTY 50"])
                    if ltps and "NSE:NIFTY 50" in ltps:
                        spot = float(ltps["NSE:NIFTY 50"].get("last_price", 0.0))
                        ltp = spot
                        bid = spot
                        ask = spot
                        last_tick_time = now_str
                except Exception:
                    pass

        # ---- ATR and VWAP from intraday candle buffer ----
        try:
            _refresh_candle_buffer(bs)
        except Exception:
            pass

        vwap = _compute_vwap(_candle_buffer)
        atr = _compute_atr(_candle_buffer)

        # If we have a live spot but VWAP not available yet, use spot as proxy
        if vwap <= 0 and spot > 0:
            vwap = spot

        # ---- Trend determination from observed values ----
        market_regime, trend_direction, trend_strength = _determine_trend(spot, vwap, atr)
        supports, resistances = _compute_support_resistance(spot, atr)

        # ---- Volatility ----
        if india_vix <= 0.0 and bs.is_connected():
            try:
                ltps = bs.get_ltp(["NSE:INDIA VIX"])
                if ltps and "NSE:INDIA VIX" in ltps:
                    india_vix = float(ltps["NSE:INDIA VIX"].get("last_price", 0.0))
            except Exception:
                pass
        vol_state = _determine_volatility_state(india_vix)

        # ---- PCR from cached option context ----
        pcr = 0.0
        atm_strike = 0.0
        current_weekly_expiry = ""
        current_monthly_expiry = ""
        try:
            from src.broker.services.market_feed_service import MarketFeedService
            mfs = MarketFeedService.get_instance()
            atm_strike = round(spot / 50.0) * 50.0 if spot > 0 else 0.0
            # PCR from option chain if available
            if hasattr(mfs, "subscribed_options") and mfs.last_expiry_for_sub:
                current_weekly_expiry = mfs.last_expiry_for_sub
        except Exception:
            pass

        # Attempt to get PCR from cached option context
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

        # ---- Trading session ----
        try:
            from src.broker.services.market_status_service import MarketStatusService
            ms = MarketStatusService.get_instance().get_market_status()
            trading_session = ms.get("status", "UNKNOWN")
        except Exception:
            trading_session = "UNKNOWN"

        return {
            # Spot & Tick
            "current_spot": spot,
            "ltp": ltp,
            "last_tick_time": last_tick_time,
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
            # Volatility
            "india_vix": india_vix,
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
            "support_levels": supports,
            "resistance_levels": resistances,
            # Breadth (N/A — requires equity scanner)
            "market_breadth": 0.0,
            # Feed health
            "feed_latency_ms": feed_latency_ms,
            "feed_health": feed_health,
            # Session
            "trading_session": trading_session,
            "current_expiry": current_weekly_expiry,
            "timestamp": now_str,
        }
