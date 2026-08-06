from __future__ import annotations

import math
from typing import List
from src.models import (
    OptionContext,
    StrategyEvaluation,
    TradeCandidate,
    CandidateReason,
)


def get_allowed_expiries_for_strategy(
    strategy_name: str,
    trading_style: str,
    current_weekly: str,
    next_weekly: str,
    current_monthly: str,
    next_monthly: str,
    far_expiry: str,
) -> tuple[list[str], str]:
    """
    Returns a tuple of (allowed_expiries_list, expiry_reason) based on strategy rules.
    """
    style = trading_style.lower()
    strat = strategy_name.upper()
    
    holding_period = "Intraday"
    preferred_expiry = "Current Weekly"
    allowed = [current_weekly]
    
    if strat == "SCALPING":
        holding_period = "Intraday"
        preferred_expiry = "Current Weekly Only"
        allowed = [current_weekly]
    elif strat in ("MOMENTUM", "MEAN_REVERSION", "RANGE_TRADING"):
        holding_period = "Intraday"
        if style == "positional":
            preferred_expiry = "Current Monthly"
            allowed = [current_monthly]
        else:
            preferred_expiry = "Current Weekly"
            allowed = [current_weekly, next_weekly]
    elif strat == "BREAKOUT":
        holding_period = "1-3 Days"
        if style == "positional":
            preferred_expiry = "Current Monthly"
            allowed = [current_monthly]
        elif style == "swing":
            preferred_expiry = "Next Weekly"
            allowed = [next_weekly, current_monthly]
        else:
            preferred_expiry = "Current Weekly"
            allowed = [current_weekly, next_weekly]
    elif strat == "TREND_FOLLOWING":
        holding_period = "3-7 Days"
        if style == "positional":
            preferred_expiry = "Next Monthly"
            allowed = [current_monthly, next_monthly]
        elif style == "intraday":
            preferred_expiry = "Current Weekly"
            allowed = [current_weekly, next_weekly]
        else:
            preferred_expiry = "Next Weekly"
            allowed = [next_weekly, current_monthly]
    elif strat == "POSITIONAL":
        holding_period = "2-6 Weeks"
        if style == "intraday":
            preferred_expiry = "Current Weekly"
            allowed = [current_weekly, next_weekly]
        else:
            preferred_expiry = "Monthly"
            allowed = [current_monthly, next_monthly]
    elif strat == "LONG_TERM":
        holding_period = "Several Months"
        preferred_expiry = "Monthly or Far Expiry"
        allowed = [current_monthly, next_monthly, far_expiry]
        
    reason = (
        f"{preferred_expiry} expiry selected because:\n"
        f"• {strategy_name.replace('_', ' ').title()} Strategy\n"
        f"• Expected holding period: {holding_period}\n"
        f"• Preferred Style: {trading_style.title()}\n"
        f"• Validated for liquidity & narrow spread"
    )
    
    return [a for a in allowed if a], reason


class CandidateGenerator:
    """
    Generates potential trade candidates by crossing evaluated strategies
    with candidate option strikes from OptionContext.
    """

    @staticmethod
    def generate_candidates(
        option_context: OptionContext,
        strategy_evaluation: StrategyEvaluation,
    ) -> List[TradeCandidate]:
        candidates: List[TradeCandidate] = []
        
        atm_strike = option_context.atm_strike
        step = option_context.strike_step if option_context.strike_step > 0 else 50.0
        expiry = option_context.current_weekly_expiry or option_context.current_monthly_expiry or ""
        
        # We loop through all evaluations
        for strat_score in strategy_evaluation.evaluations:
            strategy_name = strat_score.strategy_name
            suitability_score = strat_score.suitability_score
            
            # Cross with each candidate strike in option_context
            for strike_dict in option_context.top_candidate_strikes:
                tradingsymbol = strike_dict.get("tradingsymbol", "")
                strike = float(strike_dict.get("strike", 0.0))
                inst_type = strike_dict.get("instrument_type", "CE")
                oi = int(strike_dict.get("oi", 0))
                volume = int(strike_dict.get("volume", 0))
                spread_pct = float(strike_dict.get("spread_pct", 0.0))
                iv = float(strike_dict.get("iv", 0.0))
                tradability_score = float(strike_dict.get("tradability_score", 0.0))
                strike_expiry = strike_dict.get("expiry", "") or expiry
                
                # Calculate absolute distance from ATM
                distance_from_atm = abs(strike - atm_strike)
                
                # Calculate ATM step offset
                diff = strike - atm_strike
                steps = int(round(diff / step))
                
                if steps == 0:
                    atm_distance_class = "ATM"
                elif steps == 1:
                    atm_distance_class = "ATM_PLUS_1"
                elif steps == -1:
                    atm_distance_class = "ATM_MINUS_1"
                elif steps == 2:
                    atm_distance_class = "ATM_PLUS_2"
                elif steps == -2:
                    atm_distance_class = "ATM_MINUS_2"
                else:
                    atm_distance_class = "OTHER"
                    
                candidate_id = f"{strategy_name}_{tradingsymbol}"
                
                # Resolve expiry selection reason
                import os
                trading_style = os.getenv("PREFERRED_TRADING_STYLE", "Intraday")
                
                _, expiry_reason = get_allowed_expiries_for_strategy(
                    strategy_name=strategy_name,
                    trading_style=trading_style,
                    current_weekly=option_context.current_weekly_expiry,
                    next_weekly=getattr(option_context, "next_weekly_expiry", "") or option_context.current_weekly_expiry,
                    current_monthly=option_context.current_monthly_expiry,
                    next_monthly=getattr(option_context, "next_monthly_expiry", "") or option_context.current_monthly_expiry,
                    far_expiry=getattr(option_context, "far_expiry", "") or option_context.current_monthly_expiry,
                )
                
                # Base candidate construction
                candidate = TradeCandidate(
                    candidate_id=candidate_id,
                    strategy_name=strategy_name,
                    tradingsymbol=tradingsymbol,
                    strike=strike,
                    instrument_type=inst_type,
                    expiry=strike_expiry,
                    distance_from_atm=distance_from_atm,
                    atm_distance_class=atm_distance_class,
                    oi=oi,
                    volume=volume,
                    spread_pct=spread_pct,
                    iv=iv,
                    tradability_score=tradability_score,
                    suitability_score=suitability_score,
                    ranking_score=0.0,  # To be calculated by candidate_ranker
                    rank=999,          # To be calculated by candidate_ranker
                    reasons=[],
                    warnings=[],
                    expiry_reason=expiry_reason
                )
                candidates.append(candidate)
                
        return candidates
