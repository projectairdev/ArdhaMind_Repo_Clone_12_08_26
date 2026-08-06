from __future__ import annotations

from typing import Dict, Any, List, Optional
from src.models.configuration_report import ConfigurationWarning

# Schema expectations and deprecation lists
REQUIRED_KEYS: Dict[str, List[str]] = {
    "trading": ["version", "default_instrument", "allowed_segments"],
    "risk": ["version", "max_risk_score", "max_capital_allocation", "max_drawdown_limit"],
    "scoring": ["version", "overall_weights"],
    "news": ["version", "news_sources", "sentiment_threshold"],
    "broker": ["version", "broker_name", "api_version"],
    "dashboard": ["version", "refresh_interval_seconds", "default_theme"],
    "paper_trading": ["version", "initial_margin", "slippage_percent"],
    "analytics": ["version", "metrics_window", "performance_benchmark"],
    "operations": ["version", "log_level", "backup_frequency"]
}

KNOWN_KEYS: Dict[str, List[str]] = {
    "trading": ["version", "default_instrument", "allowed_segments", "trading_hours"],
    "risk": ["version", "max_risk_score", "max_capital_allocation", "max_drawdown_limit", "allowed_strategies", "risk_profile"],
    "scoring": ["version", "overall_weights", "trend_weights", "option_weights", "volatility_weights"],
    "news": ["version", "news_sources", "sentiment_threshold", "alert_keywords"],
    "broker": ["version", "broker_name", "api_version", "reconnect_attempts", "access_token_env"],
    "dashboard": ["version", "refresh_interval_seconds", "default_theme", "visible_panels", "cli_preferences"],
    "paper_trading": ["version", "initial_margin", "slippage_percent", "execution_delay_ms"],
    "analytics": ["version", "metrics_window", "performance_benchmark", "historical_data_days"],
    "operations": ["version", "log_level", "backup_frequency", "cache_limit_mb"]
}

DEPRECATED_KEYS: Dict[str, List[str]] = {
    "trading": ["legacy_instrument_lookup", "use_old_nifty_code"],
    "risk": ["legacy_leverage_limit", "margin_buffer_ratio"],
    "scoring": ["use_legacy_scalping_weights"],
    "news": ["fetch_rss_feeds_only", "use_legacy_news_api"],
    "broker": ["old_kite_v2_api", "bypass_checksum"],
    "dashboard": ["legacy_table_layout", "enable_old_graphs"],
    "paper_trading": ["use_zero_fee_model"],
    "analytics": ["old_profit_loss_math"],
    "operations": ["force_system_restart_on_error"]
}


class ConfigurationValidator:
    """
    Validates loaded configuration datasets and generates warnings without mutating state.
    """

    @staticmethod
    def validate_config(category: str, data: Dict[str, Any]) -> List[ConfigurationWarning]:
        """
        Validates loaded configuration and returns a list of ConfigurationWarning objects.
        """
        cat_lower = category.lower()
        warnings: List[ConfigurationWarning] = []
        warning_idx = 1

        def add_warning(sev: str, msg: str, val: Optional[Any] = None) -> None:
            nonlocal warning_idx
            warnings.append(
                ConfigurationWarning(
                    warning_id=f"WARN_{cat_upper}_{warning_idx:03d}",
                    category=cat_upper,
                    severity=sev,
                    message=msg,
                    invalid_value=val
                )
            )
            warning_idx += 1

        cat_upper = category.upper()

        # 1. Missing fields
        req_keys = REQUIRED_KEYS.get(cat_lower, [])
        for k in req_keys:
            if k not in data:
                add_warning("HIGH", f"Missing required parameter: '{k}'")

        # 2. Version mismatch
        if "version" in data:
            ver = str(data["version"])
            if ver != "1.0.0":
                add_warning(
                    "MEDIUM",
                    f"Configuration version mismatch. Expected '1.0.0', got '{ver}'",
                    ver
                )

        # 3. Unknown settings (low severity)
        known = KNOWN_KEYS.get(cat_lower, [])
        for k in data:
            if k not in known and k not in DEPRECATED_KEYS.get(cat_lower, []):
                add_warning("LOW", f"Unknown configuration parameter: '{k}'", data[k])

        # 4. Deprecated parameters
        deprecated = DEPRECATED_KEYS.get(cat_lower, [])
        for k in data:
            if k in deprecated:
                add_warning("MEDIUM", f"Deprecated parameter in use: '{k}'. Please update to the latest schema.", data[k])

        # 5. Invalid values check (Value validations based on domain knowledge)
        if cat_lower == "risk":
            max_risk = data.get("max_risk_score")
            if max_risk is not None:
                try:
                    val = float(max_risk)
                    if not (0.0 <= val <= 100.0):
                        add_warning("HIGH", "max_risk_score must be between 0.0 and 100.0", max_risk)
                except ValueError:
                    add_warning("HIGH", "max_risk_score must be a numeric value", max_risk)

            max_cap = data.get("max_capital_allocation")
            if max_cap is not None:
                try:
                    val = float(max_cap)
                    if val <= 0.0:
                        add_warning("HIGH", "max_capital_allocation must be greater than zero", max_cap)
                except ValueError:
                    add_warning("HIGH", "max_capital_allocation must be a numeric value", max_cap)

            max_dd = data.get("max_drawdown_limit")
            if max_dd is not None:
                try:
                    val = float(max_dd)
                    if not (0.0 <= val <= 100.0):
                        add_warning("HIGH", "max_drawdown_limit must be a percentage between 0.0 and 100.0", max_dd)
                except ValueError:
                    add_warning("HIGH", "max_drawdown_limit must be a numeric value", max_dd)

        elif cat_lower == "scoring":
            weights = data.get("overall_weights")
            if isinstance(weights, dict):
                try:
                    total_sum = sum(float(v) for v in weights.values())
                    # Scoring engine usually expects weights summing to 100.0 or 1.0 depending on normalization
                    # Let's verify sum is 100.0 (or close to 100.0) or 1.0. Let's warn if it's completely off.
                    if abs(total_sum - 100.0) > 0.1 and abs(total_sum - 1.0) > 0.1:
                        add_warning(
                            "MEDIUM",
                            f"Overall weights sum to {total_sum:.2f}. Expected sum of 100.0 or 1.0.",
                            weights
                        )
                except (ValueError, TypeError):
                    add_warning("HIGH", "Overall weights must contain only numeric values", weights)

        elif cat_lower == "dashboard":
            refresh = data.get("refresh_interval_seconds")
            if refresh is not None:
                try:
                    val = int(refresh)
                    if val <= 0:
                        add_warning("HIGH", "refresh_interval_seconds must be a positive integer", refresh)
                except ValueError:
                    add_warning("HIGH", "refresh_interval_seconds must be an integer", refresh)

        elif cat_lower == "paper_trading":
            slippage = data.get("slippage_percent")
            if slippage is not None:
                try:
                    val = float(slippage)
                    if not (0.0 <= val <= 10.0):
                        add_warning("MEDIUM", "slippage_percent is unusually high or invalid", slippage)
                except ValueError:
                    add_warning("HIGH", "slippage_percent must be a numeric value", slippage)

        return warnings
