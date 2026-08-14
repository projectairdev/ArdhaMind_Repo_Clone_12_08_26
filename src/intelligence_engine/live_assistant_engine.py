# src/intelligence_engine/live_assistant_engine.py
"""
LiveAssistantEngine — Intraday Market Intelligence Narrator for AIR ArdhaMind.

Transforms Live Assistant into the trader's real-time intraday companion.
Supports two complementary mechanisms:
  A. Scheduled 15-Minute Market Intelligence Windows (Session-anchored IST boundaries)
  B. Event-Driven Significant Change Detection (Stateful state-transition alerts)

Principles & Rules:
  1. Purely deterministic computation from canonical state & session history.
  2. No LLM dependency (OpenAI is optional for concise formatting only).
  3. Strictly NO BUY/SELL/order execution commands or price predictions.
  4. Stateful event deduplication (no tick-alert spam).
  5. Telemetry gaps within windows mark INSUFFICIENT_WINDOW_EVIDENCE / PARTIAL_EVIDENCE and prevent false Quiet classifications.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set


@dataclass
class MarketWindowAnalysis:
    window_start: str
    window_end: str
    generated_at: str
    analysis_status: str  # SUFFICIENT_EVIDENCE | PARTIAL_EVIDENCE | INSUFFICIENT_WINDOW_EVIDENCE | BUILDING | MARKET_NOT_STARTED | SESSION_COMPLETE

    start_spot: Optional[float]
    end_spot: Optional[float]
    price_change_points: Optional[float]
    price_change_percent: Optional[float]
    window_high: Optional[float]
    window_low: Optional[float]
    window_range: Optional[float]
    window_open: Optional[float]
    window_close: Optional[float]
    close_location_in_range: float
    movement_relative_to_prev: float

    breadth_start: str
    breadth_end: str
    breadth_change: str
    breadth_delta: Optional[int]
    breadth_trend: str  # STRENGTHENING | WEAKENING | STABLE
    breadth_divergence: str  # CONFIRMING_BULLISH | CONFIRMING_BEARISH | BULLISH_DIVERGENCE | BEARISH_DIVERGENCE | NEUTRAL

    vix_start: Optional[float]
    vix_end: Optional[float]
    vix_change: Optional[float]
    vix_trend: str  # EXPANDING | CONTRACTING | STABLE

    pcr_start: Optional[float]
    pcr_end: Optional[float]
    pcr_change: Optional[float]
    options_available: bool
    options_narrative: str

    significance_classification: str  # INSUFFICIENT_EVIDENCE | QUIET | NORMAL | NOTABLE | SIGNIFICANT | MAJOR
    headline: str
    what_happened: List[str]
    why_it_matters: List[str]
    watch_next: List[str]

    contains_telemetry_gap: bool
    data_quality: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SignificantEvent:
    event_id: str
    event_type: str  # LEVEL_BREAK | LEVEL_RECLAIM | MOMENTUM_ACCELERATION | MOMENTUM_REVERSAL | BREADTH_SURGE | BREADTH_COLLAPSE | PRICE_BREADTH_DIVERGENCE | VOLATILITY_EXPANSION | VOLATILITY_COMPRESSION | OPTIONS_POSITIONING_SHIFT
    timestamp: str
    significance: str  # NOTABLE | SIGNIFICANT | MAJOR
    headline: str
    what_happened: str
    why_it_matters: str
    watch_next: str
    source_window: str
    evidence_data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LiveAssistantEngine:
    """
    Intraday Market Intelligence Narrator Engine.
    """

    _completed_windows_cache: Dict[str, MarketWindowAnalysis] = {}
    _emitted_event_states: Set[str] = set()

    @classmethod
    def reset_engine_state(cls) -> None:
        """Reset internal caches for testing or session rollover."""
        cls._completed_windows_cache.clear()
        cls._emitted_event_states.clear()

    @classmethod
    def analyze_live_session(
        cls,
        state: Dict[str, Any],
        snapshot_history: Optional[List[Dict[str, Any]]] = None,
        today_analysis_report: Optional[Dict[str, Any]] = None,
        as_of_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        now_utc = as_of_time or datetime.now(timezone.utc)
        now_ist = now_utc + timedelta(hours=5, minutes=30)
        now_str = now_utc.isoformat().replace("+00:00", "Z")

        m_session = state.get("market_session") or {}
        sess_status = str(m_session.get("status") or "OPEN").upper()
        is_closed = bool(m_session.get("is_closed") or sess_status in ("CLOSED", "HOLIDAY", "POST_CLOSE"))
        session_date = str(m_session.get("session_date") or now_ist.strftime("%Y-%m-%d"))

        # Pre-market state
        if sess_status in ("PRE_OPEN", "PRE_MARKET", "NOT_STARTED"):
            return {
                "generated_at": now_str,
                "session_status": "MARKET_NOT_STARTED",
                "windows": [],
                "significant_events": [],
                "active_monitoring": False
            }

        # 1. Evaluate Session-Anchored 15-Minute Windows
        windows = cls._evaluate_15m_windows(now_ist, session_date, snapshot_history or [], is_closed)

        # 2. Detect Event-Driven Significant Changes
        events = cls._detect_significant_events(state, snapshot_history or [], today_analysis_report, windows)

        return {
            "generated_at": now_str,
            "session_date": session_date,
            "session_status": "SESSION_COMPLETE" if is_closed else "LIVE_MONITORING",
            "windows": [w.to_dict() for w in windows],
            "significant_events": [e.to_dict() for e in events],
            "active_monitoring": not is_closed
        }

    @classmethod
    def _evaluate_15m_windows(
        cls,
        now_ist: datetime,
        session_date: str,
        history: List[Dict[str, Any]],
        is_closed: bool
    ) -> List[MarketWindowAnalysis]:
        windows: List[MarketWindowAnalysis] = []

        boundary_times = [
            ("09:15", "09:30"), ("09:30", "09:45"), ("09:45", "10:00"),
            ("10:00", "10:15"), ("10:15", "10:30"), ("10:30", "10:45"), ("10:45", "11:00"),
            ("11:00", "11:15"), ("11:15", "11:30"), ("11:30", "11:45"), ("11:45", "12:00"),
            ("12:00", "12:15"), ("12:15", "12:30"), ("12:30", "12:45"), ("12:45", "13:00"),
            ("13:00", "13:15"), ("13:15", "13:30"), ("13:30", "13:45"), ("13:45", "14:00"),
            ("14:00", "14:15"), ("14:15", "14:30"), ("14:30", "14:45"), ("14:45", "15:00"),
            ("15:00", "15:15"), ("15:15", "15:30")
        ]

        curr_hm = now_ist.strftime("%H:%M")
        eval_date = now_ist.strftime("%Y-%m-%d")
        prev_window_end_spot: Optional[float] = None
        prev_window_change: Optional[float] = None

        for w_start, w_end in boundary_times:
            win_key = f"{session_date}_{w_start}_{w_end}"

            # Filter snapshots in history belonging to this window
            win_snaps = [
                s for s in history
                if cls._snap_in_window(s, w_start, w_end)
            ]

            has_later_snaps = any(cls._snap_is_after(s, w_end) for s in history)
            is_window_past = is_closed or has_later_snaps or (eval_date > session_date) or (eval_date == session_date and curr_hm >= w_end)

            if not is_window_past and not win_snaps and (eval_date == session_date and curr_hm < w_start):
                # Future window today -> skip
                continue

            analysis = cls._build_window_analysis(
                w_start, w_end, win_snaps, is_window_past, is_closed, session_date, prev_window_end_spot, prev_window_change
            )

            if analysis.end_spot is not None:
                prev_window_end_spot = analysis.end_spot
                prev_window_change = analysis.price_change_points

            if is_window_past and analysis.analysis_status != "BUILDING":
                cls._completed_windows_cache[win_key] = analysis

            windows.append(analysis)

        return windows

    @classmethod
    def _parse_ist_hm(cls, ts: Any) -> Optional[str]:
        if not ts:
            return None
        try:
            ts_str = str(ts)
            if "+05:30" in ts_str or "+0530" in ts_str:
                dt = datetime.fromisoformat(ts_str.replace("Z", ""))
                return dt.strftime("%H:%M")
            elif "Z" in ts_str:
                dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                ist_dt = dt.astimezone(timezone(timedelta(hours=5, minutes=30)))
                return ist_dt.strftime("%H:%M")
            else:
                dt = datetime.fromisoformat(ts_str.split("+")[0])
                ist_dt = dt + timedelta(hours=5, minutes=30)
                return ist_dt.strftime("%H:%M")
        except Exception:
            return None

    @classmethod
    def _snap_in_window(cls, snap: Dict[str, Any], w_start: str, w_end: str) -> bool:
        ts = snap.get("timestamp") or snap.get("generated_at")
        hm = cls._parse_ist_hm(ts)
        if not hm:
            return False
        return w_start <= hm < w_end

    @classmethod
    def _snap_is_after(cls, snap: Dict[str, Any], w_end: str) -> bool:
        ts = snap.get("timestamp") or snap.get("generated_at")
        hm = cls._parse_ist_hm(ts)
        if not hm:
            return False
        return hm >= w_end

    @classmethod
    def _parse_ts_dt(cls, ts: Any) -> Optional[datetime]:
        if not ts:
            return None
        try:
            return datetime.fromisoformat(str(ts).replace("Z", "").split("+")[0])
        except Exception:
            return None

    @classmethod
    def _build_window_analysis(
        cls,
        w_start: str,
        w_end: str,
        snaps: List[Dict[str, Any]],
        is_completed: bool,
        is_session_closed: bool,
        session_date: str,
        prev_end_spot: Optional[float] = None,
        prev_change_pts: Optional[float] = None
    ) -> MarketWindowAnalysis:
        now_str = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        obs_count = len(snaps)
        has_gap_flag = any(s.get("is_telemetry_gap") for s in snaps)
        spots = [s.get("spot") for s in snaps if isinstance(s.get("spot"), (int, float))]
        price_obs_count = len(spots)

        b_snaps = [s.get("breadth") for s in snaps if isinstance(s.get("breadth"), dict)]
        breadth_obs_count = len(b_snaps)

        vix_snaps = [s.get("vix") for s in snaps if s.get("vix") is not None]
        vix_obs_count = len(vix_snaps)

        opt_snaps = [s.get("options") or s.get("option_intelligence") for s in snaps if (s.get("options") or s.get("option_intelligence"))]
        options_obs_count = len(opt_snaps)

        first_ts = snaps[0].get("timestamp") or snaps[0].get("generated_at") if snaps else None
        last_ts = snaps[-1].get("timestamp") or snaps[-1].get("generated_at") if snaps else None

        first_dt = cls._parse_ts_dt(first_ts)
        last_dt = cls._parse_ts_dt(last_ts)

        span_seconds = 0.0
        if first_dt and last_dt:
            span_seconds = max(0.0, (last_dt - first_dt).total_seconds())

        is_sufficient = (obs_count >= 2 and span_seconds >= 60.0) or (price_obs_count >= 2)

        if not is_completed:
            analysis_status = "BUILDING"
            evidence_quality = "BUILDING"
        elif is_sufficient:
            analysis_status = "SUFFICIENT_EVIDENCE"
            evidence_quality = "SUFFICIENT"
        elif has_gap_flag:
            analysis_status = "PARTIAL_EVIDENCE"
            evidence_quality = "PARTIAL"
        else:
            analysis_status = "INSUFFICIENT_WINDOW_EVIDENCE"
            evidence_quality = "INSUFFICIENT"

        data_quality = {
            "status": analysis_status,
            "evidence_quality": evidence_quality,
            "observation_count": obs_count,
            "first_observation_time": first_ts or "Unavailable",
            "last_observation_time": last_ts or "Unavailable",
            "observed_span_seconds": round(span_seconds, 1),
            "price_observation_count": price_obs_count,
            "breadth_observation_count": breadth_obs_count,
            "vix_observation_count": vix_obs_count,
            "options_observation_count": options_obs_count
        }

        # Insufficient Telemetry Fallback (Do NOT classify as QUIET!)
        if not is_sufficient and is_completed:
            return MarketWindowAnalysis(
                window_start=w_start, window_end=w_end, generated_at=now_str,
                analysis_status=analysis_status,
                start_spot=prev_end_spot, end_spot=spots[-1] if spots else prev_end_spot,
                price_change_points=None, price_change_percent=None,
                window_high=spots[0] if spots else prev_end_spot,
                window_low=spots[0] if spots else prev_end_spot,
                window_range=None, window_open=prev_end_spot, window_close=spots[-1] if spots else prev_end_spot,
                close_location_in_range=0.5, movement_relative_to_prev=0.0,
                breadth_start="Unavailable", breadth_end="Unavailable", breadth_change="UNAVAILABLE",
                breadth_delta=None, breadth_trend="STABLE", breadth_divergence="NEUTRAL",
                vix_start=None, vix_end=None, vix_change=None, vix_trend="STABLE",
                pcr_start=None, pcr_end=None, pcr_change=None, options_available=False,
                options_narrative="Options change analysis unavailable (insufficient snapshots in window).",
                significance_classification="INSUFFICIENT_EVIDENCE",
                headline=f"{w_start}–{w_end} IST | INSUFFICIENT WINDOW EVIDENCE",
                what_happened=[
                    f"ArdhaMind observed only {obs_count} telemetry checkpoint(s) (span: {round(span_seconds)}s) for {w_start}–{w_end} IST window."
                ],
                why_it_matters=[
                    "Telemetric observation density was too sparse to classify window movement or market character truthfully."
                ],
                watch_next=[
                    "Session complete; final session state preserved." if is_session_closed else "Awaiting telemetry density in subsequent window."
                ],
                contains_telemetry_gap=has_gap_flag or (obs_count < 2),
                data_quality=data_quality
            )

        # Sufficient or Building Window Calculation
        win_open = spots[0] if spots else prev_end_spot
        win_close = spots[-1] if spots else win_open

        start_spot = prev_end_spot if (prev_end_spot is not None) else win_open
        end_spot = win_close if win_close is not None else start_spot

        all_spots = (spots + ([prev_end_spot] if prev_end_spot else [])) if spots else ([start_spot] if start_spot else [])
        win_high = max(all_spots) if all_spots else 0.0
        win_low = min(all_spots) if all_spots else 0.0
        win_range = round((win_high - win_low), 2) if (win_high and win_low) else 0.0

        p_change = round((end_spot - start_spot), 2) if (end_spot and start_spot) else 0.0
        p_pct = round((p_change / start_spot) * 100, 2) if (start_spot and start_spot > 0) else 0.0

        close_loc = 0.5
        if win_range > 0 and win_close and win_low:
            close_loc = round((win_close - win_low) / win_range, 2)

        mov_rel_prev = round(p_change - (prev_change_pts or 0.0), 2)

        # Breadth Calculations
        b_start_obj = b_snaps[0] if b_snaps else {}
        b_end_obj = b_snaps[-1] if b_snaps else {}

        raw_adv_start = b_start_obj.get("advances") if isinstance(b_start_obj, dict) else 25
        raw_dec_start = b_start_obj.get("declines") if isinstance(b_start_obj, dict) else 25
        raw_adv_end = b_end_obj.get("advances") if isinstance(b_end_obj, dict) else raw_adv_start
        raw_dec_end = b_end_obj.get("declines") if isinstance(b_end_obj, dict) else raw_dec_start

        adv_start = int(raw_adv_start) if raw_adv_start is not None else 25
        dec_start = int(raw_dec_start) if raw_dec_start is not None else 25
        adv_end = int(raw_adv_end) if raw_adv_end is not None else adv_start
        dec_end = int(raw_dec_end) if raw_dec_end is not None else dec_start

        b_start_str = f"{adv_start}A / {dec_start}D"
        b_end_str = f"{adv_end}A / {dec_end}D"
        b_delta = adv_end - adv_start
        b_change_str = f"{'+' if b_delta >= 0 else ''}{b_delta}"

        if b_delta >= 4:
            b_trend = "STRENGTHENING"
        elif b_delta <= -4:
            b_trend = "WEAKENING"
        else:
            b_trend = "STABLE"

        if p_change > 5.0 and b_delta < -3:
            b_divergence = "BEARISH_DIVERGENCE"
        elif p_change < -5.0 and b_delta > 3:
            b_divergence = "BULLISH_DIVERGENCE"
        elif p_change > 5.0 and b_delta > 3:
            b_divergence = "CONFIRMING_BULLISH"
        elif p_change < -5.0 and b_delta < -3:
            b_divergence = "CONFIRMING_BEARISH"
        elif abs(p_change) <= 5.0 and b_delta >= 5:
            b_divergence = "BULLISH_DIVERGENCE"
        elif abs(p_change) <= 5.0 and b_delta <= -5:
            b_divergence = "BEARISH_DIVERGENCE"
        else:
            b_divergence = "NEUTRAL"

        # VIX Calculations
        v_start_obj = vix_snaps[0] if vix_snaps else None
        v_end_obj = vix_snaps[-1] if vix_snaps else None

        v_start = float(v_start_obj.get("value")) if (isinstance(v_start_obj, dict) and v_start_obj.get("value")) else (float(v_start_obj) if isinstance(v_start_obj, (int, float)) else None)
        v_end = float(v_end_obj.get("value")) if (isinstance(v_end_obj, dict) and v_end_obj.get("value")) else (float(v_end_obj) if isinstance(v_end_obj, (int, float)) else None)

        v_change = round((v_end - v_start), 2) if (v_end is not None and v_start is not None) else 0.0
        if v_change >= 0.3:
            v_trend = "EXPANDING"
        elif v_change <= -0.3:
            v_trend = "CONTRACTING"
        else:
            v_trend = "STABLE"

        # Options Calculations
        pcr_start = None
        pcr_end = None
        pcr_change = 0.0
        options_available = len(opt_snaps) >= 2
        options_narrative = "Options positioning change analysis unavailable (requires >=2 snapshots)."

        if options_available:
            p1 = opt_snaps[0].get("pcr") if isinstance(opt_snaps[0], dict) else None
            p2 = opt_snaps[-1].get("pcr") if isinstance(opt_snaps[-1], dict) else None
            if p1 and p2:
                pcr_start = round(float(p1), 2)
                pcr_end = round(float(p2), 2)
                pcr_change = round(pcr_end - pcr_start, 2)
                options_narrative = f"Option PCR moved from {pcr_start:.2f} to {pcr_end:.2f} ({'+' if pcr_change >= 0 else ''}{pcr_change:.2f})."

        abs_p = abs(p_change)
        if abs_p >= 40.0 or win_range >= 50.0 or abs(b_delta) >= 12:
            sig_class = "MAJOR"
        elif abs_p >= 25.0 or win_range >= 35.0 or abs(b_delta) >= 8:
            sig_class = "SIGNIFICANT"
        elif abs_p >= 15.0 or win_range >= 20.0 or abs(b_delta) >= 5:
            sig_class = "NOTABLE"
        elif win_range < 15.0 and abs_p < 10.0 and abs(b_delta) < 4:
            sig_class = "QUIET"
        else:
            sig_class = "NORMAL"

        headline = f"{w_start}–{w_end} IST | {sig_class} WINDOW"

        what_happened = [
            f"NIFTY spot moved {'+' if p_change >= 0 else ''}{p_change:.2f} pts ({'+' if p_pct >= 0 else ''}{p_pct:.2f}%) from {start_spot:,.2f} to {end_spot:,.2f}." if (start_spot and end_spot) else "NIFTY spot maintained current level.",
            f"Intraday window range spanned {win_range:.2f} pts (High: {win_high:,.2f}, Low: {win_low:,.2f}).",
            f"Constituent breadth changed from {b_start_str} to {b_end_str} ({b_change_str})."
        ]

        why_it_matters = []
        if b_divergence == "CONFIRMING_BULLISH":
            why_it_matters.append("Price and breadth strengthened together, indicating broader participation across constituent sectors.")
        elif b_divergence == "CONFIRMING_BEARISH":
            why_it_matters.append("Price and breadth declined together, indicating widespread selling pressure across NIFTY constituents.")
        elif b_divergence == "BEARISH_DIVERGENCE":
            why_it_matters.append("Price moved higher while constituent breadth weakened, indicating a divergent move concentrated in heavyweights.")
        elif b_divergence == "BULLISH_DIVERGENCE":
            why_it_matters.append("Price remained quiet while constituent breadth improved, indicating underlying accumulation-like strength.")
        elif sig_class == "QUIET":
            why_it_matters.append("Adequately sampled flat window indicates temporary consolidation and balanced buyer/seller equilibrium.")
        else:
            why_it_matters.append(f"Window structure reflects {sig_class.lower()} market activity with {b_trend.lower()} constituent breadth.")

        watch_next = []
        if is_session_closed:
            watch_next.append(f"SESSION COMPLETE. Final window closed at {end_spot:,.2f} IST. Intraday session telemetry complete.")
        elif p_change > 0:
            watch_next.append(f"Continuation is supported if breadth remains above {adv_end} advances and price holds above {win_low:,.2f}.")
        elif p_change < 0:
            watch_next.append(f"Further downside risk if advances stay below {adv_end} and price remains below {win_high:,.2f}.")
        else:
            watch_next.append(f"Watch for range breakout beyond {win_high:,.2f} or breakdown below {win_low:,.2f}.")

        return MarketWindowAnalysis(
            window_start=w_start, window_end=w_end, generated_at=now_str,
            analysis_status=analysis_status, start_spot=start_spot, end_spot=end_spot,
            price_change_points=p_change, price_change_percent=p_pct,
            window_high=win_high, window_low=win_low, window_range=win_range,
            window_open=win_open, window_close=win_close,
            close_location_in_range=close_loc, movement_relative_to_prev=mov_rel_prev,
            breadth_start=b_start_str, breadth_end=b_end_str, breadth_change=b_change_str,
            breadth_delta=b_delta, breadth_trend=b_trend, breadth_divergence=b_divergence,
            vix_start=v_start, vix_end=v_end, vix_change=v_change, vix_trend=v_trend,
            pcr_start=pcr_start, pcr_end=pcr_end, pcr_change=pcr_change,
            options_available=options_available, options_narrative=options_narrative,
            significance_classification=sig_class, headline=headline,
            what_happened=what_happened, why_it_matters=why_it_matters, watch_next=watch_next,
            contains_telemetry_gap=has_gap_flag, data_quality=data_quality
        )

    @classmethod
    def _detect_significant_events(
        cls,
        state: Dict[str, Any],
        history: List[Dict[str, Any]],
        today_analysis_report: Optional[Dict[str, Any]],
        windows: List[MarketWindowAnalysis]
    ) -> List[SignificantEvent]:
        events: List[SignificantEvent] = []

        m_data = state.get("market_data") or state.get("marketContext") or {}
        spot = m_data.get("current_spot")
        vwap = m_data.get("vwap")
        breadth = m_data.get("breadth") or {}
        advances = breadth.get("advances")
        declines = breadth.get("declines")

        # 1. State-level LEVEL_BREAK / LEVEL_RECLAIM detection
        if spot is not None and vwap is not None:
            if spot < vwap - 10.0:
                e_id = "EVT-LEVEL-BREAK-VWAP"
                if e_id not in cls._emitted_event_states:
                    cls._emitted_event_states.add(e_id)
                    events.append(SignificantEvent(
                        event_id=e_id,
                        event_type="LEVEL_BREAK",
                        timestamp="Current",
                        significance="SIGNIFICANT",
                        headline="VWAP Support Broken",
                        what_happened=f"NIFTY spot ({spot:,.2f}) crossed below VWAP anchor ({vwap:,.2f}).",
                        why_it_matters="Loss of VWAP anchor indicates intra-session selling pressure taking control.",
                        watch_next=f"Watch whether spot reclaims {vwap:,.2f}.",
                        source_window="Live State",
                        evidence_data={"spot": spot, "vwap": vwap}
                    ))
            elif spot > vwap + 10.0:
                e_id = "EVT-LEVEL-RECLAIM-VWAP"
                if e_id not in cls._emitted_event_states:
                    cls._emitted_event_states.add(e_id)
                    events.append(SignificantEvent(
                        event_id=e_id,
                        event_type="LEVEL_RECLAIM",
                        timestamp="Current",
                        significance="SIGNIFICANT",
                        headline="VWAP Anchor Reclaimed",
                        what_happened=f"NIFTY spot ({spot:,.2f}) reclaimed VWAP anchor ({vwap:,.2f}).",
                        why_it_matters="Reclaiming VWAP anchor indicates buyer defense and stabilizing intraday posture.",
                        watch_next=f"Watch whether spot holds above {vwap:,.2f}.",
                        source_window="Live State",
                        evidence_data={"spot": spot, "vwap": vwap}
                    ))

        # 2. State-level BREADTH_COLLAPSE detection
        if declines is not None and declines >= 35:
            e_id = "EVT-BREADTH-COLLAPSE-STATE"
            if e_id not in cls._emitted_event_states:
                cls._emitted_event_states.add(e_id)
                events.append(SignificantEvent(
                    event_id=e_id,
                    event_type="BREADTH_COLLAPSE",
                    timestamp="Current",
                    significance="NOTABLE",
                    headline=f"Constituent Breadth Collapse ({declines} Declines)",
                    what_happened=f"NIFTY constituent declines expanded to {declines}/50.",
                    why_it_matters="Deteriorating participation warns of broad selling pressure.",
                    watch_next="Watch whether advances recover above 20.",
                    source_window="Live State",
                    evidence_data={"declines": declines}
                ))

        # 3. Window-based event detection
        for w in windows:
            if w.analysis_status in ("INSUFFICIENT_WINDOW_EVIDENCE", "INSUFFICIENT_DATA") or w.significance_classification == "INSUFFICIENT_EVIDENCE":
                continue

            if w.price_change_points is not None and w.window_range is not None:
                if abs(w.price_change_points) >= 30.0 and w.window_range >= 40.0:
                    e_id = f"EVT-ACCEL-{w.window_start}"
                    if e_id not in cls._emitted_event_states:
                        cls._emitted_event_states.add(e_id)
                        events.append(SignificantEvent(
                            event_id=e_id,
                            event_type="PRICE_ACCELERATION",
                            timestamp=f"{w.window_end} IST",
                            significance="SIGNIFICANT",
                            headline=f"Price Acceleration ({'+' if w.price_change_points >= 0 else ''}{w.price_change_points:.2f} pts)",
                            what_happened=f"NIFTY spot accelerated {'upward' if w.price_change_points >= 0 else 'downward'} by {abs(w.price_change_points):.2f} pts in 15m window.",
                            why_it_matters="Strong momentum expansion indicates aggressive directional positioning.",
                            watch_next=f"Monitor key range boundary at {w.window_high if w.price_change_points >= 0 else w.window_low:,.2f}.",
                            source_window=f"{w.window_start}–{w.window_end}",
                            evidence_data={"price_change": w.price_change_points, "range": w.window_range}
                        ))

            if w.breadth_delta is not None and w.breadth_delta >= 8:
                e_id = f"EVT-BSURGE-{w.window_start}"
                if e_id not in cls._emitted_event_states:
                    cls._emitted_event_states.add(e_id)
                    events.append(SignificantEvent(
                        event_id=e_id,
                        event_type="BREADTH_SURGE",
                        timestamp=f"{w.window_end} IST",
                        significance="NOTABLE",
                        headline=f"Constituent Breadth Surge (+{w.breadth_delta} Advances)",
                        what_happened=f"NIFTY constituent advances surged by +{w.breadth_delta} to reach {w.breadth_end}.",
                        why_it_matters="Broadening participation reinforces market stability and trend credibility.",
                        watch_next="Watch whether advances hold above 30 in subsequent windows.",
                        source_window=f"{w.window_start}–{w.window_end}",
                        evidence_data={"breadth_delta": w.breadth_delta, "breadth_end": w.breadth_end}
                    ))

            elif w.breadth_delta <= -8:
                e_id = f"EVT-BCOLLAPSE-{w.window_start}"
                if e_id not in cls._emitted_event_states:
                    cls._emitted_event_states.add(e_id)
                    events.append(SignificantEvent(
                        event_id=e_id,
                        event_type="BREADTH_COLLAPSE",
                        timestamp=f"{w.window_end} IST",
                        significance="NOTABLE",
                        headline=f"Constituent Breadth Collapse ({w.breadth_delta} Advances)",
                        what_happened=f"NIFTY constituent advances dropped by {w.breadth_delta} to {w.breadth_end}.",
                        why_it_matters="Deteriorating participation warns of weakness spreading across sector constituents.",
                        watch_next="Watch for potential test of lower window support.",
                        source_window=f"{w.window_start}–{w.window_end}",
                        evidence_data={"breadth_delta": w.breadth_delta, "breadth_end": w.breadth_end}
                    ))

            if w.breadth_divergence in ("BEARISH_DIVERGENCE", "BULLISH_DIVERGENCE"):
                e_id = f"EVT-DIV-{w.window_start}"
                if e_id not in cls._emitted_event_states:
                    cls._emitted_event_states.add(e_id)
                    events.append(SignificantEvent(
                        event_id=e_id,
                        event_type="PRICE_BREADTH_DIVERGENCE",
                        timestamp=f"{w.window_end} IST",
                        significance="MAJOR",
                        headline=f"Price-Breadth Divergence ({w.breadth_divergence.replace('_', ' ')})",
                        what_happened=f"NIFTY spot price and constituent breadth exhibited opposite directions ({w.breadth_divergence}).",
                        why_it_matters="Divergence between index price and constituent participation signals potential reversal or internal pressure.",
                        watch_next="Watch for divergence resolution in subsequent window.",
                        source_window=f"{w.window_start}–{w.window_end}",
                        evidence_data={"divergence": w.breadth_divergence, "price_change": w.price_change_points}
                    ))

        return events
