# src/live_assistant/evidence_packet.py
"""
Bounded Evidence Packet Schema for Live Assistant.
Strict container holding ONLY the retrieved canonical evidence relevant to query intents.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class BoundedEvidencePacket:
    question: str
    intents: List[str]
    canonical_session: str
    market_timestamp: str
    freshness_status: str  # LIVE | FRESH | LAST_VALID_SESSION | PREVIOUS_SESSION | STALE | UNAVAILABLE
    evidence: Dict[str, Any] = field(default_factory=dict)
    missing_evidence: List[str] = field(default_factory=list)
    prohibited_inference: bool = True
    allowed_conclusions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "intents": self.intents,
            "canonical_session": self.canonical_session,
            "market_timestamp": self.market_timestamp,
            "freshness_status": self.freshness_status,
            "evidence": self.evidence,
            "missing_evidence": self.missing_evidence,
            "prohibited_inference": self.prohibited_inference,
            "allowed_conclusions": self.allowed_conclusions,
        }
