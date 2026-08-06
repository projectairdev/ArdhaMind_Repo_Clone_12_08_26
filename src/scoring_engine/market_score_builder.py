from __future__ import annotations

from src.models import MarketScore, TradeContext
from src.configuration_engine.runtime import Config
from src.scoring_engine.trend_score import evaluate_trend_score
from src.scoring_engine.option_score import evaluate_option_score
from src.scoring_engine.volatility_score import evaluate_volatility_score
from src.scoring_engine.liquidity_score import evaluate_liquidity_score
from src.scoring_engine.session_score import evaluate_session_score
from src.scoring_engine.expiry_score import evaluate_expiry_score
from src.scoring_engine.confluence_score import evaluate_confluence_score


class MarketScoreBuilder:
    """
    Assembles a complete and unified MarketScore from a TradeContext.
    Calculates overall weighted market quality on a normalized 0-100 scale.
    """

    @staticmethod
    def build(context: TradeContext, schema_version: str = "1.0", pipeline_version: str = "1.0") -> MarketScore:
        # 1. Evaluate all sub-scores
        trend = evaluate_trend_score(context)
        options = evaluate_option_score(context)
        volatility = evaluate_volatility_score(context)
        liquidity = evaluate_liquidity_score(context)
        session = evaluate_session_score(context)
        expiry = evaluate_expiry_score(context)
        confluence = evaluate_confluence_score(context)
        
        # 2. Extract configuration weights for components
        scoring_config = Config.SCORING
        overall_weights = scoring_config.get("overall_weights", {})
        
        w_trend = overall_weights.get("trend", 20.0)
        w_options = overall_weights.get("options", 25.0)
        w_volatility = overall_weights.get("volatility", 15.0)
        w_liquidity = overall_weights.get("liquidity", 15.0)
        w_session = overall_weights.get("session", 10.0)
        w_expiry = overall_weights.get("expiry", 5.0)
        w_confluence = overall_weights.get("confluence", 10.0)
        
        total_weight = w_trend + w_options + w_volatility + w_liquidity + w_session + w_expiry + w_confluence
        
        # Calculate overall weighted sum
        weighted_sum = (
            trend.overall_trend_score * w_trend +
            options.overall_option_score * w_options +
            volatility.overall_volatility_score * w_volatility +
            liquidity.overall_liquidity_score * w_liquidity +
            session.overall_session_score * w_session +
            expiry.overall_expiry_score * w_expiry +
            confluence.overall_confluence_score * w_confluence
        )
        
        overall_score = float(round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0)
        overall_score = min(100.0, max(0.0, overall_score))
        
        # 3. Determine Letter Grade
        if overall_score >= 95.0:
            letter_grade = "A+"
        elif overall_score >= 90.0:
            letter_grade = "A"
        elif overall_score >= 85.0:
            letter_grade = "B+"
        elif overall_score >= 75.0:
            letter_grade = "B"
        elif overall_score >= 60.0:
            letter_grade = "C"
        elif overall_score >= 40.0:
            letter_grade = "D"
        else:
            letter_grade = "F"
            
        # 4. Classify Market Environment (Descriptive only, no Buy/Sell indication)
        if overall_score >= 90.0:
            classification = "Excellent"
        elif overall_score >= 75.0:
            classification = "Good"
        elif overall_score >= 60.0:
            classification = "Average"
        else:
            classification = "Weak"
            
        return MarketScore(
            trend=trend,
            options=options,
            volatility=volatility,
            liquidity=liquidity,
            session=session,
            expiry=expiry,
            confluence=confluence,
            overall_score=overall_score,
            letter_grade=letter_grade,
            classification=classification,
            timestamp=context.timestamp,
            schema_version=schema_version,
            pipeline_version=pipeline_version,
        )
