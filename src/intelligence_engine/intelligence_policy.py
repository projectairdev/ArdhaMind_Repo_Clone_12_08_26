# src/intelligence_engine/intelligence_policy.py
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class IntelligenceQualificationPolicy:
    """
    Centralized, versioned Intelligence Qualification & Scoring Policy for AIR ArdhaMind.
    Ensures explicit provenance and zero ambiguity for scoring weights and thresholds.
    """
    policy_version: str = "I1-V1-STAGING"
    effective_from: str = "2026-08-20T00:00:00+05:30"
    description: str = "Sprint I1-H Hardened Intelligence Qualification Policy"

    # Quality Score Component Weights
    quality_weights: Dict[str, float] = field(default_factory=lambda: {
        "setup_quality": 0.25,
        "structure_quality": 0.20,
        "trend_alignment": 0.15,
        "options_confirmation": 0.15,
        "breadth_confirmation": 0.15,
        "reward_risk_quality": 0.10,
    })

    # Confidence Score Component Weights
    confidence_weights: Dict[str, float] = field(default_factory=lambda: {
        "setup_quality": 0.35,
        "data_quality": 0.25,
        "options_confirmation": 0.20,
        "volatility_suitability": 0.20,
    })

    # Actionability Thresholds
    trade_ready_min_quality: float = 70.0
    trade_ready_min_confidence: float = 65.0
    qualified_min_quality: float = 60.0
    qualified_min_confidence: float = 55.0
    min_reward_risk_ratio: float = 1.2

    # Hard Blocker Definitions
    hard_blockers: List[str] = field(default_factory=lambda: [
        "MARKET_CLOSED",
        "SPOT_STALE",
        "OPTION_QUOTE_STALE",
        "NO_LIQUID_CONTRACT",
        "LOT_SIZE_UNVERIFIED",
        "SPREAD_TOO_WIDE",
        "MISSING_ENTRY",
        "MISSING_STOP",
        "MISSING_TARGET",
        "INVALID_RR",
        "PROPOSAL_EXPIRED",
        "BROKER_STATE_UNVERIFIED",
    ])

    def validate_weights(self) -> bool:
        q_sum = sum(self.quality_weights.values())
        c_sum = sum(self.confidence_weights.values())
        return abs(q_sum - 1.0) < 1e-4 and abs(c_sum - 1.0) < 1e-4

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["weights_valid"] = self.validate_weights()
        return d


DEFAULT_INTELLIGENCE_POLICY = IntelligenceQualificationPolicy()
