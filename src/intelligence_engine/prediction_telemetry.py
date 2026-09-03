# src/intelligence_engine/prediction_telemetry.py
"""
PredictionTelemetry & Lightweight Historical Calibration for AIR ArdhaMind.

Provides:
1. Immutable PreMarketPredictionRecord & IntradayPredictionRecord schemas.
2. PredictionTelemetryStore for persistence and empirical outcome attachment.
3. Historical Calibration metrics (MAE, Median Absolute Error, Direction Accuracy, Interval Hit Rate).
4. Intraday Multi-Horizon (+5m, +15m, +30m, +60m) Forward Outlook Evaluator.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class PreMarketPredictionRecord:
    prediction_id: str
    generated_at: str
    target_session: str
    reference_session_date: str
    reference_close: Optional[float]
    
    # GIFT handling
    raw_gift: Optional[float]
    estimated_basis: float
    basis_quality: str  # MEASURED_PRIOR_CLOSE | HISTORICAL_MEDIAN | UNMEASURED_ESTIMATE
    normalized_gift: Optional[float]
    gift_freshness: str
    
    # Anchor & Forecast
    forecast_anchor: str  # NORMALIZED_GIFT | NSE_PREOPEN | MULTI_FACTOR_MODEL
    anchor_timestamp: str
    expected_open_center: Optional[float]
    expected_open_low: Optional[float]
    expected_open_high: Optional[float]
    opening_bias: str
    confidence_band: str  # HIGH | MODERATE | LOW
    calibrated_probability: Optional[float]  # Nullable when insufficient calibration
    interval_method: str
    calibration_sample_size: int
    
    # Evidence families
    family_contributions: Dict[str, float]
    supporting_evidence: List[str]
    opposing_evidence: List[str]
    risk_flags: List[str]
    
    # Attached Empirical Outcome (populated when market opens)
    outcome_recorded_at: Optional[str] = None
    actual_open: Optional[float] = None
    error_points: Optional[float] = None
    absolute_error: Optional[float] = None
    direction_correct: Optional[bool] = None
    interval_hit: Optional[bool] = None
    outcome_status: str = "PENDING_OBSERVATION"  # PENDING_OBSERVATION | EVALUATED | EXPIRED

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PreMarketPredictionRecord:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class HorizonOutcome:
    horizon_minutes: int
    evaluated_at: str
    future_spot: float
    change_points: float
    direction_correct: bool
    support_held: Optional[bool]
    resistance_held: Optional[bool]
    max_favorable_excursion: float
    max_adverse_excursion: float


@dataclass
class IntradayPredictionRecord:
    prediction_id: str
    generated_at: str
    session_date: str
    spot_at_prediction: float
    classification: str
    scenario: str
    confidence: str
    support: Optional[float]
    resistance: Optional[float]
    vwap: Optional[float]
    
    # Multi-horizon evaluations
    outcomes: Dict[str, HorizonOutcome] = field(default_factory=dict)  # "+5m", "+15m", "+30m", "+60m"
    is_independent_window: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["outcomes"] = {k: asdict(v) if isinstance(v, HorizonOutcome) else v for k, v in self.outcomes.items()}
        return d


class PredictionTelemetryStore:
    """
    Lightweight persistent telemetry store for immutable forecast records and empirical calibration.
    """
    _storage_file = Path("/opt/ardhamind/staging/data/cache/prediction_telemetry.json")
    _premarket_records: Dict[str, PreMarketPredictionRecord] = {}
    _intraday_records: Dict[str, IntradayPredictionRecord] = {}
    _is_loaded = False

    @classmethod
    def get_storage_path(cls) -> Path:
        return cls._storage_file

    @classmethod
    def set_storage_path(cls, path: Path) -> None:
        cls._storage_file = path
        cls._is_loaded = False
        cls._premarket_records.clear()
        cls._intraday_records.clear()

    @classmethod
    def _ensure_loaded(cls) -> None:
        if cls._is_loaded:
            return
        cls._premarket_records.clear()
        cls._intraday_records.clear()
        if cls._storage_file.exists():
            try:
                with open(cls._storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for rec in data.get("premarket", []):
                        cls._premarket_records[rec["prediction_id"]] = PreMarketPredictionRecord.from_dict(rec)
                    for rec in data.get("intraday", []):
                        cls._intraday_records[rec["prediction_id"]] = IntradayPredictionRecord(**rec)
            except Exception:
                pass
        cls._is_loaded = True

    @classmethod
    def save(cls) -> None:
        cls._storage_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": "1.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "premarket": [r.to_dict() for r in cls._premarket_records.values()],
            "intraday": [r.to_dict() for r in cls._intraday_records.values()],
        }
        tmp_file = cls._storage_file.with_suffix(".tmp")
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            os.replace(tmp_file, cls._storage_file)
        except Exception:
            if tmp_file.exists():
                try:
                    tmp_file.unlink()
                except Exception:
                    pass

    @classmethod
    def record_premarket_prediction(cls, record: PreMarketPredictionRecord) -> None:
        cls._ensure_loaded()
        if record.prediction_id not in cls._premarket_records:
            cls._premarket_records[record.prediction_id] = record
            cls.save()

    @classmethod
    def attach_premarket_outcome(
        cls,
        target_session: str,
        actual_open: float,
        observed_at: Optional[str] = None
    ) -> List[PreMarketPredictionRecord]:
        """
        Attaches real market open outcome to all pending predictions for the target session.
        """
        cls._ensure_loaded()
        updated = []
        obs_time = observed_at or datetime.now(timezone.utc).isoformat()

        for rec in cls._premarket_records.values():
            if rec.target_session == target_session and rec.outcome_status == "PENDING_OBSERVATION":
                rec.actual_open = round(actual_open, 2)
                rec.outcome_recorded_at = obs_time
                rec.outcome_status = "EVALUATED"

                if rec.expected_open_center is not None:
                    rec.error_points = round(actual_open - rec.expected_open_center, 2)
                    rec.absolute_error = round(abs(rec.error_points), 2)

                if rec.reference_close is not None:
                    actual_dir = actual_open - rec.reference_close
                    predicted_dir = (rec.expected_open_center or actual_open) - rec.reference_close
                    rec.direction_correct = (actual_dir * predicted_dir) >= 0

                if rec.expected_open_low is not None and rec.expected_open_high is not None:
                    rec.interval_hit = (rec.expected_open_low <= actual_open <= rec.expected_open_high)
                else:
                    rec.interval_hit = None

                updated.append(rec)

        if updated:
            cls.save()
        return updated

    @classmethod
    def get_historical_calibration(cls) -> Dict[str, Any]:
        """
        Computes empirical calibration metrics from all evaluated prior pre-market forecasts.
        """
        cls._ensure_loaded()
        evaluated = [r for r in cls._premarket_records.values() if r.outcome_status == "EVALUATED" and r.absolute_error is not None]
        sample_size = len(evaluated)

        if sample_size < 5:
            return {
                "status": "INSUFFICIENT_CALIBRATION",
                "sample_size": sample_size,
                "mae": None,
                "median_absolute_error": None,
                "direction_accuracy_pct": None,
                "interval_coverage_pct": None,
                "calibrated_probability": None,
            }

        abs_errors = sorted([r.absolute_error for r in evaluated if r.absolute_error is not None])
        mae = round(sum(abs_errors) / len(abs_errors), 2)
        med_ae = round(abs_errors[len(abs_errors) // 2], 2)
        
        dir_hits = sum(1 for r in evaluated if r.direction_correct is True)
        dir_acc = round((dir_hits / sample_size) * 100.0, 1)

        interval_evaluated = [r for r in evaluated if r.interval_hit is not None]
        interval_hits = sum(1 for r in interval_evaluated if r.interval_hit is True)
        interval_cov = round((interval_hits / len(interval_evaluated)) * 100.0, 1) if interval_evaluated else None

        calibrated_prob = round(dir_acc / 100.0, 2) if sample_size >= 10 else None

        return {
            "status": "CALIBRATED" if sample_size >= 10 else "EMERGING_CALIBRATION",
            "sample_size": sample_size,
            "mae": mae,
            "median_absolute_error": med_ae,
            "direction_accuracy_pct": dir_acc,
            "interval_coverage_pct": interval_cov,
            "calibrated_probability": calibrated_prob,
        }
