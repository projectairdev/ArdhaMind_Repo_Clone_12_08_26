from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple
from src.opportunity_engine.domain import DetectorInputRequirements, DetectorResult


class OpportunityDetector(ABC):
    detector_id: str
    detector_version: str = "1.0.0"
    input_requirements: DetectorInputRequirements = DetectorInputRequirements()

    def check_input_requirements(self, context: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validates if required inputs, history, and freshness constraints are satisfied.
        Returns (is_satisfied, optional_blocking_reason).
        """
        market = context.get("market_context") or {}
        freshness = str(context.get("freshness_state") or "FRESH").upper()

        if freshness == "STALE":
            return False, f"Detector [{self.detector_id}] blocked: Market data freshness is STALE"

        spot = float(market.get("current_spot") or 0.0)
        if "current_spot" in self.input_requirements.required_inputs and spot <= 0:
            return False, f"Detector [{self.detector_id}] blocked: Missing valid current_spot"

        if "resistance_levels" in self.input_requirements.required_inputs and not market.get("resistance_levels"):
            return False, f"Detector [{self.detector_id}] blocked: Missing validated resistance levels"

        if "support_levels" in self.input_requirements.required_inputs and not market.get("support_levels"):
            return False, f"Detector [{self.detector_id}] blocked: Missing validated support levels"

        return True, None

    @abstractmethod
    def evaluate(self, context: Dict[str, Any]) -> DetectorResult:
        """
        Evaluate context and return a deterministic DetectorResult.
        """
        pass
