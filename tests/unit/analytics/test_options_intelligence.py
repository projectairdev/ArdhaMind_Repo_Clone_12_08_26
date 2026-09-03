from __future__ import annotations

from datetime import date, datetime, timezone
import pytest

from src.analytics.options.models import (
    BuildupType,
    OptionLiquidityLevel,
    OptionsConfirmationBias,
    StrikeStrengthClass,
)
from src.analytics.options.options_intelligence_engine import OptionsIntelligenceEngine
from src.market_data.models.canonical_option_chain import (
    CanonicalOptionChainSnapshot,
    CanonicalOptionLeg,
    CanonicalOptionStrike,
)
from src.market_data.models.quality_enums import OptionType


def _make_chain(spot_price: float = 24500.0) -> CanonicalOptionChainSnapshot:
    strikes = []
    base_strikes = [24300, 24400, 24500, 24600, 24700]
    # Put wall at 24400 (heavy Put OI), Call wall at 24600 (heavy Call OI)
    call_ois = [10000, 25000, 80000, 150000, 90000]
    put_ois = [20000, 140000, 95000, 30000, 15000]

    for i, s in enumerate(base_strikes):
        c_leg = CanonicalOptionLeg(
            canonical_instrument_id=f"OPT:NFO:NIFTY:2026-09-03:{s}:CE",
            strike=float(s),
            option_type=OptionType.CE,
            last_price=max(10.0, spot_price - s + 100.0),
            oi=call_ois[i],
            volume=5000,
            iv=14.0,
            delta=0.5,
            bid=99.0,
            ask=100.0,
        )
        p_leg = CanonicalOptionLeg(
            canonical_instrument_id=f"OPT:NFO:NIFTY:2026-09-03:{s}:PE",
            strike=float(s),
            option_type=OptionType.PE,
            last_price=max(10.0, s - spot_price + 100.0),
            oi=put_ois[i],
            volume=5000,
            iv=14.5,
            delta=-0.5,
            bid=99.0,
            ask=100.0,
        )
        strikes.append(CanonicalOptionStrike(strike=float(s), call=c_leg, put=p_leg))

    return CanonicalOptionChainSnapshot(
        underlying_instrument_id="IDX:NSE:NIFTY_50",
        underlying_price=spot_price,
        expiry="2026-09-03",
        session_date=date(2026, 8, 28),
        captured_at=datetime.now(timezone.utc),
        provider="DHAN",
        strikes=strikes,
    )


def test_0_hand_calculated_max_pain():
    """
    Mathematical Hand-Calculation Proof:
    Strikes: [100.0, 110.0, 120.0]
    Strike 100: Call OI = 100, Put OI = 0
    Strike 110: Call OI = 50,  Put OI = 50
    Strike 120: Call OI = 0,   Put OI = 100

    Candidate Settlements (S):
    1. S = 100.0:
       - Call Payout = 0 (all OTM)
       - Put Payout  = 50 * (110 - 100) + 100 * (120 - 100) = 500 + 2000 = 2500
       Total Loss = 2500

    2. S = 110.0:
       - Call Payout = 100 * (110 - 100) = 1000
       - Put Payout  = 100 * (120 - 110) = 1000
       Total Loss = 2000

    3. S = 120.0:
       - Call Payout = 100 * (120 - 100) + 50 * (120 - 110) = 2000 + 500 = 2500
       - Put Payout  = 0 (all OTM)
       Total Loss = 2500

    Minimum Total Loss occurs at S = 110.0 (Loss = 2000). Max Pain MUST be 110.0!
    """
    s100 = CanonicalOptionStrike(
        strike=100.0,
        call=CanonicalOptionLeg("OPT:NFO:TEST:100:CE", 100.0, OptionType.CE, 10.0, oi=100),
        put=CanonicalOptionLeg("OPT:NFO:TEST:100:PE", 100.0, OptionType.PE, 1.0, oi=0),
    )
    s110 = CanonicalOptionStrike(
        strike=110.0,
        call=CanonicalOptionLeg("OPT:NFO:TEST:110:CE", 110.0, OptionType.CE, 5.0, oi=50),
        put=CanonicalOptionLeg("OPT:NFO:TEST:110:PE", 110.0, OptionType.PE, 5.0, oi=50),
    )
    s120 = CanonicalOptionStrike(
        strike=120.0,
        call=CanonicalOptionLeg("OPT:NFO:TEST:120:CE", 120.0, OptionType.CE, 1.0, oi=0),
        put=CanonicalOptionLeg("OPT:NFO:TEST:120:PE", 120.0, OptionType.PE, 10.0, oi=100),
    )

    max_pain = OptionsIntelligenceEngine.calculate_max_pain([s100, s110, s120])
    assert max_pain == 110.0


def test_1_max_pain_and_walls():
    chain = _make_chain(spot_price=24500.0)
    max_pain = OptionsIntelligenceEngine.calculate_max_pain(chain.strikes)
    assert 24400.0 <= max_pain <= 24600.0

    call_wall = max(chain.strikes, key=lambda s: s.call.oi).strike
    put_wall = max(chain.strikes, key=lambda s: s.put.oi).strike
    assert call_wall == 24600.0
    assert put_wall == 24400.0


def test_2_position_buildup_classification():
    # 1. Fresh Call Writing: Price down (-5.0), OI up (+5000)
    b1 = OptionsIntelligenceEngine.classify_buildup(
        current_price=100.0,
        prior_price=105.0,
        current_oi=55000,
        prior_oi=50000,
        is_call=True,
    )
    assert b1 == BuildupType.FRESH_CALL_WRITING

    # 2. Fresh Put Writing: Price down (-4.0), OI up (+8000)
    b2 = OptionsIntelligenceEngine.classify_buildup(
        current_price=60.0,
        prior_price=64.0,
        current_oi=88000,
        prior_oi=80000,
        is_call=False,
    )
    assert b2 == BuildupType.FRESH_PUT_WRITING

    # 3. Short Covering: Price up (+10.0), OI down (-4000)
    b3 = OptionsIntelligenceEngine.classify_buildup(
        current_price=120.0,
        prior_price=110.0,
        current_oi=46000,
        prior_oi=50000,
        is_call=True,
    )
    assert b3 == BuildupType.SHORT_COVERING

    # 4. Insufficient data: None values
    b4 = OptionsIntelligenceEngine.classify_buildup(
        current_price=100.0,
        prior_price=None,
        current_oi=50000,
        prior_oi=None,
        is_call=True,
    )
    assert b4 == BuildupType.INSUFFICIENT_DATA


def test_3_options_confirmation_synthesis():
    chain = _make_chain(spot_price=24520.0)
    ctx = OptionsIntelligenceEngine.analyze(chain)

    assert ctx.atm_strike == 24500.0
    assert ctx.call_wall == 24600.0
    assert ctx.put_wall == 24400.0
    assert ctx.pcr > 0.0
    assert len(ctx.strike_universe) == 5
    assert ctx.bias in (OptionsConfirmationBias.BULLISH, OptionsConfirmationBias.NEUTRAL, OptionsConfirmationBias.BEARISH, OptionsConfirmationBias.CONFLICTED)
    assert len(ctx.supporting_factors) > 0 or len(ctx.contradicting_factors) > 0
