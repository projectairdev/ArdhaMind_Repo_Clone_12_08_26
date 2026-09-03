from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple

from src.analytics.options.models import (
    BuildupType,
    GreeksContext,
    GreeksProvenance,
    OptionLiquidityLevel,
    OptionsConfirmationBias,
    OptionsConfirmationContext,
    StrikeIntelligence,
    StrikeStrengthClass,
)
from src.market_data.models.canonical_option_chain import (
    CanonicalOptionChainSnapshot,
    CanonicalOptionLeg,
    CanonicalOptionStrike,
)
from src.market_data.models.quality_enums import DataQualityStatus, OptionType


class OptionsIntelligenceEngine:
    """
    Deterministic provider-independent options intelligence engine.
    Calculates Max Pain, Call/Put Walls, position buildup, strike strength, and directional confirmation.
    """

    @staticmethod
    def analyze(
        snapshot: Optional[CanonicalOptionChainSnapshot],
        prior_snapshot: Optional[CanonicalOptionChainSnapshot] = None,
        strike_window_count: int = 10,
    ) -> OptionsConfirmationContext:
        """Runs full options intelligence analytics on a CanonicalOptionChainSnapshot."""
        if snapshot is None or not snapshot.strikes:
            return OptionsIntelligenceEngine._empty_context()

        und_price = snapshot.underlying_price
        strikes = snapshot.strikes

        # 1. ATM Strike & Strike Universe Filtering
        atm_strike = min(strikes, key=lambda s: abs(s.strike - und_price)).strike
        atm_idx = next(i for i, s in enumerate(strikes) if s.strike == atm_strike)

        start_idx = max(0, atm_idx - strike_window_count)
        end_idx = min(len(strikes), atm_idx + strike_window_count + 1)
        active_strikes = strikes[start_idx:end_idx]

        # Prior lookup map for OI change calculation
        prior_by_strike = {}
        if prior_snapshot:
            for s in prior_snapshot.strikes:
                prior_by_strike[s.strike] = s

        # 2. Max Pain Calculation
        max_pain = OptionsIntelligenceEngine.calculate_max_pain(strikes)

        # 3. Call Wall and Put Wall
        call_wall = max(strikes, key=lambda s: s.call.oi if s.call and s.call.oi else -1).strike
        put_wall = max(strikes, key=lambda s: s.put.oi if s.put and s.put.oi else -1).strike

        # 4. Strike-by-Strike Intelligence
        strike_intel_list: List[StrikeIntelligence] = []
        total_call_oi = 0
        total_put_oi = 0

        for s in active_strikes:
            prior_s = prior_by_strike.get(s.strike)
            intel = OptionsIntelligenceEngine.analyze_strike(s, prior_s, und_price, call_wall, put_wall)
            strike_intel_list.append(intel)

        for s in strikes:
            if s.call and s.call.oi:
                total_call_oi += s.call.oi
            if s.put and s.put.oi:
                total_put_oi += s.put.oi

        # 5. PCR
        pcr = round(total_put_oi / total_call_oi, 4) if total_call_oi > 0 else 1.0

        # 6. Directional Options Confirmation
        confirmation_score, bias, supporting, contradicting = OptionsIntelligenceEngine.evaluate_confirmation(
            und_price=und_price,
            atm_strike=atm_strike,
            pcr=pcr,
            max_pain=max_pain,
            call_wall=call_wall,
            put_wall=put_wall,
            strike_universe=strike_intel_list,
        )

        return OptionsConfirmationContext(
            bias=bias,
            confirmation_score=confirmation_score,
            atm_strike=atm_strike,
            pcr=pcr,
            max_pain=max_pain,
            call_wall=call_wall,
            put_wall=put_wall,
            strike_universe=strike_intel_list,
            supporting_factors=supporting,
            contradicting_factors=contradicting,
            quality=DataQualityStatus.VALID,
        )

    @staticmethod
    def classify_buildup(
        current_price: Optional[float],
        prior_price: Optional[float],
        current_oi: Optional[int],
        prior_oi: Optional[int],
        is_call: bool,
    ) -> BuildupType:
        """Deterministically classifies options position buildup."""
        if current_price is None or prior_price is None or current_oi is None or prior_oi is None:
            return BuildupType.INSUFFICIENT_DATA

        price_chg = current_price - prior_price
        oi_chg = current_oi - prior_oi

        if abs(oi_chg) < 100:
            return BuildupType.INSUFFICIENT_DATA

        if is_call:
            if price_chg >= 0 and oi_chg > 0:
                return BuildupType.LONG_BUILDUP
            elif price_chg < 0 and oi_chg > 0:
                return BuildupType.FRESH_CALL_WRITING
            elif price_chg >= 0 and oi_chg < 0:
                return BuildupType.SHORT_COVERING
            else:
                return BuildupType.CALL_UNWINDING
        else:
            if price_chg >= 0 and oi_chg > 0:
                return BuildupType.LONG_BUILDUP
            elif price_chg < 0 and oi_chg > 0:
                return BuildupType.FRESH_PUT_WRITING
            elif price_chg >= 0 and oi_chg < 0:
                return BuildupType.SHORT_COVERING
            else:
                return BuildupType.PUT_UNWINDING

    @staticmethod
    def calculate_max_pain(strikes: Sequence[CanonicalOptionStrike]) -> float:
        """Calculates the strike price where option buyers experience maximum cumulative loss."""
        if not strikes:
            return 0.0

        min_loss = float("inf")
        max_pain_strike = strikes[len(strikes) // 2].strike

        for test_s in strikes:
            s_val = test_s.strike
            total_loss = 0.0

            for s in strikes:
                # Call loss at s_val: max(0, s_val - s.strike) * call_oi
                if s.call and s.call.oi and s.call.oi > 0:
                    call_intrinsic = max(0.0, s_val - s.strike)
                    total_loss += call_intrinsic * s.call.oi

                # Put loss at s_val: max(0, s.strike - s_val) * put_oi
                if s.put and s.put.oi and s.put.oi > 0:
                    put_intrinsic = max(0.0, s.strike - s_val)
                    total_loss += put_intrinsic * s.put.oi

            if total_loss < min_loss:
                min_loss = total_loss
                max_pain_strike = s_val

        return max_pain_strike

    @staticmethod
    def evaluate_liquidity(leg: Optional[CanonicalOptionLeg]) -> OptionLiquidityLevel:
        """Scores leg liquidity based on bid/ask spread, volume, and open interest."""
        if leg is None or leg.last_price is None:
            return OptionLiquidityLevel.UNAVAILABLE

        spread = (leg.ask - leg.bid) if (leg.ask and leg.bid) else None
        vol = leg.volume or 0
        oi = leg.oi or 0

        if spread is not None and spread <= 1.5 and vol >= 1000 and oi >= 5000:
            return OptionLiquidityLevel.HIGH
        elif vol >= 100 and oi >= 1000:
            return OptionLiquidityLevel.MEDIUM
        else:
            return OptionLiquidityLevel.LOW

    @staticmethod
    def analyze_strike(
        current: CanonicalOptionStrike,
        prior: Optional[CanonicalOptionStrike],
        spot_price: float,
        call_wall: float,
        put_wall: float,
    ) -> StrikeIntelligence:
        """Computes intelligence classification for a single strike."""
        c = current.call
        p = current.put
        prior_c = prior.call if prior else None
        prior_p = prior.put if prior else None

        c_buildup = OptionsIntelligenceEngine.classify_buildup(
            c.last_price if c else None,
            prior_c.last_price if prior_c else None,
            c.oi if c else None,
            prior_c.oi if prior_c else None,
            is_call=True,
        )
        p_buildup = OptionsIntelligenceEngine.classify_buildup(
            p.last_price if p else None,
            prior_p.last_price if prior_p else None,
            p.oi if p else None,
            prior_p.oi if prior_p else None,
            is_call=False,
        )

        c_oi = c.oi or 0 if c else 0
        p_oi = p.oi or 0 if p else 0
        c_oi_chg = (c.oi - prior_c.oi) if (c and prior_c and c.oi and prior_c.oi) else None
        p_oi_chg = (p.oi - prior_p.oi) if (p and prior_p and p.oi and prior_p.oi) else None

        c_vol = c.volume or 0 if c else 0
        p_vol = p.volume or 0 if p else 0

        c_liq = OptionsIntelligenceEngine.evaluate_liquidity(c)
        p_liq = OptionsIntelligenceEngine.evaluate_liquidity(p)
        overall_liq = OptionLiquidityLevel.HIGH if (c_liq == OptionLiquidityLevel.HIGH or p_liq == OptionLiquidityLevel.HIGH) else OptionLiquidityLevel.MEDIUM

        # Greeks extraction
        c_greeks = GreeksContext(c.iv, c.delta, c.gamma, c.theta, c.vega) if c and c.iv is not None else None
        p_greeks = GreeksContext(p.iv, p.delta, p.gamma, p.theta, p.vega) if p and p.iv is not None else None

        # Strike bias & score
        score = 0.0
        if current.strike == call_wall:
            bias = StrikeStrengthClass.STRONG_CALL_RESISTANCE
            score = -0.8
        elif current.strike == put_wall:
            bias = StrikeStrengthClass.STRONG_PUT_SUPPORT
            score = 0.8
        elif p_oi > c_oi * 1.5:
            bias = StrikeStrengthClass.BULLISH_STRIKE_CONFIRMATION
            score = 0.5
        elif c_oi > p_oi * 1.5:
            bias = StrikeStrengthClass.BEARISH_STRIKE_CONFIRMATION
            score = -0.5
        else:
            bias = StrikeStrengthClass.MIXED
            score = 0.0

        return StrikeIntelligence(
            strike=current.strike,
            call_buildup=c_buildup,
            put_buildup=p_buildup,
            call_oi=c_oi,
            put_oi=p_oi,
            call_oi_change=c_oi_chg,
            put_oi_change=p_oi_chg,
            call_volume=c_vol,
            put_volume=p_vol,
            call_greeks=c_greeks,
            put_greeks=p_greeks,
            liquidity=overall_liq,
            strike_bias=bias,
            strength_score=score,
        )

    @staticmethod
    def evaluate_confirmation(
        und_price: float,
        atm_strike: float,
        pcr: float,
        max_pain: float,
        call_wall: float,
        put_wall: float,
        strike_universe: Sequence[StrikeIntelligence],
    ) -> Tuple[float, OptionsConfirmationBias, List[str], List[str]]:
        """Synthesizes structural options evidence into directional confirmation."""
        supporting: List[str] = []
        contradicting: List[str] = []
        score = 0.0

        # 1. PCR Evidence
        if pcr >= 1.15:
            score += 0.35
            supporting.append(f"Bullish PCR ({pcr:.2f} >= 1.15)")
        elif pcr <= 0.80:
            score -= 0.35
            supporting.append(f"Bearish PCR ({pcr:.2f} <= 0.80)")
        else:
            contradicting.append(f"Neutral PCR ({pcr:.2f} between 0.80 and 1.15)")

        # 2. Wall Proximity
        dist_to_call_wall = call_wall - und_price
        dist_to_put_wall = und_price - put_wall

        if dist_to_call_wall < 50.0:
            score -= 0.25
            contradicting.append(f"Spot approaching Call Wall resistance ({call_wall:.0f})")
        if dist_to_put_wall < 50.0:
            score += 0.25
            supporting.append(f"Spot holding above Put Wall support ({put_wall:.0f})")

        # 3. Max Pain Alignment
        if und_price > max_pain + 50.0:
            score += 0.20
            supporting.append(f"Spot ({und_price:.1f}) trading comfortably above Max Pain ({max_pain:.0f})")
        elif und_price < max_pain - 50.0:
            score -= 0.20
            supporting.append(f"Spot ({und_price:.1f}) trading below Max Pain ({max_pain:.0f})")

        # 4. ATM Strike Bias
        atm_intel = next((s for s in strike_universe if s.strike == atm_strike), None)
        if atm_intel:
            if atm_intel.put_oi > atm_intel.call_oi:
                score += 0.20
                supporting.append(f"ATM ({atm_strike:.0f}) dominant Put OI ({atm_intel.put_oi:,} vs {atm_intel.call_oi:,})")
            elif atm_intel.call_oi > atm_intel.put_oi:
                score -= 0.20
                supporting.append(f"ATM ({atm_strike:.0f}) dominant Call OI ({atm_intel.call_oi:,} vs {atm_intel.put_oi:,})")

        final_score = round(max(-1.0, min(1.0, score)), 2)

        if final_score >= 0.30:
            bias = OptionsConfirmationBias.BULLISH
        elif final_score <= -0.30:
            bias = OptionsConfirmationBias.BEARISH
        elif len(supporting) > 0 and len(contradicting) > 0:
            bias = OptionsConfirmationBias.CONFLICTED
        else:
            bias = OptionsConfirmationBias.NEUTRAL

        return final_score, bias, supporting, contradicting

    @staticmethod
    def _empty_context() -> OptionsConfirmationContext:
        return OptionsConfirmationContext(
            bias=OptionsConfirmationBias.UNAVAILABLE,
            confirmation_score=0.0,
            atm_strike=0.0,
            pcr=1.0,
            max_pain=0.0,
            call_wall=0.0,
            put_wall=0.0,
            strike_universe=[],
            supporting_factors=[],
            contradicting_factors=[],
            quality=DataQualityStatus.UNAVAILABLE,
        )
