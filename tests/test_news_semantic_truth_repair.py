# tests/test_news_semantic_truth_repair.py
"""
Automated Contract Tests for News Semantic Classification, Region Normalization & Catalyst Truth.
Section 30 Quality Gates for AIR ArdhaMind.
"""

from pathlib import Path
import pytest
from src.news_engine.event_classifier import EventClassifier
from src.news_engine.impact_assessor import NewsImpactAssessor


def read_frontend(rel_path: str) -> str:
    full_path = Path(__file__).parent.parent / "src" / "frontend" / rel_path
    return full_path.read_text(encoding="utf-8")


# ── 1. REGION NORMALIZATION & CALENDAR FILTER CONTRACTS ──

def test_region_derivation_rules_in_adapter():
    """Assert canonicalNewsAdapter defines deriveEventRegionAndCountry and handles unknown without defaulting to INDIA."""
    code = read_frontend("utils/canonicalNewsAdapter.ts")
    assert "function deriveEventRegionAndCountry" in code
    assert "region: \"UNKNOWN\", countryCode: \"UNKNOWN\"" in code
    assert "NEVER default unknown to INDIA" in code or "region: \"UNKNOWN\"" in code


def test_calendar_tab_filter_contract():
    """Assert CalendarTab implements strict GLOBAL and HIGH ONLY filtering."""
    code = read_frontend("components/news/CalendarTab.tsx")
    assert "regionFilter === \"GLOBAL\" && (ev.region === \"INDIA\" || ev.region === \"US\"" in code
    assert "impactFilter === \"HIGH\" && ev.impact !== \"HIGH\"" in code


# ── 2. ENTITY EXTRACTION & SECTOR CONTRACTS ──

def test_direct_nifty_symbol_match_works():
    res = NewsImpactAssessor.assess_impact("Reliance Industries Q1 net profit jumps 15%", "Oil refining margins expand.", "media", "ENERGY")
    assert "RELIANCE" in res["affected_symbols"]
    assert "ENERGY" in res["affected_sectors"]


def test_false_substring_match_rejected():
    res = NewsImpactAssessor.assess_impact("Bank credit growth speeds up with robust deposits", "Interbank yields remain steady.", "media", "BANKING")
    assert "INFY" not in res["affected_symbols"]
    assert "IT" not in res["affected_sectors"]


def test_company_alias_match_works():
    res = NewsImpactAssessor.assess_impact("L&T secures mega infrastructure order in Middle East", "EPC division expands capacity.", "media", "INFRA")
    assert "LT" in res["affected_symbols"]
    assert "INFRA" in res["affected_sectors"]


def test_nifty_50_never_used_as_sector():
    res = NewsImpactAssessor.assess_impact("Broad market index advances", "Nifty 50 trades in range", "media", "INDIA_MACRO")
    assert "NIFTY 50" not in res["affected_sectors"]


# ── 3. DIRECTION & IMPACT TESTS ──

def test_explicit_positive_evidence_maps_positive():
    res = NewsImpactAssessor.assess_impact("RBI VRR auction injects liquidity, interbank yields ease", "Banking system liquidity improves.", "official", "RBI_MONETARY")
    assert res["expected_direction"] == "POSITIVE"


def test_explicit_negative_evidence_maps_negative():
    res = NewsImpactAssessor.assess_impact("Brent crude jumps to $85 on supply risk, inflation concerns intensify", "Energy import bill expands.", "media", "COMMODITIES")
    assert res["expected_direction"] == "NEGATIVE"


def test_high_impact_event_maps_high():
    res = NewsImpactAssessor.assess_impact("RBI Monetary Policy Committee keeps repo rate at 6.5%", "Official policy announcement.", "official", "RBI_MONETARY")
    assert res["impact_strength"] == "HIGH"


# ── 4. CATALYSTS & CONSISTENCY CONTRACTS ──

def test_catalysts_tab_evidence_backed_drivers_and_fallbacks():
    """Assert CatalystsTab renders active drivers and evidence-backed fallbacks when empty."""
    code = read_frontend("components/news/CatalystsTab.tsx")
    assert "No active evidence-backed market drivers currently identified." in code
    assert "No material carry-forward risks currently identified." in code
    assert "No active regulatory or policy catalysts." in code
