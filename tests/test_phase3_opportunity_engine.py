from __future__ import annotations

import unittest
from datetime import datetime, timezone

from src.opportunity_engine.domain import (
    CanonicalOpportunity,
    DetectorInputRequirements,
    DetectorResult,
    Direction,
    OpportunityStatus,
)
from src.opportunity_engine.detectors import (
    BreakoutDetector,
    BreakdownDetector,
    PullbackDetector,
    ReversalDetector,
    MomentumContinuationDetector,
)
from src.opportunity_engine.scoring import OpportunityScorer
from src.opportunity_engine.qualification import QualificationEngine
from src.opportunity_engine.deduplication import DeduplicationEngine
from src.opportunity_engine.re_evaluation import ContinuousReEvaluator
from src.opportunity_engine.best_selection import BestOpportunitySelector
from src.opportunity_engine.missed_opportunity import MissedOpportunityTracker
from src.opportunity_engine.registry import OpportunityRegistryService
from src.opportunity_engine.config import OpportunityConfig, DEFAULT_OPPORTUNITY_CONFIG


class TestPhase3OpportunityEngine(unittest.TestCase):
    def setUp(self):
        self.market_bullish = {
            "current_spot": 24500.0,
            "vwap": 24450.0,
            "atr": 100.0,
            "india_vix": 14.0,
            "trend_direction": "BULLISH",
            "trend_strength": 75.0,
            "support_levels": [24350.0, 24400.0],
            "resistance_levels": [24480.0, 24600.0],
            "trading_session": "INTRADAY",
            "current_expiry": "2026-08-27",
            "market_regime": "TRENDING",
        }

        self.options_bullish = {
            "pcr": 1.15,
            "max_pain": 24450.0,
            "highest_call_oi_change": 5000.0,
            "highest_put_oi_change": 12000.0,
            "atm_iv": 14.5,
        }

        self.breadth_bullish = {
            "advances": 32,
            "declines": 18,
        }

        self.context = {
            "market_context": self.market_bullish,
            "option_context": self.options_bullish,
            "breadth": self.breadth_bullish,
            "freshness_state": "FRESH",
            "market_state": "LIVE",
            "market_closed": False,
        }

    def test_breakout_detector_detects_valid_breakout(self):
        detector = BreakoutDetector()
        result = detector.evaluate(self.context)
        self.assertTrue(result.detected)
        self.assertEqual(result.direction, Direction.BULLISH)
        self.assertGreaterEqual(result.raw_score, 50.0)
        self.assertTrue(len(result.evidence) > 0)
        self.assertIn("entry_reference", result.suggested_levels)

    def test_breakdown_detector_detects_valid_breakdown(self):
        market_bearish = dict(self.market_bullish)
        market_bearish["current_spot"] = 24320.0
        market_bearish["trend_direction"] = "BEARISH"
        market_bearish["vwap"] = 24380.0
        options_bearish = dict(self.options_bullish)
        options_bearish["pcr"] = 0.72
        options_bearish["highest_call_oi_change"] = 15000.0
        options_bearish["highest_put_oi_change"] = 4000.0
        breadth_bearish = {"advances": 12, "declines": 38}

        ctx = {
            "market_context": market_bearish,
            "option_context": options_bearish,
            "breadth": breadth_bearish,
            "freshness_state": "FRESH",
            "market_state": "LIVE",
            "market_closed": False,
        }

        detector = BreakdownDetector()
        result = detector.evaluate(ctx)
        self.assertTrue(result.detected)
        self.assertEqual(result.direction, Direction.BEARISH)
        self.assertGreaterEqual(result.raw_score, 50.0)

    def test_detector_input_requirements_blocks_when_missing(self):
        empty_ctx = {
            "market_context": {},
            "freshness_state": "FRESH",
        }
        detector = BreakoutDetector()
        result = detector.evaluate(empty_ctx)
        self.assertFalse(result.detected)
        self.assertTrue(result.blocked)
        self.assertIn("blocked", result.blocking_reason.lower())

    def test_stale_data_blocks_detector(self):
        stale_ctx = dict(self.context)
        stale_ctx["freshness_state"] = "STALE"
        detector = BreakoutDetector()
        result = detector.evaluate(stale_ctx)
        self.assertFalse(result.detected)
        self.assertTrue(result.blocked)
        self.assertIn("stale", result.blocking_reason.lower())

    def test_scoring_system_computes_master_scores(self):
        detector = BreakoutDetector()
        result = detector.evaluate(self.context)
        scores = OpportunityScorer.calculate_scores(result, self.context)

        self.assertIn("quality_score", scores)
        self.assertIn("confidence_score", scores)
        self.assertIn("priority_score", scores)
        self.assertIn("sub_scores", scores)
        self.assertGreaterEqual(scores["quality_score"], 0.0)
        self.assertLessEqual(scores["quality_score"], 100.0)
        self.assertGreaterEqual(scores["confidence_score"], 0.0)
        self.assertLessEqual(scores["confidence_score"], 100.0)

    def test_qualification_distinguishes_qualified_vs_trade_ready(self):
        detector = BreakoutDetector()
        result = detector.evaluate(self.context)
        scores = OpportunityScorer.calculate_scores(result, self.context)
        status, reason, blockers = QualificationEngine.qualify_opportunity(result, scores, self.context)

        self.assertIn(status, [OpportunityStatus.TRADE_READY, OpportunityStatus.QUALIFIED])

    def test_deduplication_engine_generates_stable_fingerprint(self):
        fp1 = DeduplicationEngine.generate_fingerprint("BREAKOUT", "BULLISH", "NIFTY", 24500.0, "breakout")
        fp2 = DeduplicationEngine.generate_fingerprint("BREAKOUT", "BULLISH", "NIFTY", 24510.0, "breakout")
        fp3 = DeduplicationEngine.generate_fingerprint("BREAKOUT", "BULLISH", "NIFTY", 24650.0, "breakout")

        self.assertEqual(fp1, fp2)  # Same 25-pt price zone bin
        self.assertNotEqual(fp1, fp3)

    def test_re_evaluation_handles_price_invalidation(self):
        opp = CanonicalOpportunity(
            opportunity_id="TEST-1",
            runtime_id="RUN-1",
            state_sequence=1,
            created_at="2026-08-17T00:00:00Z",
            updated_at="2026-08-17T00:00:00Z",
            first_detected_at="2026-08-17T00:00:00Z",
            last_detected_at="2026-08-17T00:00:00Z",
            setup_type="BREAKOUT",
            direction="BULLISH",
            status="TRADE_READY",
            invalidation_level=24400.0,
        )

        updated = ContinuousReEvaluator.re_evaluate(
            opp=opp,
            current_spot=24350.0,  # Breached SL
            freshness_state="FRESH",
            market_state="LIVE",
            state_sequence=2,
            timestamp="2026-08-17T00:01:00Z",
        )

        self.assertEqual(updated.status, OpportunityStatus.INVALIDATED.value)
        self.assertIsNotNone(updated.invalidated_at)
        self.assertEqual(len(updated.transition_history), 1)

    def test_best_opportunity_selector_handles_no_trade(self):
        best = BestOpportunitySelector.select_best([], [], market_state="LIVE")
        self.assertFalse(best["has_trade"])
        self.assertIn("NO HIGH-QUALITY TRADE", best["message"])

    def test_registry_service_runs_full_cycle_and_serializes(self):
        registry = OpportunityRegistryService.get_instance()
        intel = registry.evaluate_and_update(self.context, state_sequence=100)

        intel_dict = intel.to_dict()
        self.assertIn("best_opportunity", intel_dict)
        self.assertIn("detector_health", intel_dict)
        self.assertIn("scan_metrics", intel_dict)
        self.assertEqual(intel_dict["acceptance_status"], "NOT_ACCEPTED")
        self.assertTrue(intel_dict["staging_mode_only"])

    def test_missed_opportunity_tracker_session_metrics(self):
        tracker = MissedOpportunityTracker()
        tracker.record_event("2026-08-17T00:00:00Z", "breakout", "DETECTION", "Detected")
        tracker.record_event("2026-08-17T00:01:00Z", "breakout", "REJECTION", "Low score", {"raw_score": 60})

        metrics = tracker.compute_session_metrics()
        self.assertEqual(metrics["total_evaluations"], 2)
        self.assertEqual(metrics["total_detections"], 1)
        self.assertEqual(metrics["rejected_good_setups_count"], 1)


if __name__ == "__main__":
    unittest.main()
