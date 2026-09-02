from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional

from src.analytics.snapshot.analytics_snapshot import MarketAnalyticsSnapshot
from src.decision.decision.decision_engine import DecisionEngine
from src.decision.models.decision_models import DecisionSnapshot
from src.decision.products.live_guide import LiveGuideGenerator, LiveGuideSnapshot
from src.decision.products.market_intelligence import MarketIntelligenceSummary, MarketIntelligenceSummaryGenerator
from src.decision.products.morning_plan import MorningPlanGenerator, MorningPlanSnapshot
from src.decision.products.tomorrow_plan import TomorrowPlanGenerator, TomorrowPlanSnapshot
from src.market_data.models.completed_session_snapshot import CompletedSessionSnapshot
from src.market_data.session.session_authority import CanonicalSessionAuthority, MarketPhase
from src.prediction.models.prediction_models import PredictionOutcome, PredictionSnapshot


class ProductCoordinator:
    """
    Coordinates phase-aware routing to appropriate canonical market intelligence products:
    - PRE_MARKET / PRE_OPEN -> MorningPlan primary
    - MARKET_OPEN -> LiveGuide primary
    - POST_MARKET / MARKET_CLOSED -> TomorrowPlan primary
    """

    def __init__(self, session_authority: Optional[CanonicalSessionAuthority] = None) -> None:
        self.session_authority = session_authority or CanonicalSessionAuthority()

    def get_primary_product(
        self,
        analytics: MarketAnalyticsSnapshot,
        prediction: Optional[PredictionSnapshot] = None,
        decision: Optional[DecisionSnapshot] = None,
        completed_session: Optional[CompletedSessionSnapshot] = None,
        prediction_outcome: Optional[PredictionOutcome] = None,
    ) -> Dict[str, Any]:
        """Routes and generates the authoritative primary product based on current session phase."""
        sess_ctx = self.session_authority.evaluate_session()
        phase = sess_ctx.market_phase

        dec_snap = decision or DecisionEngine.evaluate_decision(analytics, prediction)
        summary = MarketIntelligenceSummaryGenerator.generate(dec_snap)

        if phase in (MarketPhase.PRE_MARKET, MarketPhase.PRE_OPEN) and prediction is not None:
            morning_plan = MorningPlanGenerator.generate(analytics, prediction)
            return {
                "phase": phase.value,
                "primary_product": "MORNING_PLAN",
                "morning_plan": morning_plan,
                "market_intelligence_summary": summary,
                "decision_snapshot": dec_snap,
            }
        elif phase == MarketPhase.MARKET_OPEN:
            live_guide = LiveGuideGenerator.generate(analytics, dec_snap, session_phase=phase.value)
            return {
                "phase": phase.value,
                "primary_product": "LIVE_GUIDE",
                "live_guide": live_guide,
                "market_intelligence_summary": summary,
                "decision_snapshot": dec_snap,
            }
        else:
            # POST_MARKET / MARKET_CLOSED
            if completed_session is not None:
                next_d = sess_ctx.next_trading_date
                tomorrow_plan = TomorrowPlanGenerator.generate(
                    completed_session=completed_session,
                    next_trading_date=next_d,
                    outcome=prediction_outcome,
                )
                return {
                    "phase": phase.value,
                    "primary_product": "TOMORROW_PLAN",
                    "tomorrow_plan": tomorrow_plan,
                    "market_intelligence_summary": summary,
                    "decision_snapshot": dec_snap,
                }
            else:
                live_guide = LiveGuideGenerator.generate(analytics, dec_snap, session_phase=phase.value)
                return {
                    "phase": phase.value,
                    "primary_product": "LIVE_GUIDE",
                    "live_guide": live_guide,
                    "market_intelligence_summary": summary,
                    "decision_snapshot": dec_snap,
                }
