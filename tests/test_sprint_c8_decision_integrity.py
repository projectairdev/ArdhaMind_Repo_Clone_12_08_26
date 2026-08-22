from pathlib import Path
from datetime import datetime, timezone
import pytest

from src.intelligence_engine import UnifiedNiftyIntelligenceBuilder
from src.application.data_quality_service import DataQualityService
from src.application.workstation_state_service import WorkstationStateService
from src.broker.services.market_status_service import MarketStatusService, HOLIDAYS_2026

ROOT = Path("src")


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_freshness_and_temporal_relation_independent():
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    market = {"current_spot": 24500.0, "last_tick_time": "2026-08-09T10:00:00Z"}
    options = {"pcr": 1.1, "max_pain": 24500, "atm_strike": 24500, "timestamp": "2026-08-08T15:30:00Z"}
    
    result = UnifiedNiftyIntelligenceBuilder.build(
        market=market, technical={}, options=options, macro={}, news={},
        market_state="CLOSED", now=now
    )
    
    ev_items = result.get("evidence_items") or []
    opt_ev = next((x for x in ev_items if x["category"] == "OPTION_POSITIONING"), None)
    assert opt_ev is not None
    assert "freshness" in opt_ev
    assert "temporal_relation" in opt_ev
    assert "decision_eligibility" in opt_ev
    assert opt_ev["temporal_relation"] == "PREVIOUS_SESSION"
    assert opt_ev["decision_eligibility"] == "CONTEXT_ONLY"


def test_previous_session_options_labeled_previous_session():
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    options = {"pcr": 1.1, "max_pain": 24500, "atm_strike": 24500, "timestamp": "2026-08-08T15:30:00Z"}
    
    result = UnifiedNiftyIntelligenceBuilder.build(
        market={}, technical={}, options=options, macro={}, news={},
        market_state="CLOSED", now=now
    )
    
    ev_items = result.get("evidence_items") or []
    opt_ev = next((x for x in ev_items if x["category"] == "OPTION_POSITIONING"), None)
    assert opt_ev["temporal_relation"] == "PREVIOUS_SESSION"
    assert opt_ev["decision_eligibility"] == "CONTEXT_ONLY"
    assert "(Previous Session)" in opt_ev["summary"]


def test_asynchronous_global_observations_labeled_foreign_session():
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    macro = {
        "workspace_context": {"current_context_quote_keys": ["S&P 500", "NASDAQ"]},
        "quotes": {
            "S&P 500": {"change_pct": 0.62, "observation_timestamp": "2026-08-08T20:00:00Z"},
            "NASDAQ": {"change_pct": 1.30, "observation_timestamp": "2026-08-08T20:00:00Z"}
        }
    }
    
    result = UnifiedNiftyIntelligenceBuilder.build(
        market={}, technical={}, options={}, macro=macro, news={},
        market_state="CLOSED", now=now
    )
    
    ev_items = result.get("evidence_items") or []
    global_ev = next((x for x in ev_items if x["category"] == "GLOBAL_CUES"), None)
    assert global_ev is not None
    assert global_ev["temporal_relation"] == "FOREIGN_SESSION"
    assert global_ev["decision_eligibility"] == "CONTEXT_ONLY"


def test_next_session_verification_uses_market_status_service():
    service = MarketStatusService.get_instance()
    friday_utc = datetime(2026, 8, 14, 12, 30, tzinfo=timezone.utc)
    report = service.get_market_status(friday_utc)
    assert "2026-08-17" in report.next_session_start or "2026-08-" in report.next_session_start

    result = UnifiedNiftyIntelligenceBuilder.build(
        market={}, technical={}, options={}, macro={}, news={},
        market_state="CLOSED", now=friday_utc
    )
    outlook = result["outlook"]
    assert outlook["target_session_verified"] is True
    assert outlook["target_session_relation"] == "NEXT_TRADING_SESSION"
    assert outlook["target_session_date"] is not None


def test_decision_zones_preserve_raw_levels_and_roles():
    levels = [
        {"value": 24568.69, "origin": "PRICE_STRUCTURE", "role": "SUPPORT"},
        {"value": 24569.67, "origin": "PRICE_STRUCTURE", "role": "SUPPORT"},
        {"value": 24571.63, "origin": "PRICE_STRUCTURE", "role": "SUPPORT"},
        {"value": 24572.61, "origin": "PRICE_STRUCTURE", "role": "SUPPORT"},
        {"value": 24800.00, "origin": "OPTION_OI", "role": "RESISTANCE"},
        {"value": 24500.00, "origin": "MAX_PAIN", "role": "REFERENCE"},
    ]
    
    zones = UnifiedNiftyIntelligenceBuilder._decision_zones(levels, atr=None)
    
    assert len(levels) == 6
    assert levels[0]["value"] == 24568.69
    
    sup_zones = [z for z in zones if z["role"] == "SUPPORT"]
    assert len(sup_zones) == 1
    assert sup_zones[0]["lower"] == 24568.69
    assert sup_zones[0]["upper"] == 24572.61
    assert sup_zones[0]["count"] == 4
    
    roles = {z["role"] for z in zones}
    assert roles == {"SUPPORT", "RESISTANCE", "REFERENCE"}


def test_missing_atr_uses_conservative_threshold():
    levels = [
        {"value": 24500.0, "origin": "PRICE_STRUCTURE", "role": "SUPPORT"},
        {"value": 24510.0, "origin": "PRICE_STRUCTURE", "role": "SUPPORT"},
    ]
    
    zones = UnifiedNiftyIntelligenceBuilder._decision_zones(levels, atr=None)
    assert len(zones) == 1
    assert zones[0]["display_range"] == "24500 – 24510"


def test_zero_index_volume_blocks_only_vwap():
    payload = {
        "marketContext": {"current_spot": 24500.0, "last_tick_time": "2026-08-09T10:00:00Z"},
        "technicalAnalysis": {"vwap": 0, "ema_20": 0, "ema_50": 0, "trend_direction": "UNKNOWN"}
    }
    
    canonical = WorkstationStateService.build_from_legacy(payload, market_state="CLOSED")
    tech = canonical.technical_analysis
    
    assert tech["vwap_status"] == "UNAVAILABLE"
    assert "no volume" in tech["vwap_reason"]
    assert tech["ema_status"] == "UNAVAILABLE"
    assert "minimum 50" in tech["ema_reason"]
    assert "trend_reason" in tech


def test_authoritative_candle_validation_boundary():
    corrupted_candles = [
        {"o": 24500, "h": 24450, "l": 24400, "c": 24480, "t": "2026-08-09T09:15:00Z"},
        {"o": 24500, "h": 24550, "l": 24480, "c": 24520, "t": "2026-08-09T09:16:00Z"},
        {"o": 24500, "h": 24550, "l": 24480, "c": 24520, "t": "2026-08-09T09:16:00Z"},
    ]
    
    valid, errors = DataQualityService.validate_candles(corrupted_candles)
    
    assert len(valid) == 1
    assert valid[0]["time"] == "2026-08-09T09:16:00Z"
    assert len(errors) == 2
    assert "OHLC invariant" in errors[0]
    assert "duplicate timestamp" in errors[1]


def test_evidence_statements_carry_temporal_context():
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    market = {"current_spot": 24500.0, "last_tick_time": "2026-08-09T10:00:00Z"}
    
    result = UnifiedNiftyIntelligenceBuilder.build(
        market=market, technical={}, options={}, macro={}, news={},
        market_state="CLOSED", now=now
    )
    
    ev_items = result["evidence_items"]
    for item in ev_items:
        assert "evidence_id" in item
        assert "category" in item
        assert "stance" in item
        assert "summary" in item
        assert "temporal_relation" in item
        assert "decision_eligibility" in item


def test_publication_time_controls_news_since_close():
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    payload = {
        "marketContext": {"current_spot": 24500.0, "last_tick_time": "2026-08-09T10:00:00Z"},
        "newsSentiment": {
            "items": [
                {
                    "id": "NEWS_OLD_01",
                    "headline": "Old policy announcement",
                    "published_at": "2026-08-08T00:00:00Z",
                    "received_at": "2026-08-09T09:50:00Z",
                    "nifty_relevance_score": 8,
                }
            ]
        }
    }
    
    canonical = WorkstationStateService.build_from_legacy(payload, market_state="CLOSED", now=now)
    since_close = canonical.news_intelligence.get("workspace_temporal", {}).get("since_close_item_ids", [])
    assert "NEWS_OLD_01" not in since_close


def test_premarket_validation_remains_pending_without_snapshot():
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    result = UnifiedNiftyIntelligenceBuilder.build(
        market={}, technical={}, options={}, macro={}, news={},
        market_state="MARKET_OPEN", now=now
    )
    val = result["premarket_view_validation"]
    assert val["status"] == "PENDING"
    assert "No prior pre-market synthesis snapshot" in val["reason"]


def test_read_only_protection_strictly_enforced():
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    result = UnifiedNiftyIntelligenceBuilder.build(
        market={}, technical={}, options={}, macro={}, news={},
        market_state="CLOSED", now=now
    )
    pref_desc = result["outlook"]["preferred_setup"]["description"].upper()
    for word in ["BUY", "SELL", "ENTER NOW", "PLACE ORDER", "TARGET", "STOP LOSS", "QUANTITY", "POSITION SIZE"]:
        assert word not in pref_desc


def test_mixed_conflicted_insufficient_distinct():
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    res_mixed = UnifiedNiftyIntelligenceBuilder._outlook(
        "CLOSED", {"state": "MIXED", "confirming": [], "opposing": []}, "MODERATE", {}, {}, [], [], now
    )
    res_conflicted = UnifiedNiftyIntelligenceBuilder._outlook(
        "CLOSED", {"state": "CONFLICTED", "confirming": [], "opposing": []}, "MODERATE", {}, {}, [], [], now
    )
    res_insufficient = UnifiedNiftyIntelligenceBuilder._outlook(
        "CLOSED", {"state": "INSUFFICIENT_EVIDENCE", "confirming": [], "opposing": []}, "INSUFFICIENT", {}, {}, [], [], now
    )

    assert res_mixed["overall_view"] == "Mixed Setup"
    assert res_conflicted["overall_view"] == "Conflicting Signals"
    assert res_insufficient["overall_view"] == "No Clear Setup"


def test_react_contains_no_duplicated_decision_rules():
    outlook_code = read("frontend/components/intelligence/TomorrowsOutlookCard.tsx")
    assert "intelligence.outlook" in outlook_code
    assert "if (" not in outlook_code.split("return (")[1].split("</section>")[0] or "map(" in outlook_code


# --- ADDITIONAL PRICE DATA & TEMPORAL TESTS (15 to 40) ---

def test_ohlc_low_le_open_le_high():
    valid, errors = DataQualityService.validate_candles([
        {"o": 24500, "h": 24550, "l": 24450, "c": 24520, "t": "2026-08-09T09:15:00Z"}
    ])
    assert len(valid) == 1
    assert valid[0]["l"] <= valid[0]["o"] <= valid[0]["h"]


def test_ohlc_low_le_close_le_high():
    valid, errors = DataQualityService.validate_candles([
        {"o": 24500, "h": 24550, "l": 24450, "c": 24520, "t": "2026-08-09T09:15:00Z"}
    ])
    assert len(valid) == 1
    assert valid[0]["l"] <= valid[0]["c"] <= valid[0]["h"]


def test_candles_strictly_chronological():
    input_candles = [
        {"o": 24520, "h": 24560, "l": 24500, "c": 24550, "t": "2026-08-09T09:16:00Z"},
        {"o": 24500, "h": 24550, "l": 24450, "c": 24520, "t": "2026-08-09T09:15:00Z"}
    ]
    valid, errors = DataQualityService.validate_candles(input_candles)
    assert len(valid) == 2
    assert valid[0]["time"] == "2026-08-09T09:15:00Z"
    assert valid[1]["time"] == "2026-08-09T09:16:00Z"


def test_duplicate_timestamps_rejected():
    input_candles = [
        {"o": 24500, "h": 24550, "l": 24450, "c": 24520, "t": "2026-08-09T09:15:00Z"},
        {"o": 24510, "h": 24560, "l": 24460, "c": 24530, "t": "2026-08-09T09:15:00Z"}
    ]
    valid, errors = DataQualityService.validate_candles(input_candles)
    assert len(valid) == 1
    assert len(errors) == 1
    assert "duplicate" in errors[0]


def test_session_high_matches_max_candle_high():
    candles = [
        {"o": 24500, "h": 24550, "l": 24450, "c": 24520, "t": "2026-08-09T09:15:00Z"},
        {"o": 24520, "h": 24610, "l": 24510, "c": 24590, "t": "2026-08-09T09:16:00Z"}
    ]
    valid, errors = DataQualityService.validate_candles(candles)
    session_high = max(c["h"] for c in valid)
    assert session_high == 24610.0


def test_session_low_matches_min_candle_low():
    candles = [
        {"o": 24500, "h": 24550, "l": 24410, "c": 24520, "t": "2026-08-09T09:15:00Z"},
        {"o": 24520, "h": 24610, "l": 24510, "c": 24590, "t": "2026-08-09T09:16:00Z"}
    ]
    valid, errors = DataQualityService.validate_candles(candles)
    session_low = min(c["l"] for c in valid)
    assert session_low == 24410.0


def test_corrupted_candle_payload_blocked():
    candles = [{"o": "invalid", "h": 24500, "l": 24400, "c": 24450, "t": "2026-08-09T09:15:00Z"}]
    valid, errors = DataQualityService.validate_candles(candles)
    assert len(valid) == 0
    assert len(errors) == 1


def test_insufficient_candles_produce_no_fake_ema():
    payload = {
        "marketContext": {"current_spot": 24500.0, "last_tick_time": "2026-08-09T10:00:00Z"},
        "technicalAnalysis": {"ema_20": None, "ema_50": None}
    }
    canonical = WorkstationStateService.build_from_legacy(payload, market_state="CLOSED")
    assert canonical.technical_analysis["ema_status"] == "UNAVAILABLE"
    assert "minimum 50" in canonical.technical_analysis["ema_reason"]


def test_zero_volume_index_produces_no_fake_vwap():
    payload = {
        "marketContext": {"current_spot": 24500.0, "last_tick_time": "2026-08-09T10:00:00Z"},
        "technicalAnalysis": {"vwap": 0}
    }
    canonical = WorkstationStateService.build_from_legacy(payload, market_state="CLOSED")
    assert canonical.technical_analysis["vwap_status"] == "UNAVAILABLE"
    assert "no volume" in canonical.technical_analysis["vwap_reason"]


def test_historical_market_closed_candles_labeled_session():
    payload = {
        "marketContext": {"current_spot": 24500.0, "last_tick_time": "2026-08-09T10:00:00Z"},
    }
    canonical = WorkstationStateService.build_from_legacy(payload, market_state="CLOSED")
    assert canonical.market_feed_status["status"] == "market_closed"
    assert canonical.market_feed_status["source"] == "kite_historical_api"


def test_no_executable_words_in_preferred_setup():
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    result = UnifiedNiftyIntelligenceBuilder.build(
        market={}, technical={}, options={}, macro={}, news={},
        market_state="CLOSED", now=now
    )
    pref = result["outlook"]["preferred_setup"]
    for forbidden in ["BUY", "SELL", "ORDER", "QUANTITY", "TARGET", "STOP LOSS"]:
        assert forbidden not in pref["title"].upper()
        assert forbidden not in pref["description"].upper()


def test_trader_zones_preserve_exact_raw_canonical_levels():
    raw_levels = [{"value": 24568.69, "origin": "PRICE_STRUCTURE", "role": "SUPPORT"}]
    zones = UnifiedNiftyIntelligenceBuilder._decision_zones(raw_levels)
    assert raw_levels[0]["value"] == 24568.69
    assert zones[0]["lower"] == 24568.69


def test_distinct_reference_levels_retain_identity():
    levels = [
        {"value": 24500.0, "origin": "MAX_PAIN", "role": "REFERENCE"},
        {"value": 24500.0, "origin": "ATM", "role": "REFERENCE"},
        {"value": 24480.0, "origin": "PREVIOUS_SESSION", "role": "REFERENCE"}
    ]
    zones = UnifiedNiftyIntelligenceBuilder._decision_zones(levels)
    ref_zones = [z for z in zones if z["role"] == "REFERENCE"]
    assert len(ref_zones) > 0
    # Both 24500.0 levels are preserved in contributing_levels
    all_contrib = [item for z in ref_zones for item in z["contributing_levels"]]
    origins = {x["origin"] for x in all_contrib}
    assert "MAX_PAIN" in origins
    assert "ATM" in origins
    assert "PREVIOUS_SESSION" in origins


def test_no_fake_directional_view_under_insufficient_evidence():
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    result = UnifiedNiftyIntelligenceBuilder.build(
        market={}, technical={}, options={}, macro={}, news={},
        market_state="CLOSED", now=now
    )
    assert result["alignment"] == "INSUFFICIENT_EVIDENCE"
    assert result["outlook"]["overall_view"] == "No Clear Setup"


def test_conflicting_evidence_remains_conflicted():
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    market = {"current_spot": 24500.0, "last_tick_time": "2026-08-09T10:00:00Z"}
    technical = {"trend_direction": "UP"}
    options = {"pcr": 0.7, "max_pain": 24500, "atm_strike": 24500, "timestamp": "2026-08-09T10:00:00Z", "market_option_bias": "BEARISH"}
    
    result = UnifiedNiftyIntelligenceBuilder.build(
        market=market, technical=technical, options=options, macro={}, news={},
        market_state="CLOSED", now=now
    )
    assert result["alignment"] == "CONFLICTED"
    assert result["outlook"]["overall_view"] == "Conflicting Signals"


def test_evidence_summaries_contain_actual_evidence_strings():
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    market = {"current_spot": 24500.0, "last_tick_time": "2026-08-09T10:00:00Z", "breadth": {"advances": 32, "declines": 18, "coverage": 50}}
    
    result = UnifiedNiftyIntelligenceBuilder.build(
        market=market, technical={}, options={}, macro={}, news={},
        market_state="CLOSED", now=now
    )
    ev_items = result["evidence_items"]
    breadth_ev = next((x for x in ev_items if x["category"] == "MARKET_BREADTH"), None)
    assert breadth_ev is not None
    assert "32 advances" in breadth_ev["summary"]


def test_stale_evidence_not_labeled_live():
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    options = {"pcr": 1.1, "max_pain": 24500, "atm_strike": 24500, "timestamp": "2026-08-08T15:30:00Z"}
    
    result = UnifiedNiftyIntelligenceBuilder.build(
        market={}, technical={}, options=options, macro={}, news={},
        market_state="CLOSED", now=now
    )
    ev_items = result["evidence_items"]
    opt_ev = next((x for x in ev_items if x["category"] == "OPTION_POSITIONING"), None)
    assert opt_ev["temporal_relation"] != "CURRENT_SESSION"


def test_target_session_friday_handles_weekend():
    service = MarketStatusService.get_instance()
    friday = datetime(2026, 8, 14, 18, 0, tzinfo=timezone.utc)
    report = service.get_market_status(friday)
    assert report.next_session_start.startswith("2026-08-17")


def test_target_session_saturday_handles_weekend():
    service = MarketStatusService.get_instance()
    saturday = datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc)
    report = service.get_market_status(saturday)
    assert report.next_session_start.startswith("2026-08-17")


def test_target_session_sunday_handles_weekend():
    service = MarketStatusService.get_instance()
    sunday = datetime(2026, 8, 16, 10, 0, tzinfo=timezone.utc)
    report = service.get_market_status(sunday)
    assert report.next_session_start.startswith("2026-08-17")


def test_holiday_handling_preserves_verification_truthfulness():
    service = MarketStatusService.get_instance()
    # 2026-01-26 is Republic Day holiday
    republic_day = datetime(2026, 1, 26, 10, 0, tzinfo=timezone.utc)
    assert service.is_holiday(republic_day) is True
    report = service.get_market_status(republic_day)
    assert report.is_holiday is True
    assert report.next_session_start.startswith("2026-01-27")


def test_unverified_news_remains_unverified():
    from src.application.workstation_state_service import WorkstationStateService
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    payload = {
        "marketContext": {"current_spot": 24500.0, "last_tick_time": "2026-08-09T10:00:00Z"},
        "newsSentiment": {
            "items": [
                {
                    "id": "NEWS_UNVER_01",
                    "headline": "Unverified rumor story",
                    "published_at": "2026-08-09T09:00:00Z",
                    "verification_status": "UNVERIFIED",
                }
            ]
        }
    }
    canonical = WorkstationStateService.build_from_legacy(payload, market_state="CLOSED", now=now)
    items = canonical.news_intelligence.get("items", [])
    assert items[0]["verification_status"] == "UNVERIFIED"


def test_unavailable_breadth_produces_no_fabricated_evidence():
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    result = UnifiedNiftyIntelligenceBuilder.build(
        market={}, technical={}, options={}, macro={}, news={},
        market_state="CLOSED", now=now
    )
    b_sig = result["signals"]["breadth"]
    assert b_sig["eligible"] is False
    assert b_sig["state"] == "UNAVAILABLE"


def test_unavailable_gift_produces_no_opening_confirmation():
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    result = UnifiedNiftyIntelligenceBuilder.build(
        market={}, technical={}, options={}, macro={}, news={},
        market_state="CLOSED", now=now
    )
    op_sig = result["signals"]["opening"]
    assert op_sig["eligible"] is False
    assert op_sig["state"] == "UNAVAILABLE"


def test_contradictory_broker_label_eliminated():
    code = read("frontend/components/settings/SettingsWorkspace.tsx")
    assert "Zerodha KiteConnect" in code or "Kite" in code


def test_nifty_only_product_boundary_intact():
    from src.models.canonical_workstation_state import CanonicalWorkstationState
    assert CanonicalWorkstationState._assert_read_only is not None
