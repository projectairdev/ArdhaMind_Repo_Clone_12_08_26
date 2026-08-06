from __future__ import annotations

from src.models import CandidateRejection


class RejectionEngine:
    """
    Stateless engine to standardize the logging and creation of CandidateRejections.
    """

    @staticmethod
    def reject(
        strategy_name: str,
        tradingsymbol: str,
        reason_type: str,
        message: str,
    ) -> CandidateRejection:
        return CandidateRejection(
            strategy_name=strategy_name,
            tradingsymbol=tradingsymbol,
            reason_type=reason_type,
            message=message,
        )
