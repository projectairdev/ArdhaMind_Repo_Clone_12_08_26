from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime

VALID_RESULTS = {"HIT", "NEAR", "MISS", "NOT_EVALUABLE", "PENDING"}
VALID_PHASES = {"PRE_MARKET", "EARLY_SESSION", "LIVE_INTRADAY", "CLOSE", "POST_MARKET"}


@dataclass
class ArdhaEvaluationRecord:
    id: str
    trading_date: str
    phase: str
    captured_at: str
    metric: str
    ardha_value: str
    prediction_at: Optional[str] = None
    metric_id: Optional[str] = None
    schema_version: int = 2
    ardha_value_numeric: Optional[float] = None
    ardha_payload: Dict[str, Any] = field(default_factory=dict)
    ardha_context: Dict[str, Any] = field(default_factory=dict)
    spot_at_capture: Optional[float] = None
    source_state_sequence: Optional[int] = None
    runtime_id: Optional[str] = None
    engine_version: Optional[str] = None
    reference_session_date: Optional[str] = None
    target_session_date: Optional[str] = None

    real_value: Optional[str] = None
    real_value_numeric: Optional[float] = None
    real_payload: Dict[str, Any] = field(default_factory=dict)
    evaluated_at: Optional[str] = None

    result: str = "PENDING"
    error_value: Optional[float] = None
    notes: Optional[str] = None
    pending_reason: Optional[str] = None

    immutable: bool = True

    def __post_init__(self):
        if self.result not in VALID_RESULTS:
            raise ValueError(f"Invalid result: '{self.result}'. Must be one of {VALID_RESULTS}")
        if self.phase not in VALID_PHASES:
            raise ValueError(f"Invalid phase: '{self.phase}'. Must be one of {VALID_PHASES}")
        if not self.prediction_at:
            self.prediction_at = self.captured_at
        if not self.metric_id and self.metric:
            self.metric_id = self.metric.lower().replace(" ", "_").replace("/", "_").replace("-", "_")

    def attach_evaluation(
        self,
        real_value: Optional[str],
        result: str,
        real_value_numeric: Optional[float] = None,
        real_payload: Optional[Dict[str, Any]] = None,
        error_value: Optional[float] = None,
        evaluated_at: Optional[str] = None,
        notes: Optional[str] = None,
        pending_reason: Optional[str] = None,
    ) -> ArdhaEvaluationRecord:
        """
        Attaches post-market or intraday reality and evaluation result while guaranteeing
        that original prediction parameters remain untouched.
        """
        if result not in VALID_RESULTS:
            raise ValueError(f"Invalid evaluation result: '{result}'")

        eval_time = evaluated_at or datetime.now().isoformat()

        return ArdhaEvaluationRecord(
            id=self.id,
            trading_date=self.trading_date,
            phase=self.phase,
            captured_at=self.captured_at,
            metric=self.metric,
            prediction_at=self.prediction_at,
            metric_id=self.metric_id,
            schema_version=self.schema_version,
            ardha_value=self.ardha_value,
            ardha_value_numeric=self.ardha_value_numeric,
            ardha_payload=dict(self.ardha_payload or {}),
            ardha_context=dict(self.ardha_context or {}),
            spot_at_capture=self.spot_at_capture,
            source_state_sequence=self.source_state_sequence,
            runtime_id=self.runtime_id,
            engine_version=self.engine_version,
            reference_session_date=self.reference_session_date,
            target_session_date=self.target_session_date,
            real_value=real_value,
            real_value_numeric=real_value_numeric,
            real_payload=dict(real_payload or {}),
            evaluated_at=eval_time if result != "PENDING" else None,
            result=result,
            error_value=error_value,
            notes=notes,
            pending_reason=pending_reason,
            immutable=True,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "trading_date": self.trading_date,
            "phase": self.phase,
            "captured_at": self.captured_at,
            "prediction_at": self.prediction_at or self.captured_at,
            "metric": self.metric,
            "metric_id": self.metric_id,
            "schema_version": self.schema_version,
            "ardha_value": self.ardha_value,
            "ardha_value_numeric": self.ardha_value_numeric,
            "ardha_payload": self.ardha_payload or {},
            "ardha_context": self.ardha_context or {},
            "spot_at_capture": self.spot_at_capture,
            "source_state_sequence": self.source_state_sequence,
            "runtime_id": self.runtime_id,
            "engine_version": self.engine_version,
            "reference_session_date": self.reference_session_date,
            "target_session_date": self.target_session_date,
            "real_value": self.real_value,
            "real_value_numeric": self.real_value_numeric,
            "real_payload": self.real_payload or {},
            "evaluated_at": self.evaluated_at,
            "result": self.result,
            "error_value": self.error_value,
            "notes": self.notes,
            "pending_reason": self.pending_reason,
            "immutable": self.immutable,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ArdhaEvaluationRecord:
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            trading_date=data.get("trading_date", ""),
            phase=data.get("phase", "LIVE_INTRADAY"),
            captured_at=data.get("captured_at", ""),
            metric=data.get("metric", ""),
            prediction_at=data.get("prediction_at") or data.get("captured_at"),
            metric_id=data.get("metric_id"),
            schema_version=data.get("schema_version", 1),
            ardha_value=data.get("ardha_value", "UNAVAILABLE"),
            ardha_value_numeric=data.get("ardha_value_numeric"),
            ardha_payload=data.get("ardha_payload") or {},
            ardha_context=data.get("ardha_context") or {},
            spot_at_capture=data.get("spot_at_capture"),
            source_state_sequence=data.get("source_state_sequence"),
            runtime_id=data.get("runtime_id"),
            engine_version=data.get("engine_version"),
            reference_session_date=data.get("reference_session_date"),
            target_session_date=data.get("target_session_date"),
            real_value=data.get("real_value"),
            real_value_numeric=data.get("real_value_numeric"),
            real_payload=data.get("real_payload") or {},
            evaluated_at=data.get("evaluated_at"),
            result=data.get("result", "PENDING"),
            error_value=data.get("error_value"),
            notes=data.get("notes"),
            pending_reason=data.get("pending_reason"),
            immutable=data.get("immutable", True),
        )
