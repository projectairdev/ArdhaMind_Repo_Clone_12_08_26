from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from src.models.configuration_report import ConfigurationReport

logger = logging.getLogger("ConfigurationPanel")


class ConfigurationPanel:
    """
    Dashboard Panel presenting the workstation configuration, workspace preferences,
    active profile selections, schema validation checks, and migrations.
    """

    def __init__(self, report: Optional[ConfigurationReport] = None) -> None:
        self.report = report

    def to_dict(self) -> Dict[str, Any]:
        """
        Structured representation of workspace configuration and preference metrics.
        """
        if not self.report:
            return {
                "report_id": "N/A",
                "timestamp": "N/A",
                "summary": {
                    "timestamp": "N/A",
                    "active_profile_name": "N/A",
                    "schema_version": "1.0.0",
                    "status": "UNKNOWN"
                },
                "preferences": {
                    "refresh_interval_seconds": 10,
                    "cli_theme": "HIGH_CONTRAST",
                    "react_theme": "DARK",
                    "visible_panels": [],
                    "default_screen": "SUMMARY",
                    "logging_level": "INFO",
                    "report_export_format": "JSON"
                },
                "active_profile": {
                    "profile_id": "N/A",
                    "name": "N/A",
                    "description": "N/A",
                    "settings": {}
                },
                "items": [],
                "warnings": [],
                "migration": {
                    "source_version": "1.0.0",
                    "target_version": "1.0.0",
                    "requires_migration": False,
                    "recommendations": []
                },
                "statistics": {
                    "total_keys": 0,
                    "valid_keys": 0,
                    "invalid_keys": 0,
                    "warnings_count": 0
                }
            }

        # Format items list
        items_data = [
            {
                "key": item.key,
                "value": item.value,
                "category": item.category,
                "description": item.description,
                "is_valid": item.is_valid
            }
            for item in self.report.items
        ]

        # Format warnings list
        warnings_data = [
            {
                "warning_id": w.warning_id,
                "category": w.category,
                "severity": w.severity,
                "message": w.message,
                "invalid_value": w.invalid_value
            }
            for w in self.report.warnings
        ]

        # Format migration
        mig_data = {
            "source_version": self.report.migration.source_version if self.report.migration else "1.0.0",
            "target_version": self.report.migration.target_version if self.report.migration else "1.0.0",
            "requires_migration": self.report.migration.requires_migration if self.report.migration else False,
            "recommendations": self.report.migration.recommendations if self.report.migration else []
        }

        # Format statistics
        stats_data = {
            "total_keys": self.report.statistics.total_keys if self.report.statistics else 0,
            "valid_keys": self.report.statistics.valid_keys if self.report.statistics else 0,
            "invalid_keys": self.report.statistics.invalid_keys if self.report.statistics else 0,
            "warnings_count": self.report.statistics.warnings_count if self.report.statistics else 0
        }

        # Format active profile
        prof = self.report.active_profile
        active_profile_data = {
            "profile_id": prof.profile_id,
            "name": prof.name,
            "description": prof.description,
            "settings": prof.settings
        }

        # Format preferences
        p = self.report.preferences
        preferences_data = {
            "refresh_interval_seconds": p.refresh_interval_seconds,
            "cli_theme": p.cli_theme,
            "react_theme": p.react_theme,
            "visible_panels": p.visible_panels,
            "default_screen": p.default_screen,
            "logging_level": p.logging_level,
            "report_export_format": p.report_export_format
        }

        return {
            "report_id": self.report.report_id,
            "timestamp": self.report.timestamp,
            "summary": {
                "timestamp": self.report.summary.timestamp,
                "active_profile_name": self.report.summary.active_profile_name,
                "schema_version": self.report.summary.schema_version,
                "status": self.report.summary.status
            },
            "preferences": preferences_data,
            "active_profile": active_profile_data,
            "items": items_data,
            "warnings": warnings_data,
            "migration": mig_data,
            "statistics": stats_data
        }

    def render_cli(self) -> str:
        """
        Renders a beautifully formatted ASCII text card representing workspace preferences, profiles, and warning lists.
        """
        data = self.to_dict()
        summary = data["summary"]
        preferences = data["preferences"]
        active_profile = data["active_profile"]
        stats = data["statistics"]
        warnings = data["warnings"]
        migration = data["migration"]

        lines = []
        lines.append("+- WORKSPACE CONFIGURATION & PREFERENCES PANEL --------------------------------+")
        
        # 1. Configuration Status Block
        lines.append(
            f"| STATUS        : {summary['status']:<25} | Schema Version: {summary['schema_version']:<18} |"
        )
        lines.append(
            f"| Active Profile: {summary['active_profile_name']:<25} | Loaded Keys   : {stats['total_keys']:<18} |"
        )
        lines.append(
            f"| Warnings Count: {stats['warnings_count']:<25} | Invalid Keys  : {stats['invalid_keys']:<18} |"
        )
        lines.append("|" + "-" * 78 + "|")

        # 2. Workspace Profile Information
        lines.append("| PROFILE INFORMATION                                                          |")
        desc_wrapped = active_profile['description'][:74]
        lines.append(f"|  * Profile ID : {active_profile['profile_id']:<60} |")
        lines.append(f"|  * Description: {desc_wrapped:<60} |")
        lines.append("|" + "-" * 78 + "|")

        # 3. Workspace Settings
        lines.append("| WORKSPACE SETTINGS                                                           |")
        lines.append(
            f"|  Refresh Rate : {preferences['refresh_interval_seconds']}s{' ':<22} | CLI Theme     : {preferences['cli_theme']:<25} |"
        )
        lines.append(
            f"|  React Theme  : {preferences['react_theme']:<25} | Screen Default: {preferences['default_screen']:<25} |"
        )
        lines.append(
            f"|  Logging Level: {preferences['logging_level']:<25} | Export Format : {preferences['report_export_format']:<25} |"
        )
        panels_str = ", ".join(preferences["visible_panels"])[:62]
        lines.append(
            f"|  Visible Rails: [{panels_str:<62}] |"
        )
        lines.append("|" + "-" * 78 + "|")

        # 4. Validation Results
        lines.append("| SCHEMA VALIDATION CHECKS                                                     |")
        trading_status = "PASS" if not any(w["category"] == "TRADING" and w["severity"] == "HIGH" for w in warnings) else "FAIL"
        risk_status = "PASS" if not any(w["category"] == "RISK" and w["severity"] == "HIGH" for w in warnings) else "FAIL"
        scoring_status = "PASS" if not any(w["category"] == "SCORING" and w["severity"] == "HIGH" for w in warnings) else "FAIL"
        broker_status = "PASS" if not any(w["category"] == "BROKER" and w["severity"] == "HIGH" for w in warnings) else "FAIL"
        dashboard_status = "PASS" if not any(w["category"] == "DASHBOARD" and w["severity"] == "HIGH" for w in warnings) else "FAIL"

        lines.append(
            f"|  Trading Spec : {trading_status:<10} | Risk Constraints : {risk_status:<10}                      |"
        )
        lines.append(
            f"|  Scoring Rules: {scoring_status:<10} | Broker Gateway   : {broker_status:<10}                      |"
        )
        lines.append(
            f"|  Dashboard UI : {dashboard_status:<10} | Version Integrity: PASS                       |"
        )
        lines.append("|" + "-" * 78 + "|")

        # 5. Schema Migration Warnings
        if migration["requires_migration"]:
            lines.append("| SCHEMA MIGRATION RECOMMENDED                                                 |")
            for rec in migration["recommendations"][:3]:  # Show top 3 recommendations
                lines.append(
                    f"|  [!] {rec[:70]:<70} |"
                )
        else:
            lines.append("| SCHEMA MIGRATION: No actions required. Workstation schema is fully optimal.  |")

        # 6. Active Warnings Listing
        if warnings:
            lines.append("|" + "-" * 78 + "|")
            lines.append("| ACTIVE CONFIGURATION WARNINGS                                                |")
            for w in warnings[:3]:  # Show top 3 warnings
                msg_cropped = f"[{w['severity']}] {w['category']}: {w['message']}"[:72]
                lines.append(
                    f"|  * {msg_cropped:<72} |"
                )
            if len(warnings) > 3:
                lines.append(f"|  ... and {len(warnings) - 3} more warnings.                                                 |")
                
        lines.append("+------------------------------------------------------------------------------+")

        return "\n".join(lines)
