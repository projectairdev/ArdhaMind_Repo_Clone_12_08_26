# src/intelligence_engine/what_changed_engine.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
from src.models.intelligence_snapshot import IntelligenceSnapshot, WhatChangedEvent


class WhatChangedEngine:
    """
    Detector for meaningful intraday changes between consecutive IntelligenceSnapshots.
    Produces clean, structured WhatChangedEvents for trader awareness.
    """

    @classmethod
    def compare_snapshots(
        cls,
        previous: Optional[IntelligenceSnapshot | Dict[str, Any]],
        current: IntelligenceSnapshot | Dict[str, Any]
    ) -> List[WhatChangedEvent]:
        if not previous:
            return []

        prev_dict = previous.to_dict() if hasattr(previous, "to_dict") else previous
        curr_dict = current.to_dict() if hasattr(current, "to_dict") else current

        events: List[WhatChangedEvent] = []
        ts = curr_dict.get("timestamp", "")

        # 1. Regime Change
        p_regime = prev_dict.get("regime", "")
        c_regime = curr_dict.get("regime", "")
        if p_regime and c_regime and p_regime != c_regime:
            events.append(WhatChangedEvent(
                event_type="REGIME_CHANGED",
                summary=f"Market regime transitioned from {p_regime} to {c_regime}.",
                previous_value=p_regime,
                current_value=c_regime,
                timestamp=ts,
                significance="HIGH"
            ))

        # 2. Directional Bias Shift
        p_bias = prev_dict.get("directional_bias", "")
        c_bias = curr_dict.get("directional_bias", "")
        if p_bias and c_bias and p_bias != c_bias:
            events.append(WhatChangedEvent(
                event_type="BIAS_SHIFTED",
                summary=f"Directional bias shifted from {p_bias} to {c_bias}.",
                previous_value=p_bias,
                current_value=c_bias,
                timestamp=ts,
                significance="HIGH"
            ))

        # 3. Breadth Shift
        p_brd = prev_dict.get("breadth_summary", {}) or {}
        c_brd = curr_dict.get("breadth_summary", {}) or {}
        p_adv = int(p_brd.get("advances", 0))
        c_adv = int(c_brd.get("advances", 0))
        if p_adv > 0 and c_adv > 0 and abs(c_adv - p_adv) >= 5:
            direction = "IMPROVED" if c_adv > p_adv else "DETERIORATED"
            events.append(WhatChangedEvent(
                event_type=f"BREADTH_{direction}",
                summary=f"NIFTY breadth {direction.lower()}: Advances moved from {p_adv} to {c_adv}.",
                previous_value=p_adv,
                current_value=c_adv,
                timestamp=ts,
                significance="MEDIUM"
            ))

        # 4. Primary Trade Suggestion State Transition
        p_sug = prev_dict.get("primary_suggestion", {}) or {}
        c_sug = curr_dict.get("primary_suggestion", {}) or {}
        p_state = p_sug.get("state", "NO_TRADE")
        c_state = c_sug.get("state", "NO_TRADE")
        c_strat = c_sug.get("strategy", "SETUP")

        if p_state != c_state:
            if c_state == "QUALIFIED":
                events.append(WhatChangedEvent(
                    event_type="OPPORTUNITY_QUALIFIED",
                    summary=f"Trade setup '{c_strat}' ({c_sug.get('contract_symbol', '')}) is now QUALIFIED.",
                    previous_value=p_state,
                    current_value=c_state,
                    timestamp=ts,
                    significance="HIGH"
                ))
            elif c_state == "ARMED":
                events.append(WhatChangedEvent(
                    event_type="OPPORTUNITY_ARMED",
                    summary=f"Trade setup '{c_strat}' is ARMED and watching trigger zone {c_sug.get('underlying_trigger', '')}.",
                    previous_value=p_state,
                    current_value=c_state,
                    timestamp=ts,
                    significance="HIGH"
                ))
            elif c_state == "INVALIDATED":
                events.append(WhatChangedEvent(
                    event_type="OPPORTUNITY_INVALIDATED",
                    summary=f"Trade setup '{p_sug.get('strategy', '')}' was INVALIDATED.",
                    previous_value=p_state,
                    current_value=c_state,
                    timestamp=ts,
                    significance="HIGH"
                ))

        return events
