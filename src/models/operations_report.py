from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass(frozen=True)
class ServiceStatus:
    service_name: str
    status: str
    latency_ms: float
    message: str
    last_checked: str


@dataclass(frozen=True)
class StartupDiagnostics:
    config_valid: bool
    env_vars_valid: bool
    working_dirs_valid: bool
    required_folders_exist: bool
    cache_folders_exist: bool
    instrument_db_valid: bool
    checks: Dict[str, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class DependencyStatus:
    python_packages_valid: bool
    node_modules_valid: bool
    config_files_valid: bool
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResourceUsage:
    cpu_percent: float
    memory_used_mb: float
    memory_percent: float
    disk_free_gb: float
    disk_percent: float


@dataclass(frozen=True)
class SystemMetrics:
    uptime_seconds: float
    log_size_bytes: int
    cache_size_bytes: int
    python_version: str
    platform_info: str
    resources: ResourceUsage


@dataclass(frozen=True)
class HealthWarning:
    warning_id: str
    source: str
    severity: str
    message: str
    timestamp: str


@dataclass(frozen=True)
class ReadinessStatus:
    status: str
    readiness_score: float
    critical_blockers_count: int
    warnings_count: int


@dataclass(frozen=True)
class OperationsSummary:
    timestamp: str
    overall_status: str
    readiness_score: float
    uptime_str: str


@dataclass(frozen=True)
class OperationsReport:
    report_id: str
    timestamp: str
    summary: OperationsSummary
    readiness: ReadinessStatus
    services: List[ServiceStatus]
    startup: StartupDiagnostics
    dependencies: DependencyStatus
    metrics: SystemMetrics
    warnings: List[HealthWarning]
