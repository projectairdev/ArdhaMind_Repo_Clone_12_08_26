import pytest
from src.application.workstation_state_service import WorkstationStateService


def test_cross_workspace_field_consistency():
    """
    Assert that canonicalState contains matching, mutually consistent data points
    which are shared across NIFTY, METRICS, and OPTIONS tabs.
    """
    payload = {
        "marketContext": {
            "current_spot": 24287.65,
            "spot": 24287.65,
            "previous_close": 24366.00,
            "spot_change": -78.35,
            "spot_change_pct": -0.3215,
            "vwap": 24408.25,
            "atr": 182.40,
            "timestamp": "2026-08-17T15:30:00Z",
            "observed_at": "2026-08-17T15:30:00Z",
            "breadth": {
                "advances": 18,
                "declines": 31,
                "unchanged": 1,
            },
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
            "india_vix": {
                "value": 11.33,
                "previous_close": 11.31,
                "change": 0.02,
                "change_pct": 0.18,
            },
            "institutional_flows": [
                {"dataset_type": "FII_CASH", "net_value": -2535.1, "date": "17-Aug-2026"},
                {"dataset_type": "DII_CASH", "net_value": 5101.5, "date": "17-Aug-2026"},
            ],
        },
    }

    canonical = WorkstationStateService.build_canonical_state(payload)

    market = canonical.market_data or {}
    options = canonical.option_intelligence or {}
    macro = canonical.macro_intelligence or {}

    # 1. Spot Consistency
    market_spot = market.get("current_spot") or market.get("spot")
    option_spot = options.get("underlying_spot")
    assert float(market_spot) == float(option_spot) == 24287.65

    # 2. Previous Close & Change Math
    prev_close = market.get("previous_close")
    change = market.get("spot_change")
    change_pct = market.get("spot_change_pct")

    expected_change = round(float(market_spot) - float(prev_close), 2)
    expected_pct = round((expected_change / float(prev_close)) * 100.0, 2)
    assert round(float(change), 2) == expected_change == -78.35
    assert round(float(change_pct), 2) == expected_pct == -0.32

    # 3. India VIX Math
    vix_dict = macro.get("india_vix") or {}
    v_val = float(vix_dict["value"])
    v_prev = float(vix_dict["previous_close"])
    v_chg = round(v_val - v_prev, 2)
    v_pct = round((v_chg / v_prev) * 100.0, 2)
    assert round(float(vix_dict["change"]), 2) == v_chg == 0.02
    assert round(float(vix_dict["change_pct"]), 2) == v_pct == 0.18

    # 4. Institutional Flows
    flows = macro.get("institutional_flows") or []
    fii_flow = next(f for f in flows if f.get("dataset_type") == "FII_CASH")
    dii_flow = next(f for f in flows if f.get("dataset_type") == "DII_CASH")
    assert fii_flow["net_value"] == -2535.1
    assert dii_flow["net_value"] == 5101.5
    assert "2026" in str(fii_flow["date"])
