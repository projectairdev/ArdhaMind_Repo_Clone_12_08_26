from __future__ import annotations

import numpy as np
from src.configuration_engine.runtime import Config


def compute_option_quality_score(
    strike: float,
    atm_strike: float,
    cost: float,
    option_ltp: float,
    option_oi: int,
    option_volume: int,
    spread_pct: float,
) -> float:
    """
    Computes Option Quality Score using configuration-driven weights.
    """
    distance = abs(strike - atm_strike)
    oi_score = float(np.log1p(max(0, option_oi)))
    volume_score = float(np.log1p(max(0, option_volume)))
    spread_score = float((100 - np.clip(spread_pct, 0, 100)) / 10.0)

    score = (
        (1.0 / (distance + 1.0)) * Config.OQS_DISTANCE_MULT
        - cost / Config.OQS_COST_DIV
        + option_ltp * Config.OQS_LTP_MULT
        + oi_score * Config.OQS_OI_WEIGHT
        + volume_score * Config.OQS_VOLUME_WEIGHT
        + spread_score * Config.OQS_SPREAD_WEIGHT
    )
    return float(score)
