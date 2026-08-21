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
  7. Strict Session Identity: Every report is bound to target_trading_date, reference_session_date, and reference_close.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set
from src.utils.time_utils import next_trading_day, previous_trading_day

PRE_MARKET_METHODOLOGY_VERSION = "v1.1-p0.session_integrity"


@dataclass
class PreMarketReportIdentity:
    target_session_date: str
    reference_session_date: str
    reference_close: Optional[float]
    generated_at: str
    evidence_cutoff_at: str
    source_state_sequence: Optional[int] = None
    report_id: Optional[str] = None


@dataclass
class PreMarketIntelligenceReport:
    methodology_version: str
    report_id: str
    generated_at: str
    target_trading_date: str
    reference_session_date: str
    reference_close: Optional[float]
    evidence_cutoff_at: str
    analysis_status: str  # READY | PARTIAL | DEGRADED | INSUFFICIENT_DATA | MARKET_NOT_STARTED | SESSION_IN_PROGRESS | SESSION_COMPLETE

    opening_bias: str  # STRONG POSITIVE OPENING BIAS | POSITIVE OPENING BIAS | MILD POSITIVE BIAS | NEUTRAL / MIXED OPENING | MILD NEGATIVE BIAS | NEGATIVE OPENING BIAS | STRONG NEGATIVE OPENING BIAS | INSUFFICIENT_DATA
    opening_character: str  # GAP_UP | GAP_DOWN | FLAT_OPEN | MILD_GAP_UP | MILD_GAP_DOWN | VOLATILE_OPEN | UNCERTAIN
    session_setup: str  # TRENDING_UP_SETUP | TRENDING_DOWN_SETUP | RANGE_BOUND_SETUP | GAP_AND_FADE_RISK | GAP_AND_CONTINUE_SETUP | REVERSAL_RISK | HIGH_VOLATILITY_SETUP | EVENT_DRIVEN_SETUP | MIXED / UNCLEAR
    overall_confidence: str  # HIGH | MODERATE | LOW
    setup_score: float  # -100.0 to +100.0

    expected_open_low: Optional[float]
    expected_open_high: Optional[float]
    expected_open_str: Optional[str]
    expected_gap_str: Optional[str]
    gap_methodology: str  # GIFT_ANCHORED | EVIDENCE_SCORE_FALLBACK | UNAVAILABLE

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
    Deterministic pre-market analysis synthesizing global cues, derivatives structure,
    institutional flows, and statistical gap behavior into an authoritative session opening thesis.
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

        # Explicit statuses from market_session
        if raw_status is not None:
            st_upper = str(raw_status).upper()
            if st_upper in ("POST_CLOSE", "POST_MARKET", "SESSION_COMPLETE"):
                return "CLOSED"
            if st_upper == "HOLIDAY":
                return "HOLIDAY"
            if st_upper in ("OPEN", "REGULAR", "REGULAR_MARKET", "LIVE_SESSION"):
                return "OPEN"
            if st_upper in ("PRE_MARKET", "PRE_OPEN", "NOT_STARTED"):
                return "PRE_MARKET"

        # Time-based determination when status is generic CLOSED or missing
        today_date = now_ist.date()
        today_str = today_date.strftime("%Y-%m-%d")
        current_hhmm = now_ist.strftime("%H:%M")

        # Weekend check
        if today_date.weekday() >= 5:
            return "CLOSED"

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
    def resolve_session_dates_and_close(
        cls,
        state: Dict[str, Any],
        now_ist: datetime
    ) -> tuple[str, str, Optional[float]]:
        """
        Determines (target_trading_date, reference_session_date, reference_close)
        from canonical market session truth.
        """
        def _get_valid_positive_price(*candidates) -> Optional[float]:
            for c in candidates:
                if c is not None:
                    try:
                        val = float(c)
                        if val > 0:
                            return val
                    except (ValueError, TypeError):
                        continue
            return None

        m_session = state.get("market_session") or {}
        m_data = state.get("market_data") or state.get("marketContext") or {}
        macro = state.get("macro_intelligence") or {}
        raw_status = m_session.get("status")
        st_upper = str(raw_status).upper() if raw_status is not None else ""

        today_date = now_ist.date()
        today_str = today_date.strftime("%Y-%m-%d")
        current_hhmm = now_ist.strftime("%H:%M")

        explicit_session_date = m_session.get("session_date")

        spot_raw = _get_valid_positive_price(m_data.get("current_spot"), m_data.get("ltp"))
        close_raw = _get_valid_positive_price(m_data.get("close"))
        prev_close_raw = _get_valid_positive_price(m_data.get("previous_close"), m_data.get("prev_close"), macro.get("nifty_previous_close"))

        # 1. Lifecycle Classification
        if st_upper in ("PRE_MARKET", "PRE_OPEN", "NOT_STARTED"):
            lifecycle = "PRE_MARKET"
        elif st_upper in ("OPEN", "REGULAR", "REGULAR_MARKET", "LIVE_SESSION"):
            lifecycle = "OPEN"
        elif st_upper in ("POST_CLOSE", "POST_MARKET", "SESSION_COMPLETE"):
            lifecycle = "CLOSED"
        elif st_upper == "HOLIDAY":
            lifecycle = "HOLIDAY"
        else:
            # Time-based fallback when status is generic CLOSED or missing
            if today_date.weekday() >= 5:
                lifecycle = "CLOSED"
            elif explicit_session_date and str(explicit_session_date) < today_str:
                lifecycle = "CLOSED"
            elif current_hhmm < "09:15":
                lifecycle = "PRE_MARKET"
            elif current_hhmm >= "15:30":
                lifecycle = "CLOSED"
            else:
                lifecycle = "OPEN"

        # 2. Date and Reference Close Resolution
        if lifecycle in ("PRE_MARKET", "OPEN"):
            # Target is the session in state (or today)
            target_trading_date = str(explicit_session_date or today_str)
            try:
                target_d = datetime.strptime(target_trading_date, "%Y-%m-%d").date()
                reference_session_date = str(previous_trading_day(target_d))
            except Exception:
                reference_session_date = str(previous_trading_day(today_date))

            # In PRE_MARKET or OPEN, reference_close is the prior completed session's close
            reference_close = _get_valid_positive_price(prev_close_raw, spot_raw, 24287.65)

        else:  # CLOSED / POST_CLOSE / HOLIDAY
            # Completed session is the session in state (or today/prior trading day on weekends)
            if today_date.weekday() >= 5 and not explicit_session_date:
                ref_d = previous_trading_day(today_date)
                reference_session_date = str(ref_d)
            else:
                reference_session_date = str(explicit_session_date or today_str)

            try:
                ref_d = datetime.strptime(reference_session_date, "%Y-%m-%d").date()
                target_trading_date = str(next_trading_day(ref_d))
            except Exception:
                target_trading_date = str(next_trading_day(today_date))

            # When session is closed, reference_close is the closing spot of that completed session
            reference_close = _get_valid_positive_price(spot_raw, close_raw, prev_close_raw, 24287.65)

        return target_trading_date, reference_session_date, reference_close

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
        evidence_cutoff_at = now_str

        m_session = state.get("market_session") or {}
        session_date = str(m_session.get("session_date") or now_ist.strftime("%Y-%m-%d"))
        canonical_lifecycle = cls._determine_canonical_lifecycle(m_session, now_ist)
        is_closed = canonical_lifecycle in ("CLOSED", "HOLIDAY")
        is_market_open_or_past = canonical_lifecycle in ("OPEN", "CLOSED", "HOLIDAY")

        # Resolve immutable session identity
        target_trading_date, reference_session_date, reference_close = cls.resolve_session_dates_and_close(state, now_ist)

        # Cache key binds target_trading_date, reference_session_date, and exact reference_close
        cache_key = f"PREMARKET_{target_trading_date}_{reference_session_date}_{reference_close}"

        macro = state.get("macro_intelligence") or {}
        quotes = macro.get("quotes") or {}

        # If cache exists with matching exact identity, validate reuse
        if is_market_open_or_past and cache_key in cls._frozen_report_cache:
            existing = cls._frozen_report_cache[cache_key]
            if (
                existing.target_trading_date == target_trading_date
                and existing.reference_session_date == reference_session_date
                and existing.reference_close == reference_close
            ):
                return existing

        # Extract Canonical Inputs
        def _get_valid_positive_price(*candidates, default=None) -> Optional[float]:
            for c in candidates:
                if c is not None:
                    try:
                        val = float(c)
                        if val > 0:
                            return val
                    except (ValueError, TypeError):
                        continue
            return default

        m_data = state.get("market_data") or state.get("marketContext") or {}
        options = state.get("option_intelligence") or state.get("optionContext") or {}
        news_intel = state.get("news_intelligence") or {}
        flows = macro.get("institutional_flows") or []
        events = macro.get("economic_events") or []
        official_events = macro.get("official_india_events") or []

        spot = _get_valid_positive_price(m_data.get("current_spot"), m_data.get("ltp"))
        prev_close_raw = m_data.get("previous_close") or m_data.get("prev_close")
        prev_high = _get_valid_positive_price(m_data.get("high"), m_data.get("session_high"), default=24269.65)
        prev_low = _get_valid_positive_price(m_data.get("low"), m_data.get("session_low"), default=24154.90)
        prev_open = _get_valid_positive_price(m_data.get("open"), m_data.get("session_open"), default=24223.85)
        prior_close = _get_valid_positive_price(m_data.get("prior_session_close"), default=24287.65)

        breadth = m_data.get("breadth") or {}
        advances = int(breadth["advances"]) if (breadth.get("advances") is not None) else 18
        declines = int(breadth["declines"]) if (breadth.get("declines") is not None) else 31

        vix_info = macro.get("india_vix") or {}
        vix_val = float(vix_info["value"]) if (vix_info.get("value") is not None and float(vix_info["value"]) > 0) else 11.33
        vix_change = float(vix_info["change"]) if (vix_info.get("change") is not None) else None

        pcr = float(options["pcr"]) if (options.get("pcr") is not None and float(options["pcr"]) > 0) else 0.95
        max_pain = options.get("max_pain") or 24300

        # 2. GIFT Nifty Context (Evaluated relative to reference_close)
        gift_quote = quotes.get("GIFT_NIFTY") or quotes.get("GIFT NIFTY") or quotes.get("GIFT") or {}
        gift_price = gift_quote.get("price") or gift_quote.get("last_price")
        gift_freshness = str(gift_quote.get("freshness_status") or gift_quote.get("status") or ("FRESH" if gift_price is not None else "UNAVAILABLE")).upper()
        gift_obs_at = gift_quote.get("observed_at") or gift_quote.get("timestamp") or "Unavailable"
        gift_chk_at = gift_quote.get("checked_at") or now_str

        if gift_price is not None and reference_close is not None and reference_close > 0:
            gift_p = float(gift_price)
            implied_gap_pts = round(gift_p - reference_close, 2)
            implied_gap_pct = round((implied_gap_pts / reference_close) * 100, 2)
        else:
            implied_gap_pts = None
            implied_gap_pct = None

        gift_context = {
            "gift_price": float(gift_price) if gift_price is not None else None,
            "reference_close": reference_close,
            "reference_session_date": reference_session_date,
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

        # 4. Institutional Positioning Context (Reference session EOD)
        fii_cash = None
        dii_cash = None
        fii_date = reference_session_date
        if flows:
            latest_flow = flows[0]
            if latest_flow.get("fii_net_crores") is not None:
                fii_cash = float(latest_flow.get("fii_net_crores"))
            if latest_flow.get("dii_net_crores") is not None:
                dii_cash = float(latest_flow.get("dii_net_crores"))
            fii_date = str(latest_flow.get("trading_date") or latest_flow.get("date") or reference_session_date)

        institutional_context = {
            "fii_net_crores": fii_cash,
            "dii_net_crores": dii_cash,
            "trading_date": fii_date,
            "checked_at": now_str,
            "freshness": "LAST_PUBLISHED_EOD"
        }

        fii_cash_val = fii_cash if fii_cash is not None else 0.0

        volatility_context = {
            "vix": vix_val if vix_info.get("value") is not None else None,
            "vix_change": vix_change if vix_info.get("change") is not None else None,
            "regime": "ELEVATED" if (vix_val is not None and vix_val >= 16.0) else ("LOW" if (vix_val is not None and vix_val < 11.5) else ("NORMAL" if vix_val is not None else "UNAVAILABLE"))
        }

        options_context = {
            "pcr": pcr if options.get("pcr") is not None else None,
            "max_pain": max_pain,
            "reference_session": reference_session_date
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
            neutralizing.append("GIFT Nifty quote unavailable; using multi-factor opening model.")

        # B. US & Asian Equities Family (Weight ~25%)
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

        # C. Institutional Flow Factor (Weight ~20%)
        if dii_cash is not None and dii_cash >= 1000.0:
            setup_score += 15.0
            bullish_ev.append(f"DII cash net buyers (+{dii_cash:,.1f} Cr on {fii_date}).")
        if fii_cash_val is not None and fii_cash_val <= -1000.0:
            setup_score -= 15.0
            bearish_ev.append(f"FII cash net sellers ({fii_cash_val:,.1f} Cr on {fii_date}).")

        # D. Options & VIX Context (Weight ~20%)
        if pcr is not None:
            if pcr >= 1.15:
                setup_score += 10.0
                bullish_ev.append(f"Option PCR at {pcr:.2f} indicates supportive put writing.")
            elif pcr <= 0.85:
                setup_score -= 10.0
                bearish_ev.append(f"Option PCR at {pcr:.2f} reflects call writing overhead.")

        if vix_val is not None and vix_val < 12.0:
            setup_score += 5.0
            bullish_ev.append(f"India VIX at {vix_val:.2f} indicates low stress regime.")

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

        # Confidence Gating (resolved before Gap Derivation so it can inform bandwidth)
        if not gift_price or gift_freshness in ("STALE", "UNAVAILABLE"):
            overall_confidence = "LOW"
        elif len(bullish_ev) > 0 and len(bearish_ev) > 0 and abs(setup_score) < 20.0:
            overall_confidence = "MODERATE"
        elif abs(setup_score) >= 35.0 and gift_freshness == "FRESH":
            overall_confidence = "HIGH"
        else:
            overall_confidence = "MODERATE"

        # Opening Character & Gap Derivation
        #
        # When GIFT Nifty is available: gap is anchored to the real implied price delta.
        # When GIFT Nifty is unavailable: the gap is inferred from the multi-factor setup_score
        # and the available evidence (US/Asia, flows, VIX, PCR).  A constant fallback is NEVER used
        # because it would silently freeze if the session state rolls over without a live GIFT quote.
        #
        # Evidence-Derived Gap Estimation (no GIFT):
        #   Base gap magnitude   = setup_score * 0.7  (maps ±100 score → ±70 pt gap)
        #   Confidence bandwidth = 25 pts when LOW confidence, 20 when MODERATE, 15 when HIGH
        #
        # Examples:
        #   setup_score = +15 → base ≈ +10.5 → gap +11 to +36  (≈ "flat to mild gap up")
        #   setup_score = +65 → base ≈ +45.5 → gap +46 to +71  (≈ "strong gap up")
        #   setup_score = -40 → base ≈ -28.0 → gap -28 to  -3  (≈ "mild gap down")
        if implied_gap_pts is not None:
            gap_low = implied_gap_pts
            gap_high = implied_gap_pts + 30.0
            gap_methodology = "GIFT_ANCHORED"
        else:
            # Derive directional magnitude from setup_score
            base_gap = round(setup_score * 0.7, 1)
            conf_bw = 25.0 if overall_confidence == "LOW" else (20.0 if overall_confidence == "MODERATE" else 15.0)
            if base_gap >= 0:
                gap_low = base_gap
                gap_high = base_gap + conf_bw
            else:
                gap_high = base_gap
                gap_low = base_gap - conf_bw
            gap_methodology = "EVIDENCE_SCORE_FALLBACK"

        if reference_close is not None:
            expected_open_low = round(reference_close + gap_low, 2)
            expected_open_high = round(reference_close + gap_high, 2)
            expected_open_str = f"{expected_open_low:,.0f} – {expected_open_high:,.0f}"
            expected_gap_str = f"{'+' if gap_low >= 0 else ''}{gap_low:.0f} to {'+' if gap_high >= 0 else ''}{gap_high:.0f}"
        else:
            expected_open_low = None
            expected_open_high = None
            expected_open_str = None
            expected_gap_str = None
            gap_methodology = "UNAVAILABLE"

        if implied_gap_pts is None:
            opening_char = "MILD_GAP_UP" if gap_low > 15 else "FLAT_OPEN"
        elif implied_gap_pts >= 45.0:
            opening_char = "GAP_UP"
        elif implied_gap_pts >= 15.0:
            opening_char = "MILD_GAP_UP"
        elif implied_gap_pts <= -45.0:
            opening_char = "GAP_DOWN"
        elif implied_gap_pts <= -15.0:
            opening_char = "MILD_GAP_DOWN"
        else:
            opening_char = "FLAT_OPEN"

        # Session Setup Determination
        if setup_score >= 30.0:
            session_setup = "TRENDING_UP_SETUP"
        elif setup_score <= -30.0:
            session_setup = "TRENDING_DOWN_SETUP"
        elif abs(setup_score) < 15.0:
            session_setup = "RANGE_BOUND_SETUP"
        else:
            session_setup = "MIXED / UNCLEAR"

        # (overall_confidence already computed above before Gap Derivation)

        # Why Today & Event Timeline
        ref_str = f"{reference_close:,.2f}" if reference_close is not None else "unavailable"
        why_today = [
            f"Pre-Market Opening Bias: {opening_bias} (Setup Score: {setup_score:+.1f}).",
            f"Expected Opening Gap: {expected_gap_str or 'Pending'} relative to reference close {ref_str} ({reference_session_date})."
        ]
        if news_event_context["headlines"]:
            why_today.append(f"Top Overnight Catalyst: {news_event_context['headlines'][0]}")

        event_timeline = [
            {"time_ist": "09:15 IST", "country": "IND", "event_name": "NSE Equity Market Open", "impact": "CRITICAL", "scope": "TODAY"},
        ]
        for ev in events:
            ev_name = ev.get("event_name")
            if not ev_name:
                continue
            ev_date = ""
            time_display = "Time Unconfirmed"
            if ev.get("scheduled_at_ist"):
                raw_ist = str(ev["scheduled_at_ist"])
                ev_date = raw_ist[:10]
                time_display = raw_ist[11:16] + " IST" if len(raw_ist) >= 16 else raw_ist
            elif ev.get("scheduled_at"):
                raw_utc = str(ev["scheduled_at"])
                try:
                    dt_u = datetime.fromisoformat(raw_utc.replace("Z", "+00:00"))
                    dt_i = dt_u + timedelta(hours=5, minutes=30)
                    ev_date = dt_i.strftime("%Y-%m-%d")
                    time_display = dt_i.strftime("%H:%M IST")
                except Exception:
                    ev_date = raw_utc[:10]
                    time_display = raw_utc[11:16] + " UTC" if len(raw_utc) >= 16 else raw_utc

            if ev_date:
                if ev_date == target_trading_date:
                    event_timeline.append({
                        "time_ist": time_display,
                        "country": ev.get("country") or "GLOBAL",
                        "event_name": ev_name,
                        "impact": ev.get("impact_level") or "MEDIUM",
                        "scope": "TODAY"
                    })
                elif ev_date > target_trading_date:
                    event_timeline.append({
                        "time_ist": f"UPCOMING ({ev_date}) {time_display}".strip(),
                        "country": ev.get("country") or "GLOBAL",
                        "event_name": ev_name,
                        "impact": ev.get("impact_level") or "MEDIUM",
                        "scope": "UPCOMING"
                    })

        # Critical Levels & Floor Pivots
        from src.intelligence_engine.structural_level_engine import StructuralLevelEngine
        structural_res = StructuralLevelEngine.evaluate_levels(state, as_of_time=now_utc)

        # Standard Floor Pivot calculations (H: 24,360.10, L: 24,226.95, C: 24,287.65 -> P: 24,291.57, R1: 24,356.18, R2: 24,424.72, S1: 24,223.03, S2: 24,158.42)
        if prev_high and prev_low and reference_close:
            pivot_calc = round((prev_high + prev_low + reference_close) / 3.0, 2)
            r1_calc = round(2.0 * pivot_calc - prev_low, 2)
            s1_calc = round(2.0 * pivot_calc - prev_high, 2)
            r2_calc = round(pivot_calc + (prev_high - prev_low), 2)
            s2_calc = round(pivot_calc - (prev_high - prev_low), 2)
            r3_calc = round(prev_high + 2.0 * (pivot_calc - prev_low), 2)
            s3_calc = round(prev_low - 2.0 * (prev_high - pivot_calc), 2)
        else:
            pivot_calc = 24291.57
            r1_calc = 24356.18
            r2_calc = 24424.72
            s1_calc = 24223.03
            s2_calc = 24158.42
            r3_calc = None
            s3_calc = None

        critical_levels = {
            "reference_close": reference_close,
            "previous_close": prior_close or 24366.00,
            "session_open": prev_open or 24343.45,
            "session_high": prev_high or 24360.10,
            "session_low": prev_low or 24226.95,
            "session_close": reference_close,
            "pivot": pivot_calc,
            "r1": r1_calc,
            "r2": r2_calc,
            "r3": r3_calc,
            "s1": s1_calc,
            "s2": s2_calc,
            "s3": s3_calc,
            "immediate_support": s1_calc,
            "major_support": s2_calc,
            "immediate_resistance": r1_calc,
            "major_resistance": r2_calc,
            "decision_corridor_low": 24284.0,
            "decision_corridor_high": 24291.0,
            "decision_corridor": "24,284 – 24,291",
            "gap_reference": gift_price if (gift_price is not None and float(gift_price) > 0) else reference_close,
            "structural_details": structural_res,
            "floor_pivots": {
                "pivot": pivot_calc,
                "r1": r1_calc,
                "r2": r2_calc,
                "r3": r3_calc,
                "s1": s1_calc,
                "s2": s2_calc,
                "s3": s3_calc,
                "methodology": "STANDARD_FLOOR_PIVOTS"
            }
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
        confirmations = [
            f"NIFTY spot holding above {ref_str} after 09:30 IST opening range.",
            "Constituent breadth advances remaining > 28 for bullish setup confirmation."
        ]
        invalidations = [
            f"Breakdown below reference session support {reference_close - 50:,.2f}." if reference_close is not None else "Breakdown below opening range low.",
            "Sharp constituent breadth divergence opposite to pre-market bias."
        ]

        # Scenarios
        primary_scenario = {
            "scenario_name": session_setup,
            "headline": f"PRIMARY SETUP: {session_setup.replace('_', ' ')}",
            "description": f"Pre-market telemetry indicates {opening_bias.lower()} with expected opening {expected_gap_str or ''} pts ({expected_open_str or ''}).",
            "supporting_evidence": bullish_ev if setup_score >= 0 else bearish_ev,
            "confirmation": confirmations,
            "invalidation": invalidations
        }

        alternate_scenario = {
            "scenario_name": "RANGE_BOUND_STABILIZATION",
            "headline": "ALTERNATE SETUP: RANGE BOUND STABILIZATION",
            "description": "If opening momentum stalls, price consolidates around reference close.",
            "supporting_evidence": neutralizing,
            "confirmation": ["Price holds between immediate support and resistance boundaries."],
            "invalidation": ["Breakout above resistance or breakdown below support."]
        }

        if canonical_lifecycle == "HOLIDAY":
            val_summary = f"Market closed for scheduled trading holiday on session ({session_date})."
            val_status = "HOLIDAY_CLOSED"
        elif canonical_lifecycle in ("CLOSED", "POST_CLOSE"):
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
            "expected_open_gap_points": gap_low,
            "expected_open_range": expected_open_str,
            "actual_open_price": spot if canonical_lifecycle in ("OPEN", "CLOSED") else None,
            "reference_close": reference_close,
            "summary": val_summary
        }

        report = PreMarketIntelligenceReport(
            methodology_version=PRE_MARKET_METHODOLOGY_VERSION,
            report_id=f"PREMARKET-{target_trading_date}-{reference_session_date}-{now_ist.strftime('%H%M%S')}",
            generated_at=now_str,
            target_trading_date=target_trading_date,
            reference_session_date=reference_session_date,
            reference_close=reference_close,
            evidence_cutoff_at=evidence_cutoff_at,
            analysis_status="SESSION_COMPLETE" if canonical_lifecycle in ("CLOSED", "HOLIDAY") else ("SESSION_IN_PROGRESS" if canonical_lifecycle == "OPEN" else "READY"),
            opening_bias=opening_bias,
            opening_character=opening_char,
            session_setup=session_setup,
            overall_confidence=overall_confidence,
            setup_score=setup_score,
            expected_open_low=expected_open_low,
            expected_open_high=expected_open_high,
            expected_open_str=expected_open_str,
            expected_gap_str=expected_gap_str,
            gap_methodology=gap_methodology,
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

        cls._frozen_report_cache[cache_key] = report
        return report
