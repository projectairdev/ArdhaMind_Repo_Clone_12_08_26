from __future__ import annotations

import datetime
from typing import List
from src.models import (
    TradePlan,
    TradeCandidate,
    CandidateRejection,
    PlannerStatistics,
    PlannerSummary,
)
from src.utils import now_str


class PlannerBuilder:
    """
    Assembles individual planning steps and aggregates metrics into
    a comprehensive, frozen TradePlan.
    """

    @staticmethod
    def build_trade_plan(
        raw_candidates: List[TradeCandidate],
        accepted_candidates: List[TradeCandidate],
        rejected_candidates: List[CandidateRejection],
    ) -> TradePlan:
        # 1. Compute Statistics
        total_gen = len(raw_candidates)
        total_acc = len(accepted_candidates)
        total_rej = len(rejected_candidates)

        mom_count = sum(1 for c in accepted_candidates if c.strategy_name == "MOMENTUM")
        brk_count = sum(1 for c in accepted_candidates if c.strategy_name == "BREAKOUT")
        trd_count = sum(1 for c in accepted_candidates if c.strategy_name == "TREND_FOLLOWING")
        mnr_count = sum(1 for c in accepted_candidates if c.strategy_name == "MEAN_REVERSION")
        rng_count = sum(1 for c in accepted_candidates if c.strategy_name == "RANGE")
        exp_count = sum(1 for c in accepted_candidates if c.strategy_name == "EXPIRY")
        scp_count = sum(1 for c in accepted_candidates if c.strategy_name == "SCALPING")

        avg_ranking = 0.0
        if total_acc > 0:
            avg_ranking = sum(c.ranking_score for c in accepted_candidates) / total_acc
            avg_ranking = float(round(avg_ranking, 2))

        stats = PlannerStatistics(
            total_candidates_generated=total_gen,
            total_candidates_accepted=total_acc,
            total_candidates_rejected=total_rej,
            momentum_accepted_count=mom_count,
            breakout_accepted_count=brk_count,
            trend_following_accepted_count=trd_count,
            mean_reversion_accepted_count=mnr_count,
            range_accepted_count=rng_count,
            expiry_accepted_count=exp_count,
            scalping_accepted_count=scp_count,
            average_ranking_score=avg_ranking,
        )

        # 2. Build Summary and Conclusions
        best_id = "NONE"
        conclusions: List[str] = []

        conclusions.append(f"Evaluated {total_gen} raw strategy-contract pairs across the option chain.")
        conclusions.append(f"Passed {total_acc} candidates through liquidity, spread, and bias filters; rejected {total_rej} candidates.")

        if total_acc > 0:
            best_cand = accepted_candidates[0]
            best_id = best_cand.candidate_id
            conclusions.append(
                f"Top execution candidate is {best_cand.tradingsymbol} representing {best_cand.strategy_name} "
                f"with an integrated score of {best_cand.ranking_score}/100."
            )
            # Add breakdown of accepted strategies
            active_strategies = []
            if mom_count > 0: active_strategies.append(f"MOMENTUM ({mom_count})")
            if brk_count > 0: active_strategies.append(f"BREAKOUT ({brk_count})")
            if trd_count > 0: active_strategies.append(f"TREND_FOLLOWING ({trd_count})")
            if mnr_count > 0: active_strategies.append(f"MEAN_REVERSION ({mnr_count})")
            if rng_count > 0: active_strategies.append(f"RANGE ({rng_count})")
            if exp_count > 0: active_strategies.append(f"EXPIRY ({exp_count})")
            if scp_count > 0: active_strategies.append(f"SCALPING ({scp_count})")
            
            if active_strategies:
                conclusions.append(f"Accepted candidate strategy distribution: {', '.join(active_strategies)}.")
        else:
            conclusions.append("No suitable trade setups were accepted under the current market regime.")

        summary = PlannerSummary(
            best_candidate_id=best_id,
            conclusions=conclusions,
        )

        # 3. Assemble and freeze TradePlan
        timestamp_str = now_str()
        plan_id = f"PLAN_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return TradePlan(
            trade_plan_id=plan_id,
            accepted_candidates=accepted_candidates,
            rejected_candidates=rejected_candidates,
            statistics=stats,
            summary=summary,
            timestamp=timestamp_str,
            schema_version="1.0",
            pipeline_version="1.0",
        )
