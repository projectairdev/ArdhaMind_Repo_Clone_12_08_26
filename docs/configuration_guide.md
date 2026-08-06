# Configuration Guide

The workstation features a multi-tiered configuration system. Parameters can be loaded from file templates, overridden dynamically via profiles, or adjusted through explicit workspace preference objects.

---

## 📂 Configuration Files Structure

Configuration settings are organized by category and stored under `src/config_engine/` (legacy format) and evaluated dynamically via the `src/configuration_engine/` layer:

- `scoring.yaml` / `scoring.json`: Houses overall indicators and pipeline weights.
- `risk.yaml` / `risk.json`: Houses capital constraints, drawdowns, and stop-limits.
- `trading.yaml` / `trading.json`: Houses asset classes, exchange hours, and default symbols.
- `broker.yaml` / `broker.json`: Houses gateway configurations and reconnect options.
- `dashboard.yaml` / `dashboard.json`: Houses visual refresh rates, themes, and screen preferences.

---

## 🎯 Workspace Profile Presets

Profiles are immutable configurations optimized for different trading strategies and risk tolerances. When a profile is activated, it overlays its values on top of standard defaults.

The workstation defines seven built-in profiles:

| Profile Name | Target Objective | Max Risk | Max Allocation | Drawdown Limit | Permitted Strategies |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **`DEFAULT`** | Standard balanced setup | `50.0` | `100,000 INR` | `5.0%` | Scalping, Trend, Mean Reversion |
| **`PAPER_TRADING`**| Aggressive simulated paper run | `70.0` | `500,000 INR` | `10.0%` | Scalping, Trend, Mean Reversion, Momentum |
| **`LIVE_TRADING`** | Safe real-money manual execution| `40.0` | `50,000 INR` | `3.0%` | Scalping, Trend Following |
| **`CONSERVATIVE`**| Ultra-low risk preservation | `30.0` | `25,000 INR` | `2.0%` | Trend Following |
| **`AGGRESSIVE`** | Maximum yield capture | `85.0` | `1,000,000 INR` | `15.0%` | Scalping, Trend, Mean Reversion, Momentum, Breakout |
| **`EXPIRY_DAY`** | Heavy option decay capture | `60.0` | `150,000 INR` | `6.0%` | Scalping, Expiry-Decay Strategies |
| **`SWING`** | Multi-day positioning | `45.0` | `200,000 INR` | `8.0%` | Trend Following, Mean Reversion |

---

## ⚙️ Custom Workspace Preferences

Workspace preferences govern how the visual terminal and web panels are presented. These are parsed dynamically and can be customized per workstation instance:

```json
{
  "refresh_interval_seconds": 10,
  "cli_theme": "HIGH_CONTRAST",
  "react_theme": "DARK",
  "visible_panels": ["SUMMARY", "MARKET", "TRADE", "RISK", "OPERATIONS", "CONFIGURATION"],
  "default_screen": "SUMMARY",
  "logging_level": "INFO",
  "report_export_format": "JSON"
}
```

### Parameter Explanations:
1. **`refresh_interval_seconds`**: Interval at which visual loops poll data (valid range: `1` to `60` seconds).
2. **`cli_theme`**: Terminal styling option. Can be `DARK`, `LIGHT`, or `HIGH_CONTRAST`.
3. **`react_theme`**: React dashboard theme. Can be `DARK` or `LIGHT`.
4. **`visible_panels`**: Determines which dashboard tabs or boxes to display on screen.
5. **`logging_level`**: Standard logging sensitivity limit (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
6. **`report_export_format`**: Format utilized to back up configuration profiles (`JSON` or `YAML`).

---

## ⚠️ Configuration Validation Rules

The validator performs real-time validation checks to prevent workstation crashes:
- **Range Checks**: `max_risk_score` must fall between `0.0` and `100.0`. `max_drawdown_limit` must be within `0.0%` and `100.0%`.
- **Integrity Checks**: `max_capital_allocation` must exceed zero.
- **Scoring Sum Checks**: Weights inside `scoring` must sum up to exactly `100.0` (or normalized to `1.0`) to avoid scaling overflow.
- **Migration Flags**: Flags older or deprecated schema parameters (such as `margin_buffer_ratio` or `legacy_leverage_limit`) and provides safe translation instructions.
