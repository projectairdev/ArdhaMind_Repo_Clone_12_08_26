from __future__ import annotations

from typing import List

from src.analytics.snapshot.analytics_snapshot import MarketAnalyticsSnapshot
from src.decision.models.decision_models import (
    DecisionExplanation,
    DecisionState,
    EntryReadinessStatus,
    OpportunityAssessment,
    RiskAssessment,
    SignalFusionContext,
)


class DecisionExplanationEngine:
    """
    Deterministic structured explanation generator.
    Produces comprehensive human-readable intelligence without requiring an external LLM.
    """

    @staticmethod
    def generate_explanation(
        analytics: MarketAnalyticsSnapshot,
        fusion: SignalFusionContext,
        opportunity: OpportunityAssessment,
        readiness: EntryReadinessStatus,
        risk: RiskAssessment,
        decision_state: DecisionState,
    ) -> DecisionExplanation:
        """Generates structured natural explanation across all key decision pillars."""
        # 1. What market is doing
        trend_str = analytics.price_structure.trend.value
        regime_str = analytics.market_regime.regime.value
        price_val = analytics.price_structure.last_price
        what_market = f"NIFTY is trading at {price_val:.1f} in a {trend_str} trend under the {regime_str} market regime."

        # 2. Why setup exists
        why_setup = opportunity.rationale

        # 3. What confirms it
        confirms = "; ".join(opportunity.confirmation_requirements) if opportunity.confirmation_requirements else "Awaiting initial structural trigger."

        # 4. What invalidates it
        invalidates = opportunity.invalidation_condition

        # 5. What options are saying
        options = analytics.options_intelligence
        if options.quality.value == "VALID":
            what_options = f"PCR at {options.pcr:.2f}; Put Wall support at {options.put_wall:.0f}, Call Wall resistance at {options.call_wall:.0f}. Positioning bias: {options.bias.value}."
        else:
            what_options = "Options chain data is currently unavailable."

        # 6. Main risks
        main_risks = list(risk.risk_factors)
        if not main_risks:
            main_risks = ["Normal market volatility; adhere strictly to invalidation level."]

        # 7. Why waiting or ready
        if decision_state == DecisionState.READY_FOR_HUMAN_REVIEW:
            why_status = "All confirmation criteria are satisfied and structural invalidation is clearly defined. Ready for human review."
        elif decision_state == DecisionState.WAIT:
            why_status = f"Setup identified but waiting for confirmation trigger ({opportunity.trigger_condition})."
        elif decision_state == DecisionState.WATCH:
            why_status = "Monitoring key structural levels; no immediate entry trigger active."
        elif decision_state == DecisionState.NO_TRADE:
            why_status = "No structural edge or signals are conflicted. Favorable risk/reward not present."
        else:
            why_status = f"Trading decision is blocked: {risk.blocker_reason or 'Data quality constraints'}."

        return DecisionExplanation(
            what_market_is_doing=what_market,
            why_setup_exists=why_setup,
            what_confirms_it=confirms,
            what_invalidates_it=invalidates,
            what_options_are_saying=what_options,
            main_risks=main_risks,
            why_waiting_or_ready=why_status,
            missing_information=fusion.unavailable_factors,
        )
