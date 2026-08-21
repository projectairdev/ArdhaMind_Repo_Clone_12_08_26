# tests/test_state_consistency_invariant.py
"""
Regression test suite covering session lifecycle & operational state consistency repairs.
"""
from datetime import datetime, timezone, timedelta
import pytest
from src.application.workstation_state_service import WorkstationStateService
from src.intelligence_engine.today_analysis_engine import TodayAnalysisEngine
from src.intelligence_engine.forward_outlook_engine import ForwardOutlookEngine
from src.intelligence_engine.pre_market_engine import PreMarketIntelligenceEngine
from src.intelligence_engine.live_assistant_engine import LiveAssistantEngine
from src.news_engine.relevance_v2 import NiftyRelevanceEngineV2
from src.validation_engine.state_consistency_invariant import verify_state_consistency_invariants


class TestStateConsistencyInvariants:

    def test_closed_market_transport_and_readiness_semantics(self):
        """Expected closed-market or idle stream states must not force ATTENTION_REQUIRED."""
        state = {
            "market_session": {"status": "CLOSED", "is_closed": True, "session_date": "2026-08-14"},
            "broker_status": {"status": "CONNECTED", "session_valid": True},
            "market_feed_status": {"status": "HEALTHY", "bootstrap_state": "LIVE", "stream_status": "CONNECTED"},
            "workspace_readiness": {"overall_state": "READY"},
            "pre_market_report": {
                "opening_validation": {"summary": "Opening validation completed for session (2026-08-14). Session closed at spot 24,150.00."}
            },
            "application_status": {"order_execution_enabled": False},
        }

        violations = verify_state_consistency_invariants(state)
        assert violations == [], f"Expected no invariant violations, got: {violations}"

    def test_todays_analysis_finalized_session_preservation(self):
        """Today's Analysis must preserve final authoritative session analysis post close."""
        history = [
            {
                "timestamp": "2026-08-14T09:45:00Z",
                "session_date": "2026-08-14",
                "spot": 24150.0,
                "previous_close": 24000.0,
                "open": 24050.0,
                "high": 24200.0,
                "low": 24020.0,
                "breadth": {"advances": 35, "declines": 15, "coverage": 50},
                "options": {"pcr": 1.25, "atm_strike": 24150, "max_pain": 24100},
                "vix": 14.5
            }
        ]

        # Post close empty current telemetry state
        empty_post_close_state = {
            "market_session": {"status": "CLOSED", "is_closed": True, "session_date": "2026-08-14"},
            "market_data": {}
        }

        report = TodayAnalysisEngine.analyze(empty_post_close_state, history)
        assert report.analysis_status != "INSUFFICIENT_DATA", "Post-close analysis must not fall back to INSUFFICIENT_DATA when history exists"
        assert report.session_statistics.get("spot") == 24150.0
        assert report.conviction > 0

    def test_forward_outlook_post_close_lifecycle(self):
        """Forward Outlook must expose authoritative next-session/evening outlook post close."""
        state = {
            "market_session": {"status": "CLOSED", "is_closed": True, "session_date": "2026-08-14"},
            "market_data": {"current_spot": 24150.0},
            "evening_report": {
                "tomorrow_outlook": {
                    "directional_bias": "BULLISH_CONTINUATION",
                    "confidence": "HIGH",
                    "narrative": "Sustained institutional buying into weekend supports bullish momentum.",
                    "key_support_levels": [24100.0],
                    "key_resistance_levels": [24300.0],
                    "key_drivers": ["FII net inflow", "Options PCR 1.25"]
                }
            }
        }

        report = ForwardOutlookEngine.evaluate_outlook(state)
        assert report.analysis_status == "NEXT_SESSION_OUTLOOK"
        assert report.horizon_minutes == 900
        assert "BULLISH" in report.primary_scenario.headline

    def test_pre_market_opening_validation_historical_semantics(self):
        """Opening validation must be historically scoped post close and never display active present tense."""
        PreMarketIntelligenceEngine.reset_engine_state()
        state = {
            "market_session": {"status": "CLOSED", "is_closed": True, "session_date": "2026-08-14"},
            "market_data": {"current_spot": 24150.0, "previous_close": 24000.0}
        }

        report = PreMarketIntelligenceEngine.analyze_pre_market(state)
        val_summary = report.opening_validation.get("summary", "")
        assert "Regular market session active" not in val_summary
        assert "completed" in val_summary or "closed" in val_summary

    def test_pre_market_closed_today_semantics(self):
        """1. CLOSED + session_date == today must contain completed/closed and NOT awaiting market open."""
        PreMarketIntelligenceEngine.reset_engine_state()
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        state = {
            "market_session": {"status": "CLOSED", "is_closed": True, "session_date": today_str},
            "market_data": {"current_spot": 24150.0, "previous_close": 24000.0}
        }
        post_market_utc = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0)
        report = PreMarketIntelligenceEngine.analyze_pre_market(state, as_of_time=post_market_utc)
        summary = report.opening_validation.get("summary", "")
        assert "completed" in summary or "closed" in summary
        assert "Awaiting market open" not in summary
        assert "Regular market session active" not in summary
        assert report.analysis_status == "SESSION_COMPLETE"

    def test_pre_market_closed_past_date_semantics(self):
        """2. CLOSED + session_date < today -> historical/finalized semantics."""
        PreMarketIntelligenceEngine.reset_engine_state()
        state = {
            "market_session": {"status": "CLOSED", "is_closed": True, "session_date": "2026-08-01"},
            "market_data": {"current_spot": 24000.0, "previous_close": 23900.0}
        }
        report = PreMarketIntelligenceEngine.analyze_pre_market(state)
        summary = report.opening_validation.get("summary", "")
        assert "completed" in summary or "closed" in summary
        assert report.analysis_status == "SESSION_COMPLETE"

    def test_pre_market_post_close_semantics(self):
        """3. POST_CLOSE -> finalized semantics."""
        PreMarketIntelligenceEngine.reset_engine_state()
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        state = {
            "market_session": {"status": "POST_CLOSE", "session_date": today_str},
            "market_data": {"current_spot": 24150.0}
        }
        report = PreMarketIntelligenceEngine.analyze_pre_market(state)
        summary = report.opening_validation.get("summary", "")
        assert "completed" in summary or "closed" in summary
        assert report.analysis_status == "SESSION_COMPLETE"

    def test_pre_market_holiday_semantics(self):
        """4. HOLIDAY -> non-trading/closed semantics."""
        PreMarketIntelligenceEngine.reset_engine_state()
        state = {
            "market_session": {"status": "HOLIDAY", "session_date": "2026-08-15"}
        }
        report = PreMarketIntelligenceEngine.analyze_pre_market(state)
        summary = report.opening_validation.get("summary", "")
        assert "closed" in summary or "holiday" in summary
        assert "Awaiting market open" not in summary
        assert report.analysis_status == "SESSION_COMPLETE"

    def test_pre_market_pre_open_semantics(self):
        """5. PRE_MARKET / PRE_OPEN -> awaiting/opening-preparation semantics."""
        PreMarketIntelligenceEngine.reset_engine_state()
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        state = {
            "market_session": {"status": "PRE_MARKET", "session_date": today_str}
        }
        report = PreMarketIntelligenceEngine.analyze_pre_market(state)
        summary = report.opening_validation.get("summary", "")
        assert "Awaiting market open" in summary
        assert report.analysis_status == "READY"

    def test_pre_market_open_semantics(self):
        """6. OPEN -> active-session semantics."""
        PreMarketIntelligenceEngine.reset_engine_state()
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        state = {
            "market_session": {"status": "OPEN", "session_date": today_str},
            "market_data": {"current_spot": 24200.0}
        }
        report = PreMarketIntelligenceEngine.analyze_pre_market(state)
        summary = report.opening_validation.get("summary", "")
        assert "Regular market session active" in summary
        assert report.analysis_status == "SESSION_IN_PROGRESS"

    def test_pre_market_unknown_missing_status_fallback(self):
        """7. Unknown/missing status -> date/time fallback still works."""
        PreMarketIntelligenceEngine.reset_engine_state()
        # Past date with missing status -> fallback to CLOSED
        state_past = {
            "market_session": {"session_date": "2026-08-01"},
            "market_data": {"current_spot": 24000.0}
        }
        report_past = PreMarketIntelligenceEngine.analyze_pre_market(state_past)
        assert report_past.analysis_status == "SESSION_COMPLETE"

        # Future date with missing status -> fallback to PRE_MARKET
        state_future = {
            "market_session": {"session_date": "2030-01-01"}
        }
        report_future = PreMarketIntelligenceEngine.analyze_pre_market(state_future)
        assert report_future.analysis_status == "READY"

    def test_live_assistant_observation_density(self):
        """Live Assistant 15-minute windows must evaluate price delta when history contains observations."""
        history = [
            {"timestamp": "2026-08-14T03:45:00Z", "session_date": "2026-08-14", "spot": 24000.0, "breadth": {"advances": 20, "declines": 30}, "vix": 14.0},
            {"timestamp": "2026-08-14T03:50:00Z", "session_date": "2026-08-14", "spot": 24050.0, "breadth": {"advances": 25, "declines": 25}, "vix": 14.1},
            {"timestamp": "2026-08-14T03:55:00Z", "session_date": "2026-08-14", "spot": 24100.0, "breadth": {"advances": 30, "declines": 20}, "vix": 14.2},
            {"timestamp": "2026-08-14T03:59:00Z", "session_date": "2026-08-14", "spot": 24120.0, "breadth": {"advances": 35, "declines": 15}, "vix": 14.3},
        ]
        state = {
            "market_session": {"status": "CLOSED", "is_closed": True, "session_date": "2026-08-14"},
            "market_data": {"current_spot": 24120.0}
        }

        intel = LiveAssistantEngine.analyze_live_session(state, history)
        windows = intel.get("windows") or []
        win_0915 = next((w for w in windows if w.get("window_start") == "09:15"), None)
        assert win_0915 is not None
        assert win_0915.get("data_quality", {}).get("observation_count") >= 4
        assert win_0915.get("analysis_status") != "INSUFFICIENT_WINDOW_EVIDENCE"

    def test_news_ranking_explainer_penalty(self):
        """Generic explainer / educational articles must be penalized and cannot outrank direct market-moving news."""
        explainer = NiftyRelevanceEngineV2.assess(
            headline="What is NIFTY Option Trading: A Complete Beginner's Guide",
            content="Learn how option trading works in Indian stock markets.",
            category="Markets",
            stream="INDIA",
            source_tier="TIER_2"
        )

        market_moving = NiftyRelevanceEngineV2.assess(
            headline="RBI Announces Unexpected 25bps Rate Cut; NIFTY Bank Surges",
            content="Reserve Bank of India monetary policy committee cuts repo rate.",
            category="Policy",
            stream="INDIA",
            source_tier="TIER_1"
        )

        assert explainer["nifty_relevance_score"] <= 3.0
        assert explainer["impact_level"] == "LOW"
        assert market_moving["nifty_relevance_score"] >= 7.0
        assert market_moving["impact_level"] in ("HIGH", "CRITICAL")
        assert market_moving["nifty_relevance_score"] > explainer["nifty_relevance_score"]

    def test_read_only_safety_invariant(self):
        """Enforce hard-disabled order execution invariant."""
        state = {
            "application_status": {"order_execution_enabled": False},
            "read_only_policy": {"orders_enabled": False}
        }
        violations = verify_state_consistency_invariants(state)
        assert not any("READ_ONLY" in v for v in violations)

        violating_state = {
            "application_status": {"order_execution_enabled": True},
            "read_only_policy": {"orders_enabled": True}
        }
        violations = verify_state_consistency_invariants(violating_state)
        assert any("READ_ONLY" in v for v in violations)
