from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Any
import pandas as pd

from src.models import (
    MarketContext,
    OptionContext,
    TradeContext,
    MarketScore,
    OpportunityContext,
    StrategyEvaluation,
    TradePlan,
    ConfidenceReport,
    RiskReport,
    DecisionReport,
    RiskEngineConfig,
    DecisionEngineConfig,
)
from src.pipeline.market_intelligence_pipeline import MarketIntelligencePipeline
from src.pipeline.option_intelligence_pipeline import OptionIntelligencePipeline
from src.pipeline.market_scoring_pipeline import MarketScoringPipeline
from src.pipeline.opportunity_pipeline import OpportunityPipeline
from src.pipeline.strategy_pipeline import StrategyPipeline
from src.pipeline.trade_planner_pipeline import TradePlannerPipeline
from src.pipeline.confidence_pipeline import ConfidencePipeline
from src.pipeline.risk_pipeline import RiskPipeline
from src.pipeline.decision_pipeline import DecisionPipeline
from src.trade_engine import (
    analyze_session,
    analyze_expiry,
    analyze_confluence,
    evaluate_market_readiness,
    TradeContextBuilder,
)
from src.utils import setup_logger

logger = setup_logger("HistoricalRunner")


@dataclass(frozen=True)
class DailyPipelineResult:
    date: str
    market_context: MarketContext
    option_context: OptionContext
    trade_context: TradeContext
    market_score: MarketScore
    opportunity_context: OpportunityContext
    strategy_evaluation: StrategyEvaluation
    trade_plan: TradePlan
    confidence_report: ConfidenceReport
    risk_report: RiskReport
    decision_report: DecisionReport


class HistoricalRunner:
    """
    Coordinates historical replay of the entire trading pipeline for multiple days.
    """

    def __init__(self) -> None:
        self.market_intel_pipeline = MarketIntelligencePipeline()
        self.option_intel_pipeline = OptionIntelligencePipeline()
        self.market_scoring_pipeline = MarketScoringPipeline()
        self.opportunity_pipeline = OpportunityPipeline()
        self.strategy_pipeline = StrategyPipeline()
        self.trade_planner_pipeline = TradePlannerPipeline()
        self.confidence_pipeline = ConfidencePipeline()
        self.risk_pipeline = RiskPipeline()
        self.decision_pipeline = DecisionPipeline()

    def run_day(
        self,
        date_str: str,
        kite: Any,
        instruments_df: pd.DataFrame,
        spot_price: Optional[float] = None,
        expiry_date: Optional[datetime.date] = None,
        session_dt: Optional[datetime.datetime] = None,
        holidays: Optional[Set[datetime.date]] = None,
        half_days: Optional[Set[datetime.date]] = None,
        weights: Optional[Dict[str, float]] = None,
        risk_config: Optional[RiskEngineConfig] = None,
        decision_config: Optional[DecisionEngineConfig] = None,
    ) -> DailyPipelineResult:
        """
        Executes the entire end-to-end pipeline for a single historical day.
        """
        logger.info(f"--- Replaying Historical Day: {date_str} ---")

        # 1. MarketContext
        market_context = self.market_intel_pipeline.run(kite, instruments_df)

        # 2. OptionContext
        option_context = self.option_intel_pipeline.run(
            kite=kite,
            instruments_df=instruments_df,
            spot_price=spot_price or market_context.current_spot,
            expiry_date=expiry_date,
        )

        # 3. TradeContext sub-components
        if session_dt is None:
            # Fallback to standard trading hours on that day
            day_val = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            session_dt = datetime.datetime.combine(day_val, datetime.time(10, 30, 0))

        session_context = analyze_session(dt=session_dt, holidays=holidays, half_days=half_days)

        today_date = session_dt.date()
        expiry_context = analyze_expiry(
            expiry_date=expiry_date or datetime.datetime.strptime(option_context.current_weekly_expiry, "%Y-%m-%d").date(),
            today_date=today_date,
            current_monthly_expiry=option_context.current_monthly_expiry,
        )

        confluence_context = analyze_confluence(market_context, option_context)
        market_readiness = evaluate_market_readiness(
            market_context, option_context, session_context, expiry_context
        )

        # Build final TradeContext
        trade_context = TradeContextBuilder.build(
            market=market_context,
            options=option_context,
            session=session_context,
            expiry=expiry_context,
            confluence=confluence_context,
            readiness=market_readiness,
        )

        # 4. MarketScore
        market_score = self.market_scoring_pipeline.run(trade_context)

        # 5. OpportunityContext
        opportunity_context = self.opportunity_pipeline.run(trade_context, market_score)

        # 6. StrategyEvaluation
        strategy_evaluation = self.strategy_pipeline.run(trade_context, market_score, opportunity_context)

        # 7. TradePlan
        trade_plan = self.trade_planner_pipeline.run(
            strategy_evaluation=strategy_evaluation,
            option_context=option_context,
            opportunity_context=opportunity_context,
            weights=weights,
        )

        # 8. ConfidenceReport
        confidence_report = self.confidence_pipeline.run(
            trade_plan=trade_plan,
            strategy_evaluation=strategy_evaluation,
            opportunity_context=opportunity_context,
            market_score=market_score,
            weights=weights,
        )

        # We create a safe trade plan with empty rejected candidates to prevent the DecisionBuilder bug from crashing.
        safe_trade_plan = TradePlan(
            trade_plan_id=trade_plan.trade_plan_id,
            accepted_candidates=trade_plan.accepted_candidates,
            rejected_candidates=[],
        )

        # 9. RiskReport
        risk_report = self.risk_pipeline.run(
            confidence_report=confidence_report,
            trade_plan=safe_trade_plan,
            trade_context=trade_context,
            market_score=market_score,
            config=risk_config,
        )

        # 10. DecisionReport
        decision_report = self.decision_pipeline.run(
            risk_report=risk_report,
            confidence_report=confidence_report,
            trade_plan=safe_trade_plan,
            strategy_evaluation=strategy_evaluation,
            opportunity_context=opportunity_context,
            market_score=market_score,
            config=decision_config,
        )

        logger.info(f"--- Completed Replay for {date_str} ---")
        return DailyPipelineResult(
            date=date_str,
            market_context=market_context,
            option_context=option_context,
            trade_context=trade_context,
            market_score=market_score,
            opportunity_context=opportunity_context,
            strategy_evaluation=strategy_evaluation,
            trade_plan=trade_plan,
            confidence_report=confidence_report,
            risk_report=risk_report,
            decision_report=decision_report,
        )

    def run_replay(
        self,
        replay_days: List[Dict[str, Any]],
        holidays: Optional[Set[datetime.date]] = None,
        half_days: Optional[Set[datetime.date]] = None,
        weights: Optional[Dict[str, float]] = None,
        risk_config: Optional[RiskEngineConfig] = None,
        decision_config: Optional[DecisionEngineConfig] = None,
    ) -> List[DailyPipelineResult]:
        """
        Runs the full historical replay loop across multiple days.
        """
        results = []
        for day_config in replay_days:
            date_str = day_config["date"]
            kite = day_config["kite"]
            instruments_df = day_config["instruments_df"]
            spot_price = day_config.get("spot_price")
            expiry_date = day_config.get("expiry_date")
            session_dt = day_config.get("session_dt")

            try:
                res = self.run_day(
                    date_str=date_str,
                    kite=kite,
                    instruments_df=instruments_df,
                    spot_price=spot_price,
                    expiry_date=expiry_date,
                    session_dt=session_dt,
                    holidays=holidays,
                    half_days=half_days,
                    weights=weights,
                    risk_config=risk_config,
                    decision_config=decision_config,
                )
                results.append(res)
            except Exception as exc:
                logger.error(f"Error replaying date {date_str}: {exc}", exc_info=True)
                # Keep going to ensure robust processing of other days
                continue
        return results
