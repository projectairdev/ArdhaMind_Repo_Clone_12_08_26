import subprocess
from datetime import date
from src.utils.time_utils import is_trading_day, previous_trading_day, next_trading_day
from src.intelligence_engine.today_analysis_engine import TodayAnalysisEngine


def test_midnight_session_identity_invariant():
    """1-4: Midnight 00:05 IST calendar 20 Aug -> Completed=19 Aug, Target=20 Aug, Prev=18 Aug."""
    calendar_date = date(2026, 8, 20)
    
    # Target trading session for overnight pre-market/planning is 20 Aug
    target_session = calendar_date if is_trading_day(calendar_date) else next_trading_day(calendar_date)
    
    # Latest completed trading session is previous trading day of target date
    completed_session = previous_trading_day(target_session)
    
    # Previous completed session is previous trading day of completed date
    previous_completed_session = previous_trading_day(completed_session)

    assert str(completed_session) == "2026-08-19"
    assert str(target_session) == "2026-08-20"
    assert str(previous_completed_session) == "2026-08-18"
    assert target_session > completed_session > previous_completed_session


def test_post_ohlc_invariants():
    """10-12: POST OHLC same-session bounds: Low <= Close <= High and Range >= 0."""
    state = {
        "market_session": {"status": "CLOSED", "session_date": "2026-08-19"},
        "market_data": {
            "current_spot": 24025.65,
            "previous_close": 24150.00,
            "open": 24152.05,
            "high": 24172.85,
            "low": 24025.65,
        }
    }
    report = TodayAnalysisEngine.analyze(state, [])
    stats = report.session_statistics
    
    spot = stats.get("spot")
    high = stats.get("high")
    low = stats.get("low")
    open_price = stats.get("open")
    day_range = stats.get("range")

    assert low <= spot <= high, f"Close ({spot}) must be within [Low ({low}), High ({high})]"
    assert low <= open_price <= high, f"Open ({open_price}) must be within [Low ({low}), High ({high})]"
    assert high >= low, "High must be >= Low"
    assert day_range == round(high - low, 2)


def test_weekend_rollover_safety():
    """13: Saturday calendar date -> Completed = Friday, Target = Monday."""
    saturday = date(2026, 8, 22) # Saturday
    target = next_trading_day(saturday)
    completed = previous_trading_day(target)

    assert saturday.weekday() == 5 # Saturday
    assert str(completed) == "2026-08-21" # Friday
    assert str(target) == "2026-08-24" # Monday
    assert target > completed


def test_production_untouched():
    """15: Verify production /opt/ArdhaMind status remains 100% clean."""
    res = subprocess.run(["git", "-C", "/opt/ArdhaMind", "status", "--porcelain"], capture_output=True, text=True)
    assert res.stdout.strip() == "", f"Production git tree must be clean, got: {res.stdout}"
