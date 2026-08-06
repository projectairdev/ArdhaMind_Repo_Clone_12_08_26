from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional
from src.models import (
    RiskReport,
    ConfidenceReport,
    TradePlan,
    StrategyEvaluation,
    OpportunityContext,
    MarketScore,
    DecisionEngineConfig,
    DecisionReport,
    CandidateDecision,
    DecisionSummary,
    DecisionStatistics,
    DecisionReason,
)
from src.decision_engine.decision_rules import evaluate_candidate_decision
from src.decision_engine.decision_priority import calculate_priority_score, assign_execution_priorities
from src.decision_engine.decision_explanations import generate_explanations
from src.decision_engine.decision_filters import check_global_market_blockers


class DecisionBuilder:
    """
    Stateless coordinator that builds the final DecisionReport based on the inputs from
    the Risk Engine, Confidence Engine, Trade Planner, Strategy Evaluation, and Market contexts.
    """

    @staticmethod
    def build_decision_report(
        risk_report: RiskReport,
        confidence_report: ConfidenceReport,
        trade_plan: TradePlan,
        strategy_evaluation: StrategyEvaluation,
        opportunity_context: OpportunityContext,
        market_score: Optional[MarketScore] = None,
        config: Optional[DecisionEngineConfig] = None,
    ) -> DecisionReport:
        if config is None:
            config = DecisionEngineConfig()

        # 1. Lookups for mapping candidate attributes
        confidence_map = {
            c.candidate_id: c.confidence_score for c in confidence_report.candidate_confidences
        }
        risk_map = {
            r.candidate_id: r for r in risk_report.candidate_risks
        }

        # Combine all candidates from trade plan (accepted and rejected)
        all_candidates = list(trade_plan.accepted_candidates) + list(trade_plan.rejected_candidates)
        # Avoid duplicates just in case
        unique_candidates = {c.candidate_id: c for c in all_candidates}.values()

        preliminary_decisions: List[CandidateDecision] = []

        # 2. Check for global market blockers (e.g. extreme risk-off or unready market)
        global_blockers = []
        if market_score is not None:
            global_blockers = check_global_market_blockers(market_score, opportunity_context)

        # 3. Evaluate each candidate
        for candidate in unique_candidates:
            confidence = confidence_map.get(candidate.candidate_id, 50.0)
            risk_cand = risk_map.get(candidate.candidate_id)

            # Evaluate base decision
            if global_blockers:
                decision = "WATCH"
            else:
                if risk_cand is None:
                    # No risk engine info, reject
                    decision = "REJECT"
                else:
                    decision = evaluate_candidate_decision(
                        candidate=candidate,
                        confidence_score=confidence,
                        risk_cand=risk_cand,
                        config=config,
                    )

            # Calculate priority score
            allocated_cap = risk_cand.capital_allocation.allocated_capital if risk_cand else 0.0
            priority_score = calculate_priority_score(
                confidence_score=confidence,
                tradability_score=candidate.tradability_score,
                allocated_capital=allocated_cap,
                config=config,
            )

            # Generate structured explanations, evidence, and warnings
            explanation, supporting, blocking, warnings = generate_explanations(
                candidate=candidate,
                confidence_score=confidence,
                risk_cand=risk_cand,
                decision=decision,
            )

            # If global blockers are active, override explanation and add to blocking factors
            if global_blockers and decision in ("BUY", "SELL", "WATCH"):
                for blocker in global_blockers:
                    blocking.append(
                        DecisionReason(
                            reason_type="GLOBAL_MARKET_BLOCKER",
                            message=blocker,
                            metric_name="global_market_ready",
                            metric_value=0.0,
                        )
                    )
                explanation = "Trade set to WATCH due to global market blockers."

            # Construct preliminary CandidateDecision
            allocated_lots = risk_cand.capital_allocation.allocated_lots if risk_cand else 0
            dec_cand = CandidateDecision(
                candidate_id=candidate.candidate_id,
                tradingsymbol=candidate.tradingsymbol,
                strategy_name=candidate.strategy_name,
                decision=decision,
                priority_score=priority_score,
                execution_priority=-1,  # updated next
                explanation=explanation,
                supporting_evidence=supporting,
                blocking_factors=blocking,
                warnings=warnings,
                allocated_capital=allocated_cap,
                allocated_lots=allocated_lots,
                expiry_reason=getattr(candidate, "expiry_reason", ""),
            )
            preliminary_decisions.append(dec_cand)

        # 4. Process execution priorities (handles max concurrent slots and tie-breaking)
        final_decisions = assign_execution_priorities(preliminary_decisions, config)

        # 5. Extract statistics
        buy_count = sum(1 for d in final_decisions if d.decision == "BUY")
        sell_count = sum(1 for d in final_decisions if d.decision == "SELL")
        watch_count = sum(1 for d in final_decisions if d.decision == "WATCH")
        reject_count = sum(1 for d in final_decisions if d.decision == "REJECT")
        no_trade_count = sum(1 for d in final_decisions if d.decision == "NO TRADE")
        total_allocated = sum(d.allocated_capital for d in final_decisions if d.decision in ("BUY", "SELL"))

        stats = DecisionStatistics(
            total_candidates_evaluated=len(final_decisions),
            buy_count=buy_count,
            sell_count=sell_count,
            watch_count=watch_count,
            reject_count=reject_count,
            no_trade_count=no_trade_count,
            total_allocated_capital=float(round(total_allocated, 2)),
        )

        # 6. Priority ranking list
        priority_list = [
            d.candidate_id for d in sorted(
                [d for d in final_decisions if d.execution_priority > 0],
                key=lambda x: x.execution_priority
            )
        ]

        # 7. Create summary
        highest_priority_id = priority_list[0] if priority_list else "NONE"
        overall_action = "EXECUTE" if priority_list else "HOLD"
        portfolio_status_message = (
            f"Approved {len(priority_list)} trades for execution with total capital {total_allocated:.2f}."
            if priority_list else "No trades approved for execution. Monitoring mode active."
        )

        conclusions = []
        conclusions.append(f"Decision evaluation completed. Action: {overall_action}.")
        conclusions.append(portfolio_status_message)
        conclusions.append(f"Execution priorities: {', '.join(priority_list) if priority_list else 'None'}")
        if global_blockers:
            conclusions.append(f"Global blockers detected: {len(global_blockers)}")

        summary = DecisionSummary(
            overall_action=overall_action,
            highest_priority_candidate_id=highest_priority_id,
            portfolio_status_message=portfolio_status_message,
            conclusions=conclusions,
        )

        report_id = f"DECISION_REPORT_{uuid.uuid4().hex[:8].upper()}"
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return DecisionReport(
            report_id=report_id,
            risk_report_id=risk_report.report_id,
            candidate_decisions=final_decisions,
            priority_ranking=priority_list,
            summary=summary,
            stats=stats,
            timestamp=timestamp_str,
            schema_version="2.0",
            engine_version="2.0",
        )
