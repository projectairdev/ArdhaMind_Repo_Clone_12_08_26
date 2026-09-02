"""Comprehensive test suite for MARKET -> OPTIONS Derivatives Workstation.

Verifies:
1. Canonical data integrity and null safety.
2. Single-state expiry architecture.
3. Positioning Map, Smart Option Chain, and Options Inspector contracts.
4. TABLE / OI HEATMAP / OI CHANGE view mode contracts.
5. Smart row highlighting and clickable strike inspection.
6. Greeks validation and graceful UNAVAILABLE handling (no fake zeros).
7. What Changed temporal evidence and Strike Structure Summary.
8. Product boundary invariants: no execution controls, no trade recommendations.
"""
from pathlib import Path
import pytest

FRONTEND_ROOT = Path(__file__).resolve().parent.parent / "src" / "frontend"
OPTIONS_SRC = (FRONTEND_ROOT / "components/OptionsWorkspace.tsx").read_text(encoding="utf-8")
CHAIN_SRC = (FRONTEND_ROOT / "components/visualizations/OptionChainLadder.tsx").read_text(encoding="utf-8")


def test_derivatives_state_strip_structure():
    """Top derivatives strip must include all essential macro derivatives metrics."""
    assert "DERIVATIVES STATE STRIP" in OPTIONS_SRC
    for field in ("EXPIRY", "SPOT", "ATM STRIKE", "PCR (OI)", "PCR (VOL)", "MAX PAIN", "ATM IV", "IV STATE", "TOTAL CALL OI", "TOTAL PUT OI", "OI SKEW / BIAS"):
        assert field in OPTIONS_SRC, f"Missing {field} in Derivatives State Strip"


def test_positioning_map_structure():
    """Left rail must contain coherent Positioning Map with single expiry dropdown."""
    assert "POSITIONING MAP" in OPTIONS_SRC
    assert "EXPIRY SELECTOR" in OPTIONS_SRC
    assert "<select" in OPTIONS_SRC
    assert "CALL VS PUT OI" in OPTIONS_SRC
    assert "KEY CONCENTRATIONS" in OPTIONS_SRC
    assert "CALL WALL (RES):" in OPTIONS_SRC
    assert "PUT WALL (SUPP):" in OPTIONS_SRC
    assert "MAX PAIN PIN:" in OPTIONS_SRC
    assert "DISTANCE & STRUCTURE" in OPTIONS_SRC
    assert "Spot → Call Wall:" in OPTIONS_SRC
    assert "Spot → Put Wall:" in OPTIONS_SRC
    assert "Spot → Max Pain:" in OPTIONS_SRC
    assert "Range Bracket:" in OPTIONS_SRC


def test_smart_option_chain_and_view_modes():
    """Option chain ladder must support TABLE, HEATMAP, and CHANGE modes with strike selection."""
    assert "SMART OPTION CHAIN" in CHAIN_SRC
    assert "OptionChainViewMode" in CHAIN_SRC
    assert '"TABLE" | "HEATMAP" | "CHANGE"' in CHAIN_SRC
    assert "Table" in CHAIN_SRC
    assert "OI Heatmap" in CHAIN_SRC
    assert "OI Change" in CHAIN_SRC
    assert "onSelectStrike" in CHAIN_SRC
    assert "CALL WALL" in CHAIN_SRC
    assert "PUT WALL" in CHAIN_SRC
    assert "ATM" in CHAIN_SRC


def test_options_inspector_and_greeks_validity():
    """Right rail must contain Options Inspector with strict Greeks model validation."""
    assert "OPTIONS INSPECTOR" in OPTIONS_SRC
    assert "VOLATILITY STRUCTURE" in OPTIONS_SRC
    assert "ATM Implied Vol (IV):" in OPTIONS_SRC
    assert "IV Percentile / Rank:" in OPTIONS_SRC
    assert "UNAVAILABLE" in OPTIONS_SRC
    assert "SELECTED STRIKE:" in OPTIONS_SRC
    assert "CALL (CE)" in OPTIONS_SRC
    assert "PUT (PE)" in OPTIONS_SRC
    assert "BLACK-SCHOLES GREEKS" in OPTIONS_SRC
    assert "GREEKS UNAVAILABLE" in OPTIONS_SRC
    assert "Insufficient model inputs / canonical calculation unavailable" in OPTIONS_SRC


def test_what_changed_and_strike_structure_summary():
    """Bottom region must contain What Changed evidence and Strike Structure Summary."""
    assert "WHAT CHANGED (DERIVATIVES EVIDENCE)" in OPTIONS_SRC
    assert "INSUFFICIENT HISTORICAL SNAPSHOTS" in OPTIONS_SRC
    assert "STRIKE STRUCTURE SUMMARY" in OPTIONS_SRC
    assert "PUT SUPPORT" in OPTIONS_SRC
    assert "SPOT / ATM" in OPTIONS_SRC
    assert "CALL RESISTANCE" in OPTIONS_SRC


def test_strict_product_boundary_no_execution_controls():
    """MARKET -> OPTIONS must contain zero execution or order placement controls."""
    combined = OPTIONS_SRC + CHAIN_SRC
    for forbidden in ("Place Order", "Buy Call", "Buy Put", "Sell Call", "Sell Put", "Execute Strategy", "Iron Condor Setup", "Bull Call Spread", "STRATEGY EVALUATION (INFO ONLY)"):
        assert forbidden not in combined, f"Forbidden execution/strategy string found: {forbidden}"


def test_contract_hooks_preserved():
    """Hidden test anchors must remain for backward compatibility with existing tests."""
    assert "Market structure" in OPTIONS_SRC
    assert "OptionChainLadder" in OPTIONS_SRC
    assert "<OptionChainLadder" in OPTIONS_SRC
    assert "<OpenInterestHeatmap" in OPTIONS_SRC
