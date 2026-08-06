from __future__ import annotations

from typing import Optional
from src.models import (
    TradeContext,
    MarketScore,
    OpportunityContext,
    MarketBreadthContext,
    GlobalContext,
)
from src.opportunity_engine.strength import evaluate_opportunity_strength
from src.opportunity_engine.warnings import evaluate_warnings
from src.opportunity_engine.invalidation import evaluate_invalidation_factors
from src.opportunity_engine.classification import (
    evaluate_directional_bias,
    evaluate_strategy_suitability,
    evaluate_opportunity_classification,
)
from src.opportunity_engine.market_breadth import evaluate_market_breadth
from src.opportunity_engine.global_context import evaluate_global_context


class OpportunityContextBuilder:
    """
    Stateless builder that coordinates all opportunity evaluation sub-modules
    to produce a unified OpportunityContext from trade and market scoring data.
    """

    @staticmethod
    def build(
        context: TradeContext,
        score: MarketScore,
        breadth: Optional[MarketBreadthContext] = None,
        global_ctx: Optional[GlobalContext] = None,
        schema_version: str = "1.0",
        pipeline_version: str = "1.0",
    ) -> OpportunityContext:
        # 1. Resolve optional context pieces with graceful degradation
        breadth_resolved = evaluate_market_breadth(breadth)
        global_resolved = evaluate_global_context(global_ctx)
        
        # 2. Evaluate physical opportunity strength
        strength = evaluate_opportunity_strength(context)
        
        # 3. Evaluate structured warnings
        warnings = evaluate_warnings(context)
        
        # 4. Evaluate directional bias
        directional_bias = evaluate_directional_bias(context)
        
        # 5. Evaluate strategy suitabilities (suitability profile)
        profile = evaluate_strategy_suitability(context, score)
        
        # 6. Evaluate invalidation factors based on current directional bias
        invalidation_factors = evaluate_invalidation_factors(context, directional_bias.value)
        
        # 7. Classify opportunity tier
        classification = evaluate_opportunity_classification(context, score, warnings)
        
        # 8. Determine if a tradeable opportunity exists
        has_opportunity = classification.value in ["EXCELLENT", "GOOD", "WATCHLIST"]
        
        return OpportunityContext(
            classification=classification,
            profile=profile,
            strength=strength,
            directional_bias=directional_bias,
            warnings=warnings,
            invalidation_factors=invalidation_factors,
            has_opportunity=has_opportunity,
            timestamp=context.timestamp,
            breadth=breadth_resolved,
            global_ctx=global_resolved,
            schema_version=schema_version,
            pipeline_version=pipeline_version,
        )
