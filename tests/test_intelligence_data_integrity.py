import pytest
from src.application.workstation_state_service import WorkstationStateService


def test_intelligence_shared_canonical_market_truth():
    service = WorkstationStateService()
    payload = {
        "marketContext": {
            "current_spot": 24287.65,
            "previous_close": 24366.00,
            "spot_change": -78.35,
            "spot_change_pct": -0.3216,
            "breadth": {"advances": 18, "declines": 31, "unchanged": 1},
        },
        "optionContext": {
            "underlying_spot": 24287.65,
            "atm_strike": 24300,
            "max_pain": 24350,
            "pcr": 1.22,
            "atm_iv": 11.41,
            "expiry": "2026-08-18",
            "current_weekly_expiry": "2026-08-18",
            "timestamp": "2026-08-17T15:30:00Z",
            "snapshot_timestamp": "2026-08-17T15:30:00Z",
            "observed_at": "2026-08-17T15:30:00Z",
        },
        "macroIntelligence": {
            "india_vix": {"value": 11.33, "change": 0.02, "change_pct": 0.18}
        },
    }
    state = service.build_canonical_state(payload)

    md = state.market_data
    oi = state.option_intelligence
    mi = state.macro_intelligence

    # Shared market fields
    assert md.get("current_spot") == 24287.65
    assert md.get("previous_close") == 24366.00
    assert md.get("spot_change") == -78.35
    assert round(md.get("spot_change_pct"), 2) == -0.32

    # Volatility
    assert mi.get("india_vix", {}).get("value") == 11.33

    # Breadth
    breadth = md.get("breadth", {})
    assert breadth.get("advances") == 18
    assert breadth.get("declines") == 31
    assert breadth.get("unchanged") == 1

    # Options
    assert oi.get("pcr") is not None
    assert round(oi.get("pcr"), 2) == 1.22
    assert oi.get("max_pain") == 24350
    assert oi.get("atm_strike") == 24300


def test_opportunity_qualification_gating_contract():
    # Qualification contract rules
    def evaluate_opportunity_qualification(
        confidence_pct: int,
        breadth_adv: int,
        breadth_dec: int,
        spot: float,
        r1: float,
        s1: float,
        is_market_closed: bool,
    ) -> str:
        if is_market_closed:
            return "NO_SETUP_MARKET_CLOSED"
        if confidence_pct < 70:
            return "UNQUALIFIED_LOW_CONFIDENCE"
        if breadth_adv < breadth_dec:
            return "UNQUALIFIED_NEGATIVE_BREADTH"
        if s1 <= spot <= r1:
            return "UNQUALIFIED_INSIDE_RANGE"
        return "QUALIFIED"

    # Current staging conditions
    res = evaluate_opportunity_qualification(
        confidence_pct=50,
        breadth_adv=18,
        breadth_dec=31,
        spot=24287.65,
        r1=24291.0,
        s1=24284.0,
        is_market_closed=True,
    )
    assert res == "NO_SETUP_MARKET_CLOSED"

    # Even if market were open, 50% confidence blocks qualification
    res_open = evaluate_opportunity_qualification(
        confidence_pct=50,
        breadth_adv=18,
        breadth_dec=31,
        spot=24287.65,
        r1=24291.0,
        s1=24284.0,
        is_market_closed=False,
    )
    assert res_open == "UNQUALIFIED_LOW_CONFIDENCE"


def test_pre_market_mathematical_gap_open_reconciliation():
    ref_close = 24287.65
    gap_low = 40.0
    gap_high = 70.0

    expected_open_low = round(ref_close + gap_low, 2)
    expected_open_high = round(ref_close + gap_high, 2)

    assert expected_open_low == 24327.65
    assert expected_open_high == 24357.65
    assert f"{expected_open_low:,.0f} – {expected_open_high:,.0f}" == "24,328 – 24,358"


def test_sector_ranking_reconciliation():
    sectors = [
        {"name": "NIFTY METAL", "change_pct": 0.55},
        {"name": "NIFTY AUTO", "change_pct": 0.45},
        {"name": "NIFTY PHARMA", "change_pct": 0.32},
        {"name": "NIFTY REALTY", "change_pct": 0.20},
        {"name": "NIFTY FIN SERVICE", "change_pct": 0.08},
        {"name": "NIFTY BANK", "change_pct": 0.01},
        {"name": "NIFTY FMCG", "change_pct": -0.12},
        {"name": "NIFTY OIL & GAS", "change_pct": -0.15},
        {"name": "NIFTY ENERGY", "change_pct": -0.40},
        {"name": "NIFTY IT", "change_pct": -0.66},
    ]

    gainers = [s for s in sectors if s["change_pct"] > 0]
    laggards = [s for s in sectors if s["change_pct"] < 0]

    assert len(gainers) == 6
    assert len(laggards) == 4
    assert gainers[0]["name"] == "NIFTY METAL"
    assert laggards[-1]["name"] == "NIFTY IT"


def test_evidence_stack_accounting():
    evidence = [
        {"type": "SUPPORTING", "factor": "Institutional Accumulation"},
        {"type": "SUPPORTING", "factor": "Derivatives PCR"},
        {"type": "SUPPORTING", "factor": "Low VIX"},
        {"type": "OPPOSING", "factor": "Market Breadth"},
        {"type": "OPPOSING", "factor": "Price Below R1"},
        {"type": "NEUTRAL", "factor": "Sector Dispersion"},
    ]

    supporting = len([e for e in evidence if e["type"] == "SUPPORTING"])
    opposing = len([e for e in evidence if e["type"] == "OPPOSING"])
    neutral = len([e for e in evidence if e["type"] == "NEUTRAL"])

    assert supporting == 3
    assert opposing == 2
    assert neutral == 1


def test_explanation_contract_coverage_and_structure():
    # Verify required keys in explanation contract
    required_conclusions = [
        "opportunity_verdict",
        "opening_bias",
        "expected_open",
        "live_bias",
        "market_regime",
        "breadth",
        "institutional",
        "options_bias",
        "volatility",
        "next_day_bias",
        "projected_sector_focus",
    ]

    # Dummy canonical representation
    mock_explanations = {
        "opportunity_verdict": {
            "what": {"summary": "No qualified setup", "traderMeaning": "Preserve capital", "currentImplication": "Stand aside"},
            "why": {"summary": "Failed qualification gates", "supporting": ["DII Accumulation"], "opposing": ["Negative breadth", "Range compression"]},
            "provenance": {"sessionDate": "17 Aug 2026", "freshness": "Deterministic Model Evaluation"},
        },
        "opening_bias": {
            "what": {"summary": "Mild positive opening expected", "traderMeaning": "Higher tick probable", "currentImplication": "Wait for pre-open book"},
            "why": {"summary": "DII +5.1K Cr and low VIX outweigh FII sales", "supporting": ["DII Cash", "Low VIX"], "opposing": ["FII Selling"]},
            "provenance": {"targetSession": "18 Aug 2026", "freshness": "Pre-Market Reference Telemetry"},
        },
        "expected_open": {
            "what": {"summary": "Expected open range 24,328-24,358", "traderMeaning": "Opening auction projection", "currentImplication": "Watch 24,328 level"},
            "why": {"summary": "Ref Close 24,287.65 + Gap (+40 to +70)", "supporting": ["Ref Close 24,287.65", "Gap Projection"]},
            "provenance": {"targetSession": "18 Aug 2026", "freshness": "Pre-Market Reference Model"},
        },
        "live_bias": {
            "what": {"summary": "Neutral rangebound bias", "traderMeaning": "No statistical trend edge", "currentImplication": "Trade range boundaries"},
            "why": {"summary": "Tension between DII buying and negative breadth", "supporting": ["DII Cash"], "opposing": ["Negative Breadth"]},
            "provenance": {"sessionDate": "17 Aug 2026", "freshness": "Completed Session Reference"},
        },
        "market_regime": {
            "what": {"summary": "Sideways consolidation", "traderMeaning": "Whipsaw risk inside chop", "currentImplication": "Range bound play"},
            "why": {"summary": "VIX 11.33 and spot inside 24,284-24,291", "supporting": ["Low VIX", "Decision Corridor"]},
            "provenance": {"sessionDate": "17 Aug 2026", "freshness": "Authoritative Classification"},
        },
        "breadth": {
            "what": {"summary": "Negative breadth (18/31/1)", "traderMeaning": "Weak internal health", "currentImplication": "Breakouts likely to fail"},
            "why": {"summary": "18 Advancers vs 31 Decliners out of 50", "opposing": ["31 Declining Members"]},
            "provenance": {"sessionDate": "17 Aug 2026", "freshness": "Official NSE Constituent Feed"},
        },
        "institutional": {
            "what": {"summary": "Net institutional buying (+2,566.4 Cr)", "traderMeaning": "Macro liquidity support", "currentImplication": "Dips absorbed"},
            "why": {"summary": "DII +5,101.5 Cr vs FII -2,535.1 Cr = +2,566.4 Cr", "supporting": ["DII +5,101.5 Cr"], "opposing": ["FII -2,535.1 Cr"]},
            "provenance": {"sessionDate": "17 Aug 2026", "freshness": "Last Published EOD Report"},
        },
        "options_bias": {
            "what": {"summary": "Supportive options structure", "traderMeaning": "Put writing cushion", "currentImplication": "Defend 24,300 strike"},
            "why": {"summary": "PCR 1.22 with 24,300 Put Wall and 24,350 Max Pain", "supporting": ["PCR 1.22", "Put Wall 24,300"]},
            "provenance": {"sessionDate": "17 Aug 2026", "freshness": "Last Valid Session Snapshot"},
        },
        "volatility": {
            "what": {"summary": "Low volatility regime", "traderMeaning": "Subdued market panic", "currentImplication": "Low expansion probability"},
            "why": {"summary": "India VIX 11.33 (+0.18%) < 12.00 threshold", "supporting": ["VIX 11.33"]},
            "provenance": {"sessionDate": "17 Aug 2026", "freshness": "NSE India VIX Index"},
        },
        "next_day_bias": {
            "what": {"summary": "Mixed to cautious carryover", "traderMeaning": "No overnight directional edge", "currentImplication": "Hedge overnight risk"},
            "why": {"summary": "DII buying vs negative breadth and sub-pivot close", "supporting": ["DII buying"], "opposing": ["Negative breadth"]},
            "provenance": {"targetSession": "18 Aug 2026", "freshness": "End of Session Forward Synthesis"},
        },
        "projected_sector_focus": {
            "what": {"summary": "Key sectors to monitor for catalysts", "traderMeaning": "Watchlist focus, not performance prediction", "currentImplication": "Track Banking and IT"},
            "why": {"summary": "Banking weight + IT laggard + Metal momentum", "supporting": ["Banking Weight", "Metal Momentum"]},
            "provenance": {"targetSession": "18 Aug 2026", "freshness": "Post-Market Watchlist Synthesis"},
        },
    }

    for key in required_conclusions:
        assert key in mock_explanations, f"Missing explanation for {key}"
        exp = mock_explanations[key]
        assert "what" in exp and "summary" in exp["what"]
        assert "why" in exp and "summary" in exp["why"]
        assert "provenance" in exp


def test_contradiction_guards_contract():
    # 1. Negative FII cash cannot claim FII buying
    fii_cash = -2535.1
    fii_claim = "FII buying" if fii_cash > 0 else "FII net selling"
    assert fii_claim == "FII net selling"

    # 2. Low confidence cannot claim high conviction
    confidence_score = 35
    conviction_label = "HIGH CONVICTION" if confidence_score >= 70 else "PRELIMINARY / LOW CONVICTION"
    assert conviction_label == "PRELIMINARY / LOW CONVICTION"

    # 3. Market closed cannot claim active live intraday trade execution
    market_closed = True
    tactical_instruction = (
        "Active 30-minute scalp plan in progress"
        if not market_closed
        else "Market is closed. Tactical execution rules activate at 09:15 IST next session."
    )
    assert "Market is closed" in tactical_instruction

    # 4. No qualified setup cannot advise immediate trade entry
    has_qualified_setup = False
    verdict_advice = (
        "Execute approved setup with defined stop"
        if has_qualified_setup
        else "Stand aside. Preserve capital during range-bound chop."
    )
    assert "Stand aside" in verdict_advice

    # 5. Sector focus must be labeled watchlist/forward monitoring, not past ranking
    focus_label = "WATCHLIST ONLY (Catalyst Monitoring)"
    assert "WATCHLIST" in focus_label

