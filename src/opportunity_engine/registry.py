from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.models.opportunity_intelligence import OpportunityIntelligence
from src.opportunity_engine.domain import (
    CanonicalOpportunity,
    DetectorHealthInfo,
    OpportunityStatus,
    ScanMetrics,
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
from src.opportunity_engine.config import DEFAULT_OPPORTUNITY_CONFIG, OpportunityConfig
from src.utils import setup_logger

logger = setup_logger("OpportunityRegistryService")


class OpportunityRegistryService:
    """
    Singleton in-runtime stateful opportunity registry service for Phase 3.1.
    Orchestrates all 5 detectors, qualification, scoring, deduplication,
    continuous re-evaluation, best opportunity ranking, and memory retention.
    Strictly staging-only with acceptance status gate NOT_ACCEPTED.
    """

    _instance: Optional[OpportunityRegistryService] = None

    def __init__(self, max_retention: int = 100, config: OpportunityConfig = DEFAULT_OPPORTUNITY_CONFIG) -> None:
        self.max_retention = max_retention
        self.config = config
        self.runtime_id = str(uuid.uuid4())[:8]
        self.acceptance_status = "NOT_ACCEPTED"  # Phase 3.1 real-market acceptance gate
        self.staging_mode_only = True

        # 5 Independent Detectors
        self.detectors = [
            BreakoutDetector(),
            BreakdownDetector(),
            PullbackDetector(),
            ReversalDetector(),
            MomentumContinuationDetector(),
        ]

        # Health state for diagnostics
        self.health_map: Dict[str, DetectorHealthInfo] = {
            d.detector_id: DetectorHealthInfo(
                detector_id=d.detector_id,
                status="HEALTHY",
                version=d.detector_version,
            )
            for d in self.detectors
        }

        # Candidate Storage
        self.active_opportunities: Dict[str, CanonicalOpportunity] = {}
        self.blocked_recent: List[CanonicalOpportunity] = []
        self.rejected_recent: List[CanonicalOpportunity] = []
        self.invalidated_recent: List[CanonicalOpportunity] = []
        self.expired_recent: List[CanonicalOpportunity] = []

        # Observability & Metrics
        self.tracker = MissedOpportunityTracker(max_events=300)
        self.scan_metrics = ScanMetrics()

    @classmethod
    def get_instance(cls) -> OpportunityRegistryService:
        if cls._instance is None:
            cls._instance = OpportunityRegistryService()
        return cls._instance

    def evaluate_and_update(
        self,
        context: Dict[str, Any],
        state_sequence: int,
    ) -> OpportunityIntelligence:
        scan_start = time.perf_counter()
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        market = context.get("market_context") or {}
        options = context.get("option_context") or {}
        freshness = str(context.get("freshness_state") or "FRESH").upper()
        market_state = str(context.get("market_state") or "LIVE").upper()
        spot = float(market.get("current_spot") or 0.0)

        # 1. Continuous Re-evaluation of active candidates
        for opp_id, opp in list(self.active_opportunities.items()):
            updated_opp = ContinuousReEvaluator.re_evaluate(
                opp=opp,
                current_spot=spot,
                freshness_state=freshness,
                market_state=market_state,
                state_sequence=state_sequence,
                timestamp=now_iso,
            )
            if updated_opp.status == OpportunityStatus.INVALIDATED.value:
                self.invalidated_recent.insert(0, updated_opp)
                del self.active_opportunities[opp_id]
            elif updated_opp.status == OpportunityStatus.EXPIRED.value:
                self.expired_recent.insert(0, updated_opp)
                del self.active_opportunities[opp_id]
            elif updated_opp.status == OpportunityStatus.BLOCKED.value:
                self.blocked_recent.insert(0, updated_opp)

        # 2. Run all 5 Independent Detectors
        det_start = time.perf_counter()
        evaluated_count = 0

        for detector in self.detectors:
            health = self.health_map[detector.detector_id]
            health.last_evaluated = now_iso
            try:
                result = detector.evaluate(context)
                evaluated_count += 1

                if result.blocked:
                    health.status = "BLOCKED"
                    health.data_blockers = [result.blocking_reason or "Input requirements missing"]
                    health.blocked_today += 1
                    self.tracker.record_event(
                        timestamp=now_iso,
                        detector_id=detector.detector_id,
                        event_type="BLOCKED",
                        reason=result.blocking_reason or "Detector input requirements not met",
                    )
                    continue

                health.data_blockers = []

                if result.detected:
                    health.detections_today += 1

                    # 3. Multi-component Scoring
                    scores = OpportunityScorer.calculate_scores(result, context)

                    # 4. Qualification Engine with strict QUALIFIED vs TRADE_READY & BLOCKED handling
                    status, status_reason, blocking_reasons = QualificationEngine.qualify_opportunity(
                        detector_result=result,
                        scores=scores,
                        context=context,
                        config=self.config,
                    )

                    if status == OpportunityStatus.REJECTED:
                        health.rejected_today += 1
                        self.tracker.record_event(
                            timestamp=now_iso,
                            detector_id=detector.detector_id,
                            event_type="REJECTION",
                            reason=status_reason,
                            details={"raw_score": result.raw_score, "conflicts": result.conflicts},
                        )
                    elif status == OpportunityStatus.BLOCKED:
                        health.blocked_today += 1
                        self.tracker.record_event(
                            timestamp=now_iso,
                            detector_id=detector.detector_id,
                            event_type="BLOCKED",
                            reason=status_reason,
                        )
                    else:
                        health.qualified_today += 1

                    # 5. Deduplication & Update/Create
                    fp = DeduplicationEngine.generate_fingerprint(
                        setup_type=detector.detector_id.upper(),
                        direction=result.direction.value,
                        underlying="NIFTY",
                        entry_reference=result.suggested_levels.get("entry_reference", spot),
                        source_detector=detector.detector_id,
                    )

                    existing_match = DeduplicationEngine.match_existing_opportunity(
                        fp, list(self.active_opportunities.values())
                    )

                    levels = result.suggested_levels
                    sub_scores = scores["sub_scores"]
                    explanation_tokens = result.evidence + [f"Quality: {scores['quality_score']:.0f}%", f"Confidence: {scores['confidence_score']:.0f}%"]

                    if existing_match:
                        existing_match.updated_at = now_iso
                        existing_match.last_detected_at = now_iso
                        existing_match.state_sequence = state_sequence
                        existing_match.confidence_score = scores["confidence_score"]
                        existing_match.quality_score = scores["quality_score"]
                        existing_match.priority_score = scores["priority_score"]
                        existing_match.estimated_reward = scores["estimated_reward"]
                        existing_match.estimated_risk = scores["estimated_risk"]
                        existing_match.reward_risk_ratio = scores["reward_risk_ratio"]
                        existing_match.confirmation_signals = result.evidence
                        existing_match.conflicting_signals = result.conflicts
                        existing_match.detector_scores[detector.detector_id] = result.raw_score

                        if existing_match.status != status.value:
                            prev = existing_match.status
                            existing_match.status = status.value
                            existing_match.status_reason = status_reason
                            existing_match.transition_history.append({
                                "timestamp": now_iso,
                                "previous_status": prev,
                                "new_status": status.value,
                                "reason": status_reason,
                                "state_sequence": state_sequence,
                            })
                    else:
                        opp_id = f"OPP-NIFTY-{state_sequence}-{uuid.uuid4().hex[:6].upper()}"
                        instr_family = "NIFTY CE" if result.direction.value == "BULLISH" else "NIFTY PE"

                        new_opp = CanonicalOpportunity(
                            opportunity_id=opp_id,
                            runtime_id=self.runtime_id,
                            state_sequence=state_sequence,
                            created_at=now_iso,
                            updated_at=now_iso,
                            first_detected_at=now_iso,
                            last_detected_at=now_iso,
                            setup_type=detector.detector_id.upper(),
                            direction=result.direction.value,
                            underlying="NIFTY",
                            instrument_family=instr_family,
                            market_session=str(market.get("trading_session") or "INTRADAY"),
                            market_state=market_state,
                            freshness_state=freshness,
                            status=status.value,
                            status_reason=status_reason,
                            entry_reference=levels.get("entry_reference", spot),
                            entry_zone_low=levels.get("entry_zone_low", spot - 10),
                            entry_zone_high=levels.get("entry_zone_high", spot + 10),
                            invalidation_level=levels.get("invalidation_level", 0.0),
                            target_reference=levels.get("target_reference", 0.0),
                            target_zone_1=levels.get("target_zone_1", 0.0),
                            target_zone_2=levels.get("target_zone_2", 0.0),
                            estimated_reward=scores["estimated_reward"],
                            estimated_risk=scores["estimated_risk"],
                            reward_risk_ratio=scores["reward_risk_ratio"],
                            confidence_score=scores["confidence_score"],
                            quality_score=scores["quality_score"],
                            priority_score=scores["priority_score"],
                            detector_scores={detector.detector_id: result.raw_score},
                            confirmation_signals=result.evidence,
                            conflicting_signals=result.conflicts,
                            market_context_snapshot={
                                "spot": spot,
                                "vwap": market.get("vwap"),
                                "regime": market.get("market_regime"),
                                "trend": market.get("trend_direction"),
                                "vix": market.get("india_vix"),
                            },
                            options_context_snapshot={
                                "pcr": options.get("pcr"),
                                "max_pain": options.get("max_pain"),
                                "atm_iv": options.get("atm_iv"),
                            },
                            expiry_at=str(market.get("current_expiry") or ""),
                            source_detector=detector.detector_id,
                            detector_version=detector.detector_version,
                            scoring_version=OpportunityScorer.scoring_version,
                            qualification_version=QualificationEngine.qualification_version,
                            config_version=self.config.config_version,
                            explanation_tokens=explanation_tokens,
                            explanation_fields=sub_scores,
                            blocking_reasons=blocking_reasons,
                            transition_history=[{
                                "timestamp": now_iso,
                                "previous_status": "RAW",
                                "new_status": status.value,
                                "reason": status_reason,
                                "state_sequence": state_sequence,
                            }],
                        )

                        if status == OpportunityStatus.REJECTED:
                            self.rejected_recent.insert(0, new_opp)
                        elif status == OpportunityStatus.BLOCKED:
                            self.blocked_recent.insert(0, new_opp)
                        else:
                            self.active_opportunities[opp_id] = new_opp

                        self.tracker.record_event(
                            timestamp=now_iso,
                            detector_id=detector.detector_id,
                            event_type="DETECTION",
                            reason=f"Detected {detector.detector_id} setup with status {status.value}",
                            details={"opportunity_id": opp_id},
                        )

                health.status = "HEALTHY"
            except Exception as exc:
                health.status = "ERROR"
                health.errors.append(str(exc))
                logger.error(f"Detector {detector.detector_id} error: {exc}", exc_info=True)

        det_duration = (time.perf_counter() - det_start) * 1000.0

        # Memory Retention Pruning
        self.blocked_recent = self.blocked_recent[: self.max_retention]
        self.rejected_recent = self.rejected_recent[: self.max_retention]
        self.invalidated_recent = self.invalidated_recent[: self.max_retention]
        self.expired_recent = self.expired_recent[: self.max_retention]

        # Separate Active Opportunities by Status
        active_list = list(self.active_opportunities.values())
        trade_ready_list = [o for o in active_list if o.status == OpportunityStatus.TRADE_READY.value]
        watching_list = [
            o for o in active_list if o.status in (OpportunityStatus.WATCHING.value, OpportunityStatus.QUALIFIED.value)
        ]

        # Best Opportunity Selection
        best_selection = BestOpportunitySelector.select_best(
            trade_ready_opportunities=trade_ready_list,
            watching_opportunities=watching_list,
            market_state=market_state,
        )

        scan_duration = (time.perf_counter() - scan_start) * 1000.0
        self.scan_metrics = ScanMetrics(
            scan_duration_ms=scan_duration,
            detector_duration_ms=det_duration,
            candidates_evaluated=evaluated_count,
            active_candidates=len(self.active_opportunities),
            last_scan_at=now_iso,
        )

        return OpportunityIntelligence(
            best_opportunity=best_selection,
            trade_ready=[o.to_dict() for o in trade_ready_list],
            watching=[o.to_dict() for o in watching_list],
            blocked_recent=[o.to_dict() for o in self.blocked_recent[:20]],
            rejected_recent=[o.to_dict() for o in self.rejected_recent[:20]],
            invalidated_recent=[o.to_dict() for o in self.invalidated_recent[:20]],
            expired_recent=[o.to_dict() for o in self.expired_recent[:20]],
            detector_health={k: v.to_dict() for k, v in self.health_map.items()},
            scan_metrics=self.scan_metrics.to_dict(),
            acceptance_status=self.acceptance_status,
            staging_mode_only=self.staging_mode_only,
        )


OpportunityRegistry = OpportunityRegistryService
