"""
src/storage/reconciliation.py

Configurable Close Reconciliation Engine for AIR Ardha.
Implements CloseReconciliationPolicy evaluation without hardcoded drift invariants.
"""
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from src.storage.schemas import CloseReconciliationPolicy


class CloseReconciler:
    """
    Evaluates observed session OHLC and closing prices against official provider settlement values.
    """

    @classmethod
    def reconcile(
        cls,
        observed_close: Optional[float],
        provider_close: Optional[float],
        policy: Optional[CloseReconciliationPolicy] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Reconciles observed vs provider close using the given policy.
        Returns (reconciliation_status, reconciliation_metadata_dict).
        
        Statuses:
        - MATCHED: Exact match
        - WITHIN_TOLERANCE: Drift is within absolute or relative basis point tolerance
        - CORRECTED_FROM_PROVIDER: Drift exceeds tolerance; provider value adopted if allowed
        - PARTIAL: One of the inputs is missing
        - UNRESOLVED: Critical mismatch without provider correction permission
        """
        active_policy = policy or CloseReconciliationPolicy()
        
        if observed_close is None or provider_close is None:
            return "PARTIAL", {
                "status": "PARTIAL",
                "observed_close": observed_close,
                "provider_close": provider_close,
                "drift_points": None,
                "drift_bps": None,
                "policy_version": active_policy.policy_version,
                "note": "One or both close values were unavailable."
            }
        
        drift_points = round(abs(observed_close - provider_close), 2)
        ref_price = provider_close if provider_close > 0 else observed_close
        drift_bps = round((drift_points / ref_price) * 10000.0, 2) if ref_price > 0 else 0.0
        
        if drift_points == 0.0:
            return "MATCHED", {
                "status": "MATCHED",
                "observed_close": observed_close,
                "provider_close": provider_close,
                "drift_points": 0.0,
                "drift_bps": 0.0,
                "policy_version": active_policy.policy_version
            }
            
        is_within_abs = drift_points <= active_policy.max_absolute_drift_points
        is_within_rel = drift_bps <= active_policy.max_relative_drift_bps
        
        if is_within_abs or is_within_rel:
            return "WITHIN_TOLERANCE", {
                "status": "WITHIN_TOLERANCE",
                "observed_close": observed_close,
                "provider_close": provider_close,
                "drift_points": drift_points,
                "drift_bps": drift_bps,
                "policy_version": active_policy.policy_version,
                "tolerance_applied": "ABSOLUTE" if is_within_abs else "RELATIVE_BPS"
            }
            
        if active_policy.allow_provider_correction:
            return "CORRECTED_FROM_PROVIDER", {
                "status": "CORRECTED_FROM_PROVIDER",
                "observed_close": observed_close,
                "provider_close": provider_close,
                "drift_points": drift_points,
                "drift_bps": drift_bps,
                "policy_version": active_policy.policy_version,
                "adopted_close": provider_close
            }
            
        return "UNRESOLVED", {
            "status": "UNRESOLVED",
            "observed_close": observed_close,
            "provider_close": provider_close,
            "drift_points": drift_points,
            "drift_bps": drift_bps,
            "policy_version": active_policy.policy_version,
            "warning": "Close drift exceeded tolerance and provider correction was disallowed."
        }
