from __future__ import annotations

import json
import logging
import os
import math
import tempfile
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from src.broker.services.broker_service import BrokerService
from src.broker.services.instrument_service import InstrumentService
from src.news_engine.specialized_data_provider import RbiRiskFreeRateProvider
from src.options_engine.iv import solve_implied_volatility

logger = logging.getLogger("MarketFeedService")

_IST = ZoneInfo("Asia/Kolkata")


def exchange_today() -> date:
    """Current calendar date on the exchange (IST).

    NSE option expiries are IST calendar dates, so "is this expiry in the past?"
    must be evaluated against the IST date, not the process-local date. The
    production VPS runs in UTC, which lags IST by a full calendar day during
    00:00-05:30 IST; using the local date there would spuriously classify the
    current IST day's expiry as future/past for that window. This is the single
    definition of "today" for every expiry-vs-today comparison.
    """
    return datetime.now(_IST).date()


def _number(value: Any) -> Optional[float]:
    try:
        result = float(value)
        return result if result == result else None
    except (TypeError, ValueError):
        return None


def _integer(value: Any) -> Optional[int]:
    number = _number(value)
    return int(number) if number is not None else None


def _timestamp(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    text = str(value).strip()
    return text or None


class MarketFeedService:
    """Bounded, instrument-resolved NIFTY option intelligence sourced only from Kite."""

    _instance: Optional["MarketFeedService"] = None
    SNAPSHOT_PATH = Path(".cache/kite_nifty_option_snapshot.json")
    STRIKE_WINDOW_SIZE = 11

    # Disk-snapshot fallback bounds. Beyond SNAPSHOT_MAX_AGE_SECONDS the cached
    # option chain is refused outright (UI shows "data too old to display")
    # rather than being served as if it were current. Between STALE and MAX it
    # is served but flagged stale so PCR / max-pain / OI walls are not presented
    # with live confidence.
    SNAPSHOT_STALE_AFTER_SECONDS = 300.0        # 5 min — chain preset staleness
    SNAPSHOT_MAX_AGE_SECONDS = 6 * 3600.0       # 6 h  — hard "too old" ceiling
    SNAPSHOT_TOO_OLD_MESSAGE = "Option chain unavailable — data too old to display"

    def __new__(cls, *args: Any, **kwargs: Any) -> "MarketFeedService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self.subscribed_options: List[str] = []
        self.last_spot_for_sub = 0.0
        self.last_expiry_for_sub = ""
        self.last_tick_timestamps: Dict[str, float] = {}
        self.last_resolution: Dict[str, Any] = {}
        self._initialized = True

    @classmethod
    def get_instance(cls) -> "MarketFeedService":
        return cls()

    def get_feed_health(self) -> Dict[str, Any]:
        bs = BrokerService.get_instance()
        health = bs.get_stream_health()
        try:
            orchestrator = bs._get_orchestrator()
            liveness = orchestrator.check_feed_liveness()
        except PermissionError:
            liveness = {
                "status": getattr(health, "feed_liveness_status", "AUTH_REQUIRED"),
                "observation_age_seconds": None,
                "stale_duration_seconds": 0.0,
                "auth_required_reason": getattr(health, "auth_required_reason", "Broker authentication required"),
                "reconnect_state": "IDLE"
            }
        latency = float(getattr(health, "average_latency_ms", getattr(health, "latency", 0.0)) or 0.0)
        return {
            "status": liveness["status"],
            "latency_ms": latency,
            "stream_connected": bs.is_stream_connected(),
            "fallback_active": bs.is_fallback_active(),
            "observation_age_seconds": liveness.get("observation_age_seconds", 0.0),
            "stale_duration_seconds": liveness.get("stale_duration_seconds", 0.0),
            "auth_required_reason": liveness.get("auth_required_reason"),
            "reconnect_state": liveness.get("reconnect_state")
        }

    @staticmethod
    def _future_nifty_expiries(service: Any) -> List[str]:
        today = exchange_today()
        valid = []
        for value in service.lookup_expiries("NIFTY"):
            try:
                if datetime.strptime(value, "%Y-%m-%d").date() >= today:
                    valid.append(value)
            except (TypeError, ValueError):
                continue
        return sorted(valid)

    def resolve_expiries(self, bs: Any) -> List[str]:
        service = InstrumentService.get_instance()
        service.load_instruments(bs)
        valid = self._future_nifty_expiries(service)

        if not valid:
            # The in-memory instrument master is missing or so stale that every
            # NIFTY expiry it knows about is already in the past. Force one live
            # re-download and retry rather than silently returning nothing
            # forever (which freezes the option chain on a stale disk snapshot).
            raw = list(service.lookup_expiries("NIFTY"))
            logger.warning(
                "resolve_expiries: no future NIFTY expiry from current instrument index "
                f"(known={raw[:6]}{'...' if len(raw) > 6 else ''}, source={service.load_diagnostics().get('source')}); "
                "forcing instrument-master refresh."
            )
            service.load_instruments(bs, force_refresh=True)
            valid = self._future_nifty_expiries(service)
            if not valid:
                logger.error(
                    "resolve_expiries: still no resolvable future NIFTY expiry after forced refresh — "
                    "instrument master could not be synced; option chain will report UNAVAILABLE."
                )

        self.last_resolution = {
            **(self.last_resolution or {}),
            "expiries": valid,
            "resolved_at": datetime.now(_IST).isoformat(),
            "instrument_source": service.load_diagnostics().get("source"),
        }
        return valid

    def resolve_option_contracts(self, bs: Any, spot: float, expiry: Optional[str] = None) -> Dict[str, Any]:
        service = InstrumentService.get_instance()
        service.load_instruments(bs)
        expiries = self.resolve_expiries(bs)
        selected_expiry = expiry if expiry in expiries else (expiries[0] if expiries else None)
        if not selected_expiry or spot <= 0:
            return {"status": "UNAVAILABLE", "expiry": selected_expiry,
                    "reason": "missing_future_expiry_or_underlying_spot", "contracts": [], "strikes": []}

        strikes = service.lookup_strikes("NIFTY", selected_expiry)
        pairs = []
        for strike in strikes:
            ce = service.lookup_option_type("NIFTY", selected_expiry, strike, "CE")
            pe = service.lookup_option_type("NIFTY", selected_expiry, strike, "PE")
            if ce and pe:
                pairs.append((float(strike), ce, pe))
        if not pairs:
            return {"status": "UNAVAILABLE", "expiry": selected_expiry,
                    "reason": "no_paired_ce_pe_contracts", "contracts": [], "strikes": []}

        actual_strikes = [row[0] for row in pairs]
        differences = [round(actual_strikes[i + 1] - actual_strikes[i], 6)
                       for i in range(len(actual_strikes) - 1)
                       if actual_strikes[i + 1] > actual_strikes[i]]
        strike_step = Counter(differences).most_common(1)[0][0] if differences else None
        atm_index = min(range(len(actual_strikes)), key=lambda index: abs(actual_strikes[index] - spot))
        half = self.STRIKE_WINDOW_SIZE // 2
        start = max(0, min(atm_index - half, len(pairs) - self.STRIKE_WINDOW_SIZE))
        selected = pairs[start:start + self.STRIKE_WINDOW_SIZE]
        contracts: List[Dict[str, Any]] = []
        for strike, ce, pe in selected:
            for option_type, item in (("CE", ce), ("PE", pe)):
                contracts.append({
                    "instrument_token": int(item["instrument_token"]),
                    "trading_symbol": item["tradingsymbol"],
                    "exchange": item.get("exchange", "NFO"),
                    "strike": strike,
                    "option_type": option_type,
                    "expiry": selected_expiry,
                    "lot_size": _integer(item.get("lot_size")),
                    "tick_size": _number(item.get("tick_size")),
                })
        result = {
            "status": "READY" if len(contracts) == len(selected) * 2 else "PARTIAL",
            "expiry": selected_expiry,
            "all_expiries": expiries,
            "atm_strike": actual_strikes[atm_index],
            "strike_step": strike_step,
            "strikes": [row[0] for row in selected],
            "contracts": contracts,
            "contracts_resolved": len(contracts),
            "total_nifty_option_contracts": sum(
                1 for item in service._instruments
                if item.get("exchange") == "NFO" and item.get("name") == "NIFTY"
                and str(item.get("instrument_type", "")).upper() in {"CE", "PE"}
            ),
            "source": "Kite NFO instrument dump",
        }
        self.last_resolution = result
        return result

    def update_subscriptions(self, bs: Any, spot: float, expiry: str) -> None:
        if not bs.is_connected() or not bs.is_stream_connected():
            return
        resolution = self.resolve_option_contracts(bs, spot, expiry)
        new_symbols = [item["trading_symbol"] for item in resolution.get("contracts", [])]
        if new_symbols == self.subscribed_options:
            return
        old = [symbol for symbol in self.subscribed_options if symbol not in new_symbols]
        new = [symbol for symbol in new_symbols if symbol not in self.subscribed_options]
        if old:
            bs.unsubscribe_stream(old)
        if new:
            bs.subscribe_stream(new)
        self.subscribed_options = new_symbols
        self.last_spot_for_sub = spot
        self.last_expiry_for_sub = expiry

    @staticmethod
    def _quote_row(contract: Dict[str, Any], quote: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        ltp = _number(quote.get("last_price"))
        oi = _integer(quote.get("oi"))
        if ltp is None or oi is None:
            return None
        previous_close = _number((quote.get("ohlc") or {}).get("close"))
        change = ltp - previous_close if previous_close is not None else None
        change_pct = change / previous_close * 100.0 if change is not None and previous_close else None
        depth = quote.get("depth") or {}
        buy = depth.get("buy") or []
        sell = depth.get("sell") or []
        bid = _number((buy[0] or {}).get("price")) if buy else None
        ask = _number((sell[0] or {}).get("price")) if sell else None
        return {
            **contract,
            "ltp": ltp,
            "previous_close": previous_close,
            "change": change,
            "change_pct": change_pct,
            "oi": oi,
            "volume": _integer(quote.get("volume")),
            "bid": bid,
            "ask": ask,
            "bid_ask_spread": ask - bid if bid is not None and ask is not None else None,
            "market_depth": depth or None,
            "last_trade_time": _timestamp(quote.get("last_trade_time")),
            "quote_timestamp": _timestamp(quote.get("timestamp")),
            "iv": None,
            "iv_status": "UNAVAILABLE",
            "iv_reason": "kite_quote_payload_does_not_provide_iv_and_verified_risk_free_rate_is_unavailable",
        }

    @staticmethod
    def calculate_max_pain(rows: List[Dict[str, Any]]) -> Optional[float]:
        strikes = sorted({float(row["strike"]) for row in rows})
        if len(rows) != len(strikes) * 2 or not strikes:
            return None
        totals: Dict[float, float] = {}
        for settlement in strikes:
            payout = 0.0
            for row in rows:
                strike = float(row["strike"])
                oi = float(row.get("oi") or 0)
                if row["option_type"] == "CE":
                    payout += max(0.0, settlement - strike) * oi
                else:
                    payout += max(0.0, strike - settlement) * oi
            totals[settlement] = payout
        return min(totals, key=totals.get)

    @staticmethod
    def _iv_time_to_expiry(expiry: str, snapshot_timestamp: str) -> Optional[float]:
        try:
            observed = datetime.fromisoformat(str(snapshot_timestamp).replace("Z", "+00:00"))
            if observed.tzinfo is None:
                observed = observed.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
            expiry_day = date.fromisoformat(str(expiry)[:10])
            expiry_at = datetime.combine(expiry_day, datetime.min.time(), ZoneInfo("Asia/Kolkata")).replace(hour=15, minute=30)
            seconds = (expiry_at - observed.astimezone(ZoneInfo("Asia/Kolkata"))).total_seconds()
            return seconds / (365.0 * 24.0 * 3600.0) if seconds > 0 else None
        except (TypeError, ValueError):
            return None

    @classmethod
    def _apply_implied_volatility(
        cls,
        rows: List[Dict[str, Any]],
        spot: float,
        expiry: str,
        snapshot_timestamp: str,
        atm_strike: float,
    ) -> Dict[str, Any]:
        rate = RbiRiskFreeRateProvider.load_validated_rate()
        rate_value = _number(rate.get("rate")) if rate.get("status") in {"AVAILABLE", "DEGRADED"} else None
        time_to_expiry = cls._iv_time_to_expiry(expiry, snapshot_timestamp)
        if rate_value is None or time_to_expiry is None or spot <= 0:
            reason = "MISSING_RISK_FREE_RATE" if rate_value is None else "INVALID_OR_EXPIRED_OPTION_TIMESTAMP"
            for row in rows:
                row.update({"iv": None, "iv_status": "UNAVAILABLE", "iv_reason": reason,
                            "solver_status": "UNAVAILABLE", "iterations": 0, "convergence_error": None})
            return {"status": "UNAVAILABLE", "reason": reason, "rows": 0,
                    "atm_ce_iv": None, "atm_pe_iv": None, "atm_average_iv": None,
                    "rate": rate, "time_to_expiry_years": time_to_expiry}
        converged: List[Dict[str, Any]] = []
        for row in rows:
            solved = solve_implied_volatility(
                price=float(row["ltp"]), S=spot, K=float(row["strike"]), T=time_to_expiry,
                r=rate_value, option_type=str(row["option_type"]),
            )
            row.update({
                "iv": solved.iv, "iv_status": "AVAILABLE" if solved.iv is not None else "UNAVAILABLE",
                "iv_reason": solved.reason, "solver_status": solved.solver_status,
                "iterations": solved.iterations, "convergence_error": solved.convergence_error,
                "iv_input_timestamp": snapshot_timestamp, "rate_source": rate.get("source"),
                "rate_observation_date": rate.get("observation_date"),
                "option_snapshot_timestamp": snapshot_timestamp,
            })
            if solved.iv is not None:
                converged.append(row)
        atm_ce = next((row.get("iv") for row in converged if row["strike"] == atm_strike and row["option_type"] == "CE"), None)
        atm_pe = next((row.get("iv") for row in converged if row["strike"] == atm_strike and row["option_type"] == "PE"), None)
        atm_average = (float(atm_ce) + float(atm_pe)) / 2.0 if atm_ce is not None and atm_pe is not None else None
        return {
            "status": "AVAILABLE" if converged else "UNAVAILABLE",
            "reason": None if converged else "NO_CONVERGED_CONTRACT_IV",
            "rows": len(converged), "atm_ce_iv": atm_ce, "atm_pe_iv": atm_pe,
            "atm_average_iv": round(atm_average, 4) if atm_average is not None else None,
            "rate": rate, "time_to_expiry_years": time_to_expiry,
            "skew": [{"strike": row["strike"], "option_type": row["option_type"], "iv": row["iv"]}
                     for row in converged],
        }

    @staticmethod
    def _load_snapshot(path: Path) -> Optional[Dict[str, Any]]:
        try:
            with path.open("r", encoding="utf-8") as handle:
                value = json.load(handle)
            return value if isinstance(value, dict) else None
        except (OSError, ValueError):
            return None

    @staticmethod
    def _snapshot_age_seconds(snapshot: Dict[str, Any]) -> Optional[float]:
        """Age of a persisted option-chain snapshot in seconds, or None if it
        carries no usable timestamp."""
        ts = (snapshot.get("snapshot_timestamp")
              or snapshot.get("provider_timestamp")
              or snapshot.get("timestamp"))
        if not ts:
            return None
        try:
            observed = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
        if observed.tzinfo is None:
            observed = observed.replace(tzinfo=_IST)  # Kite quote times are IST-naive
        return max(0.0, (datetime.now(timezone.utc) - observed.astimezone(timezone.utc)).total_seconds())

    @classmethod
    def _apply_snapshot_freshness(cls, payload: Dict[str, Any], *, served_from_disk: bool) -> Dict[str, Any]:
        """Annotate an option-chain context with its age and staleness verdict.

        For a context served from the persisted disk snapshot (``served_from_disk``),
        anything past the hard ceiling is replaced with an explicit UNAVAILABLE
        result so no consumer can render a multi-hour-old chain as current.
        A freshly built context is only annotated (age + ``stale`` flag) and
        never rejected — it was just fetched, and an old quote timestamp there
        merely reflects low liquidity / a closed session.
        """
        if not isinstance(payload, dict):
            return payload
        age = cls._snapshot_age_seconds(payload)
        if age is None:
            payload.setdefault("stale", False)
            payload.setdefault("snapshot_age_seconds", None)
            return payload
        if served_from_disk and age > cls.SNAPSHOT_MAX_AGE_SECONDS:
            logger.warning(
                "Option-chain disk snapshot is %.1fh old (ceiling %.1fh) — refusing to serve it.",
                age / 3600.0, cls.SNAPSHOT_MAX_AGE_SECONDS / 3600.0,
            )
            return {
                "status": "UNAVAILABLE",
                "reason": "snapshot_exceeds_staleness_ceiling",
                "unavailable_message": cls.SNAPSHOT_TOO_OLD_MESSAGE,
                "snapshot_age_seconds": age,
                "staleness_ceiling_seconds": cls.SNAPSHOT_MAX_AGE_SECONDS,
                "last_snapshot_timestamp": payload.get("snapshot_timestamp"),
                "last_valid_snapshot": "EXPIRED",
                "stale": True,
            }
        payload["snapshot_age_seconds"] = age
        # A freshly built context was just fetched from the quote API; an old
        # quote timestamp only reflects low liquidity / a closed session, which
        # `freshness`/`observation_mode` already convey. Only the disk-fallback
        # path marks the served chain stale on age.
        payload["stale"] = served_from_disk and age > cls.SNAPSHOT_STALE_AFTER_SECONDS
        if payload["stale"]:
            payload.setdefault("stale_reason", "disk_snapshot_not_refreshed")
        return payload

    @staticmethod
    def _persist_snapshot(path: Path, snapshot: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=str(path.parent))
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(snapshot, handle, indent=2, default=str)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def build_option_chain_context(self, bs: Any, spot: float, target_expiries: List[str]) -> Dict[str, Any]:
        resolution = self.resolve_option_contracts(bs, spot, target_expiries[0] if target_expiries else None)
        contracts = resolution.get("contracts", [])
        if not contracts:
            persisted = self._load_snapshot(self.SNAPSHOT_PATH)
            if persisted:
                return self._apply_snapshot_freshness(persisted, served_from_disk=True)
            return {"status": "UNAVAILABLE", "reason": resolution.get("reason"),
                    "last_valid_snapshot": "UNAVAILABLE"}

        keys = [f"NFO:{item['trading_symbol']}" for item in contracts]
        quotes: Dict[str, Dict[str, Any]] = {}
        try:
            quotes = bs.get_quote(keys) or {}
        except Exception as exc:
            logger.warning("Kite option quote request failed: %s", exc)
        orch = None
        try:
            orch = bs._get_orchestrator()
        except PermissionError:
            orch = None
        rows: List[Dict[str, Any]] = []
        for contract, key in zip(contracts, keys):
            websocket_quote = (orch.latest_ticks.get(key) or orch.latest_ticks.get(contract["trading_symbol"]) or {}) if orch else {}
            quote = {**(quotes.get(key) or {}), **websocket_quote}
            row = self._quote_row(contract, quote)
            if row:
                rows.append(row)

        expected = len(contracts)
        complete = len(rows) >= 2
        quote_timestamps = [row.get("quote_timestamp") or row.get("last_trade_time") for row in rows]
        quote_timestamps = [value for value in quote_timestamps if value]
        snapshot_timestamp = max(quote_timestamps) if quote_timestamps else datetime.utcnow().isoformat() + "Z"
        if len(rows) == 0:
            persisted = self._load_snapshot(self.SNAPSHOT_PATH)
            if persisted:
                return self._apply_snapshot_freshness({
                    **persisted, "status": "MARKET_CLOSED", "last_valid_snapshot": "AVAILABLE",
                    "current_attempt_coverage": {"observed": len(rows), "expected": expected},
                }, served_from_disk=True)
            return {"status": "UNAVAILABLE", "expiry": resolution.get("expiry"),
                    "coverage": {"observed": len(rows), "expected": expected},
                    "reason": "incomplete_core_option_quote_rows", "last_valid_snapshot": "UNAVAILABLE"}

        previous = self._load_snapshot(self.SNAPSHOT_PATH)
        previous_rows = {}
        comparable_previous = bool(previous and previous.get("expiry") == resolution["expiry"]
                                   and previous.get("snapshot_timestamp") != snapshot_timestamp)
        if comparable_previous:
            previous_rows = {(row["strike"], row["option_type"]): row for row in previous.get("contracts", [])}
        for row in rows:
            old = previous_rows.get((row["strike"], row["option_type"]))
            row["oi_change"] = row["oi"] - int(old.get("oi") or 0) if old else None
            row["oi_change_provenance"] = "PREVIOUS_SNAPSHOT" if old else "SESSION_BASELINE"

        calls = [row for row in rows if row["option_type"] == "CE"]
        puts = [row for row in rows if row["option_type"] == "PE"]
        total_call_oi = sum(row["oi"] for row in calls)
        total_put_oi = sum(row["oi"] for row in puts)
        total_call_volume = sum(row.get("volume") or 0 for row in calls)
        total_put_volume = sum(row.get("volume") or 0 for row in puts)
        pcr = round(total_put_oi / total_call_oi, 2) if total_call_oi > 0 else 1.0
        volume_pcr = round(total_put_volume / total_call_volume, 2) if total_call_volume > 0 else 1.0
        max_pain = self.calculate_max_pain(rows)
        iv_summary = self._apply_implied_volatility(
            rows, spot, resolution["expiry"], snapshot_timestamp,
            float(resolution["atm_strike"]),
        )

        by_strike: Dict[float, Dict[str, Dict[str, Any]]] = {}
        for row in rows:
            by_strike.setdefault(float(row["strike"]), {})[row["option_type"]] = row
        strike_rows = []
        for strike in resolution["strikes"]:
            s_dict = by_strike.get(strike, {})
            call = s_dict.get("CE") or {}
            put = s_dict.get("PE") or {}
            if not call and not put:
                continue
            strike_rows.append({
                "strike": strike,
                "callOi": call.get("oi") or 0, "putOi": put.get("oi") or 0,
                "callChg": call.get("oi_change"), "putChg": put.get("oi_change"),
                "callVolume": call.get("volume") or 0, "putVolume": put.get("volume") or 0,
                "callLtp": call.get("ltp"), "putLtp": put.get("ltp"),
                "callBid": call.get("bid"), "callAsk": call.get("ask"),
                "putBid": put.get("bid"), "putAsk": put.get("ask"),
                "callIv": call.get("iv"), "putIv": put.get("iv"),
                "callRatio": (call.get("oi") or 0) / max(total_call_oi, 1),
                "putRatio": (put.get("oi") or 0) / max(total_put_oi, 1),
            })
        atm = by_strike.get(float(resolution["atm_strike"]), {})
        atm_call, atm_put = atm.get("CE") or {}, atm.get("PE") or {}
        atm_context = None
        if atm_call and atm_put and "ltp" in atm_call and "ltp" in atm_put:
            atm_context = {
                "strike": resolution["atm_strike"],
                "ce": atm_call, "pe": atm_put,
                "combined_premium": atm_call["ltp"] + atm_put["ltp"],
                "combined_oi": atm_call["oi"] + atm_put["oi"],
                "combined_volume": (atm_call.get("volume") or 0) + (atm_put.get("volume") or 0),
            }
        changes = [row for row in rows if row.get("oi_change") is not None]
        oi_change = {
            "status": "AVAILABLE" if changes else "BASELINE_CREATED",
            "provenance": "PREVIOUS_SNAPSHOT" if changes else "SESSION_BASELINE",
            "baseline_timestamp": None if changes else snapshot_timestamp,
            "strongest_call_build_up": max((row for row in changes if row["option_type"] == "CE"), key=lambda row: row["oi_change"], default=None),
            "strongest_put_build_up": max((row for row in changes if row["option_type"] == "PE"), key=lambda row: row["oi_change"], default=None),
        }
        try:
            from src.broker.services.market_status_service import MarketStatusService
            session_status = str(MarketStatusService.get_instance().get_market_status().status).upper()
        except Exception:
            session_status = "UNKNOWN"
        market_closed = any(value in session_status for value in ("CLOSED", "HOLIDAY", "POST_MARKET"))

        # Total OI and Volumes
        total_oi = total_call_oi + total_put_oi
        total_volume = total_call_volume + total_put_volume
        total_call_oi_cr = round(total_call_oi / 10000000.0, 2) if total_call_oi else 0.0
        total_put_oi_cr = round(total_put_oi / 10000000.0, 2) if total_put_oi else 0.0
        total_oi_cr = round(total_oi / 10000000.0, 2) if total_oi else 0.0
        total_vol_lakh = round(total_volume / 100000.0, 2) if total_volume else 0.0

        # Highest OI strikes (Walls & Concentrations)
        highest_call_oi_strike = max(calls, key=lambda x: x["oi"])["strike"] if calls else None
        highest_put_oi_strike = max(puts, key=lambda x: x["oi"])["strike"] if puts else None

        sorted_calls_by_oi = sorted(calls, key=lambda x: x["oi"], reverse=True)
        sorted_puts_by_oi = sorted(puts, key=lambda x: x["oi"], reverse=True)
        oi_concentration = [
            {"strike": c["strike"], "type": "CE", "oi_cr": round(c["oi"] / 10000000.0, 2), "oi": c["oi"]}
            for c in sorted_calls_by_oi[:3]
        ] + [
            {"strike": p["strike"], "type": "PE", "oi_cr": round(p["oi"] / 10000000.0, 2), "oi": p["oi"]}
            for p in sorted_puts_by_oi[:3]
        ]

        # Options Bias Synthesis
        if pcr is not None:
            if pcr >= 1.15:
                options_bias = "BULLISH"
            elif pcr <= 0.85:
                options_bias = "BEARISH"
            else:
                options_bias = "NEUTRAL"
        else:
            options_bias = "NEUTRAL"

        # Calendar DTE
        try:
            exp_date_obj = date.fromisoformat(str(resolution["expiry"])[:10])
            today_date_obj = exchange_today()
            calendar_dte = max(0, (exp_date_obj - today_date_obj).days)
        except Exception:
            calendar_dte = 1

        # Black-Scholes Greeks for ATM Contract
        atm_iv_pct = iv_summary.get("atm_average_iv")
        rate_val = (iv_summary.get("rate") or {}).get("rate", 0.065)
        t_years = iv_summary.get("time_to_expiry_years", 1.0 / 365.0)
        atm_greeks = None
        if atm_iv_pct and spot > 0 and t_years and t_years > 0:
            try:
                sigma = atm_iv_pct / 100.0
                r = float(rate_val) if rate_val else 0.065
                K = float(resolution["atm_strike"])
                T = max(t_years, 0.0001)
                d1 = (math.log(spot / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
                d2 = d1 - sigma * math.sqrt(T)
                pdf_d1 = (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * d1 * d1)

                delta_ce = 0.5 * (1.0 + math.erf(d1 / math.sqrt(2.0)))
                delta_pe = delta_ce - 1.0
                gamma = pdf_d1 / (spot * sigma * math.sqrt(T))
                vega = (spot * math.sqrt(T) * pdf_d1) / 100.0
                theta_annual_ce = -(spot * pdf_d1 * sigma) / (2.0 * math.sqrt(T)) - r * K * math.exp(-r * T) * (0.5 * (1.0 + math.erf(d2 / math.sqrt(2.0))))
                theta_ce = theta_annual_ce / 365.0

                atm_greeks = {
                    "delta_ce": round(delta_ce, 3),
                    "delta_pe": round(delta_pe, 3),
                    "delta": round(delta_ce, 3),
                    "gamma": round(gamma, 5),
                    "theta": round(theta_ce, 2),
                    "vega": round(vega, 2),
                    "status": "CALCULATED",
                }
            except Exception as e:
                logger.warning("Failed to calculate ATM greeks: %s", e)
                atm_greeks = {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "status": "UNAVAILABLE"}
        else:
            atm_greeks = {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "status": "UNAVAILABLE"}

        snapshot = {
            "status": "READY",
            "underlying_spot": spot,
            "expiry": resolution["expiry"],
            "current_weekly_expiry": resolution["expiry"],
            "calendar_dte": calendar_dte,
            "all_expiries": resolution["all_expiries"],
            "snapshot_timestamp": snapshot_timestamp,
            "provider_timestamp": snapshot_timestamp,
            "timestamp": snapshot_timestamp,
            "source": "Kite Quote API",
            "observation_mode": "LAST_VALID_SNAPSHOT" if market_closed else "LIVE",
            "freshness": "MARKET_CLOSED" if market_closed else "FRESH",
            "quality": "VALIDATED",
            "coverage": {"observed": len(rows), "expected": expected, "strikes": len(strike_rows)},
            "contracts_resolved": expected,
            "total_nifty_option_contracts": resolution["total_nifty_option_contracts"],
            "atm_strike": resolution["atm_strike"],
            "strike_step": resolution["strike_step"],
            "strikes": strike_rows,
            "contracts": rows,
            "pcr": pcr,
            "pcr_provenance": {"put_oi": total_put_oi, "call_oi": total_call_oi,
                               "strike_window": resolution["strikes"], "timestamp": snapshot_timestamp},
            "volume_pcr": volume_pcr,
            "max_pain": max_pain,
            "max_pain_provenance": {"expiry": resolution["expiry"], "strike_coverage": len(strike_rows),
                                    "timestamp": snapshot_timestamp},
            "total_call_oi": total_call_oi,
            "total_put_oi": total_put_oi,
            "total_oi": total_oi,
            "total_call_oi_cr": total_call_oi_cr,
            "total_put_oi_cr": total_put_oi_cr,
            "total_oi_cr": total_oi_cr,
            "total_call_volume": total_call_volume,
            "total_put_volume": total_put_volume,
            "total_volume": total_volume,
            "total_vol_lakh": total_vol_lakh,
            "highest_call_oi_strike": highest_call_oi_strike,
            "highest_put_oi_strike": highest_put_oi_strike,
            "call_wall": highest_call_oi_strike,
            "put_wall": highest_put_oi_strike,
            "oi_concentration": oi_concentration,
            "options_bias": options_bias,
            "options_confirmation": options_bias.get("bias", "BULLISH") if isinstance(options_bias, dict) else "BULLISH",
            "atm_greeks": atm_greeks,
            "greeks": atm_greeks,
            "oi_change": oi_change,
            "atm_context": atm_context,
            "atm_iv": iv_summary.get("atm_average_iv"),
            "atm_ce_iv": iv_summary.get("atm_ce_iv"),
            "atm_pe_iv": iv_summary.get("atm_pe_iv"),
            "iv_status": iv_summary.get("status"),
            "iv_reason": iv_summary.get("reason"),
            "iv_rows": iv_summary.get("rows", 0),
            "iv_skew": iv_summary.get("skew") or [],
            "iv_time_to_expiry_years": iv_summary.get("time_to_expiry_years"),
            "risk_free_rate": iv_summary.get("rate"),
            "last_valid_snapshot": "AVAILABLE",
            "schema_version": "2.0",
        }
        self._persist_snapshot(self.SNAPSHOT_PATH, snapshot)
        return self._apply_snapshot_freshness(snapshot, served_from_disk=False)
