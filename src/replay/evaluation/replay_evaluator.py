from __future__ import annotations

from typing import List, Tuple

from src.replay.models.replay_models import ReplayReport


class ReplayEvaluator:
    """
    Evaluates replay runs for deterministic reproducibility.
    Verifies bitwise and semantic parity between independent replay executions.
    """

    @staticmethod
    def verify_reproducibility(runs: List[ReplayReport]) -> Tuple[bool, List[str]]:
        """Compares multiple replay runs and returns (is_reproducible, differences)."""
        if len(runs) < 2:
            return True, []

        diffs = []
        baseline = runs[0]

        for i, run in enumerate(runs[1:], start=2):
            if run.reproducibility_hash != baseline.reproducibility_hash:
                diffs.append(f"Run {i} hash mismatch: {run.reproducibility_hash} != {baseline.reproducibility_hash}")
            if run.final_state_revision != baseline.final_state_revision:
                diffs.append(f"Run {i} revision mismatch: {run.final_state_revision} != {baseline.final_state_revision}")
            if run.final_nifty_price != baseline.final_nifty_price:
                diffs.append(f"Run {i} NIFTY price mismatch: {run.final_nifty_price} != {baseline.final_nifty_price}")
            if run.final_decision_state != baseline.final_decision_state:
                diffs.append(f"Run {i} decision state mismatch: {run.final_decision_state} != {baseline.final_decision_state}")

        is_reproducible = (len(diffs) == 0)
        return is_reproducible, diffs
