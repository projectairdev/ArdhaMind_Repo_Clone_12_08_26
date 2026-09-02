from __future__ import annotations

from typing import List, Tuple

from src.analytics.options.models import OptionLiquidityLevel
from src.analytics.snapshot.analytics_snapshot import MarketAnalyticsSnapshot
from src.decision.models.decision_models import (
    DecisionRiskLevel,
    RiskAssessment,
    SignalFusionContext,
    StrategySuitability,
    StrikeCandidate,
)
from src.market_data.models.quality_enums import DataQualityStatus, OptionType


class StrategySuitabilityEngine:
    """
    Deterministic options structure classification and strike selection engine.
    Produces human-review strike candidates only (read-only advisory intelligence).
    """

    @staticmethod
    def evaluate_strategy(
        analytics: MarketAnalyticsSnapshot,
        fusion: SignalFusionContext,
        risk: RiskAssessment,
    ) -> Tuple[StrategySuitability, List[StrikeCandidate]]:
        """Evaluates suitable options structures and filters liquid strike candidates."""
        options = analytics.options_intelligence
        if options.quality == DataQualityStatus.UNAVAILABLE or not options.strike_universe:
            return StrategySuitability.UNAVAILABLE, []

        align = fusion.directional_alignment
        vix = analytics.vix_price or 14.0
        candidates: List[StrikeCandidate] = []

        # 1. Structure Classification
        if risk.risk_level == DecisionRiskLevel.BLOCKED or align == "INSUFFICIENT_DATA":
            strategy = StrategySuitability.NO_OPTIONS_STRATEGY
        elif vix >= 18.0:
            strategy = StrategySuitability.DEFINED_RISK_ONLY
        elif align == "BULLISH":
            strategy = StrategySuitability.BULL_CALL_SPREAD if vix >= 16.0 else StrategySuitability.LONG_CALL
        elif align == "BEARISH":
            strategy = StrategySuitability.BEAR_PUT_SPREAD if vix >= 16.0 else StrategySuitability.LONG_PUT
        else:
            strategy = StrategySuitability.NO_OPTIONS_STRATEGY

        # 2. Strike Selection Filter
        spot = analytics.price_structure.last_price
        target_opt_type = OptionType.CE if align == "BULLISH" else (OptionType.PE if align == "BEARISH" else None)

        if target_opt_type is not None:
            for s in options.strike_universe:
                dist = round(abs(s.strike - spot), 1)
                # Keep near-the-money strikes within 150 points
                if dist <= 150.0:
                    reasons: List[str] = []
                    risks: List[str] = []

                    if s.liquidity == OptionLiquidityLevel.HIGH:
                        reasons.append(f"High leg liquidity (OI: {s.call_oi if target_opt_type == OptionType.CE else s.put_oi:,})")
                    else:
                        risks.append("Moderate/low liquidity on strike")

                    if target_opt_type == OptionType.CE and s.strike == options.call_wall:
                        risks.append("Strike coincides with major Call Wall overhead")
                    if target_opt_type == OptionType.PE and s.strike == options.put_wall:
                        risks.append("Strike coincides with major Put Wall support")

                    candidates.append(
                        StrikeCandidate(
                            strike=s.strike,
                            option_type=target_opt_type,
                            strength=s.strike_bias.value,
                            liquidity=s.liquidity.value,
                            oi_context=f"Call OI: {s.call_oi:,} | Put OI: {s.put_oi:,}",
                            iv=s.call_greeks.iv if (target_opt_type == OptionType.CE and s.call_greeks) else (s.put_greeks.iv if (target_opt_type == OptionType.PE and s.put_greeks) else None),
                            spread=1.0 if s.liquidity == OptionLiquidityLevel.HIGH else 2.5,
                            distance_from_spot=dist,
                            supporting_reasons=reasons,
                            risks=risks,
                        )
                    )

        # Sort candidates by distance from spot
        candidates.sort(key=lambda c: c.distance_from_spot)

        return strategy, candidates[:3]
