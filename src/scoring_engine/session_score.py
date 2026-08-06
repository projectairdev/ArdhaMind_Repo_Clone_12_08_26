from __future__ import annotations

from src.models import TradeContext, SessionScore
from src.configuration_engine.runtime import Config


def evaluate_session_score(context: TradeContext) -> SessionScore:
    """
    Evaluates Session Score based on session type and whether the current time is tradable.
    """
    session = context.session
    scoring_config = Config.SCORING
    
    weights = scoring_config.get("session_weights", {})
    params = scoring_config.get("session_params", {})
    
    # 1. Session Type Score
    st = getattr(session, "session_type", "POST_MARKET")
    if st == "MORNING":
        session_type_score = float(params.get("score_morning", 100.0))
    elif st == "AFTERNOON":
        session_type_score = float(params.get("score_afternoon", 90.0))
    elif st == "MID_SESSION" or st == "LUNCH":
        session_type_score = float(params.get("score_mid_session", 75.0))
    elif st == "MARKET_OPEN":
        session_type_score = float(params.get("score_market_open", 65.0))
    elif st == "CLOSING_SESSION":
        session_type_score = float(params.get("score_closing_session", 55.0))
    elif st == "HALF_DAY":
        session_type_score = float(params.get("score_half_day", 80.0))
    elif st == "WEEKEND":
        session_type_score = float(params.get("score_weekend", 0.0))
    elif st == "HOLIDAY":
        session_type_score = float(params.get("score_holiday", 0.0))
    else:  # POST_MARKET or other
        session_type_score = float(params.get("score_post_market", 0.0))
        
    # 2. Is Tradable Score
    is_tradable_score = 100.0 if session.is_tradable_time else 0.0
    
    # Calculate overall weighted score
    w_type = weights.get("session_type", 0.60)
    w_tradable = weights.get("is_tradable", 0.40)
    
    total_weight = w_type + w_tradable
    weighted_sum = (
        session_type_score * w_type +
        is_tradable_score * w_tradable
    )
    
    overall_session_score = float(round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0)
    
    return SessionScore(
        session_type_score=session_type_score,
        is_tradable_score=is_tradable_score,
        overall_session_score=overall_session_score,
    )
