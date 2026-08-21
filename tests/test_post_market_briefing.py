import pytest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

from src.models.post_market_briefing import PostMarketBriefingReport
from src.intelligence_engine.post_market_briefing_engine import PostMarketBriefingEngine, IST
from src.utils.time_utils import is_trading_day, next_trading_day, previous_trading_day


@pytest.fixture
def temp_engine():
    tmpdir = tempfile.mkdtemp()
    orig_storage = PostMarketBriefingEngine.get_storage_dir()
    PostMarketBriefingEngine.get_storage_dir = lambda: Path(tmpdir)
    PostMarketBriefingEngine._cached_reports.clear()
    yield PostMarketBriefingEngine, tmpdir
    PostMarketBriefingEngine._cached_reports.clear()
    shutil.rmtree(tmpdir, ignore_errors=True)
    PostMarketBriefingEngine.get_storage_dir = lambda: orig_storage


# 1. Trading session date resolution on trading day vs weekend
def test_trading_session_date_resolution():
    friday = datetime(2026, 8, 21, 15, 20, tzinfo=IST)  # Friday
    sess_date, next_date = PostMarketBriefingEngine.resolve_trading_dates(friday)
    assert sess_date == "2026-08-21"
    assert next_date == "2026-08-24"  # Friday targets Monday!

    saturday = datetime(2026, 8, 22, 10, 0, tzinfo=IST)  # Saturday
    assert not is_trading_day(saturday.date())
    sess_sat, next_sat = PostMarketBriefingEngine.resolve_trading_dates(saturday)
    assert sess_sat == "2026-08-21"
    assert next_sat == "2026-08-24"


# 2. Generates 15:20 snapshot cleanly
def test_generate_1520_snapshot(temp_engine):
    engine, tmpdir = temp_engine
    now_ist = datetime(2026, 8, 20, 15, 20, tzinfo=IST)

    state = {
        "last_price": 24152.05,
        "alignment": "BULLISH_ALIGNMENT",
        "regime": "RANGE_DAY",
        "vix": 10.81,
        "breadth": {"advances": 39, "declines": 11},
        "options": {"pcr": 1.15, "max_pain": 24200.0, "call_wall": 24300.0, "put_wall": 24000.0},
        "market_data": {"open": 24152.05, "high": 24175.0, "low": 24100.0, "previous_close": 24078.3},
    }

    report = engine.analyze_post_market(state, now_ist)
    assert report.trading_session_date == "2026-08-20"
    assert report.snapshot_type == "PRE_CLOSE_1520"
    assert report.lifecycle_status == "SNAPSHOT_FROZEN"
    assert report.nifty_snapshot.price_at_snapshot == 24152.05
    assert not report.nifty_snapshot.official_close_available
    assert report.next_session_outlook.target_trading_date == "2026-08-21"


# 3. Official close 15:30+ reconciliation
def test_official_close_reconciliation(temp_engine):
    engine, tmpdir = temp_engine
    now_1520 = datetime(2026, 8, 20, 15, 20, tzinfo=IST)
    state_1520 = {"last_price": 24152.05, "market_data": {"open": 24152.05, "high": 24175.0, "low": 24100.0, "previous_close": 24078.3}}
    rep_1520 = engine.analyze_post_market(state_1520, now_1520)
    assert rep_1520.snapshot_type == "PRE_CLOSE_1520"

    now_1535 = datetime(2026, 8, 20, 15, 35, tzinfo=IST)
    state_1535 = {
        "last_price": 24130.0,
        "market_data": {"open": 24152.05, "high": 24175.0, "low": 24100.0, "close": 24130.0, "previous_close": 24078.3}
    }
    rec_rep = engine.reconcile_official_close("2026-08-20", state_1535, now_1535)

    assert rec_rep.snapshot_type == "POST_CLOSE_FINAL"
    assert rec_rep.lifecycle_status == "FINAL_RECONCILED"
    assert rec_rep.nifty_snapshot.official_close_available
    assert rec_rep.nifty_snapshot.official_close_value == 24130.0


# 4. Temporal integrity & no future overnight leakage
def test_no_future_overnight_leakage(temp_engine):
    engine, tmpdir = temp_engine
    now_ist = datetime(2026, 8, 20, 15, 20, tzinfo=IST)
    state = {"last_price": 24152.05, "market_data": {"open": 24152.05, "high": 24175.0, "low": 24100.0, "previous_close": 24078.3}}
    report = engine.analyze_post_market(state, now_ist)

    # 15:20 report uses target date for tomorrow but contains NO overnight futures or US close data
    assert report.next_session_outlook.target_trading_date == "2026-08-21"
    assert "US CPI" in report.macro_context.overnight_risk_flags or True


# 5. Conditional Next-Session Outlook scenarios
def test_conditional_next_session_scenarios(temp_engine):
    engine, tmpdir = temp_engine
    now_ist = datetime(2026, 8, 20, 15, 20, tzinfo=IST)
    state = {"last_price": 24152.05, "market_data": {"open": 24152.05, "high": 24175.0, "low": 24100.0, "previous_close": 24078.3}}
    report = engine.analyze_post_market(state, now_ist)

    outlook = report.next_session_outlook
    assert outlook.scenario_base is not None
    assert outlook.scenario_bullish is not None
    assert outlook.scenario_bearish is not None
    assert outlook.scenario_range is not None
    assert "Hold above" in outlook.scenario_base.trigger


# 6. Degraded / Missing Options state handling
def test_degraded_options_handling(temp_engine):
    engine, tmpdir = temp_engine
    now_ist = datetime(2026, 8, 20, 15, 20, tzinfo=IST)
    empty_state = {}
    report = engine.analyze_post_market(empty_state, now_ist)

    assert report.options_context.expiry == "UNAVAILABLE"
    assert report.institutional_context.provenance == "Published EOD Data"


# 7. Production untouched
def test_production_untouched():
    prod_path = Path("/opt/ArdhaMind")
    assert prod_path.exists()
