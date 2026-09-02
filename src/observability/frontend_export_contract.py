from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class CanonicalFrontendEnvelope:
    """
    Unified provider-independent frontend delivery envelope.
    Guarantees state revision monotonic convergence across browser reconnects and server restarts.
    """
    runtime_id: str
    state_revision: int
    published_at: datetime
    session: Dict[str, Any]
    market: Dict[str, Any]
    feed_health: Dict[str, Any]
    analytics: Dict[str, Any]
    prediction: Dict[str, Any]
    decision: Dict[str, Any]
    active_product: Dict[str, Any]
    data_quality: str


class FrontendConvergenceHandler:
    """
    Client-side or bridge convergence evaluator.
    Prevents sequence locks on process restart via (runtime_id, revision) tuple tracking.
    """

    def __init__(self) -> None:
        self.last_runtime_id: Optional[str] = None
        self.last_revision: int = -1

    def evaluate_incoming_envelope(self, envelope: CanonicalFrontendEnvelope) -> Tuple[bool, str]:
        """
        Returns (should_accept, reason).
        Accepts state if runtime_id changed (server restart) or revision is strictly greater.
        """
        # Server restart detection
        if self.last_runtime_id is None or envelope.runtime_id != self.last_runtime_id:
            self.last_runtime_id = envelope.runtime_id
            self.last_revision = envelope.state_revision
            return True, "ACCEPTED_NEW_RUNTIME_INSTANCE"

        # Same runtime instance: enforce monotonic progression
        if envelope.state_revision > self.last_revision:
            self.last_revision = envelope.state_revision
            return True, "ACCEPTED_NEWER_REVISION"
        elif envelope.state_revision == self.last_revision:
            return False, "IGNORED_DUPLICATE_REVISION"
        else:
            return False, f"REJECTED_STALE_REVISION ({envelope.state_revision} < {self.last_revision})"
