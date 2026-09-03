from __future__ import annotations

import os
import json
from dataclasses import dataclass
from datetime import datetime, date, timezone, timedelta
from typing import Any, Dict, List, Optional

from src.market_data.models.canonical_option_chain import CanonicalOptionChainSnapshot
from src.market_data.models.quality_enums import DataQualityStatus
from src.analytics.options.greeks import calculate_black_scholes_greeks


@dataclass(frozen=True)
class OptionChainSummary:
    """
    Derived canonical intelligence summary of an option chain snapshot.
    Identifies ATM strike, key open interest concentrations, and Put-Call Ratio (PCR).
    """
    underlying_id: str
    expiry: str
    underlying_price: float
    atm_strike: float
    total_call_oi: int
    total_put_oi: int
    pcr: float
    max_call_oi_strike: Optional[float]
    max_put_oi_strike: Optional[float]
    total_call_volume: int
    total_put_volume: int
    chain_timestamp: datetime
    quality: DataQualityStatus = DataQualityStatus.VALID
    strike_universe: Optional[List[Dict[str, Any]]] = None


class OptionChainAggregator:
    """
    Provider-independent option chain metrics aggregator.
    Extracts structural option boundaries and computes session Delta OI from morning baselines.
    """
    _opening_oi_baseline: Dict[str, Dict[str, Dict[float, Dict[str, int]]]] = {}  # session_date -> expiry -> strike -> {CE, PE}
    _baseline_established: Dict[str, bool] = {}  # session_date -> bool
    _loaded_date: Optional[str] = None

    @classmethod
    def _ensure_disk_loaded(cls, session_date_str: Optional[str] = None) -> None:
        ist = timezone(timedelta(hours=5, minutes=30))
        target_date = session_date_str or datetime.now(ist).strftime("%Y-%m-%d")
        if cls._loaded_date == target_date and target_date in cls._opening_oi_baseline:
            return
        cls._loaded_date = target_date

        cls._opening_oi_baseline.setdefault(target_date, {})

        # 1. Try loading from LightweightSessionStore
        try:
            from src.storage.lightweight_session_store import LightweightSessionStore
            store = LightweightSessionStore.get_instance()
            baseline_doc = store.load_options_baseline(target_date)
            if baseline_doc and baseline_doc.strike_baseline:
                exp = baseline_doc.expiry_date or "NEAR"
                cls._opening_oi_baseline[target_date].setdefault(exp, {})
                for row in baseline_doc.strike_baseline:
                    s = float(row.get("strike", 0))
                    c_oi = int(row.get("ce_oi", 0) or row.get("call_oi", 0) or 0)
                    p_oi = int(row.get("pe_oi", 0) or row.get("put_oi", 0) or 0)
                    cls._opening_oi_baseline[target_date][exp][s] = {"CE": c_oi, "PE": p_oi}
                cls._baseline_established[target_date] = True
                return
        except Exception:
            pass

        # 2. Try loading from cache JSON for target date or newest available baseline
        cache_path = os.path.join("data", "cache", f"oi_baseline_{target_date.replace('-', '')}.json")
        if not os.path.exists(cache_path) and os.path.exists(os.path.join("data", "cache")):
            try:
                candidate_files = sorted(
                    [f for f in os.listdir(os.path.join("data", "cache")) if f.startswith("oi_baseline_") and f.endswith(".json")],
                    reverse=True
                )
                if candidate_files:
                    cache_path = os.path.join("data", "cache", candidate_files[0])
            except Exception:
                pass

        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    for exp, st_map in raw.items():
                        cls._opening_oi_baseline[target_date].setdefault(exp, {})
                        for s_key, vals in st_map.items():
                            cls._opening_oi_baseline[target_date][exp][float(s_key)] = vals
                    if cls._opening_oi_baseline[target_date]:
                        cls._baseline_established[target_date] = True
            except Exception:
                pass

    @classmethod
    def _flush_to_disk(cls, session_date_str: Optional[str] = None) -> None:
        ist = timezone(timedelta(hours=5, minutes=30))
        target_date = session_date_str or datetime.now(ist).strftime("%Y-%m-%d")
        os.makedirs(os.path.join("data", "cache"), exist_ok=True)
        cache_path = os.path.join("data", "cache", f"oi_baseline_{target_date.replace('-', '')}.json")
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cls._opening_oi_baseline.get(target_date, {}), f, indent=2)
        except Exception:
            pass

    @classmethod
    def set_morning_baseline(cls, expiry: str, strike: float, call_oi: int, put_oi: int, session_date_str: Optional[str] = None) -> None:
        """Stores the initial 09:15:00 IST open interest baseline for a strike and persists to disk."""
        ist = timezone(timedelta(hours=5, minutes=30))
        s_date = session_date_str or datetime.now(ist).strftime("%Y-%m-%d")
        cls._ensure_disk_loaded(s_date)
        if s_date not in cls._opening_oi_baseline:
            cls._opening_oi_baseline[s_date] = {}
        if expiry not in cls._opening_oi_baseline[s_date]:
            cls._opening_oi_baseline[s_date][expiry] = {}
        cls._opening_oi_baseline[s_date][expiry][strike] = {"CE": call_oi, "PE": put_oi}
        cls._baseline_established[s_date] = True
        cls._flush_to_disk(s_date)

    @classmethod
    def take_opening_baseline_snapshot(cls, snapshot: CanonicalOptionChainSnapshot) -> None:
        """Explicitly snapshots 09:15:00 IST opening OI baseline from the opening snapshot."""
        if not snapshot or not snapshot.strikes:
            return
        s_date = str(snapshot.session_date)
        expiry = snapshot.expiry
        cls._ensure_disk_loaded(s_date)
        if s_date not in cls._opening_oi_baseline:
            cls._opening_oi_baseline[s_date] = {}
        if expiry not in cls._opening_oi_baseline[s_date]:
            cls._opening_oi_baseline[s_date][expiry] = {}
        for s in snapshot.strikes:
            c_oi = (s.call.oi or 0) if s.call is not None else 0
            p_oi = (s.put.oi or 0) if s.put is not None else 0
            cls._opening_oi_baseline[s_date][expiry][s.strike] = {"CE": c_oi, "PE": p_oi}
        cls._baseline_established[s_date] = True
        cls._flush_to_disk(s_date)

    @classmethod
    def get_morning_baseline(cls, expiry: str, strike: float, session_date_str: Optional[str] = None) -> Optional[Dict[str, int]]:
        ist = timezone(timedelta(hours=5, minutes=30))
        s_date = session_date_str or datetime.now(ist).strftime("%Y-%m-%d")
        cls._ensure_disk_loaded(s_date)
        date_map = cls._opening_oi_baseline.get(s_date, {})
        res = date_map.get(expiry, {}).get(strike)
        if res is None:
            for exp_key, s_dict in date_map.items():
                if strike in s_dict:
                    return s_dict[strike]
        return res

    @classmethod
    def aggregate(cls, snapshot: CanonicalOptionChainSnapshot) -> OptionChainSummary:
        und_price = snapshot.underlying_price
        strikes = snapshot.strikes
        s_date = str(snapshot.session_date)
        cls._ensure_disk_loaded(s_date)

        if not strikes:
            return OptionChainSummary(
                underlying_id=snapshot.underlying_instrument_id,
                expiry=snapshot.expiry,
                underlying_price=und_price,
                atm_strike=und_price,
                total_call_oi=0,
                total_put_oi=0,
                pcr=0.0,
                max_call_oi_strike=None,
                max_put_oi_strike=None,
                total_call_volume=0,
                total_put_volume=0,
                chain_timestamp=snapshot.captured_at,
                quality=DataQualityStatus.UNAVAILABLE,
                strike_universe=[],
            )

        # 1. Find ATM strike (closest to spot price)
        atm_strike = min(strikes, key=lambda s: abs(s.strike - und_price)).strike

        total_call_oi = 0
        total_put_oi = 0
        total_call_vol = 0
        total_put_vol = 0

        max_call_oi = -1
        max_call_strike: Optional[float] = None
        max_put_oi = -1
        max_put_strike: Optional[float] = None

        strike_rows: List[Dict[str, Any]] = []

        # FIX 8: Compute exact DTE from contract expiry timestamp and capture timestamp
        expiry_dt: Optional[datetime] = None
        try:
            if isinstance(snapshot.expiry, str):
                exp_date = datetime.strptime(snapshot.expiry.strip()[:10], "%Y-%m-%d").date()
            elif hasattr(snapshot.expiry, "strftime"):
                exp_date = snapshot.expiry if isinstance(snapshot.expiry, date) else snapshot.expiry.date()
            else:
                exp_date = snapshot.session_date

            # NSE F&O contracts expire at 15:30:00 IST on the expiry date
            ist = timezone(timedelta(hours=5, minutes=30))
            expiry_dt = datetime(exp_date.year, exp_date.month, exp_date.day, 15, 30, 0, tzinfo=ist)
        except Exception:
            expiry_dt = None

        now_ts = snapshot.captured_at
        if expiry_dt and now_ts:
            diff_seconds = (expiry_dt - now_ts).total_seconds()
            # Same-day expiry edge case: clamp to a small positive epsilon (1 second in fractional years)
            # to prevent division by zero or negative DTE in Black-Scholes formulas
            EPSILON_YEARS = 1.0 / (365.0 * 86400.0)
            dte_years = max(EPSILON_YEARS, diff_seconds / (365.0 * 86400.0))
        else:
            dte_years = max(1.0 / 365.0, 3.0 / 365.0)

        is_baseline_ready = cls._baseline_established.get(s_date, False)

        for s in strikes:
            c_iv = getattr(s.call, "iv", None) if s.call is not None else None
            if c_iv is None and c_ltp > 0 and und_price > 0 and dte_years > 0 and s.call is not None:
                from src.options_engine.iv import calculate_implied_volatility
                solved_c = calculate_implied_volatility(c_ltp, und_price, s.strike, dte_years, 0.07, "CE")
                if solved_c > 0:
                    c_iv = round(solved_c, 2)

            p_oi = (s.put.oi or 0) if s.put is not None else 0
            p_vol = (s.put.volume or 0) if s.put is not None else 0
            p_ltp = (getattr(s.put, "last_price", None) or getattr(s.put, "ltp", None) or 0.0) if s.put is not None else 0.0
            p_iv = getattr(s.put, "iv", None) if s.put is not None else None
            if p_iv is None and p_ltp > 0 and und_price > 0 and dte_years > 0 and s.put is not None:
                from src.options_engine.iv import calculate_implied_volatility
                solved_p = calculate_implied_volatility(p_ltp, und_price, s.strike, dte_years, 0.07, "PE")
                if solved_p > 0:
                    p_iv = round(solved_p, 2)

            total_call_oi += c_oi
            total_call_vol += c_vol
            if c_oi > max_call_oi:
                max_call_oi = c_oi
                max_call_strike = s.strike

            total_put_oi += p_oi
            total_put_vol += p_vol
            if p_oi > max_put_oi:
                max_put_oi = p_oi
                max_put_strike = s.strike

            # FIX 6 & FIX 7: Compute Delta OI relative to session opening baseline
            baseline = cls.get_morning_baseline(snapshot.expiry, s.strike, s_date)
            if baseline is not None:
                c_chg_oi: Any = c_oi - baseline.get("CE", c_oi)
                p_chg_oi: Any = p_oi - baseline.get("PE", p_oi)
            elif is_baseline_ready:
                # Baseline established at 09:15, but this strike entered range mid-day
                c_chg_oi = "NO BASELINE (NEW STRIKE)"
                p_chg_oi = "NO BASELINE (NEW STRIKE)"
            else:
                # No baseline established yet on disk or live snapshot
                c_chg_oi = "PENDING BASELINE"
                p_chg_oi = "PENDING BASELINE"

            # Compute Black-Scholes Greeks
            ce_greeks = calculate_black_scholes_greeks(
                spot=und_price,
                strike=s.strike,
                time_to_expiry_years=dte_years,
                volatility=c_iv / 100.0 if c_iv > 0 else 0.13,
                option_type="CE",
            )
            pe_greeks = calculate_black_scholes_greeks(
                spot=und_price,
                strike=s.strike,
                time_to_expiry_years=dte_years,
                volatility=p_iv / 100.0 if p_iv > 0 else 0.13,
                option_type="PE",
            )

            strike_rows.append({
                "strike": s.strike,
                "ce_ltp": c_ltp,
                "ce_oi": c_oi,
                "ce_change_oi": c_chg_oi,
                "ce_volume": c_vol,
                "ce_iv": c_iv,
                "ce_delta": ce_greeks.delta if ce_greeks else None,
                "ce_theta": ce_greeks.theta if ce_greeks else None,
                "pe_ltp": p_ltp,
                "pe_oi": p_oi,
                "pe_change_oi": p_chg_oi,
                "pe_volume": p_vol,
                "pe_iv": p_iv,
                "pe_delta": pe_greeks.delta if pe_greeks else None,
                "pe_theta": pe_greeks.theta if pe_greeks else None,
            })

        # 2. PCR calculation (total Put OI / total Call OI)
        pcr = round(total_put_oi / total_call_oi, 4) if total_call_oi > 0 else 0.0

        return OptionChainSummary(
            underlying_id=snapshot.underlying_instrument_id,
            expiry=snapshot.expiry,
            underlying_price=und_price,
            atm_strike=atm_strike,
            total_call_oi=total_call_oi,
            total_put_oi=total_put_oi,
            pcr=pcr,
            max_call_oi_strike=max_call_strike,
            max_put_oi_strike=max_put_strike,
            total_call_volume=total_call_vol,
            total_put_volume=total_put_vol,
            chain_timestamp=snapshot.captured_at,
            quality=DataQualityStatus.VALID,
            strike_universe=strike_rows,
        )

