from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PipelineStageResult:
    status: str
    value: Any = None
    source: str = "canonical_analytical_pipeline"
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass(frozen=True)
class AnalyticalPipelineResult:
    snapshot_id: str
    generated_at: str
    stages: dict[str, PipelineStageResult]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def compatibility_values(self) -> dict[str, Any]:
        names = {
            "market": "marketContext", "options": "optionContext", "score": "marketScore",
            "opportunity": "opportunityContext", "strategy": "strategyEvaluation",
            "scenarios": "tradeScenarios", "confidence": "confidenceReport",
            "risk": "riskReport", "decision_support": "decisionReport",
            "explanation": "explanationReport", "news": "newsSentiment",
        }
        result: dict[str, Any] = {}
        for stage, target in names.items():
            item = self.stages[stage]
            value = item.value if item.value is not None else {}
            if stage == "scenarios":
                result[target] = value
            else:
                result[target] = {**value, "status": item.status, "source": item.source,
                                  "blockers": item.blockers, "warnings": item.warnings}
        return result
