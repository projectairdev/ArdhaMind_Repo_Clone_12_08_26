from __future__ import annotations

from src.pipeline.market_intelligence_pipeline import MarketIntelligencePipeline
from src.pipeline.option_intelligence_pipeline import OptionIntelligencePipeline
from src.pipeline.market_scoring_pipeline import MarketScoringPipeline
from src.pipeline.opportunity_pipeline import OpportunityPipeline
from src.pipeline.strategy_pipeline import StrategyPipeline
from src.pipeline.trade_planner_pipeline import TradePlannerPipeline
from src.pipeline.confidence_pipeline import ConfidencePipeline
from src.pipeline.risk_pipeline import RiskPipeline
from src.pipeline.decision_pipeline import DecisionPipeline
from src.pipeline.optimization_pipeline import OptimizationPipeline
from src.pipeline.intraday_pipeline import IntradayPipeline
from src.pipeline.news_pipeline import NewsPipeline

def __getattr__(name: str):
    if name == "ValidationPipeline":
        from src.pipeline.validation_pipeline import ValidationPipeline
        return ValidationPipeline
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    "MarketIntelligencePipeline",
    "OptionIntelligencePipeline",
    "MarketScoringPipeline",
    "OpportunityPipeline",
    "StrategyPipeline",
    "TradePlannerPipeline",
    "ConfidencePipeline",
    "RiskPipeline",
    "DecisionPipeline",
    "ValidationPipeline",
    "OptimizationPipeline",
    "IntradayPipeline",
    "NewsPipeline",
]




