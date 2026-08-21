from __future__ import annotations

from src.opportunity_engine.detectors.base import OpportunityDetector
from src.opportunity_engine.detectors.breakout import BreakoutDetector
from src.opportunity_engine.detectors.breakdown import BreakdownDetector
from src.opportunity_engine.detectors.pullback import PullbackDetector
from src.opportunity_engine.detectors.reversal import ReversalDetector
from src.opportunity_engine.detectors.momentum import MomentumContinuationDetector

ALL_DETECTORS: list[type[OpportunityDetector]] = [
    BreakoutDetector,
    BreakdownDetector,
    PullbackDetector,
    ReversalDetector,
    MomentumContinuationDetector,
]

__all__ = [
    "OpportunityDetector",
    "BreakoutDetector",
    "BreakdownDetector",
    "PullbackDetector",
    "ReversalDetector",
    "MomentumContinuationDetector",
    "ALL_DETECTORS",
]
