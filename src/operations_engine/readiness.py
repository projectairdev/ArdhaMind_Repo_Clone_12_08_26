from __future__ import annotations

from typing import List, Dict, Any
from src.models.operations_report import (
    ReadinessStatus,
    ServiceStatus,
    StartupDiagnostics,
    DependencyStatus,
    SystemMetrics,
    HealthWarning
)


class ReadinessEvaluator:
    """
    Task 10: Compiles overall readiness metrics, classifications, and scores.
    """

    @staticmethod
    def evaluate(
        services: List[ServiceStatus],
        startup: StartupDiagnostics,
        dependencies: DependencyStatus,
        metrics: SystemMetrics,
        warnings: List[HealthWarning]
    ) -> ReadinessStatus:
        """
        Calculates readiness score and classifies readiness status based on diagnostic results.
        """
        score = 100.0
        critical_blockers = 0
        warnings_count = len(warnings)

        # 1. Startup Diagnostics
        if not startup.config_valid:
            score -= 25.0
            critical_blockers += 1
        if not startup.env_vars_valid:
            score -= 20.0
            critical_blockers += 1
        if not startup.working_dirs_valid:
            score -= 10.0
            warnings_count += 1
        if not startup.instrument_db_valid:
            score -= 15.0
            critical_blockers += 1

        # 2. Dependency Validations
        if not dependencies.python_packages_valid:
            score -= 25.0
            critical_blockers += 1
        if not dependencies.node_modules_valid:
            score -= 10.0
            warnings_count += 1
        if not dependencies.config_files_valid:
            score -= 15.0
            warnings_count += 1

        # 3. Service Statuses
        for svc in services:
            if svc.status == "CRITICAL":
                score -= 35.0
                critical_blockers += 1
            elif svc.status == "DEGRADED":
                score -= 15.0
                warnings_count += 1
            elif svc.status == "WARNING":
                score -= 10.0
                warnings_count += 1

        # 4. System Resources Check
        resources = metrics.resources
        if resources.cpu_percent > 95.0:
            score -= 10.0
            warnings_count += 1
        if resources.memory_percent > 95.0:
            score -= 10.0
            warnings_count += 1
        if resources.disk_percent > 98.0:
            score -= 15.0
            critical_blockers += 1

        # Calculate final score bounded [0.0, 100.0]
        final_score = max(0.0, min(100.0, score))

        # Classify overall readiness state
        if critical_blockers > 0:
            status = "NOT_READY"
        elif final_score >= 90.0 and warnings_count == 0:
            status = "READY"
        elif final_score >= 75.0:
            status = "READY_WITH_WARNINGS"
        else:
            status = "LIMITED"

        return ReadinessStatus(
            status=status,
            readiness_score=round(final_score, 2),
            critical_blockers_count=critical_blockers,
            warnings_count=warnings_count
        )
