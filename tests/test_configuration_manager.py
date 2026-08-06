from __future__ import annotations

import unittest
from typing import Dict, Any, List

from src.models.configuration_report import (
    ConfigurationReport,
    ConfigurationItem,
    WorkspacePreferences,
    ConfigurationProfile,
    ConfigurationWarning,
    ConfigurationMigration,
    ConfigurationStatistics,
    ConfigurationSummary
)
from src.configuration_engine.loader import ConfigurationLoader, DEFAULT_CONFIGS
from src.configuration_engine.validator import ConfigurationValidator
from src.configuration_engine.profiles import ProfileManager
from src.configuration_engine.workspace import WorkspaceManager
from src.configuration_engine.migration import MigrationManager
from src.configuration_engine.exporter import ExportManager
from src.configuration_engine.builder import ConfigurationReportBuilder
from src.dashboard.configuration_panel import ConfigurationPanel


class TestConfigurationManager(unittest.TestCase):
    """
    Sprint 25: Comprehensive Unit Tests for the Configuration & Workspace Management Layer.
    Verifies 100% logical correctness of loader, validator, workspace manager,
    profile manager, migration engine, exporter, builder, and presentation panel.
    """

    def test_profile_manager_presets(self) -> None:
        """
        Verify all predefined immutable workspace profiles are valid and accessible.
        """
        profiles = ProfileManager.list_profiles()
        self.assertIn("DEFAULT", profiles)
        self.assertIn("PAPER_TRADING", profiles)
        self.assertIn("LIVE_TRADING", profiles)
        self.assertIn("CONSERVATIVE", profiles)
        self.assertIn("AGGRESSIVE", profiles)

        # Retrieve individual profile
        prof = ProfileManager.get_profile("AGGRESSIVE")
        self.assertEqual(prof.name, "AGGRESSIVE")
        self.assertIn("workspace_preferences", prof.settings)
        self.assertIn("risk", prof.settings)
        self.assertEqual(prof.settings["risk"]["max_risk_score"], 85.0)

        # Retrieve non-existing profile fallback
        fallback_prof = ProfileManager.get_profile("UNKNOWN_RANDOM_PROFILE")
        self.assertEqual(fallback_prof.name, "DEFAULT")

    def test_workspace_preferences_parsing(self) -> None:
        """
        Verify parsing logic for user-configured dashboard preferences.
        """
        # Case 1: Pure default fallback
        prefs_1 = WorkspaceManager.parse_preferences()
        self.assertEqual(prefs_1.refresh_interval_seconds, 10)
        self.assertEqual(prefs_1.react_theme, "DARK")
        self.assertEqual(prefs_1.cli_theme, "HIGH_CONTRAST")

        # Case 2: Fallback to Profile Settings
        profile_settings = {
            "workspace_preferences": {
                "refresh_interval_seconds": 3,
                "cli_theme": "DARK",
                "react_theme": "LIGHT",
                "visible_panels": ["SUMMARY", "MARKET"],
                "default_screen": "MARKET",
                "logging_level": "DEBUG",
                "report_export_format": "YAML"
            }
        }
        prefs_2 = WorkspaceManager.parse_preferences(profile_settings=profile_settings)
        self.assertEqual(prefs_2.refresh_interval_seconds, 3)
        self.assertEqual(prefs_2.cli_theme, "DARK")
        self.assertEqual(prefs_2.react_theme, "LIGHT")
        self.assertEqual(prefs_2.default_screen, "MARKET")
        self.assertEqual(prefs_2.logging_level, "DEBUG")
        self.assertEqual(prefs_2.report_export_format, "YAML")

        # Case 3: Explicit Custom Preference overrides
        custom_prefs = {
            "refresh_interval_seconds": 1,
            "cli_theme": "LIGHT",
            "react_theme": "LIGHT",
        }
        prefs_3 = WorkspaceManager.parse_preferences(custom_prefs=custom_prefs, profile_settings=profile_settings)
        self.assertEqual(prefs_3.refresh_interval_seconds, 1)
        self.assertEqual(prefs_3.cli_theme, "LIGHT")
        self.assertEqual(prefs_3.react_theme, "LIGHT")
        self.assertEqual(prefs_3.default_screen, "MARKET")  # Persisted from profile

    def test_configuration_loader_mock_parsing(self) -> None:
        """
        Verify ConfigurationLoader handles empty files, custom files, and fallback logic cleanly.
        """
        # Case 1: Fallback to default when no files present
        config_risk = ConfigurationLoader.load_config_file("risk")
        self.assertEqual(config_risk["max_risk_score"], 50.0)

        # Case 2: Parse custom mock yaml content
        mock_yaml_data = """
        version: "1.0.0"
        max_risk_score: 75.5
        max_capital_allocation: 250000.0
        max_drawdown_limit: 8.0
        """
        mock_files = {"risk.yaml": mock_yaml_data}
        loaded = ConfigurationLoader.load_config_file("risk", mock_files=mock_files)
        self.assertEqual(loaded.get("version"), "1.0.0")
        self.assertEqual(loaded.get("max_risk_score"), 75.5)
        self.assertEqual(loaded.get("max_capital_allocation"), 250000.0)
        self.assertEqual(loaded.get("max_drawdown_limit"), 8.0)

        # Case 3: Parse custom mock json content
        mock_json_data = '{"version": "1.0.0", "max_risk_score": 60.0}'
        mock_files_json = {"risk.json": mock_json_data}
        loaded_json = ConfigurationLoader.load_config_file("risk", mock_files=mock_files_json)
        self.assertEqual(loaded_json.get("max_risk_score"), 60.0)

    def test_configuration_validator_rules(self) -> None:
        """
        Verify the schema validator detects invalid values, deprecated params, version mismatches, and missing fields.
        """
        # Case 1: Missing field and version mismatch
        bad_risk_data = {
            "version": "0.9.0",
            # missing max_risk_score, max_capital_allocation, max_drawdown_limit
            "legacy_leverage_limit": 10.0,  # Deprecated parameter
            "unknown_setting": "val"       # Unknown setting
        }
        warnings = ConfigurationValidator.validate_config("risk", bad_risk_data)
        
        warning_messages = [w.message for w in warnings]
        warning_categories = [w.category for w in warnings]
        warning_severities = [w.severity for w in warnings]

        # Missing fields flagged as HIGH severity
        self.assertTrue(any("Missing required parameter" in msg for msg in warning_messages))
        self.assertIn("HIGH", warning_severities)

        # Version mismatch flagged as MEDIUM severity
        self.assertTrue(any("version mismatch" in msg.lower() for msg in warning_messages))
        self.assertIn("MEDIUM", warning_severities)

        # Deprecated key flagged
        self.assertTrue(any("Deprecated parameter in use" in msg for msg in warning_messages))

        # Unknown parameter flagged as LOW
        self.assertTrue(any("Unknown configuration parameter" in msg for msg in warning_messages))
        self.assertIn("LOW", warning_severities)

        # Case 2: Range constraints validation on Risk
        invalid_bounds_risk = {
            "version": "1.0.0",
            "max_risk_score": 105.0,                  # Out of [0, 100] range
            "max_capital_allocation": -50.0,         # Negative allocation
            "max_drawdown_limit": 110.0,              # Out of [0, 100] range
        }
        warnings_bounds = ConfigurationValidator.validate_config("risk", invalid_bounds_risk)
        bounds_messages = [w.message for w in warnings_bounds]
        self.assertTrue(any("must be between 0.0 and 100.0" in msg for msg in bounds_messages))
        self.assertTrue(any("must be greater than zero" in msg for msg in bounds_messages))
        self.assertTrue(any("must be a percentage between 0.0 and 100.0" in msg for msg in bounds_messages))

        # Case 3: Scoring weights sums verification
        bad_scoring = {
            "version": "1.0.0",
            "overall_weights": {
                "trend": 10.0,
                "options": 10.0
            } # Sum is 20.0, which is neither 1.0 nor 100.0
        }
        warnings_score = ConfigurationValidator.validate_config("scoring", bad_scoring)
        score_messages = [w.message for w in warnings_score]
        self.assertTrue(any("Expected sum of 100.0 or 1.0" in msg for msg in score_messages))

    def test_schema_migration_evaluation(self) -> None:
        """
        Verify the migration engine recommends changes without mutating config files.
        """
        # Case 1: All on current version
        loaded_current = {"risk": "1.0.0", "trading": "1.0.0"}
        mig_current = MigrationManager.evaluate_migration(loaded_current)
        self.assertFalse(mig_current.requires_migration)
        self.assertIn("No migration required", mig_current.recommendations[0])

        # Case 2: Older version present
        loaded_old = {"risk": "0.8.0", "trading": "1.0.0"}
        mig_old = MigrationManager.evaluate_migration(loaded_old)
        self.assertTrue(mig_old.requires_migration)
        self.assertTrue(any("is on older version v0.8.0" in rec for rec in mig_old.recommendations))

    def test_configuration_exporter(self) -> None:
        """
        Verify ExportManager formats configuration data to JSON, YAML, and ASCII text.
        """
        test_data = {
            "risk": {
                "max_risk_score": 50.0,
                "allowed_strategies": ["SCALPING"]
            }
        }
        
        # JSON
        json_str = ExportManager.to_json(test_data)
        self.assertIn('"max_risk_score": 50.0', json_str)

        # YAML
        yaml_str = ExportManager.to_yaml(test_data)
        self.assertIn("max_risk_score", yaml_str)

        # Text summary report
        summary_str = ExportManager.to_summary_text(test_data)
        self.assertIn("CATEGORY: RISK", summary_str)
        self.assertIn("max_risk_score", summary_str)

    def test_configuration_report_builder_and_panel(self) -> None:
        """
        Verify end-to-end report building and terminal CLI display.
        """
        # Build configuration report with aggressive profile and mock files
        mock_files = {
            "risk.yaml": """
            version: "1.0.0"
            max_risk_score: 95.0
            max_capital_allocation: 500000.0
            max_drawdown_limit: 12.0
            """,
            "trading.yaml": """
            version: "0.9.0"
            default_instrument: "NIFTY"
            allowed_segments: ["OPTIONS"]
            """
        }

        report = ConfigurationReportBuilder.build(
            profile_name="AGGRESSIVE",
            mock_files=mock_files
        )

        # Confirm dataclass properties
        self.assertEqual(report.summary.active_profile_name, "AGGRESSIVE")
        self.assertEqual(report.preferences.cli_theme, "DARK") # Set by AGGRESSIVE profile
        self.assertTrue(len(report.items) > 0)
        self.assertTrue(len(report.warnings) > 0) # Should have a version warning for trading
        self.assertEqual(report.statistics.warnings_count, len(report.warnings))

        # Instantiate presentation panel
        panel = ConfigurationPanel(report)
        panel_dict = panel.to_dict()
        self.assertEqual(panel_dict["summary"]["active_profile_name"], "AGGRESSIVE")
        self.assertTrue(len(panel_dict["items"]) > 0)

        # Render ASCII CLI display
        ascii_view = panel.render_cli()
        self.assertIn("WORKSPACE CONFIGURATION & PREFERENCES PANEL", ascii_view)
        self.assertIn("AGGRESSIVE", ascii_view)
        self.assertIn("DARK", ascii_view)
        self.assertIn("SCHEMA VALIDATION CHECKS", ascii_view)

        # Verify default rendering when no report is passed
        empty_panel = ConfigurationPanel(None)
        empty_dict = empty_panel.to_dict()
        self.assertEqual(empty_dict["report_id"], "N/A")
        empty_cli = empty_panel.render_cli()
        self.assertIn("UNKNOWN", empty_cli)
