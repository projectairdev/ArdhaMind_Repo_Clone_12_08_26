# src/intelligence_engine/intraday_scoring_evaluator.py
"""
IntradayPredictionScoringEvaluator — Mathematically Trustworthy Multi-Horizon Evaluation.

Evaluates Forward Outlook forecasts against authoritative minute candle price series (nifty_candles_cache.json)
or live session snapshots.

Strict Invariants:
1. Direction Accuracy and Range Containment are strictly separated.
2. Range scenarios have direction = N/A (excluded from directional accuracy).
3. MFE/MAE:
   - Bullish: MFE = max(high - spot_0), MAE = max(spot_0 - low)
   - Bearish: MFE = max(spot_0 - low), MAE = max(high - spot_0)
   - Range: Directional MFE/MAE is None (null, not 0.0).
4. Range Containment tracks endpoint_inside_range, full_horizon_contained, temporary_breach, sustained_breakout.
5. Incomplete horizons (end of session) are excluded from evaluation denominators.
6. Distinguishes RAW_OBSERVATIONS from INDEPENDENT_WINDOWS (spaced by horizon, e.g. 30m).
7. Confidence calibration reports scenario success, directional accuracy, and invalidation rates separately.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class IntradayPredictionScoringEvaluator:
    """
    Empirical multi-horizon evaluator for intraday predictions.
    """

    @classmethod
    def evaluate_session_history(
        cls,
        session_history_path: str = "/opt/ardhamind/staging/data/cache/session_history_2026-08-24.json",
        candles_cache_path: str = "/opt/ardhamind/staging/data/cache/nifty_candles_cache.json",
        independent_window_minutes: int = 30
    ) -> Dict[str, Any]:
        s_path = Path(session_history_path)
        c_path = Path(candles_cache_path)

        if not s_path.exists():
            return {"status": "FILE_NOT_FOUND", "path": str(s_path)}

        with open(s_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Load candle series if available for authoritative minute-level truth
        candles_by_minute: Dict[str, Dict[str, Any]] = {}
        candle_list: List[Dict[str, Any]] = []
        if c_path.exists():
            try:
                with open(c_path, "r", encoding="utf-8") as f:
                    raw_candles = json.load(f)
                    for c in raw_candles:
                        # c["date"] e.g. "2026-08-24T09:15:00+05:30"
                        d_str = c["date"]
                        hhmm = d_str[11:16]
                        c_dict = {
                            "hhmm": hhmm,
                            "open": float(c["open"]),
                            "high": float(c["high"]),
                            "low": float(c["low"]),
                            "close": float(c["close"]),
                            "dt_str": d_str,
                        }
                        candles_by_minute[hhmm] = c_dict
                        candle_list.append(c_dict)
            except Exception:
                pass

        snapshots = data.get("snapshots", [])
        if not snapshots:
            return {"status": "NO_SNAPSHOTS"}

        # Extract regular session live snapshots (09:15 to 15:30 IST / 03:45 to 10:00 UTC)
        live_records: List[Dict[str, Any]] = []
        for s in snapshots:
            ts_str = s.get("timestamp") or ""
            if len(ts_str) >= 16 and "T03:45" <= ts_str[10:16] <= "T10:00":
                fo = s.get("forward_outlook")
                if fo:
                    dt_utc = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    dt_ist = dt_utc + timedelta(hours=5, minutes=30)
                    hhmm = dt_ist.strftime("%H:%M")
                    
                    # Authoritative spot from minute candle close (or fallback to snapshot spot)
                    if hhmm in candles_by_minute:
                        spot_val = candles_by_minute[hhmm]["close"]
                    else:
                        _sv = s.get("spot") or s.get("close")
                        spot_val = float(_sv) if _sv is not None else None
                    if spot_val is None:
                        # No real spot for this snapshot — skip it rather than
                        # scoring the outlook against a fabricated price.
                        continue

                    live_records.append({
                        "dt_utc": dt_utc,
                        "dt_ist": dt_ist,
                        "hhmm": hhmm,
                        "timestamp": ts_str,
                        "spot": spot_val,
                        "forward_outlook": fo,
                    })

        if not live_records:
            return {"status": "NO_LIVE_RECORDS"}

        live_records.sort(key=lambda x: x["dt_utc"])

        # Horizon minutes to evaluate
        horizon_minutes_map = {
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "60m": 60,
        }

        evaluated_forecasts: List[Dict[str, Any]] = []
        last_independent_dt: Optional[datetime] = None

        for i, rec in enumerate(live_records):
            dt_ist = rec["dt_ist"]
            spot_0 = rec["spot"]
            fo = rec["forward_outlook"]
            classification = fo.get("classification") or fo.get("scenario") or "UNKNOWN"
            confidence = fo.get("confidence") or "UNKNOWN"
            support = fo.get("support")
            resistance = fo.get("resistance")
            vwap = fo.get("vwap")

            is_independent = False
            if last_independent_dt is None or (dt_ist - last_independent_dt).total_seconds() >= (independent_window_minutes * 60):
                is_independent = True
                last_independent_dt = dt_ist

            outcomes: Dict[str, Any] = {}

            for h_name, h_mins in horizon_minutes_map.items():
                target_dt_ist = dt_ist + timedelta(minutes=h_mins)
                target_hhmm = target_dt_ist.strftime("%H:%M")

                if target_hhmm > "15:30":
                    outcomes[h_name] = {"status": "INCOMPLETE_HORIZON"}
                    continue

                # Find intermediate candles in interval [dt_ist, target_dt_ist]
                inter_candles = []
                if candle_list:
                    start_str = dt_ist.strftime("%H:%M")
                    end_str = target_hhmm
                    inter_candles = [c for c in candle_list if start_str <= c["hhmm"] <= end_str]

                # End observation spot
                if target_hhmm in candles_by_minute:
                    future_spot = candles_by_minute[target_hhmm]["close"]
                else:
                    # Find closest snapshot in live_records
                    matching_recs = [r for r in live_records[i + 1:] if r["hhmm"] >= target_hhmm]
                    if matching_recs:
                        future_spot = matching_recs[0]["spot"]
                    else:
                        outcomes[h_name] = {"status": "INCOMPLETE_HORIZON"}
                        continue

                change_pts = round(future_spot - spot_0, 2)

                # 1. Direction Accuracy
                if "BEARISH" in classification:
                    direction_correct = (future_spot < spot_0)
                elif "BULLISH" in classification:
                    direction_correct = (future_spot > spot_0)
                else:
                    direction_correct = None  # N/A for RANGE scenarios

                # 2. Range Containment
                if support is not None and resistance is not None:
                    endpoint_inside_range = (support <= future_spot <= resistance)
                    if inter_candles:
                        min_low = min(c["low"] for c in inter_candles)
                        max_high = max(c["high"] for c in inter_candles)
                        full_horizon_contained = (support <= min_low and max_high <= resistance)
                        range_break_above = (max_high > resistance)
                        range_break_below = (min_low < support)
                    else:
                        full_horizon_contained = endpoint_inside_range
                        range_break_above = (future_spot > resistance)
                        range_break_below = (future_spot < support)

                    temporary_breach = (not full_horizon_contained and endpoint_inside_range)
                    sustained_breakout = (not full_horizon_contained and not endpoint_inside_range)
                else:
                    endpoint_inside_range = None
                    full_horizon_contained = None
                    temporary_breach = None
                    sustained_breakout = None
                    range_break_above = None
                    range_break_below = None

                # 3. Confirmation & Invalidation
                confirmation_hit = None
                invalidation_hit = None
                if "BEARISH" in classification:
                    # Bearish confirmation: spot remained below VWAP or broke support
                    confirmation_hit = (future_spot <= vwap) if vwap is not None else None
                    # Invalidation: broke resistance
                    invalidation_hit = (range_break_above is True)
                elif "BULLISH" in classification:
                    confirmation_hit = (future_spot >= vwap) if vwap is not None else None
                    invalidation_hit = (range_break_below is True)
                else:  # RANGE_CONTINUATION
                    confirmation_hit = endpoint_inside_range
                    invalidation_hit = sustained_breakout

                # 4. Scenario Success
                if "BEARISH" in classification:
                    scenario_success = (direction_correct is True and invalidation_hit is not True)
                elif "BULLISH" in classification:
                    scenario_success = (direction_correct is True and invalidation_hit is not True)
                else:  # RANGE
                    scenario_success = (endpoint_inside_range is True and sustained_breakout is not True)

                # 5. MFE & MAE
                if inter_candles:
                    h_high = max(c["high"] for c in inter_candles)
                    h_low = min(c["low"] for c in inter_candles)
                    if "BEARISH" in classification:
                        mfe = round(max(0.0, spot_0 - h_low), 2)
                        mae = round(max(0.0, h_high - spot_0), 2)
                    elif "BULLISH" in classification:
                        mfe = round(max(0.0, h_high - spot_0), 2)
                        mae = round(max(0.0, spot_0 - h_low), 2)
                    else:
                        mfe = None
                        mae = None
                else:
                    mfe = None
                    mae = None

                outcomes[h_name] = {
                    "status": "COMPLETED",
                    "future_spot": future_spot,
                    "change_points": change_pts,
                    "direction_correct": direction_correct,
                    "endpoint_inside_range": endpoint_inside_range,
                    "full_horizon_contained": full_horizon_contained,
                    "temporary_breach": temporary_breach,
                    "sustained_breakout": sustained_breakout,
                    "confirmation_hit": confirmation_hit,
                    "invalidation_hit": invalidation_hit,
                    "scenario_success": scenario_success,
                    "mfe": mfe,
                    "mae": mae,
                }

            evaluated_forecasts.append({
                "timestamp": rec["timestamp"],
                "hhmm_ist": rec["hhmm"],
                "spot": spot_0,
                "classification": classification,
                "confidence": confidence,
                "support": support,
                "resistance": resistance,
                "vwap": vwap,
                "is_independent": is_independent,
                "outcomes": outcomes,
            })

        # Aggregation function
        def _calc_stats(forecast_list: List[Dict[str, Any]]) -> Dict[str, Any]:
            by_scenario: Dict[str, Any] = {}
            by_confidence: Dict[str, Any] = {}

            for f in forecast_list:
                sc = f["classification"]
                cf = f["confidence"]

                if sc not in by_scenario:
                    by_scenario[sc] = {
                        "count": 0,
                        "5m": {"evals": 0, "dir_hits": 0, "dir_evals": 0, "range_endpoint_hits": 0, "full_contain_hits": 0, "temp_breach_hits": 0, "scenario_success": 0, "confirm_hits": 0, "invalid_hits": 0, "mfes": [], "maes": []},
                        "15m": {"evals": 0, "dir_hits": 0, "dir_evals": 0, "range_endpoint_hits": 0, "full_contain_hits": 0, "temp_breach_hits": 0, "scenario_success": 0, "confirm_hits": 0, "invalid_hits": 0, "mfes": [], "maes": []},
                        "30m": {"evals": 0, "dir_hits": 0, "dir_evals": 0, "range_endpoint_hits": 0, "full_contain_hits": 0, "temp_breach_hits": 0, "scenario_success": 0, "confirm_hits": 0, "invalid_hits": 0, "mfes": [], "maes": []},
                        "60m": {"evals": 0, "dir_hits": 0, "dir_evals": 0, "range_endpoint_hits": 0, "full_contain_hits": 0, "temp_breach_hits": 0, "scenario_success": 0, "confirm_hits": 0, "invalid_hits": 0, "mfes": [], "maes": []},
                    }
                by_scenario[sc]["count"] += 1

                for h in ("5m", "15m", "30m", "60m"):
                    out = f["outcomes"].get(h)
                    if out and out.get("status") == "COMPLETED":
                        s_h = by_scenario[sc][h]
                        s_h["evals"] += 1
                        if out["direction_correct"] is not None:
                            s_h["dir_evals"] += 1
                            if out["direction_correct"]:
                                s_h["dir_hits"] += 1
                        if out["endpoint_inside_range"]:
                            s_h["range_endpoint_hits"] += 1
                        if out["full_horizon_contained"]:
                            s_h["full_contain_hits"] += 1
                        if out["temporary_breach"]:
                            s_h["temp_breach_hits"] += 1
                        if out["scenario_success"]:
                            s_h["scenario_success"] += 1
                        if out["confirmation_hit"]:
                            s_h["confirm_hits"] += 1
                        if out["invalidation_hit"]:
                            s_h["invalid_hits"] += 1
                        if out["mfe"] is not None:
                            s_h["mfes"].append(out["mfe"])
                        if out["mae"] is not None:
                            s_h["maes"].append(out["mae"])

                if cf not in by_confidence:
                    by_confidence[cf] = {
                        "count": 0,
                        "30m_evals": 0,
                        "30m_dir_evals": 0,
                        "30m_dir_hits": 0,
                        "30m_scenario_success": 0,
                        "30m_full_contain_hits": 0,
                        "30m_invalid_hits": 0,
                    }
                by_confidence[cf]["count"] += 1
                out_30 = f["outcomes"].get("30m")
                if out_30 and out_30.get("status") == "COMPLETED":
                    c_h = by_confidence[cf]
                    c_h["30m_evals"] += 1
                    if out_30["direction_correct"] is not None:
                        c_h["30m_dir_evals"] += 1
                        if out_30["direction_correct"]:
                            c_h["30m_dir_hits"] += 1
                    if out_30["scenario_success"]:
                        c_h["30m_scenario_success"] += 1
                    if out_30["full_horizon_contained"]:
                        c_h["30m_full_contain_hits"] += 1
                    if out_30["invalidation_hit"]:
                        c_h["30m_invalid_hits"] += 1

            # Format scenario stats
            scenario_summary = {}
            for sc, data in by_scenario.items():
                scenario_summary[sc] = {
                    "forecast_count": data["count"],
                    "5m": {
                        "completed_evals": data["5m"]["evals"],
                        "direction_accuracy_pct": round((data["5m"]["dir_hits"] / data["5m"]["dir_evals"]) * 100.0, 1) if data["5m"]["dir_evals"] > 0 else "N/A (RANGE)",
                        "endpoint_containment_pct": round((data["5m"]["range_endpoint_hits"] / data["5m"]["evals"]) * 100.0, 1) if data["5m"]["evals"] > 0 else None,
                        "full_horizon_containment_pct": round((data["5m"]["full_contain_hits"] / data["5m"]["evals"]) * 100.0, 1) if data["5m"]["evals"] > 0 else None,
                        "temporary_breach_pct": round((data["5m"]["temp_breach_hits"] / data["5m"]["evals"]) * 100.0, 1) if data["5m"]["evals"] > 0 else None,
                        "scenario_success_pct": round((data["5m"]["scenario_success"] / data["5m"]["evals"]) * 100.0, 1) if data["5m"]["evals"] > 0 else None,
                        "avg_mfe_pts": round(sum(data["5m"]["mfes"]) / len(data["5m"]["mfes"]), 2) if data["5m"]["mfes"] else None,
                        "avg_mae_pts": round(sum(data["5m"]["maes"]) / len(data["5m"]["maes"]), 2) if data["5m"]["maes"] else None,
                    },
                    "15m": {
                        "completed_evals": data["15m"]["evals"],
                        "direction_accuracy_pct": round((data["15m"]["dir_hits"] / data["15m"]["dir_evals"]) * 100.0, 1) if data["15m"]["dir_evals"] > 0 else "N/A (RANGE)",
                        "endpoint_containment_pct": round((data["15m"]["range_endpoint_hits"] / data["15m"]["evals"]) * 100.0, 1) if data["15m"]["evals"] > 0 else None,
                        "full_horizon_containment_pct": round((data["15m"]["full_contain_hits"] / data["15m"]["evals"]) * 100.0, 1) if data["15m"]["evals"] > 0 else None,
                        "temporary_breach_pct": round((data["15m"]["temp_breach_hits"] / data["15m"]["evals"]) * 100.0, 1) if data["15m"]["evals"] > 0 else None,
                        "scenario_success_pct": round((data["15m"]["scenario_success"] / data["15m"]["evals"]) * 100.0, 1) if data["15m"]["evals"] > 0 else None,
                        "avg_mfe_pts": round(sum(data["15m"]["mfes"]) / len(data["15m"]["mfes"]), 2) if data["15m"]["mfes"] else None,
                        "avg_mae_pts": round(sum(data["15m"]["maes"]) / len(data["15m"]["maes"]), 2) if data["15m"]["maes"] else None,
                    },
                    "30m": {
                        "completed_evals": data["30m"]["evals"],
                        "direction_accuracy_pct": round((data["30m"]["dir_hits"] / data["30m"]["dir_evals"]) * 100.0, 1) if data["30m"]["dir_evals"] > 0 else "N/A (RANGE)",
                        "endpoint_containment_pct": round((data["30m"]["range_endpoint_hits"] / data["30m"]["evals"]) * 100.0, 1) if data["30m"]["evals"] > 0 else None,
                        "full_horizon_containment_pct": round((data["30m"]["full_contain_hits"] / data["30m"]["evals"]) * 100.0, 1) if data["30m"]["evals"] > 0 else None,
                        "temporary_breach_pct": round((data["30m"]["temp_breach_hits"] / data["30m"]["evals"]) * 100.0, 1) if data["30m"]["evals"] > 0 else None,
                        "confirmation_rate_pct": round((data["30m"]["confirm_hits"] / data["30m"]["evals"]) * 100.0, 1) if data["30m"]["evals"] > 0 else None,
                        "invalidation_rate_pct": round((data["30m"]["invalid_hits"] / data["30m"]["evals"]) * 100.0, 1) if data["30m"]["evals"] > 0 else None,
                        "scenario_success_pct": round((data["30m"]["scenario_success"] / data["30m"]["evals"]) * 100.0, 1) if data["30m"]["evals"] > 0 else None,
                        "avg_mfe_pts": round(sum(data["30m"]["mfes"]) / len(data["30m"]["mfes"]), 2) if data["30m"]["mfes"] else None,
                        "avg_mae_pts": round(sum(data["30m"]["maes"]) / len(data["30m"]["maes"]), 2) if data["30m"]["maes"] else None,
                    },
                }

            # Format confidence stats
            confidence_summary = {}
            for cf, data in by_confidence.items():
                ev = data["30m_evals"]
                dir_ev = data["30m_dir_evals"]
                confidence_summary[cf] = {
                    "forecast_count": data["count"],
                    "completed_30m_evals": ev,
                    "scenario_success_pct": round((data["30m_scenario_success"] / ev) * 100.0, 1) if ev > 0 else None,
                    "directional_success_pct": round((data["30m_dir_hits"] / dir_ev) * 100.0, 1) if dir_ev > 0 else "N/A (NO_DIRECTIONAL_EVALS)",
                    "full_range_containment_pct": round((data["30m_full_contain_hits"] / ev) * 100.0, 1) if ev > 0 else None,
                    "invalidation_rate_pct": round((data["30m_invalid_hits"] / ev) * 100.0, 1) if ev > 0 else None,
                }

            return {
                "total_observations": len(forecast_list),
                "scenario_summary": scenario_summary,
                "confidence_summary": confidence_summary,
            }

        return {
            "status": "EVALUATION_SUCCESS",
            "session_date": "2026-08-24",
            "all_observations": _calc_stats(evaluated_forecasts),
            "independent_windows": _calc_stats([f for f in evaluated_forecasts if f["is_independent"]]),
        }
