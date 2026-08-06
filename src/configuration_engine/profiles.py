from __future__ import annotations

from typing import Dict, Any, Optional, List
from src.models.configuration_report import ConfigurationProfile

# Immutable presets for workspace profiles
PROFILE_SETTINGS: Dict[str, Dict[str, Any]] = {
    "DEFAULT": {
        "workspace_preferences": {
            "refresh_interval_seconds": 10,
            "cli_theme": "HIGH_CONTRAST",
            "react_theme": "DARK",
            "visible_panels": ["SUMMARY", "MARKET", "TRADE", "RISK", "OPERATIONS", "CONFIGURATION"],
            "default_screen": "SUMMARY",
            "logging_level": "INFO",
            "report_export_format": "JSON"
        },
        "risk": {
            "max_risk_score": 50.0,
            "max_capital_allocation": 100000.0,
            "max_drawdown_limit": 5.0,
            "allowed_strategies": ["SCALPING", "TREND_FOLLOWING", "MEAN_REVERSION"]
        },
        "scoring": {
            "trend_weight": 0.35,
            "volatility_weight": 0.20,
            "liquidity_weight": 0.15,
            "option_score_weight": 0.30
        }
    },
    "PAPER_TRADING": {
        "workspace_preferences": {
            "refresh_interval_seconds": 5,
            "cli_theme": "DARK",
            "react_theme": "DARK",
            "visible_panels": ["SUMMARY", "MARKET", "PAPER_TRADING", "OPERATIONS", "CONFIGURATION"],
            "default_screen": "PAPER_TRADING",
            "logging_level": "DEBUG",
            "report_export_format": "JSON"
        },
        "risk": {
            "max_risk_score": 70.0,
            "max_capital_allocation": 500000.0,
            "max_drawdown_limit": 10.0,
            "allowed_strategies": ["SCALPING", "TREND_FOLLOWING", "MEAN_REVERSION", "MOMENTUM"]
        },
        "scoring": {
            "trend_weight": 0.30,
            "volatility_weight": 0.25,
            "liquidity_weight": 0.20,
            "option_score_weight": 0.25
        }
    },
    "LIVE_TRADING": {
        "workspace_preferences": {
            "refresh_interval_seconds": 2,
            "cli_theme": "HIGH_CONTRAST",
            "react_theme": "LIGHT",
            "visible_panels": ["SUMMARY", "MARKET", "TRADE", "RISK", "EXECUTION", "OPERATIONS", "CONFIGURATION"],
            "default_screen": "SUMMARY",
            "logging_level": "WARNING",
            "report_export_format": "YAML"
        },
        "risk": {
            "max_risk_score": 40.0,
            "max_capital_allocation": 50000.0,
            "max_drawdown_limit": 3.0,
            "allowed_strategies": ["SCALPING", "TREND_FOLLOWING"]
        },
        "scoring": {
            "trend_weight": 0.40,
            "volatility_weight": 0.10,
            "liquidity_weight": 0.20,
            "option_score_weight": 0.30
        }
    },
    "CONSERVATIVE": {
        "workspace_preferences": {
            "refresh_interval_seconds": 15,
            "cli_theme": "LIGHT",
            "react_theme": "LIGHT",
            "visible_panels": ["SUMMARY", "RISK", "OPERATIONS", "CONFIGURATION"],
            "default_screen": "SUMMARY",
            "logging_level": "INFO",
            "report_export_format": "JSON"
        },
        "risk": {
            "max_risk_score": 30.0,
            "max_capital_allocation": 25000.0,
            "max_drawdown_limit": 2.0,
            "allowed_strategies": ["TREND_FOLLOWING"]
        },
        "scoring": {
            "trend_weight": 0.50,
            "volatility_weight": 0.05,
            "liquidity_weight": 0.25,
            "option_score_weight": 0.20
        }
    },
    "AGGRESSIVE": {
        "workspace_preferences": {
            "refresh_interval_seconds": 1,
            "cli_theme": "DARK",
            "react_theme": "DARK",
            "visible_panels": ["SUMMARY", "TRADE", "RISK", "EXECUTION", "CONFIGURATION"],
            "default_screen": "TRADE",
            "logging_level": "DEBUG",
            "report_export_format": "YAML"
        },
        "risk": {
            "max_risk_score": 85.0,
            "max_capital_allocation": 1000000.0,
            "max_drawdown_limit": 15.0,
            "allowed_strategies": ["SCALPING", "TREND_FOLLOWING", "MEAN_REVERSION", "MOMENTUM", "BREAKOUT"]
        },
        "scoring": {
            "trend_weight": 0.20,
            "volatility_weight": 0.30,
            "liquidity_weight": 0.10,
            "option_score_weight": 0.40
        }
    },
    "EXPIRY_DAY": {
        "workspace_preferences": {
            "refresh_interval_seconds": 2,
            "cli_theme": "HIGH_CONTRAST",
            "react_theme": "DARK",
            "visible_panels": ["SUMMARY", "MARKET", "TRADE", "RISK", "CONFIGURATION"],
            "default_screen": "MARKET",
            "logging_level": "INFO",
            "report_export_format": "JSON"
        },
        "risk": {
            "max_risk_score": 60.0,
            "max_capital_allocation": 150000.0,
            "max_drawdown_limit": 6.0,
            "allowed_strategies": ["SCALPING", "EXPIRY_STRATEGY"]
        },
        "scoring": {
            "trend_weight": 0.15,
            "volatility_weight": 0.35,
            "liquidity_weight": 0.10,
            "option_score_weight": 0.40
        }
    },
    "SWING": {
        "workspace_preferences": {
            "refresh_interval_seconds": 30,
            "cli_theme": "DARK",
            "react_theme": "LIGHT",
            "visible_panels": ["SUMMARY", "MARKET", "TRADE", "CONFIGURATION"],
            "default_screen": "SUMMARY",
            "logging_level": "INFO",
            "report_export_format": "YAML"
        },
        "risk": {
            "max_risk_score": 45.0,
            "max_capital_allocation": 200000.0,
            "max_drawdown_limit": 8.0,
            "allowed_strategies": ["TREND_FOLLOWING", "MEAN_REVERSION"]
        },
        "scoring": {
            "trend_weight": 0.45,
            "volatility_weight": 0.15,
            "liquidity_weight": 0.15,
            "option_score_weight": 0.25
        }
    }
}


class ProfileManager:
    """
    Stateless manager supporting retrieval and registration of immutable workspace profiles.
    """

    @staticmethod
    def get_profile(name: str) -> ConfigurationProfile:
        """
        Retrieves a workspace profile by name. Falls back to DEFAULT if not found.
        """
        profile_name = name.upper() if name else "DEFAULT"
        if profile_name not in PROFILE_SETTINGS:
            profile_name = "DEFAULT"

        settings = PROFILE_SETTINGS[profile_name]
        desc = f"Immutable workspace profile optimized for {profile_name.lower().replace('_', ' ')}."
        
        return ConfigurationProfile(
            profile_id=f"PROF_{profile_name}",
            name=profile_name,
            description=desc,
            settings=settings
        )

    @staticmethod
    def list_profiles() -> List[str]:
        """
        Returns a list of all available profile names.
        """
        return list(PROFILE_SETTINGS.keys())
