from __future__ import annotations

from typing import Any

from src.models.canonical_workstation_state import CanonicalWorkstationState


class CompatibilitySerializer:
    """DEPRECATED: CompatibilitySerializer is deprecated since Phase 5.1
    and is retained only for backward-compatibility in legacy unit tests.
    """

    FIELD_MAP = {
        "market_data": "marketContext", "option_intelligence": "optionContext",
        "market_score": "marketScore", "opportunity": "opportunityContext",
        "strategy_suitability": "strategyEvaluation", "confidence": "confidenceReport",
        "deterministic_risk": "riskReport", "decision_support": "decisionReport",
        "explanation": "explanationReport", "news_intelligence": "newsSentiment",
        "operations_health": "operationsReport",
    }

    @classmethod
    def to_phase1_payload(cls, state: CanonicalWorkstationState,
                          legacy_payload: dict[str, Any] | None = None) -> dict[str, Any]:
        canonical = state.to_dict()
        result = dict(legacy_payload or {})
        populated: list[str] = []
        legacy: list[str] = []
        for source, target in cls.FIELD_MAP.items():
            section = canonical[source]
            status = section.get("status") if isinstance(section, dict) else None
            # Structured blocked/unavailable states remain structured; never synthesize numeric zero.
            if section:
                result[target] = section
                populated.append(target)
            elif target in result:
                legacy.append(target)
        result["workspaceReadiness"] = canonical["workspace_readiness"]
        result["canonicalMetadata"] = {
            "schemaVersion": canonical["schema_version"],
            "stateSequence": canonical["state_sequence"],
            "generatedAt": canonical["generated_at"],
            "dataQuality": canonical["data_quality"],
            "canonicalFields": populated,
            "legacyProducedFields": sorted(set(legacy) | (set(result) - set(cls.FIELD_MAP.values())
                                                           - {"workspaceReadiness", "canonicalMetadata"})),
        }
        return result
