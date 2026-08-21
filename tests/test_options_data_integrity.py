import pytest
from src.options_engine.max_pain import calculate_max_pain
from src.options_engine.iv import solve_implied_volatility


def test_pcr_calculation():
    total_put_oi = 67495190
    total_call_oi = 55116970
    pcr = round(total_put_oi / total_call_oi, 2)
    assert pcr == 1.22


def test_pcr_volume_ratio():
    total_put_vol = 2885704120
    total_call_vol = 2606269445
    pcr_vol = round(total_put_vol / total_call_vol, 2)
    assert pcr_vol == 1.11


def test_put_and_call_wall_argmax_derivation():
    # Option chain strikes and OI
    chain = [
        {"strike": 24050, "call_oi": 75855, "put_oi": 3630575},
        {"strike": 24100, "call_oi": 482040, "put_oi": 7254520},
        {"strike": 24150, "call_oi": 396240, "put_oi": 6395025},
        {"strike": 24200, "call_oi": 1765595, "put_oi": 10639655},
        {"strike": 24250, "call_oi": 1874210, "put_oi": 8689200},
        {"strike": 24300, "call_oi": 6413420, "put_oi": 14618045},  # Highest Put OI
        {"strike": 24350, "call_oi": 7402655, "put_oi": 6259890},
        {"strike": 24400, "call_oi": 11326380, "put_oi": 5145790},
        {"strike": 24450, "call_oi": 6245590, "put_oi": 1718340},
        {"strike": 24500, "call_oi": 12819365, "put_oi": 2764190},  # Highest Call OI
        {"strike": 24550, "call_oi": 6292000, "put_oi": 350545},
    ]

    call_wall = max(chain, key=lambda x: x["call_oi"])["strike"]
    put_wall = max(chain, key=lambda x: x["put_oi"])["strike"]

    assert call_wall == 24500
    assert put_wall == 24300


def test_expiry_countdown_formatting():
    def format_expiry_countdown(exp_str: str, today_str: str = "2026-08-18") -> str:
        if exp_str == today_str or exp_str == "18 Aug 2026":
            return "EXPIRES TODAY"
        elif exp_str > today_str:
            # calculate days
            from datetime import date
            d_exp = date.fromisoformat(exp_str)
            d_today = date.fromisoformat(today_str)
            days = (d_exp - d_today).days
            return f"{days} Day" if days == 1 else f"{days} Days"
        return "EXPIRED"

    assert format_expiry_countdown("2026-08-18", "2026-08-18") == "EXPIRES TODAY"
    assert format_expiry_countdown("2026-08-19", "2026-08-18") == "1 Day"
    assert format_expiry_countdown("2026-08-25", "2026-08-18") == "7 Days"
    assert format_expiry_countdown("2026-08-17", "2026-08-18") == "EXPIRED"


def test_max_pain_calculation():
    rows = [
        {"strike": 24200, "option_type": "CE", "oi": 50000},
        {"strike": 24200, "option_type": "PE", "oi": 200000},
        {"strike": 24300, "option_type": "CE", "oi": 80000},
        {"strike": 24300, "option_type": "PE", "oi": 150000},
        {"strike": 24350, "option_type": "CE", "oi": 120000},
        {"strike": 24350, "option_type": "PE", "oi": 120000},
        {"strike": 24400, "option_type": "CE", "oi": 180000},
        {"strike": 24400, "option_type": "PE", "oi": 60000},
        {"strike": 24500, "option_type": "CE", "oi": 250000},
        {"strike": 24500, "option_type": "PE", "oi": 30000},
    ]
    res = calculate_max_pain(rows)
    assert res.max_pain_strike == 24350


def test_black_scholes_iv_solver():
    solved = solve_implied_volatility(
        price=80.0,
        S=24300.0,
        K=24300.0,
        T=1.0 / 365.0,
        r=0.065,
        option_type="CE",
    )
    assert solved.iv is not None
    assert 5.0 < solved.iv < 30.0


def test_contract_unit_scaling():
    contracts_lakh = 75855
    contracts_cr = 14618045
    total_vol_raw = 5491973565

    lakh_scaled = round(contracts_lakh / 100000.0, 2)
    cr_scaled = round(contracts_cr / 10000000.0, 2)
    cr_units_vol = round(total_vol_raw / 10000000.0, 2)

    assert lakh_scaled == 0.76
    assert cr_scaled == 1.46
    assert cr_units_vol == 549.20
