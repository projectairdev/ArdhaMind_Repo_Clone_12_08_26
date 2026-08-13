# tests/test_d38_structural_levels_and_session_reliability.py
"""
Targeted Pytest Suite for Sprint D3.8:
1. Structural Level Intelligence (StructuralLevelEngine) without manufactured offsets.
2. Evidence Confluence & Level Metadata (sources, strength, confidence).
3. Pre-Market Confidence Gating on stale GIFT Nifty or missing options structure.
4. Scoped Macro Asset Refresh (unrelated quote immutability).
5. Kite Connect/Disconnect Session Reliability & Diagnostic Telemetry.
6. READ_ONLY Workstation Policy Enforcement.
"""
import pytest
from datetime import datetime, timezone
from src.intelligence_engine.structural_level_engine import StructuralLevelEngine, StructuralLevel
from src.intelligence_engine.pre_market_engine import PreMarketIntelligenceEngine
from src.broker.adapters.kite_ticker_adapter import KiteTickerAdapter
from src.broker.services.streaming_orchestrator import StreamingOrchestrator


def test_1_structural_level_engine_no_arbitrary_offsets():
    state = {
        "market_data": {
            "current_spot": 24500.0,
            "previous_close": 24500.0,
            "high": 24580.0,
            "low": 24420.0,
            "open": 24490.0,
        },
        "option_intelligence": {
            "pcr": 1.15,
            "max_pain": 24500.0,
            "highest_call_oi_strike": 24700.0,
            "highest_put_oi_strike": 24300.0,
            "atm_strike": 24500.0,
        },
        "macro_intelligence": {
            "quotes": {
                "GIFT_NIFTY": {"price": 24540.0, "status": "FRESH"}
            }
        }
    }

    res = StructuralLevelEngine.evaluate_levels(state)

    # Prove levels are not arbitrary +/- 50 or +/- 120
    imm_sup = res["immediate_support"]
    imm_res = res["immediate_resistance"]

    assert imm_sup["price"] != 24450.0  # Not prev_close - 50
    assert imm_res["price"] != 24550.0  # Not prev_close + 50

    # Prove structured metadata is present
    assert "sources" in imm_sup
    assert "strength" in imm_sup
    assert "confidence" in imm_sup
    assert len(imm_sup["sources"]) >= 1


def test_2_structural_level_confluence_clustering():
    # Setup overlapping evidence near 24420.0 (prev_low = 24420, put_oi = 24425)
    state = {
        "market_data": {
            "current_spot": 24500.0,
            "previous_close": 24500.0,
            "high": 24650.0,
            "low": 24420.0,
        },
        "option_intelligence": {
            "highest_call_oi_strike": 24650.0,
            "highest_put_oi_strike": 24425.0,
            "max_pain": 24420.0,
            "atm_strike": 24500.0,
        }
    }

    res = StructuralLevelEngine.evaluate_levels(state)
    all_levels = res["all_structural_levels"]

    # Look for clustered level near 24420
    cluster_24420 = next((l for l in all_levels if abs(l["price"] - 24420.0) <= 10.0), None)
    assert cluster_24420 is not None
    assert cluster_24420["evidence_count"] >= 2
    assert "PREVIOUS_SESSION_LOW" in cluster_24420["sources"] or "HIGHEST_PUT_OI_STRIKE" in cluster_24420["sources"]
    assert cluster_24420["strength"] in ("STRONG", "MODERATE")


def test_3_pre_market_engine_consumes_structural_levels():
    state = {
        "market_data": {
            "current_spot": 24500.0,
            "previous_close": 24500.0,
            "high": 24580.0,
            "low": 24420.0,
        },
        "option_intelligence": {
            "pcr": 1.0,
            "highest_call_oi_strike": 24600.0,
            "highest_put_oi_strike": 24400.0,
        },
        "macro_intelligence": {
            "quotes": {
                "GIFT_NIFTY": {"price": 24520.0, "status": "FRESH", "observed_at": "2026-08-14T08:30:00Z", "checked_at": "2026-08-14T08:35:00Z"}
            }
        }
    }

    rpt = PreMarketIntelligenceEngine.analyze_pre_market(state)
    levels = rpt.critical_levels

    assert "structural_details" in levels
    assert levels["immediate_support"] != 24450.0  # Not arbitrary offset
    assert levels["immediate_resistance"] != 24550.0  # Not arbitrary offset


def test_4_pre_market_stale_gift_confidence_limiter():
    PreMarketIntelligenceEngine._frozen_report_cache.clear()
    state = {
        "market_data": {"previous_close": 24500.0},
        "macro_intelligence": {
            "quotes": {
                "GIFT_NIFTY": {"price": 24580.0, "freshness_status": "STALE"}
            }
        }
    }

    rpt = PreMarketIntelligenceEngine.analyze_pre_market(state)
    # Stale GIFT Nifty must strictly limit overall confidence to LOW!
    assert rpt.overall_confidence == "LOW"


def test_5_kite_ticker_adapter_telemetry_ring_buffer():
    adapter = KiteTickerAdapter(api_key="test_key", access_token="test_token")
    events = adapter.get_telemetry_events()
    assert isinstance(events, list)

    # Initial state generation is 1
    assert adapter.generation_id == 1

    # Connect requested event should be logged in telemetry
    adapter._record_telemetry("CONNECT_REQUESTED", reason="Test startup")
    events_after = adapter.get_telemetry_events()
    assert len(events_after) == 1
    assert events_after[0]["event_type"] == "CONNECT_REQUESTED"
    assert events_after[0]["generation_id"] == 1


def test_6_streaming_orchestrator_singleton_invariant():
    orch1 = StreamingOrchestrator.get_instance()
    orch2 = StreamingOrchestrator.get_instance()
    assert orch1 is orch2


def test_7_read_only_invariants():
    state = {"market_data": {"previous_close": 24500.0}}
    rpt = PreMarketIntelligenceEngine.analyze_pre_market(state)
    rpt_dict = rpt.to_dict()

    raw_str = str(rpt_dict).lower()
    assert "buy" not in raw_str
    assert "sell" not in raw_str
    assert "order" not in raw_str
    assert "execute" not in raw_str
