# src/live_assistant/grounding_validator.py
"""
Grounding Validator for Live Assistant.
Performs strict post-generation verification to block unsupported market numbers,
fake trade setups, or contradictory LLM outputs.
"""
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Union

from src.live_assistant.evidence_packet import BoundedEvidencePacket


@dataclass
class GroundingValidationResult:
    is_valid: bool
    violations: List[str] = field(default_factory=list)


class GroundingValidator:
    """
    Validates LLM generated answers against the canonical evidence packet.
    """

    @classmethod
    def extract_numbers_from_dict(cls, data: Any) -> Set[str]:
        """Recursively extracts all numeric strings and floats from nested dictionaries/lists."""
        found: Set[str] = set()
        if isinstance(data, dict):
            for v in data.values():
                found.update(cls.extract_numbers_from_dict(v))
        elif isinstance(data, list):
            for item in data:
                found.update(cls.extract_numbers_from_dict(item))
        elif isinstance(data, (int, float)):
            found.add(str(data))
            if isinstance(data, float):
                found.add(f"{data:.2f}")
                found.add(f"{data:.1f}")
                found.add(str(int(data)))
        elif isinstance(data, str):
            # Extract numbers inside text like "24,250" or "1.25"
            matches = re.findall(r"\d+(?:,\d+)*(?:\.\d+)?", data)
            for m in matches:
                clean_m = m.replace(",", "")
                found.add(clean_m)
                found.add(m)
        return found

    @classmethod
    def validate(cls, llm_response: str, packet: BoundedEvidencePacket) -> GroundingValidationResult:
        violations: List[str] = []
        resp_lower = llm_response.lower()

        # 1. Trade Safety Gate: NO_SETUP / NONE cannot become a trade recommendation
        opp_state = packet.evidence.get("opportunity_state", {})
        opp_status = str(opp_state.get("status", "NO_SETUP")).upper()

        if opp_status in ("NO_SETUP", "NONE", "UNQUALIFIED"):
            prohibited_trade_triggers = [
                "buy ce", "buy pe", "enter call", "enter put", "take position",
                "recommended entry", "target 1 is", "stop loss at"
            ]
            for trigger in prohibited_trade_triggers:
                if trigger in resp_lower:
                    violations.append(
                        f"Trade Safety Violation: Generated '{trigger}' when canonical opportunity status is {opp_status}."
                    )

        # 2. Hallucination Guard: User prompt injection resistance
        prohibited_hallucination_phrases = [
            "ignore ardhamind", "my own prediction", "independently calculated",
            "model forecast", "i predict"
        ]
        for phrase in prohibited_hallucination_phrases:
            if phrase in resp_lower:
                violations.append(f"Hallucination Contract Violation: Found phrase '{phrase}'.")

        # 3. Numeric Grounding Check
        # Extract all numbers from evidence packet
        packet_numbers = cls.extract_numbers_from_dict(packet.evidence)
        # Add basic single digit integers 0-9 to avoid flagging common prose counts
        packet_numbers.update({str(i) for i in range(10)})
        # Add timestamp numbers
        packet_numbers.update(cls.extract_numbers_from_dict(packet.market_timestamp))

        # Find numbers in LLM response
        resp_numbers = re.findall(r"\b\d+(?:,\d+)*(?:\.\d+)?\b", llm_response)

        for num_str in resp_numbers:
            clean_num = num_str.replace(",", "")
            # Skip small integers/percentages (e.g. 1st, 50%, 78/100, 15m)
            if clean_num.isdigit() and int(clean_num) <= 100:
                continue
            if clean_num in ("2026", "2025", "2024", "0915", "15", "30", "45", "60"):
                continue

            if clean_num not in packet_numbers and num_str not in packet_numbers:
                violations.append(
                    f"Numeric Grounding Failure: Number '{num_str}' in answer is not present in canonical evidence."
                )

        is_valid = len(violations) == 0
        return GroundingValidationResult(is_valid=is_valid, violations=violations)
