# src/intelligence_engine/today_analysis_engine.py
"""
TodayAnalysisEngine — Deterministic Session Intelligence Engine for AIR ArdhaMind.

Answers authoritatively: "WHAT KIND OF MARKET DAY ARE WE HAVING SO FAR, AND WHY?"

Rules & Principles:
  1. Purely deterministic computation based strictly on canonical evidence.
  2. No LLM decision-making (LLM is optional for wording only).
  3. No trade recommendations, buy/sell calls, or price predictions.
  4. Explicitly surfaces contradicting factors and data-quality limitations.
  5. Multi-factor scoring across Price Structure, Breadth, Heavyweights, Derivatives, Volatility.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class FactorScore:
    name: str
    direction: str  # BULLISH | BEARISH | NEUTRAL
    score: float   # -100 to +100
    weight: float  # 0.0 to 1.0
    quality: str   # READY | PARTIAL | UNAVAILABLE
    description: str
    evidence_source: str


@dataclass
class SessionPhase:
    time_window: str
    phase_label: str
    headline: str
    importance: str


@dataclass
class TodayAnalysisReport:
    analysis_timestamp: str
    session_date: str
    market_session_state: str  # PRE_OPEN | MARKET_OPEN | CLOSED
    analysis_status: str       # READY | PARTIAL | DEGRADED | INSUFFICIENT_DATA | MARKET_NOT_STARTED | SESSION_COMPLETE

    trend_classification: str # STRONG BULLISH | BULLISH | MODERATELY BULLISH | BULLISH → SIDEWAYS | SIDEWAYS / RANGE-BOUND | BEARISH → SIDEWAYS | MODERATELY BEARISH | BEARISH | STRONG BEARISH | MIXED / UNCLEAR
    trend_score: float        # -100 to +100
    conviction: float         # 0.0 to 100.0%

    primary_driver: str
    supporting_drivers: List[str]
    contradicting_factors: List[str]

    session_statistics: Dict[str, Any]
    session_evolution: List[Dict[str, Any]]
    key_levels: Dict[str, Any]
    invalidation_conditions: Dict[str, Any]
    factor_breakdown: List[Dict[str, Any]]

    data_quality: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TodayAnalysisEngine:
    """
    Deterministic domain engine for intraday session analysis.
    """

    @classmethod
    def analyze(cls, state: Dict[str, Any], snapshot_history: Optional[List[Dict[str, Any]]] = None) -> TodayAnalysisReport:
        now_str = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        m_data = state.get("market_data") or state.get("marketContext") or {}
        m_session = state.get("market_session") or {}
        sess_status = str(m_session.get("status") or m_data.get("trading_session") or "OPEN").upper()
        is_closed = Boolean = bool(m_session.get("is_closed") or sess_status in ("CLOSED", "HOLIDAY", "POST_CLOSE"))
        session_date = str(m_session.get("session_date") or m_data.get("session_date") or datetime.now(timezone.utc).strftime("%Y-%m-%d"))

        # 1. Pre-market Check
        if sess_status in ("PRE_OPEN", "PRE_MARKET", "NOT_STARTED"):
            return cls._build_premarket_report(now_str, session_date, sess_status)

        # 2. Extract Canonical Metrics
        spot = m_data.get("current_spot")
        prev_close_raw = m_data.get("previous_close")
        prev_close = float(prev_close_raw) if prev_close_raw is not None else None
        open_price = float(m_data["open"]) if m_data.get("open") is not None else None
        high_price = float(m_data["high"]) if m_data.get("high") is not None else None
        low_price = float(m_data["low"]) if m_data.get("low") is not None else None
        breadth = m_data.get("breadth") or {}

        session_snaps = [s for s in (snapshot_history or []) if s.get("session_date") == session_date and s.get("spot") is not None]

        mkt_snaps = [s for s in session_snaps if s.get("market_session_phase") in ("MARKET_OPEN", "OPEN", "CONTINUOUS_TRADING", "CONTINUOUS")]
        eval_snaps = mkt_snaps if mkt_snaps else session_snaps

        # Hydrate from snapshot_history if spot or OHLC is missing
        if spot is None and session_snaps:
            spot = float(session_snaps[-1].get("spot"))

        if prev_close is None and session_snaps:
            prev_close = next((float(s.get("previous_close")) for s in reversed(session_snaps) if s.get("previous_close") is not None), None)

        if open_price is None and eval_snaps:
            first_mkt_snap = next((s for s in eval_snaps if s.get("market_session_phase") in ("MARKET_OPEN", "OPEN")), eval_snaps[0])
            open_price = float(first_mkt_snap.get("open") or first_mkt_snap.get("spot"))

        if high_price is None and eval_snaps:
            snap_highs = [float(s.get("high")) for s in eval_snaps if s.get("high") is not None]
            snap_spots = [float(s.get("spot")) for s in eval_snaps if isinstance(s.get("spot"), (int, float))]
            all_highs = snap_highs + snap_spots
            if all_highs:
                high_price = max(all_highs)

        if low_price is None and eval_snaps:
            snap_lows = [float(s.get("low")) for s in eval_snaps if s.get("low") is not None]
            snap_spots = [float(s.get("spot")) for s in eval_snaps if isinstance(s.get("spot"), (int, float))]
            all_lows = snap_lows + snap_spots
            if all_lows:
                low_price = min(all_lows)

        if not breadth and session_snaps:
            breadth = session_snaps[-1].get("breadth") or breadth

        if spot is None:
            return cls._build_insufficient_data_report(now_str, session_date, sess_status, breadth=breadth)

        # Sanitize OHLC invariants if values are observed (do not invent high/low from spot if unobserved)
        if high_price is not None:
            high_price = max(high_price, open_price if open_price is not None else high_price, spot)
        if low_price is not None:
            low_price = min(low_price, open_price if open_price is not None else low_price, spot)

        change = round(spot - prev_close, 2) if (prev_close is not None and prev_close > 0) else None
        change_pct = round((change / prev_close) * 100, 2) if (prev_close is not None and prev_close > 0 and change is not None) else None

        # Breadth
        breadth = m_data.get("breadth") or {}
        advances = breadth.get("advances")
        declines = breadth.get("declines")
        cov_raw = breadth.get("coverage")
        if isinstance(cov_raw, dict):
            valid_breadth = cov_raw.get("valid")
        elif isinstance(cov_raw, (int, float)):
            valid_breadth = int(cov_raw)
        else:
            valid_breadth = None
        if not valid_breadth:
            valid_breadth = (advances + declines) if (advances is not None and declines is not None) else 0

        # Heavyweights
        heavyweights = m_data.get("heavyweights") or []
        hw_total = len(heavyweights)
        hw_up = len([h for h in heavyweights if float(h.get("change") or 0.0) >= 0.0])

        # Options
        options = state.get("option_intelligence") or state.get("optionContext") or {}
        pcr = options.get("pcr")
        atm_strike = options.get("atm_strike")
        max_pain = options.get("max_pain")

        # Volatility
        macro = state.get("macro_intelligence") or {}
        vix_info = macro.get("india_vix") or {}
        vix_val = float(vix_info["value"]) if vix_info.get("value") is not None else None
        vix_change = float(vix_info["change"]) if vix_info.get("change") is not None else None

        # 3. Factor Scoring
        factors: List[FactorScore] = []

        # Factor A: Price Structure (Weight 0.30)
        if change_pct is not None and change is not None:
            p_score = 0.0
            if change_pct > 0.8:
                p_score = 80.0
            elif change_pct > 0.3:
                p_score = 50.0
            elif change_pct > 0.05:
                p_score = 20.0
            elif change_pct < -0.8:
                p_score = -80.0
            elif change_pct < -0.3:
                p_score = -50.0
            elif change_pct < -0.05:
                p_score = -20.0
            else:
                p_score = 0.0

            # Range position boost
            if high_price and low_price and high_price > low_price:
                pos_ratio = (spot - low_price) / (high_price - low_price)
                if pos_ratio > 0.8:
                    p_score += 15.0
                elif pos_ratio < 0.2:
                    p_score -= 15.0

            p_score = max(-100.0, min(100.0, p_score))
            p_dir = "BULLISH" if p_score > 15 else "BEARISH" if p_score < -15 else "NEUTRAL"
            factors.append(FactorScore(
                name="Price Structure", direction=p_dir, score=p_score, weight=0.30, quality="READY",
                description=f"NIFTY spot is {spot:,.2f} ({'+' if change >= 0 else ''}{change:.2f}, {'+' if change_pct >= 0 else ''}{change_pct:.2f}%).",
                evidence_source="Canonical NIFTY Spot Feed"
            ))
        else:
            factors.append(FactorScore(
                name="Price Structure", direction="NEUTRAL", score=0.0, weight=0.30, quality="UNAVAILABLE",
                description=f"NIFTY spot is {spot:,.2f} (session change unavailable).",
                evidence_source="Canonical NIFTY Spot Feed"
            ))

        # Factor B: Market Breadth (Weight 0.25)
        if advances is not None and declines is not None and valid_breadth > 0:
            b_ratio = advances / valid_breadth
            b_score = (b_ratio - 0.5) * 200.0  # 0.5 -> 0, 0.75 -> +50, 0.25 -> -50
            b_score = max(-100.0, min(100.0, b_score))
            b_dir = "BULLISH" if b_score > 15 else "BEARISH" if b_score < -15 else "NEUTRAL"
            factors.append(FactorScore(
                name="Market Breadth", direction=b_dir, score=b_score, weight=0.25, quality="READY",
                description=f"Constituent breadth is {advances} Advances / {declines} Declines ({valid_breadth} observed).",
                evidence_source="NSE NIFTY 50 Constituent Feed"
            ))
        else:
            factors.append(FactorScore(
                name="Market Breadth", direction="NEUTRAL", score=0.0, weight=0.25, quality="UNAVAILABLE",
                description="Constituent breadth observation unavailable.",
                evidence_source="NSE Constituent Feed"
            ))

        # Factor C: Heavyweight Participation (Weight 0.15)
        if hw_total > 0:
            hw_ratio = hw_up / hw_total
            hw_score = (hw_ratio - 0.5) * 200.0
            hw_score = max(-100.0, min(100.0, hw_score))
            hw_dir = "BULLISH" if hw_score > 15 else "BEARISH" if hw_score < -15 else "NEUTRAL"
            factors.append(FactorScore(
                name="Heavyweights", direction=hw_dir, score=hw_score, weight=0.15, quality="READY",
                description=f"{hw_up} of top {hw_total} heavyweights trading positive.",
                evidence_source="NIFTY Heavyweight Basket"
            ))
        else:
            factors.append(FactorScore(
                name="Heavyweights", direction="NEUTRAL", score=0.0, weight=0.15, quality="UNAVAILABLE",
                description="Heavyweight participation metadata unavailable.",
                evidence_source="Heavyweight Basket"
            ))

        # Factor D: Derivatives (Weight 0.15)
        if pcr is not None:
            if pcr > 1.1:
                opt_score = 45.0
            elif pcr > 0.9:
                opt_score = 15.0
            elif pcr < 0.7:
                opt_score = -45.0
            else:
                opt_score = -15.0

            opt_dir = "BULLISH" if opt_score > 15 else "BEARISH" if opt_score < -15 else "NEUTRAL"
            atm_desc = f" with ATM strike {float(atm_strike):.0f}." if (atm_strike is not None and float(atm_strike) > 0) else "."
            factors.append(FactorScore(
                name="Derivatives", direction=opt_dir, score=opt_score, weight=0.15, quality="READY",
                description=f"PCR is {pcr:.2f}{atm_desc}",
                evidence_source="Zerodha Option Chain"
            ))
        else:
            factors.append(FactorScore(
                name="Derivatives", direction="NEUTRAL", score=0.0, weight=0.15, quality="UNAVAILABLE",
                description="Option chain snapshot unavailable.",
                evidence_source="Option Intelligence"
            ))

        # Factor E: Volatility / VIX (Weight 0.15)
        if vix_val is not None and vix_change is not None:
            vix_score = 0.0
            if vix_change > 0.5:
                vix_score = -35.0  # Volatility expansion creates drag/uncertainty
            elif vix_change < -0.5:
                vix_score = 25.0
            vix_dir = "BEARISH" if vix_score < -15 else "BULLISH" if vix_score > 15 else "NEUTRAL"
            factors.append(FactorScore(
                name="Volatility", direction=vix_dir, score=vix_score, weight=0.15, quality="READY",
                description=f"India VIX is {vix_val:.2f} ({'+' if vix_change >= 0 else ''}{vix_change:.2f}).",
                evidence_source="India VIX Feed"
            ))
        else:
            factors.append(FactorScore(
                name="Volatility", direction="NEUTRAL", score=0.0, weight=0.15, quality="UNAVAILABLE",
                description="India VIX observation unavailable.",
                evidence_source="India VIX Feed"
            ))

        # 4. Weighted Trend Score Calculation
        valid_weight = sum(f.weight for f in factors if f.quality == "READY")
        if valid_weight > 0:
            total_weighted_score = sum(f.score * f.weight for f in factors if f.quality == "READY") / valid_weight
        else:
            total_weighted_score = 0.0

        total_weighted_score = round(total_weighted_score, 1)

        # 5. Session Evolution & Transition Check
        history = snapshot_history or []
        evolution = cls._build_session_evolution(history, spot, open_price, high_price, low_price)
        is_flattening = cls._check_momentum_flattening(history, total_weighted_score)

        # 6. Trend Classification
        trend_class = cls._classify_trend(total_weighted_score, is_flattening, factors)

        # 7. Conviction Calculation
        conviction = cls._calculate_conviction(factors, total_weighted_score, valid_weight)

        # 8. Drivers & Contradictions
        primary_driver, supporting_drivers, contradicting_factors = cls._rank_drivers(factors, total_weighted_score)

        # 9. Key Levels & Invalidation
        vwap_val = m_data.get("vwap") or spot
        ref_low = low_price if low_price is not None else spot
        ref_high = high_price if high_price is not None else spot
        sup_levels = m_data.get("support_levels") or ([round(ref_low - 50, 0), round(ref_low - 100, 0)] if ref_low is not None else [])
        res_levels = m_data.get("resistance_levels") or ([round(ref_high + 50, 0), round(ref_high + 100, 0)] if ref_high is not None else [])

        key_levels = {
            "vwap": vwap_val,
            "opening_range_high": high_price,
            "opening_range_low": low_price,
            "immediate_support": sup_levels[0] if sup_levels else low_price,
            "immediate_resistance": res_levels[0] if res_levels else high_price,
        }

        invalidation = cls._build_invalidation_conditions(trend_class, key_levels, spot, advances)

        # 10. Session Statistics
        stats = {
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": spot,
            "spot": spot,
            "previous_close": prev_close,
            "change": change,
            "change_pct": change_pct,
            "range": round(high_price - low_price, 2) if (high_price and low_price) else 0.0,
            "position_in_range_pct": round(((spot - low_price) / (high_price - low_price)) * 100, 1) if (high_price and low_price and high_price > low_price) else 50.0,
            "vwap": vwap_val,
            "advances": advances,
            "declines": declines,
            "india_vix": vix_val,
            "pcr": pcr
        }

        analysis_status = "SESSION_COMPLETE" if is_closed else ("PARTIAL" if valid_weight < 0.8 else "READY")

        return TodayAnalysisReport(
            analysis_timestamp=now_str,
            session_date=session_date,
            market_session_state=sess_status,
            analysis_status=analysis_status,
            trend_classification=trend_class,
            trend_score=total_weighted_score,
            conviction=conviction,
            primary_driver=primary_driver,
            supporting_drivers=supporting_drivers,
            contradicting_factors=contradicting_factors,
            session_statistics=stats,
            session_evolution=evolution,
            key_levels=key_levels,
            invalidation_conditions=invalidation,
            factor_breakdown=[asdict(f) for f in factors],
            data_quality={
                "coverage_pct": round(valid_weight * 100, 0),
                "quality_status": analysis_status,
                "data_loss_pct": round((1.0 - valid_weight) * 100, 0)
            }
        )

    @classmethod
    def _classify_trend(cls, score: float, is_flattening: bool, factors: List[FactorScore]) -> str:
        if score >= 60.0:
            return "STRONG BULLISH"
        elif score >= 30.0:
            return "BULLISH → SIDEWAYS" if is_flattening else "BULLISH"
        elif score >= 15.0:
            return "BULLISH → SIDEWAYS" if is_flattening else "MODERATELY BULLISH"
        elif score <= -60.0:
            return "STRONG BEARISH"
        elif score <= -30.0:
            return "BEARISH → SIDEWAYS" if is_flattening else "BEARISH"
        elif score <= -15.0:
            return "BEARISH → SIDEWAYS" if is_flattening else "MODERATELY BEARISH"

        # For scores between -15 and +15, check if factors strongly diverge
        ready_factors = [f for f in factors if f.quality == "READY"]
        directions = {f.direction for f in ready_factors if f.direction != "NEUTRAL"}
        if "BULLISH" in directions and "BEARISH" in directions:
            return "MIXED / UNCLEAR"

        return "SIDEWAYS / RANGE-BOUND"

    @classmethod
    def _calculate_conviction(cls, factors: List[FactorScore], score: float, valid_weight: float) -> float:
        if valid_weight <= 0:
            return 0.0

        ready_factors = [f for f in factors if f.quality == "READY"]
        if not ready_factors:
            return 0.0

        main_dir = "BULLISH" if score > 15 else "BEARISH" if score < -15 else "NEUTRAL"
        if main_dir == "NEUTRAL":
            agree_count = len([f for f in ready_factors if f.direction == "NEUTRAL"])
        else:
            agree_count = len([f for f in ready_factors if f.direction == main_dir])

        agreement_ratio = agree_count / len(ready_factors)
        base_conviction = (0.5 * agreement_ratio + 0.5 * min(1.0, abs(score) / 60.0)) * 100.0
        # Scale down for missing data coverage
        final_conviction = round(base_conviction * valid_weight, 1)
        return max(10.0, min(95.0, final_conviction))

    @classmethod
    def _rank_drivers(cls, factors: List[FactorScore], overall_score: float) -> tuple[str, List[str], List[str]]:
        ready = [f for f in factors if f.quality == "READY"]
        if not ready:
            return "Insufficient data to determine primary driver", [], []

        main_dir = "BULLISH" if overall_score > 15 else "BEARISH" if overall_score < -15 else "NEUTRAL"

        # Sort factors by magnitude of score * weight
        sorted_factors = sorted(ready, key=lambda f: abs(f.score * f.weight), reverse=True)

        primary = sorted_factors[0].description if sorted_factors else "Balanced session factors"

        supporting = [f.description for f in sorted_factors[1:] if f.direction == main_dir or (main_dir == "NEUTRAL" and abs(f.score) < 20)]
        contradicting = [f.description for f in sorted_factors if (main_dir == "BULLISH" and f.direction == "BEARISH") or (main_dir == "BEARISH" and f.direction == "BULLISH")]

        return primary, supporting, contradicting

    @classmethod
    def _build_session_evolution(cls, history: List[Dict[str, Any]], spot: float, open_price: Optional[float], high_price: Optional[float], low_price: Optional[float]) -> List[Dict[str, Any]]:
        open_str = f"{open_price:,.2f}" if isinstance(open_price, (int, float)) else "session open"
        high_str = f"{high_price:,.2f}" if isinstance(high_price, (int, float)) else "session high"
        low_str = f"{low_price:,.2f}" if isinstance(low_price, (int, float)) else "session low"
        spot_str = f"{spot:,.2f}" if isinstance(spot, (int, float)) else "current price"

        phases = [
            {"time_window": "09:15 – 09:30", "phase_label": "OPENING RANGE", "headline": f"Opened at {open_str} with initial session discovery.", "importance": "MEDIUM"},
            {"time_window": "09:30 – 11:30", "phase_label": "MORNING EXPANSION", "headline": f"Session range expanded between {low_str} and {high_str}.", "importance": "HIGH"},
            {"time_window": "11:30 – NOW", "phase_label": "CURRENT CONSOLIDATION", "headline": f"Trading near {spot_str} with active institutional rebalancing.", "importance": "HIGH"}
        ]
        return phases

    @classmethod
    def _check_momentum_flattening(cls, history: List[Dict[str, Any]], score: float) -> bool:
        if len(history) < 3:
            return False
        # If last 3 snapshots have compressed price range or score change < 5, consider flattening
        return False

    @classmethod
    def _build_invalidation_conditions(cls, trend_class: str, levels: Dict[str, Any], spot: float, advances: Optional[int]) -> Dict[str, Any]:
        sup = levels.get("immediate_support") or round(spot - 50, 0)
        res = levels.get("immediate_resistance") or round(spot + 50, 0)
        adv_threshold = 20 if advances is None else max(15, advances - 10)

        return {
            "view_weakens_if": f"NIFTY loses immediate support at {sup:,.2f} or constituent advances drop below {adv_threshold}.",
            "view_strengthens_if": f"NIFTY clears immediate resistance at {res:,.2f} with sustained buying momentum.",
            "support_threshold": sup,
            "resistance_threshold": res
        }

    @classmethod
    def _build_premarket_report(cls, now_str: str, session_date: str, sess_status: str) -> TodayAnalysisReport:
        return TodayAnalysisReport(
            analysis_timestamp=now_str,
            session_date=session_date,
            market_session_state=sess_status,
            analysis_status="MARKET_NOT_STARTED",
            trend_classification="MIXED / UNCLEAR",
            trend_score=0.0,
            conviction=0.0,
            primary_driver="Market session has not started. Awaiting opening bell and live constituent ticks.",
            supporting_drivers=[],
            contradicting_factors=[],
            session_statistics={},
            session_evolution=[],
            key_levels={},
            invalidation_conditions={"view_weakens_if": "Pre-market session active", "view_strengthens_if": "Live market session opens"},
            factor_breakdown=[],
            data_quality={"quality_status": "MARKET_NOT_STARTED", "coverage_pct": 0.0, "data_loss_pct": 100.0}
        )

    @classmethod
    def _build_insufficient_data_report(cls, now_str: str, session_date: str, sess_status: str, breadth: Optional[Dict[str, Any]] = None) -> TodayAnalysisReport:
        has_partial_breadth = bool(breadth and (breadth.get("advances") is not None or breadth.get("declines") is not None))
        status = "PARTIAL_EVIDENCE" if has_partial_breadth else "INSUFFICIENT_DATA"
        driver = "Partial canonical evidence available: constituent breadth observed, but spot price telemetry unavailable." if has_partial_breadth else "Insufficient canonical market data to evaluate session trend."

        return TodayAnalysisReport(
            analysis_timestamp=now_str,
            session_date=session_date,
            market_session_state=sess_status,
            analysis_status=status,
            trend_classification=status,
            trend_score=0.0,
            conviction=0.0,
            primary_driver=driver,
            supporting_drivers=[],
            contradicting_factors=[],
            session_statistics={
                "spot": None,
                "open": None,
                "high": None,
                "low": None,
                "session_change": None,
                "session_change_pct": None,
                "breadth": breadth if has_partial_breadth else None
            },
            session_evolution=[],
            key_levels={},
            invalidation_conditions={"view_weakens_if": "Data stream restored", "view_strengthens_if": "Data stream restored"},
            factor_breakdown=[],
            data_quality={"quality_status": status, "coverage_pct": 50.0 if has_partial_breadth else 0.0, "data_loss_pct": 50.0 if has_partial_breadth else 100.0}
        )
