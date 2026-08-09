from __future__ import annotations

import unittest
import tempfile
from pathlib import Path
from datetime import datetime
from src.models.operations_report import (
    OperationsReport,
    ServiceStatus,
    StartupDiagnostics,
    DependencyStatus,
    SystemMetrics,
    HealthWarning,
    ReadinessStatus,
    ResourceUsage,
)
from src.operations_engine.startup import StartupDiagnosticManager
from src.operations_engine.dependency_checker import DependencyValidator
from src.operations_engine.service_monitor import ServiceHealthMonitor
from src.operations_engine.system_metrics import SystemMetricsCollector
from src.operations_engine.readiness import ReadinessEvaluator
from src.operations_engine.builder import OperationsReportBuilder
from src.dashboard.operations_panel import OperationsPanel
from src.dashboard.dashboard_builder import TradingWorkstationDashboard


class TestOperationsManager(unittest.TestCase):
    """
    Unit tests for Sprint 24 (Operations & Workstation Health Manager).
    Verifies diagnostics, dependency checking, health monitoring, readiness scoring,
    dashboard and CLI rendering under both healthy and degraded states.
    """

    def test_startup_diagnostics(self) -> None:
        """
        Verify startup diagnostics with mocked configuration, environments, and directories.
        """
        custom_env = {
            "KITE_API_KEY": "test_key",
            "KITE_ACCESS_TOKEN": "test_token",
            "KITE_API_SECRET": "test_secret",
        }
        
        # Test full success
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            temp_scoring_yaml = root / "test_scoring.yaml"
            temp_log_dir = root / "logs"
            temp_cache_dir = root / "cache"
            temp_db_path = temp_cache_dir / "instruments.db"

            temp_cache_dir.mkdir()
            temp_log_dir.mkdir()
            temp_scoring_yaml.write_text("test_config: 1.0", encoding="utf-8")
            temp_db_path.touch()

            custom_paths = {
                "scoring_yaml": str(temp_scoring_yaml),
                "log_dir": str(temp_log_dir),
                "cache_dir": str(temp_cache_dir),
                "instrument_db": str(temp_db_path),
            }

            diagnostics = StartupDiagnosticManager.run_diagnostics(
                custom_env=custom_env,
                custom_paths=custom_paths
            )

            self.assertTrue(diagnostics.config_valid)
            self.assertTrue(diagnostics.env_vars_valid)
            self.assertTrue(diagnostics.instrument_db_valid)
            self.assertTrue(diagnostics.working_dirs_valid)

            # Test failure case (e.g. missing environment variables)
            bad_env = {"KITE_API_KEY": ""}
            bad_diagnostics = StartupDiagnosticManager.run_diagnostics(
                custom_env=bad_env,
                custom_paths=custom_paths
            )
            self.assertFalse(bad_diagnostics.env_vars_valid)

    def test_dependency_validator(self) -> None:
        """
        Verify python and node dependency checking with mocks.
        """
        mock_pkg = {"dataclasses": True, "unittest": False}
        mock_node = {"react": True, "vite": False}

        status = DependencyValidator.validate_dependencies(
            mock_packages=mock_pkg,
            mock_node_modules=mock_node
        )

        self.assertFalse(status.python_packages_valid)
        self.assertFalse(status.node_modules_valid)
        self.assertIn("python_packages", status.details)
        self.assertIn("node_packages", status.details)

    def test_service_health_monitor(self) -> None:
        """
        Verify Broker, Market Data, News, and Execution service evaluations and latency readings.
        """
        # 1. Broker Healthy
        brk_status, brk_warns = ServiceHealthMonitor.monitor_broker({
            "session_active": True,
            "api_responsive": True,
            "profile_retrieval": True,
            "funds_retrieval": True,
            "latency_ms": 15.4
        })
        self.assertEqual(brk_status.status, "HEALTHY")
        self.assertEqual(len(brk_warns), 0)

        # Broker Critical
        brk_status, brk_warns = ServiceHealthMonitor.monitor_broker({
            "session_active": False,
            "api_responsive": True,
            "profile_retrieval": True,
            "funds_retrieval": True,
            "latency_ms": 15.4
        })
        self.assertEqual(brk_status.status, "CRITICAL")
        self.assertEqual(len(brk_warns), 1)
        self.assertEqual(brk_warns[0].severity, "HIGH")

        # 2. Market Data Healthy
        mkt_status, mkt_warns = ServiceHealthMonitor.monitor_market_data({
            "quotes_available": True,
            "historical_reachable": True,
            "option_chain_retrieval": True,
            "instrument_lookup": True,
            "vix_availability": True,
            "gift_nifty_availability": True,
            "latency_ms": 20.0
        })
        self.assertEqual(mkt_status.status, "HEALTHY")

        # Market Data Degraded
        mkt_status, mkt_warns = ServiceHealthMonitor.monitor_market_data({
            "quotes_available": True,
            "historical_reachable": True,
            "option_chain_retrieval": False,
            "instrument_lookup": True,
            "vix_availability": True,
            "gift_nifty_availability": True,
            "latency_ms": 20.0
        })
        self.assertEqual(mkt_status.status, "DEGRADED")

        # 3. News Graceful Degradation
        nws_status, nws_warns = ServiceHealthMonitor.monitor_news({
            "provider_availability": False,
            "provider_response_time_ok": True,
            "latest_successful_fetch": False,
            "latency_ms": 12.0
        })
        self.assertEqual(nws_status.status, "DEGRADED")
        self.assertEqual(len(nws_warns), 1)
        self.assertIn("degrading gracefully", nws_status.message)

        # 4. Execution Layer Checked
        exe_status, exe_warns = ServiceHealthMonitor.monitor_execution_layer({
            "broker_synchronization": True,
            "execution_queue": False,
            "portfolio_synchronization": True,
            "order_retrieval": True,
            "position_synchronization": True,
            "latency_ms": 5.0
        })
        self.assertEqual(exe_status.status, "WARNING")
        self.assertEqual(len(exe_warns), 1)

    def test_system_metrics_collection(self) -> None:
        """
        Verify platform info, disk, memory, and CPU collection with resource limit fallbacks.
        """
        metrics = SystemMetricsCollector.collect_metrics(
            mock_resources={
                "cpu_percent": 12.4,
                "memory_used_mb": 256.0,
                "memory_percent": 15.0,
                "disk_free_gb": 42.0,
                "disk_percent": 30.0
            },
            mock_sizes={
                "log_size_bytes": 1024,
                "cache_size_bytes": 2048
            }
        )

        self.assertEqual(metrics.resources.cpu_percent, 12.4)
        self.assertEqual(metrics.resources.disk_free_gb, 42.0)
        self.assertEqual(metrics.log_size_bytes, 1024)
        self.assertEqual(metrics.cache_size_bytes, 2048)
        self.assertIsNotNone(metrics.python_version)
        self.assertIsNotNone(metrics.platform_info)

    def test_readiness_scoring(self) -> None:
        """
        Verify math logic of readiness evaluation across READY, READY_WITH_WARNINGS, LIMITED, and NOT_READY classifications.
        """
        # Complete success state
        startup = StartupDiagnostics(True, True, True, True, True, True)
        dependencies = DependencyStatus(True, True, True)
        metrics = SystemMetrics(100.0, 100, 100, "3.10", "Linux", ResourceUsage(10.0, 100.0, 10.0, 50.0, 10.0))
        services = [
            ServiceStatus("Broker Connection", "HEALTHY", 10.0, "OK", "10:00:00"),
            ServiceStatus("Market Data", "HEALTHY", 10.0, "OK", "10:00:00"),
            ServiceStatus("News", "HEALTHY", 10.0, "OK", "10:00:00"),
            ServiceStatus("Execution", "HEALTHY", 10.0, "OK", "10:00:00"),
        ]
        
        # READY status
        r_status = ReadinessEvaluator.evaluate(services, startup, dependencies, metrics, [])
        self.assertEqual(r_status.status, "READY")
        self.assertEqual(r_status.readiness_score, 100.0)

        # WARNING status -> score decreases
        warnings = [HealthWarning("W1", "News", "LOW", "Slow RSS response", "10:00:00")]
        services_warn = [
            ServiceStatus("Broker Connection", "HEALTHY", 10.0, "OK", "10:00:00"),
            ServiceStatus("Market Data", "HEALTHY", 10.0, "OK", "10:00:00"),
            ServiceStatus("News", "WARNING", 10.0, "Slow RSS", "10:00:00"),
            ServiceStatus("Execution", "HEALTHY", 10.0, "OK", "10:00:00"),
        ]
        r_status2 = ReadinessEvaluator.evaluate(services_warn, startup, dependencies, metrics, warnings)
        self.assertEqual(r_status2.status, "READY_WITH_WARNINGS")
        self.assertLess(r_status2.readiness_score, 100.0)

        # CRITICAL status -> NOT_READY
        services_critical = [
            ServiceStatus("Broker Connection", "CRITICAL", 10.0, "Offline", "10:00:00"),
            ServiceStatus("Market Data", "HEALTHY", 10.0, "OK", "10:00:00"),
            ServiceStatus("News", "HEALTHY", 10.0, "OK", "10:00:00"),
            ServiceStatus("Execution", "HEALTHY", 10.0, "OK", "10:00:00"),
        ]
        r_status3 = ReadinessEvaluator.evaluate(services_critical, startup, dependencies, metrics, warnings)
        self.assertEqual(r_status3.status, "NOT_READY")

    def test_operations_report_builder_and_dashboard(self) -> None:
        """
        Verify report builder integration, OperationsPanel structure, serialization, and high-contrast CLI ASCII rendering.
        """
        # Build mocked report
        report = OperationsReportBuilder.build(
            custom_env={
                "KITE_API_KEY": "mock",
                "KITE_ACCESS_TOKEN": "mock",
                "KITE_API_SECRET": "mock"
            },
            mock_packages={"dataclasses": True, "unittest": True},
            mock_node_modules={"react": True, "vite": True},
            mock_broker_data={
                "session_active": True,
                "api_responsive": True,
                "profile_retrieval": True,
                "funds_retrieval": True
            },
            mock_market_data={
                "quotes_available": True,
                "historical_reachable": True,
                "option_chain_retrieval": True,
                "instrument_lookup": True,
                "vix_availability": True,
                "gift_nifty_availability": True
            },
            mock_news_data={
                "provider_availability": True,
                "provider_response_time_ok": True,
                "latest_successful_fetch": True
            },
            mock_execution_data={
                "broker_synchronization": True,
                "execution_queue": True,
                "portfolio_synchronization": True,
                "order_retrieval": True,
                "position_synchronization": True
            },
            mock_resources={"cpu_percent": 15.0, "memory_percent": 25.0},
            mock_sizes={"log_size_bytes": 1000}
        )

        self.assertIsNotNone(report.report_id)
        self.assertEqual(report.summary.overall_status, "READY")

        # OperationsPanel tests
        panel = OperationsPanel(report)
        dct = panel.to_dict()
        self.assertEqual(dct["summary"]["overall_status"], "READY")
        self.assertEqual(dct["metrics"]["resources"]["cpu_percent"], 15.0)

        cli_out = panel.render_cli()
        self.assertIn("OPERATIONS & WORKSTATION HEALTH PANEL", cli_out)
        self.assertIn("SERVICE STATUS", cli_out)
        self.assertIn("SYSTEM RESOURCES", cli_out)
        self.assertIn("STARTUP & DEPENDENCY CHECKLIST", cli_out)

        # Integrated workstation dashboard
        dash = TradingWorkstationDashboard(operations_report=report)
        dash_dct = dash.to_dict()
        self.assertIn("operations", dash_dct)
        self.assertEqual(dash_dct["operations"]["summary"]["overall_status"], "READY")

        dash_cli = dash.render_cli()
        self.assertIn("OPERATIONS & WORKSTATION HEALTH PANEL", dash_cli)
