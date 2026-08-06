from __future__ import annotations

from typing import Dict, Any, Optional, List
from src.models.configuration_report import WorkspacePreferences


class WorkspaceManager:
    """
    Manages and parses user workstation/dashboard preferences.
    """

    @staticmethod
    def parse_preferences(
        custom_prefs: Optional[Dict[str, Any]] = None,
        profile_settings: Optional[Dict[str, Any]] = None
    ) -> WorkspacePreferences:
        """
        Parses workspace preferences from custom settings or active profile fallback.
        """
        # Default fallback values
        refresh_interval = 10
        cli_theme = "HIGH_CONTRAST"
        react_theme = "DARK"
        visible_panels = ["SUMMARY", "MARKET", "TRADE", "RISK", "OPERATIONS", "CONFIGURATION"]
        default_screen = "SUMMARY"
        logging_level = "INFO"
        report_export_format = "JSON"

        # 1. Fallback to Profile Settings if provided
        if profile_settings and "workspace_preferences" in profile_settings:
            p_prefs = profile_settings["workspace_preferences"]
            refresh_interval = p_prefs.get("refresh_interval_seconds", refresh_interval)
            cli_theme = p_prefs.get("cli_theme", cli_theme)
            react_theme = p_prefs.get("react_theme", react_theme)
            visible_panels = p_prefs.get("visible_panels", visible_panels)
            default_screen = p_prefs.get("default_screen", default_screen)
            logging_level = p_prefs.get("logging_level", logging_level)
            report_export_format = p_prefs.get("report_export_format", report_export_format)

        # 2. Override with custom preference values if explicitly provided
        if custom_prefs:
            refresh_interval = custom_prefs.get("refresh_interval_seconds", refresh_interval)
            cli_theme = custom_prefs.get("cli_theme", cli_theme)
            react_theme = custom_prefs.get("react_theme", react_theme)
            visible_panels = custom_prefs.get("visible_panels", visible_panels)
            default_screen = custom_prefs.get("default_screen", default_screen)
            logging_level = custom_prefs.get("logging_level", logging_level)
            report_export_format = custom_prefs.get("report_export_format", report_export_format)

        return WorkspacePreferences(
            refresh_interval_seconds=int(refresh_interval),
            cli_theme=str(cli_theme),
            react_theme=str(react_theme),
            visible_panels=list(visible_panels),
            default_screen=str(default_screen),
            logging_level=str(logging_level),
            report_export_format=str(report_export_format)
        )
