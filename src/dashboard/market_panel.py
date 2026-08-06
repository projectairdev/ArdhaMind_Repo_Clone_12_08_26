from __future__ import annotations

from typing import Any, Dict, Optional
from src.models import MarketScore, OpportunityContext

class MarketPanel:
    """
    Stateless Market Panel.
    Presents Market Score, Opportunity Classification, Strength, and Global/Breadth Contexts.
    """

    def __init__(
        self,
        market_score: Optional[MarketScore] = None,
        opportunity: Optional[OpportunityContext] = None,
    ) -> None:
        self.market_score = market_score
        self.opportunity = opportunity

    def to_dict(self) -> Dict[str, Any]:
        """
        Extracts structured presentation data for market overview, scores, and opportunity.
        """
        score_data = {}
        if self.market_score:
            ms = self.market_score
            score_data = {
                "overall_score": ms.overall_score,
                "letter_grade": ms.letter_grade,
                "classification": ms.classification,
                "timestamp": ms.timestamp,
                "sub_scores": {
                    "trend_score": ms.trend.overall_trend_score if hasattr(ms.trend, "overall_trend_score") else None,
                    "option_score": ms.options.overall_option_score if hasattr(ms.options, "overall_option_score") else None,
                    "volatility_score": ms.volatility.overall_volatility_score if hasattr(ms.volatility, "overall_volatility_score") else None,
                    "liquidity_score": ms.liquidity.overall_liquidity_score if hasattr(ms.liquidity, "overall_liquidity_score") else None,
                    "session_score": ms.session.overall_session_score if hasattr(ms.session, "overall_session_score") else None,
                    "expiry_score": ms.expiry.overall_expiry_score if hasattr(ms.expiry, "overall_expiry_score") else None,
                    "confluence_score": ms.confluence.overall_confluence_score if hasattr(ms.confluence, "overall_confluence_score") else None,
                }
            }

        opp_data = {}
        if self.opportunity:
            op = self.opportunity
            opp_data = {
                "classification": op.classification.value,
                "classification_description": op.classification.description,
                "directional_bias": op.directional_bias.value,
                "directional_bias_description": op.directional_bias.description,
                "has_opportunity": op.has_opportunity,
                "timestamp": op.timestamp,
                "strength": {
                    "overall_strength": op.strength.overall_strength,
                    "imbalance_magnitude": op.strength.imbalance_magnitude,
                    "trend_force": op.strength.trend_force,
                    "option_force": op.strength.option_force,
                    "liquidity_force": op.strength.liquidity_force,
                },
                "profile": {
                    "opportunity_type": op.profile.opportunity_type,
                    "momentum_suitability": op.profile.momentum_suitability,
                    "breakout_suitability": op.profile.breakout_suitability,
                    "reversal_suitability": op.profile.reversal_suitability,
                    "range_suitability": op.profile.range_suitability,
                },
                "warnings": [
                    {"type": w.warning_type, "message": w.message, "severity": w.severity}
                    for w in op.warnings
                ],
                "invalidation_factors": [
                    {"type": f.factor_type, "is_invalidated": f.is_invalidated, "reason": f.reason}
                    for f in op.invalidation_factors
                ]
            }

        return {
            "market_score": score_data or None,
            "opportunity": opp_data or None,
        }

    def render_cli(self) -> str:
        """
        Renders an ASCII text-based representation of the Market & Opportunity panel.
        """
        data = self.to_dict()
        lines = []
        lines.append("+- MARKET & OPPORTUNITY CONTEXT -----------------------------------------------+")

        # Market Score Section
        if data["market_score"]:
            ms = data["market_score"]
            sub = ms["sub_scores"]
            lines.append(f"| OVERALL SCORE: {ms['overall_score']:.2f} ({ms['letter_grade']}) - {ms['classification']:<40} |")
            lines.append("| " + "-"*76 + " |")
            lines.append(f"| Sub-Scores: Trend: {sub['trend_score'] or 0.0:>5.1f} | Options: {sub['option_score'] or 0.0:>5.1f} | Volatility: {sub['volatility_score'] or 0.0:>5.1f} |")
            lines.append(f"|             Liquidity: {sub['liquidity_score'] or 0.0:>5.1f} | Session: {sub['session_score'] or 0.0:>5.1f} | Expiry: {sub['expiry_score'] or 0.0:>5.1f} |")
            lines.append(f"|             Confluence Score: {sub['confluence_score'] or 0.0:>5.1f}                                      |")
        else:
            lines.append("| Market Score details: NOT AVAILABLE                                          |")

        lines.append("| " + "="*76 + " |")

        # Opportunity Section
        if data["opportunity"]:
            op = data["opportunity"]
            lines.append(f"| Opportunity Assessment: {op['classification']:<12} | Bias: {op['directional_bias']:<12} | Has Opp: {str(op['has_opportunity']):<5} |")
            lines.append(f"| Desc: {op['classification_description'][:70]:<70} |")
            st = op["strength"]
            lines.append("| " + "-"*76 + " |")
            lines.append(f"| Imbalance Strength: {st['overall_strength']:>5.1f}% (Trend: {st['trend_force']:.1f} | Option: {st['option_force']:.1f} | Liquidity: {st['liquidity_force']:.1f}) |")
            
            # Profile Suitability
            prof = op["profile"]
            lines.append(f"| Profile Type: {prof['opportunity_type']:<15} | Suitability: Mom={prof['momentum_suitability']} Break={prof['breakout_suitability']} Rev={prof['reversal_suitability']} |")
            
            # Warnings
            if op["warnings"]:
                lines.append("| " + "-"*76 + " |")
                lines.append("| Warnings:                                                                    |")
                for w in op["warnings"][:3]:
                    lines.append(f"|   * [{w['severity']}] {w['message'][:65]:<66} |")
            
            # Invalidation Factors
            active_inv = [f for f in op["invalidation_factors"] if f["is_invalidated"]]
            if active_inv:
                lines.append("| " + "-"*76 + " |")
                lines.append("| Active Invalidation Factors:                                                 |")
                for f in active_inv[:2]:
                    lines.append(f"|   * {f['type']}: {f['reason'][:55]:<56} |")
        else:
            lines.append("| Opportunity details: NOT AVAILABLE                                           |")

        lines.append("+------------------------------------------------------------------------------+")
        return "\n".join(lines)
