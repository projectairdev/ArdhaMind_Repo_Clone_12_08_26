from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


FORBIDDEN_CANONICAL_KEYS = {
    "place_order", "modify_order", "cancel_order", "exit_position", "quantity",
    "allocated_lots", "lot_recommendations", "capital_allocation", "allocated_capital",
    "paper_portfolio", "virtual_positions", "virtual_pnl", "paper_journal",
    "mock_mode", "sample_mode", "trading_mode", "execution_mode",
}


def sanitize_read_only(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: sanitize_read_only(v) for k, v in value.items()
                if k.lower().replace("-", "_") not in FORBIDDEN_CANONICAL_KEYS}
    if isinstance(value, list):
        return [sanitize_read_only(item) for item in value]
    return value


@dataclass(frozen=True)
class CanonicalWorkstationState:
    schema_version: str
    state_sequence: int
    generated_at: str
    runtime_id: str
    market_session: dict[str, Any]
    application_status: dict[str, Any]
    broker_status: dict[str, Any]
    market_feed_status: dict[str, Any]
    market_data: dict[str, Any]
    technical_analysis: dict[str, Any]
    option_intelligence: dict[str, Any]
    market_score: dict[str, Any]
    opportunity: dict[str, Any]
    strategy_suitability: dict[str, Any]
    trade_scenarios: list[dict[str, Any]]
    confidence: dict[str, Any]
    deterministic_risk: dict[str, Any]
    decision_support: dict[str, Any]
    explanation: dict[str, Any]
    news_intelligence: dict[str, Any]
    read_only_account_summary: Optional[dict[str, Any]]
    operations_health: dict[str, Any]
    workspace_readiness: dict[str, Any]
    data_quality: dict[str, Any]
    evening_report: dict[str, Any]
    intraday_report: dict[str, Any]
    validation_report: dict[str, Any]
    optimization_report: dict[str, Any]
    analytics_report: dict[str, Any]
    macro_intelligence: Optional[dict[str, Any]] = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        result = sanitize_read_only(asdict(self))
        self._assert_read_only(result)
        return result

    @staticmethod
    def _assert_read_only(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                normalized = key.lower().replace("-", "_")
                if normalized in FORBIDDEN_CANONICAL_KEYS:
                    raise ValueError(f"Forbidden canonical field: {key}")
                CanonicalWorkstationState._assert_read_only(child)
        elif isinstance(value, list):
            for child in value:
                CanonicalWorkstationState._assert_read_only(child)
