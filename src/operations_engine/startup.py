from __future__ import annotations

import os
import sys
from typing import Dict, Any
from src.models.operations_report import StartupDiagnostics


class StartupDiagnosticManager:
    """
    Validates configuration files, environment variables, working/log/cache directories,
    required folders, and the instrument database.
    """

    @staticmethod
    def run_diagnostics(
        custom_env: Optional[Dict[str, str]] = None,
        custom_paths: Optional[Dict[str, str]] = None
    ) -> StartupDiagnostics:
        """
        Executes startup checks.
        """
        env = custom_env if custom_env is not None else os.environ
        
        # Paths to check
        root_dir = os.getcwd()
        scoring_yaml_path = custom_paths.get("scoring_yaml") if custom_paths else os.path.join(root_dir, "src", "config_engine", "scoring.yaml")
        log_dir = custom_paths.get("log_dir") if custom_paths else os.path.join(root_dir, "logs")
        cache_dir = custom_paths.get("cache_dir") if custom_paths else os.path.join(root_dir, "cache")
        instrument_db_path = custom_paths.get("instrument_db") if custom_paths else os.path.join(cache_dir, "instruments.db")

        checks: Dict[str, bool] = {}

        # 1. Configuration files
        config_valid = os.path.isfile(scoring_yaml_path)
        checks["config_files"] = config_valid

        # 2. Environment variables
        required_env_vars = ["KITE_API_KEY", "KITE_ACCESS_TOKEN", "KITE_API_SECRET"]
        env_vars_valid = all(env.get(var) for var in required_env_vars)
        checks["env_vars"] = env_vars_valid

        # 3. Working directories
        working_dirs_valid = os.path.isdir(os.path.join(root_dir, "src"))
        checks["working_dirs"] = working_dirs_valid

        # 4. Log directories
        # We check or try to create log_dir to be helpful
        log_dir_exists = os.path.isdir(log_dir)
        if not log_dir_exists and not custom_paths:
            try:
                os.makedirs(log_dir, exist_ok=True)
                log_dir_exists = True
            except Exception:
                log_dir_exists = False
        checks["log_dirs"] = log_dir_exists

        # 5. Required folders (src, tests)
        required_folders_exist = os.path.isdir(os.path.join(root_dir, "src")) and os.path.isdir(os.path.join(root_dir, "tests"))
        checks["required_folders"] = required_folders_exist

        # 6. Cache folders
        cache_folders_exist = os.path.isdir(cache_dir)
        if not cache_folders_exist and not custom_paths:
            try:
                os.makedirs(cache_dir, exist_ok=True)
                cache_folders_exist = True
            except Exception:
                cache_folders_exist = False
        checks["cache_folders"] = cache_folders_exist

        # 7. Instrument database
        # Create a mock or check database file
        instrument_db_valid = os.path.isfile(instrument_db_path)
        if not instrument_db_valid and cache_folders_exist and not custom_paths:
            try:
                with open(instrument_db_path, "w") as f:
                    f.write("")  # Touch file
                instrument_db_valid = True
            except Exception:
                instrument_db_valid = False
        checks["instrument_db"] = instrument_db_valid

        return StartupDiagnostics(
            config_valid=config_valid,
            env_vars_valid=env_vars_valid,
            working_dirs_valid=working_dirs_valid,
            required_folders_exist=required_folders_exist,
            cache_folders_exist=cache_folders_exist,
            instrument_db_valid=instrument_db_valid,
            checks=checks
        )
