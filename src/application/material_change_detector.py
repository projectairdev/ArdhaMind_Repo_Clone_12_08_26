from __future__ import annotations

import json
import hashlib
from typing import Any
from uuid import uuid4


class MaterialChangeDetector:
    """Detects critical state transitions and computes deterministic payload hashes."""

    @staticmethod
    def compute_payload_hash(payload: dict[str, Any]) -> str:
        """Computes deterministic 12-char hash of dictionary excluding dynamic timestamp fields."""
        if not payload or not isinstance(payload, dict):
            return "EMPTY"
        cleaned = {k: v for k, v in payload.items() if k not in ("generated_at", "timestamp", "runtime_id", "retrieved_at")}
        s = json.dumps(cleaned, sort_keys=True, default=str)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]

    @classmethod
    def detect_material_changes(cls, current: dict[str, Any], last_state: dict[str, Any], timestamp_str: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Detects critical state transitions and returns formatted material event objects."""
        events = []

        checks = [
            ("SESSION_PHASE_CHANGED", "session_phase"),
            ("BROKER_AUTH_CHANGED", "broker_state"),
            ("SPOT_SOURCE_CHANGED", "spot_source"),
            ("FRESHNESS_CHANGED", "spot_freshness"),
            ("ATM_STRIKE_CHANGED", "atm_strike"),
            ("REGIME_CHANGED", "regime"),
            ("TREND_CHANGED", "trend"),
            ("FEED_HEALTH_CHANGED", "feed_health"),
        ]

        for ev_type, key in checks:
            old_v = last_state.get(key)
            new_v = current.get(key)
            if old_v is not None and new_v is not None and old_v != new_v:
                events.append({
                    "id": str(uuid4()),
                    "event_type": ev_type,
                    "timestamp": timestamp_str,
                    "field": key,
                    "old_value": old_v,
                    "new_value": new_v
                })

        old_st = last_state.get("stream_status")
        new_st = current.get("stream_status")
        if old_st is not None and new_st is not None and old_st != new_st:
            ev_type = "STREAM_CONNECTED" if new_st == "CONNECTED" else "STREAM_DISCONNECTED"
            events.append({
                "id": str(uuid4()),
                "event_type": ev_type,
                "timestamp": timestamp_str,
                "field": "stream_status",
                "old_value": old_st,
                "new_value": new_st
            })

        return events, dict(current)
