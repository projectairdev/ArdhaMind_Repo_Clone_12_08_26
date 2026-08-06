from __future__ import annotations

from typing import List, Dict
from src.models import (
    TradeCandidate,
    OptionContext,
    CandidateReason,
    CandidateWarning,
)


class CandidateRanker:
    """
    Ranks accepted trade candidates using configuration-driven weights across
    multiple analytical dimensions (suitability, liquidity, OI, spread, ATM proximity, IV).
    """

    DEFAULT_WEIGHTS: Dict[str, float] = {
        "strategy_suitability": 0.40,
        "liquidity": 0.20,
        "oi": 0.10,
        "distance_from_atm": 0.10,
        "spread": 0.10,
        "iv": 0.10,
    }

    @classmethod
    def rank_candidates(
        cls,
        candidates: List[TradeCandidate],
        option_context: OptionContext,
        weights: Dict[str, float] | None = None,
    ) -> List[TradeCandidate]:
        if weights is None:
            weights = cls.DEFAULT_WEIGHTS

        # Validate weights sum close to 1.0; if not, normalize them
        total_w = sum(weights.values())
        if not (0.99 <= total_w <= 1.01) and total_w > 0:
            weights = {k: v / total_w for k, v in weights.items()}

        ranked: List[TradeCandidate] = []
        step = option_context.strike_step if option_context.strike_step > 0 else 50.0

        for cand in candidates:
            # 1. Calculate individual sub-scores scaled to 0-100
            strategy_suit_score = cand.suitability_score
            liquidity_score = cand.tradability_score
            
            # OI relative to a benchmark of 50,000 contracts
            oi_score = min(100.0, (cand.oi / 50000.0) * 100.0)
            
            # ATM distance score (nearer ATM is higher score)
            dist_score = max(0.0, 100.0 - (cand.distance_from_atm / step) * 25.0)
            
            # Spread score (scaled relative to our maximum allowed filter of 0.35%)
            spread_score = max(0.0, 100.0 - (cand.spread_pct / 0.35) * 100.0)
            
            # IV score (scaled relative to our maximum allowed filter of 40.0%)
            iv_score = max(0.0, 100.0 - (cand.iv / 40.0) * 100.0)

            # 2. Compute composite weighted ranking score
            ranking_score = (
                strategy_suit_score * weights.get("strategy_suitability", 0.40) +
                liquidity_score * weights.get("liquidity", 0.20) +
                oi_score * weights.get("oi", 0.10) +
                dist_score * weights.get("distance_from_atm", 0.10) +
                spread_score * weights.get("spread", 0.10) +
                iv_score * weights.get("iv", 0.10)
            )
            ranking_score = float(round(ranking_score, 2))

            # 3. Dynamic Reason and Warning Generation
            reasons: List[CandidateReason] = []
            warnings: List[CandidateWarning] = []

            if ranking_score >= 80.0:
                reasons.append(
                    CandidateReason(
                        reason_type="TOP_TIER_CONFLUENCE",
                        message=f"Outstanding alignment of high strategy suitability ({strategy_suit_score:.1f}%) and premium option metrics."
                    )
                )
            elif ranking_score >= 60.0:
                reasons.append(
                    CandidateReason(
                        reason_type="STRONG_SETUP",
                        message=f"Robust confluence scoring ({ranking_score:.1f}/100) supports execution."
                    )
                )

            if cand.oi >= 30000:
                reasons.append(
                    CandidateReason(
                        reason_type="DEEP_OI_SUPPORT",
                        message=f"Strong open interest of {cand.oi} contracts provides thick order book resilience."
                    )
                )

            if cand.spread_pct <= 0.12:
                reasons.append(
                    CandidateReason(
                        reason_type="ULTRA_TIGHT_SPREAD",
                        message=f"Highly competitive spread ({cand.spread_pct:.2f}%) reduces entering friction."
                    )
                )

            if cand.iv > 28.0:
                warnings.append(
                    CandidateWarning(
                        warning_type="ELEVATED_IV_PREMIUM",
                        message=f"Implied volatility of {cand.iv:.1f}% is elevated; watch for premium compression risk.",
                        severity="MEDIUM"
                    )
                )

            if cand.distance_from_atm >= (step * 2):
                warnings.append(
                    CandidateWarning(
                        warning_type="FAR_OTM_STRIKE",
                        message="Strike is situated 2+ steps from ATM. Higher decay exposure and lower probability of expiring ITM.",
                        severity="LOW"
                    )
                )

            # Re-instantiate with final ranking score, reasons, and warnings
            new_cand = TradeCandidate(
                candidate_id=cand.candidate_id,
                strategy_name=cand.strategy_name,
                tradingsymbol=cand.tradingsymbol,
                strike=cand.strike,
                instrument_type=cand.instrument_type,
                expiry=cand.expiry,
                distance_from_atm=cand.distance_from_atm,
                atm_distance_class=cand.atm_distance_class,
                oi=cand.oi,
                volume=cand.volume,
                spread_pct=cand.spread_pct,
                iv=cand.iv,
                tradability_score=cand.tradability_score,
                suitability_score=cand.suitability_score,
                ranking_score=ranking_score,
                rank=999,  # Assigned in next step
                reasons=reasons,
                warnings=warnings,
            )
            ranked.append(new_cand)

        # Sort descending by composite ranking score
        ranked = sorted(ranked, key=lambda x: x.ranking_score, reverse=True)

        # Assign ranks
        for idx, item in enumerate(ranked):
            # Replacing rank using a new dataclass instance is clean
            ranked[idx] = TradeCandidate(
                candidate_id=item.candidate_id,
                strategy_name=item.strategy_name,
                tradingsymbol=item.tradingsymbol,
                strike=item.strike,
                instrument_type=item.instrument_type,
                expiry=item.expiry,
                distance_from_atm=item.distance_from_atm,
                atm_distance_class=item.atm_distance_class,
                oi=item.oi,
                volume=item.volume,
                spread_pct=item.spread_pct,
                iv=item.iv,
                tradability_score=item.tradability_score,
                suitability_score=item.suitability_score,
                ranking_score=item.ranking_score,
                rank=idx + 1,
                reasons=item.reasons,
                warnings=item.warnings,
            )

        return ranked
