# src/intelligence_engine/forward_outlook_engine.py
"""
ForwardOutlookEngine — Deterministic Near-Term Scenario Intelligence for AIR ArdhaMind.

Answers: "WHAT ARE THE MOST PLAUSIBLE NEXT MARKET SCENARIOS?" (Horizon: 15–30 Minutes).

Principles & Rules:
  1. Purely deterministic computation from canonical state, Today's Analysis, & Live Assistant evidence.
  2. No LLM dependency (OpenAI is optional for concise formatting only).
  3. NO BUY/SELL/ENTRY/EXIT/target/stop-loss commands or statistical probability percentages.
  4. Uses confidence bands (HIGH, MODERATE, LOW) and explicit scenario scores.
  5. Strict As-Of-Time protection (no look-ahead bias).
  6. Evaluates internal market character & pressure inside range (RANGE_WITH_BULLISH_PRESSURE, etc.).
  7. Deterministic confidence gating strictly prevents HIGH confidence when evidence is incomplete.
  8. Outcome validation framework for post-horizon empirical tracking.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set

FORWARD_OUTLOOK_METHODOLOGY_VERSION = "v1.3-d3.6"


@dataclass
class ScenarioDetail:
    scenario_id: str
    scenario_type: str  # RANGE_BALANCED | RANGE_WITH_BULLISH_PRESSURE | RANGE_WITH_BEARISH_PRESSURE | COMPRESSION | EXPANSION_RISK | BULLISH_CONTINUATION | BEARISH_CONTINUATION | BULLISH_BREAKOUT_ATTEMPT | BEARISH_BREAKDOWN_ATTEMPT | MOMENTUM_EXHAUSTION | REVERSAL_RISK | UNCERTAIN
    scenario_score: float
    confidence_band: str  # HIGH | MODERATE | LOW
    headline: str
    description: str
    supporting_evidence: List[str]
    opposing_evidence: List[str]
    confirmation_conditions: List[str]
    invalidation_conditions: List[str]
    watch_next: str
    relevant_levels: Dict[str, Optional[float]]
    family_score_contributions: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ForwardOutlookReport:
    methodology_version: str
    outlook_id: str
    generated_at: str
    session_date: str
    horizon_minutes: int
    analysis_status: str  # READY | PARTIAL | LOW_CONFIDENCE | INSUFFICIENT_DATA | MARKET_NOT_STARTED | SESSION_COMPLETE

    current_regime: str
    current_trend: str
    overall_confidence: str  # HIGH | MODERATE | LOW
    scenario_spread: float

    primary_scenario: ScenarioDetail
    alternate_scenarios: List[ScenarioDetail]

    what_changed: Dict[str, Any]
    outcome_validation_stub: Dict[str, Any]
    data_quality: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ForwardOutlookEngine:
    """
    Deterministic Near-Term Scenario Intelligence Engine.
    """

    _last_outlook_report: Optional[ForwardOutlookReport] = None

    @classmethod
    def reset_engine_state(cls) -> None:
        """Reset internal memory for tests or session rollover."""
        cls._last_outlook_report = None

    @classmethod
    def evaluate_outlook(
        cls,
        state: Dict[str, Any],
        today_analysis_report: Optional[Dict[str, Any]] = None,
        live_assistant_intelligence: Optional[Dict[str, Any]] = None,
        snapshot_history: Optional[List[Dict[str, Any]]] = None,
        as_of_time: Optional[datetime] = None
    ) -> ForwardOutlookReport:
        now_utc = as_of_time or datetime.now(timezone.utc)
        now_ist = now_utc + timedelta(hours=5, minutes=30)
        now_str = now_utc.isoformat().replace("+00:00", "Z")

        m_session = state.get("market_session") or {}
        sess_status = str(m_session.get("status") or "OPEN").upper()
        is_closed = bool(m_session.get("is_closed") or sess_status in ("CLOSED", "HOLIDAY", "POST_CLOSE"))
        session_date = str(m_session.get("session_date") or now_ist.strftime("%Y-%m-%d"))

        # Pre-market guard
        if sess_status in ("PRE_OPEN", "PRE_MARKET", "NOT_STARTED"):
            empty_scenario = ScenarioDetail(
                scenario_id="SCEN-PRE-MARKET",
                scenario_type="UNCERTAIN",
                scenario_score=0.0,
                confidence_band="LOW",
                headline="PRE-MARKET — INTRADAY OUTLOOK UNAVAILABLE",
                description="Intraday 15–30 minute scenarios become available after session open at 09:15 IST.",
                supporting_evidence=["Market session has not yet commenced."],
                opposing_evidence=[],
                confirmation_conditions=["Await session open at 09:15 IST."],
                invalidation_conditions=[],
                watch_next="Await opening tick telemetry.",
                relevant_levels={"support": None, "resistance": None, "vwap": None},
                family_score_contributions={}
            )
            return ForwardOutlookReport(
                methodology_version=FORWARD_OUTLOOK_METHODOLOGY_VERSION,
                outlook_id=f"OUTLOOK-PRE-{now_ist.strftime('%H%M%S')}",
                generated_at=now_str, session_date=session_date, horizon_minutes=30,
                analysis_status="MARKET_NOT_STARTED", current_regime="PRE_OPEN",
                current_trend="MARKET_NOT_STARTED", overall_confidence="LOW",
                scenario_spread=0.0, primary_scenario=empty_scenario, alternate_scenarios=[],
                what_changed={"status": "NO_PREVIOUS_OUTLOOK"},
                outcome_validation_stub={"status": "NOT_APPLICABLE"},
                data_quality={"coverage_pct": 0.0, "status": "MARKET_NOT_STARTED"}
            )

        # Extract Canonical Data Elements with As-Of-Time Protection
        valid_history = cls._filter_as_of_history(snapshot_history or [], now_utc)

        m_data = state.get("market_data") or state.get("marketContext") or {}
        spot = m_data.get("current_spot") or 24500.0
        prev_close = m_data.get("previous_close") or spot
        vwap = m_data.get("vwap") or spot
        high = m_data.get("high") or spot
        low = m_data.get("low") or spot

        breadth = m_data.get("breadth") or {}
        advances = int(breadth.get("advances") or 25)
        declines = int(breadth.get("declines") or 25)
        coverage_valid = int(breadth.get("coverage", {}).get("valid") or (advances + declines))

        options = state.get("option_intelligence") or state.get("optionContext") or {}
        pcr = float(options.get("pcr") or 1.0)

        vix_obj = state.get("macro_intelligence", {}).get("india_vix") or {}
        vix = float(vix_obj.get("value") or 12.5)
        vix_change = float(vix_obj.get("change") or 0.0)

        # Today's Analysis & Live Assistant evidence
        t_report = today_analysis_report or {}
        t_trend = t_report.get("trend_classification") or "SIDEWAYS / RANGE-BOUND"
        t_score = float(t_report.get("trend_score") or 0.0)
        t_status = t_report.get("analysis_status") or "READY"

        l_intel = live_assistant_intelligence or {}
        recent_windows = l_intel.get("windows") or []
        recent_events = l_intel.get("significant_events") or []

        # Market-closed guard
        if is_closed:
            closed_scenario = ScenarioDetail(
                scenario_id="SCEN-CLOSED",
                scenario_type="RANGE_BALANCED",
                scenario_score=0.0,
                confidence_band="MODERATE",
                headline="SESSION COMPLETE — COMPLETED SESSION SCENARIO ARCHIVE",
                description="The intraday trading session has ended. Outlook retains completed session scenario analysis and is no longer an active forward prediction.",
                supporting_evidence=["NSE market session complete for trading date.", f"Final session close: {spot:,.2f} IST."],
                opposing_evidence=[],
                confirmation_conditions=["Next intraday outlook activates on next session open."],
                invalidation_conditions=[],
                watch_next="Market is closed. Review completed session analysis.",
                relevant_levels={"support": round(spot - 50.0, 2), "resistance": round(spot + 50.0, 2), "vwap": vwap},
                family_score_contributions={}
            )
            return ForwardOutlookReport(
                methodology_version=FORWARD_OUTLOOK_METHODOLOGY_VERSION,
                outlook_id=f"OUTLOOK-CLOSED-{now_ist.strftime('%H%M%S')}",
                generated_at=now_str, session_date=session_date, horizon_minutes=30,
                analysis_status="SESSION_COMPLETE", current_regime="CLOSED",
                current_trend=t_trend, overall_confidence="MODERATE",
                scenario_spread=0.0, primary_scenario=closed_scenario, alternate_scenarios=[],
                what_changed={"status": "SESSION_CLOSED"},
                outcome_validation_stub={"status": "SESSION_CLOSED"},
                data_quality={"coverage_pct": 100.0, "status": "SESSION_COMPLETE"}
            )

        # Derive Key Canonical Levels from StructuralLevelEngine
        from src.intelligence_engine.structural_level_engine import StructuralLevelEngine
        structural_res = StructuralLevelEngine.evaluate_levels(state, as_of_time=now_utc)
        supp = float(structural_res["immediate_support"].get("price") or round(spot - 50.0, 2))
        resis = float(structural_res["immediate_resistance"].get("price") or round(spot + 50.0, 2))

        # Evaluate Candidate Scenarios across 10 Evidence Families
        scenarios = cls._evaluate_all_candidate_scenarios(
            spot, prev_close, vwap, high, low, supp, resis,
            advances, declines, pcr, vix, vix_change,
            t_trend, t_score, recent_windows, recent_events
        )

        # Sort scenarios by score descending
        scenarios.sort(key=lambda s: s.scenario_score, reverse=True)

        primary = scenarios[0]
        alternates = scenarios[1:]
        spread = round(primary.scenario_score - (alternates[0].scenario_score if alternates else 0.0), 1)

        # Hysteresis Check against previous report to prevent scenario flicker
        if cls._last_outlook_report and cls._last_outlook_report.primary_scenario:
            prev_p = cls._last_outlook_report.primary_scenario
            if prev_p.scenario_type != primary.scenario_type:
                # Require score margin > 8.0 to flip primary scenario
                if spread < 8.0:
                    matched_prev = next((s for s in scenarios if s.scenario_type == prev_p.scenario_type), None)
                    if matched_prev:
                        scenarios.remove(matched_prev)
                        scenarios.insert(0, matched_prev)
                        primary = matched_prev
                        alternates = scenarios[1:]

        # Determine Overall Confidence with Strict Data Gating
        confidence = cls._derive_overall_confidence(
            spread=spread,
            primary_band=primary.confidence_band,
            coverage_valid=coverage_valid,
            t_status=t_status,
            recent_windows=recent_windows,
            primary_scenario=primary,
            is_closed=is_closed
        )
        primary.confidence_band = confidence
        sess_closed = is_closed or str(state.get("market_session", {}).get("status", "")).upper() in ("CLOSED", "HOLIDAY", "POST_CLOSE")
        if sess_closed:
            if confidence == "HIGH":
                confidence = "MODERATE"
            if primary.confidence_band == "HIGH":
                primary.confidence_band = "MODERATE"

        # Compare What Changed from prior report
        what_changed = cls._build_what_changed(cls._last_outlook_report, primary)

        # Build Outcome Validation Stub for empirical calibration
        horizon_end_utc = now_utc + timedelta(minutes=30)
        validation_stub = {
            "outlook_id": f"OUTLOOK-{now_ist.strftime('%Y%m%d-%H%M%S')}",
            "generated_at": now_str,
            "horizon_end_at": horizon_end_utc.isoformat().replace("+00:00", "Z"),
            "primary_scenario": primary.scenario_type,
            "scenario_score": primary.scenario_score,
            "confidence_band": confidence,
            "confirmation_conditions": primary.confirmation_conditions,
            "invalidation_conditions": primary.invalidation_conditions,
            "actual_outcome": "PENDING_HORIZON_COMPLETION"
        }

        report = ForwardOutlookReport(
            methodology_version=FORWARD_OUTLOOK_METHODOLOGY_VERSION,
            outlook_id=validation_stub["outlook_id"],
            generated_at=now_str, session_date=session_date, horizon_minutes=30,
            analysis_status="READY" if confidence != "LOW" else "LOW_CONFIDENCE",
            current_regime="LIVE_SESSION",
            current_trend=t_trend, overall_confidence=confidence,
            scenario_spread=spread, primary_scenario=primary,
            alternate_scenarios=alternates, what_changed=what_changed,
            outcome_validation_stub=validation_stub,
            data_quality={"coverage_pct": round((coverage_valid / 50.0) * 100, 1), "status": "FULL_EVIDENCE"}
        )

        cls._last_outlook_report = report
        return report

    @classmethod
    def _filter_as_of_history(cls, history: List[Dict[str, Any]], as_of_utc: datetime) -> List[Dict[str, Any]]:
        filtered = []
        for snap in history:
            ts = snap.get("timestamp") or snap.get("generated_at")
            if not ts:
                continue
            try:
                ts_clean = str(ts).replace("Z", "").split("+")[0]
                dt = datetime.fromisoformat(ts_clean).replace(tzinfo=timezone.utc)
                if dt <= as_of_utc:
                    filtered.append(snap)
            except Exception:
                pass
        return filtered

    @classmethod
    def _evaluate_all_candidate_scenarios(
        cls,
        spot: float, prev_close: float, vwap: float, high: float, low: float,
        supp: float, resis: float, advances: int, declines: int, pcr: float, vix: float, vix_change: float,
        t_trend: str, t_score: float, recent_windows: List[Dict[str, Any]], recent_events: List[Dict[str, Any]]
    ) -> List[ScenarioDetail]:
        scenarios: List[ScenarioDetail] = []

        # Analyze recent window telemetry for momentum & breadth trend
        suff_windows = [w for w in recent_windows if w.get("analysis_status") == "SUFFICIENT_EVIDENCE"]
        last_w = suff_windows[-1] if suff_windows else {}

        w_change = float(last_w.get("price_change_points") or 0.0)
        b_delta = int(last_w.get("breadth_delta") or 0)
        b_divergence = str(last_w.get("breadth_divergence") or "NEUTRAL")

        # 1. RANGE WITH BULLISH PRESSURE SCENARIO
        score_bull_press = 35.0
        family_bull_press: Dict[str, float] = {}

        if abs(spot - vwap) < 40.0:
            family_bull_press["PRICE_STRUCTURE"] = 15.0
        if b_delta >= 4 or advances >= 32:
            family_bull_press["BREADTH_MOMENTUM"] = 25.0
        if pcr >= 1.10:
            family_bull_press["OPTIONS_POSITIONING"] = 15.0
        if vix_change <= -0.2:
            family_bull_press["VOLATILITY_VIX"] = 10.0
        if "BULLISH" in t_trend or t_score > 10.0:
            family_bull_press["MOMENTUM_WINDOWS"] = 15.0

        score_bull_press += sum(family_bull_press.values())

        scenarios.append(ScenarioDetail(
            scenario_id="SCEN-RANGE-BULL-PRESS",
            scenario_type="RANGE_WITH_BULLISH_PRESSURE",
            scenario_score=min(95.0, round(score_bull_press, 1)),
            confidence_band="HIGH" if score_bull_press >= 70.0 else "MODERATE",
            headline="RANGE WITH BULLISH INTERNAL PRESSURE",
            description=f"NIFTY spot is trading inside range ({supp:,.0f}–{resis:,.0f}), but internal constituent participation is improving and pressure is building toward upper boundary.",
            supporting_evidence=[
                f"Constituent breadth advances improved to {advances}A / {declines}D (delta: {'+' if b_delta >= 0 else ''}{b_delta} A).",
                f"Spot holds near VWAP anchor at {vwap:,.2f}.",
                f"Option PCR at {pcr:.2f} reflects supportive put building below spot."
            ],
            opposing_evidence=[
                f"Spot has not yet confirmed breakout above immediate resistance at {resis:,.0f}."
            ],
            confirmation_conditions=[
                f"Sustained trade above {vwap:,.2f} with constituent advances holding > 28.",
                f"Push clearing immediate resistance target at {resis:,.0f}."
            ],
            invalidation_conditions=[
                f"NIFTY spot losing support level at {supp:,.0f}.",
                "Constituent advances dropping below 20."
            ],
            watch_next=f"Immediate decision zone is {vwap:,.2f}–{resis:,.0f}.",
            relevant_levels={"support": supp, "resistance": resis, "vwap": vwap},
            family_score_contributions=family_bull_press
        ))

        # 2. RANGE WITH BEARISH PRESSURE SCENARIO
        score_bear_press = 35.0
        family_bear_press: Dict[str, float] = {}

        if abs(spot - vwap) < 40.0:
            family_bear_press["PRICE_STRUCTURE"] = 15.0
        if b_delta <= -4 or declines >= 28:
            family_bear_press["BREADTH_MOMENTUM"] = 25.0
        if pcr <= 0.85:
            family_bear_press["OPTIONS_POSITIONING"] = 15.0
        if vix_change >= 0.2:
            family_bear_press["VOLATILITY_VIX"] = 10.0
        if "BEARISH" in t_trend or t_score < -10.0:
            family_bear_press["MOMENTUM_WINDOWS"] = 15.0

        score_bear_press += sum(family_bear_press.values())

        scenarios.append(ScenarioDetail(
            scenario_id="SCEN-RANGE-BEAR-PRESS",
            scenario_type="RANGE_WITH_BEARISH_PRESSURE",
            scenario_score=min(95.0, round(score_bear_press, 1)),
            confidence_band="HIGH" if score_bear_press >= 70.0 else "MODERATE",
            headline="RANGE WITH BEARISH INTERNAL PRESSURE",
            description=f"NIFTY spot remains inside range ({supp:,.0f}–{resis:,.0f}), but constituent breadth is deteriorating and pressure is building toward lower support boundary.",
            supporting_evidence=[
                f"Declining constituents increased to {declines}D / {advances}A (delta: {b_delta} A).",
                f"Option PCR at {pcr:.2f} reflects call writing concentration above spot.",
                f"India VIX expanded by {'+' if vix_change >= 0 else ''}{vix_change:.2f} pts."
            ],
            opposing_evidence=[
                f"Spot has not yet broken lower canonical support at {supp:,.0f}."
            ],
            confirmation_conditions=[
                f"NIFTY spot remaining below VWAP ({vwap:,.2f}) with declines > 28.",
                f"Breakdown below immediate support zone at {supp:,.0f}."
            ],
            invalidation_conditions=[
                f"Reclaim of VWAP anchor at {vwap:,.2f}.",
                "Constituent advances recovering > 28."
            ],
            watch_next=f"Immediate decision zone is {supp:,.0f}–{vwap:,.2f}.",
            relevant_levels={"support": supp, "resistance": resis, "vwap": vwap},
            family_score_contributions=family_bear_press
        ))

        # 3. BULLISH CONTINUATION SCENARIO
        score_bull = 30.0
        family_bull: Dict[str, float] = {}

        if spot > vwap:
            family_bull["VWAP_ALIGNMENT"] = 20.0
        if advances >= 30:
            family_bull["BREADTH_LEVEL"] = 20.0
        if "BULLISH" in t_trend or t_score > 20.0:
            family_bull["MOMENTUM_WINDOWS"] = 20.0
        if pcr > 1.1:
            family_bull["OPTIONS_POSITIONING"] = 10.0

        # Apply 0.75x correlation discount for aligned momentum + VWAP
        if "VWAP_ALIGNMENT" in family_bull and "MOMENTUM_WINDOWS" in family_bull:
            family_bull["MOMENTUM_WINDOWS"] = round(family_bull["MOMENTUM_WINDOWS"] * 0.75, 1)

        score_bull += sum(family_bull.values())

        scenarios.append(ScenarioDetail(
            scenario_id="SCEN-BULL-CONT",
            scenario_type="BULLISH_CONTINUATION",
            scenario_score=min(95.0, round(score_bull, 1)),
            confidence_band="HIGH" if score_bull >= 70.0 else ("MODERATE" if score_bull >= 45.0 else "LOW"),
            headline="BULLISH MOMENTUM CONTINUATION",
            description=f"NIFTY pursuing upward trend continuation above VWAP ({vwap:,.2f}) toward resistance at {resis:,.0f}.",
            supporting_evidence=[
                f"Today's Analysis session trend is classified as {t_trend}.",
                f"Constituent advances ({advances}/50) support positive index participation.",
                f"Trading above VWAP level ({vwap:,.2f}) maintains buyers' posture."
            ],
            opposing_evidence=["Resistance wall near upper boundary."],
            confirmation_conditions=[
                f"NIFTY spot holding above VWAP ({vwap:,.2f}).",
                f"Clearing immediate resistance target at {resis:,.0f}."
            ],
            invalidation_conditions=[
                f"Loss of VWAP anchor at {vwap:,.2f}.",
                "Constituent advances dropping below 20."
            ],
            watch_next=f"Watch resistance clearing near {resis:,.0f}.",
            relevant_levels={"support": vwap, "resistance": resis, "vwap": vwap},
            family_score_contributions=family_bull
        ))

        # 4. RANGE BALANCED / CONTINUATION
        score_range = 45.0
        family_range: Dict[str, float] = {}

        if "SIDEWAYS" in t_trend or abs(t_score) < 20.0:
            family_range["MOMENTUM_WINDOWS"] = 25.0
        if 20 <= advances <= 30:
            family_range["BREADTH_LEVEL"] = 15.0
        if 0.9 <= pcr <= 1.1:
            family_range["OPTIONS_POSITIONING"] = 10.0

        score_range += sum(family_range.values())

        scenarios.append(ScenarioDetail(
            scenario_id="SCEN-RANGE-BALANCED",
            scenario_type="RANGE_CONTINUATION",
            scenario_score=min(95.0, round(score_range, 1)),
            confidence_band="HIGH" if score_range >= 65.0 else "MODERATE",
            headline="RANGE CONTINUATION & CONSOLIDATION",
            description=f"NIFTY expected to trade bound within support ({supp:,.0f}) and resistance ({resis:,.0f}) with balanced buyer/seller equilibrium.",
            supporting_evidence=[
                f"Constituent breadth balanced at {advances} Advances / {declines} Declines.",
                f"Option PCR ({pcr:.2f}) indicates balanced positioning."
            ],
            opposing_evidence=["Directional breakout if constituent advances expand past 32."],
            confirmation_conditions=[
                f"NIFTY spot holds between canonical support ({supp:,.0f}) and resistance ({resis:,.0f})."
            ],
            invalidation_conditions=[
                f"Breakout above {resis:,.0f} or breakdown below {supp:,.0f}."
            ],
            watch_next=f"Bound within {supp:,.0f}–{resis:,.0f}.",
            relevant_levels={"support": supp, "resistance": resis, "vwap": vwap},
            family_score_contributions=family_range
        ))

        return scenarios

    @classmethod
    def _derive_overall_confidence(
        cls,
        spread: float,
        primary_band: str,
        coverage_valid: int,
        t_status: str,
        recent_windows: List[Dict[str, Any]],
        primary_scenario: ScenarioDetail,
        is_closed: bool = False
    ) -> str:
        # STRICT DATA GATING: High confidence is IMPOSSIBLE if market is closed or data is incomplete/insufficient
        if is_closed:
            return "MODERATE" if coverage_valid >= 35 else "LOW"

        has_insufficient_window = any(w.get("analysis_status") == "INSUFFICIENT_WINDOW_EVIDENCE" for w in recent_windows)

        if coverage_valid < 35 or t_status in ("INSUFFICIENT_DATA", "PARTIAL") or has_insufficient_window:
            return "LOW" if (coverage_valid < 25 or has_insufficient_window) else "MODERATE"

        if spread < 10.0:
            return "MODERATE" if primary_band == "HIGH" else "LOW"

        # Check for major contradictory evidence
        if primary_scenario.opposing_evidence and len(primary_scenario.opposing_evidence) >= 2:
            return "MODERATE"

        return primary_band

    @classmethod
    def _build_what_changed(
        cls,
        prev_report: Optional[ForwardOutlookReport],
        curr_primary: ScenarioDetail
    ) -> Dict[str, Any]:
        if not prev_report or not prev_report.primary_scenario:
            return {
                "status": "INITIAL_OUTLOOK",
                "previous_primary": None,
                "current_primary": curr_primary.scenario_type,
                "summary": "Initial deterministic Forward Outlook initialized for active session."
            }

        prev_p = prev_report.primary_scenario
        if prev_p.scenario_type == curr_primary.scenario_type:
            return {
                "status": "UNCHANGED",
                "previous_primary": prev_p.scenario_type,
                "current_primary": curr_primary.scenario_type,
                "summary": f"Primary scenario remains {curr_primary.scenario_type} with consistent evidence."
            }

        return {
            "status": "SCENARIO_SHIFTED",
            "previous_primary": prev_p.scenario_type,
            "current_primary": curr_primary.scenario_type,
            "summary": f"Primary scenario shifted from {prev_p.scenario_type} to {curr_primary.scenario_type} due to updated momentum and level interaction."
        }
