from __future__ import annotations

import datetime
from typing import Dict, List, Optional
from src.models import (
    TradePlan,
    StrategyEvaluation,
    OpportunityContext,
    MarketScore,
    CandidateConfidence,
    ConfidenceReport,
    ConfidenceSummary,
)
from src.confidence_engine.bonuses import BonusCalculator
from src.confidence_engine.penalties import PenaltyCalculator
from src.confidence_engine.normalizer import ScoreNormalizer
from src.confidence_engine.explanation import ExplanationGenerator
from src.utils import now_str


class ConfidenceBuilder:
    """
    Coordinates sub-score evaluations, applies bonuses and penalties,
    invokes generators, and builds the immutable ConfidenceReport.
    """

    DEFAULT_WEIGHTS: Dict[str, float] = {
        "strategy_suitability": 0.15,
        "opportunity_quality": 0.15,
        "market_score": 0.10,
        "liquidity": 0.10,
        "iv": 0.10,
        "oi": 0.10,
        "spread": 0.10,
        "trend_agreement": 0.10,
        "expiry_suitability": 0.05,
        "confluence": 0.05,
    }

    @classmethod
    def evaluate_all(
        cls,
        trade_plan: TradePlan,
        strategy_evaluation: StrategyEvaluation,
        opportunity_context: OpportunityContext,
        market_score: MarketScore,
        weights: Optional[Dict[str, float]] = None,
    ) -> ConfidenceReport:
        if weights is None:
            weights = cls.DEFAULT_WEIGHTS

        # 1. Normalize weights if they do not sum to 1.0
        total_weight = sum(weights.values())
        if not (0.99 <= total_weight <= 1.01) and total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}

        candidate_confidences: List[CandidateConfidence] = []

        # Iterate over all accepted candidates in the trade plan
        for cand in trade_plan.accepted_candidates:
            # 2. Compute individual sub-scores
            sub_scores: Dict[str, float] = {}
            
            # Sub-score 1: Strategy Suitability
            sub_scores["strategy_suitability"] = float(cand.suitability_score)
            
            # Sub-score 2: Opportunity Quality
            base_class_scores = {
                "EXCELLENT": 100.0,
                "GOOD": 80.0,
                "WATCHLIST": 60.0,
                "WAIT": 40.0,
                "POOR": 20.0,
                "AVOID": 0.0,
            }
            class_val = opportunity_context.classification.value if opportunity_context.classification else "GOOD"
            base_class_score = base_class_scores.get(class_val, 50.0)
            strength_val = opportunity_context.strength.overall_strength if opportunity_context.strength else 50.0
            sub_scores["opportunity_quality"] = (base_class_score + strength_val) / 2.0
            
            # Sub-score 3: Market Score
            sub_scores["market_score"] = float(market_score.overall_score)
            
            # Sub-score 4: Liquidity
            sub_scores["liquidity"] = float(cand.tradability_score)
            
            # Sub-score 5: IV
            sub_scores["iv"] = max(0.0, 100.0 - (cand.iv / 40.0) * 100.0)
            
            # Sub-score 6: OI
            sub_scores["oi"] = min(100.0, (cand.oi / 50000.0) * 100.0)
            
            # Sub-score 7: Spread
            sub_scores["spread"] = max(0.0, 100.0 - (cand.spread_pct / 0.35) * 100.0)
            
            # Sub-score 8: Trend Agreement
            bias = opportunity_context.directional_bias.value if opportunity_context.directional_bias else "NEUTRAL"
            if bias == "BULLISH":
                sub_scores["trend_agreement"] = 100.0 if cand.instrument_type == "CE" else 10.0
            elif bias == "BEARISH":
                sub_scores["trend_agreement"] = 100.0 if cand.instrument_type == "PE" else 10.0
            else:
                sub_scores["trend_agreement"] = 70.0
                
            # Sub-score 9: Expiry Suitability
            sub_scores["expiry_suitability"] = float(market_score.expiry.overall_expiry_score)
            
            # Sub-score 10: Confluence
            sub_scores["confluence"] = float(market_score.confluence.overall_confluence_score)

            # Calculate raw weighted score
            raw_score = sum(sub_scores[k] * weights.get(k, 0.10) for k in weights)

            # 3. Calculate bonuses and penalties
            bonuses = BonusCalculator.calculate_bonuses(cand, market_score, opportunity_context)
            penalties = PenaltyCalculator.calculate_penalties(cand, market_score, opportunity_context)

            # 4. Normalize and Cap score to 0 - 100
            confidence_score = ScoreNormalizer.normalize_score(raw_score, bonuses, penalties)

            # 5. Generate dynamic explanations (Positive / Negative factors)
            pos_factors, neg_factors = ExplanationGenerator.generate_explanation(
                cand=cand,
                market_score=market_score,
                opportunity_ctx=opportunity_context,
                sub_scores=sub_scores,
                weights=weights,
            )

            # Create immutable CandidateConfidence
            candidate_confidences.append(
                CandidateConfidence(
                    candidate_id=cand.candidate_id,
                    tradingsymbol=cand.tradingsymbol,
                    strategy_name=cand.strategy_name,
                    confidence_score=confidence_score,
                    raw_score=float(round(raw_score, 2)),
                    positive_factors=pos_factors,
                    negative_factors=neg_factors,
                    bonuses=bonuses,
                    penalties=penalties,
                )
            )

        # 6. Rank candidate confidences descending by confidence score
        candidate_confidences = sorted(
            candidate_confidences, key=lambda x: x.confidence_score, reverse=True
        )

        # 7. Aggregate Summary Metrics
        total_eval = len(candidate_confidences)
        avg_conf = 0.0
        highest_id = "NONE"
        lowest_id = "NONE"
        conclusions: List[str] = []

        if total_eval > 0:
            avg_conf = float(round(sum(c.confidence_score for c in candidate_confidences) / total_eval, 2))
            highest_id = candidate_confidences[0].candidate_id
            lowest_id = candidate_confidences[-1].candidate_id
            
            best_cc = candidate_confidences[0]
            conclusions.append(
                f"Evaluated {total_eval} accepted trade candidates for independent confidence scoring."
            )
            conclusions.append(
                f"Top confidence trade candidate is {best_cc.tradingsymbol} ({best_cc.strategy_name}) "
                f"with a confidence score of {best_cc.confidence_score:.1f}/100."
            )
            
            # Analyze bonuses/penalties to add specific insight
            total_active_bonuses = sum(len(cc.bonuses) for cc in candidate_confidences)
            total_active_penalties = sum(len(cc.penalties) for cc in candidate_confidences)
            conclusions.append(
                f"Accumulated {total_active_bonuses} confidence bonuses and {total_active_penalties} "
                f"confidence penalties across all analyzed candidate options."
            )
        else:
            conclusions.append("No active candidates were available to evaluate in the trade plan.")

        summary = ConfidenceSummary(
            highest_confidence_candidate_id=highest_id,
            lowest_confidence_candidate_id=lowest_id,
            average_confidence=avg_conf,
            total_evaluated=total_eval,
            conclusions=conclusions,
        )

        # 8. Assemble ConfidenceReport
        report_id = f"CONF_REP_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        timestamp_str = now_str()

        return ConfidenceReport(
            report_id=report_id,
            trade_plan_id=trade_plan.trade_plan_id,
            candidate_confidences=candidate_confidences,
            summary=summary,
            timestamp=timestamp_str,
            schema_version="1.0",
            engine_version="1.0",
        )
