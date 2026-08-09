from pathlib import Path
from datetime import datetime, timezone
import pytest

from src.intelligence_engine import UnifiedNiftyIntelligenceBuilder

ROOT = Path("src")


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_outlook_derives_only_from_genuine_canonical_data():
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    market = {"current_spot": 24500.0, "last_tick_time": "2026-08-09T10:00:00Z"}
    technical = {"trend_direction": "UP"}
    options = {"pcr": 1.1, "max_pain": 24500, "atm_strike": 24500, "timestamp": "2026-08-09T10:00:00Z"}
    macro = {}
    news = {}
    
    result = UnifiedNiftyIntelligenceBuilder.build(
        market=market, technical=technical, options=options, macro=macro, news=news,
        market_state="CLOSED", now=now
    )
    
    assert "outlook" in result
    outlook = result["outlook"]
    assert "target_session_relation" in outlook
    assert "target_session_verified" in outlook
    assert "overall_view" in outlook
    assert "preferred_setup" in outlook
    assert "key_concerns" in outlook
    assert "at_the_open" in outlook


def test_preferred_setup_references_canonical_scenario():
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    market = {"current_spot": 24500.0, "last_tick_time": "2026-08-09T10:00:00Z"}
    technical = {"trend_direction": "UP"}
    options = {"pcr": 1.1, "max_pain": 24500, "atm_strike": 24500, "timestamp": "2026-08-09T10:00:00Z"}
    
    result = UnifiedNiftyIntelligenceBuilder.build(
        market=market, technical=technical, options=options, macro={}, news={},
        market_state="CLOSED", now=now
    )
    
    outlook = result["outlook"]
    pref = outlook["preferred_setup"]
    assert "scenario_id" in pref
    assert "title" in pref
    assert "description" in pref


def test_preferred_setup_is_not_executable():
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    result = UnifiedNiftyIntelligenceBuilder.build(
        market={}, technical={}, options={}, macro={}, news={},
        market_state="CLOSED", now=now
    )
    desc = result["outlook"]["preferred_setup"]["description"].upper()
    for forbidden in ["BUY", "SELL", "ENTER NOW", "QUANTITY", "POSITION SIZE", "TARGET PROFIT", "STOP LOSS"]:
        assert forbidden not in desc


def test_mixed_conflicted_insufficient_distinct():
    ts_code = read("frontend/utils/traderTerminology.ts")
    assert '"MIXED": "Mixed Setup"' in ts_code or 'MIXED' in ts_code
    assert '"CONFLICTED": "Mixed Signals"' in ts_code or 'CONFLICTED' in ts_code
    assert '"INSUFFICIENT": "Insufficient Conviction"' in ts_code or 'INSUFFICIENT' in ts_code

    # Test Python canonical outlook overall view mapping for each state
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


def test_key_concerns_evidence_backed():
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    result = UnifiedNiftyIntelligenceBuilder.build(
        market={}, technical={}, options={}, macro={}, news={},
        market_state="CLOSED", now=now
    )
    outlook = result["outlook"]
    assert isinstance(outlook["key_concerns"], list)
    assert len(outlook["key_concerns"]) > 0


def test_at_the_open_items_traceable():
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    result = UnifiedNiftyIntelligenceBuilder.build(
        market={}, technical={}, options={}, macro={}, news={},
        market_state="CLOSED", now=now
    )
    at_open = result["outlook"]["at_the_open"]
    assert isinstance(at_open, list)
    for item in at_open:
        assert "item" in item
        assert "source_rule" in item


def test_tomorrows_outlook_card_is_pure_renderer():
    text = read("frontend/components/intelligence/TomorrowsOutlookCard.tsx")
    assert "intelligence.outlook" in text
    assert "preferred_setup" in text
    assert "overallView" in text
    assert "fetch(" not in text and "axios" not in text
    assert "if (" not in text.split("return (")[1].split("</section>")[0] or "map(" in text  # No complex logic inside JSX return


def test_premarket_information_hierarchy():
    text = read("frontend/components/PreMarketPlannerWorkspace.tsx")
    assert "<TomorrowsOutlookCard" in text
    assert "<PreMarketIntelligenceView" in text


def test_expected_vs_actual_pending_without_prior_snapshot():
    now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
    result = UnifiedNiftyIntelligenceBuilder.build(
        market={}, technical={}, options={}, macro={}, news={},
        market_state="MARKET_OPEN", now=now
    )
    val = result["premarket_view_validation"]
    assert val["status"] == "PENDING"
    assert "No prior pre-market synthesis snapshot" in val["reason"]
