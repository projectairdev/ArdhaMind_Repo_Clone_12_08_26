from __future__ import annotations

import hashlib
from typing import Dict, List, Optional
from src.opportunity_engine.domain import CanonicalOpportunity


class DeduplicationEngine:
    """
    Computes a stable fingerprint key for candidate opportunities and matches them
    against existing active opportunities to update state rather than duplicate.
    """

    @staticmethod
    def generate_fingerprint(
        setup_type: str,
        direction: str,
        underlying: str,
        entry_reference: float,
        source_detector: str,
        zone_step: float = 25.0,  # 25-pt price bin for NIFTY levels
    ) -> str:
        # Group entry reference into price zone buckets
        binned_level = round(entry_reference / zone_step) * zone_step
        raw_key = f"{setup_type}:{direction}:{underlying}:{binned_level:.0f}:{source_detector}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def match_existing_opportunity(
        cls,
        candidate_fingerprint: str,
        existing_opportunities: List[CanonicalOpportunity],
    ) -> Optional[CanonicalOpportunity]:
        for opp in existing_opportunities:
            opp_fp = cls.generate_fingerprint(
                opp.setup_type,
                opp.direction,
                opp.underlying,
                opp.entry_reference,
                opp.source_detector,
            )
            if opp_fp == candidate_fingerprint:
                return opp
        return None
