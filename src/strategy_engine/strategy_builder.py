from __future__ import annotations

from src.models import (
    TradeContext,
    MarketScore,
    OpportunityContext,
    StrategyEvaluation,
    StrategyScore,
    EvaluationSummary,
)
from src.strategy_engine.momentum import evaluate_momentum
from src.strategy_engine.breakout import evaluate_breakout
from src.strategy_engine.trend_following import evaluate_trend_following
from src.strategy_engine.mean_reversion import evaluate_mean_reversion
from src.strategy_engine.range import evaluate_range
from src.strategy_engine.expiry import evaluate_expiry
from src.strategy_engine.scalping import evaluate_scalping


class StrategyEvaluationBuilder:
    """
    Stateless builder that runs independent strategy evaluations and
    assembles the final composite StrategyEvaluation.
    """

    @staticmethod
    def build(
        trade_context: TradeContext,
        market_score: MarketScore,
        opportunity_context: OpportunityContext,
        schema_version: str = "1.0",
        pipeline_version: str = "1.0",
    ) -> StrategyEvaluation:
        # 1. Run all independent strategy evaluators
        momentum_eval = evaluate_momentum(trade_context, market_score, opportunity_context)
        breakout_eval = evaluate_breakout(trade_context, market_score, opportunity_context)
        trend_following_eval = evaluate_trend_following(trade_context, market_score, opportunity_context)
        mean_reversion_eval = evaluate_mean_reversion(trade_context, market_score, opportunity_context)
        range_eval = evaluate_range(trade_context, market_score, opportunity_context)
        expiry_eval = evaluate_expiry(trade_context, market_score, opportunity_context)
        scalping_eval = evaluate_scalping(trade_context, market_score, opportunity_context)
        
        evaluations = [
            momentum_eval,
            breakout_eval,
            trend_following_eval,
            mean_reversion_eval,
            range_eval,
            expiry_eval,
            scalping_eval,
        ]
        
        # 2. Determine overall best strategy by suitability score
        valid_evals = [e for e in evaluations if e.suitability_level != "NONE"]
        if valid_evals:
            sorted_evals = sorted(valid_evals, key=lambda x: x.suitability_score, reverse=True)
            overall_best_strategy = sorted_evals[0].strategy_name if sorted_evals[0].suitability_score > 0 else "NONE"
        else:
            overall_best_strategy = "NONE"
        
        # 3. Build top strategies list (Suitability level HIGH or MEDIUM)
        suitable_strategies = [e for e in evaluations if e.suitability_level in ["HIGH", "MEDIUM"]]
        suitable_strategies_sorted = sorted(suitable_strategies, key=lambda x: x.suitability_score, reverse=True)
        top_strategies = [e.strategy_name for e in suitable_strategies_sorted]
        
        suitable_count = len(suitable_strategies)
        unsuitable_count = len(evaluations) - suitable_count
        
        # 4. Formulate conclusions
        conclusions: list[str] = []
        if overall_best_strategy != "NONE":
            conclusions.append(
                f"The overall most suitable trading style is {overall_best_strategy} with a suitability score of {sorted_evals[0].suitability_score:.1f}%."
            )
        else:
            conclusions.append("No suitable strategies were identified for the current market environment.")
            
        if suitable_count > 0:
            conclusions.append(f"There are {suitable_count} active strategy configurations matching current conditions: {', '.join(top_strategies)}.")
        else:
            conclusions.append("Market conditions or option parameters do not satisfy the minimum requirements for active setups.")
            
        # Specific structural highlights
        if range_eval.suitability_level == "HIGH":
            conclusions.append("Sideways channels are highly consolidated. Income-generating option premium collection models are favored.")
        elif trend_following_eval.suitability_level == "HIGH":
            conclusions.append("Spot and option chain indicators strongly align in a structural trend. Trend riding configurations are favored.")
            
        summary = EvaluationSummary(
            top_strategies=top_strategies,
            suitable_strategies_count=suitable_count,
            unsuitable_strategies_count=unsuitable_count,
            conclusions=conclusions,
        )
        
        return StrategyEvaluation(
            overall_best_strategy=overall_best_strategy,
            evaluations=evaluations,
            momentum_evaluation=momentum_eval,
            breakout_evaluation=breakout_eval,
            trend_following_evaluation=trend_following_eval,
            mean_reversion_evaluation=mean_reversion_eval,
            range_evaluation=range_eval,
            expiry_evaluation=expiry_eval,
            scalping_evaluation=scalping_eval,
            summary=summary,
            timestamp=trade_context.timestamp,
            schema_version=schema_version,
            pipeline_version=pipeline_version,
        )
