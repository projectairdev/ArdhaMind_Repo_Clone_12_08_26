import pytest
import os
import json
from datetime import datetime, date, timezone, timedelta
from src.market_data.models.canonical_option_chain import CanonicalOptionChainSnapshot, CanonicalOptionStrike, CanonicalOptionLeg
from src.market_data.services.option_chain_aggregator import OptionChainAggregator, OptionChainSummary


IST = timezone(timedelta(hours=5, minutes=30))


@pytest.fixture(autouse=True)
def reset_aggregator_state():
    """Resets in-memory class state and removes test cache files before and after each test."""
    OptionChainAggregator._opening_oi_baseline.clear()
    OptionChainAggregator._baseline_established.clear()
    OptionChainAggregator._loaded_date = None
    for f in ["oi_baseline_20260828.json", "oi_baseline_20260915.json"]:
        p = os.path.join("data", "cache", f)
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass
    yield
    OptionChainAggregator._opening_oi_baseline.clear()
    OptionChainAggregator._baseline_established.clear()
    OptionChainAggregator._loaded_date = None
    for f in ["oi_baseline_20260828.json", "oi_baseline_20260915.json"]:
        p = os.path.join("data", "cache", f)
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass


def test_dte_calculation_normal_and_expiry_day():
    """FIX 8: Verify exact DTE calculation and same-day expiry positive epsilon clamping."""
    # Scenario A: 3 days to expiry (2026-08-28 captured on 2026-08-25 10:00:00 IST)
    captured_3d = datetime(2026, 8, 25, 10, 0, 0, tzinfo=IST)
    strikes = [
        CanonicalOptionStrike(
            strike=24200.0,
            call=CanonicalOptionLeg(canonical_instrument_id="NIFTY24200CE", strike=24200.0, option_type="CE", oi=50000, volume=1000, last_price=150.0, iv=12.5),
            put=CanonicalOptionLeg(canonical_instrument_id="NIFTY24200PE", strike=24200.0, option_type="PE", oi=60000, volume=1200, last_price=120.0, iv=13.0),
        )
    ]
    snapshot_3d = CanonicalOptionChainSnapshot(
        underlying_instrument_id="NIFTY 50",
        underlying_price=24205.0,
        expiry="2026-08-28",
        session_date=date(2026, 8, 25),
        captured_at=captured_3d,
        provider="ZERODHA_KITE",
        strikes=strikes,
    )
    summary_3d = OptionChainAggregator.aggregate(snapshot_3d)
    assert summary_3d.strike_universe is not None
    ce_delta_3d = summary_3d.strike_universe[0]["ce_delta"]
    assert ce_delta_3d is not None and 0.45 < ce_delta_3d < 0.55

    # Scenario B: Expiry Day (2026-08-28 15:29:50 IST, 10 seconds to close)
    captured_exp_day = datetime(2026, 8, 28, 15, 29, 50, tzinfo=IST)
    snapshot_exp = CanonicalOptionChainSnapshot(
        underlying_instrument_id="NIFTY 50",
        underlying_price=24205.0,
        expiry="2026-08-28",
        session_date=date(2026, 8, 28),
        captured_at=captured_exp_day,
        provider="ZERODHA_KITE",
        strikes=strikes,
    )
    summary_exp = OptionChainAggregator.aggregate(snapshot_exp)
    assert summary_exp.strike_universe is not None
    # Greeks should compute cleanly without division-by-zero or NaN
    ce_delta_exp = summary_exp.strike_universe[0]["ce_delta"]
    assert ce_delta_exp is not None
    assert isinstance(ce_delta_exp, float)
    assert not (ce_delta_exp != ce_delta_exp)  # not NaN

    # Scenario C: Post-expiry timestamp (past 15:30:00 on expiry day) - must clamp to EPSILON_YEARS > 0
    captured_post_exp = datetime(2026, 8, 28, 16, 0, 0, tzinfo=IST)
    snapshot_post = CanonicalOptionChainSnapshot(
        underlying_instrument_id="NIFTY 50",
        underlying_price=24205.0,
        expiry="2026-08-28",
        session_date=date(2026, 8, 28),
        captured_at=captured_post_exp,
        provider="ZERODHA_KITE",
        strikes=strikes,
    )
    summary_post = OptionChainAggregator.aggregate(snapshot_post)
    assert summary_post.strike_universe is not None
    assert summary_post.strike_universe[0]["ce_delta"] is not None


def test_delta_oi_baseline_restore_from_disk(tmp_path):
    """FIX 6: Mid-session restart loads disk-persisted baseline instead of resetting to 0.00."""
    session_date = date(2026, 8, 28)
    session_str = "2026-08-28"
    captured_at = datetime(2026, 8, 28, 9, 15, 0, tzinfo=IST)

    # 1. Establish baseline at 09:15:00 with initial OI
    strikes_915 = [
        CanonicalOptionStrike(
            strike=24200.0,
            call=CanonicalOptionLeg(canonical_instrument_id="NIFTY24200CE", strike=24200.0, option_type="CE", oi=100000, volume=1000, last_price=150.0, iv=12.5),
            put=CanonicalOptionLeg(canonical_instrument_id="NIFTY24200PE", strike=24200.0, option_type="PE", oi=80000, volume=1200, last_price=120.0, iv=13.0),
        )
    ]
    snapshot_915 = CanonicalOptionChainSnapshot(
        underlying_instrument_id="NIFTY 50",
        underlying_price=24200.0,
        expiry="2026-08-28",
        session_date=session_date,
        captured_at=captured_at,
        provider="ZERODHA_KITE",
        strikes=strikes_915,
    )
    OptionChainAggregator.take_opening_baseline_snapshot(snapshot_915)

    # Verify baseline in-memory
    b = OptionChainAggregator.get_morning_baseline("2026-08-28", 24200.0, session_str)
    assert b == {"CE": 100000, "PE": 80000}

    # 2. Simulate server restart: completely clear in-memory class attributes
    OptionChainAggregator._opening_oi_baseline.clear()
    OptionChainAggregator._baseline_established.clear()
    OptionChainAggregator._loaded_date = None

    # 3. Process 11:30:00 tick with changed OI: CE increased by +15,000, PE increased by +5,000
    captured_1130 = datetime(2026, 8, 28, 11, 30, 0, tzinfo=IST)
    strikes_1130 = [
        CanonicalOptionStrike(
            strike=24200.0,
            call=CanonicalOptionLeg(canonical_instrument_id="NIFTY24200CE", strike=24200.0, option_type="CE", oi=115000, volume=5000, last_price=165.0, iv=12.5),
            put=CanonicalOptionLeg(canonical_instrument_id="NIFTY24200PE", strike=24200.0, option_type="PE", oi=85000, volume=4000, last_price=110.0, iv=13.0),
        )
    ]
    snapshot_1130 = CanonicalOptionChainSnapshot(
        underlying_instrument_id="NIFTY 50",
        underlying_price=24220.0,
        expiry="2026-08-28",
        session_date=session_date,
        captured_at=captured_1130,
        provider="ZERODHA_KITE",
        strikes=strikes_1130,
    )

    summary_1130 = OptionChainAggregator.aggregate(snapshot_1130)
    assert summary_1130.strike_universe is not None
    row = summary_1130.strike_universe[0]
    # ΔOI should accurately report +15000 and +5000 (NOT +0.00 from wipe)
    assert row["ce_change_oi"] == 15000
    assert row["pe_change_oi"] == 5000


def test_new_strike_mid_day_marked_no_baseline():
    """FIX 7: Strikes entering range mid-day are marked NO BASELINE (NEW STRIKE) rather than computing against now."""
    session_date = date(2026, 8, 28)
    session_str = "2026-08-28"

    # 1. 09:15 baseline only contains 24200 strike
    strikes_915 = [
        CanonicalOptionStrike(
            strike=24200.0,
            call=CanonicalOptionLeg(canonical_instrument_id="NIFTY24200CE", strike=24200.0, option_type="CE", oi=100000, volume=1000, last_price=150.0, iv=12.5),
            put=CanonicalOptionLeg(canonical_instrument_id="NIFTY24200PE", strike=24200.0, option_type="PE", oi=80000, volume=1200, last_price=120.0, iv=13.0),
        )
    ]
    snapshot_915 = CanonicalOptionChainSnapshot(
        underlying_instrument_id="NIFTY 50",
        underlying_price=24200.0,
        expiry="2026-08-28",
        session_date=session_date,
        captured_at=datetime(2026, 8, 28, 9, 15, 0, tzinfo=IST),
        provider="ZERODHA_KITE",
        strikes=strikes_915,
    )
    OptionChainAggregator.take_opening_baseline_snapshot(snapshot_915)

    # 2. At 13:00, market trends and 24400 enters the strike universe for the first time
    strikes_1300 = [
        CanonicalOptionStrike(
            strike=24200.0,
            call=CanonicalOptionLeg(canonical_instrument_id="NIFTY24200CE", strike=24200.0, option_type="CE", oi=120000, volume=8000, last_price=180.0, iv=12.5),
            put=CanonicalOptionLeg(canonical_instrument_id="NIFTY24200PE", strike=24200.0, option_type="PE", oi=70000, volume=6000, last_price=90.0, iv=13.0),
        ),
        CanonicalOptionStrike(
            strike=24400.0,
            call=CanonicalOptionLeg(canonical_instrument_id="NIFTY24400CE", strike=24400.0, option_type="CE", oi=45000, volume=3000, last_price=45.0, iv=13.2),
            put=CanonicalOptionLeg(canonical_instrument_id="NIFTY24400PE", strike=24400.0, option_type="PE", oi=30000, volume=2500, last_price=220.0, iv=14.0),
        ),
    ]
    snapshot_1300 = CanonicalOptionChainSnapshot(
        underlying_instrument_id="NIFTY 50",
        underlying_price=24380.0,
        expiry="2026-08-28",
        session_date=session_date,
        captured_at=datetime(2026, 8, 28, 13, 0, 0, tzinfo=IST),
        provider="ZERODHA_KITE",
        strikes=strikes_1300,
    )

    summary_1300 = OptionChainAggregator.aggregate(snapshot_1300)
    assert summary_1300.strike_universe is not None
    row_24200 = next(r for r in summary_1300.strike_universe if r["strike"] == 24200.0)
    row_24400 = next(r for r in summary_1300.strike_universe if r["strike"] == 24400.0)

    # 24200 has valid ΔOI (+20,000 CE, -10,000 PE)
    assert row_24200["ce_change_oi"] == 20000
    assert row_24200["pe_change_oi"] == -10000

    # 24400 was not in 09:15 baseline, so it must read "NO BASELINE (NEW STRIKE)"
    assert row_24400["ce_change_oi"] == "NO BASELINE (NEW STRIKE)"
    assert row_24400["pe_change_oi"] == "NO BASELINE (NEW STRIKE)"


def test_pending_baseline_before_snapshot():
    """FIX 6: Before 09:15 baseline is taken, ΔOI reports PENDING BASELINE."""
    session_date = date(2026, 8, 28)
    strikes = [
        CanonicalOptionStrike(
            strike=24200.0,
            call=CanonicalOptionLeg(canonical_instrument_id="NIFTY24200CE", strike=24200.0, option_type="CE", oi=50000, volume=0, last_price=150.0, iv=12.5),
            put=CanonicalOptionLeg(canonical_instrument_id="NIFTY24200PE", strike=24200.0, option_type="PE", oi=60000, volume=0, last_price=120.0, iv=13.0),
        )
    ]
    # Snapshot at 08:45 IST (pre-market, no baseline taken yet)
    snapshot_pre = CanonicalOptionChainSnapshot(
        underlying_instrument_id="NIFTY 50",
        underlying_price=24200.0,
        expiry="2026-08-28",
        session_date=session_date,
        captured_at=datetime(2026, 8, 28, 8, 45, 0, tzinfo=IST),
        provider="ZERODHA_KITE",
        strikes=strikes,
    )
    summary_pre = OptionChainAggregator.aggregate(snapshot_pre)
    assert summary_pre.strike_universe is not None
    assert summary_pre.strike_universe[0]["ce_change_oi"] == "PENDING BASELINE"
    assert summary_pre.strike_universe[0]["pe_change_oi"] == "PENDING BASELINE"
