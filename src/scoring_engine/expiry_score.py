from __future__ import annotations

from src.models import TradeContext, ExpiryScore
from src.configuration_engine.runtime import Config


def evaluate_expiry_score(context: TradeContext) -> ExpiryScore:
    """
    Evaluates Expiry Score based on days remaining, weekly/monthly type, and classification.
    """
    expiry = context.expiry
    scoring_config = Config.SCORING
    
    weights = scoring_config.get("expiry_weights", {})
    params = scoring_config.get("expiry_params", {})
    
    # 1. Days Remaining Score
    dr = expiry.days_remaining
    opt_min = params.get("optimal_days_min", 2)
    opt_max = params.get("optimal_days_max", 5)
    
    if opt_min <= dr <= opt_max:
        days_remaining_score = 100.0
    elif dr == 1:
        days_remaining_score = float(params.get("score_expiry_eve", 65.0))
    elif dr == 0:
        days_remaining_score = float(params.get("score_expiry_day", 35.0))
    else:  # Far expiry
        # Decay score slowly as we go further out from optimal zone
        days_remaining_score = float(max(50.0, 100.0 - (dr - opt_max) * 2.0))
        
    # 2. Expiry Type Score
    et = expiry.expiry_type
    if et == "WEEKLY":
        expiry_type_score = float(params.get("score_weekly", 100.0))
    elif et == "MONTHLY":
        expiry_type_score = float(params.get("score_monthly", 90.0))
    else:
        expiry_type_score = 80.0
        
    # 3. Classification Score
    cls = expiry.classification
    if cls == "EXPIRY_DAY":
        classification_score = float(params.get("score_expiry_day", 35.0))
    elif cls == "EXPIRY_EVE":
        classification_score = float(params.get("score_expiry_eve", 65.0))
    elif cls == "FAR_EXPIRY":
        classification_score = float(params.get("score_far_expiry", 85.0))
    elif cls == "WEEKLY_EXPIRY":
        classification_score = 100.0
    elif cls == "MONTHLY_EXPIRY":
        classification_score = 95.0
    else:
        classification_score = 80.0
        
    # Calculate overall weighted score
    w_days = weights.get("days_remaining", 0.40)
    w_type = weights.get("expiry_type", 0.20)
    w_cls = weights.get("classification", 0.40)
    
    total_weight = w_days + w_type + w_cls
    weighted_sum = (
        days_remaining_score * w_days +
        expiry_type_score * w_type +
        classification_score * w_cls
    )
    
    overall_expiry_score = float(round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0)
    
    return ExpiryScore(
        days_remaining_score=days_remaining_score,
        expiry_type_score=expiry_type_score,
        classification_score=classification_score,
        overall_expiry_score=overall_expiry_score,
    )
