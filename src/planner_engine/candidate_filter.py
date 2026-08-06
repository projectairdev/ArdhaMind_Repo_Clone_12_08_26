from __future__ import annotations

from typing import List, Tuple
from src.models import (
    TradeCandidate,
    CandidateRejection,
    OpportunityContext,
    OptionContext,
)
from src.planner_engine.rejection_engine import RejectionEngine


class CandidateFilter:
    """
    Filters out candidates based on strict market, liquidity, option,
    and strategic suitability rules.
    """

    @staticmethod
    def filter_candidates(
        candidates: List[TradeCandidate],
        opportunity_context: OpportunityContext,
        option_context: OptionContext | None = None,
    ) -> Tuple[List[TradeCandidate], List[CandidateRejection]]:
        accepted: List[TradeCandidate] = []
        rejected: List[CandidateRejection] = []

        directional_strategies = {"MOMENTUM", "TREND_FOLLOWING", "BREAKOUT", "SCALPING"}

        for cand in candidates:
            strat = cand.strategy_name
            symbol = cand.tradingsymbol
            inst = cand.instrument_type

            # Rule 1: Weak overall opportunity
            if not opportunity_context.has_opportunity:
                rejected.append(
                    RejectionEngine.reject(
                        strategy_name=strat,
                        tradingsymbol=symbol,
                        reason_type="WEAK_OPPORTUNITY",
                        message=f"No active market opportunity is currently identified (opportunity_strength: {opportunity_context.strength.overall_strength:.1f}%)."
                    )
                )
                continue

            # Rule 2: Low strategy suitability
            if cand.suitability_score < 50.0:
                rejected.append(
                    RejectionEngine.reject(
                        strategy_name=strat,
                        tradingsymbol=symbol,
                        reason_type="LOW_STRATEGY_SUITABILITY",
                        message=f"Strategy suitability score ({cand.suitability_score:.1f}%) is below the minimum required threshold of 50.0%."
                    )
                )
                continue

            # Rule 3: Directional Alignment
            bias = opportunity_context.directional_bias.value if opportunity_context.directional_bias else "NEUTRAL"
            if strat in directional_strategies:
                if bias == "BULLISH" and inst != "CE":
                    rejected.append(
                        RejectionEngine.reject(
                            strategy_name=strat,
                            tradingsymbol=symbol,
                            reason_type="DIRECTIONAL_MISALIGNMENT",
                            message=f"Candidate option type {inst} is misaligned with the active BULLISH directional bias."
                        )
                    )
                    continue
                elif bias == "BEARISH" and inst != "PE":
                    rejected.append(
                        RejectionEngine.reject(
                            strategy_name=strat,
                            tradingsymbol=symbol,
                            reason_type="DIRECTIONAL_MISALIGNMENT",
                            message=f"Candidate option type {inst} is misaligned with the active BEARISH directional bias."
                        )
                    )
                    continue
                elif bias not in ("BULLISH", "BEARISH") and strat in ("MOMENTUM", "TREND_FOLLOWING"):
                    rejected.append(
                        RejectionEngine.reject(
                            strategy_name=strat,
                            tradingsymbol=symbol,
                            reason_type="NO_DIRECTIONAL_BIAS",
                            message=f"Strategy {strat} requires a clear directional bias, but current market bias is {bias}."
                        )
                    )
                    continue

            # Rule 4: Low Liquidity
            if cand.tradability_score < 50.0:
                rejected.append(
                    RejectionEngine.reject(
                        strategy_name=strat,
                        tradingsymbol=symbol,
                        reason_type="LOW_LIQUIDITY",
                        message=f"Contract tradability score of {cand.tradability_score:.1f} is below the liquid trading floor of 50.0."
                    )
                )
                continue

            # Rule 5: Wide Spread
            if cand.spread_pct > 0.35:
                rejected.append(
                    RejectionEngine.reject(
                        strategy_name=strat,
                        tradingsymbol=symbol,
                        reason_type="WIDE_SPREAD",
                        message=f"Average contract bid-ask spread is too wide ({cand.spread_pct:.2f}% > 0.35%), creating extreme frictional costs."
                    )
                )
                continue

            # Rule 6: Poor Open Interest
            if cand.oi < 1000:
                rejected.append(
                    RejectionEngine.reject(
                        strategy_name=strat,
                        tradingsymbol=symbol,
                        reason_type="POOR_OI",
                        message=f"Contract open interest is extremely thin ({cand.oi} contracts < 1000 threshold), increasing liquidity risk."
                    )
                )
                continue

            # Rule 7: High IV Risk
            if cand.iv > 40.0:
                rejected.append(
                    RejectionEngine.reject(
                        strategy_name=strat,
                        tradingsymbol=symbol,
                        reason_type="HIGH_IV_RISK",
                        message=f"Contract implied volatility is dangerously elevated ({cand.iv:.1f}% > 40.0%), presenting major overpricing/crash risk."
                    )
                )
                continue

            # Rule 8: Wrong/Empty Expiry
            if not cand.expiry:
                rejected.append(
                    RejectionEngine.reject(
                        strategy_name=strat,
                        tradingsymbol=symbol,
                        reason_type="WRONG_EXPIRY",
                        message="Option contract has no valid active expiry date mapped."
                    )
                )
                continue

            # Rule 9: Allowed Expiry Window Filter
            if option_context is not None:
                current_weekly = option_context.current_weekly_expiry
                next_weekly = getattr(option_context, "next_weekly_expiry", "") or current_weekly
                current_monthly = option_context.current_monthly_expiry
                next_monthly = getattr(option_context, "next_monthly_expiry", "") or current_monthly
                far_expiry = getattr(option_context, "far_expiry", "") or current_monthly
                
                import os
                trading_style = os.getenv("PREFERRED_TRADING_STYLE", "Intraday")
                
                from src.planner_engine.candidate_generator import get_allowed_expiries_for_strategy
                allowed_expiries, _ = get_allowed_expiries_for_strategy(
                    strategy_name=strat,
                    trading_style=trading_style,
                    current_weekly=current_weekly,
                    next_weekly=next_weekly,
                    current_monthly=current_monthly,
                    next_monthly=next_monthly,
                    far_expiry=far_expiry
                )
                
                if cand.expiry not in allowed_expiries:
                    rejected.append(
                        RejectionEngine.reject(
                            strategy_name=strat,
                            tradingsymbol=symbol,
                            reason_type="EXPIRY_MISALIGNMENT",
                            message=f"Far expiry contract {symbol} (expiry: {cand.expiry}) is outside the allowed window for {strat} Strategy under {trading_style} style (Allowed: {', '.join(allowed_expiries)})."
                        )
                    )
                    continue

            # If all filters pass, accept!
            accepted.append(cand)

        return accepted, rejected
