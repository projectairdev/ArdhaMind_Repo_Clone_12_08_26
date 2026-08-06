from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.application.compatibility_serializer import CompatibilitySerializer
from src.application.data_quality_service import DataQualityService
from src.application.workstation_state_service import WorkstationStateService
from src.models.canonical_workstation_state import CanonicalWorkstationState
from src.models.data_quality import FreshnessStatus, ValueClassification
from src.models.decision_support import DecisionSupportReport


NOW = datetime(2026, 8, 6, 6, 0, tzinfo=timezone.utc)


def iso(seconds_ago: int = 0) -> str:
    return (NOW - timedelta(seconds=seconds_ago)).isoformat().replace("+00:00", "Z")


def payload(market_age: int = 1, option_age: int = 1) -> dict:
    return {
        "marketContext": {"price": 24500.5, "timestamp": iso(market_age)},
        "optionContext": {"pcr": 1.1, "timestamp": iso(option_age)},
        "marketScore": {"score": 68}, "opportunityContext": {"direction": "WATCH"},
        "strategyEvaluation": {"statusText": "monitor"}, "confidenceReport": {"score": 60},
        "riskReport": {"riskLevel": "MEDIUM"}, "explanationReport": {"summary": "Wait"},
        "newsSentiment": {}, "operationsReport": {"healthy": True},
    }


@pytest.mark.parametrize("kind,ages,expected", [
    ("nifty_spot", (5, 6, 16), (FreshnessStatus.FRESH, FreshnessStatus.STALE, FreshnessStatus.BLOCKED)),
    ("option_quote", (10, 11, 31), (FreshnessStatus.FRESH, FreshnessStatus.STALE, FreshnessStatus.BLOCKED)),
    ("option_aggregate", (15, 16, 46), (FreshnessStatus.FRESH, FreshnessStatus.STALE, FreshnessStatus.BLOCKED)),
])
def test_approved_freshness_transitions(kind, ages, expected):
    assert tuple(DataQualityService.classify(kind, iso(age), now=NOW)[0] for age in ages) == expected


def test_market_closed_is_not_stale():
    status, _ = DataQualityService.classify("nifty_spot", iso(1000), now=NOW, market_closed=True)
    assert status == FreshnessStatus.MARKET_CLOSED


def test_invalid_data_rejection_and_zero_semantics():
    assert not DataQualityService.is_valid_number(None)
    assert not DataQualityService.is_valid_number(float("nan"))
    assert DataQualityService.is_valid_number(0)
    assert not DataQualityService.is_valid_number(0, positive=True)


def test_canonical_schema_sequence_metadata_and_read_only_contract():
    first = WorkstationStateService.build_from_legacy(payload(), market_state="OPEN", now=NOW)
    second = WorkstationStateService.build_from_legacy(payload(), market_state="OPEN", now=NOW)
    data = first.to_dict()
    assert data["schema_version"] == "2.0.0"
    assert second.state_sequence > first.state_sequence
    assert data["data_quality"]["market_data"]["source"] == "kite_market_feed"
    assert data["data_quality"]["market_data"]["observed_at"] == iso(1)
    assert data["read_only_account_summary"] is None
    forbidden = ("place_order", "cancel_order", "exit_position", "quantity", "paper_portfolio", "mock_mode")
    rendered = repr(data).lower()
    assert not any(key in rendered for key in forbidden)


def test_forbidden_fields_are_removed_recursively():
    dirty = payload()
    dirty["marketContext"]["quantity"] = 50
    dirty["riskReport"]["capital_allocation"] = 100000
    state = WorkstationStateService.build_from_legacy(dirty, market_state="OPEN", now=NOW).to_dict()
    assert "quantity" not in repr(state)
    assert "capital_allocation" not in repr(state)


def test_section_blocking_is_dependency_scoped():
    state = WorkstationStateService.build_from_legacy(payload(market_age=16), market_state="OPEN", now=NOW).to_dict()
    assert state["technical_analysis"]["status"] == "blocked"
    assert state["market_score"]["status"] == "blocked"
    assert state["opportunity"]["status"] == "blocked"
    assert state["news_intelligence"]["status"] == "unavailable"
    assert "validated market context" in state["workspace_readiness"]["live_assistant"]["dependency_reasons"]


def test_option_block_degrades_analysis_but_not_market():
    state = WorkstationStateService.build_from_legacy(payload(option_age=46), market_state="OPEN", now=NOW).to_dict()
    assert state["market_data"]["status"] == "ready"
    assert state["option_intelligence"]["status"] == "blocked"
    assert state["workspace_readiness"]["todays_analysis"]["status"] == "degraded"


def test_unavailable_serialization_never_fabricates_zero():
    state = WorkstationStateService.build_from_legacy({}, market_state="OPEN", now=NOW)
    result = CompatibilitySerializer.to_phase1_payload(state)
    assert result["marketContext"] == {"status": "unavailable"}
    assert result["optionContext"] == {"status": "unavailable"}
    assert 0 not in result["marketContext"].values()
    assert result["canonicalMetadata"]["schemaVersion"] == "2.0.0"


def test_decision_support_compatibility_is_non_executable():
    report = DecisionSupportReport(market_interpretation="Range", blockers=["spot"],
                                   missing_confirmations=["spot"])
    legacy = report.to_legacy_dict()
    assert legacy["summary"]["overallAction"] == "HOLD"
    assert legacy["candidateDecisions"] == []
    assert "quantity" not in repr(report.to_dict()).lower()


def test_production_classification_has_no_mock_or_sample():
    values = {item.value for item in ValueClassification}
    assert "mock" not in values and "sample" not in values


def test_kite_expired_is_explicit_and_settings_accessible():
    state = WorkstationStateService.build_from_legacy(payload(), broker_state="SESSION_EXPIRED",
                                                       market_state="OPEN", now=NOW).to_dict()
    assert state["broker_status"]["status"] == "session_expired"
    assert state["broker_status"]["reconnect_required"] is True
    assert state["market_feed_status"]["status"] == "unavailable"
    assert state["workspace_readiness"]["settings"]["accessible"] is True


def test_market_closed_preserves_snapshot_as_historical():
    state = WorkstationStateService.build_from_legacy(payload(market_age=1000, option_age=1000),
                                                       market_state="CLOSED", now=NOW).to_dict()
    assert state["market_data"]["price"] == 24500.5
    assert state["market_data"]["status"] == "market_closed"
    assert state["data_quality"]["market_data"]["value_classification"] == "historical"


def test_official_kite_package_resolution():
    import kiteconnect
    module_path = Path(kiteconnect.__file__).resolve()
    root = Path(__file__).resolve().parents[1]
    assert module_path != root / "kiteconnect.py"
    assert module_path.name == "__init__.py" and module_path.parent.name == "kiteconnect"
