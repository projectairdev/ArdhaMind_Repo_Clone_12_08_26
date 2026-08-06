from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional
from src.models import (
    TradePlan,
    ConfidenceReport,
    TradeContext,
    MarketScore,
    RiskEngineConfig,
    RiskReport,
    CandidateRisk,
    RiskSummary,
)
from src.risk_engine_v2.allocation import calculate_allocation, determine_risk_grade
from src.risk_engine_v2.constraints import evaluate_candidate_constraints
from src.risk_engine_v2.exposure import calculate_portfolio_exposures
from src.risk_engine_v2.warnings import generate_portfolio_warnings, generate_candidate_warnings
from src.risk_engine_v2.portfolio import apply_portfolio_level_limits


class RiskBuilder:
    """
    Stateless builder that coordinates independent candidate evaluation,
    portfolio constraint enforcement, exposure aggregation, and risk warnings generation
    to construct the final RiskReport.
    """

    @staticmethod
    def build_risk_report(
        trade_plan: TradePlan,
        confidence_report: ConfidenceReport,
        trade_context: TradeContext,
        market_score: MarketScore,
        config: Optional[RiskEngineConfig] = None,
    ) -> RiskReport:
        if config is None:
            config = RiskEngineConfig()

        # Create a lookup for candidate confidence scores
        confidence_map = {
            c.candidate_id: c.confidence_score for c in confidence_report.candidate_confidences
        }

        raw_candidate_risks: List[CandidateRisk] = []
        ranking_scores: List[float] = []

        # 1. Independent Candidate Evaluation
        for candidate in trade_plan.accepted_candidates:
            # Match confidence score
            confidence = confidence_map.get(candidate.candidate_id, 50.0)

            # Calculate allocation
            allocation = calculate_allocation(
                candidate=candidate,
                confidence_score=confidence,
                option_context=trade_context.options,
                config=config,
            )

            # Evaluate constraints
            constraints, is_approved = evaluate_candidate_constraints(
                candidate=candidate,
                confidence_score=confidence,
                allocated_capital=allocation.allocated_capital,
                config=config,
            )

            # Base risk grade
            risk_grade = determine_risk_grade(candidate, allocation, is_approved)

            # Build initial CandidateRisk
            cand_risk = CandidateRisk(
                candidate_id=candidate.candidate_id,
                tradingsymbol=candidate.tradingsymbol,
                strategy_name=candidate.strategy_name,
                risk_grade=risk_grade,
                capital_allocation=allocation,
                warnings=[],
                constraints=constraints,
                is_approved=is_approved,
            )

            # Dynamic candidate warnings
            cand_warnings = generate_candidate_warnings(cand_risk)
            cand_risk = CandidateRisk(
                candidate_id=cand_risk.candidate_id,
                tradingsymbol=cand_risk.tradingsymbol,
                strategy_name=cand_risk.strategy_name,
                risk_grade=cand_risk.risk_grade,
                capital_allocation=cand_risk.capital_allocation,
                warnings=cand_warnings,
                constraints=cand_risk.constraints,
                is_approved=cand_risk.is_approved,
            )

            raw_candidate_risks.append(cand_risk)
            # Use ranking score from candidate if available, otherwise fallback to confidence
            ranking_scores.append(candidate.ranking_score if candidate.ranking_score > 0 else confidence)

        # 2. Portfolio-Level Constraints & Limits (Max concurrent, Max portfolio exposure)
        portfolio_candidate_risks = apply_portfolio_level_limits(
            candidate_risks=raw_candidate_risks,
            ranking_scores=ranking_scores,
            config=config,
        )

        # 3. Aggregate Portfolio Exposures
        exposure_summary = calculate_portfolio_exposures(
            candidate_risks=portfolio_candidate_risks,
            config=config,
        )

        # 4. Generate Portfolio Warnings
        portfolio_warnings = generate_portfolio_warnings(
            exposure=exposure_summary,
            config=config,
        )

        # 5. Compile Conclusions and Overall Summary
        approved_candidates = [r for r in portfolio_candidate_risks if r.is_approved]
        
        # Sort approved by capital allocation to find highest and lowest risk
        sorted_approved = sorted(approved_candidates, key=lambda x: x.capital_allocation.allocated_capital)
        highest_risk_id = sorted_approved[-1].candidate_id if sorted_approved else "NONE"
        lowest_risk_id = sorted_approved[0].candidate_id if sorted_approved else "NONE"

        # Portfolio Risk Grade selection
        total_warnings = len(portfolio_warnings) + sum(len(r.warnings) for r in portfolio_candidate_risks if r.is_approved)
        if exposure_summary.portfolio_utilization_pct > 60.0 or total_warnings >= 3:
            portfolio_risk_grade = "AGGRESSIVE"
        elif exposure_summary.portfolio_utilization_pct > 30.0 or total_warnings >= 1:
            portfolio_risk_grade = "MODERATE"
        else:
            portfolio_risk_grade = "CONSERVATIVE"

        # Build human-friendly conclusions
        conclusions = []
        conclusions.append(f"Risk evaluation complete. Portfolio risk profile is {portfolio_risk_grade}.")
        conclusions.append(f"Approved {len(approved_candidates)} out of {len(trade_plan.accepted_candidates)} trade candidates.")
        conclusions.append(f"Allocated capital: {exposure_summary.total_capital_allocated:.2f} / {config.max_portfolio_exposure:.2f}.")
        conclusions.append(f"Portfolio utilization is {exposure_summary.portfolio_utilization_pct:.2f}%.")
        
        for warning in portfolio_warnings:
            conclusions.append(f"[{warning.severity}] {warning.message}")

        summary = RiskSummary(
            highest_risk_candidate_id=highest_risk_id,
            lowest_risk_candidate_id=lowest_risk_id,
            portfolio_risk_grade=portfolio_risk_grade,
            total_warnings=total_warnings,
            conclusions=conclusions,
        )

        # Generate report UUID and timestamp
        report_id = f"RISK_REPORT_{uuid.uuid4().hex[:8].upper()}"
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return RiskReport(
            report_id=report_id,
            confidence_report_id=confidence_report.report_id,
            candidate_risks=portfolio_candidate_risks,
            exposure_summary=exposure_summary,
            summary=summary,
            timestamp=timestamp_str,
            schema_version="2.0",
            engine_version="2.0",
        )
