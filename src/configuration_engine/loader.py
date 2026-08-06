from __future__ import annotations

import os
import json
from typing import Dict, Any, Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


DEFAULT_CONFIGS: Dict[str, Dict[str, Any]] = {
    "trading": {
        "version": "1.0.0",
        "default_instrument": "NIFTY",
        "allowed_segments": ["OPTIONS", "FUTURES"],
        "trading_hours": {"start": "09:15", "end": "15:30"}
    },
    "risk": {
        "version": "1.0.0",
        "max_risk_score": 50.0,
        "max_capital_allocation": 100000.0,
        "max_drawdown_limit": 5.0,
        "allowed_strategies": ["SCALPING", "TREND_FOLLOWING", "MEAN_REVERSION"]
    },
    "scoring": {
        "version": "1.0.0",
        "overall_weights": {
            "trend": 20.0,
            "options": 25.0,
            "volatility": 15.0,
            "liquidity": 15.0,
            "session": 10.0,
            "expiry": 5.0,
            "confluence": 10.0
        }
    },
    "news": {
        "version": "1.0.0",
        "news_sources": ["BLOOMBERG", "REUTERS", "MONEYCONTROL"],
        "sentiment_threshold": 0.15
    },
    "broker": {
        "version": "1.0.0",
        "broker_name": "ZERODHA",
        "api_version": "3.0",
        "reconnect_attempts": 3
    },
    "dashboard": {
        "version": "1.0.0",
        "refresh_interval_seconds": 10,
        "default_theme": "DARK",
        "visible_panels": ["SUMMARY", "MARKET", "TRADE", "RISK", "OPERATIONS", "CONFIGURATION"]
    },
    "paper_trading": {
        "version": "1.0.0",
        "initial_margin": 1000000.0,
        "slippage_percent": 0.05
    },
    "analytics": {
        "version": "1.0.0",
        "metrics_window": 30,
        "performance_benchmark": "NIFTY_50"
    },
    "operations": {
        "version": "1.0.0",
        "log_level": "INFO",
        "backup_frequency": "DAILY"
    }
}


class ConfigurationLoader:
    """
    Loads configuration datasets from files, mock-dicts, or fallback structures.
    """

    @staticmethod
    def load_config_file(
        category: str,
        custom_root: Optional[str] = None,
        mock_files: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Loads a config file for a specific category. Supports YAML/JSON and mock-files.
        """
        category_lower = category.lower()
        if category_lower not in DEFAULT_CONFIGS:
            return {}

        # 1. Check mock files dictionary first (important for pure unit testing without FS)
        if mock_files:
            filename = f"{category_lower}.yaml"
            if filename in mock_files:
                return ConfigurationLoader._parse_string(mock_files[filename], is_yaml=True)
            filename_json = f"{category_lower}.json"
            if filename_json in mock_files:
                return ConfigurationLoader._parse_string(mock_files[filename_json], is_yaml=False)

        # 2. Check on actual filesystem
        root = custom_root if custom_root else os.getcwd()
        config_dir = os.path.join(root, "src", "config_engine")

        # Check for YAML
        yaml_path = os.path.join(config_dir, f"{category_lower}.yaml")
        if os.path.isfile(yaml_path):
            try:
                with open(yaml_path, "r") as f:
                    content = f.read()
                    return ConfigurationLoader._parse_string(content, is_yaml=True)
            except Exception:
                pass

        # Check for JSON
        json_path = os.path.join(config_dir, f"{category_lower}.json")
        if os.path.isfile(json_path):
            try:
                with open(json_path, "r") as f:
                    content = f.read()
                    return ConfigurationLoader._parse_string(content, is_yaml=False)
            except Exception:
                pass

        # 3. Fall back to clean defaults
        return dict(DEFAULT_CONFIGS[category_lower])

    @staticmethod
    def _parse_string(content: str, is_yaml: bool) -> Dict[str, Any]:
        """
        Parses JSON or YAML strings securely.
        """
        if not content.strip():
            return {}

        if is_yaml:
            if yaml:
                try:
                    res = yaml.safe_load(content)
                    if isinstance(res, dict):
                        return res
                except Exception:
                    pass
            # Super basic line-by-line fallback parser for YAML if PyYAML isn't available or fails
            config: Dict[str, Any] = {}
            for line in content.splitlines():
                line = line.split("#")[0].strip()
                if not line or ":" not in line:
                    continue
                k, v = line.split(":", 1)
                k = k.strip().strip("'\"")
                v = v.strip().strip("'\"")
                # Type conversions
                if v.lower() == "true":
                    config[k] = True
                elif v.lower() == "false":
                    config[k] = False
                else:
                    try:
                        if "." in v:
                            config[k] = float(v)
                        else:
                            config[k] = int(v)
                    except ValueError:
                        config[k] = v
            return config
        else:
            try:
                res = json.loads(content)
                if isinstance(res, dict):
                    return res
            except Exception:
                pass
        return {}
