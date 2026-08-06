from __future__ import annotations

import time
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any, List, Optional

from src.models.configuration_report import (
    ConfigurationReport,
    ConfigurationSummary,
    WorkspacePreferences,
    ConfigurationProfile,
    ConfigurationItem,
    ConfigurationWarning,
    ConfigurationMigration,
    ConfigurationStatistics
)
from src.configuration_engine.loader import ConfigurationLoader, DEFAULT_CONFIGS
from src.configuration_engine.validator import ConfigurationValidator
from src.configuration_engine.workspace import WorkspaceManager
from src.configuration_engine.profiles import ProfileManager
from src.configuration_engine.migration import MigrationManager


class ConfigurationReportBuilder:
    """
    Ties together all stateless configuration and workspace preferences subsystems
    to construct the final immutable ConfigurationReport.
    """

    @staticmethod
    def build(
        profile_name: Optional[str] = None,
        custom_prefs: Optional[Dict[str, Any]] = None,
        mock_files: Optional[Dict[str, str]] = None,
        custom_root: Optional[str] = None
    ) -> ConfigurationReport:
        """
        Gathers workstation settings, evaluates schema rules, tracks warnings,
        and generates a ConfigurationReport.
        """
        report_id = f"CONF_REP_{uuid4().hex[:8].upper()}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Resolve Profile
        active_profile = ProfileManager.get_profile(profile_name)

        # 2. Load configurations from files / defaults / mocks
        categories = [
            "trading", "risk", "scoring", "news", "broker",
            "dashboard", "paper_trading", "analytics", "operations"
        ]
        
        loaded_configs: Dict[str, Dict[str, Any]] = {}
        loaded_versions: Dict[str, str] = {}
        items: List[ConfigurationItem] = []
        warnings: List[ConfigurationWarning] = []

        # Description helper for config parameters
        descriptions: Dict[str, str] = {
            "version": "Schema version of this configuration block.",
            "default_instrument": "Fallback instrument to analyze if none is provided.",
            "allowed_segments": "Segments enabled for live order execution.",
            "trading_hours": "Core daily active exchange execution hours.",
            "max_risk_score": "Hard ceiling on calculated trade candidacy risk score.",
            "max_capital_allocation": "Absolute capital allocation limit per candidate trade.",
            "max_drawdown_limit": "Max acceptable portfolio drawdown threshold percentage.",
            "allowed_strategies": "Strategy modes permitted to write signals.",
            "overall_weights": "Core scoring weight distribution across metrics.",
            "news_sources": "External news providers verified for news parsing.",
            "sentiment_threshold": "Minimum news sentiment confidence for trend bias shift.",
            "broker_name": "Active integrated broker gateway.",
            "api_version": "Current broker API release version.",
            "refresh_interval_seconds": "Dashboard UI query poll rate.",
            "default_theme": "Initial workstation visual representation style.",
            "initial_margin": "Mock account paper trading start capital.",
            "slippage_percent": "Simulated slippage percentage per transaction.",
            "metrics_window": "P&L tracking lookback days for analytics.",
            "performance_benchmark": "Market benchmark tracking index.",
            "log_level": "Severity threshold for logging events.",
            "backup_frequency": "Auto configuration backup interval."
        }

        for cat in categories:
            # Load config data
            data = ConfigurationLoader.load_config_file(cat, custom_root=custom_root, mock_files=mock_files)
            
            # Blend with active profile settings if any exist
            profile_override = active_profile.settings.get(cat, {})
            blended_data = {**data, **profile_override}
            loaded_configs[cat] = blended_data

            # Save version for migration checks
            loaded_versions[cat] = blended_data.get("version", "1.0.0")

            # Validate config
            cat_warnings = ConfigurationValidator.validate_config(cat, blended_data)
            warnings.extend(cat_warnings)

            # Generate individual ConfigurationItems
            for k, v in blended_data.items():
                # Check if this specific item has a high-severity warning
                is_valid = not any(w.category == cat.upper() and w.invalid_value == v and w.severity == "HIGH" for w in cat_warnings)
                desc = descriptions.get(k, f"Configuration setting for {cat} layer.")
                items.append(
                    ConfigurationItem(
                        key=k,
                        value=v,
                        category=cat.upper(),
                        description=desc,
                        is_valid=is_valid
                    )
                )

        # 3. Parse Workspace Preferences
        preferences = WorkspaceManager.parse_preferences(
            custom_prefs=custom_prefs,
            profile_settings=active_profile.settings
        )

        # 4. Evaluate Migration
        migration = MigrationManager.evaluate_migration(loaded_versions, target_version="1.0.0")

        # 5. Compute Statistics
        total_keys = len(items)
        invalid_keys = sum(1 for item in items if not item.is_valid)
        valid_keys = total_keys - invalid_keys
        warnings_count = len(warnings)

        statistics = ConfigurationStatistics(
            total_keys=total_keys,
            valid_keys=valid_keys,
            invalid_keys=invalid_keys,
            warnings_count=warnings_count
        )

        # 6. Define status based on warning severity
        critical_blockers = sum(1 for w in warnings if w.severity == "HIGH")
        if critical_blockers > 0:
            overall_status = "INVALID"
        elif warnings_count > 0:
            overall_status = "VALID_WITH_WARNINGS"
        else:
            overall_status = "VALID"

        summary = ConfigurationSummary(
            timestamp=timestamp,
            active_profile_name=active_profile.name,
            schema_version="1.0.0",
            status=overall_status
        )

        return ConfigurationReport(
            report_id=report_id,
            timestamp=timestamp,
            summary=summary,
            preferences=preferences,
            active_profile=active_profile,
            items=items,
            warnings=warnings,
            migration=migration,
            statistics=statistics
        )
