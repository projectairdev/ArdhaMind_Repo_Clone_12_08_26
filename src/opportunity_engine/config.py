from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class OpportunityConfig:
    config_version: str = "1.0.0"

    # Per-setup minimum Risk:Reward ratio requirements
    min_reward_risk_ratios: Dict[str, float] = field(
        default_factory=lambda: {
            "BREAKOUT": 1.5,
            "BREAKDOWN": 1.5,
            "PULLBACK": 1.3,
            "REVERSAL": 1.8,
            "MOMENTUM_CONTINUATION": 1.4,
        }
    )

    # Status Quality & Confidence Thresholds
    trade_ready_min_quality: float = 70.0
    trade_ready_min_confidence: float = 65.0

    qualified_min_quality: float = 60.0
    qualified_min_confidence: float = 55.0

    watching_min_quality: float = 45.0

    # Freshness Limits
    max_data_freshness_seconds: float = 30.0

    # Memory Retention Limits
    max_history_retention: int = 100

    def get_min_rr(self, setup_type: str) -> float:
        return self.min_reward_risk_ratios.get(setup_type.upper(), 1.5)


DEFAULT_OPPORTUNITY_CONFIG = OpportunityConfig()
