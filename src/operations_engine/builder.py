from __future__ import annotations

import time
from uuid import uuid4
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.models.operations_report import (
    OperationsReport,
    OperationsSummary,
    ServiceStatus,
    HealthWarning
)
from src.operations_engine.startup import StartupDiagnosticManager
from src.operations_engine.dependency_checker import DependencyValidator
from src.operations_engine.service_monitor import ServiceHealthMonitor
from src.operations_engine.system_metrics import SystemMetricsCollector
from src.operations_engine.readiness import ReadinessEvaluator


class OperationsReportBuilder:
    """
    Ties together all stateless operations monitoring subsystems to construct
    the final immutable OperationsReport.
    """

    @staticmethod
    def build(
        custom_env: Optional[Dict[str, str]] = None,
        custom_paths: Optional[Dict[str, str]] = None,
        mock_packages: Optional[Dict[str, bool]] = None,
        mock_node_modules: Optional[Dict[str, bool]] = None,
        mock_broker_data: Optional[Dict[str, Any]] = None,
        mock_market_data: Optional[Dict[str, Any]] = None,
        mock_news_data: Optional[Dict[str, Any]] = None,
        mock_execution_data: Optional[Dict[str, Any]] = None,
        mock_resources: Optional[Dict[str, float]] = None,
        mock_sizes: Optional[Dict[str, int]] = None
    ) -> OperationsReport:
        """
        Gathers operational diagnostics and generates an OperationsReport.
        """
        report_id = f"OP_REP_{uuid4().hex[:8].upper()}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Startup Diagnostics
        startup = StartupDiagnosticManager.run_diagnostics(
            custom_env=custom_env,
            custom_paths=custom_paths
        )

        # 2. Dependency check
        dependencies = DependencyValidator.validate_dependencies(
            mock_packages=mock_packages,
            mock_node_modules=mock_node_modules,
            custom_root=custom_paths.get("root_dir") if custom_paths else None,
            custom_env=custom_env
        )

        # 3. Services Health & Warnings Aggregation
        services: List[ServiceStatus] = []
        warnings: List[HealthWarning] = []

        # Broker
        brk_status, brk_warns = ServiceHealthMonitor.monitor_broker(mock_broker_data)
        services.append(brk_status)
        warnings.extend(brk_warns)

        # Market Data
        mkt_status, mkt_warns = ServiceHealthMonitor.monitor_market_data(mock_market_data)
        services.append(mkt_status)
        warnings.extend(mkt_warns)

        # News
        nws_status, nws_warns = ServiceHealthMonitor.monitor_news(mock_news_data)
        services.append(nws_status)
        warnings.extend(nws_warns)

        # Execution Layer
        exe_status, exe_warns = ServiceHealthMonitor.monitor_execution_layer(mock_execution_data)
        services.append(exe_status)
        warnings.extend(exe_warns)

        # Real-Time Streaming Layer
        from src.broker.services.broker_service import BrokerService
        brk_svc = BrokerService.get_instance()
        str_status, str_warns = ServiceHealthMonitor.monitor_streaming(brk_svc, mock_market_data)
        services.append(str_status)
        warnings.extend(str_warns)


        # 4. System Metrics
        metrics = SystemMetricsCollector.collect_metrics(
            mock_resources=mock_resources,
            mock_sizes=mock_sizes
        )

        # 5. Readiness Evaluation
        readiness = ReadinessEvaluator.evaluate(
            services=services,
            startup=startup,
            dependencies=dependencies,
            metrics=metrics,
            warnings=warnings
        )

        # Format uptime string (e.g. "1h 23m" or "45s")
        uptime_secs = metrics.uptime_seconds
        if uptime_secs < 60:
            uptime_str = f"{int(uptime_secs)}s"
        elif uptime_secs < 3600:
            uptime_str = f"{int(uptime_secs // 60)}m {int(uptime_secs % 60)}s"
        else:
            uptime_str = f"{int(uptime_secs // 3600)}h {int((uptime_secs % 3600) // 60)}m"

        summary = OperationsSummary(
            timestamp=timestamp,
            overall_status=readiness.status,
            readiness_score=readiness.readiness_score,
            uptime_str=uptime_str
        )

        return OperationsReport(
            report_id=report_id,
            timestamp=timestamp,
            summary=summary,
            readiness=readiness,
            services=services,
            startup=startup,
            dependencies=dependencies,
            metrics=metrics,
            warnings=warnings
        )
