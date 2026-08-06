from __future__ import annotations

from typing import List, Tuple
from src.models import (
    CandidateRisk,
    RiskEngineConfig,
    PortfolioConstraint,
    CapitalAllocation,
)


def apply_portfolio_level_limits(
    candidate_risks: List[CandidateRisk],
    ranking_scores: List[float],  # scores to sort by (higher is better)
    config: RiskEngineConfig,
) -> List[CandidateRisk]:
    """
    Enforces portfolio-wide limits: max concurrent trades and max portfolio exposure.
    Prioritizes candidates with higher ranking scores.
    """
    # 1. Zip candidate risks with ranking scores
    paired_candidates = list(zip(candidate_risks, ranking_scores))

    # 2. Sort candidates: approved first, then by ranking score descending
    paired_candidates.sort(key=lambda x: (x[0].is_approved, x[1]), reverse=True)

    adjusted_risks: List[CandidateRisk] = []
    current_approved_count = 0
    accumulated_exposure = 0.0

    for risk, score in paired_candidates:
        # If candidate was already rejected by individual checks, keep it rejected
        if not risk.is_approved:
            adjusted_risks.append(risk)
            continue

        # Check Max Concurrent Trades limit
        concurrent_violated = current_approved_count >= config.max_concurrent_trades
        new_constraints = list(risk.constraints)
        
        new_constraints.append(
            PortfolioConstraint(
                constraint_type="MAX_CONCURRENT_TRADES",
                limit_value=float(config.max_concurrent_trades),
                current_value=float(current_approved_count + 1),
                is_violated=concurrent_violated,
            )
        )

        if concurrent_violated:
            # Reclassify as rejected due to concurrent trade limit
            new_allocation = CapitalAllocation(
                allocated_capital=0.0,
                allocated_lots=0,
                risk_amount=0.0,
                utilization_pct=0.0,
                confidence_score=risk.capital_allocation.confidence_score,
                risk_multiplier=risk.capital_allocation.risk_multiplier,
            )
            adjusted_risks.append(
                CandidateRisk(
                    candidate_id=risk.candidate_id,
                    tradingsymbol=risk.tradingsymbol,
                    strategy_name=risk.strategy_name,
                    risk_grade="REJECTED",
                    capital_allocation=new_allocation,
                    warnings=risk.warnings,
                    constraints=new_constraints,
                    is_approved=False,
                )
            )
            continue

        # Check Portfolio Exposure limit
        proposed_capital = risk.capital_allocation.allocated_capital
        exposure_violated = (accumulated_exposure + proposed_capital) > config.max_portfolio_exposure
        
        if exposure_violated:
            # Try to scale down lots to fit inside remaining exposure
            remaining_exposure = config.max_portfolio_exposure - accumulated_exposure
            if remaining_exposure > 0 and risk.capital_allocation.allocated_lots > 0:
                cost_per_lot = proposed_capital / risk.capital_allocation.allocated_lots
                allowed_lots = int(remaining_exposure // cost_per_lot)
                
                if allowed_lots > 0:
                    scaled_capital = float(allowed_lots * cost_per_lot)
                    new_allocation = CapitalAllocation(
                        allocated_capital=float(round(scaled_capital, 2)),
                        allocated_lots=allowed_lots,
                        risk_amount=float(round(scaled_capital, 2)),
                        utilization_pct=float(round((scaled_capital / config.total_portfolio_value) * 100.0, 4)) if config.total_portfolio_value > 0 else 0.0,
                        confidence_score=risk.capital_allocation.confidence_score,
                        risk_multiplier=risk.capital_allocation.risk_multiplier,
                    )
                    accumulated_exposure += scaled_capital
                    current_approved_count += 1
                    
                    new_constraints.append(
                        PortfolioConstraint(
                            constraint_type="PORTFOLIO_EXPOSURE_FIT",
                            limit_value=config.max_portfolio_exposure,
                            current_value=accumulated_exposure,
                            is_violated=False,
                        )
                    )
                    
                    adjusted_risks.append(
                        CandidateRisk(
                            candidate_id=risk.candidate_id,
                            tradingsymbol=risk.tradingsymbol,
                            strategy_name=risk.strategy_name,
                            risk_grade=risk.risk_grade,
                            capital_allocation=new_allocation,
                            warnings=risk.warnings,
                            constraints=new_constraints,
                            is_approved=True,
                        )
                    )
                    continue

            # If we cannot even allocate 1 lot within the limit
            new_allocation = CapitalAllocation(
                allocated_capital=0.0,
                allocated_lots=0,
                risk_amount=0.0,
                utilization_pct=0.0,
                confidence_score=risk.capital_allocation.confidence_score,
                risk_multiplier=risk.capital_allocation.risk_multiplier,
            )
            new_constraints.append(
                PortfolioConstraint(
                    constraint_type="PORTFOLIO_EXPOSURE_BREACH",
                    limit_value=config.max_portfolio_exposure,
                    current_value=accumulated_exposure + proposed_capital,
                    is_violated=True,
                )
            )
            adjusted_risks.append(
                CandidateRisk(
                    candidate_id=risk.candidate_id,
                    tradingsymbol=risk.tradingsymbol,
                    strategy_name=risk.strategy_name,
                    risk_grade="REJECTED",
                    capital_allocation=new_allocation,
                    warnings=risk.warnings,
                    constraints=new_constraints,
                    is_approved=False,
                )
            )
        else:
            # Fully approved within exposure limits
            accumulated_exposure += proposed_capital
            current_approved_count += 1
            adjusted_risks.append(
                CandidateRisk(
                    candidate_id=risk.candidate_id,
                    tradingsymbol=risk.tradingsymbol,
                    strategy_name=risk.strategy_name,
                    risk_grade=risk.risk_grade,
                    capital_allocation=risk.capital_allocation,
                    warnings=risk.warnings,
                    constraints=new_constraints,
                    is_approved=True,
                )
            )

    return adjusted_risks
