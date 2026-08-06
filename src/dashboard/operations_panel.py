from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from src.models import OperationsReport

logger = logging.getLogger("OperationsPanel")


class OperationsPanel:
    """
    Dashboard Panel presenting the workstation health, resource statistics,
    dependencies, active operational warnings, and overall readiness.
    """

    def __init__(self, report: Optional[OperationsReport] = None) -> None:
        self.report = report

    def to_dict(self) -> Dict[str, Any]:
        """
        Structured representation of workstation operations and health metrics.
        """
        if not self.report:
            return {
                "report_id": "N/A",
                "timestamp": "N/A",
                "summary": {
                    "timestamp": "N/A",
                    "overall_status": "UNKNOWN",
                    "readiness_score": 0.0,
                    "uptime_str": "0s"
                },
                "readiness": {
                    "status": "UNKNOWN",
                    "readiness_score": 0.0,
                    "critical_blockers_count": 0,
                    "warnings_count": 0
                },
                "services": [],
                "startup": {
                    "config_valid": False,
                    "env_vars_valid": False,
                    "working_dirs_valid": False,
                    "required_folders_exist": False,
                    "cache_folders_exist": False,
                    "instrument_db_valid": False,
                    "checks": {}
                },
                "dependencies": {
                    "python_packages_valid": False,
                    "node_modules_valid": False,
                    "config_files_valid": False,
                    "details": {}
                },
                "metrics": {
                    "uptime_seconds": 0.0,
                    "log_size_bytes": 0,
                    "cache_size_bytes": 0,
                    "python_version": "N/A",
                    "platform_info": "N/A",
                    "resources": {
                        "cpu_percent": 0.0,
                        "memory_used_mb": 0.0,
                        "memory_percent": 0.0,
                        "disk_free_gb": 0.0,
                        "disk_percent": 0.0
                    }
                },
                "warnings": []
            }

        # Format services list
        services_data = [
            {
                "service_name": s.service_name,
                "status": s.status,
                "latency_ms": s.latency_ms,
                "message": s.message,
                "last_checked": s.last_checked
            }
            for s in self.report.services
        ]

        # Format warnings list
        warnings_data = [
            {
                "warning_id": w.warning_id,
                "source": w.source,
                "severity": w.severity,
                "message": w.message,
                "timestamp": w.timestamp
            }
            for w in self.report.warnings
        ]

        # Format resources data
        res = self.report.metrics.resources
        resources_data = {
            "cpu_percent": res.cpu_percent,
            "memory_used_mb": res.memory_used_mb,
            "memory_percent": res.memory_percent,
            "disk_free_gb": res.disk_free_gb,
            "disk_percent": res.disk_percent
        }

        # Format metrics data
        metrics_data = {
            "uptime_seconds": self.report.metrics.uptime_seconds,
            "log_size_bytes": self.report.metrics.log_size_bytes,
            "cache_size_bytes": self.report.metrics.cache_size_bytes,
            "python_version": self.report.metrics.python_version,
            "platform_info": self.report.metrics.platform_info,
            "resources": resources_data
        }

        return {
            "report_id": self.report.report_id,
            "timestamp": self.report.timestamp,
            "summary": {
                "timestamp": self.report.summary.timestamp,
                "overall_status": self.report.summary.overall_status,
                "readiness_score": self.report.summary.readiness_score,
                "uptime_str": self.report.summary.uptime_str
            },
            "readiness": {
                "status": self.report.readiness.status,
                "readiness_score": self.report.readiness.readiness_score,
                "critical_blockers_count": self.report.readiness.critical_blockers_count,
                "warnings_count": self.report.readiness.warnings_count
            },
            "services": services_data,
            "startup": {
                "config_valid": self.report.startup.config_valid,
                "env_vars_valid": self.report.startup.env_vars_valid,
                "working_dirs_valid": self.report.startup.working_dirs_valid,
                "required_folders_exist": self.report.startup.required_folders_exist,
                "cache_folders_exist": self.report.startup.cache_folders_exist,
                "instrument_db_valid": self.report.startup.instrument_db_valid,
                "checks": self.report.startup.checks
            },
            "dependencies": {
                "python_packages_valid": self.report.dependencies.python_packages_valid,
                "node_modules_valid": self.report.dependencies.node_modules_valid,
                "config_files_valid": self.report.dependencies.config_files_valid,
                "details": self.report.dependencies.details
            },
            "metrics": metrics_data,
            "warnings": warnings_data
        }

    def render_cli(self) -> str:
        """
        Renders a beautifully formatted ASCII text card representing Operations & Readiness.
        """
        data = self.to_dict()
        readiness = data["readiness"]
        metrics = data["metrics"]
        resources = metrics["resources"]
        services = data["services"]
        startup = data["startup"]
        dependencies = data["dependencies"]
        warnings = data["warnings"]

        lines = []
        lines.append("+- OPERATIONS & WORKSTATION HEALTH PANEL --------------------------------------+")
        
        # 1. Workstation Readiness Section
        lines.append(
            f"| STATUS        : {readiness['status']:<25} | Score      : {readiness['readiness_score']:.1f}%              |"
        )
        lines.append(
            f"| Blockers      : {readiness['critical_blockers_count']:<25} | Warnings   : {readiness['warnings_count']:<18} |"
        )
        lines.append(
            f"| Uptime        : {data['summary']['uptime_str']:<25} | Report ID  : {data['report_id']:<18} |"
        )
        lines.append("|" + "-" * 78 + "|")

        # 2. Service Status Section
        lines.append("| SERVICE STATUS                                                               |")
        for svc in services:
            # Format status cleanly with latency
            status_str = f"[{svc['status']}]"
            latency_str = f"{svc['latency_ms']:.1f}ms"
            lines.append(
                f"|  * {svc['service_name']:<24} {status_str:<10} Latency: {latency_str:<10} {svc['message'][:24]:<18} |"
            )
        lines.append("|" + "-" * 78 + "|")

        # 3. System Resources Section
        lines.append("| SYSTEM RESOURCES                                                             |")
        cpu_bar = "=" * int(resources["cpu_percent"] // 10) + " " * (10 - int(resources["cpu_percent"] // 10))
        mem_bar = "=" * int(resources["memory_percent"] // 10) + " " * (10 - int(resources["memory_percent"] // 10))
        
        lines.append(
            f"|  CPU Usage    : [{cpu_bar}] {resources['cpu_percent']:>5.1f}% | Platform   : {metrics['platform_info'][:31]:<31} |"
        )
        lines.append(
            f"|  Memory Usage : [{mem_bar}] {resources['memory_percent']:>5.1f}% | Python     : {metrics['python_version']:<31} |"
        )
        lines.append(
            f"|  Memory Used  : {resources['memory_used_mb']:>7.1f} MB            | Logs Size  : {metrics['log_size_bytes'] / (1024*1024):>6.2f} MB                    |"
        )
        lines.append(
            f"|  Disk Free    : {resources['disk_free_gb']:>7.1f} GB ({resources['disk_percent']:>4.1f}%)   | Cache Size : {metrics['cache_size_bytes'] / (1024*1024):>6.2f} MB                    |"
        )
        lines.append("|" + "-" * 78 + "|")

        # 4. Dependencies & Startup Checklist
        lines.append("| STARTUP & DEPENDENCY CHECKLIST                                               |")
        
        py_status = "PASS" if dependencies["python_packages_valid"] else "FAIL"
        node_status = "PASS" if dependencies["node_modules_valid"] else "FAIL"
        cfg_status = "PASS" if dependencies["config_files_valid"] else "FAIL"
        
        lines.append(
            f"|  Python Packages  : {py_status:<10} | Configuration files: {cfg_status:<10}                     |"
        )
        lines.append(
            f"|  Node React Mod   : {node_status:<10} | Instrument DB      : {'PASS' if startup['instrument_db_valid'] else 'FAIL':<10}                     |"
        )
        lines.append(
            f"|  Config Loaded    : {'PASS' if startup['config_valid'] else 'FAIL':<10} | Required Folders   : {'PASS' if startup['required_folders_exist'] else 'FAIL':<10}                     |"
        )
        lines.append("|" + "-" * 78 + "|")

        # 5. Active Warnings
        if warnings:
            lines.append("| ACTIVE WARNINGS                                                              |")
            for w in warnings[:4]:  # Show top 4 warnings
                lines.append(
                    f"|  [{w['severity']}] {w['source']}: {w['message'][:54]:<54} |"
                )
            if len(warnings) > 4:
                lines.append(f"|  ... and {len(warnings) - 4} more warnings.                                                 |")
        else:
            lines.append("| ACTIVE WARNINGS: None (System operates within nominal parameters)            |")
        lines.append("+------------------------------------------------------------------------------+")

        return "\n".join(lines)
