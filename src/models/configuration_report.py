from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass(frozen=True)
class ConfigurationItem:
    key: str
    value: Any
    category: str               # "RISK", "SCORING", "NEWS", "BROKER", "PAPER_TRADING", etc.
    description: str
    is_valid: bool


@dataclass(frozen=True)
class WorkspacePreferences:
    refresh_interval_seconds: int
    cli_theme: str              # "HIGH_CONTRAST", "DARK", "LIGHT"
    react_theme: str            # "DARK", "LIGHT"
    visible_panels: List[str]
    default_screen: str
    logging_level: str          # "INFO", "DEBUG", "WARNING"
    report_export_format: str   # "JSON", "YAML"


@dataclass(frozen=True)
class ConfigurationWarning:
    warning_id: str
    category: str
    severity: str               # "LOW", "MEDIUM", "HIGH"
    message: str
    invalid_value: Optional[Any] = None


@dataclass(frozen=True)
class ConfigurationMigration:
    source_version: str
    target_version: str
    requires_migration: bool
    recommendations: List[str]


@dataclass(frozen=True)
class ConfigurationProfile:
    profile_id: str
    name: str                   # "DEFAULT", "PAPER_TRADING", "LIVE_TRADING", "CONSERVATIVE", "AGGRESSIVE", etc.
    description: str
    settings: Dict[str, Any]


@dataclass(frozen=True)
class ConfigurationStatistics:
    total_keys: int
    valid_keys: int
    invalid_keys: int
    warnings_count: int


@dataclass(frozen=True)
class ConfigurationSummary:
    timestamp: str
    active_profile_name: str
    schema_version: str
    status: str                 # "VALID", "VALID_WITH_WARNINGS", "INVALID"


@dataclass(frozen=True)
class ConfigurationReport:
    report_id: str
    timestamp: str
    summary: ConfigurationSummary
    preferences: WorkspacePreferences
    active_profile: ConfigurationProfile
    items: List[ConfigurationItem] = field(default_factory=list)
    warnings: List[ConfigurationWarning] = field(default_factory=list)
    migration: Optional[ConfigurationMigration] = None
    statistics: Optional[ConfigurationStatistics] = None
