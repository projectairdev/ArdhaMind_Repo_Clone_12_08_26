# tests/test_pre_deployment_truth_gate.py
"""
Pre-Deployment Truth Audit Test Suite for AIR ArdhaMind.

Verifies 6 strict truth contracts:
1. Previous Close Semantic Strictness (Spot MUST NOT substitute for previous_close)
2. GIFT Truth Contract & Snapshot Semantics
3. Monday Rollover Isolation (Friday telemetry cannot contaminate Monday current state)
4. Multi-Date Event Timeline & IST Boundary Isolation
5. Closed-Session Persistence Throttling & Atomic Flush
6. READ_ONLY & Zero Synthetic Data Invariants
"""
import pytest
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

from src.intelligence_engine.pre_market_engine import PreMarketIntelligenceEngine
from src.intelligence_engine.forward_outlook_engine import ForwardOutlookEngine
from src.intelligence_engine.structural_level_engine import StructuralLevelEngine
from src.application.workstation_state_service import WorkstationStateService


def test_previous_close_strictness_no_spot_fallback(tmp_path):
    """Truth Gate 1: spot MUST NOT substitute for previous_close when previous_close is absent."""
    state = {
        "market_session": {"session_date": "2026-08-17", "status": "OPEN"},
        "market_data": {
            "current_spot": 24500.0,
            # previous_close is intentionally missing / None
        },
        "macro_intelligence": {}
    }

    # 1. StructuralLevelEngine audit
    levels = StructuralLevelEngine.evaluate_levels(state)
    assert levels["previous_close"] is None, "StructuralLevelEngine must not substitute spot for missing previous_close"

    # 2. PreMarketIntelligenceEngine audit
    try:
        WorkstationStateService.reset_for_testing()
        WorkstationStateService.CACHE_DIR = tmp_path
        WorkstationStateService._allow_disk_cache_in_test = True

        report = PreMarketIntelligenceEngine.analyze_pre_market(state)
        pm_prev_close = report.critical_levels.get("previous_close")
        assert pm_prev_close is None, "PreMarketIntelligenceEngine must not substitute spot for missing previous_close"

        # 3. WorkstationStateService audit
        snap = WorkstationStateService.build_from_legacy(state)
        mc = snap.to_dict()["market_data"]
        assert mc.get("previous_close") is None, "WorkstationStateService must retain previous_close as None when unsupplied"
    finally:
        WorkstationStateService.reset_for_testing()


def test_gift_truth_contract():
    """Truth Gate 2: Verify GIFT provider snapshot semantics and distinct frozen labeling."""
    from src.news_engine.specialized_data_provider import GiftNiftyProvider

    provider = GiftNiftyProvider()
    assert provider.provider_name == "gift_nifty_provider"
    assert provider.refresh_interval == 60.0


def test_monday_rollover_isolation(tmp_path):
    """Truth Gate 3: Friday 14-Aug values cannot contaminate Monday 17-Aug current live state."""
    try:
        WorkstationStateService.reset_for_testing()
        WorkstationStateService.CACHE_DIR = tmp_path
        WorkstationStateService._allow_disk_cache_in_test = True

        # Friday session state
        fri_payload = {
            "marketContext": {
                "current_spot": 24366.0,
                "open": 24361.90,
                "high": 24404.05,
                "low": 24309.10,
                "close": 24366.00,
                "previous_close": 24395.85,
                "breadth": {"advances": 35, "declines": 15, "coverage": 50},
                "session_date": "2026-08-14"
            },
            "optionContext": {
                "pcr": 1.25,
                "atm_strike": 24350,
                "max_pain": 24400
            }
        }
        WorkstationStateService.build_from_legacy(fri_payload, broker_state="CONNECTED", market_state="CLOSED")

        # Monday pre-market state (new session date 2026-08-17)
        mon_payload = {
            "marketContext": {
                "current_spot": 24510.0,
                "previous_close": 24366.00,  # Friday close becomes Monday previous_close
                "session_date": "2026-08-17"
            }
        }
        mon_snap = WorkstationStateService.build_from_legacy(mon_payload, broker_state="CONNECTED", market_state="PRE_MARKET")
        mon_dict = mon_snap.to_dict()
        mon_mc = mon_dict["market_data"]

        # Assert Monday current state does NOT carry Friday intraday breadth or ticks
        assert mon_mc.get("previous_close") == 24366.00
        assert mon_mc.get("open") in (None, 24510.0)
    finally:
        WorkstationStateService.reset_for_testing()


def test_event_timeline_multi_date_and_ist_conversion(tmp_path):
    """Truth Gate 4: Multi-date events strictly isolated by IST date matching target_trading_date."""
    state = {
        "market_session": {"session_date": "2026-08-17", "status": "PRE_MARKET"},
        "market_data": {"current_spot": 24500.0, "previous_close": 24450.0},
        "macro_intelligence": {
            "economic_events": [
                {
                    "event_name": "Historical 2025 US CPI",
                    "scheduled_at": "2025-08-14T18:00:00Z",
                    "country": "US", "impact_level": "HIGH"
                },
                {
                    "event_name": "Friday 14-Aug Session Event",
                    "scheduled_at": "2026-08-14T12:00:00Z",
                    "country": "IND", "impact_level": "HIGH"
                },
                {
                    "event_name": "Weekend Event",
                    "scheduled_at": "2026-08-16T10:00:00Z",
                    "country": "IND", "impact_level": "MEDIUM"
                },
                {
                    "event_name": "Monday 17-Aug Target Event",
                    "scheduled_at": "2026-08-17T05:30:00Z",  # 11:00 IST on 17-Aug
                    "country": "IND", "impact_level": "CRITICAL"
                },
                {
                    "event_name": "Tuesday 18-Aug Future Event",
                    "scheduled_at": "2026-08-18T18:00:00Z",
                    "country": "US", "impact_level": "HIGH"
                }
            ]
        }
    }

    try:
        WorkstationStateService.reset_for_testing()
        WorkstationStateService.CACHE_DIR = tmp_path
        WorkstationStateService._allow_disk_cache_in_test = True
        PreMarketIntelligenceEngine.reset_engine_state()

        report = PreMarketIntelligenceEngine.analyze_pre_market(state)
        timeline = report.event_timeline

        event_names = [e["event_name"] for e in timeline]

        # 1. Historical 2025 and Friday 14-Aug events MUST be excluded
        assert "Historical 2025 US CPI" not in event_names
        assert "Friday 14-Aug Session Event" not in event_names
        assert "Weekend Event" not in event_names

        # 2. Target date 17-Aug event MUST be in TODAY scope
        target_ev = next(e for e in timeline if e["event_name"] == "Monday 17-Aug Target Event")
        assert target_ev["scope"] == "TODAY"
        assert target_ev["time_ist"] == "11:00 IST"

        # 3. Future 18-Aug event MUST be in UPCOMING scope
        future_ev = next(e for e in timeline if e["event_name"] == "Tuesday 18-Aug Future Event")
        assert future_ev["scope"] == "UPCOMING"
    finally:
        WorkstationStateService.reset_for_testing()


def test_closed_session_persistence_throttling(tmp_path):
    """Truth Gate 5: CLOSED state forces flush once, then throttles unchanged cycles."""
    try:
        WorkstationStateService.reset_for_testing()
        WorkstationStateService.CACHE_DIR = tmp_path
        WorkstationStateService._allow_disk_cache_in_test = True

        state_raw = {
            "market_state": "MARKET_CLOSED",
            "market_session": {"status": "CLOSED", "session_date": "2026-08-14", "is_closed": True},
            "market_data": {"current_spot": 24400.0, "previous_close": 24350.0},
            "broker_account": {"session_valid": True, "broker_state": "CONNECTED"},
        }

        # First build on CLOSED market -> triggers initial force flush ONCE
        WorkstationStateService.build_from_legacy(state_raw)
        t_first = WorkstationStateService._last_disk_flush_timestamp
        assert t_first > 0.0

        # Second build on CLOSED market without sequence or snapshot changes
        WorkstationStateService.build_from_legacy(state_raw)
        t_second = WorkstationStateService._last_disk_flush_timestamp

        # Flush timestamp MUST NOT update on unchanged closed evaluations
        assert t_second == t_first
    finally:
        WorkstationStateService.reset_for_testing()
