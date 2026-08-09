from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class UnifiedNiftyIntelligenceBuilder:
    """Pure, inexpensive synthesis over already-canonical observations.

    Rules are intentionally categorical.  No provider is called here and no
    numeric confidence is manufactured from signal counts.
    """

    BREADTH_MIN_COVERAGE = 40
    LIVE_FRESHNESS = {"fresh", "current", "live", "intraday"}
    CLOSED_FRESHNESS = LIVE_FRESHNESS | {"recent", "last_valid_session", "market_closed"}
    POSITIVE = {"BULLISH", "POSITIVE", "STRONG_POSITIVE", "RISK_ON"}
    NEGATIVE = {"BEARISH", "NEGATIVE", "STRONG_NEGATIVE", "RISK_OFF"}

    @classmethod
    def build(cls, *, market: dict[str, Any], technical: dict[str, Any], options: dict[str, Any],
              macro: dict[str, Any], news: dict[str, Any], market_state: str,
              market_meta: dict[str, Any] | None = None, option_meta: dict[str, Any] | None = None,
              now: datetime | None = None) -> dict[str, Any]:
        session = cls._session(market_state)
        current = now or datetime.now(timezone.utc)
        signals = {
            "price": cls._price(market, technical, session, market_meta or {}),
            "opening": cls._opening(macro, session),
            "global": cls._global(macro, session),
            "institutional": cls._institutional(macro),
            "breadth": cls._breadth(market, session),
            "options": cls._options(options, session, option_meta or {}),
            "volatility": cls._volatility(market, options, macro, session),
            "news": cls._news(news),
            "events": cls._events(macro, current),
        }
        eligible = [name for name, signal in signals.items() if signal["eligible"]]
        ineligible = [name for name, signal in signals.items() if not signal["eligible"]]
        alignment = cls._alignment(signals, session)
        levels = cls._levels(market, technical, options)
        regime = cls._regime(market, technical, signals)
        risk = cls._risk(signals, alignment)
        confidence = cls._confidence(signals, alignment, session)
        scenarios = cls._scenarios(signals, levels, session)
        invalidations = cls._invalidations(alignment, signals, levels)
        explanation = cls._explanation(session, alignment, signals, regime, risk)
        outlook = cls._outlook(session, alignment, confidence, risk, signals, scenarios, levels, current)
        readiness = "READY" if confidence == "HIGH" else "PARTIAL" if eligible else "BLOCKED"
        mode = {"PRE_OPEN": "PRE_MARKET_INTELLIGENCE", "MARKET_OPEN": "LIVE_MARKET_INTELLIGENCE",
                "POST_CLOSE": "SESSION_REVIEW"}.get(session, "NEXT_SESSION_CONTEXT")
        return {
            "schema_version": "1.0.0", "engine": "UNIFIED_NIFTY_INTELLIGENCE_V1",
            "session": session, "mode": mode, "readiness": readiness,
            "input_contract": {"canonical_only": True, "external_fetches": 0,
                               "eligible_signals": eligible, "ineligible_signals": ineligible},
            "signals": signals, "alignment": alignment["state"],
            "confirming_signals": alignment["confirming"], "opposing_signals": alignment["opposing"],
            "neutral_signals": alignment["neutral"], "unavailable_or_ineligible_signals": ineligible,
            "market_regime": regime, "key_levels": levels, "scenarios": scenarios,
            "invalidation_conditions": invalidations, "risk": risk, "confidence": confidence,
            "outlook": outlook,
            "premarket_view_validation": {
                "status": "PENDING",
                "reason": "No prior pre-market synthesis snapshot is retained in current session state."
            },
            "change_intelligence": {"status": "UNAVAILABLE", "transitions": [],
                                    "reason": "No prior canonical synthesis snapshot is available in this refresh."},
            "evidence_completeness": {"state": confidence, "eligible": len(eligible),
                                      "total": len(signals), "critical_missing": cls._critical_missing(signals, session)},
            "explanation": explanation, "human_decision_required": True,
            "execution_authorized": False, "synthetic_inputs": [],
        }

    @staticmethod
    def _session(value: str) -> str:
        state = str(value or "").upper()
        if state in {"PRE_OPEN", "PRE_MARKET"}: return "PRE_OPEN"
        if state in {"MARKET_OPEN", "OPEN", "LIVE"}: return "MARKET_OPEN"
        if state in {"WEEKEND"}: return "WEEKEND"
        if state in {"HOLIDAY", "TRADING_HOLIDAY"}: return "HOLIDAY"
        return "POST_CLOSE"

    @classmethod
    def _signal(cls, state: str, evidence: list[str], *, source: str, observed_at: Any = None,
                freshness: str = "unavailable", eligible: bool = True, reason: str | None = None) -> dict[str, Any]:
        return {"state": state, "eligible": eligible, "evidence": evidence, "source": source,
                "observed_at": observed_at, "freshness": freshness, "ineligibility_reason": reason}

    @classmethod
    def _price(cls, market, technical, session, meta):
        trend = str(technical.get("trend_direction") or market.get("trend_direction") or "").upper()
        observed = market.get("last_tick_time") or market.get("timestamp")
        fresh = str(meta.get("freshness_status") or ("fresh" if observed else "unavailable")).lower()
        eligible = bool(observed and market.get("current_spot")) and (session != "MARKET_OPEN" or fresh in cls.LIVE_FRESHNESS)
        state = "BULLISH" if trend in {"UP", "UPTREND", "BULLISH"} else "BEARISH" if trend in {"DOWN", "DOWNTREND", "BEARISH"} else "NEUTRAL"
        return cls._signal(state if eligible else "UNAVAILABLE", [f"Validated price structure is {state.lower()}."] if eligible else [],
                           source="canonical.market_data+technical_analysis", observed_at=observed, freshness=fresh,
                           eligible=eligible, reason=None if eligible else "current-session price structure unavailable")

    @classmethod
    def _opening(cls, macro, session):
        gap = macro.get("opening_gap") or {}
        ready = gap.get("status") == "READY"
        allowed = session != "MARKET_OPEN"
        raw = str(gap.get("classification") or "")
        state = "POSITIVE" if raw.startswith("POSITIVE") else "NEGATIVE" if raw.startswith("NEGATIVE") else "FLAT" if raw.startswith("FLAT") else "UNAVAILABLE"
        eligible = ready and allowed and state != "UNAVAILABLE"
        ev = [f"{raw}; {gap.get('gap_points')} points ({gap.get('gap_pct')}%)."] if eligible else []
        return cls._signal(state if eligible else "UNAVAILABLE", ev, source=str(gap.get("source") or "canonical.opening_gap"),
                           observed_at=gap.get("observation_timestamp"), freshness=str(gap.get("freshness") or "unavailable").lower(),
                           eligible=eligible, reason="opening indication is historical context during market open" if ready and not allowed else "eligible opening indication unavailable")

    @classmethod
    def _global(cls, macro, session):
        quotes = macro.get("quotes") or {}; allowed = set((macro.get("workspace_context") or {}).get("current_context_quote_keys") or [])
        keys = [k for k in ("S&P 500", "NASDAQ", "DOW_JONES", "NIKKEI_225", "HANG_SENG") if k in allowed and k in quotes]
        if not keys: return cls._signal("UNAVAILABLE", [], source="canonical.macro_quotes", eligible=False, reason="no freshness-eligible global equity observations")
        moves = [(k, float(quotes[k].get("change_pct") or 0)) for k in keys]
        pos = sum(v > .15 for _, v in moves); neg = sum(v < -.15 for _, v in moves)
        state = "RISK_ON" if pos >= 3 and pos > neg else "RISK_OFF" if neg >= 3 and neg > pos else "MIXED"
        return cls._signal(state, [f"{k} {v:+.2f}%." for k, v in moves], source="canonical.macro_quotes",
                           observed_at=max((quotes[k].get("observation_timestamp") or "" for k in keys), default=""), freshness="eligible")

    @classmethod
    def _institutional(cls, macro):
        context = macro.get("institutional_context") or {}; cash = context.get("cash") or []; deriv = context.get("derivatives") or {}
        evidence=[]; directions=[]
        for row in cash:
            net=float(row.get("net_value") or 0); label=str(row.get("dataset_type") or "institutional cash")
            directions.append(1 if net > 0 else -1 if net < 0 else 0); evidence.append(f"{label} net {net:+.2f}.")
        for key in ("FII_INDEX_FUTURES", "FII_INDEX_CALLS", "FII_INDEX_PUTS"):
            row=deriv.get(key) or {}
            if row:
                pos=str(row.get("positioning") or "NEUTRAL"); evidence.append(f"{key}: {pos}.")
                directions.append(-1 if pos in {"NET_SHORT", "SHORT_EXCEEDS_LONG"} else 1 if pos in {"NET_LONG", "LONG_EXCEEDS_SHORT"} else 0)
        if not evidence: return cls._signal("UNAVAILABLE", [], source="canonical.institutional_context", eligible=False, reason="institutional observations unavailable")
        state="POSITIVE" if directions and all(v >= 0 for v in directions) and any(directions) else "NEGATIVE" if directions and all(v <= 0 for v in directions) and any(directions) else "NEUTRAL" if not any(directions) else "MIXED"
        return cls._signal(state, evidence, source="canonical.institutional_context", freshness="last_valid_session")

    @classmethod
    def _breadth(cls, market, session):
        b=market.get("breadth") or {}; coverage_value=b.get("valid_observations") or b.get("coverage") or 0
        coverage=int(coverage_value.get("valid") or 0) if isinstance(coverage_value, dict) else int(coverage_value)
        eligible=coverage >= cls.BREADTH_MIN_COVERAGE and (session != "MARKET_OPEN" or str(market.get("session_mode") or "").upper() != "LAST_SESSION")
        if not eligible: return cls._signal("UNAVAILABLE", [], source="canonical.market_data.breadth", eligible=False, reason=f"coverage {coverage}/50 below live eligibility or not current-session")
        a=int(b.get("advances") or 0); d=int(b.get("declines") or 0); ratio=a/max(1,a+d)
        state="STRONG_POSITIVE" if ratio >= .7 else "POSITIVE" if ratio >= .56 else "STRONG_NEGATIVE" if ratio <= .3 else "NEGATIVE" if ratio <= .44 else "MIXED"
        return cls._signal(state, [f"Breadth {a} advances, {d} declines; coverage {coverage}/50."], source="Kite constituent observations", observed_at=market.get("last_tick_time"), freshness="current" if session == "MARKET_OPEN" else "last_valid_session")

    @classmethod
    def _options(cls, options, session, meta):
        pcr=options.get("pcr"); mp=options.get("max_pain"); atm=options.get("atm_strike")
        observed=options.get("provider_timestamp") or options.get("snapshot_timestamp") or options.get("timestamp")
        fresh=str(meta.get("freshness_status") or ("fresh" if observed else "unavailable")).lower()
        eligible=pcr is not None and mp is not None and bool(observed) and (session != "MARKET_OPEN" or fresh in cls.LIVE_FRESHNESS)
        if not eligible: return cls._signal("UNAVAILABLE", [], source="canonical.option_intelligence", eligible=False, reason="fresh session-appropriate option aggregate unavailable", freshness=fresh)
        p=float(pcr); bias=str(options.get("market_option_bias") or "").upper()
        pstate="BULLISH" if p >= 1.05 else "BEARISH" if p <= .8 else "BALANCED"
        mapped="BULLISH" if "BULL" in bias else "BEARISH" if "BEAR" in bias else "BALANCED"
        state="CONFLICTED" if mapped != "BALANCED" and pstate != "BALANCED" and mapped != pstate else mapped if mapped != "BALANCED" else pstate
        return cls._signal(state, [f"PCR {p:.2f} ({pstate.lower()}); Max Pain {mp}; ATM {atm}."], source="Kite option chain", observed_at=observed, freshness=fresh)

    @classmethod
    def _volatility(cls, market, options, macro, session):
        v=(macro.get("india_vix") or market.get("india_vix_context") or {}); value=v.get("value"); state=str(v.get("regime") or "UNAVAILABLE").upper()
        eligible=value is not None and state in {"LOW","NORMAL","ELEVATED","HIGH"}
        return cls._signal(state if eligible else "UNAVAILABLE", [f"India VIX {value}; regime {state}.", f"ATM IV {options.get('atm_iv')}."] if eligible else [], source=str(v.get("source") or "canonical.india_vix"), observed_at=v.get("observation_timestamp"), freshness=str(v.get("freshness") or "unavailable").lower(), eligible=eligible, reason=None if eligible else "validated VIX unavailable")

    @classmethod
    def _news(cls, news):
        items=[x for x in (news.get("items") or []) if x.get("canonical_eligible", True)]
        dirs=[str(x.get("expected_direction") or "NEUTRAL").upper() for x in items if float(x.get("nifty_relevance_score") or 0) >= 6]
        if not items: return cls._signal("UNAVAILABLE", [], source="canonical.news_intelligence", eligible=False, reason="eligible current news unavailable")
        pos=dirs.count("POSITIVE"); neg=dirs.count("NEGATIVE"); state="POSITIVE" if pos and not neg else "NEGATIVE" if neg and not pos else "MIXED" if pos and neg else "NEUTRAL"
        return cls._signal(state, [f"{len(items)} freshness-eligible news items; {pos} positive, {neg} negative high-relevance classifications."], source="canonical.news_intelligence", freshness=str(news.get("freshness") or "eligible"))

    @classmethod
    def _events(cls, macro, now):
        events=macro.get("economic_events") or []
        if not events: return cls._signal("UNAVAILABLE", [], source="canonical.economic_calendar", eligible=False, reason="calendar unavailable; event risk is unknown")
        upcoming=[]
        for event in events:
            if str(event.get("status") or "").upper() not in {"SCHEDULED","UPCOMING","DUE"}: continue
            raw=event.get("scheduled_at_ist") or event.get("scheduled_at")
            try:
                dt=datetime.fromisoformat(str(raw).replace("Z","+00:00")); dt=dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
                hours=(dt.astimezone(timezone.utc)-now.astimezone(timezone.utc)).total_seconds()/3600
            except (TypeError, ValueError): hours=999
            if hours >= 0: upcoming.append((hours,event))
        high=[x for x in upcoming if str(x[1].get("impact_level") or "").upper() in {"HIGH","CRITICAL"}]
        state="IMMINENT" if high and min(x[0] for x in high) <= 2 else "HIGH" if high and min(x[0] for x in high) <= 24 else "MODERATE" if high else "LOW"
        ordered_high=sorted(high, key=lambda x: (x[0], str(x[1].get("event_name") or "")))
        evidence=[f"{x[1].get('event_name')} in {x[0]:.1f}h ({x[1].get('impact_level')})." for x in ordered_high[:3]] or ["No upcoming high-impact event in the eligible calendar window."]
        return cls._signal(state,evidence,source="canonical.economic_calendar",freshness="eligible")

    @classmethod
    def _alignment(cls, signals, session):
        directional=["price","breadth","options"] if session == "MARKET_OPEN" else ["price","opening","global","institutional","options","news"]
        eligible=[k for k in directional if signals[k]["eligible"]]
        pos=[k for k in eligible if signals[k]["state"] in cls.POSITIVE]; neg=[k for k in eligible if signals[k]["state"] in cls.NEGATIVE]
        neutral=[k for k in eligible if k not in pos+neg]
        if len(eligible)<2: state="INSUFFICIENT_EVIDENCE"
        elif pos and neg: state="CONFLICTED"
        elif len(pos)>=4: state="STRONG_BULLISH_ALIGNMENT"
        elif len(pos)>=2: state="BULLISH_ALIGNMENT"
        elif len(neg)>=4: state="STRONG_BEARISH_ALIGNMENT"
        elif len(neg)>=2: state="BEARISH_ALIGNMENT"
        else: state="MIXED"
        dominant=pos if "BULLISH" in state or state == "CONFLICTED" else neg if "BEARISH" in state else []
        opposing=neg if dominant is pos else pos if dominant is neg else pos+neg
        return {"state":state,"confirming":dominant,"opposing":opposing,"neutral":neutral}

    @staticmethod
    def _levels(market, technical, options):
        rows=[]
        def add(value, origin, role):
            if isinstance(value,(int,float)) and value>0 and not any(x["value"]==float(value) and x["origin"]==origin for x in rows): rows.append({"value":float(value),"origin":origin,"role":role,"synthetic":False})
        for v in market.get("support_levels") or technical.get("support_levels") or []: add(v,"PRICE_STRUCTURE","SUPPORT")
        for v in market.get("resistance_levels") or technical.get("resistance_levels") or []: add(v,"PRICE_STRUCTURE","RESISTANCE")
        for v in options.get("support_strikes") or []: add(v,"OPTION_OI","SUPPORT")
        for v in options.get("resistance_strikes") or []: add(v,"OPTION_OI","RESISTANCE")
        add(options.get("max_pain"),"MAX_PAIN","REFERENCE"); add(options.get("atm_strike"),"ATM","REFERENCE")
        add(market.get("previous_close"),"PREVIOUS_SESSION","REFERENCE")
        return rows

    @staticmethod
    def _regime(market, technical, signals):
        raw=str(technical.get("market_regime") or market.get("market_regime") or "").upper()
        mapping={"TRENDING_UP":"TRENDING_UP","UPTREND":"TRENDING_UP","TRENDING_DOWN":"TRENDING_DOWN","DOWNTREND":"TRENDING_DOWN","RANGE":"RANGE_BOUND","RANGE_BOUND":"RANGE_BOUND","COMPRESSION":"COMPRESSION"}
        if signals["volatility"]["state"] in {"ELEVATED","HIGH"} and raw not in mapping: return "VOLATILE"
        return mapping.get(raw,"UNCERTAIN" if signals["price"]["eligible"] else "INSUFFICIENT_DATA")

    @classmethod
    def _risk(cls, signals, alignment):
        reasons=[]
        if signals["volatility"]["state"] in {"ELEVATED","HIGH"}: reasons.append("volatility elevated")
        if signals["events"]["state"] in {"HIGH","IMMINENT"}: reasons.append("high-impact event risk")
        if alignment["state"]=="CONFLICTED": reasons.append("directional evidence conflicts")
        if not signals["events"]["eligible"]: reasons.append("event calendar unavailable")
        if any(not x["eligible"] for x in signals.values()): reasons.append("some evidence is unavailable or ineligible")
        state="HIGH" if signals["volatility"]["state"]=="HIGH" or signals["events"]["state"]=="IMMINENT" else "ELEVATED" if reasons[:3] else "NORMAL"
        return {"state":state,"reasons":reasons,"position_sizing":None}

    @classmethod
    def _critical_missing(cls, signals, session):
        names=["price","breadth","options"] if session=="MARKET_OPEN" else ["price","opening","global","events"]
        return [n for n in names if not signals[n]["eligible"]]

    @classmethod
    def _confidence(cls, signals, alignment, session):
        missing=cls._critical_missing(signals,session)
        if len(missing)>=3 or alignment["state"]=="INSUFFICIENT_EVIDENCE": return "INSUFFICIENT"
        if alignment["state"]=="CONFLICTED" or missing: return "LOW"
        if any(not s["eligible"] for s in signals.values()): return "MODERATE"
        return "HIGH"

    @classmethod
    def _scenarios(cls, signals, levels, session):
        if session not in {"PRE_OPEN","WEEKEND","HOLIDAY"}: return []
        opening=signals["opening"]["state"]
        names=("GAP_UP_HOLD","GAP_UP_FADE") if opening=="POSITIVE" else ("GAP_DOWN_RECOVERY","GAP_DOWN_CONTINUATION") if opening=="NEGATIVE" else ("FLAT_OPEN_BREAKOUT","FLAT_OPEN_RANGE")
        common=["opening range is established from genuine current-session prices","breadth has at least 40/50 coverage"]
        return [{"name":names[0],"priority":"PRIMARY_CONTEXT","prediction":False,"confirmation_conditions":common+["price sustains beyond the opening range with breadth confirmation"],"invalidation_conditions":["opening indication is retraced and validated structure is lost"]},
                {"name":names[1],"priority":"ALTERNATE","prediction":False,"confirmation_conditions":common+["opening move fails to sustain and price returns through the opening range"],"invalidation_conditions":["price reclaims the opening extreme with breadth confirmation"]}]

    @staticmethod
    def _invalidations(alignment, signals, levels):
        conditions=[]
        supports=[x["value"] for x in levels if x["role"]=="SUPPORT"]; resistance=[x["value"] for x in levels if x["role"]=="RESISTANCE"]
        if "BULLISH" in alignment["state"] and supports: conditions.append(f"Price loses genuine support {max(supports):g}.")
        if "BEARISH" in alignment["state"] and resistance: conditions.append(f"Price reclaims genuine resistance {min(resistance):g}.")
        conditions += ["Breadth changes to the opposing state with at least 40/50 coverage.","India VIX escalates to HIGH.","A high-impact event becomes IMMINENT."]
        return conditions

    @staticmethod
    def _explanation(session, alignment, signals, regime, risk):
        label=alignment["state"].replace("_"," ").lower()
        confirming=", ".join(alignment["confirming"]) or "no dominant confirming family"
        opposing=", ".join(alignment["opposing"]) or "no eligible opposing family"
        prefix={"PRE_OPEN":"Pre-market context","MARKET_OPEN":"Live market context","POST_CLOSE":"Completed-session review"}.get(session,"Next-session context")
        return f"{prefix} is {label}. Confirming evidence: {confirming}. Opposing evidence: {opposing}. Market regime is {regime.lower().replace('_',' ')}; analytical risk is {risk['state'].lower()}."

    @classmethod
    def _outlook(cls, session: str, alignment: dict[str, Any], confidence: str, risk: dict[str, Any],
                 signals: dict[str, Any], scenarios: list[dict[str, Any]], levels: list[dict[str, Any]],
                 now: datetime) -> dict[str, Any]:
        current_utc = now.astimezone(timezone.utc)
        weekday = current_utc.strftime("%a")

        if session == "WEEKEND":
            relation = "NEXT_TRADING_SESSION"
            date_str = None
            verified = False
        elif session == "HOLIDAY":
            relation = "NEXT_TRADING_SESSION"
            date_str = None
            verified = False
        elif session == "PRE_OPEN":
            relation = "TODAY"
            date_str = current_utc.strftime("%Y-%m-%d")
            verified = True
        else:
            relation = "TOMORROW"
            date_str = None
            verified = False

        align_state = str(alignment.get("state") or "").upper()
        if align_state == "STRONG_BULLISH_ALIGNMENT":
            overall_view = "Strongly Positive"
        elif align_state == "BULLISH_ALIGNMENT":
            overall_view = "Cautiously Positive"
        elif align_state == "MIXED":
            overall_view = "Mixed Setup"
        elif align_state == "CONFLICTED":
            overall_view = "Conflicting Signals"
        elif align_state == "BEARISH_ALIGNMENT":
            overall_view = "Cautiously Negative"
        elif align_state == "STRONG_BEARISH_ALIGNMENT":
            overall_view = "Strongly Negative"
        else:
            overall_view = "No Clear Setup"

        op_signal = signals.get("opening") or {}
        if op_signal.get("eligible") and op_signal.get("evidence"):
            expected_opening = op_signal["evidence"][0]
        else:
            expected_opening = "Opening Indication Unavailable"

        conviction = "High Conviction" if confidence == "HIGH" else "Moderate Conviction" if confidence == "MODERATE" else "Low Conviction" if confidence == "LOW" else "Insufficient Conviction"
        risk_label = "High Risk" if risk.get("state") == "HIGH" else "Higher Risk" if risk.get("state") == "ELEVATED" else "Normal Risk"

        primary_scenario = scenarios[0] if scenarios else None
        primary_id = primary_scenario.get("name") if primary_scenario else None

        if "BULLISH" in align_state:
            pref_title = "Bullish Continuation"
            pref_desc = "Bullish continuation if opening range holds and market breadth confirms."
        elif "BEARISH" in align_state:
            pref_title = "Bearish Continuation"
            pref_desc = "Bearish continuation after support failure and breadth deterioration."
        elif align_state == "CONFLICTED":
            pref_title = "No Clear Preferred Setup"
            pref_desc = "Conflicting signals between options, breadth, and global cues. Wait for opening range and breadth confirmation."
        elif align_state == "MIXED":
            pref_title = "No Clear Preferred Setup"
            pref_desc = "Mixed indicator signals. Wait for opening range and breadth confirmation."
        else:
            pref_title = "No Clear Setup"
            pref_desc = "Insufficient canonical evidence to determine a preferred market setup."

        preferred_setup = {
            "scenario_id": primary_id,
            "title": pref_title,
            "description": pref_desc,
        }

        reasons = risk.get("reasons") or []
        key_concerns = [str(r) for r in reasons] if reasons else ["No major concern reported."]

        confirming_ev = []
        for name in alignment.get("confirming") or []:
            sig = signals.get(name) or {}
            confirming_ev.extend(sig.get("evidence") or [])
        if not confirming_ev and op_signal.get("eligible"):
            confirming_ev.extend(op_signal.get("evidence") or [])

        opposing_ev = []
        for name in alignment.get("opposing") or []:
            sig = signals.get(name) or {}
            opposing_ev.extend(sig.get("evidence") or [])

        at_the_open = [
            {"item": "Does the opening gap hold or fill quickly?", "source_rule": "signals.opening"},
            {"item": "Does market breadth confirm the move (min 40/50 constituents)?", "source_rule": "signals.breadth"},
            {"item": "Does price remain above key support / below resistance?", "source_rule": "key_levels"},
            {"item": "Does option PCR & IV positioning align with price movement?", "source_rule": "signals.options"},
            {"item": "Is there any sudden volatility expansion or scheduled event risk?", "source_rule": "signals.volatility"}
        ]

        return {
            "target_session_date": date_str,
            "target_session_relation": relation,
            "target_session_verified": verified,
            "overall_view": overall_view,
            "expected_opening": expected_opening,
            "conviction": conviction,
            "risk_label": risk_label,
            "preferred_setup": preferred_setup,
            "key_concerns": key_concerns,
            "supports": confirming_ev,
            "caution": key_concerns,
            "opposes": opposing_ev,
            "at_the_open": at_the_open,
        }
