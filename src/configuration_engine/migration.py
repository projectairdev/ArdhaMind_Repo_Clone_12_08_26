from __future__ import annotations

from typing import List, Dict, Any, Optional
from src.models.configuration_report import ConfigurationMigration


class MigrationManager:
    """
    Stateless schema migration evaluation layer.
    """

    @staticmethod
    def evaluate_migration(
        loaded_versions: Dict[str, str],
        target_version: str = "1.0.0"
    ) -> ConfigurationMigration:
        """
        Analyzes loaded configuration versions and produces migration recommendations.
        """
        requires_migration = False
        recommendations: List[str] = []
        source_versions: List[str] = []

        for category, ver in loaded_versions.items():
            if ver != target_version:
                requires_migration = True
                recommendations.append(
                    f"[{category.upper()}] Config is on older version v{ver}. Migrate keys and set version to '{target_version}'."
                )
                if ver not in source_versions:
                    source_versions.append(ver)

        # Standard recommendations based on common old versions
        if requires_migration:
            recommendations.append("Update all file headers to include 'version: 1.0.0'.")
            recommendations.append("Consolidate legacy/deprecated keys into standard categories.")
            recommendations.append("Add missing dashboard 'visible_panels' keys to match Sprint 25 specifications.")
        else:
            recommendations.append("All configurations are up to date. No migration required.")

        source_ver_str = ", ".join(source_versions) if source_versions else target_version

        return ConfigurationMigration(
            source_version=source_ver_str,
            target_version=target_version,
            requires_migration=requires_migration,
            recommendations=recommendations
        )
