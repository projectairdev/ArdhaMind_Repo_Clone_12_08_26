from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from src.opportunity_engine.models import (
    CanonicalOpportunity,
    DetectorResult,
    OpportunityStatus,
)
from src.opportunity_engine.detectors import ALL_DETECTORS, OpportunityDetector
from src.opportunity_engine.scoring import calculate_opportunity_scores
from src.opportunity_engine.qualification import qualify_opportunity
from src.opportunity_engine.lifecycle import build_canonical_opportunity, generate_dedup_key
from src.opportunity_engine.registry import OpportunityRegistry
from src.opportunity_engine.ranking import select_best_opportunity
from src.utils import setup_logger

logger = setup_logger("OpportunityEngine")


class OpportunityEngine:
    """
    Deterministic Opportunity Detection, Scoring, Ranking, and Lifecycle Orchestrator for Phase 3.1.
    """

    def __init__(self, registry: Optional[OpportunityRegistry] = None) -> None:
        self.registry = registry or OpportunityRegistry()
        self.detectors: list[OpportunityDetector] = [det_cls() for det_cls in ALL_DETECTORS]

    def _normalize_context(self, raw_context: dict[str, Any]) -> dict[str, Any]:
        market = raw_context.get("market") or raw_context.get("market_context") or {}
        options = raw_context.get("options") or raw_context.get("option_context") or {}
        technical = raw_context.get("technical_analysis") or raw_context.get("technical") or {}
        breadth = raw_context.get("breadth") or market.get("breadth") or {}
        news = raw_context.get("news") or raw_context.get("news_sentiment") or {}
        macro = raw_context.get("macro") or raw_context.get("macro_intelligence") or {}
        broker = raw_context.get("broker") or raw_context.get("broker_status") or {}

        session = raw_context.get("session") or {
            "session_type": raw_context.get("freshness_state", "LIVE"),
            "is_closed": raw_context.get("market_closed", False),
        }

        data_qual = raw_context.get("data_quality") or {
            "status": market.get("freshness_status", "FRESH")
        }

        return {
            "market": market,
            "options": options,
            "technical_analysis": technical,
            "breadth": breadth,
            "news": news,
            "macro": macro,
            "broker": broker,
            "session": session,
            "data_quality": data_qual,
        }

    def evaluate(
        self,
        raw_context: dict[str, Any],
        state_sequence: int = 1,
        runtime_id: str = "rt-prod-1"
    ) -> dict[str, Any]:
        start_time = time.perf_counter()
        context = self._normalize_context(raw_context)

        session = context.get("session", {})
        market_session_type = str(session.get("session_type", "LIVE")).upper()
        is_closed = bool(session.get("is_closed", False)) or market_session_type in ["CLOSED", "WEEKEND", "HOLIDAY"]

        evaluated_candidates: list[CanonicalOpportunity] = []
        candidates_count = 0

        for detector in self.detectors:
            try:
                res: DetectorResult = detector.evaluate(context)
                candidates_count += 1

                if res.detected or res.blocking_reason:
                    qual_score, conf_score, prio_score, breakdown = calculate_opportunity_scores(res, context)

                    status, status_reason, blocking_reasons = qualify_opportunity(
                        res, qual_score, conf_score, prio_score, breakdown, context
                    )

                    self.registry.update_detector_health(
                        detector_id=detector.detector_id,
                        version=detector.detector_version,
                        detected=res.detected,
                        qualified=(status in [OpportunityStatus.QUALIFIED, OpportunityStatus.TRADE_READY]),
                        rejected=(status == OpportunityStatus.REJECTED),
                        data_blocker=res.blocking_reason,
                    )

                    spot = float(context.get("market", {}).get("current_spot", 0.0) or 0.0)
                    strike = res.provisional_strike or (int(round(spot / 50.0) * 50) if spot > 0 else 24500)
                    dedup_key = generate_dedup_key(res.setup_type, res.direction, "NIFTY 50", strike)

                    existing_match = next(
                        (
                            o for o in self.registry.get_all_active()
                            if generate_dedup_key(
                                o.setup_type,
                                o.direction,
                                o.underlying,
                                int(o.instrument_family.split()[-2]) if len(o.instrument_family.split()) >= 2 and o.instrument_family.split()[-2].isdigit() else None
                            ) == dedup_key
                        ),
                        None
                    )

                    opp = build_canonical_opportunity(
                        detector_result=res,
                        quality_score=qual_score,
                        confidence_score=conf_score,
                        priority_score=prio_score,
                        score_breakdown_dict=breakdown.to_dict(),
                        status=status,
                        status_reason=status_reason,
                        blocking_reasons=blocking_reasons,
                        context=context,
                        runtime_id=runtime_id,
                        state_sequence=state_sequence,
                        existing=existing_match,
                    )

                    self.registry.register_opportunity(opp)
                    evaluated_candidates.append(opp)

                    if not res.detected and res.blocking_reason:
                        self.registry.record_missed_opportunity_audit({
                            "detector_id": detector.detector_id,
                            "setup_type": res.setup_type,
                            "direction": res.direction,
                            "blocking_reason": res.blocking_reason,
                            "raw_score": res.raw_score,
                            "timestamp": opp.updated_at,
                        })

                else:
                    self.registry.update_detector_health(
                        detector_id=detector.detector_id,
                        version=detector.detector_version,
                        detected=False,
                        qualified=False,
                        rejected=False,
                    )

            except Exception as e:
                logger.error(f"Detector {detector.detector_id} failed during evaluation: {e}", exc_info=True)
                self.registry.update_detector_health(
                    detector_id=detector.detector_id,
                    version=detector.detector_version,
                    detected=False,
                    qualified=False,
                    rejected=False,
                    error=str(e),
                )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        self.registry.update_scan_metrics(elapsed_ms, candidates_count)

        all_active = self.registry.get_all_active()
        best_opp_dict = select_best_opportunity(all_active, market_closed=is_closed)

        return {
            "best_opportunity": best_opp_dict,
            "trade_ready": [opp.to_dict() for opp in self.registry.get_trade_ready()],
            "watching": [opp.to_dict() for opp in self.registry.get_watching()],
            "blocked_recent": [opp.to_dict() for opp in self.registry.get_watching() if opp.blocking_reasons],
            "rejected_recent": [opp.to_dict() for opp in self.registry.get_rejected()],
            "invalidated_recent": [opp.to_dict() for opp in self.registry.get_invalidated()],
            "expired_recent": [opp.to_dict() for opp in self.registry.get_expired()],
            "detector_health": self.registry.get_detector_health_report(),
            "scan_metrics": self.registry.get_scan_metrics(),
            "acceptance_status": "ACCEPTED",
            "staging_mode_only": False,
        }
