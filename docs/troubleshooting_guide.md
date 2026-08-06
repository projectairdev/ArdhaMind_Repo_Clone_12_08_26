# Troubleshooting Guide

This guide details common error codes, diagnostic issues, and performance bottlenecks, and provides instructions for resolving them quickly.

---

## 🛠️ Common Operational Errors

### 1. Missing or Expired Broker Environment Variables
* **Symptom**: Startup health diagnostics panel displays `env_vars: FAIL` or the broker panel raises connection timeouts.
* **Root Cause**: The `.env` file does not contain necessary credentials or the manual token has expired.
* **Remedy**:
  1. Verify the `.env` file exists at the root folder of your project workspace.
  2. Confirm that `KITE_API_KEY` and `KITE_API_SECRET` are correct.
  3. Generate a fresh access token from your broker developer portal and update the environment or `session.json` cache.

### 2. Invalid Configuration Warnings (`VALID_WITH_WARNINGS` / `INVALID`)
* **Symptom**: The Configuration Panel displays a status of `INVALID` or lists numerous HIGH-severity warnings.
* **Root Cause**: Config values violate mathematical bounds (e.g. risk weights do not sum up to 100.0, or maximum risk score is set to `115.0`).
* **Remedy**:
  1. View the **Active Configuration Warnings** list in your terminal panel.
  2. Open `src/config_engine/scoring.yaml` or relevant profile settings.
  3. Ensure weights are balanced and within ranges:
     - Risk scores: `0.0` to `100.0`
     - Sizing allocations: `> 0`
  4. Re-run tests to confirm resolution:
     ```bash
     python3 -m unittest tests/test_configuration_manager.py
     ```

### 3. Missing Local SQLite Cache Database (`instruments.db`)
* **Symptom**: Database queries fail or instrument lookups fail.
* **Root Cause**: The instruments cache was cleared or the disk directory does not exist.
* **Remedy**:
  1. The workstation automatically handles touch-creation of `/cache/instruments.db` on startup. If this fails, verify write permissions on the workspace folder.
  2. Run the startup validator to re-create cache folders:
     ```bash
     python3 -m unittest tests/test_operations_manager.py
     ```

---

## 🏎️ Performance Tuning & Resource Limits

### 1. High CPU Utilization
* **Symptom**: Dashboard frame rate lags, system metrics report high CPU percentages.
* **Root Cause**: Too many option contract candidates are evaluated concurrently, or the refresh interval is set too low (e.g., `1` second).
* **Remedy**:
  1. Open workspace preferences or your active profile configuration.
  2. Set `refresh_interval_seconds` to a higher rate, such as `5` or `10` seconds.
  3. Filter option candidates to ATM +/- 2 strikes to minimize processing loops.

### 2. Python Module Import Slowdown
* **Symptom**: Startup time of pipelines takes more than 2 seconds.
* **Root Cause**: Heavy third-party packages or circular import checks.
* **Remedy**:
  - The codebase has been optimized for clean, stateless imports.
  - Ensure you are running under a local Python virtual environment (`venv`) to prevent python from crawling global system directories for packages.
