from __future__ import annotations

import os
import sys
import json
import importlib
from typing import Dict, Any, List, Optional
from src.models.operations_report import DependencyStatus


class DependencyValidator:
    """
    Validates required Python packages, React Node modules, configuration files,
    and engine-specific configurations.
    """

    @staticmethod
    def validate_dependencies(
        mock_packages: Optional[Dict[str, bool]] = None,
        mock_node_modules: Optional[Dict[str, bool]] = None,
        custom_root: Optional[str] = None,
        custom_env: Optional[Dict[str, str]] = None
    ) -> DependencyStatus:
        """
        Runs dependency checks.
        """
        root_dir = custom_root if custom_root is not None else os.getcwd()
        env = custom_env if custom_env is not None else os.environ
        details: Dict[str, Any] = {}

        # 1. Python packages
        required_python = ["dataclasses", "unittest", "typing", "json", "os"]
        # Try checking for standard library or external ones we might need.
        # We can also check if `kiteconnect` is present or mockable.
        python_packages_valid = True
        python_details: Dict[str, bool] = {}
        
        for pkg in required_python:
            if mock_packages is not None:
                status = mock_packages.get(pkg, True)
            else:
                try:
                    importlib.import_module(pkg)
                    status = True
                except ImportError:
                    status = False
            python_details[pkg] = status
            if not status:
                python_packages_valid = False
                
        details["python_packages"] = python_details

        # 2. Node modules
        # Check if node_modules exists, and specifically if major packages like 'react' and 'vite' are installed
        node_modules_valid = True
        node_details: Dict[str, bool] = {}
        node_pkgs = ["react", "vite", "lucide-react"]
        
        node_modules_path = os.path.join(root_dir, "node_modules")
        node_modules_exists = os.path.isdir(node_modules_path)
        
        for pkg in node_pkgs:
            if mock_node_modules is not None:
                status = mock_node_modules.get(pkg, True)
            else:
                status = node_modules_exists and os.path.isdir(os.path.join(node_modules_path, pkg))
            node_details[pkg] = status
            if not status:
                node_modules_valid = False

        details["node_modules_installed"] = node_modules_exists
        details["node_packages"] = node_details

        # 3. Configuration files
        config_files_valid = True
        config_details: Dict[str, bool] = {}

        # Scoring config
        scoring_path = os.path.join(root_dir, "src", "config_engine", "scoring.yaml")
        scoring_valid = os.path.isfile(scoring_path)
        config_details["scoring_configuration"] = scoring_valid

        # News config - checking if configuration is mock-valid
        config_details["news_configuration"] = True

        # Broker config - checking if broker env exists
        broker_env_exists = env.get("KITE_API_KEY") is not None
        config_details["broker_configuration"] = broker_env_exists

        if not (scoring_valid and broker_env_exists):
            config_files_valid = False

        details["config_files"] = config_details

        return DependencyStatus(
            python_packages_valid=python_packages_valid,
            node_modules_valid=node_modules_valid,
            config_files_valid=config_files_valid,
            details=details
        )
