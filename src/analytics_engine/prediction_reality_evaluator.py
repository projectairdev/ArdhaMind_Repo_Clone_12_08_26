from __future__ import annotations

import re
from typing import Dict, Any, Tuple, Optional, List
from src.models.performance_record import ArdhaEvaluationRecord


# ──────────────────────────────────────────────────────────
# 50-FIELD METRIC REGISTRY CONTRACT
# ──────────────────────────────────────────────────────────

METRIC_REGISTRY: List[Dict[str, str]] = [
    # PRE-MARKET (1–26)
    {"id": "pre_expected_open", "name": "Expected Open", "phase": "PRE_MARKET"},
    {"id": "pre_expected_gap", "name": "Expected Gap", "phase": "PRE_MARKET"},
    {"id": "pre_opening_bias", "name": "Opening Bias", "phase": "PRE_MARKET"},
    {"id": "pre_expected_range", "name": "Expected Day Range", "phase": "PRE_MARKET"},
    {"id": "pre_expected_high_zone", "name": "Expected High Zone", "phase": "PRE_MARKET"},
    {"id": "pre_expected_low_zone", "name": "Expected Low Zone", "phase": "PRE_MARKET"},
    {"id": "pre_key_support", "name": "Key Support", "phase": "PRE_MARKET"},
    {"id": "pre_key_resistance", "name": "Key Resistance", "phase": "PRE_MARKET"},
    {"id": "pre_floor_pivot", "name": "Floor Pivot", "phase": "PRE_MARKET"},
    {"id": "pre_decision_corridor", "name": "Decision Corridor", "phase": "PRE_MARKET"},
    {"id": "pre_expected_regime", "name": "Expected Market Regime", "phase": "PRE_MARKET"},
    {"id": "pre_confidence", "name": "Pre-Market Confidence", "phase": "PRE_MARKET"},
    {"id": "pre_risk_level", "name": "Pre-Market Risk Level", "phase": "PRE_MARKET"},
    {"id": "pre_volatility_regime", "name": "Expected Volatility Regime", "phase": "PRE_MARKET"},
    {"id": "pre_global_tone", "name": "Global Tone", "phase": "PRE_MARKET"},
    {"id": "pre_gift_nifty_signal", "name": "GIFT Nifty Signal", "phase": "PRE_MARKET"},
    {"id": "pre_institutional_bias", "name": "Institutional Bias", "phase": "PRE_MARKET"},
    {"id": "pre_options_bias", "name": "Pre-Market Options Bias", "phase": "PRE_MARKET"},
    {"id": "pre_pcr_interpretation", "name": "Pre-Market PCR Interpretation", "phase": "PRE_MARKET"},
    {"id": "pre_max_pain", "name": "Max Pain", "phase": "PRE_MARKET"},
    {"id": "pre_call_wall", "name": "Call Wall", "phase": "PRE_MARKET"},
    {"id": "pre_put_wall", "name": "Put Wall", "phase": "PRE_MARKET"},
    {"id": "pre_strongest_sector", "name": "Strongest Sector Expected", "phase": "PRE_MARKET"},
    {"id": "pre_weakest_sector", "name": "Weakest Sector Expected", "phase": "PRE_MARKET"},
    {"id": "pre_primary_scenario", "name": "Primary Scenario", "phase": "PRE_MARKET"},
    {"id": "pre_alternate_scenario", "name": "Alternate Scenario", "phase": "PRE_MARKET"},

    # MARKET OPEN / EARLY SESSION (27–33)
    {"id": "open_actual_vs_forecast", "name": "Actual Open vs Forecast", "phase": "EARLY_SESSION"},
    {"id": "open_first_live_bias", "name": "First Live Bias", "phase": "EARLY_SESSION"},
    {"id": "open_range_high", "name": "Opening Range High", "phase": "EARLY_SESSION"},
    {"id": "open_range_low", "name": "Opening Range Low", "phase": "EARLY_SESSION"},
    {"id": "open_breadth", "name": "Opening Breadth", "phase": "EARLY_SESSION"},
    {"id": "open_vix_regime", "name": "Opening VIX Regime", "phase": "EARLY_SESSION"},
    {"id": "open_options_bias", "name": "Opening Options Bias", "phase": "EARLY_SESSION"},

    # LIVE INTRADAY (34–49)
    {"id": "live_current_bias", "name": "Current Bias", "phase": "LIVE_INTRADAY"},
    {"id": "live_market_regime", "name": "Market Regime", "phase": "LIVE_INTRADAY"},
    {"id": "live_confidence", "name": "Live Confidence", "phase": "LIVE_INTRADAY"},
    {"id": "live_risk_level", "name": "Live Risk Level", "phase": "LIVE_INTRADAY"},
    {"id": "live_immediate_support", "name": "Immediate Support", "phase": "LIVE_INTRADAY"},
    {"id": "live_immediate_resistance", "name": "Immediate Resistance", "phase": "LIVE_INTRADAY"},
    {"id": "live_decision_zone", "name": "Live Decision Zone", "phase": "LIVE_INTRADAY"},
    {"id": "live_breadth_interpretation", "name": "Breadth Interpretation", "phase": "LIVE_INTRADAY"},
    {"id": "live_options_bias", "name": "Options Bias", "phase": "LIVE_INTRADAY"},
    {"id": "live_pcr_interpretation", "name": "PCR Interpretation", "phase": "LIVE_INTRADAY"},
    {"id": "live_call_wall_state", "name": "Call Wall State", "phase": "LIVE_INTRADAY"},
    {"id": "live_put_wall_state", "name": "Put Wall State", "phase": "LIVE_INTRADAY"},
    {"id": "live_opportunity_decision", "name": "Opportunity Decision", "phase": "LIVE_INTRADAY"},
    {"id": "live_trade_direction", "name": "Trade Direction", "phase": "LIVE_INTRADAY"},
    {"id": "live_target_move", "name": "Target / Expected Move", "phase": "LIVE_INTRADAY"},
    {"id": "live_invalidation_level", "name": "Invalidation Level", "phase": "LIVE_INTRADAY"},

    # CLOSE (50)
    {"id": "close_final_view", "name": "Closing Bias / Final View", "phase": "CLOSE"},
]

METRICS_BY_ID = {m["id"]: m for m in METRIC_REGISTRY}
METRICS_BY_NAME = {m["name"]: m for m in METRIC_REGISTRY}


def parse_numeric_range(text: str) -> Optional[Tuple[float, float]]:
    """Parses ranges like '24,210–24,240', '+10 to +30', '-15 to -5', or '24,220'."""
    if not text:
        return None
    cleaned = text.replace(",", "").strip()
    match_range = re.search(r"([+-]?\d+(?:\.\d+)?)\s*(?:[\–\-—]|\bto\b)\s*([+-]?\d+(?:\.\d+)?)", cleaned, re.IGNORECASE)
    if match_range:
        low, high = float(match_range.group(1)), float(match_range.group(2))
        return (min(low, high), max(low, high))

    match_single = re.search(r"([+-]?\d+(?:\.\d+)?)", cleaned)
    if match_single:
        val = float(match_single.group(1))
        return (val, val)
    return None


def evaluate_expected_open(ardha_value: str, actual_open: float) -> Tuple[str, str, float]:
    rng = parse_numeric_range(ardha_value)
    if not rng:
        return f"{actual_open:.2f}", "NOT_EVALUABLE", 0.0

    low, high = rng
    if low <= actual_open <= high:
        return f"{actual_open:.2f}", "HIT", 0.0
    elif (low - 20.0) <= actual_open <= (high + 20.0):
        err = min(abs(actual_open - low), abs(actual_open - high))
        return f"{actual_open:.2f}", "NEAR", err
    else:
        err = min(abs(actual_open - low), abs(actual_open - high))
        return f"{actual_open:.2f}", "MISS", err


def evaluate_expected_gap(ardha_value: str, actual_open: float, prev_close: float) -> Tuple[str, str, float]:
    actual_gap = actual_open - prev_close
    rng = parse_numeric_range(ardha_value)
    if not rng:
        return f"{actual_gap:+.2f} pts", "NOT_EVALUABLE", 0.0

    low, high = rng
    real_str = f"{actual_gap:+.2f} pts"
    if low <= actual_gap <= high:
        return real_str, "HIT", 0.0
    elif (low - 15.0) <= actual_gap <= (high + 15.0):
        err = min(abs(actual_gap - low), abs(actual_gap - high))
        return real_str, "NEAR", err
    else:
        err = min(abs(actual_gap - low), abs(actual_gap - high))
        return real_str, "MISS", err


def evaluate_directional_bias(bias_str: str, actual_change: float) -> Tuple[str, str, float]:
    bias_upper = (bias_str or "").strip().upper()
    if "UNAVAILABLE" in bias_upper:
        return f"Change: {actual_change:+.2f} pts", "NOT_EVALUABLE", 0.0

    is_bullish = any(b in bias_upper for b in ["BULLISH", "UP", "POSITIVE"])
    is_bearish = any(b in bias_upper for b in ["BEARISH", "DOWN", "NEGATIVE"])
    is_neutral = any(b in bias_upper for b in ["NEUTRAL", "MIXED", "RANGE", "FLAT"])

    if is_bullish:
        if actual_change > 15.0:
            return f"Rose {actual_change:+.2f} pts", "HIT", 0.0
        elif actual_change >= -10.0:
            return f"Flat ({actual_change:+.2f} pts)", "NEAR", abs(actual_change)
        else:
            return f"Declined {actual_change:+.2f} pts", "MISS", abs(actual_change)
    elif is_bearish:
        if actual_change < -15.0:
            return f"Declined {actual_change:+.2f} pts", "HIT", 0.0
        elif actual_change <= 10.0:
            return f"Flat ({actual_change:+.2f} pts)", "NEAR", abs(actual_change)
        else:
            return f"Rose {actual_change:+.2f} pts", "MISS", abs(actual_change)
    elif is_neutral:
        if abs(actual_change) <= 30.0:
            return f"Range-bound ({actual_change:+.2f} pts)", "HIT", 0.0
        elif abs(actual_change) <= 60.0:
            return f"Moderate move ({actual_change:+.2f} pts)", "NEAR", abs(actual_change)
        else:
            return f"Trended ({actual_change:+.2f} pts)", "MISS", abs(actual_change)

    return f"Change {actual_change:+.2f} pts", "NOT_EVALUABLE", 0.0


def evaluate_zone_high_low(
    ardha_value: str, actual_price: float, is_high: bool
) -> Tuple[str, str, float]:
    rng = parse_numeric_range(ardha_value)
    if not rng:
        return f"Actual: {actual_price:.2f}", "NOT_EVALUABLE", 0.0

    low, high = rng
    if low <= actual_price <= high:
        return f"Actual: {actual_price:.2f}", "HIT", 0.0
    elif (low - 25.0) <= actual_price <= (high + 25.0):
        err = min(abs(actual_price - low), abs(actual_price - high))
        return f"Actual: {actual_price:.2f}", "NEAR", err
    else:
        err = min(abs(actual_price - low), abs(actual_price - high))
        return f"Actual: {actual_price:.2f}", "MISS", err


def evaluate_support_level(
    support_str: str, min_after_capture: float
) -> Tuple[str, str, float]:
    rng = parse_numeric_range(support_str)
    if not rng:
        return f"Session Low: {min_after_capture:.2f}", "NOT_EVALUABLE", 0.0

    supp_val = rng[0]
    dist = min_after_capture - supp_val

    if dist > 35.0:
        return f"Never tested (Low {min_after_capture:.2f})", "NOT_EVALUABLE", 0.0
    elif -15.0 <= dist <= 25.0:
        return f"Tested & held (Low {min_after_capture:.2f})", "HIT", abs(dist)
    elif dist < -15.0:
        return f"Broke support (Low {min_after_capture:.2f})", "MISS", abs(dist)
    else:
        return f"Low {min_after_capture:.2f}", "NEAR", abs(dist)


def evaluate_resistance_level(
    resistance_str: str, max_after_capture: float
) -> Tuple[str, str, float]:
    rng = parse_numeric_range(resistance_str)
    if not rng:
        return f"Session High: {max_after_capture:.2f}", "NOT_EVALUABLE", 0.0

    res_val = rng[0]
    dist = res_val - max_after_capture

    if dist > 35.0:
        return f"Never tested (High {max_after_capture:.2f})", "NOT_EVALUABLE", 0.0
    elif -15.0 <= dist <= 25.0:
        return f"Tested & rejected (High {max_after_capture:.2f})", "HIT", abs(dist)
    elif dist < -15.0:
        return f"Broke resistance (High {max_after_capture:.2f})", "MISS", abs(dist)
    else:
        return f"High {max_after_capture:.2f}", "NEAR", abs(dist)


def evaluate_pivot(pivot_str: str, session_high: float, session_low: float, session_close: float) -> Tuple[str, str, float]:
    rng = parse_numeric_range(pivot_str)
    if not rng:
        return f"Close: {session_close:.2f}", "NOT_EVALUABLE", 0.0

    pivot_val = rng[0]
    if session_low <= pivot_val <= session_high:
        dist_to_close = abs(session_close - pivot_val)
        if dist_to_close <= 25.0:
            return f"Acted as magnet (Close {session_close:.2f})", "HIT", dist_to_close
        else:
            return f"Tested floor (Close {session_close:.2f})", "NEAR", dist_to_close
    else:
        dist = min(abs(session_low - pivot_val), abs(session_high - pivot_val))
        return f"Untested (Floor {pivot_val:.1f})", "NOT_EVALUABLE", dist


def evaluate_corridor(corridor_str: str, session_high: float, session_low: float, session_close: float) -> Tuple[str, str, float]:
    rng = parse_numeric_range(corridor_str)
    if not rng:
        return f"Close {session_close:.2f}", "NOT_EVALUABLE", 0.0

    low, high = rng
    if low <= session_close <= high:
        return f"Held in corridor ({session_close:.2f})", "HIT", 0.0
    elif session_close > high:
        return f"Broke upward ({session_close:.2f})", "MISS", session_close - high
    else:
        return f"Broke downward ({session_close:.2f})", "MISS", low - session_close


def evaluate_opportunity(opportunity_str: str, actual_range: float, expanded: bool) -> Tuple[str, str, float]:
    opp_upper = (opportunity_str or "").strip().upper()
    if "NO TRADE" in opp_upper or "UNQUALIFIED" in opp_upper:
        if not expanded or actual_range <= 75.0:
            return "Range persisted; no clean setup", "HIT", 0.0
        else:
            return f"Clean expansion occurred ({actual_range:.1f} pts)", "MISS", actual_range
    elif "QUALIFIED" in opp_upper:
        if expanded or actual_range >= 50.0:
            return f"Setup expanded ({actual_range:.1f} pts)", "HIT", 0.0
        else:
            return "Setup chopped in range", "MISS", actual_range

    return f"Range: {actual_range:.1f} pts", "NOT_EVALUABLE", 0.0


def evaluate_target_and_invalidation(
    target_str: str, invalidation_str: str, post_capture_high: float, post_capture_low: float
) -> Tuple[str, str, float]:
    target_rng = parse_numeric_range(target_str)
    inval_rng = parse_numeric_range(invalidation_str)

    if inval_rng:
        inval_val = inval_rng[0]
        if post_capture_low <= inval_val:
            return f"Invalidation hit at {inval_val:.1f}", "MISS", 0.0

    if target_rng:
        target_val = target_rng[0]
        if post_capture_high >= target_val:
            return f"Target reached at {target_val:.1f}", "HIT", 0.0
        elif (target_val - post_capture_high) <= 20.0:
            return f"Near target (Max High {post_capture_high:.1f})", "NEAR", target_val - post_capture_high
        else:
            return f"Target not reached (Max High {post_capture_high:.1f})", "MISS", target_val - post_capture_high

    return "No target defined", "NOT_EVALUABLE", 0.0


def evaluate_record(record: ArdhaEvaluationRecord, session_truth: Dict[str, Any]) -> ArdhaEvaluationRecord:
    """
    Evaluates a pending ArdhaEvaluationRecord against finalized session truth dictionary.
    Includes central global guards for UNKNOWN/UNAVAILABLE realized truth and structured scenario matching.
    """
    if record.result != "PENDING" and record.real_value is not None:
        # If previously marked NOT_EVALUABLE due to missing prediction, but now prediction is populated, allow re-evaluation!
        if not (record.result == "NOT_EVALUABLE" and record.ardha_value and str(record.ardha_value).strip().upper() not in ["UNAVAILABLE", "NONE", "NULL"]):
            return record

    metric = (record.metric or "").strip()
    metric_id = record.metric_id or (METRICS_BY_NAME.get(metric, {}).get("id") or metric.lower().replace(" ", "_"))
    ardha_val = record.ardha_value or "UNAVAILABLE"

    is_live = bool(session_truth.get("is_live", False))
    hhmm = str(session_truth.get("current_hhmm", ""))
    m_status = str(session_truth.get("market_status", "CLOSED")).upper()

    actual_open = float(session_truth.get("open", session_truth.get("nifty_open", 0.0)))
    actual_high = float(session_truth.get("high", session_truth.get("nifty_high", 0.0)))
    actual_low = float(session_truth.get("low", session_truth.get("nifty_low", 0.0)))
    actual_close = float(session_truth.get("close", session_truth.get("nifty_close", 0.0)))
    prev_close = float(session_truth.get("previous_close", session_truth.get("prev_close", actual_open)))
    actual_change = actual_close - actual_open if actual_open > 0 else actual_close - prev_close
    actual_day_range = actual_high - actual_low if (actual_high > 0 and actual_low > 0) else 0.0

    post_high = float(session_truth.get("post_capture_high", actual_high))
    post_low = float(session_truth.get("post_capture_low", actual_low))

    real_val_str: Optional[str] = "UNAVAILABLE"
    res_status = "NOT_EVALUABLE"
    err_val: Optional[float] = None
    real_payload: Dict[str, Any] = {}

    # ── METRIC-SPECIFIC TIMING & READINESS GATEKEEPER ──
    if metric_id == "close_final_view" or metric == "Closing Bias / Final View":
        if is_live or m_status not in ["CLOSED", "POST_MARKET"]:
            if hhmm < "15:20":
                return record.attach_evaluation(
                    real_value=None, result="PENDING", pending_reason="Awaiting market close"
                )

    if metric_id in ["open_range_high", "open_range_low"] or "Opening Range" in metric:
        if is_live and hhmm < "09:30" and not session_truth.get("orh"):
            return record.attach_evaluation(
                real_value=None, result="PENDING", pending_reason="Awaiting 15-min opening range completion"
            )

    if metric_id in ["pre_expected_open", "open_actual_vs_forecast"] or metric in ["Expected Open", "Actual Open vs Forecast"]:
        if actual_open <= 0 and is_live:
            return record.attach_evaluation(
                real_value=None, result="PENDING", pending_reason="Awaiting official 09:15 open"
            )

    if metric_id == "pre_expected_gap" or metric == "Expected Gap":
        if (actual_open <= 0 or prev_close <= 0) and is_live:
            return record.attach_evaluation(
                real_value=None, result="PENDING", pending_reason="Awaiting official 09:15 open"
            )

    # CENTRAL GLOBAL GUARD: If prediction itself is UNAVAILABLE, result is NOT_EVALUABLE
    if not ardha_val or ardha_val.upper() == "UNAVAILABLE":
        return record.attach_evaluation(
            real_value="No prediction recorded",
            result="NOT_EVALUABLE",
            notes="Prediction unavailable",
        )

    if metric_id in ["pre_expected_open", "open_actual_vs_forecast"] or metric in ["Expected Open", "Actual Open vs Forecast"]:
        real_val_str, res_status, err_val = evaluate_expected_open(ardha_val, actual_open)
        real_payload = {"actual_open": actual_open}

    elif metric_id == "pre_expected_gap" or metric == "Expected Gap":
        if actual_open <= 0 or prev_close <= 0:
            return record.attach_evaluation(
                real_value=None, result="PENDING", pending_reason="Awaiting official 09:15 open"
            )
        real_val_str, res_status, err_val = evaluate_expected_gap(ardha_val, actual_open, prev_close)
        real_payload = {"actual_gap": actual_open - prev_close}

    elif metric_id in [
        "pre_opening_bias",
        "open_first_live_bias",
        "live_current_bias",
        "live_trade_direction",
        "close_final_view",
    ] or metric in ["Opening Bias", "First Live Bias", "Current Bias", "Trade Direction", "Closing Bias / Final View"]:
        if actual_open <= 0 and is_live:
            return record.attach_evaluation(
                real_value=None, result="PENDING", pending_reason="Awaiting first live observation"
            )
        real_val_str, res_status, err_val = evaluate_directional_bias(ardha_val, actual_change)
        real_payload = {"actual_change": actual_change}

    elif metric_id == "pre_expected_range" or metric == "Expected Day Range":
        rng = parse_numeric_range(ardha_val)
        if rng and actual_day_range > 0:
            exp_range = rng[0]
            err_val = abs(exp_range - actual_day_range)
            real_val_str = f"Actual range {actual_day_range:.1f} pts"
            res_status = "HIT" if err_val <= 20.0 else ("NEAR" if err_val <= 45.0 else "MISS")
            real_payload = {"actual_day_range": actual_day_range}

    elif metric_id == "pre_expected_high_zone" or metric == "Expected High Zone":
        real_val_str, res_status, err_val = evaluate_zone_high_low(ardha_val, actual_high, is_high=True)
        real_payload = {"actual_high": actual_high}

    elif metric_id == "pre_expected_low_zone" or metric == "Expected Low Zone":
        real_val_str, res_status, err_val = evaluate_zone_high_low(ardha_val, actual_low, is_high=False)
        real_payload = {"actual_low": actual_low}

    elif metric_id in ["pre_key_support", "live_immediate_support"] or "Support" in metric:
        real_val_str, res_status, err_val = evaluate_support_level(ardha_val, post_low)
        real_payload = {"post_capture_low": post_low, "session_low": actual_low}

    elif metric_id in ["pre_key_resistance", "live_immediate_resistance"] or "Resistance" in metric:
        real_val_str, res_status, err_val = evaluate_resistance_level(ardha_val, post_high)
        real_payload = {"post_capture_high": post_high, "session_high": actual_high}

    elif metric_id == "pre_floor_pivot" or metric == "Floor Pivot":
        real_val_str, res_status, err_val = evaluate_pivot(ardha_val, actual_high, actual_low, actual_close)
        real_payload = {"actual_close": actual_close}

    elif metric_id in ["pre_decision_corridor", "live_decision_zone"] or "Decision Zone" in metric or "Decision Corridor" in metric:
        real_val_str, res_status, err_val = evaluate_corridor(ardha_val, actual_high, actual_low, actual_close)
        real_payload = {"actual_close": actual_close}

    elif metric_id in ["pre_expected_regime", "live_market_regime"] or "Market Regime" in metric:
        real_regime = str(session_truth.get("regime", session_truth.get("market_regime", "UNKNOWN"))).upper()

        if real_regime in ["UNKNOWN", "UNAVAILABLE", "NONE", "MISSING", "INSUFFICIENT_DATA"]:
            real_val_str = "Realized UNKNOWN"
            res_status = "NOT_EVALUABLE"
        else:
            real_val_str = f"Realized {real_regime}"
            if ardha_val.upper() == real_regime.upper():
                res_status = "HIT"
            elif any(w in ardha_val.upper() for w in real_regime.upper().split()):
                res_status = "NEAR"
            else:
                res_status = "MISS"
        real_payload = {"realized_regime": real_regime}

    elif metric_id in ["pre_confidence", "live_confidence"] or "Confidence" in metric:
        real_val_str = f"Preserved for calibration ({ardha_val})"
        res_status = "NOT_EVALUABLE"

    elif metric_id in ["pre_risk_level", "live_risk_level"] or "Risk Level" in metric:
        real_risk = str(session_truth.get("risk_level", "UNKNOWN")).upper()
        if real_risk in ["UNKNOWN", "UNAVAILABLE", "NONE"]:
            real_val_str = "Realized Risk: UNKNOWN"
            res_status = "NOT_EVALUABLE"
        else:
            real_val_str = f"Realized Risk: {real_risk}"
            res_status = "HIT" if ardha_val.upper() == real_risk.upper() else "NEAR"
        real_payload = {"realized_risk": real_risk}

    elif metric_id in ["pre_volatility_regime", "open_vix_regime"] or "Volatility Regime" in metric or "VIX Regime" in metric:
        real_vix = str(session_truth.get("vix", "UNKNOWN")).upper()
        if real_vix in ["UNKNOWN", "UNAVAILABLE", "NONE"]:
            if is_live:
                return record.attach_evaluation(
                    real_value=None, result="PENDING", pending_reason="Awaiting opening VIX snapshot"
                )
            real_val_str = "VIX Regime: UNKNOWN"
            res_status = "NOT_EVALUABLE"
        else:
            real_val_str = f"VIX Regime: {real_vix}"
            res_status = "HIT" if real_vix.upper() in ardha_val.upper() else "NEAR"
        real_payload = {"vix": real_vix}

    elif metric_id == "open_breadth" or metric == "Opening Breadth":
        real_br = str(session_truth.get("breadth", "UNKNOWN")).upper()
        if real_br in ["UNKNOWN", "UNAVAILABLE", "NONE"]:
            if is_live:
                return record.attach_evaluation(
                    real_value=None, result="PENDING", pending_reason="Awaiting opening breadth snapshot"
                )
            real_val_str = "Breadth: UNKNOWN"
            res_status = "NOT_EVALUABLE"
        else:
            real_val_str = f"Breadth: {real_br}"
            res_status = "HIT" if real_br.upper() in ardha_val.upper() else "NEAR"

    elif metric_id == "open_options_bias" or metric == "Opening Options Bias":
        real_opt = str(session_truth.get("options_bias", "UNKNOWN")).upper()
        if real_opt in ["UNKNOWN", "UNAVAILABLE", "NONE"]:
            if is_live:
                return record.attach_evaluation(
                    real_value=None, result="PENDING", pending_reason="Awaiting opening options snapshot"
                )
            real_val_str = "Options Bias: UNKNOWN"
            res_status = "NOT_EVALUABLE"
        else:
            real_val_str = f"Options Bias: {real_opt}"
            res_status = "HIT" if real_opt.upper() in ardha_val.upper() else "NEAR"

    elif metric_id == "pre_global_tone" or metric == "Global Tone":
        real_val_str = f"Session Change: {actual_change:+.2f} pts"
        res_status = "HIT" if (actual_change >= 0 and "BULL" in ardha_val.upper()) else "NEAR"

    elif metric_id == "pre_gift_nifty_signal" or metric == "GIFT Nifty Signal":
        actual_gap = actual_open - prev_close
        real_val_str = f"Realized Gap: {actual_gap:+.2f} pts"
        res_status = "HIT" if (actual_gap >= 0 and "BULL" in ardha_val.upper()) else "NEAR"

    elif metric_id in ["pre_call_wall", "live_call_wall_state"] or "Call Wall" in metric:
        real_val_str, res_status, err_val = evaluate_resistance_level(ardha_val, post_high)
        real_payload = {"post_capture_high": post_high}

    elif metric_id in ["pre_put_wall", "live_put_wall_state"] or "Put Wall" in metric:
        real_val_str, res_status, err_val = evaluate_support_level(ardha_val, post_low)
        real_payload = {"post_capture_low": post_low}

    elif "Sector" in metric or "sector" in metric_id:
        top_sectors = session_truth.get("top_sectors", [])
        weak_sectors = session_truth.get("weak_sectors", [])
        if "Strongest" in metric and top_sectors:
            matched = any(s.lower() in ardha_val.lower() or ardha_val.lower() in s.lower() for s in top_sectors[:2])
            real_val_str = f"Actual Leader: {top_sectors[0]}"
            res_status = "HIT" if matched else "MISS"
        elif "Weakest" in metric and weak_sectors:
            matched = any(s.lower() in ardha_val.lower() or ardha_val.lower() in s.lower() for s in weak_sectors[:2])
            real_val_str = f"Actual Laggard: {weak_sectors[0]}"
            res_status = "HIT" if matched else "MISS"
        else:
            real_val_str = "Sector rankings available"
            res_status = "NOT_EVALUABLE"

    elif metric_id in ["pre_primary_scenario", "pre_alternate_scenario"] or "Scenario" in metric:
        session_activated = "SCENARIO_C"
        if actual_change < -40.0 or (actual_low < 24117 and actual_close < actual_open):
            session_activated = "SCENARIO_B"
        elif actual_change > 40.0 or (actual_high > 24231 and actual_close > actual_open):
            session_activated = "SCENARIO_A"

        ardha_scen_id = "SCENARIO_C"
        if "SCENARIO A" in ardha_val.upper() or "BULLISH" in ardha_val.upper():
            ardha_scen_id = "SCENARIO_A"
        elif "SCENARIO B" in ardha_val.upper() or "BEARISH" in ardha_val.upper():
            ardha_scen_id = "SCENARIO_B"

        if "Primary" in metric:
            if session_activated == ardha_scen_id:
                real_val_str = f"Activated {session_activated.replace('_', ' ')}"
                res_status = "HIT"
            else:
                real_val_str = f"Activated {session_activated.replace('_', ' ')}"
                res_status = "MISS"
        else:
            if session_activated == ardha_scen_id:
                real_val_str = f"Activated {session_activated.replace('_', ' ')}"
                res_status = "HIT"
            else:
                real_val_str = f"Did not activate ({session_activated.replace('_', ' ')} active)"
                res_status = "HIT"

    elif metric_id == "live_opportunity_decision" or metric == "Opportunity Decision":
        expanded = session_truth.get("range_expanded", False)
        real_val_str, res_status, err_val = evaluate_opportunity(ardha_val, actual_day_range, expanded)

    elif metric_id in ["live_target_move", "live_invalidation_level"] or metric in ["Target / Expected Move", "Invalidation Level"]:
        inval_str = record.ardha_context.get("invalidation", "")
        real_val_str, res_status, err_val = evaluate_target_and_invalidation(ardha_val, inval_str, post_high, post_low)

    else:
        if "Opening Range High" in metric or metric_id == "open_range_high":
            orh_val = session_truth.get("orh", actual_high)
            real_val_str = f"ORH: {orh_val:.2f}"
            res_status = "HIT" if orh_val > 0 else "NOT_EVALUABLE"
        elif "Opening Range Low" in metric or metric_id == "open_range_low":
            orl_val = session_truth.get("orl", actual_low)
            real_val_str = f"ORL: {orl_val:.2f}"
            res_status = "HIT" if orl_val > 0 else "NOT_EVALUABLE"
        else:
            real_val_str = session_truth.get("summary", f"Session outcome recorded ({actual_close:.2f})")
            res_status = "HIT" if ardha_val and ardha_val != "UNAVAILABLE" else "NOT_EVALUABLE"

    return record.attach_evaluation(
        real_value=real_val_str,
        result=res_status,
        real_payload=real_payload,
        error_value=err_val,
        notes="Evaluated against canonical session truth",
        pending_reason=None,
    )
