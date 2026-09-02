from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from src.analytics.snapshot.analytics_snapshot import MarketAnalyticsSnapshot
from src.decision.explanation.decision_explanation_engine import DecisionExplanationEngine
from src.decision.models.decision_models import (
    DecisionAuditRecord,
    DecisionRiskLevel,
    DecisionSnapshot,
    DecisionState,
    EntryReadinessStatus,
)
from src.decision.opportunity.opportunity_detection_engine import OpportunityDetectionEngine
from src.decision.risk.no_trade_engine import NoTradeEngine
from src.decision.risk.risk_assessment_engine import RiskAssessmentEngine
from src.decision.signal_fusion.signal_fusion_engine import SignalFusionEngine
from src.decision.strategy.strategy_suitability_engine import StrategySuitabilityEngine
from src.market_data.models.quality_enums import DataQualityStatus
from src.prediction.models.prediction_models import PredictionSnapshot


class DecisionEngine:
    """
    Authoritative provider-independent decision intelligence coordinator.
    Evaluates signal fusion, setup opportunities, risk gating, strategy suitability,
    and structured explanations into an immutable DecisionSnapshot.
    """

    MODEL_VERSION = "v1.0.0"

    @staticmethod
    def evaluate_decision(
        analytics: MarketAnalyticsSnapshot,
        prediction: Optional[PredictionSnapshot] = None,
    ) -> DecisionSnapshot:
        """Computes comprehensive, immutable DecisionSnapshot directly from analytics and prediction inputs."""
        now_utc = datetime.now(timezone.utc)
        dec_id = f"dec_{uuid4().hex[:12]}"

        # 1. Signal Fusion
        fusion = SignalFusionEngine.fuse_signals(analytics, prediction)

        # 2. Opportunity Assessment & Entry Readiness
        opportunity, readiness = OpportunityDetectionEngine.evaluate_opportunity(analytics, fusion)

        # 3. Risk Assessment
        risk = RiskAssessmentEngine.assess_risk(analytics, fusion)

        # 4. No-Trade & Safety Gating
        is_gated, gated_state, _ = NoTradeEngine.evaluate_gate(analytics, fusion, opportunity, risk)

        # 5. State Machine Resolution
        if is_gated and gated_state is not None:
            dec_state = gated_state
        elif readiness == EntryReadinessStatus.READY_FOR_HUMAN_REVIEW:
            dec_state = DecisionState.READY_FOR_HUMAN_REVIEW
        elif readiness == EntryReadinessStatus.WAITING_FOR_TRIGGER:
            dec_state = DecisionState.WAIT
        elif opportunity.status == "WATCH":
            dec_state = DecisionState.WATCH
        else:
            dec_state = DecisionState.NO_TRADE

        # 6. Strategy Suitability & Strike Candidates
        strategy, strikes = StrategySuitabilityEngine.evaluate_strategy(analytics, fusion, risk)

        # 7. Decision Confidence Calculation
        pred_conf = prediction.prediction_record.confidence_score if prediction else 0.50
        conf_score = round(
            (fusion.agreement_score * 0.40) +
            (pred_conf * 0.30) +
            (0.30 if dec_state == DecisionState.READY_FOR_HUMAN_REVIEW else 0.15) -
            (fusion.conflict_score * 0.30),
            2
        )
        conf_score = max(0.05, min(0.95, conf_score))

        # Confidence Band with Data Quality Guard
        if analytics.quality != DataQualityStatus.VALID and conf_score >= 0.75:
            conf_score = 0.65

        if conf_score >= 0.75 and dec_state == DecisionState.READY_FOR_HUMAN_REVIEW:
            conf_band = "HIGH"
        elif conf_score >= 0.50:
            conf_band = "MODERATE"
        elif conf_score >= 0.25:
            conf_band = "LOW"
        else:
            conf_band = "INSUFFICIENT"

        # 8. Structured Explanation
        explanation = DecisionExplanationEngine.generate_explanation(
            analytics=analytics,
            fusion=fusion,
            opportunity=opportunity,
            readiness=readiness,
            risk=risk,
            decision_state=dec_state,
        )

        return DecisionSnapshot(
            decision_id=dec_id,
            session_date=analytics.session_date,
            captured_at=now_utc,
            decision_state=dec_state,
            confidence_score=conf_score,
            confidence_band=conf_band,
            setup=opportunity,
            entry_readiness=readiness,
            risk_assessment=risk,
            strategy_suitability=strategy,
            strike_candidates=strikes,
            signal_fusion=fusion,
            explanation=explanation,
            quality=analytics.quality,
            state_revision=analytics.state_revision,
        )
