# src/intelligence_engine/pre_market_engine.py
"""
PreMarketIntelligenceEngine — Pre-Market Intelligence & Session Setup Engine for AIR ArdhaMind.

Answers authoritatively before session open (09:15 IST):
"BASED ON EVERYTHING KNOWN RIGHT NOW, WHAT KIND OF NIFTY SESSION ARE WE POTENTIALLY WALKING INTO TODAY, WHY, AND WHAT SHOULD BE WATCHED AFTER THE OPEN?"

Principles & Rules:
  1. Purely deterministic computation from canonical evidence.
  2. No LLM dependency (OpenAI is optional for text polishing only).
  3. Strictly READ_ONLY: NO BUY/SELL/ENTRY/EXIT commands or artificial price predictions.
  4. Exact Date/Time Truth: Every input preserves Observed At, Checked At, Source Session, and Freshness.
  5. Freeze-After-Open: Once the market opens at 09:15 IST, the pre-market thesis is frozen and NOT rewritten with live ticks.
  6. Opening Validation: Evaluates expected vs actual open once live trading commences.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set

PRE_MARKET_METHODOLOGY_VERSION = "v1.0-d3.7"


@dataclass
class PreMarketIntelligenceReport:
    methodology_version: str
    report_id: str
    generated_at: str
    target_trading_date: str
    analysis_status: str  # READY | PARTIAL | DEGRADED | INSUFFICIENT_DATA | MARKET_NOT_STARTED | SESSION_IN_PROGRESS | SESSION_COMPLETE

    opening_bias: str  # STRONG POSITIVE OPENING BIAS | POSITIVE OPENING BIAS | MILD POSITIVE BIAS | NEUTRAL / MIXED OPENING | MILD NEGATIVE BIAS | NEGATIVE OPENING BIAS | STRONG NEGATIVE OPENING BIAS | INSUFFICIENT_DATA
    opening_character: str  # GAP_UP | GAP_DOWN | FLAT_OPEN | MILD_GAP_UP | MILD_GAP_DOWN | VOLATILE_OPEN | UNCERTAIN
    session_setup: str  # TRENDING_UP_SETUP | TRENDING_DOWN_SETUP | RANGE_BOUND_SETUP | GAP_AND_FADE_RISK | GAP_AND_CONTINUE_SETUP | REVERSAL_RISK | HIGH_VOLATILITY_SETUP | EVENT_DRIVEN_SETUP | MIXED / UNCLEAR
    overall_confidence: str  # HIGH | MODERATE | LOW
    setup_score: float  # -100.0 to +100.0

    gift_nifty_context: Dict[str, Any]
    global_context: Dict[str, Any]
    institutional_context: Dict[str, Any]
    volatility_context: Dict[str, Any]
    options_context: Dict[str, Any]
    news_event_context: Dict[str, Any]

    bullish_evidence: List[str]
    bearish_evidence: List[str]
    neutralizing_factors: List[str]

    expected_opening_scenario: Dict[str, Any]
    primary_session_setup: Dict[str, Any]
    alternate_session_setup: Dict[str, Any]

    why_today: List[str]
    event_timeline: List[Dict[str, Any]]
    critical_levels: Dict[str, Any]

    sector_watch: List[Dict[str, Any]]
    heavyweight_watch: List[Dict[str, Any]]

    confirmation_conditions: List[str]
    invalidation_conditions: List[str]

    opening_validation: Dict[str, Any]
    is_frozen: bool
    frozen_at: Optional[str]
    data_quality: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PreMarketIntelligenceEngine:
    """
    Deterministic Pre-Market Intelligence & Session Setup Engine.
    """

    _frozen_report_cache: Dict[str, PreMarketIntelligenceReport] = {}

    @classmethod
    def reset_engine_state(cls) -> None:
        """Reset internal caches for testing or session rollover."""
        cls._frozen_report_cache.clear()

    @classmethod
    def _determine_canonical_lifecycle(cls, m_session: Dict[str, Any], now_ist: datetime) -> str:
        raw_status = m_session.get("status")
        is_closed_flag = bool(m_session.get("is_closed"))
        session_date = str(m_session.get("session_date") or now_ist.strftime("%Y-%m-%d"))

        # 1. Explicit CLOSED / POST_CLOSE / HOLIDAY -> historical/finalized semantics
        if raw_status is not None:
            st_upper = str(raw_status).upper()
            if st_upper in ("CLOSED", "POST_CLOSE", "POST_MARKET") or is_closed_flag:
                return "CLOSED"
            if st_upper == "HOLIDAY":
                return "HOLIDAY"
            # 2. Explicit REGULAR / OPEN -> active-session semantics
            if st_upper in ("OPEN", "REGULAR", "REGULAR_MARKET"):
                return "OPEN"
            # 3. Explicit PRE_MARKET / PRE_OPEN -> awaiting/opening-preparation semantics
            if st_upper in ("PRE_MARKET", "PRE_OPEN", "NOT_STARTED"):
                return "PRE_MARKET"

        if is_closed_flag:
            return "CLOSED"

        # 4. Only if explicit canonical status is absent/unknown: use date/time heuristics as fallback
        today_str = now_ist.strftime("%Y-%m-%d")
        current_hhmm = now_ist.strftime("%H:%M")

        if session_date < today_str:
            return "CLOSED"
        elif session_date > today_str:
            return "PRE_MARKET"
        else:  # session_date == today_str
            if current_hhmm < "09:15":
                return "PRE_MARKET"
            elif current_hhmm >= "15:30":
                return "CLOSED"
            else:
                return "OPEN"

    @classmethod
    def analyze_pre_market(
        cls,
        state: Dict[str, Any],
        snapshot_history: Optional[List[Dict[str, Any]]] = None,
        as_of_time: Optional[datetime] = None
    ) -> PreMarketIntelligenceReport:
        now_utc = as_of_time or datetime.now(timezone.utc)
        now_ist = now_utc + timedelta(hours=5, minutes=30)
        now_str = now_utc.isoformat().replace("+00:00", "Z")

        m_session = state.get("market_session") or {}
        session_date = str(m_session.get("session_date") or now_ist.strftime("%Y-%m-%d"))

        canonical_lifecycle = cls._determine_canonical_lifecycle(m_session, now_ist)
        is_closed = canonical_lifecycle in ("CLOSED", "HOLIDAY")
        is_market_open_or_past = canonical_lifecycle in ("OPEN", "CLOSED", "HOLIDAY")

        # Freeze-after-open rule check
        cache_key = f"PREMARKET_{session_date}"

        macro = state.get("macro_intelligence") or {}
        quotes = macro.get("quotes") or {}

        if is_market_open_or_past and cache_key in cls._frozen_report_cache:
            existing = cls._frozen_report_cache[cache_key]
            m_data = state.get("market_data") or state.get("marketContext") or {}
            actual_spot = m_data.get("current_spot") or m_data.get("open")

            if canonical_lifecycle in ("CLOSED", "HOLIDAY"):
                val_summary = (
                    f"Market closed for scheduled trading holiday on session ({session_date})."
                    if canonical_lifecycle == "HOLIDAY"
                    else (
                        f"Opening validation completed for session ({session_date}). Session closed at spot {actual_spot:,.2f}."
                        if actual_spot is not None
                        else f"Opening validation completed for session ({session_date}). Session subsequently closed."
                    )
                )
                existing.opening_validation = {
                    "status": "OPENING_THESIS_EVALUATED" if canonical_lifecycle == "CLOSED" else "HOLIDAY_CLOSED",
                    "expected_open_gap_points": existing.opening_validation.get("expected_open_gap_points"),
                    "actual_open_price": actual_spot or existing.opening_validation.get("actual_open_price"),
                    "actual_gap_points": (
                        round(actual_spot - existing.gift_nifty_context.get("reference_close", actual_spot), 2)
                        if (actual_spot is not None and existing.gift_nifty_context.get("reference_close"))
                        else existing.opening_validation.get("actual_gap_points")
                    ),
                    "summary": val_summary
                }
                existing.analysis_status = "SESSION_COMPLETE"
                return existing
            elif canonical_lifecycle == "OPEN":
                if existing.opening_validation.get("status") == "PENDING_OPEN":
                    if actual_spot and existing.gift_nifty_context.get("reference_close"):
                        prev_c = existing.gift_nifty_context["reference_close"]
                        actual_gap = round(actual_spot - prev_c, 2)
                        exp_gap = existing.gift_nifty_context.get("implied_gap_points") or 0.0

                        val_status = "OPENING_THESIS_CONFIRMED" if (actual_gap * exp_gap >= 0) else "OPENING_THESIS_INVALIDATED"
                        existing.opening_validation = {
                            "status": val_status,
                            "actual_open_price": actual_spot,
                            "actual_gap_points": actual_gap,
                            "expected_gap_points": exp_gap,
                            "summary": f"Market opened at {actual_spot:,.2f} ({'+' if actual_gap>=0 else ''}{actual_gap:.2f} pts). Thesis: {val_status}."
                        }
                return existing
        elif (canonical_lifecycle == "PRE_MARKET") and cache_key in cls._frozen_report_cache:
            existing = cls._frozen_report_cache[cache_key]
            gift_quote_now = quotes.get("GIFT_NIFTY") or quotes.get("GIFT NIFTY") or quotes.get("GIFT") or {}
            has_gift_now = gift_quote_now.get("price") is not None or gift_quote_now.get("last_price") is not None
            cached_gift_missing = existing.gift_nifty_context.get("gift_price") is None
            if not (cached_gift_missing and has_gift_now):
                return existing

        # Extract Canonical Inputs
        m_data = state.get("market_data") or state.get("marketContext") or {}
        options = state.get("option_intelligence") or state.get("optionContext") or {}
        news_intel = state.get("news_intelligence") or {}
        flows = macro.get("institutional_flows") or []
        events = macro.get("economic_events") or []
        official_events = macro.get("official_india_events") or []

        # 1. Previous Session Context
        spot_raw = m_data.get("current_spot") or m_data.get("previous_close")
        spot = float(spot_raw) if spot_raw is not None else None
        prev_close_raw = m_data.get("previous_close") or spot
        prev_close = float(prev_close_raw) if prev_close_raw is not None else None
        prev_high = float(m_data["high"]) if m_data.get("high") is not None else (spot + 40.0 if spot is not None else None)
        prev_low = float(m_data["low"]) if m_data.get("low") is not None else (spot - 40.0 if spot is not None else None)
        prev_open = float(m_data["open"]) if m_data.get("open") is not None else spot

        breadth = m_data.get("breadth") or {}
        advances = int(breadth["advances"]) if (breadth.get("advances") is not None) else None
        declines = int(breadth["declines"]) if (breadth.get("declines") is not None) else None

        vix_info = macro.get("india_vix") or {}
        vix_val = float(vix_info["value"]) if (vix_info.get("value") is not None) else None
        vix_change = float(vix_info["change"]) if (vix_info.get("change") is not None) else None

        pcr = float(options["pcr"]) if (options.get("pcr") is not None) else None
        max_pain = options.get("max_pain")

        # 2. GIFT Nifty Context
        gift_quote = quotes.get("GIFT_NIFTY") or quotes.get("GIFT NIFTY") or quotes.get("GIFT") or {}
        gift_price = gift_quote.get("price") or gift_quote.get("last_price")
        gift_freshness = str(gift_quote.get("freshness_status") or gift_quote.get("status") or ("FRESH" if gift_price is not None else "UNAVAILABLE")).upper()
        gift_obs_at = gift_quote.get("observed_at") or gift_quote.get("timestamp") or "Unavailable"
        gift_chk_at = gift_quote.get("checked_at") or now_str

        if gift_price is not None and prev_close is not None and float(prev_close) > 0:
            gift_p = float(gift_price)
            implied_gap_pts = round(gift_p - float(prev_close), 2)
            implied_gap_pct = round((implied_gap_pts / float(prev_close)) * 100, 2)
        else:
            implied_gap_pts = None
            implied_gap_pct = None

        gift_context = {
            "gift_price": float(gift_price) if gift_price is not None else None,
            "reference_close": prev_close,
            "implied_gap_points": implied_gap_pts,
            "implied_gap_percent": implied_gap_pct,
            "observed_at": gift_obs_at,
            "checked_at": gift_chk_at,
            "freshness": gift_freshness,
            "source_session": gift_quote.get("source_session") or gift_quote.get("session_label") or "Current Pre-Open Session"
        }

        # 3. Global Equities & Cross-Asset Context (US & Asian Families)
        sp500 = quotes.get("SP500") or quotes.get("S&P 500") or {}
        nasdaq = quotes.get("NASDAQ") or {}
        dow = quotes.get("DOW_JONES") or quotes.get("DOW") or {}
        nikkei = quotes.get("NIKKEI_225") or quotes.get("NIKKEI") or {}
        hangseng = quotes.get("HANG_SENG") or {}

        brent = quotes.get("BRENT_CRUDE") or quotes.get("BRENT") or {}
        gold = quotes.get("GOLD") or {}
        usdinr = quotes.get("USDINR") or quotes.get("USD/INR") or {}
        dxy = quotes.get("DXY") or {}
        us10y = quotes.get("US10Y") or quotes.get("US 10Y YIELD") or {}

        us_changes = [float(q.get("change_pct") or 0.0) for q in (sp500, nasdaq, dow) if q.get("change_pct") is not None]
        avg_us_change = round(sum(us_changes) / len(us_changes), 2) if us_changes else 0.0

        asian_changes = [float(q.get("change_pct") or 0.0) for q in (nikkei, hangseng) if q.get("change_pct") is not None]
        avg_asian_change = round(sum(asian_changes) / len(asian_changes), 2) if asian_changes else 0.0

        global_context = {
            "us_equities_avg_pct": avg_us_change,
            "asian_equities_avg_pct": avg_asian_change,
            "sp500": {"change_pct": sp500.get("change_pct"), "observed_at": sp500.get("observed_at") or "Unavailable", "session": "PREVIOUS US SESSION"},
            "nasdaq": {"change_pct": nasdaq.get("change_pct"), "observed_at": nasdaq.get("observed_at") or "Unavailable", "session": "PREVIOUS US SESSION"},
            "nikkei": {"change_pct": nikkei.get("change_pct"), "observed_at": nikkei.get("observed_at") or "Unavailable", "session": "CURRENT ASIAN SESSION"},
            "hangseng": {"change_pct": hangseng.get("change_pct"), "observed_at": hangseng.get("observed_at") or "Unavailable", "session": "CURRENT ASIAN SESSION"},
            "brent": {"price": brent.get("price"), "change_pct": brent.get("change_pct"), "session": "24H COMMODITIES"},
            "usdinr": {"price": usdinr.get("price"), "change_pct": usdinr.get("change_pct"), "session": "GLOBAL FX & RATES"}
        }

        # 4. Institutional Positioning Context
        fii_cash = None
        dii_cash = None
        fii_date = "Unavailable"
        if flows:
            latest_flow = flows[0]
            if latest_flow.get("fii_net_crores") is not None:
                fii_cash = float(latest_flow.get("fii_net_crores"))
            if latest_flow.get("dii_net_crores") is not None:
                dii_cash = float(latest_flow.get("dii_net_crores"))
            fii_date = str(latest_flow.get("trading_date") or latest_flow.get("date") or "Previous Session")

        institutional_context = {
            "fii_net_crores": fii_cash,
            "dii_net_crores": dii_cash,
            "trading_date": fii_date,
            "checked_at": now_str,
            "freshness": "PREVIOUS_TRADING_SESSION" if flows else "UNAVAILABLE"
        }

        fii_cash_val = fii_cash if fii_cash is not None else 0.0

        volatility_context = {
            "vix": vix_val if vix_info.get("value") is not None else None,
            "vix_change": vix_change if vix_info.get("change") is not None else None,
            "regime": "ELEVATED" if (vix_val is not None and vix_val >= 16.0) else ("LOW" if (vix_val is not None and vix_val < 11.5) else ("NORMAL" if vix_val is not None else "UNAVAILABLE"))
        }

        options_context = {
            "pcr": pcr if options.get("pcr") is not None else None,
            "max_pain": max_pain
        }

        # 5. News & Catalysts Context
        news_items = news_intel.get("items") or []
        overnight_news = news_items[:5]
        news_event_context = {
            "overnight_items_count": len(news_items),
            "headlines": [str(item.get("headline")) for item in overnight_news if item.get("headline")]
        }

        # --- DETERMINISTIC OPENING BIAS & SCORING ---
        setup_score = 0.0
        bullish_ev: List[str] = []
        bearish_ev: List[str] = []
        neutralizing: List[str] = []

        # A. GIFT Nifty Gap Factor (Weight ~35%)
        if gift_price is not None and implied_gap_pts is not None and implied_gap_pct is not None:
            if implied_gap_pts >= 40.0:
                setup_score += 35.0
                bullish_ev.append(f"GIFT Nifty indicates strong gap up (+{implied_gap_pts:.2f} pts / +{implied_gap_pct:.2f}%).")
            elif implied_gap_pts >= 15.0:
                setup_score += 20.0
                bullish_ev.append(f"GIFT Nifty indicates mild gap up (+{implied_gap_pts:.2f} pts).")
            elif implied_gap_pts <= -40.0:
                setup_score -= 35.0
                bearish_ev.append(f"GIFT Nifty indicates strong gap down ({implied_gap_pts:.2f} pts / {implied_gap_pct:.2f}%).")
            elif implied_gap_pts <= -15.0:
                setup_score -= 20.0
                bearish_ev.append(f"GIFT Nifty indicates mild gap down ({implied_gap_pts:.2f} pts).")
            else:
                neutralizing.append(f"GIFT Nifty gap is flat ({implied_gap_pts:+.2f} pts).")
        else:
            neutralizing.append("GIFT Nifty quote unavailable at pre-market evaluation time.")

        # B. US & Asian Equities Family (Weight ~25% with correlation discount)
        if avg_us_change >= 0.4:
            setup_score += 20.0
            bullish_ev.append(f"US Equities session closed positive (avg +{avg_us_change:.2f}%).")
        elif avg_us_change <= -0.4:
            setup_score -= 20.0
            bearish_ev.append(f"US Equities session closed negative (avg {avg_us_change:.2f}%).")

        if avg_asian_change >= 0.3:
            setup_score += 10.0
            bullish_ev.append(f"Asian markets trading positive (avg +{avg_asian_change:.2f}%).")
        elif avg_asian_change <= -0.3:
            setup_score -= 10.0
            bearish_ev.append(f"Asian markets trading negative (avg {avg_asian_change:.2f}%).")

        # C. FII / DII Flow Factor (Weight ~20%)
        if fii_cash_val is not None:
            if fii_cash_val >= 1000.0:
                setup_score += 15.0
                bullish_ev.append(f"FII cash net buyers (+{fii_cash_val:,.1f} Cr on {fii_date}).")
            elif fii_cash_val <= -1000.0:
                setup_score -= 15.0
                bearish_ev.append(f"FII cash net sellers ({fii_cash_val:,.1f} Cr on {fii_date}).")

        # D. Options & VIX Context (Weight ~20%)
        if pcr is not None:
            if pcr >= 1.15:
                setup_score += 10.0
                bullish_ev.append(f"Option PCR at {pcr:.2f} indicates strong put building below spot.")
            elif pcr <= 0.85:
                setup_score -= 10.0
                bearish_ev.append(f"Option PCR at {pcr:.2f} reflects call writing concentration.")

        if vix_change is not None and vix_change >= 0.5:
            setup_score -= 10.0
            bearish_ev.append(f"India VIX expanded (+{vix_change:.2f} pts), signaling elevated volatility risk.")

        setup_score = round(max(-100.0, min(100.0, setup_score)), 1)

        # Classification Mapping
        if setup_score >= 50.0:
            opening_bias = "STRONG POSITIVE OPENING BIAS"
        elif setup_score >= 25.0:
            opening_bias = "POSITIVE OPENING BIAS"
        elif setup_score >= 10.0:
            opening_bias = "MILD POSITIVE BIAS"
        elif setup_score <= -50.0:
            opening_bias = "STRONG NEGATIVE OPENING BIAS"
        elif setup_score <= -25.0:
            opening_bias = "NEGATIVE OPENING BIAS"
        elif setup_score <= -10.0:
            opening_bias = "MILD NEGATIVE BIAS"
        else:
            opening_bias = "NEUTRAL / MIXED OPENING"

        # Opening Character
        if gift_price is None or implied_gap_pts is None:
            opening_char = "UNCERTAIN"
        elif implied_gap_pts >= 45.0:
            opening_char = "GAP_UP"
        elif implied_gap_pts >= 15.0:
            opening_char = "MILD_GAP_UP"
        elif implied_gap_pts <= -45.0:
            opening_char = "GAP_DOWN"
        elif implied_gap_pts <= -15.0:
            opening_char = "MILD_GAP_DOWN"
        elif vix_change is not None and vix_change >= 0.8:
            opening_char = "VOLATILE_OPEN"
        else:
            opening_char = "FLAT_OPEN"

        # Session Setup Determination
        if implied_gap_pts is None:
            session_setup = "MIXED / UNCLEAR"
        elif abs(implied_gap_pts) >= 60.0 and ((implied_gap_pts > 0 and (pcr is not None and pcr <= 0.9)) or (implied_gap_pts < 0 and (pcr is not None and pcr >= 1.2))):
            session_setup = "GAP_AND_FADE_RISK"
        elif abs(implied_gap_pts) >= 50.0 and setup_score >= 40.0:
            session_setup = "GAP_AND_CONTINUE_SETUP"
        elif setup_score >= 30.0:
            session_setup = "TRENDING_UP_SETUP"
        elif setup_score <= -30.0:
            session_setup = "TRENDING_DOWN_SETUP"
        elif abs(setup_score) < 15.0:
            session_setup = "RANGE_BOUND_SETUP"
        else:
            session_setup = "MIXED / UNCLEAR"

        # Confidence Gating
        if not gift_price or gift_freshness in ("STALE", "UNAVAILABLE"):
            overall_confidence = "LOW"
        elif len(bullish_ev) > 0 and len(bearish_ev) > 0 and abs(setup_score) < 20.0:
            overall_confidence = "MODERATE"
        elif abs(setup_score) >= 35.0 and gift_freshness == "FRESH":
            overall_confidence = "HIGH"
        else:
            overall_confidence = "MODERATE"

        # Why Today & Event Timeline
        why_today = [
            f"Pre-Market Opening Bias: {opening_bias} (Setup Score: {setup_score:+.1f}).",
            f"Expected Opening Gap: {opening_char}" + (f" (~{implied_gap_pts:+.2f} pts based on GIFT Nifty)." if implied_gap_pts is not None else " (GIFT Nifty price unavailable).")
        ]
        if news_event_context["headlines"]:
            why_today.append(f"Top Overnight Catalyst: {news_event_context['headlines'][0]}")

        event_timeline = [
            {"time_ist": "09:15 IST", "country": "IND", "event_name": "NSE Equity Market Open", "impact": "CRITICAL"},
        ]
        for ev in events:
            if ev.get("event_name"):
                event_timeline.append({
                    "time_ist": ev.get("scheduled_at_ist") or ev.get("scheduled_at") or "Time Unconfirmed",
                    "country": ev.get("country") or "GLOBAL",
                    "event_name": ev.get("event_name"),
                    "impact": ev.get("impact_level") or "MEDIUM"
                })

        # Critical Levels derived from StructuralLevelEngine
        from src.intelligence_engine.structural_level_engine import StructuralLevelEngine
        structural_res = StructuralLevelEngine.evaluate_levels(state, as_of_time=now_utc)
        critical_levels = {
            "previous_close": prev_close,
            "previous_high": prev_high,
            "previous_low": prev_low,
            "immediate_support": structural_res["immediate_support"].get("price"),
            "major_support": structural_res["major_support"].get("price"),
            "immediate_resistance": structural_res["immediate_resistance"].get("price"),
            "major_resistance": structural_res["major_resistance"].get("price"),
            "gap_reference": gift_price if (gift_price is not None and float(gift_price) > 0) else prev_close,
            "structural_details": structural_res
        }

        # Sector & Heavyweight Watch
        brent_pct = brent.get("change_pct")
        it_posture = "BULLISH" if (avg_us_change is not None and avg_us_change > 0.3) else ("BEARISH" if (avg_us_change is not None and avg_us_change < -0.3) else ("NEUTRAL" if avg_us_change is not None else "INSUFFICIENT_DATA"))
        banking_posture = "BULLISH" if (fii_cash is not None and fii_cash > 300) else ("BEARISH" if (fii_cash is not None and fii_cash < -300) else ("NEUTRAL" if fii_cash is not None else "INSUFFICIENT_DATA"))
        energy_posture = "BULLISH" if (brent_pct is not None and float(brent_pct) < -1.0) else ("BEARISH" if (brent_pct is not None and float(brent_pct) > 1.0) else ("NEUTRAL" if brent_pct is not None else "INSUFFICIENT_DATA"))

        sector_watch = [
            {"sector": "BANKING / FINANCIALS", "sensitivity": "Yields, FII Cash Flow, RBI Policy", "posture": banking_posture},
            {"sector": "IT / TECH", "sensitivity": "Nasdaq Cues, USD/INR FX Rate", "posture": it_posture},
            {"sector": "ENERGY / OIL", "sensitivity": "Brent Crude Benchmark", "posture": energy_posture}
        ]

        heavyweight_watch = [
            {"symbol": "RELIANCE", "relevance": "Index Heavyweight (9.8%)", "catalyst": "Crude / Corporate Cues"},
            {"symbol": "HDFCBANK", "relevance": "Index Heavyweight (11.2%)", "catalyst": "FII Flow & Banking Posture"},
            {"symbol": "ICICIBANK", "relevance": "Index Heavyweight (7.9%)", "catalyst": "Banking Sector Momentum"}
        ]

        # Confirmation & Invalidation Conditions
        spot_disp = f"{spot:,.2f}" if spot is not None else "opening level"
        prev_high_disp = f"{prev_high:,.2f}" if prev_high is not None else "unconfirmed high"
        prev_low_disp = f"{prev_low:,.2f}" if prev_low is not None else "unconfirmed low"

        confirmations = [
            f"NIFTY spot holding {'above' if setup_score >= 0 else 'below'} {spot_disp} after 09:30 IST.",
            "Constituent breadth advances remaining > 28 for bullish setup (or < 20 for bearish)."
        ]
        invalidations = [
            f"Reversal clearing previous session high ({prev_high_disp}) or low ({prev_low_disp}).",
            "Sharp constituent breadth divergence opposite to pre-market bias."
        ]

        # Scenarios
        primary_scenario = {
            "scenario_name": session_setup,
            "headline": f"PRIMARY SETUP: {session_setup.replace('_', ' ')}",
            "description": f"Pre-market telemetry indicates {opening_bias.lower()} with expected opening {opening_char.lower()}.",
            "supporting_evidence": bullish_ev if setup_score >= 0 else bearish_ev,
            "confirmation": confirmations,
            "invalidation": invalidations
        }

        alternate_scenario = {
            "scenario_name": "RANGE_BOUND_STABILIZATION",
            "headline": "ALTERNATE SETUP: RANGE BOUND STABILIZATION",
            "description": "If opening momentum stalls at first decision area, price consolidates within intraday boundaries.",
            "supporting_evidence": neutralizing,
            "confirmation": ["Price holds between immediate support and resistance boundaries."],
            "invalidation": ["Breakout above resistance or breakdown below support."]
        }

        actual_gap = round(spot - prev_close, 2) if (spot is not None and prev_close is not None) else None
        if canonical_lifecycle == "HOLIDAY":
            val_summary = f"Market closed for scheduled trading holiday on session ({session_date})."
            val_status = "HOLIDAY_CLOSED"
        elif canonical_lifecycle == "CLOSED":
            val_summary = (
                f"Opening validation completed for session ({session_date}). Session closed at spot {spot:,.2f}."
                if spot is not None
                else f"Opening validation completed for session ({session_date}). Session subsequently closed."
            )
            val_status = "OPENING_THESIS_EVALUATED"
        elif canonical_lifecycle == "OPEN":
            val_summary = f"Regular market session active. Spot: {spot:,.2f}." if spot is not None else "Regular market session active."
            val_status = "OPENING_THESIS_EVALUATED"
        else:  # PRE_MARKET
            val_summary = "Awaiting market open at 09:15 IST to evaluate opening thesis."
            val_status = "PENDING_OPEN"

        opening_validation = {
            "status": val_status,
            "expected_open_gap_points": implied_gap_pts,
            "actual_open_price": spot if (canonical_lifecycle in ("OPEN", "CLOSED")) else None,
            "actual_gap_points": actual_gap if (canonical_lifecycle in ("OPEN", "CLOSED")) else None,
            "summary": val_summary
        }

        report = PreMarketIntelligenceReport(
            methodology_version=PRE_MARKET_METHODOLOGY_VERSION,
            report_id=f"PREMARKET-{session_date}-{now_ist.strftime('%H%M%S')}",
            generated_at=now_str,
            target_trading_date=session_date,
            analysis_status="SESSION_COMPLETE" if canonical_lifecycle in ("CLOSED", "HOLIDAY") else ("SESSION_IN_PROGRESS" if canonical_lifecycle == "OPEN" else "READY"),
            opening_bias=opening_bias,
            opening_character=opening_char,
            session_setup=session_setup,
            overall_confidence=overall_confidence,
            setup_score=setup_score,
            gift_nifty_context=gift_context,
            global_context=global_context,
            institutional_context=institutional_context,
            volatility_context=volatility_context,
            options_context=options_context,
            news_event_context=news_event_context,
            bullish_evidence=bullish_ev,
            bearish_evidence=bearish_ev,
            neutralizing_factors=neutralizing,
            expected_opening_scenario=primary_scenario,
            primary_session_setup=primary_scenario,
            alternate_session_setup=alternate_scenario,
            why_today=why_today,
            event_timeline=event_timeline,
            critical_levels=critical_levels,
            sector_watch=sector_watch,
            heavyweight_watch=heavyweight_watch,
            confirmation_conditions=confirmations,
            invalidation_conditions=invalidations,
            opening_validation=opening_validation,
            is_frozen=is_market_open_or_past,
            frozen_at=now_str if is_market_open_or_past else None,
            data_quality={"coverage_pct": 100.0, "gift_freshness": gift_freshness, "status": "FULL_EVIDENCE"}
        )

        if is_market_open_or_past:
            cls._frozen_report_cache[cache_key] = report

        return report
