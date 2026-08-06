# Part 7: Configuration & Workspace Management

This section documents the multi-tiered configuration system, preset profiles, and active workspace management structures within the NIFTY Option Finder & Market Intelligence Workstation.

---

## 🎯 Configuration Philosophy

The workstation's configuration architecture is built around three core principles:
1. **Separation of Concerns**: Configuration files are modular and organized by domain (e.g., scoring, risk, trading, broker, and dashboard parameters).
2. **Preset Profiles over Ad-Hoc Tweak**: Operators should not manually adjust individual parameters during live trading. Instead, they activate pre-configured profiles (such as Conservative, Aggressive, or Expiry Day) designed and tested for specific market conditions.
3. **Strict Validation Checks**: All configurations undergo mathematical and range checks on startup to prevent system crashes or invalid trade executions.

---

## 📂 Modular Configuration Templates

System configurations are stored as structured JSON or YAML files inside `src/configuration_engine/templates/`:

- **`scoring.yaml`**: Houses mathematical coefficients for the Market Scoring Pipeline.
- **`risk.yaml`**: Houses capital constraints, drawdown limits, and allocation rules.
- **`trading.yaml`**: Houses index definitions, market hours, and standard lot sizes.
- **`broker.yaml`**: Houses connection credentials, rate limits, and fallback settings.
- **`dashboard.yaml`**: Houses visual themes, panel visibility, and polling rates.

---

## 👤 Profile Preset Matrix

Profiles are immutable configurations optimized for different trading styles. When a profile is activated, it overlays its values on top of standard system defaults:

| Profile | Primary Objective | Max Risk (0-100) | Max Capital (INR) | Drawdown Limit (%) | Permitted Strategies |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **`DEFAULT`** | Balanced, low-friction | `50.0` | `100,000` | `5.0%` | Scalping, Trend, Mean Reversion |
| **`PAPER_TRADING`**| Aggressive simulation | `70.0` | `500,000` | `10.0%` | Scalping, Trend, Mean Reversion, Momentum |
| **`LIVE_TRADING`** | Safe manual execution | `40.0` | `50,000` | `3.0%` | Scalping, Trend Following |
| **`CONSERVATIVE`**| Capital preservation | `30.0` | `25,000` | `2.0%` | Trend Following |
| **`AGGRESSIVE`** | High yield capture | `85.0` | `1,000,000` | `15.0%` | All Strategies |
| **`EXPIRY_DAY`** | Option decay capture | `60.0` | `150,000` | `6.0%` | Scalping, Expiry-Decay |
| **`SWING`** | Multi-day positioning | `45.0` | `200,000` | `8.0%` | Trend Following, Mean Reversion |

---

## ⚙️ Workspace Preferences Specification

Operators can customize dashboard presentation, refresh rates, and reporting formats using standard workspace preferences:

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
1. **`refresh_interval_seconds`**: Polling rate for visual panels (valid range: `1` to `60` seconds).
2. **`cli_theme`**: Terminal theme. Can be `DARK`, `LIGHT`, or `HIGH_CONTRAST`.
3. **`react_theme`**: React dashboard theme. Can be `DARK` or `LIGHT`.
4. **`visible_panels`**: Determines which dashboard panels to display on screen.
5. **`logging_level`**: Standard logging sensitivity limit (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
6. **`report_export_format`**: Export format for backup files (`JSON` or `YAML`).

---

## 🔍 Validation & Migration Systems

### A. Real-Time Configuration Validation
The configuration validator runs checks on startup:
- **Range Constraints**: Risk scores must fall between `0.0` and `100.0`. Max drawdown limits must be within `0.0%` and `100.0%`.
- **Integrity Constraints**: Capital allocations must exceed zero.
- **Normalization Verification**: Scoring coefficients must sum up to exactly `100.0` to prevent calculation overflows in the scoring pipelines.

### B. Schema Migration Layer
To ensure backward compatibility, the workstation includes a schema migration layer. If the loader detects legacy configuration keys (e.g., `margin_buffer_ratio` or `legacy_leverage_limit`), it flags them as warnings and translates them to modern schema fields, preventing startup crashes.
